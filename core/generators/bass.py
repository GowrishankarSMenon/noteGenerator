"""
Logic for generating bass lines with root notes that lock to the kick drum.
The bridge between Rhythm and Harmony.

Section-aware:
  - Intro: whole-note root only (sparse)
  - Verse: lock to kick drum (standard)
  - Chorus: busier (extra passing tones, higher velocity)
  - Bridge: sustained root notes only
  - Outro: fade out
  - Transition bars: chromatic walk-up/down into next chord
"""

import sys
import os
import random
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.context import SongContext
from config.settings import TICKS_PER_BEAT, DEFAULT_VELOCITY, DRUM_NOTES


class BassGenerator:
    """
    Generates bass lines that follow chord progressions and sync with kick drum.
    Adapts density and velocity to each section's energy level.
    """
    
    def __init__(self):
        self.bass_octave = 2

    def generate(self, ctx: SongContext, drum_track: List[Dict]) -> List[Dict]:
        events: List[Dict] = []
        
        kick_times = self._get_kick_times(drum_track)
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        
        for bar in ctx.timeline:
            bar_start = bar.bar_index * ticks_per_bar
            bar_end = bar_start + ticks_per_bar
            section = bar.section
            energy = bar.energy
            bass_note = (bar.root_note % 12) + (12 * (self.bass_octave + 1))
            
            vel_base = max(40, int(DEFAULT_VELOCITY * energy))

            if section == 'intro':
                # Single whole note on the root
                events.append({
                    'note': bass_note,
                    'start': bar_start,
                    'duration': int(ticks_per_bar * 0.9),
                    'velocity': max(40, vel_base - 10),
                })
            elif section == 'bridge':
                # Half notes on root
                half = ticks_per_bar // 2
                for offset in [0, half]:
                    events.append({
                        'note': bass_note,
                        'start': bar_start + offset,
                        'duration': int(half * 0.85),
                        'velocity': vel_base,
                    })
            elif bar.is_transition:
                # Chromatic walk into next chord root
                events.extend(self._chromatic_walk(
                    bar, ctx.timeline, ticks_per_bar, vel_base
                ))
            elif section == 'outro':
                # Sparse root, fading
                events.append({
                    'note': bass_note,
                    'start': bar_start,
                    'duration': int(ticks_per_bar * 0.8),
                    'velocity': max(30, vel_base),
                })
            else:
                # verse / chorus: lock to kick
                bar_kicks = [k for k in kick_times if bar_start <= k < bar_end]
                if not bar_kicks:
                    bar_kicks = [bar_start]  # Fallback to downbeat

                for i, kick_time in enumerate(bar_kicks):
                    # Duration until next kick or bar end
                    next_times = [k for k in bar_kicks if k > kick_time]
                    dur_end = next_times[0] if next_times else bar_end
                    duration = int((dur_end - kick_time) * 0.9)
                    duration = max(duration, TICKS_PER_BEAT // 4)

                    events.append({
                        'note': bass_note,
                        'start': kick_time,
                        'duration': duration,
                        'velocity': vel_base + (10 if section == 'chorus' else 0),
                    })

                # Chorus gets extra passing tones between kicks
                if section == 'chorus' and len(bar_kicks) >= 2:
                    events.extend(self._add_passing_tones_bar(
                        bar, bar_kicks, ticks_per_bar, vel_base - 10
                    ))

        # Global approach notes (before bar boundaries of different chords)
        events.extend(self._add_approach_notes(ctx, kick_times, ticks_per_bar))

        return events

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_kick_times(self, drum_track: List[Dict]) -> List[int]:
        kick_note = DRUM_NOTES['kick']
        kicks = [e['start'] for e in drum_track if e['note'] == kick_note]
        return sorted(kicks)

    def _chromatic_walk(
        self, bar, timeline, ticks_per_bar: int, vel: int,
    ) -> List[Dict]:
        """Walk chromatically into the next bar's root."""
        events: List[Dict] = []
        bar_start = bar.bar_index * ticks_per_bar
        current_root = (bar.root_note % 12) + (12 * (self.bass_octave + 1))

        next_idx = bar.bar_index + 1
        if next_idx < len(timeline):
            target_root = (timeline[next_idx].root_note % 12) + (12 * (self.bass_octave + 1))
        else:
            target_root = current_root

        # 4-step walk occupying the whole bar
        steps = 4
        step_dur = ticks_per_bar // steps
        direction = 1 if target_root >= current_root else -1
        dist = abs(target_root - current_root)

        for s in range(steps):
            if dist == 0:
                note = current_root
            else:
                frac = s / max(1, steps - 1)
                note = current_root + int(round(frac * dist)) * direction
            events.append({
                'note': note,
                'start': bar_start + s * step_dur,
                'duration': int(step_dur * 0.85),
                'velocity': vel,
            })
        return events

    def _add_passing_tones_bar(
        self, bar, kicks: list, ticks_per_bar: int, vel: int,
    ) -> List[Dict]:
        """Add a passing tone between kicks on chorus bars."""
        events: List[Dict] = []
        root = (bar.root_note % 12) + (12 * (self.bass_octave + 1))
        fifth = root + 7

        for i in range(len(kicks) - 1):
            gap = kicks[i + 1] - kicks[i]
            if gap > TICKS_PER_BEAT:
                mid = kicks[i] + gap // 2
                events.append({
                    'note': fifth,
                    'start': mid,
                    'duration': int(gap * 0.3),
                    'velocity': vel,
                })
        return events

    def _add_approach_notes(
        self, ctx: SongContext, kick_times: List[int], ticks_per_bar: int,
    ) -> List[Dict]:
        passing_events: List[Dict] = []
        
        for bar_idx in range(1, ctx.total_bars):
            bar_start = bar_idx * ticks_per_bar
            bar = ctx.timeline[bar_idx]
            prev_bar = ctx.timeline[bar_idx - 1]
            
            # Skip if same chord or if in intro
            if bar.root_note == prev_bar.root_note:
                continue
            if bar.section == 'intro':
                continue
            
            approach_time = bar_start - TICKS_PER_BEAT // 2
            if approach_time < 0:
                continue
            
            curr_root = (bar.root_note % 12) + (12 * (self.bass_octave + 1))
            
            if random.random() < 0.5:
                approach_note = curr_root - 2
            else:
                approach_note = curr_root + 2
            
            passing_events.append({
                'note': approach_note,
                'start': approach_time,
                'duration': TICKS_PER_BEAT // 4,
                'velocity': max(40, int(DEFAULT_VELOCITY * bar.energy) - 10),
            })
        
        return passing_events
