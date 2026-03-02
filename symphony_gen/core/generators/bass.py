"""
Logic for generating bass lines with root notes that lock to the kick drum.
The bridge between Rhythm and Harmony.
"""

import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.context import SongContext
from config.settings import TICKS_PER_BEAT, DEFAULT_VELOCITY, DRUM_NOTES


class BassGenerator:
    """
    Generates bass lines that follow chord progressions and sync with kick drum.
    """
    
    def __init__(self):
        self.bass_octave = 2  # Bass plays in octave 2-3
    
    def generate(self, ctx: SongContext, drum_track: List[Dict]) -> List[Dict]:
        """
        Generate bass line based on chords and drum patterns.
        
        Args:
            ctx: The SongContext with chord progression
            drum_track: Generated drum data to sync with kick
            
        Returns:
            List of MIDI events for bass
        """
        events = []
        
        # Get kick drum timestamps
        kick_times = self._get_kick_times(drum_track)
        
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        
        # Generate bass notes at kick positions
        for kick_time in kick_times:
            # Find which bar we're in
            bar_idx = kick_time // ticks_per_bar
            
            if bar_idx >= len(ctx.timeline):
                continue
            
            bar = ctx.timeline[bar_idx]
            
            # Get root note of current chord, transposed to bass octave
            root = bar.root_note
            bass_note = (root % 12) + (12 * (self.bass_octave + 1))
            
            # Determine duration (until next kick or end of bar)
            next_kicks = [k for k in kick_times if k > kick_time]
            bar_end = (bar_idx + 1) * ticks_per_bar
            
            if next_kicks:
                duration = min(next_kicks[0] - kick_time, bar_end - kick_time)
            else:
                duration = bar_end - kick_time
            
            # Shorten slightly for groove
            duration = int(duration * 0.9)
            duration = max(duration, TICKS_PER_BEAT // 4)  # Minimum duration
            
            events.append({
                'note': bass_note,
                'start': kick_time,
                'duration': duration,
                'velocity': DEFAULT_VELOCITY + 10
            })
        
        # Add occasional passing tones for more interesting bass lines
        events.extend(self._add_passing_tones(ctx, events, kick_times, ticks_per_bar))
        
        return events
    
    def _get_kick_times(self, drum_track: List[Dict]) -> List[int]:
        """Extract kick drum timestamps from drum track."""
        kick_note = DRUM_NOTES['kick']
        kicks = [event['start'] for event in drum_track if event['note'] == kick_note]
        return sorted(kicks)
    
    def _add_passing_tones(
        self,
        ctx: SongContext,
        existing_events: List[Dict],
        kick_times: List[int],
        ticks_per_bar: int
    ) -> List[Dict]:
        """
        Add passing tones between main bass notes for groove.
        
        Returns:
            Additional bass events for passing tones
        """
        passing_events = []
        
        # Add a note before each bar's first kick (approach note)
        for bar_idx in range(1, ctx.total_bars):
            bar_start = bar_idx * ticks_per_bar
            
            # Find first kick in this bar
            bar_kicks = [k for k in kick_times if bar_start <= k < bar_start + ticks_per_bar]
            if not bar_kicks:
                continue
            
            first_kick = bar_kicks[0]
            
            # Add approach note (half beat before)
            approach_time = first_kick - TICKS_PER_BEAT // 2
            if approach_time < 0:
                continue
            
            # Get previous and current bar root notes
            prev_bar = ctx.timeline[bar_idx - 1]
            curr_bar = ctx.timeline[bar_idx]
            
            prev_root = (prev_bar.root_note % 12) + (12 * (self.bass_octave + 1))
            curr_root = (curr_bar.root_note % 12) + (12 * (self.bass_octave + 1))
            
            # Approach note is one step above or below target
            if curr_root > prev_root:
                approach_note = curr_root - 2  # Step below
            else:
                approach_note = curr_root + 2  # Step above
            
            passing_events.append({
                'note': approach_note,
                'start': approach_time,
                'duration': TICKS_PER_BEAT // 4,
                'velocity': DEFAULT_VELOCITY - 10
            })
        
        return passing_events
