"""
Logic for generating harmonic content including chords and pads.
The chordal backing (Piano/Pad/Rhythm Guitar).

Section-aware:
  - Intro: sparse sustained open voicing, low velocity
  - Verse: standard style (rhythmic/arpeggiated/voicing per mood)
  - Chorus: fuller voicings, chord inversions, higher velocity
  - Bridge: sustained pads only (contrast from verse/chorus)
  - Outro: sustained, fading velocity
  - Transition bars: rolled chord / arpeggio sweep
"""

import sys
import os
import random
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.context import SongContext, BarContext
from config.settings import TICKS_PER_BEAT, DEFAULT_VELOCITY
from utils.music_theory import get_chord_notes


class HarmonyGenerator:
    """
    Generates chords, pads, and harmonic accompaniment.
    Adapts voicing density and rhythm to the current section.
    """
    
    def __init__(self):
        self.chord_octave = 4

    def generate(self, ctx: SongContext, bass_track: List[Dict]) -> List[Dict]:
        events: List[Dict] = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        style = ctx.harmony_style

        for bar in ctx.timeline:
            bar_start = bar.bar_index * ticks_per_bar
            section = bar.section
            energy = bar.energy
            vel = max(35, int(DEFAULT_VELOCITY * energy))

            root = (bar.root_note % 12) + (12 * (self.chord_octave + 1))
            chord_notes = get_chord_notes(root, bar.chord_type)

            if bar.is_transition:
                # Rolled arpeggio sweep leading into next section
                events.extend(self._rolled_chord(
                    chord_notes, bar_start, ticks_per_bar, vel + 5
                ))
            elif section == 'intro':
                # Sparse sustained open chord
                events.extend(self._sustained_bar(
                    chord_notes, bar_start, ticks_per_bar, max(35, vel - 15)
                ))
            elif section == 'bridge':
                # Sustained pads for contrast
                events.extend(self._sustained_bar(
                    chord_notes, bar_start, ticks_per_bar, vel
                ))
            elif section == 'outro':
                events.extend(self._sustained_bar(
                    chord_notes, bar_start, ticks_per_bar, vel
                ))
            elif section == 'chorus':
                # Fuller: add octave doubling, use main style
                full_notes = chord_notes + [n + 12 for n in chord_notes[:1]]
                events.extend(self._section_style(
                    full_notes, bar_start, ticks_per_bar, style, vel + 5
                ))
            else:
                # verse: standard style
                events.extend(self._section_style(
                    chord_notes, bar_start, ticks_per_bar, style, vel
                ))

        return events

    # ------------------------------------------------------------------
    # Style dispatchers
    # ------------------------------------------------------------------
    def _section_style(
        self, chord_notes, bar_start, ticks_per_bar, style, vel
    ) -> List[Dict]:
        if style == 'sustained':
            return self._sustained_bar(chord_notes, bar_start, ticks_per_bar, vel)
        elif style == 'rhythmic':
            return self._rhythmic_bar(chord_notes, bar_start, ticks_per_bar, vel)
        elif style == 'arpeggiated':
            return self._arpeggiated_bar(chord_notes, bar_start, ticks_per_bar, vel)
        elif style == 'power':
            return self._power_bar(chord_notes, bar_start, ticks_per_bar, vel)
        elif style == 'voicing':
            return self._jazz_voicing_bar(chord_notes, bar_start, ticks_per_bar, vel)
        else:
            return self._sustained_bar(chord_notes, bar_start, ticks_per_bar, vel)

    # ------------------------------------------------------------------
    # Bar-level generators
    # ------------------------------------------------------------------
    def _sustained_bar(self, chord_notes, bar_start, ticks_per_bar, vel) -> List[Dict]:
        events: List[Dict] = []
        for note in chord_notes:
            events.append({
                'note': note,
                'start': bar_start,
                'duration': ticks_per_bar - 10,
                'velocity': vel,
            })
        return events

    def _rhythmic_bar(self, chord_notes, bar_start, ticks_per_bar, vel) -> List[Dict]:
        events: List[Dict] = []
        pattern = [1, 0, 1, 0, 1, 0, 1, 0]
        ticks_per_8th = TICKS_PER_BEAT // 2
        for step_idx, hit in enumerate(pattern):
            if hit:
                step_time = bar_start + step_idx * ticks_per_8th
                accent = vel if step_idx % 4 == 0 else vel - 15
                for note in chord_notes:
                    events.append({
                        'note': note,
                        'start': step_time,
                        'duration': ticks_per_8th - 20,
                        'velocity': max(30, accent),
                    })
        return events

    def _arpeggiated_bar(self, chord_notes, bar_start, ticks_per_bar, vel) -> List[Dict]:
        events: List[Dict] = []
        ticks_per_8th = TICKS_PER_BEAT // 2
        note_idx = 0
        for step in range(8):
            step_time = bar_start + step * ticks_per_8th
            note = chord_notes[note_idx % len(chord_notes)]
            events.append({
                'note': note,
                'start': step_time,
                'duration': ticks_per_8th - 10,
                'velocity': vel - 10,
            })
            note_idx += 1 if step < 4 else -1
        return events

    def _power_bar(self, chord_notes, bar_start, ticks_per_bar, vel) -> List[Dict]:
        events: List[Dict] = []
        pattern = [1, 0, 0, 1, 1, 0, 1, 0]
        ticks_per_8th = TICKS_PER_BEAT // 2
        root = chord_notes[0]
        power = [root, root + 7, root + 12]
        for step_idx, hit in enumerate(pattern):
            if hit:
                step_time = bar_start + step_idx * ticks_per_8th
                for note in power:
                    events.append({
                        'note': note,
                        'start': step_time,
                        'duration': ticks_per_8th - 10,
                        'velocity': vel + 10,
                    })
        return events

    def _jazz_voicing_bar(self, chord_notes, bar_start, ticks_per_bar, vel) -> List[Dict]:
        events: List[Dict] = []
        root = chord_notes[0]
        voicing = [root + 3, root + 10, root + 14]  # rootless
        hits = [(0, 1.0), (TICKS_PER_BEAT * 2 + TICKS_PER_BEAT // 2, 0.5)]
        for offset, dur_mult in hits:
            hit_time = bar_start + offset
            duration = int(TICKS_PER_BEAT * dur_mult)
            for note in voicing:
                events.append({
                    'note': note,
                    'start': hit_time,
                    'duration': duration,
                    'velocity': vel - 15,
                })
        return events

    def _rolled_chord(self, chord_notes, bar_start, ticks_per_bar, vel) -> List[Dict]:
        """Rolled/strummed chord — each note offset by a few ticks."""
        events: List[Dict] = []
        roll_gap = 40  # ticks between each note of the roll
        sorted_notes = sorted(chord_notes)
        for i, note in enumerate(sorted_notes):
            events.append({
                'note': note,
                'start': bar_start + i * roll_gap,
                'duration': ticks_per_bar - i * roll_gap - 10,
                'velocity': vel,
            })
        # Also add an octave root stab 2 beats before bar end for push
        events.append({
            'note': sorted_notes[0] + 12,
            'start': bar_start + ticks_per_bar - TICKS_PER_BEAT * 2,
            'duration': TICKS_PER_BEAT,
            'velocity': vel + 5,
        })
        return events
