"""
Guitar effects processor v2 — phrase-aware, technique-driven.

Instead of rolling per-note random dice for every technique, this
processor reads technique hints that were either:
  1. Embedded in the Markov chain output (from annotated CSV datasets)
  2. Embedded in arpeggio / riff patterns (from arpeggio_patterns.py)
  3. Applied as a fallback with strict phrase-level budgets

This ensures musical coherence: effects appear at the *right* musical
moments rather than chaotically on every note.

Event types produced:
    {'type': 'note', 'note': int, 'start': int, 'duration': int,
     'velocity': int, 'technique': str}
    {'type': 'pitchbend', 'value': int, 'time': int}
    {'type': 'control_change', 'control': int, 'value': int, 'time': int}
"""

import math
import random
from typing import List, Dict, Tuple, Optional, Set

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import TICKS_PER_BEAT
from config.guitar_techniques import (
    BEND_PROFILES, VIBRATO_PROFILES, SLIDE_PROFILES,
    TECHNIQUE_PROFILES, get_technique_profile,
)


# MIDI pitch-bend range: ±2 semitones (GM default set via RPN in renderer)
PB_RANGE_SEMITONES = 2
PB_MAX = 8191
PB_CENTER = 0

# Phrase-level limits to prevent chaos
PHRASE_LENGTH = 8                 # Notes per phrase for budget tracking
MAX_EFFECTS_PER_PHRASE = 3        # At most 3 non-normal techniques per phrase
MIN_COOLDOWN_NOTES = 2            # Minimum notes between consecutive effects

# Minimum durations for certain techniques (in ticks)
MIN_DUR_BEND = TICKS_PER_BEAT // 2        # ≥ eighth note for bends
MIN_DUR_VIBRATO = TICKS_PER_BEAT          # ≥ quarter note for vibrato
MIN_DUR_SLIDE = TICKS_PER_BEAT // 4       # ≥ sixteenth for slides


def _semitones_to_pb(semitones: float) -> int:
    """Convert a semitone offset to a MIDI pitch-bend value."""
    return int((semitones / PB_RANGE_SEMITONES) * PB_MAX)


class GuitarEffectsProcessor:
    """
    Post-processes a lead track to inject guitar articulations.

    The processor works in two modes:
    1. **Technique-driven** (preferred): Each note event carries a 'technique'
       key from the Markov chain or arpeggio system.  The processor applies
       exactly that technique — no randomness.
    2. **Fallback mode**: For notes without a technique hint (or with
       technique='normal'), the processor *may* apply a random technique
       but respects strict phrase-level budgets and cooldowns.

    Usage:
        processor = GuitarEffectsProcessor()
        enriched = processor.process(events, style, scale_notes)
    """

    def process(
        self,
        events: List[Dict],
        style: dict,
        scale_notes: Optional[Set[int]] = None,
    ) -> List[Dict]:
        """
        Apply guitar techniques to a list of note events.

        Each event dict should have at minimum:
            'note', 'start', 'duration', 'velocity'
        And optionally:
            'technique'  — one of the canonical technique names

        Returns enriched event list with pitchbend / CC / modified notes.
        """
        if not events:
            return events

        articulation = style.get('articulation', 'medium')
        profile = get_technique_profile(articulation)

        # Per-style overrides
        bend_prob_override = style.get('bend_probability')
        hammer_prob_override = style.get('hammer_on_probability')
        vibrato_intensity = style.get('vibrato_intensity', 0)
        tapping_enabled = style.get('tapping', False)

        enriched: List[Dict] = []
        n = len(events)
        i = 0

        # Phrase-level state
        phrase_effects_used = 0
        notes_since_last_effect = MIN_COOLDOWN_NOTES  # Allow first note

        while i < n:
            evt = events[i]
            note = evt['note']
            start = evt['start']
            dur = evt['duration']
            vel = evt.get('velocity', 80)
            technique = evt.get('technique', 'normal')

            # Reset phrase budget every PHRASE_LENGTH notes
            phrase_position = i % PHRASE_LENGTH
            if phrase_position == 0:
                phrase_effects_used = 0

            applied = False

            # ==========================================================
            # MODE 1: Technique hint from data — apply deterministically
            # ==========================================================
            if technique != 'normal':
                applied = self._apply_technique_hint(
                    technique, note, start, dur, vel,
                    enriched, events, i, n,
                    profile, scale_notes, tapping_enabled,
                )
                if applied:
                    phrase_effects_used += 1
                    notes_since_last_effect = 0
                    # Hammer-on / pull-off runs consume multiple events
                    if technique in ('hammer_on', 'pull_off'):
                        run = self._collect_technique_run(events, i, technique)
                        if len(run) > 1:
                            if technique == 'hammer_on':
                                enriched.extend(self._make_hammer_on_run(run, profile))
                            else:
                                enriched.extend(self._make_pull_off_run(run, profile))
                            i += len(run)
                            notes_since_last_effect = 0
                            continue

            # ==========================================================
            # MODE 2: Fallback — conservative random with phrase budget
            # ==========================================================
            if not applied and technique == 'normal':
                can_apply = (
                    phrase_effects_used < MAX_EFFECTS_PER_PHRASE
                    and notes_since_last_effect >= MIN_COOLDOWN_NOTES
                )
                if can_apply:
                    applied = self._fallback_random(
                        note, start, dur, vel,
                        enriched, events, i, n,
                        profile, scale_notes,
                        bend_prob_override, hammer_prob_override,
                        vibrato_intensity, tapping_enabled,
                    )
                    if applied:
                        phrase_effects_used += 1
                        notes_since_last_effect = 0
                        # Check if fallback consumed a run
                        if isinstance(applied, int) and applied > 1:
                            i += applied
                            continue

            # ==========================================================
            # No technique applied — pass note through unchanged
            # ==========================================================
            if not applied:
                enriched.append({
                    'type': 'note',
                    'note': note,
                    'start': start,
                    'duration': dur,
                    'velocity': vel,
                })

            notes_since_last_effect += 1
            i += 1

        # Reset pitch bend at end
        if any(e.get('type') == 'pitchbend' for e in enriched):
            last_time = max(
                (e.get('start', 0) + e.get('duration', 0) if e.get('type') == 'note'
                 else e.get('time', 0))
                for e in enriched
            )
            enriched.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': last_time})

        return enriched

    # =================================================================
    # Technique hint dispatcher
    # =================================================================
    def _apply_technique_hint(
        self, technique: str, note: int, start: int, dur: int, vel: int,
        enriched: List[Dict], events: List[Dict], idx: int, n: int,
        profile: dict, scale_notes, tapping_enabled: bool,
    ) -> bool:
        """Apply a specific technique from the data annotation."""

        if technique in ('bend_half', 'bend_whole', 'bend_slow'):
            if dur < MIN_DUR_BEND:
                return False
            bend_map = {
                'bend_half': 'half',
                'bend_whole': 'whole',
                'bend_slow': 'slow_blues',
            }
            enriched.extend(self._make_bend(note, start, dur, vel, bend_map[technique]))
            return True

        if technique == 'vibrato':
            if dur < MIN_DUR_VIBRATO:
                return False
            vib_name = profile.get('vibrato', {}).get('profile', 'standard')
            enriched.extend(self._make_vibrato(note, start, dur, vel, vib_name))
            return True

        if technique in ('slide_up', 'slide_down'):
            if dur < MIN_DUR_SLIDE:
                return False
            slide_name = 'into' if technique == 'slide_up' else 'out_of'
            enriched.extend(self._make_slide(note, start, dur, vel, slide_name, events, idx))
            return True

        if technique == 'tap' and tapping_enabled:
            interval_range = profile.get('tapping', {}).get('interval_range', (7, 15))
            enriched.extend(self._make_tapping(note, start, dur, vel, interval_range, scale_notes))
            return True

        if technique == 'tap' and not tapping_enabled:
            # Tapping not enabled for this style — treat as normal fast note
            return False

        if technique == 'hammer_on':
            # Handled in process() which consumes the run
            return True  # Signal that technique was recognized

        if technique == 'pull_off':
            return True  # Same — handled by run consumer

        if technique == 'palm_mute':
            v_cut = profile.get('palm_mute', {}).get('velocity_cut', 0.65)
            enriched.append({
                'type': 'note',
                'note': note,
                'start': start,
                'duration': max(TICKS_PER_BEAT // 8, int(dur * 0.4)),
                'velocity': max(1, int(vel * v_cut)),
            })
            return True

        if technique == 'staccato':
            factor = profile.get('staccato', {}).get('duration_factor', 0.30)
            enriched.append({
                'type': 'note',
                'note': note,
                'start': start,
                'duration': max(TICKS_PER_BEAT // 8, int(dur * factor)),
                'velocity': vel,
            })
            return True

        if technique == 'legato':
            # Extend previous note to overlap
            overlap = profile.get('legato', {}).get('overlap_ticks', 30)
            for prev in reversed(enriched):
                if prev.get('type', 'note') == 'note':
                    prev['duration'] += overlap
                    break
            enriched.append({
                'type': 'note',
                'note': note,
                'start': start,
                'duration': dur,
                'velocity': max(1, vel - random.randint(0, 8)),
            })
            return True

        return False

    # =================================================================
    # Conservative fallback random application
    # =================================================================
    def _fallback_random(
        self, note, start, dur, vel,
        enriched, events, idx, n,
        profile, scale_notes,
        bend_prob_override, hammer_prob_override,
        vibrato_intensity, tapping_enabled,
    ):
        """
        Apply a single random technique with LOW probability.
        Uses halved probabilities compared to the technique profile
        to keep things conservative.
        """
        DAMPEN = 0.4  # Multiply all probabilities by this factor

        # Only attempt on longer notes for bends / vibrato
        bend_cfg = profile.get('bend', {})
        bend_prob = bend_prob_override if bend_prob_override is not None else bend_cfg.get('prob', 0)
        bend_prob *= DAMPEN
        if bend_prob > 0 and dur >= MIN_DUR_BEND and random.random() < bend_prob:
            variants = bend_cfg.get('variants', ['half'])
            enriched.extend(self._make_bend(note, start, dur, vel, random.choice(variants)))
            return True

        vib_cfg = profile.get('vibrato', {})
        vib_prob = vib_cfg.get('prob', 0) * DAMPEN
        if vibrato_intensity > 0:
            vib_prob = max(vib_prob, vibrato_intensity * 0.3)
        if vib_prob > 0 and dur >= MIN_DUR_VIBRATO and random.random() < vib_prob:
            enriched.extend(self._make_vibrato(note, start, dur, vel,
                                                vib_cfg.get('profile', 'standard')))
            return True

        slide_cfg = profile.get('slide', {})
        slide_prob = slide_cfg.get('prob', 0) * DAMPEN
        if slide_prob > 0 and dur >= MIN_DUR_SLIDE and random.random() < slide_prob:
            variants = slide_cfg.get('variants', ['into'])
            enriched.extend(self._make_slide(note, start, dur, vel,
                                              random.choice(variants), events, idx))
            return True

        return False

    # =================================================================
    # Run collectors for hammer-on / pull-off
    # =================================================================
    def _collect_technique_run(self, events: List[Dict], start_idx: int, technique: str) -> List[Dict]:
        """Collect consecutive notes that share the same technique hint."""
        run = [events[start_idx]]
        for j in range(start_idx + 1, min(start_idx + 6, len(events))):
            if events[j].get('technique') == technique:
                run.append(events[j])
            else:
                break
        return run

    def _collect_run(
        self, events: List[Dict], start_idx: int, max_len: int, direction: str
    ) -> List[Dict]:
        """Collect ascending/descending runs for fallback mode."""
        run = [events[start_idx]]
        for j in range(start_idx + 1, min(start_idx + max_len, len(events))):
            prev = run[-1]['note']
            curr = events[j]['note']
            if direction == 'up' and curr > prev:
                run.append(events[j])
            elif direction == 'down' and curr < prev:
                run.append(events[j])
            else:
                break
        return run

    # =================================================================
    # TECHNIQUE IMPLEMENTATIONS (unchanged MIDI logic)
    # =================================================================

    def _make_bend(
        self, note: int, start: int, dur: int, vel: int, bend_name: str
    ) -> List[Dict]:
        """Generate pitch-bend events for a string bend."""
        bp = BEND_PROFILES.get(bend_name, BEND_PROFILES['half'])
        semitones = bp['semitones']
        attack_ticks = bp['attack_ticks']
        release_ticks = bp['release_ticks']
        hold = bp.get('hold', True)
        pre_bent = bp.get('pre_bent', False)
        steps = bp['steps']
        events: List[Dict] = []

        events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': max(0, start - 1)})

        if pre_bent:
            events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones), 'time': start})
            events.append({'type': 'note', 'note': note, 'start': start, 'duration': dur, 'velocity': vel})
            if release_ticks > 0:
                release_start = start + dur - release_ticks
                for s in range(steps):
                    t = release_start + int(release_ticks * s / steps)
                    frac = 1.0 - (s / steps)
                    events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones * frac), 'time': t})
            events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': start + dur})
        else:
            events.append({'type': 'note', 'note': note, 'start': start, 'duration': dur, 'velocity': vel})
            bend_dur = min(attack_ticks, dur // 2)
            for s in range(steps):
                t = start + int(bend_dur * s / steps)
                frac = s / steps
                events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones * frac), 'time': t})
            events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones), 'time': start + bend_dur})

            if not hold and release_ticks > 0:
                rel_start = start + bend_dur + max(0, dur // 4)
                for s in range(steps):
                    t = rel_start + int(release_ticks * s / steps)
                    frac = 1.0 - (s / steps)
                    events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones * frac), 'time': t})
            events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': start + dur})

        return events

    def _make_vibrato(
        self, note: int, start: int, dur: int, vel: int, profile_name: str
    ) -> List[Dict]:
        """Generate CC1 modulation + pitch-bend vibrato."""
        vp = VIBRATO_PROFILES.get(profile_name, VIBRATO_PROFILES['standard'])
        delay = vp['delay_ticks']
        depth_cents = vp['depth_cents']
        rate_hz = vp['rate_hz']
        cc1_max = vp['cc1_max']
        events: List[Dict] = []

        events.append({'type': 'note', 'note': note, 'start': start, 'duration': dur, 'velocity': vel})

        vib_start = start + delay
        vib_dur = dur - delay
        if vib_dur < TICKS_PER_BEAT // 8:
            return events

        ramp_ticks = min(TICKS_PER_BEAT // 4, vib_dur // 4)
        ramp_steps = 4
        for s in range(ramp_steps):
            t = vib_start + int(ramp_ticks * s / ramp_steps)
            val = int(cc1_max * (s / ramp_steps))
            events.append({'type': 'control_change', 'control': 1, 'value': min(127, val), 'time': t})
        events.append({'type': 'control_change', 'control': 1, 'value': min(127, cc1_max), 'time': vib_start + ramp_ticks})

        semitone_depth = depth_cents / 100.0
        period_ticks = int(TICKS_PER_BEAT * 2 / rate_hz) if rate_hz > 0 else 0
        if period_ticks > 0:
            t = vib_start + ramp_ticks
            while t < start + dur:
                phase = ((t - vib_start) % period_ticks) / period_ticks
                wobble = math.sin(phase * 2 * math.pi) * semitone_depth
                events.append({'type': 'pitchbend', 'value': _semitones_to_pb(wobble), 'time': t})
                t += max(1, period_ticks // 6)

        end = start + dur
        events.append({'type': 'control_change', 'control': 1, 'value': 0, 'time': end})
        events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': end})

        return events

    def _make_slide(
        self, note: int, start: int, dur: int, vel: int,
        slide_name: str, events_list: List[Dict], idx: int
    ) -> List[Dict]:
        """Generate pitch-bend slide into or out of a note."""
        sp = SLIDE_PROFILES.get(slide_name, SLIDE_PROFILES['into'])
        semitones = sp['semitones']
        slide_dur = min(sp['duration_ticks'], dur // 3)
        steps = sp['steps']
        direction = sp['direction']
        events: List[Dict] = []

        if direction == 'auto' and idx > 0:
            prev_note = events_list[idx - 1].get('note', note)
            direction = 'up' if note > prev_note else 'down'
        elif direction == 'auto':
            direction = random.choice(['up', 'down'])

        if slide_name in ('into', 'glissando'):
            offset = semitones if direction == 'up' else -semitones
            events.append({'type': 'pitchbend', 'value': _semitones_to_pb(-offset), 'time': max(0, start - 1)})
            events.append({'type': 'note', 'note': note, 'start': start, 'duration': dur, 'velocity': vel})
            for s in range(steps + 1):
                t = start + int(slide_dur * s / steps)
                frac = s / steps
                current_offset = -offset * (1.0 - frac)
                events.append({'type': 'pitchbend', 'value': _semitones_to_pb(current_offset), 'time': t})
            events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': start + slide_dur})
        else:
            events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': max(0, start - 1)})
            events.append({'type': 'note', 'note': note, 'start': start, 'duration': dur, 'velocity': vel})
            slide_start = start + dur - slide_dur
            offset = semitones if direction == 'down' else -semitones
            for s in range(steps + 1):
                t = slide_start + int(slide_dur * s / steps)
                frac = s / steps
                events.append({'type': 'pitchbend', 'value': _semitones_to_pb(-offset * frac), 'time': t})
            events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': start + dur})

        return events

    def _make_hammer_on_run(self, run: List[Dict], profile: dict) -> List[Dict]:
        """Hammer-on: ascending legato notes, first picked, rest hammered."""
        events: List[Dict] = []
        overlap = profile.get('legato', {}).get('overlap_ticks', 25)

        for idx, evt in enumerate(run):
            n = evt['note']
            s = evt['start']
            d = evt['duration']
            v = evt.get('velocity', 80)

            if idx == 0:
                events.append({
                    'type': 'note', 'note': n, 'start': s,
                    'duration': d + overlap, 'velocity': v,
                })
            else:
                events.append({
                    'type': 'note', 'note': n, 'start': s,
                    'duration': d + (overlap if idx < len(run) - 1 else 0),
                    'velocity': max(1, v - random.randint(8, 20)),
                })
        return events

    def _make_pull_off_run(self, run: List[Dict], profile: dict) -> List[Dict]:
        """Pull-off: descending legato notes, first picked, rest pulled."""
        events: List[Dict] = []
        overlap = profile.get('legato', {}).get('overlap_ticks', 25)

        for idx, evt in enumerate(run):
            n = evt['note']
            s = evt['start']
            d = evt['duration']
            v = evt.get('velocity', 80)

            if idx == 0:
                events.append({
                    'type': 'note', 'note': n, 'start': s,
                    'duration': d + overlap, 'velocity': v,
                })
            else:
                events.append({
                    'type': 'note', 'note': n, 'start': s,
                    'duration': max(TICKS_PER_BEAT // 8, int(d * 0.85)),
                    'velocity': max(1, v - random.randint(10, 25)),
                })
        return events

    def _make_tapping(
        self, base_note: int, start: int, dur: int, vel: int,
        interval_range: Tuple[int, int], scale_notes: Optional[Set[int]]
    ) -> List[Dict]:
        """Two-hand tapping: alternating base and high tapped note."""
        events: List[Dict] = []
        lo, hi = interval_range
        tap_interval = random.randint(lo, hi)
        tapped_note = base_note + tap_interval

        if scale_notes:
            closest = min(scale_notes, key=lambda x: abs(x - tapped_note))
            if abs(closest - tapped_note) <= 2:
                tapped_note = closest

        tap_dur = TICKS_PER_BEAT // 4
        t = start
        is_base = True
        while t < start + dur:
            remaining = start + dur - t
            note_dur = min(tap_dur, remaining)
            if note_dur < TICKS_PER_BEAT // 8:
                break
            n = base_note if is_base else tapped_note
            v = vel if is_base else max(1, vel - random.randint(5, 15))
            events.append({
                'type': 'note', 'note': n, 'start': t,
                'duration': max(TICKS_PER_BEAT // 8, int(note_dur * 0.85)),
                'velocity': v,
            })
            t += note_dur
            is_base = not is_base

        return events
