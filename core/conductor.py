"""
PLANNER: Creates the SongContext (Key, Chords, Structure).
The Conductor determines what the song is before any notes are generated.
"""

import random
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.context import SongContext, BarContext
from config.settings import MOOD_CONFIGS, TICKS_PER_BEAT
from utils.music_theory import (
    parse_key, roman_to_chord, get_scale_notes, name_to_midi, NOTE_NAMES
)


class Conductor:
    """
    The Conductor is responsible for high-level musical planning.
    It creates the overall song structure, key, and chord progression.
    """
    
    def __init__(self):
        self.available_moods = list(MOOD_CONFIGS.keys())
    
    def create_song_context(
        self,
        mood: str,
        length_in_bars: int = 16,
        bpm: Optional[int] = None,
        key: Optional[str] = None
    ) -> SongContext:
        """
        Create and return a SongContext object with key, chords, and structure.
        
        Args:
            mood: The desired mood (e.g., "happy", "sad", "rock")
            length_in_bars: Total number of bars in the song
            bpm: Override BPM (uses mood default if None)
            key: Override key (uses mood default if None)
            
        Returns:
            SongContext: The planned musical context
        """
        # Validate mood
        if mood not in MOOD_CONFIGS:
            print(f"Unknown mood '{mood}', defaulting to 'happy'")
            mood = 'happy'
        
        config = MOOD_CONFIGS[mood]
        
        # Select BPM
        if bpm is None:
            bpm_min, bpm_max = config['bpm_range']
            bpm = random.randint(bpm_min, bpm_max)
        
        # Select Key
        if key is None:
            key = random.choice(config['key_options'])
        
        # Parse key info
        root_name, key_root_midi, scale_type = parse_key(key)
        
        # Override scale type from mood config if specified
        mood_scale = config.get('scale_type', scale_type)
        
        # Select chord progression
        progression = random.choice(config['chord_progressions'])
        
        # Determine if minor key
        is_minor_key = key.endswith('m') or mood_scale in ['minor', 'dorian']
        
        # Build timeline
        timeline = self._build_timeline(
            progression=progression,
            key_root_midi=key_root_midi,
            is_minor_key=is_minor_key,
            scale_type=mood_scale,
            total_bars=length_in_bars
        )
        
        # Create context
        ctx = SongContext(
            mood=mood,
            bpm=bpm,
            key=key,
            key_root_midi=key_root_midi,
            scale_type=mood_scale,
            time_signature=(4, 4),
            total_bars=length_in_bars,
            timeline=timeline,
            instruments=config['instruments'],
            drum_style=config['drum_style'],
            harmony_style=config['harmony_style']
        )
        
        print(f"Conductor created: {ctx}")
        print(f"  Progression: {' -> '.join([bar.chord_name for bar in timeline[:4]])}")
        
        return ctx
    
    def _build_timeline(
        self,
        progression: list,
        key_root_midi: int,
        is_minor_key: bool,
        scale_type: str,
        total_bars: int
    ) -> list:
        """
        Build the bar-by-bar timeline for the song.
        
        Args:
            progression: List of Roman numeral chords
            key_root_midi: MIDI note of the key root
            is_minor_key: Whether we're in a minor key
            scale_type: Scale type to use
            total_bars: Total number of bars
            
        Returns:
            List of BarContext objects
        """
        timeline = []
        bars_per_chord = max(1, total_bars // (len(progression) * 4))
        
        for bar_idx in range(total_bars):
            # Determine which chord in the progression
            chord_idx = (bar_idx // bars_per_chord) % len(progression)
            roman = progression[chord_idx]
            
            # Convert Roman numeral to actual chord
            chord_name, root_midi, chord_type = roman_to_chord(
                roman, key_root_midi, is_minor_key
            )
            
            # Get root name
            root_name = NOTE_NAMES[root_midi % 12]
            
            # Get valid scale notes for this bar (for melody filtering)
            scale_notes = list(get_scale_notes(root_midi, scale_type))
            
            bar = BarContext(
                bar_index=bar_idx,
                chord_name=chord_name,
                chord_type=chord_type,
                root_note=root_midi,
                root_name=root_name,
                scale_type=scale_type,
                scale_notes=scale_notes
            )
            
            timeline.append(bar)
        
        return timeline
    
    def get_available_moods(self) -> list:
        """Return list of available moods."""
        return self.available_moods
