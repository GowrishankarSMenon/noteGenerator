"""
Logic for generating drum patterns and beat structures.
Creates the rhythmic foundation - outputs MIDI events for Channel 10 (Drums).
Includes varied rock patterns inspired by legendary drummers.

Section-aware:
  - Intro: sparse kick/ride only, low velocity
  - Verse: standard pattern at moderate velocity
  - Chorus: full pattern with open hi-hats, higher velocity
  - Bridge: half-time or simplified pattern
  - Outro: gradual fade (decreasing velocity)
  - Transition bars get drum fills automatically
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

# Sparse intro pattern — kick on 1 and gentle ride
_INTRO_PATTERN = {
    'kick':  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'ride':  [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
}

# Half-time bridge pattern
_BRIDGE_PATTERN = {
    'kick':         [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'snare':        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    'closed_hihat': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
}

# Section-build fill (cymbal swell + toms)
_SECTION_TRANSITION_FILL = {
    'snare':   [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1],
    'tom_low': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    'tom_mid': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    'tom_high':[0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    'crash':   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
}


class DrumsGenerator:
    """
    Generates drum patterns including kick, snare, hi-hats, etc.
    Features varied rock patterns inspired by Bonham, Rudd, Copeland, etc.
    Supports 3 style modes: Auto (mood-based), Random, Manual Selection.

    Section-aware: adjusts pattern density, velocity, and fills
    according to `bar.section` and `bar.energy`.
    """
    
    def __init__(self):
        self.ticks_per_16th = TICKS_PER_BEAT // 4  # 120 ticks at 480 TPB
        self.current_pattern = None
        self.current_pattern_name = None
        self._forced_style = None
        self._style_mode = 'auto'
    
    def set_style(self, mode: str = 'auto', style_name: str = None):
        self._style_mode = mode
        self._forced_style = style_name if mode == 'selection' else None
        print(f"[Drums] Style mode set to: {mode}" + (f" ({style_name})" if style_name else ""))
    
    def generate(self, ctx: SongContext) -> List[Dict]:
        events: List[Dict] = []
        
        # Resolve main pattern (the "verse" pattern)
        style = ctx.drum_style
        pattern = self._resolve_pattern(style)

        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]

        prev_section = None

        for bar_idx in range(ctx.total_bars):
            bar = ctx.timeline[bar_idx]
            bar_start = bar_idx * ticks_per_bar
            section = bar.section
            energy = bar.energy

            # ---------- Section-dependent pattern selection ----------
            if bar.is_transition:
                # Transition bar → drum fill
                fill_pat = self._pick_fill(style)
                events.extend(self._generate_bar(bar_start, fill_pat, is_fill=True,
                                                  velocity_scale=energy))
            elif section == 'intro':
                events.extend(self._generate_bar(bar_start, _INTRO_PATTERN,
                                                  velocity_scale=energy))
            elif section == 'bridge':
                events.extend(self._generate_bar(bar_start, _BRIDGE_PATTERN,
                                                  velocity_scale=energy))
            elif section == 'chorus':
                # Full pattern + open hi-hat on beat 2/4
                events.extend(self._generate_bar(bar_start, pattern,
                                                  velocity_scale=energy))
                # Add open hi-hat accents in chorus
                for beat in [1, 3]:
                    oh_time = bar_start + beat * TICKS_PER_BEAT
                    events.append({
                        'note': DRUM_NOTES.get('open_hihat', 46),
                        'start': oh_time,
                        'duration': self.ticks_per_16th * 2,
                        'velocity': int(DRUM_VELOCITY * energy),
                    })
            elif section == 'outro':
                # Progressively thinner outro
                if energy < 0.15:
                    # Almost silent — just ride taps
                    events.extend(self._generate_bar(bar_start, _INTRO_PATTERN,
                                                      velocity_scale=energy))
                else:
                    events.extend(self._generate_bar(bar_start, pattern,
                                                      velocity_scale=energy))
            else:
                # verse / default
                is_fill_bar = (bar.section_bar + 1) % 4 == 0 and bar.section_bar > 0
                if is_fill_bar:
                    fill_pat = self._pick_fill(style)
                    events.extend(self._generate_bar(bar_start, fill_pat,
                                                      is_fill=True, velocity_scale=energy))
                else:
                    events.extend(self._generate_bar(bar_start, pattern,
                                                      velocity_scale=energy))

            # ---------- Crash cymbal on first bar of each section ----------
            if section != prev_section:
                if section not in ('intro',):
                    events.append({
                        'note': DRUM_NOTES['crash'],
                        'start': bar_start,
                        'duration': self.ticks_per_16th * 4,
                        'velocity': min(127, int(DRUM_VELOCITY * energy) + 15),
                    })
            prev_section = section
        
        return events

    # ------------------------------------------------------------------
    # Pattern resolution
    # ------------------------------------------------------------------
    def _resolve_pattern(self, style: str) -> dict:
        """Resolve the main verse pattern based on style mode."""
        pattern = None

        if self._style_mode == 'selection' and self._forced_style:
            forced = self._forced_style
            for rp in ROCK_DRUM_PATTERNS:
                if rp.get('name') == forced:
                    pattern = {k: v for k, v in rp.items() if k != 'name'}
                    self.current_pattern_name = forced
                    style = 'rock'
                    print(f"[Drums] Using selected rock pattern: {forced}")
                    break
            if pattern is None:
                pattern = DRUM_PATTERNS.get(forced, DRUM_PATTERNS['pop'])
                self.current_pattern_name = forced
                print(f"[Drums] Using selected standard pattern: {forced}")
        elif self._style_mode == 'random':
            all_patterns = list(DRUM_PATTERNS.keys()) + [p['name'] for p in ROCK_DRUM_PATTERNS]
            choice = random.choice(all_patterns)
            for rp in ROCK_DRUM_PATTERNS:
                if rp.get('name') == choice:
                    pattern = {k: v for k, v in rp.items() if k != 'name'}
                    self.current_pattern_name = choice
                    print(f"[Drums] Random pick: {choice}")
                    break
            if pattern is None:
                pattern = DRUM_PATTERNS.get(choice, DRUM_PATTERNS['pop'])
                self.current_pattern_name = choice
                print(f"[Drums] Random pick: {choice}")
        else:
            if style == 'rock' and ROCK_DRUM_PATTERNS:
                selected_pattern = random.choice(ROCK_DRUM_PATTERNS)
                self.current_pattern_name = selected_pattern.get('name', 'rock')
                pattern = {k: v for k, v in selected_pattern.items() if k != 'name'}
                print(f"[Drums] Auto selected rock pattern: {self.current_pattern_name}")
            else:
                pattern = DRUM_PATTERNS.get(style, DRUM_PATTERNS['pop'])
                self.current_pattern_name = style

        self.current_pattern = pattern
        return pattern

    def _pick_fill(self, style: str) -> dict:
        """Pick a drum fill appropriate for the style."""
        if style == 'rock' and ROCK_DRUM_FILLS:
            fill = random.choice(ROCK_DRUM_FILLS)
            return {k: v for k, v in fill.items() if k != 'name'}
        return _SECTION_TRANSITION_FILL

    # ------------------------------------------------------------------
    # Bar renderer
    # ------------------------------------------------------------------
    def _generate_bar(
        self, bar_start: int, pattern: Dict,
        is_fill: bool = False,
        velocity_scale: float = 1.0,
    ) -> List[Dict]:
        events: List[Dict] = []
        
        for drum_name, steps in pattern.items():
            if drum_name not in DRUM_NOTES:
                continue
            
            note_num = DRUM_NOTES[drum_name]
            
            for step_idx, hit in enumerate(steps):
                if hit:
                    step_time = bar_start + (step_idx * self.ticks_per_16th)
                    
                    velocity = DRUM_VELOCITY
                    if drum_name == 'closed_hihat':
                        velocity = 70 if step_idx % 2 == 0 else 60
                    elif drum_name == 'open_hihat':
                        velocity = 80
                    elif drum_name == 'ride':
                        velocity = 65
                    elif drum_name == 'snare':
                        velocity = 100
                    elif drum_name == 'kick':
                        velocity = 110
                    
                    # Scale by section energy
                    velocity = max(30, min(127, int(velocity * velocity_scale)))
                    
                    events.append({
                        'note': note_num,
                        'start': step_time,
                        'duration': self.ticks_per_16th,
                        'velocity': velocity
                    })
        
        return events
    
    def get_kick_timestamps(self, ctx: SongContext) -> List[int]:
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