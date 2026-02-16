"""
Guitar effects processor — converts plain note events into expressive
MIDI events with pitch bends, CC messages, overlapping notes, etc.

This module takes a list of basic note dicts (note, start, duration, velocity)
and returns an enriched list that may include additional 'pitchbend' and
'control_change' events alongside the modified note events.

Event types produced:
    {'type': 'note', 'note': int, 'start': int, 'duration': int, 'velocity': int}
    {'type': 'pitchbend', 'value': int, 'time': int}          # -8192..+8191
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


# MIDI pitch-bend range assumed: +/- 2 semitones (GM default)
PB_RANGE_SEMITONES = 2
PB_MAX = 8191                           # Max positive pitch-bend value
PB_CENTER = 0                           # No bend


def _semitones_to_pb(semitones: float) -> int:
    """Convert a semitone offset to a MIDI pitch-bend value."""
    return int((semitones / PB_RANGE_SEMITONES) * PB_MAX)


class GuitarEffectsProcessor:
    """
    Post-processes a lead track to inject guitar articulations.

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

        Args:
            events:      Raw note events from LeadGenerator.
            style:       The current sub-style dict from lead_styles.
            scale_notes: Set of valid MIDI pitches (for tapping targets).

        Returns:
            Enriched event list (may be longer than input due to added
            pitch-bend / CC / extra tapping notes).
        """
        if not events:
            return events

        articulation = style.get('articulation', 'medium')
        profile = get_technique_profile(articulation)

        # Override probabilities with any per-style explicit values
        bend_prob_override = style.get('bend_probability')
        hammer_prob_override = style.get('hammer_on_probability')
        vibrato_intensity = style.get('vibrato_intensity', 0)
        tapping_enabled = style.get('tapping', False)

        enriched: List[Dict] = []
        # We need lookahead/behind so iterate by index
        n = len(events)
        i = 0

        while i < n:
            evt = events[i]
            note = evt['note']
            start = evt['start']
            dur = evt['duration']
            vel = evt.get('velocity', 80)

            applied = False  # Track whether a technique was applied

            # ------------------------------------------------------------------
            # 1. BENDING
            # ------------------------------------------------------------------
            bend_cfg = profile.get('bend', {})
            bend_prob = bend_prob_override if bend_prob_override is not None else bend_cfg.get('prob', 0)
            if bend_prob > 0 and random.random() < bend_prob and dur >= TICKS_PER_BEAT // 4:
                variants = bend_cfg.get('variants', ['half'])
                bend_name = random.choice(variants)
                bend_events = self._make_bend(note, start, dur, vel, bend_name)
                enriched.extend(bend_events)
                applied = True

            # ------------------------------------------------------------------
            # 2. VIBRATO  (adds CC1 modulation wheel + optional pitch-bend wobble)
            # ------------------------------------------------------------------
            if not applied:
                vib_cfg = profile.get('vibrato', {})
                vib_prob = vib_cfg.get('prob', 0)
                # Boost probability based on style's vibrato_intensity
                if vibrato_intensity > 0:
                    vib_prob = max(vib_prob, vibrato_intensity * 0.6)
                if vib_prob > 0 and random.random() < vib_prob and dur >= TICKS_PER_BEAT // 2:
                    vib_profile_name = vib_cfg.get('profile', 'standard')
                    vib_events = self._make_vibrato(note, start, dur, vel, vib_profile_name)
                    enriched.extend(vib_events)
                    applied = True

            # ------------------------------------------------------------------
            # 3. HAMMER-ON / PULL-OFF  (consecutive legato notes)
            # ------------------------------------------------------------------
            if not applied:
                ho_cfg = profile.get('hammer_on', {})
                po_cfg = profile.get('pull_off', {})
                ho_prob = hammer_prob_override if hammer_prob_override is not None else ho_cfg.get('prob', 0)
                po_prob = po_cfg.get('prob', 0)

                # Hammer-on: ascending pair (current < next)
                if ho_prob > 0 and i + 1 < n and random.random() < ho_prob:
                    next_evt = events[i + 1]
                    if next_evt['note'] > note:
                        max_run = ho_cfg.get('max_run', 3)
                        run = self._collect_run(events, i, max_run, direction='up')
                        ho_events = self._make_hammer_on_run(run, profile)
                        enriched.extend(ho_events)
                        i += len(run)
                        continue

                # Pull-off: descending pair (current > next)
                if po_prob > 0 and i + 1 < n and random.random() < po_prob:
                    next_evt = events[i + 1]
                    if next_evt['note'] < note:
                        max_run = po_cfg.get('max_run', 3)
                        run = self._collect_run(events, i, max_run, direction='down')
                        po_events = self._make_pull_off_run(run, profile)
                        enriched.extend(po_events)
                        i += len(run)
                        continue

            # ------------------------------------------------------------------
            # 4. TAPPING  (interleave high tapped notes)
            # ------------------------------------------------------------------
            if not applied and tapping_enabled:
                tap_cfg = profile.get('tapping', {})
                tap_prob = tap_cfg.get('prob', 0)
                if tapping_enabled:
                    tap_prob = max(tap_prob, 0.30)
                if tap_prob > 0 and random.random() < tap_prob and dur >= TICKS_PER_BEAT // 4:
                    interval_range = tap_cfg.get('interval_range', (7, 15))
                    tap_events = self._make_tapping(
                        note, start, dur, vel, interval_range, scale_notes
                    )
                    enriched.extend(tap_events)
                    applied = True

            # ------------------------------------------------------------------
            # 5. SLIDE INTO NOTE
            # ------------------------------------------------------------------
            if not applied:
                slide_cfg = profile.get('slide', {})
                slide_prob = slide_cfg.get('prob', 0)
                if slide_prob > 0 and random.random() < slide_prob and dur >= TICKS_PER_BEAT // 4:
                    variants = slide_cfg.get('variants', ['into'])
                    slide_name = random.choice(variants)
                    slide_events = self._make_slide(note, start, dur, vel, slide_name, events, i)
                    enriched.extend(slide_events)
                    applied = True

            # ------------------------------------------------------------------
            # 6. STACCATO  (shorten note, reduce sustain)
            # ------------------------------------------------------------------
            if not applied:
                stac_cfg = profile.get('staccato', {})
                stac_prob = stac_cfg.get('prob', 0)
                if stac_prob > 0 and random.random() < stac_prob:
                    factor = stac_cfg.get('duration_factor', 0.30)
                    enriched.append({
                        'type': 'note',
                        'note': note,
                        'start': start,
                        'duration': max(TICKS_PER_BEAT // 8, int(dur * factor)),
                        'velocity': vel,
                    })
                    applied = True

            # ------------------------------------------------------------------
            # 7. LEGATO OVERLAP (extend previous note to overlap into this one)
            # ------------------------------------------------------------------
            if not applied:
                leg_cfg = profile.get('legato', {})
                leg_prob = leg_cfg.get('prob', 0)
                if leg_prob > 0 and random.random() < leg_prob and len(enriched) > 0:
                    overlap = leg_cfg.get('overlap_ticks', 30)
                    # Extend previous note's duration to overlap
                    for prev in reversed(enriched):
                        if prev.get('type', 'note') == 'note':
                            prev['duration'] = prev['duration'] + overlap
                            break
                    enriched.append({
                        'type': 'note',
                        'note': note,
                        'start': start,
                        'duration': dur,
                        'velocity': max(1, vel - random.randint(0, 8)),
                    })
                    applied = True

            # ------------------------------------------------------------------
            # 8. PALM MUTE (lower velocity, shorter note)
            # ------------------------------------------------------------------
            if not applied:
                pm_cfg = profile.get('palm_mute', {})
                pm_prob = pm_cfg.get('prob', 0)
                if pm_prob > 0 and random.random() < pm_prob:
                    v_cut = pm_cfg.get('velocity_cut', 0.65)
                    enriched.append({
                        'type': 'note',
                        'note': note,
                        'start': start,
                        'duration': max(TICKS_PER_BEAT // 8, int(dur * 0.4)),
                        'velocity': max(1, int(vel * v_cut)),
                    })
                    applied = True

            # ------------------------------------------------------------------
            # Fallback: unchanged note
            # ------------------------------------------------------------------
            if not applied:
                enriched.append({
                    'type': 'note',
                    'note': note,
                    'start': start,
                    'duration': dur,
                    'velocity': vel,
                })

            i += 1

        # Reset pitch bend at the very end
        if any(e.get('type') == 'pitchbend' for e in enriched):
            last_time = max(
                (e.get('start', 0) + e.get('duration', 0) if e.get('type') == 'note'
                 else e.get('time', 0))
                for e in enriched
            )
            enriched.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': last_time})

        return enriched

    # =====================================================================
    # TECHNIQUE IMPLEMENTATIONS
    # =====================================================================

    def _make_bend(
        self, note: int, start: int, dur: int, vel: int, bend_name: str
    ) -> List[Dict]:
        """Generate pitch-bend events for a string bend."""
        profile = BEND_PROFILES.get(bend_name, BEND_PROFILES['half'])
        semitones = profile['semitones']
        attack_ticks = profile['attack_ticks']
        release_ticks = profile['release_ticks']
        hold = profile.get('hold', True)
        pre_bent = profile.get('pre_bent', False)
        steps = profile['steps']
        events: List[Dict] = []

        # Reset PB before the note
        events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': max(0, start - 1)})

        if pre_bent:
            # Start at bent pitch, release down
            events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones), 'time': start})
            events.append({'type': 'note', 'note': note, 'start': start, 'duration': dur, 'velocity': vel})
            # Release bend
            if release_ticks > 0:
                release_start = start + dur - release_ticks
                for s in range(steps):
                    t = release_start + int(release_ticks * s / steps)
                    frac = 1.0 - (s / steps)
                    events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones * frac), 'time': t})
            events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': start + dur})
        else:
            # Normal bend: start flat, bend up
            events.append({'type': 'note', 'note': note, 'start': start, 'duration': dur, 'velocity': vel})
            bend_dur = min(attack_ticks, dur // 2)
            for s in range(steps):
                t = start + int(bend_dur * s / steps)
                frac = s / steps
                events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones * frac), 'time': t})
            # Peak
            events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones), 'time': start + bend_dur})

            if not hold and release_ticks > 0:
                rel_start = start + bend_dur + max(0, dur // 4)
                for s in range(steps):
                    t = rel_start + int(release_ticks * s / steps)
                    frac = 1.0 - (s / steps)
                    events.append({'type': 'pitchbend', 'value': _semitones_to_pb(semitones * frac), 'time': t})
            # Reset at note end
            events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': start + dur})

        return events

    def _make_vibrato(
        self, note: int, start: int, dur: int, vel: int, profile_name: str
    ) -> List[Dict]:
        """Generate CC1 (mod wheel) + optional pitch-bend vibrato."""
        profile = VIBRATO_PROFILES.get(profile_name, VIBRATO_PROFILES['standard'])
        delay = profile['delay_ticks']
        depth_cents = profile['depth_cents']
        rate_hz = profile['rate_hz']
        cc1_max = profile['cc1_max']
        events: List[Dict] = []

        # The note itself
        events.append({'type': 'note', 'note': note, 'start': start, 'duration': dur, 'velocity': vel})

        # Modulation wheel (CC1) ramp-up then sustain
        vib_start = start + delay
        vib_dur = dur - delay
        if vib_dur < TICKS_PER_BEAT // 8:
            return events  # Too short for vibrato

        # CC1 envelope: quick ramp up, sustain, quick ramp down
        ramp_ticks = min(TICKS_PER_BEAT // 4, vib_dur // 4)
        # Ramp up
        ramp_steps = 4
        for s in range(ramp_steps):
            t = vib_start + int(ramp_ticks * s / ramp_steps)
            val = int(cc1_max * (s / ramp_steps))
            events.append({'type': 'control_change', 'control': 1, 'value': min(127, val), 'time': t})
        # Sustain
        events.append({'type': 'control_change', 'control': 1, 'value': min(127, cc1_max), 'time': vib_start + ramp_ticks})

        # Pitch-bend wobble for more realism
        semitone_depth = depth_cents / 100.0
        period_ticks = int(TICKS_PER_BEAT * 2 / rate_hz)  # Approx period in ticks
        if period_ticks > 0:
            t = vib_start + ramp_ticks
            while t < start + dur:
                phase = ((t - vib_start) % period_ticks) / period_ticks
                wobble = math.sin(phase * 2 * math.pi) * semitone_depth
                events.append({'type': 'pitchbend', 'value': _semitones_to_pb(wobble), 'time': t})
                t += max(1, period_ticks // 6)

        # Reset at note end
        end = start + dur
        events.append({'type': 'control_change', 'control': 1, 'value': 0, 'time': end})
        events.append({'type': 'pitchbend', 'value': PB_CENTER, 'time': end})

        return events

    def _make_slide(
        self, note: int, start: int, dur: int, vel: int,
        slide_name: str, events_list: List[Dict], idx: int
    ) -> List[Dict]:
        """Generate pitch-bend slide into or out of a note."""
        profile = SLIDE_PROFILES.get(slide_name, SLIDE_PROFILES['into'])
        semitones = profile['semitones']
        slide_dur = min(profile['duration_ticks'], dur // 3)
        steps = profile['steps']
        direction = profile['direction']
        events: List[Dict] = []

        if direction == 'auto' and idx > 0:
            prev_note = events_list[idx - 1]['note']
            direction = 'up' if note > prev_note else 'down'
        elif direction == 'auto':
            direction = random.choice(['up', 'down'])

        if slide_name in ('into', 'glissando'):
            # Slide INTO: start low/high, glide to target
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
            # Slide OUT: start on pitch, slide away
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

    def _collect_run(
        self, events: List[Dict], start_idx: int, max_len: int, direction: str
    ) -> List[Dict]:
        """Collect a run of ascending (up) or descending (down) notes."""
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

    def _make_hammer_on_run(self, run: List[Dict], profile: dict) -> List[Dict]:
        """
        Hammer-on: ascending notes with
         - first note at full velocity (picked)
         - following notes slightly softer (hammered)
         - notes overlap slightly for legato feel
        """
        events: List[Dict] = []
        overlap = profile.get('legato', {}).get('overlap_ticks', 25)

        for idx, evt in enumerate(run):
            note = evt['note']
            start = evt['start']
            dur = evt['duration']
            vel = evt.get('velocity', 80)

            if idx == 0:
                # First note: picked normally
                events.append({
                    'type': 'note', 'note': note, 'start': start,
                    'duration': dur + overlap, 'velocity': vel,
                })
            else:
                # Hammered: softer, overlaps with previous
                events.append({
                    'type': 'note', 'note': note, 'start': start,
                    'duration': dur + (overlap if idx < len(run) - 1 else 0),
                    'velocity': max(1, vel - random.randint(8, 20)),
                })
        return events

    def _make_pull_off_run(self, run: List[Dict], profile: dict) -> List[Dict]:
        """
        Pull-off: descending notes with
         - first note at full velocity (picked)
         - following notes softer (pulled off)
         - notes overlap slightly
        """
        events: List[Dict] = []
        overlap = profile.get('legato', {}).get('overlap_ticks', 25)

        for idx, evt in enumerate(run):
            note = evt['note']
            start = evt['start']
            dur = evt['duration']
            vel = evt.get('velocity', 80)

            if idx == 0:
                events.append({
                    'type': 'note', 'note': note, 'start': start,
                    'duration': dur + overlap, 'velocity': vel,
                })
            else:
                # Pulled-off note: softer, slightly less sustain
                events.append({
                    'type': 'note', 'note': note, 'start': start,
                    'duration': max(TICKS_PER_BEAT // 8, int(dur * 0.85)),
                    'velocity': max(1, vel - random.randint(10, 25)),
                })
        return events

    def _make_tapping(
        self, base_note: int, start: int, dur: int, vel: int,
        interval_range: Tuple[int, int], scale_notes: Optional[Set[int]]
    ) -> List[Dict]:
        """
        Two-hand tapping: interleave the base note with a high tapped note.
        Creates a rapid alternating pattern within the note's duration.
        """
        events: List[Dict] = []
        lo, hi = interval_range
        tap_interval = random.randint(lo, hi)
        tapped_note = base_note + tap_interval

        # If we have scale notes, snap the tapped note
        if scale_notes:
            closest = min(scale_notes, key=lambda x: abs(x - tapped_note))
            if abs(closest - tapped_note) <= 2:
                tapped_note = closest

        # Rapid alternation
        tap_dur = TICKS_PER_BEAT // 4  # 16th notes
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
