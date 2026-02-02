"""
Utilities for rendering and saving MIDI files.
"""

import mido


class MidiRenderer:
    """
    Handles the creation and saving of MIDI files.
    """
    
    def __init__(self, bpm=120):
        """
        Initialize the MIDI renderer.
        
        Args:
            bpm (int): Tempo in beats per minute
        """
        self.bpm = bpm
        self.mid = mido.MidiFile()
    
    def create_track(self, name, events):
        """
        Create a MIDI track with the given events.
        
        Args:
            name (str): Track name
            events (list): List of MIDI events/notes
            
        Returns:
            mido.MidiTrack: The created track
        """
        track = mido.MidiTrack()
        track.name = name
        
        # Add tempo
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(self.bpm)))
        
        # Add events
        for event in events:
            track.append(event)
        
        return track
    
    def save(self, filename):
        """
        Save the MIDI file to disk.
        
        Args:
            filename (str): Path to save the MIDI file
        """
        self.mid.save(filename)
        print(f"MIDI file saved: {filename}")
