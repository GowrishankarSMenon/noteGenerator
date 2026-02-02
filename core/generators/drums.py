"""
Logic for generating drum patterns and beat structures.
Creates the rhythmic foundation - outputs MIDI events for Channel 10 (Drums).
"""

import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.context import SongContext
from config.settings import (
    DRUM_PATTERNS, DRUM_FILL, DRUM_NOTES, TICKS_PER_BEAT, DRUM_VELOCITY
)


class DrumsGenerator:
    """
    Generates drum patterns including kick, snare, hi-hats, etc.
    """
    
    def __init__(self):
        self.ticks_per_16th = TICKS_PER_BEAT // 4  # 120 ticks at 480 TPB
    
    def generate(self, ctx: SongContext) -> List[Dict]:
        """
        Generate drum patterns based on the song context.
        
        Args:
            ctx: The SongContext defining tempo and structure
            
        Returns:
            List of MIDI note events for drums
        """
        events = []
        
        # Get drum pattern for this style
        style = ctx.drum_style
        pattern = DRUM_PATTERNS.get(style, DRUM_PATTERNS['pop'])
        
        # Calculate timing
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]  # 4 beats per bar
        
        # Generate for each bar
        for bar_idx in range(ctx.total_bars):
            bar_start = bar_idx * ticks_per_bar
            
            # Check if this is the last bar of a 4-bar phrase (for fill)
            is_fill_bar = (bar_idx + 1) % 4 == 0 and bar_idx > 0
            
            if is_fill_bar:
                # Play fill pattern
                events.extend(self._generate_bar(bar_start, DRUM_FILL))
            else:
                # Play normal pattern
                events.extend(self._generate_bar(bar_start, pattern))
            
            # Add crash on first beat of first bar and after fills
            if bar_idx == 0 or (bar_idx % 4 == 0 and bar_idx > 0):
                if 'crash' in DRUM_NOTES:
                    events.append({
                        'note': DRUM_NOTES['crash'],
                        'start': bar_start,
                        'duration': self.ticks_per_16th * 2,
                        'velocity': DRUM_VELOCITY
                    })
        
        return events
    
    def _generate_bar(self, bar_start: int, pattern: Dict) -> List[Dict]:
        """
        Generate drum events for a single bar.
        
        Args:
            bar_start: Start time of the bar in ticks
            pattern: Dict mapping drum names to 16-step patterns
            
        Returns:
            List of drum events for this bar
        """
        events = []
        
        for drum_name, steps in pattern.items():
            if drum_name not in DRUM_NOTES:
                continue
            
            note_num = DRUM_NOTES[drum_name]
            
            for step_idx, hit in enumerate(steps):
                if hit:
                    step_time = bar_start + (step_idx * self.ticks_per_16th)
                    
                    # Vary velocity slightly for humanization
                    velocity = DRUM_VELOCITY
                    if drum_name == 'closed_hihat':
                        velocity = 70 if step_idx % 2 == 0 else 60
                    elif drum_name == 'snare':
                        velocity = 100
                    elif drum_name == 'kick':
                        velocity = 110
                    
                    events.append({
                        'note': note_num,
                        'start': step_time,
                        'duration': self.ticks_per_16th,
                        'velocity': velocity
                    })
        
        return events
    
    def get_kick_timestamps(self, ctx: SongContext) -> List[int]:
        """
        Get timestamps of all kick drum hits.
        Used by bass generator to lock to the groove.
        
        Args:
            ctx: Song context
            
        Returns:
            List of tick timestamps where kick drum hits
        """
        kicks = []
        style = ctx.drum_style
        pattern = DRUM_PATTERNS.get(style, DRUM_PATTERNS['pop'])
        kick_pattern = pattern.get('kick', [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0])
        
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        
        for bar_idx in range(ctx.total_bars):
            bar_start = bar_idx * ticks_per_bar
            
            for step_idx, hit in enumerate(kick_pattern):
                if hit:
                    kicks.append(bar_start + (step_idx * self.ticks_per_16th))
        
        return kicks
