"""
Logic for generating drum patterns and beat structures.
Creates the rhythmic foundation - outputs MIDI events for Channel 10 (Drums).
Includes varied rock patterns inspired by legendary drummers.
"""

import sys
import os
import random
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.context import SongContext
from config.settings import (
    DRUM_PATTERNS, DRUM_FILL, DRUM_NOTES, TICKS_PER_BEAT, DRUM_VELOCITY
)
from config.drum_patterns import ROCK_DRUM_PATTERNS, ROCK_DRUM_FILLS


class DrumsGenerator:
    """
    Generates drum patterns including kick, snare, hi-hats, etc.
    Features varied rock patterns inspired by Bonham, Rudd, Copeland, etc.
    Supports 3 style modes: Auto (mood-based), Random, Manual Selection.
    """
    
    def __init__(self):
        self.ticks_per_16th = TICKS_PER_BEAT // 4  # 120 ticks at 480 TPB
        self.current_pattern = None
        self.current_pattern_name = None
        self._forced_style = None  # Set via set_style() for manual selection
        self._style_mode = 'auto'  # 'auto', 'random', or 'selection'
    
    def set_style(self, mode: str = 'auto', style_name: str = None):
        """
        Set the style selection mode for drum generation.
        
        Args:
            mode: 'auto' (mood-based), 'random' (any style), 'selection' (user picks)
            style_name: Specific style name when mode='selection'
        """
        self._style_mode = mode
        self._forced_style = style_name if mode == 'selection' else None
        print(f"[Drums] Style mode set to: {mode}" + (f" ({style_name})" if style_name else ""))
    
    def generate(self, ctx: SongContext) -> List[Dict]:
        """
        Generate drum patterns based on the song context.
        
        Args:
            ctx: The SongContext defining tempo and structure
            
        Returns:
            List of MIDI note events for drums
        """
        events = []
        
        # Resolve drum style based on mode
        style = ctx.drum_style
        pattern = None
        
        if self._style_mode == 'selection' and self._forced_style:
            # User manually selected a specific style
            forced = self._forced_style
            # Check if it's a rock pattern name
            for rp in ROCK_DRUM_PATTERNS:
                if rp.get('name') == forced:
                    pattern = {k: v for k, v in rp.items() if k != 'name'}
                    self.current_pattern_name = forced
                    style = 'rock'  # Treat as rock for fills
                    print(f"[Drums] Using selected rock pattern: {forced}")
                    break
            if pattern is None:
                # Standard style name (pop, ballad, jazz, electronic, soft)
                pattern = DRUM_PATTERNS.get(forced, DRUM_PATTERNS['pop'])
                self.current_pattern_name = forced
                style = forced
                print(f"[Drums] Using selected standard pattern: {forced}")
        elif self._style_mode == 'random':
            # Random: pick any style from all available
            all_patterns = list(DRUM_PATTERNS.keys()) + [p['name'] for p in ROCK_DRUM_PATTERNS]
            choice = random.choice(all_patterns)
            for rp in ROCK_DRUM_PATTERNS:
                if rp.get('name') == choice:
                    pattern = {k: v for k, v in rp.items() if k != 'name'}
                    self.current_pattern_name = choice
                    style = 'rock'
                    print(f"[Drums] Random pick: {choice}")
                    break
            if pattern is None:
                pattern = DRUM_PATTERNS.get(choice, DRUM_PATTERNS['pop'])
                self.current_pattern_name = choice
                style = choice
                print(f"[Drums] Random pick: {choice}")
        else:
            # Auto mode: original mood-based behavior
            if style == 'rock' and ROCK_DRUM_PATTERNS:
                selected_pattern = random.choice(ROCK_DRUM_PATTERNS)
                self.current_pattern_name = selected_pattern.get('name', 'rock')
                pattern = {k: v for k, v in selected_pattern.items() if k != 'name'}
                print(f"[Drums] Auto selected rock pattern: {self.current_pattern_name}")
            else:
                pattern = DRUM_PATTERNS.get(style, DRUM_PATTERNS['pop'])
                self.current_pattern_name = style
        
        self.current_pattern = pattern
        
        # Calculate timing
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]  # 4 beats per bar
        
        # For rock, we may change patterns every 8 bars for variety
        pattern_change_interval = 8 if style == 'rock' else 999
        
        # Generate for each bar
        for bar_idx in range(ctx.total_bars):
            bar_start = bar_idx * ticks_per_bar
            
            # Change rock pattern periodically for variety
            if style == 'rock' and bar_idx > 0 and bar_idx % pattern_change_interval == 0:
                if random.random() < 0.5:  # 50% chance to switch patterns
                    selected_pattern = random.choice(ROCK_DRUM_PATTERNS)
                    pattern = {k: v for k, v in selected_pattern.items() if k != 'name'}
                    self.current_pattern = pattern
            
            # Check if this is the last bar of a 4-bar phrase (for fill)
            is_fill_bar = (bar_idx + 1) % 4 == 0 and bar_idx > 0
            
            if is_fill_bar:
                # For rock, use varied fills
                if style == 'rock' and ROCK_DRUM_FILLS:
                    fill = random.choice(ROCK_DRUM_FILLS)
                    fill_pattern = {k: v for k, v in fill.items() if k != 'name'}
                    events.extend(self._generate_bar(bar_start, fill_pattern, is_fill=True))
                else:
                    events.extend(self._generate_bar(bar_start, DRUM_FILL, is_fill=True))
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
                        'velocity': DRUM_VELOCITY + random.randint(0, 15)
                    })
        
        return events
    
    def _generate_bar(self, bar_start: int, pattern: Dict, is_fill: bool = False) -> List[Dict]:
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


