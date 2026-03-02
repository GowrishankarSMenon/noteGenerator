"""
Wrapper for FluidSynth audio synthesis.
Uses pyfluidsynth library for MIDI-to-WAV rendering and pygame for playback.
Falls back to system CLI fluidsynth if pyfluidsynth is unavailable.
"""

import subprocess
import os
import sys
import platform
import wave
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SOUNDFONT_PATH, FLUIDSYNTH_DIR, OUTPUT_DIR, SAMPLE_RATE, DRUM_CHANNEL

# Register local FluidSynth DLL directory BEFORE importing pyfluidsynth.
# pyfluidsynth's module-level code calls os.add_dll_directory('C:\\tools\\fluidsynth\\bin')
# which crashes if that path doesn't exist. We pre-create it as an empty dir to
# prevent the FileNotFoundError, then register our real DLL path.
if platform.system() == 'Windows' and hasattr(os, 'add_dll_directory'):
    # Ensure the hardcoded pyfluidsynth path exists (even if empty) to avoid crash
    _hardcoded = r'C:\tools\fluidsynth\bin'
    os.makedirs(_hardcoded, exist_ok=True)
    # Register our bundled FluidSynth binaries
    if os.path.isdir(FLUIDSYNTH_DIR):
        os.add_dll_directory(FLUIDSYNTH_DIR)
        os.environ['PATH'] = FLUIDSYNTH_DIR + ';' + os.environ.get('PATH', '')


class AudioEngine:
    """
    Handles audio synthesis using pyfluidsynth (Python binding) or CLI FluidSynth.
    Also uses pygame for playback.
    """
    
    def __init__(self, soundfont_path: str = None):
        """
        Initialize the audio engine.
        
        Args:
            soundfont_path: Path to SoundFont file (uses default if None)
        """
        self.soundfont_path = soundfont_path or SOUNDFONT_PATH
        self.fluidsynth_available = False
        self.pyfluidsynth_available = False
        self.cli_fluidsynth_available = False
        self.pygame_available = False
        
        self._check_pyfluidsynth()
        self._check_cli_fluidsynth()
        self._check_pygame()
        
        # Overall availability
        self.fluidsynth_available = self.pyfluidsynth_available or self.cli_fluidsynth_available
        
        if self.fluidsynth_available:
            method = "pyfluidsynth" if self.pyfluidsynth_available else "CLI"
            print(f"✅ FluidSynth available via {method}")
        else:
            print("⚠️  FluidSynth not available. Audio rendering will be limited.")
    
    def _check_pyfluidsynth(self) -> bool:
        """Check if pyfluidsynth Python library is available."""
        try:
            import fluidsynth
            # Try to create a synth instance to verify the library loads
            fs = fluidsynth.Synth(samplerate=float(SAMPLE_RATE))
            fs.delete()
            self.pyfluidsynth_available = True
        except (ImportError, Exception):
            self.pyfluidsynth_available = False
        return self.pyfluidsynth_available
    
    def _check_cli_fluidsynth(self) -> bool:
        """Check if FluidSynth CLI is available on PATH."""
        try:
            result = subprocess.run(
                ['fluidsynth', '--version'],
                capture_output=True,
                text=True
            )
            self.cli_fluidsynth_available = result.returncode == 0
        except FileNotFoundError:
            self.cli_fluidsynth_available = False
        return self.cli_fluidsynth_available
    
    def _check_pygame(self) -> bool:
        """Check if pygame is available for playback."""
        try:
            import pygame
            self.pygame_available = True
        except ImportError:
            self.pygame_available = False
        return self.pygame_available
    
    def _check_soundfont(self) -> bool:
        """Check if SoundFont file exists."""
        if not os.path.exists(self.soundfont_path):
            print(f"Warning: SoundFont not found at {self.soundfont_path}")
            print("Please download FluidR3_GM.sf2 and place it in assets/fonts/")
            return False
        return True
    
    def render_to_wav(self, midi_path: str, output_path: str = None) -> str:
        """
        Render a MIDI file to WAV.
        Tries pyfluidsynth first, then CLI FluidSynth as fallback.
        
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
        
        # Try pyfluidsynth first (preferred - no PATH issues)
        if self.pyfluidsynth_available:
            result = self._render_with_pyfluidsynth(midi_path, output_path)
            if result:
                return result
            print("pyfluidsynth rendering failed, trying CLI...")
        
        # Fallback to CLI
        if self.cli_fluidsynth_available:
            return self._render_with_cli(midi_path, output_path)
        
        print("All rendering methods failed.")
        return None
    
    def _render_with_pyfluidsynth(self, midi_path: str, output_path: str) -> str:
        """Render MIDI to WAV using pyfluidsynth Python library."""
        try:
            import fluidsynth
            import mido
            
            print(f"Rendering audio (pyfluidsynth): {os.path.basename(midi_path)}")
            
            # Create synth with higher gain for audibility
            fs = fluidsynth.Synth(samplerate=float(SAMPLE_RATE), gain=0.8)
            sfid = fs.sfload(self.soundfont_path)
            
            # Read MIDI file using mido
            mid = mido.MidiFile(midi_path)
            
            # Select programs for each channel based on the MIDI file
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'program_change':
                        fs.program_select(msg.channel, sfid, 0, msg.program)
            
            # Explicitly set up drum channel (bank 128 = GM percussion kit)
            # The MIDI file doesn't include program_change for drums (standard GM),
            # but FluidSynth needs program_select to load the percussion SoundFont.
            fs.program_select(DRUM_CHANNEL, sfid, 128, 0)
            
            # Set channel volumes (CC7) for all active channels to ensure audibility
            for ch in [DRUM_CHANNEL, 1, 2, 3]:
                fs.cc(ch, 7, 100)   # CC7 = channel volume
                fs.cc(ch, 10, 64)   # CC10 = pan center
            
            # Calculate total duration in seconds
            total_seconds = mid.length + 1.0  # extra second for decay
            total_samples = int(total_seconds * SAMPLE_RATE)
            
            # Allocate audio buffer
            audio_data = np.zeros((total_samples, 2), dtype=np.float32)
            
            # Process MIDI messages
            sample_pos = 0
            
            for msg in mid:
                if msg.time > 0:
                    # Render audio for this time gap
                    num_samples = int(msg.time * SAMPLE_RATE)
                    if num_samples > 0 and sample_pos < total_samples:
                        samples = fs.get_samples(num_samples)
                        # Convert interleaved stereo to array
                        stereo = np.frombuffer(samples, dtype=np.int16).reshape(-1, 2)
                        end_pos = min(sample_pos + len(stereo), total_samples)
                        copy_len = end_pos - sample_pos
                        if copy_len > 0:
                            audio_data[sample_pos:end_pos] = stereo[:copy_len].astype(np.float32) / 32768.0
                        sample_pos = end_pos
                
                # Send MIDI message to synth
                if msg.type == 'note_on':
                    fs.noteon(msg.channel, msg.note, msg.velocity)
                elif msg.type == 'note_off':
                    fs.noteoff(msg.channel, msg.note)
                elif msg.type == 'control_change':
                    fs.cc(msg.channel, msg.control, msg.value)
                elif msg.type == 'program_change':
                    fs.program_select(msg.channel, sfid, 0, msg.program)
                elif msg.type == 'pitchwheel':
                    fs.pitch_bend(msg.channel, msg.pitch + 8192)
            
            # Render any remaining samples (tail / decay)
            remaining = total_samples - sample_pos
            if remaining > 0:
                samples = fs.get_samples(remaining)
                stereo = np.frombuffer(samples, dtype=np.int16).reshape(-1, 2)
                copy_len = min(len(stereo), remaining)
                audio_data[sample_pos:sample_pos + copy_len] = stereo[:copy_len].astype(np.float32) / 32768.0
            
            fs.delete()
            
            # Normalize audio
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val * 0.9  # Leave some headroom
            
            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(2)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(audio_int16.tobytes())
            
            print(f"✅ Audio rendered: {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            print(f"pyfluidsynth rendering error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _render_with_cli(self, midi_path: str, output_path: str) -> str:
        """Render MIDI to WAV using FluidSynth CLI."""
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
            
            print(f"Rendering audio (CLI): {os.path.basename(midi_path)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Audio rendered: {os.path.basename(output_path)}")
                return output_path
            else:
                print(f"FluidSynth CLI error: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error rendering audio via CLI: {e}")
            return None
    
    def play_midi(self, midi_path: str):
        """
        Play a MIDI file. Uses pygame if available, else CLI FluidSynth, else system player.
        
        Args:
            midi_path: Path to MIDI file
        """
        if not os.path.exists(midi_path):
            print(f"MIDI file not found: {midi_path}")
            return
        
        # Try pygame first (best cross-platform)
        if self.pygame_available:
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(midi_path)
                pygame.mixer.music.play()
                print(f"Playing MIDI via pygame: {os.path.basename(midi_path)}")
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.quit()
                return
            except Exception as e:
                print(f"pygame MIDI playback failed: {e}")
        
        # Try FluidSynth CLI
        if self.cli_fluidsynth_available and self._check_soundfont():
            try:
                system = platform.system()
                audio_driver = 'dsound' if system == 'Windows' else (
                    'coreaudio' if system == 'Darwin' else 'pulseaudio'
                )
                
                cmd = [
                    'fluidsynth',
                    '-a', audio_driver,
                    '-g', '1.0',
                    self.soundfont_path,
                    midi_path
                ]
                
                print(f"Playing via FluidSynth CLI: {os.path.basename(midi_path)}")
                subprocess.run(cmd)
                return
            except Exception as e:
                print(f"FluidSynth CLI playback failed: {e}")
        
        # Last resort: system player
        self._try_system_player(midi_path)
    
    def play_wav(self, wav_path: str):
        """
        Play a WAV file. Uses pygame if available, else system player.
        
        Args:
            wav_path: Path to WAV file
        """
        if not os.path.exists(wav_path):
            print(f"WAV file not found: {wav_path}")
            return
        
        # Try pygame first
        if self.pygame_available:
            try:
                import pygame
                pygame.mixer.init(frequency=SAMPLE_RATE)
                pygame.mixer.music.load(wav_path)
                pygame.mixer.music.play()
                print(f"Playing WAV via pygame: {os.path.basename(wav_path)}")
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.quit()
                return
            except Exception as e:
                print(f"pygame WAV playback failed: {e}")
        
        # System player fallback
        try:
            system = platform.system()
            if system == 'Windows':
                os.startfile(wav_path)
            elif system == 'Darwin':
                subprocess.run(['afplay', wav_path])
            else:
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

    # =================================================================
    # PER-TRACK RENDERING WITH EFFECTS
    # =================================================================
    def _render_midi_to_array(self, midi_path: str) -> np.ndarray:
        """
        Render a MIDI file to a numpy float32 stereo array.

        Args:
            midi_path: Path to a MIDI file

        Returns:
            numpy array of shape (samples, 2), float32, or None on failure
        """
        try:
            import fluidsynth
            import mido

            fs = fluidsynth.Synth(samplerate=float(SAMPLE_RATE), gain=0.8)
            sfid = fs.sfload(self.soundfont_path)

            mid = mido.MidiFile(midi_path)

            # Setup programs from the MIDI file
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'program_change':
                        fs.program_select(msg.channel, sfid, 0, msg.program)

            # Drum kit
            fs.program_select(DRUM_CHANNEL, sfid, 128, 0)

            # Channel volumes
            for ch in range(16):
                fs.cc(ch, 7, 100)
                fs.cc(ch, 10, 64)

            total_seconds = mid.length + 1.0
            total_samples = int(total_seconds * SAMPLE_RATE)
            audio_data = np.zeros((total_samples, 2), dtype=np.float32)

            sample_pos = 0
            for msg in mid:
                if msg.time > 0:
                    num_samples = int(msg.time * SAMPLE_RATE)
                    if num_samples > 0 and sample_pos < total_samples:
                        samples = fs.get_samples(num_samples)
                        stereo = np.frombuffer(samples, dtype=np.int16).reshape(-1, 2)
                        end_pos = min(sample_pos + len(stereo), total_samples)
                        copy_len = end_pos - sample_pos
                        if copy_len > 0:
                            audio_data[sample_pos:end_pos] = stereo[:copy_len].astype(np.float32) / 32768.0
                        sample_pos = end_pos

                if msg.type == 'note_on':
                    fs.noteon(msg.channel, msg.note, msg.velocity)
                elif msg.type == 'note_off':
                    fs.noteoff(msg.channel, msg.note)
                elif msg.type == 'control_change':
                    fs.cc(msg.channel, msg.control, msg.value)
                elif msg.type == 'program_change':
                    fs.program_select(msg.channel, sfid, 0, msg.program)

            remaining = total_samples - sample_pos
            if remaining > 0:
                samples = fs.get_samples(remaining)
                stereo = np.frombuffer(samples, dtype=np.int16).reshape(-1, 2)
                copy_len = min(len(stereo), remaining)
                audio_data[sample_pos:sample_pos + copy_len] = stereo[:copy_len].astype(np.float32) / 32768.0

            fs.delete()
            return audio_data

        except Exception as e:
            print(f"Error rendering track to array: {e}")
            import traceback
            traceback.print_exc()
            return None

    def render_with_effects(
        self,
        track_midi_paths: dict,
        effects_config: dict,
        output_path: str
    ) -> str:
        """
        Render multiple single-track MIDI files, apply per-track effects, mix.

        Args:
            track_midi_paths: Dict mapping section name -> temp MIDI path
                              e.g. {'drums': '/path/to/_temp_drums.mid', ...}
            effects_config: Dict mapping section name -> effects dict
                            e.g. {'drums': {'reverb': 20, 'delay': 0, ...}, ...}
            output_path: Path for the final mixed WAV file

        Returns:
            Path to the mixed WAV file, or None on failure
        """
        if not self.pyfluidsynth_available or not self._check_soundfont():
            print("Cannot render with effects: FluidSynth not available")
            return None

        try:
            from utils.effects_processor import EffectsProcessor
            fx = EffectsProcessor(SAMPLE_RATE)

            print("Rendering per-track with effects...")
            track_arrays = {}
            max_length = 0

            for track_name, midi_path in track_midi_paths.items():
                print(f"  Rendering {track_name}...")
                arr = self._render_midi_to_array(midi_path)
                if arr is not None and len(arr) > 0:
                    track_arrays[track_name] = arr
                    max_length = max(max_length, len(arr))

            if not track_arrays:
                print("No tracks rendered successfully")
                return None

            # Pad all arrays to same length
            for name in track_arrays:
                arr = track_arrays[name]
                if len(arr) < max_length:
                    pad = np.zeros((max_length - len(arr), 2), dtype=np.float32)
                    track_arrays[name] = np.concatenate([arr, pad])

            # Apply per-track effects
            for track_name, arr in track_arrays.items():
                section_fx = effects_config.get(track_name, {})
                if section_fx and any(v > 0 for v in section_fx.values()):
                    print(f"  Applying effects to {track_name}: {section_fx}")
                    track_arrays[track_name] = fx.apply_effects_chain(arr, section_fx)

            # Mix all tracks
            mixed = np.zeros((max_length, 2), dtype=np.float64)
            for arr in track_arrays.values():
                mixed += arr.astype(np.float64)

            # Normalise
            max_val = np.max(np.abs(mixed))
            if max_val > 0:
                mixed = mixed / max_val * 0.9

            # Convert to 16-bit PCM and save
            audio_int16 = (mixed * 32767).astype(np.int16)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(2)
                wav_file.setsampwidth(2)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(audio_int16.tobytes())

            print(f"✅ Audio rendered with effects: {os.path.basename(output_path)}")
            return output_path

        except Exception as e:
            print(f"Error rendering with effects: {e}")
            import traceback
            traceback.print_exc()
            return None
