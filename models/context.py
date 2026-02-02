"""
Class definition for SongContext - the musical "State" of the composition.
These dataclasses represent the "Contract" that all generators must obey.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BarContext:
    """
    Represents a single measure/bar of music.
    
    Attributes:
        bar_index: The position of this bar in the song (0-indexed)
        chord_name: The chord for this bar (e.g., "Am", "C", "G7")
        chord_type: The type of chord (e.g., "min", "maj", "dom7")
        root_note: The MIDI note number of the chord root
        root_name: The note name of the root (e.g., "A", "C")
        scale_type: The scale type for this bar (e.g., "minor", "major")
        scale_notes: List of valid MIDI notes in the scale (for melody filtering)
    """
    bar_index: int
    chord_name: str
    chord_type: str = "maj"
    root_note: int = 60
    root_name: str = "C"
    scale_type: str = "major"
    scale_notes: List[int] = field(default_factory=list)
    
    def __repr__(self):
        return f"Bar({self.bar_index}: {self.chord_name})"


@dataclass
class SongContext:
    """
    Represents the global state of the entire song.
    This is the central data structure passed between all generators.
    
    Attributes:
        mood: The selected mood (e.g., "happy", "sad", "rock")
        bpm: Tempo in beats per minute
        key: The musical key (e.g., "C", "Am")
        key_root_midi: MIDI note number of the key root
        scale_type: Primary scale type for the song
        time_signature: Tuple of (beats_per_bar, beat_unit)
        total_bars: Total number of bars in the song
        timeline: List of BarContext objects for each bar
        instruments: Dictionary of instrument assignments
        drum_style: The drum pattern style to use
        harmony_style: How harmony should be played
    """
    mood: str
    bpm: int
    key: str
    key_root_midi: int = 60
    scale_type: str = "major"
    time_signature: tuple = (4, 4)
    total_bars: int = 16
    timeline: List[BarContext] = field(default_factory=list)
    instruments: dict = field(default_factory=dict)
    drum_style: str = "pop"
    harmony_style: str = "rhythmic"
    
    def get_bar(self, index: int) -> Optional[BarContext]:
        """Get a specific bar by index."""
        if 0 <= index < len(self.timeline):
            return self.timeline[index]
        return None
    
    def get_current_chord_at_tick(self, tick: int, ticks_per_bar: int) -> Optional[BarContext]:
        """Get the bar context at a specific tick position."""
        bar_index = tick // ticks_per_bar
        return self.get_bar(bar_index)
    
    def __repr__(self):
        return (f"SongContext(mood={self.mood}, key={self.key}, "
                f"bpm={self.bpm}, bars={self.total_bars})")
