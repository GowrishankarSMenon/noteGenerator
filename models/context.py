"""
Class definition for SongContext - the musical "State" of the composition.
"""


class SongContext:
    """
    Represents the complete musical context for song generation.
    
    Attributes:
        key (str): The musical key (e.g., 'C', 'Am')
        scale (list): List of scale degrees
        bpm (int): Tempo in beats per minute
        chord_progression (list): List of chords for the song
        structure (list): Song structure sections (e.g., ['intro', 'verse', 'chorus'])
        time_signature (tuple): Time signature (numerator, denominator)
    """
    
    def __init__(self, key='C', scale=None, bpm=120, chord_progression=None,
                 structure=None, time_signature=(4, 4)):
        self.key = key
        self.scale = scale or [0, 2, 4, 5, 7, 9, 11]  # Major scale default
        self.bpm = bpm
        self.chord_progression = chord_progression or []
        self.structure = structure or ['intro', 'verse', 'chorus', 'verse', 'chorus', 'outro']
        self.time_signature = time_signature
    
    def __repr__(self):
        return f"SongContext(key={self.key}, bpm={self.bpm}, chords={len(self.chord_progression)})"
