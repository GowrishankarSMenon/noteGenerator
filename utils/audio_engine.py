"""
Wrapper for FluidSynth audio synthesis.
"""

import subprocess
import os
from config.settings import SOUNDFONT_PATH


class AudioEngine:
    """
    Handles audio synthesis using FluidSynth.
    """
    
    def __init__(self, soundfont_path=None):
        """
        Initialize the audio engine.
        
        Args:
            soundfont_path (str): Path to SoundFont file
        """
        self.soundfont_path = soundfont_path or SOUNDFONT_PATH
    
    def render_to_wav(self, midi_path, output_path):
        """
        Render a MIDI file to WAV using FluidSynth.
        
        Args:
            midi_path (str): Path to input MIDI file
            output_path (str): Path for output WAV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(self.soundfont_path):
            print(f"SoundFont not found: {self.soundfont_path}")
            return False
        
        try:
            cmd = [
                'fluidsynth',
                '-ni',
                self.soundfont_path,
                midi_path,
                '-F',
                output_path,
                '-r',
                '44100'
            ]
            
            subprocess.run(cmd, check=True)
            print(f"Audio rendered: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error rendering audio: {e}")
            return False
    
    def play_midi(self, midi_path):
        """
        Play a MIDI file using FluidSynth.
        
        Args:
            midi_path (str): Path to MIDI file
        """
        if not os.path.exists(self.soundfont_path):
            print(f"SoundFont not found: {self.soundfont_path}")
            return
        
        try:
            cmd = [
                'fluidsynth',
                '-a', 'alsa',
                '-m', 'alsa_seq',
                self.soundfont_path,
                midi_path
            ]
            
            subprocess.run(cmd)
            
        except Exception as e:
            print(f"Error playing MIDI: {e}")
