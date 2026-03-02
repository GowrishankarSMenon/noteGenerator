"""
Helper functions for music theory operations.
The "Brain" for musical translation - converts text-based music concepts into MIDI.
"""

from typing import List, Set, Tuple, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SCALES, CHORD_TYPES

# =============================================================================
# CONSTANTS
# =============================================================================

MIDDLE_C = 60
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NOTE_NAMES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

NOTE_TO_SEMITONE = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4, 'E#': 5,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11, 'Cb': 11, 'B#': 0,
}

ROMAN_TO_DEGREE = {
    'I': 0, 'i': 0,
    'II': 2, 'ii': 2, 'bII': 1,
    'III': 4, 'iii': 4, 'bIII': 3,
    'IV': 5, 'iv': 5,
    'V': 7, 'v': 7,
    'VI': 9, 'vi': 9, 'bVI': 8,
    'VII': 11, 'vii': 11, 'bVII': 10,
}


# =============================================================================
# NOTE CONVERSION FUNCTIONS
# =============================================================================

def name_to_midi(note_name: str) -> int:
    """Convert a note name (with optional octave) to MIDI number."""
    octave = 4
    name = note_name.strip()
    
    if name and name[-1].isdigit():
        if len(name) >= 2 and name[-2] == '-':
            octave = -int(name[-1])
            name = name[:-2]
        else:
            i = len(name) - 1
            while i > 0 and name[i-1].isdigit():
                i -= 1
            octave = int(name[i:])
            name = name[:i]
    
    if name not in NOTE_TO_SEMITONE:
        raise ValueError(f"Invalid note name: {note_name}")
    
    semitone = NOTE_TO_SEMITONE[name]
    return (octave + 1) * 12 + semitone


def midi_to_name(midi_number: int, use_sharps: bool = True) -> str:
    """Convert MIDI number to note name with octave."""
    octave = (midi_number // 12) - 1
    note_index = midi_number % 12
    
    if use_sharps:
        note_name = NOTE_NAMES[note_index]
    else:
        note_name = NOTE_NAMES_FLAT[note_index]
    
    return f"{note_name}{octave}"


def transpose(midi_number: int, semitones: int) -> int:
    """Transpose a MIDI note by a given number of semitones."""
    return max(0, min(127, midi_number + semitones))


# =============================================================================
# CHORD FUNCTIONS
# =============================================================================

def parse_chord_name(chord_name: str) -> Tuple[str, str]:
    """Parse a chord name into root and type."""
    name = chord_name.strip()
    
    if len(name) >= 2 and name[1] in '#b':
        root = name[:2]
        suffix = name[2:]
    else:
        root = name[0]
        suffix = name[1:]
    
    suffix_lower = suffix.lower()
    
    if suffix_lower in ('', 'maj', 'major'):
        chord_type = 'maj'
    elif suffix_lower in ('m', 'min', 'minor'):
        chord_type = 'min'
    elif suffix_lower in ('dim', 'o'):
        chord_type = 'dim'
    elif suffix_lower in ('aug', '+'):
        chord_type = 'aug'
    elif suffix_lower in ('7', 'dom7'):
        chord_type = 'dom7'
    elif suffix_lower in ('maj7', 'major7'):
        chord_type = 'maj7'
    elif suffix_lower in ('m7', 'min7', 'minor7'):
        chord_type = 'min7'
    elif suffix_lower in ('dim7', 'o7'):
        chord_type = 'dim7'
    elif suffix_lower == 'sus2':
        chord_type = 'sus2'
    elif suffix_lower == 'sus4':
        chord_type = 'sus4'
    else:
        chord_type = 'maj'
    
    return root, chord_type


def get_chord_notes(root_midi: int, chord_type: str = "maj") -> List[int]:
    """Get MIDI note numbers for a chord."""
    intervals = CHORD_TYPES.get(chord_type, CHORD_TYPES['maj'])
    return [root_midi + interval for interval in intervals]


def get_chord_notes_from_name(chord_name: str, octave: int = 4) -> List[int]:
    """Get MIDI note numbers for a chord by name."""
    root_name, chord_type = parse_chord_name(chord_name)
    root_midi = name_to_midi(f"{root_name}{octave}")
    return get_chord_notes(root_midi, chord_type)


# =============================================================================
# SCALE FUNCTIONS
# =============================================================================

def get_scale_notes(root_midi: int, scale_type: str = "major", octave_range: int = 2) -> Set[int]:
    """Get all valid MIDI notes in a scale across multiple octaves."""
    intervals = SCALES.get(scale_type, SCALES['major'])
    root_pc = root_midi % 12
    
    valid_notes = set()
    
    for midi_note in range(24, 108):
        note_pc = midi_note % 12
        relative_pc = (note_pc - root_pc) % 12
        if relative_pc in intervals:
            valid_notes.add(midi_note)
    
    return valid_notes


def get_scale_notes_in_octave(root_midi: int, scale_type: str = "major") -> List[int]:
    """Get scale notes within a single octave starting from root."""
    intervals = SCALES.get(scale_type, SCALES['major'])
    return [root_midi + interval for interval in intervals]


# =============================================================================
# KEY & CHORD PROGRESSION FUNCTIONS
# =============================================================================

def parse_key(key_name: str) -> Tuple[str, int, str]:
    """Parse a key name into components."""
    key = key_name.strip()
    
    if key.endswith('m') and not key.endswith('dim'):
        root = key[:-1]
        scale_type = 'minor'
    else:
        root = key
        scale_type = 'major'
    
    root_midi = name_to_midi(f"{root}4")
    
    return root, root_midi, scale_type


def roman_to_chord(roman: str, key_root_midi: int, is_minor_key: bool = False) -> Tuple[str, int, str]:
    """Convert a Roman numeral chord to actual chord name and MIDI root."""
    base_roman = roman.rstrip('7').rstrip('maj').rstrip('dim').rstrip('aug')
    
    interval = ROMAN_TO_DEGREE.get(base_roman, 0)
    root_midi = key_root_midi + interval
    root_name = NOTE_NAMES[root_midi % 12]
    
    is_lowercase = base_roman[0].islower() if base_roman else False
    
    if 'dim' in roman:
        chord_type = 'dim'
        chord_suffix = 'dim'
    elif 'aug' in roman:
        chord_type = 'aug'
        chord_suffix = 'aug'
    elif '7' in roman:
        if is_lowercase:
            chord_type = 'min7'
            chord_suffix = 'm7'
        else:
            chord_type = 'dom7'
            chord_suffix = '7'
    elif is_lowercase:
        chord_type = 'min'
        chord_suffix = 'm'
    else:
        chord_type = 'maj'
        chord_suffix = ''
    
    chord_name = f"{root_name}{chord_suffix}"
    
    return chord_name, root_midi, chord_type


def expand_progression(
    roman_numerals: List[str],
    key_root_midi: int,
    is_minor_key: bool = False,
    bars_per_chord: int = 1,
    total_bars: int = 16
) -> List[Tuple[str, int, str]]:
    """Expand a Roman numeral progression to fill the song length."""
    chords = [roman_to_chord(r, key_root_midi, is_minor_key) for r in roman_numerals]
    
    result = []
    
    for bar in range(total_bars):
        chord_in_pattern = (bar // bars_per_chord) % len(chords)
        result.append(chords[chord_in_pattern])
    
    return result
