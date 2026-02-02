"""
Wrapper for FluidSynth audio synthesis.
Bridges the MIDI output to audio playback and rendering.
"""

import subprocess
import os
import sys
import platform

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SOUNDFONT_PATH, OUTPUT_DIR, SAMPLE_RATE


class AudioEngine:
    """
    Handles audio synthesis using FluidSynth.
    Wraps the FluidSynth command-line interface.
    """
    
    def __init__(self, soundfont_path: str = None):
        """
        Initialize the audio engine.
        
        Args:
            soundfont_path: Path to SoundFont file (uses default if None)
        """
        self.soundfont_path = soundfont_path or SOUNDFONT_PATH
        self._check_fluidsynth()
    
    def _check_fluidsynth(self) -> bool:
        """Check if FluidSynth is available."""
        try:
            result = subprocess.run(
                ['fluidsynth', '--version'],
                capture_output=True,
                text=True
            )
            self.fluidsynth_available = result.returncode == 0
        except FileNotFoundError:
            self.fluidsynth_available = False
            print("Warning: FluidSynth not found. Audio rendering will be unavailable.")
            print("Install FluidSynth: https://www.fluidsynth.org/")
        return self.fluidsynth_available
    
    def _check_soundfont(self) -> bool:
        """Check if SoundFont file exists."""
        if not os.path.exists(self.soundfont_path):
            print(f"Warning: SoundFont not found at {self.soundfont_path}")
            print("Please download FluidR3_GM.sf2 and place it in assets/fonts/")
            return False
        return True
    
    def render_to_wav(self, midi_path: str, output_path: str = None) -> str:
        """
        Render a MIDI file to WAV using FluidSynth.
        
        Args:
            midi_path: Path to input MIDI file
            output_path: Path for output WAV file (auto-generated if None)
            
        Returns:
            Path to the rendered WAV file, or None if failed
        """
        if not self.fluidsynth_available:
            print("FluidSynth not available. Cannot render audio.")
            return None
        
        if not self._check_soundfont():
            return None
        
        if not os.path.exists(midi_path):
            print(f"MIDI file not found: {midi_path}")
            return None
        
        # Generate output path if not provided
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(midi_path))[0]
            output_path = os.path.join(OUTPUT_DIR, f"{base_name}.wav")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            cmd = [
                'fluidsynth',
                '-ni',                      # No interactive mode
                '-g', '1.0',                # Gain
                '-r', str(SAMPLE_RATE),     # Sample rate
                '-F', output_path,          # Output file
                self.soundfont_path,        # SoundFont
                midi_path                   # Input MIDI
            ]
            
            print(f"Rendering audio: {midi_path} -> {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Audio rendered successfully: {output_path}")
                return output_path
            else:
                print(f"FluidSynth error: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error rendering audio: {e}")
            return None
    
    def play_midi(self, midi_path: str):
        """
        Play a MIDI file using FluidSynth (real-time playback).
        
        Args:
            midi_path: Path to MIDI file
        """
        if not self.fluidsynth_available:
            print("FluidSynth not available. Cannot play audio.")
            self._try_system_player(midi_path)
            return
        
        if not self._check_soundfont():
            return
        
        if not os.path.exists(midi_path):
            print(f"MIDI file not found: {midi_path}")
            return
        
        try:
            # Determine audio driver based on OS
            system = platform.system()
            if system == 'Windows':
                audio_driver = 'dsound'
            elif system == 'Darwin':  # macOS
                audio_driver = 'coreaudio'
            else:  # Linux
                audio_driver = 'pulseaudio'
            
            cmd = [
                'fluidsynth',
                '-a', audio_driver,
                '-g', '1.0',
                self.soundfont_path,
                midi_path
            ]
            
            print(f"Playing: {midi_path}")
            subprocess.run(cmd)
            
        except Exception as e:
            print(f"Error playing MIDI: {e}")
            self._try_system_player(midi_path)
    
    def play_wav(self, wav_path: str):
        """
        Play a WAV file using the system's default player.
        
        Args:
            wav_path: Path to WAV file
        """
        if not os.path.exists(wav_path):
            print(f"WAV file not found: {wav_path}")
            return
        
        try:
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(wav_path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['afplay', wav_path])
            else:  # Linux
                subprocess.run(['aplay', wav_path])
                
        except Exception as e:
            print(f"Error playing WAV: {e}")
    
    def _try_system_player(self, midi_path: str):
        """Try to play MIDI using system's default handler."""
        try:
            system = platform.system()
            if system == 'Windows':
                os.startfile(midi_path)
            elif system == 'Darwin':
                subprocess.run(['open', midi_path])
            else:
                subprocess.run(['xdg-open', midi_path])
        except Exception as e:
            print(f"Could not open MIDI file: {e}")
