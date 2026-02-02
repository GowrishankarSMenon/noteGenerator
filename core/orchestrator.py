"""
MANAGER: Runs the sequential generation cascade.
The Orchestrator ties everything together - the "Main Loop" of generation.
"""

import os
import sys
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.context import SongContext
from core.conductor import Conductor
from core.generators.drums import DrumsGenerator
from core.generators.bass import BassGenerator
from core.generators.harmony import HarmonyGenerator
from core.generators.lead import LeadGenerator
from utils.midi_renderer import MidiRenderer
from utils.audio_engine import AudioEngine
from config.settings import INSTRUMENTS, DRUM_CHANNEL


class Orchestrator:
    """
    The Orchestrator manages the sequential generation of all instruments.
    It coordinates the generation process across drums, bass, harmony, and lead.
    """
    
    def __init__(self):
        self.conductor = Conductor()
        self.drums_gen = DrumsGenerator()
        self.bass_gen = BassGenerator()
        self.harmony_gen = HarmonyGenerator()
        self.lead_gen = LeadGenerator()
        self.audio_engine = AudioEngine()
    
    def generate(
        self,
        mood: str,
        length_in_bars: int = 16,
        bpm: Optional[int] = None,
        key: Optional[str] = None,
        render_audio: bool = True
    ) -> Tuple[str, Optional[str], SongContext]:
        """
        Execute the full generation pipeline.
        
        Args:
            mood: The desired mood
            length_in_bars: Song length in bars
            bpm: Override BPM (optional)
            key: Override key (optional)
            render_audio: Whether to render WAV file
            
        Returns:
            Tuple of (midi_path, wav_path, song_context)
        """
        print(f"\n{'='*50}")
        print(f"ORCHESTRATOR: Generating {mood} song ({length_in_bars} bars)")
        print(f"{'='*50}\n")
        
        # Step 1: Plan the song
        print("[1/6] Conductor planning song structure...")
        ctx = self.conductor.create_song_context(
            mood=mood,
            length_in_bars=length_in_bars,
            bpm=bpm,
            key=key
        )
        
        # Step 2: Generate drums (foundation)
        print("\n[2/6] Generating drums...")
        drum_track = self.drums_gen.generate(ctx)
        print(f"       Generated {len(drum_track)} drum events")
        
        # Step 3: Generate bass (locks to kick drum)
        print("\n[3/6] Generating bass...")
        bass_track = self.bass_gen.generate(ctx, drum_track)
        print(f"       Generated {len(bass_track)} bass events")
        
        # Step 4: Generate harmony (chords/pads)
        print("\n[4/6] Generating harmony...")
        harmony_track = self.harmony_gen.generate(ctx, bass_track)
        print(f"       Generated {len(harmony_track)} harmony events")
        
        # Step 5: Generate lead melody (Markov)
        print("\n[5/6] Generating lead melody...")
        lead_track = self.lead_gen.generate(ctx, harmony_track)
        print(f"       Generated {len(lead_track)} melody events")
        
        # Step 6: Render to MIDI
        print("\n[6/6] Rendering MIDI file...")
        midi_path, wav_path = self._render_tracks(
            ctx, drum_track, bass_track, harmony_track, lead_track,
            render_audio=render_audio
        )
        
        print(f"\n{'='*50}")
        print(f"GENERATION COMPLETE!")
        print(f"  MIDI: {midi_path}")
        if wav_path:
            print(f"  WAV:  {wav_path}")
        print(f"{'='*50}\n")
        
        return midi_path, wav_path, ctx
    
    def _render_tracks(
        self,
        ctx: SongContext,
        drum_track: list,
        bass_track: list,
        harmony_track: list,
        lead_track: list,
        render_audio: bool = True
    ) -> Tuple[str, Optional[str]]:
        """
        Render all tracks to MIDI and optionally WAV.
        
        Returns:
            Tuple of (midi_path, wav_path)
        """
        renderer = MidiRenderer(bpm=ctx.bpm)
        
        # Get instrument programs
        bass_program = INSTRUMENTS.get(ctx.instruments.get('bass', 'electric_bass'), 33)
        harmony_program = INSTRUMENTS.get(ctx.instruments.get('harmony', 'piano'), 0)
        lead_program = INSTRUMENTS.get(ctx.instruments.get('lead', 'synth_lead'), 80)
        
        # Prepare tracks data
        tracks_data = {
            'Drums': (drum_track, DRUM_CHANNEL, 0),
            'Bass': (bass_track, 1, bass_program),
            'Harmony': (harmony_track, 2, harmony_program),
            'Lead': (lead_track, 3, lead_program),
        }
        
        # Generate filename
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ctx.mood}_{ctx.key}_{ctx.bpm}bpm_{timestamp}.mid"
        
        # Render MIDI
        midi_path = renderer.render(tracks_data, filename)
        
        # Render audio if requested
        wav_path = None
        if render_audio:
            wav_path = self.audio_engine.render_to_wav(midi_path)
        
        return midi_path, wav_path
    
    def get_available_moods(self) -> list:
        """Get list of available moods."""
        return self.conductor.get_available_moods()
