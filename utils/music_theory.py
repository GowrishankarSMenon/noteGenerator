"""
Helper functions for music theory operations.
Conversions between note names and MIDI numbers.
"""

# MIDI note number for middle C
MIDDLE_C = 60

# Note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def note_to_midi(note_name, octave=4):
    """
    Convert a note name and octave to MIDI number.
    
    Args:
        note_name (str): Note name (e.g., 'C', 'C#', 'D')
        octave (int): Octave number (middle C is octave 4)
        
    Returns:
        int: MIDI note number
    """
    if note_name not in NOTE_NAMES:
        raise ValueError(f"Invalid note name: {note_name}")
    
    note_index = NOTE_NAMES.index(note_name)
    return (octave + 1) * 12 + note_index


def midi_to_note(midi_number):
    """
    Convert MIDI number to note name and octave.
    
    Args:
        midi_number (int): MIDI note number
        
    Returns:
        tuple: (note_name, octave)
    """
    octave = (midi_number // 12) - 1
    note_index = midi_number % 12
    note_name = NOTE_NAMES[note_index]
    return note_name, octave


def transpose(midi_number, semitones):
    """
    Transpose a MIDI note by a given number of semitones.
    
    Args:
        midi_number (int): Original MIDI note number
        semitones (int): Number of semitones to transpose (positive or negative)
        
    Returns:
        int: Transposed MIDI note number
    """
    return max(0, min(127, midi_number + semitones))
