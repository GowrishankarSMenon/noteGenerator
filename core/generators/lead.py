"""
Logic for generating lead melodies using Markov chains.
The "Singer" or "Soloist" - the only part using Markov Chains.
"""

import sys
import os
import random
from typing import List, Dict, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.context import SongContext
from models.markov_chain import MarkovChain
from config.settings import TICKS_PER_BEAT, DEFAULT_VELOCITY, DATASET_PATH
from utils.music_theory import get_scale_notes


class LeadGenerator:
    """
    Generates lead melodies using Markov chain models.
    """
    
    def __init__(self):
        self.lead_octave = 5  # Lead plays in upper register
        self.markov = MarkovChain(order=2)
        self._load_markov_model()
    
    def _load_markov_model(self):
        """Load and train the Markov model from dataset."""
        if os.path.exists(DATASET_PATH):
            self.markov.train_from_csv(DATASET_PATH)
        else:
            print(f"Dataset not found at {DATASET_PATH}, using default training data")
            self.markov._create_default_training_data()
    
    def generate(self, ctx: SongContext, harmony_track: List[Dict]) -> List[Dict]:
        """
        Generate lead melody using Markov chain sampling.
        
        Args:
            ctx: The SongContext with key and scale
            harmony_track: Harmony track (for reference)
            
        Returns:
            List of MIDI events for lead melody
        """
        events = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        
        # Calculate total duration and estimate notes needed
        total_ticks = ctx.total_bars * ticks_per_bar
        estimated_notes = int(total_ticks / (TICKS_PER_BEAT // 2))  # Avg 8th note density
        
        # Generate melody using Markov chain
        melody = self._generate_melody(ctx, estimated_notes)
        
        # Place notes across the song
        current_tick = 0
        note_idx = 0
        
        while current_tick < total_ticks and note_idx < len(melody):
            # Get current bar context
            bar_idx = current_tick // ticks_per_bar
            if bar_idx >= len(ctx.timeline):
                break
            
            bar = ctx.timeline[bar_idx]
            
            # Get note from melody
            pitch, duration = melody[note_idx]
            
            # Adjust pitch to current scale (snap to scale)
            scale_notes = set(bar.scale_notes)
            if scale_notes:
                pitch = self._snap_to_scale(pitch, scale_notes)
            
            # Ensure note is in lead octave range
            pitch = self._adjust_to_range(pitch, self.lead_octave * 12, (self.lead_octave + 1) * 12)
            
            # Add some rhythmic variation
            duration = self._humanize_duration(duration)
            
            # Check we don't go past end
            if current_tick + duration > total_ticks:
                duration = total_ticks - current_tick
            
            events.append({
                'note': pitch,
                'start': current_tick,
                'duration': duration,
                'velocity': self._get_velocity(current_tick, ticks_per_bar)
            })
            
            current_tick += duration
            note_idx += 1
            
            # Add occasional rests
            if random.random() < 0.15:  # 15% chance of rest
                rest_duration = random.choice([TICKS_PER_BEAT // 2, TICKS_PER_BEAT])
                current_tick += rest_duration
        
        return events
    
    def _generate_melody(self, ctx: SongContext, length: int) -> List[Tuple[int, int]]:
        """
        Generate raw melody using Markov chain.
        
        Returns:
            List of (pitch, duration) tuples
        """
        # Get scale notes for filtering
        scale_notes = set(get_scale_notes(ctx.key_root_midi, ctx.scale_type))
        
        # Generate sequence
        melody = self.markov.generate_sequence(
            length=length,
            valid_scale_notes=scale_notes
        )
        
        return melody
    
    def _snap_to_scale(self, pitch: int, valid_notes: Set[int]) -> int:
        """Snap a pitch to the nearest valid scale note."""
        if pitch in valid_notes:
            return pitch
        
        # Find nearest valid note
        closest = min(valid_notes, key=lambda x: abs(x - pitch))
        return closest
    
    def _adjust_to_range(self, pitch: int, min_pitch: int, max_pitch: int) -> int:
        """Adjust pitch to stay within the desired range."""
        while pitch < min_pitch:
            pitch += 12
        while pitch > max_pitch:
            pitch -= 12
        return pitch
    
    def _humanize_duration(self, duration: int) -> int:
        """Add slight variation to note durations for humanization."""
        # Quantize to common note values
        common_durations = [
            TICKS_PER_BEAT // 4,   # 16th
            TICKS_PER_BEAT // 2,   # 8th
            TICKS_PER_BEAT,        # Quarter
            TICKS_PER_BEAT * 2,    # Half
        ]
        
        # Find closest common duration
        closest = min(common_durations, key=lambda x: abs(x - duration))
        
        # Add slight variation
        variation = random.randint(-20, 20)
        return max(TICKS_PER_BEAT // 8, closest + variation)
    
    def _get_velocity(self, tick: int, ticks_per_bar: int) -> int:
        """Get velocity based on position in bar (emphasis on beats)."""
        position_in_bar = tick % ticks_per_bar
        beat = position_in_bar // TICKS_PER_BEAT
        
        # Emphasize beat 1 and 3
        if beat == 0:
            return DEFAULT_VELOCITY + 15
        elif beat == 2:
            return DEFAULT_VELOCITY + 5
        else:
            return DEFAULT_VELOCITY - 5 + random.randint(-5, 5)
