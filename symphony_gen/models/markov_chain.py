"""
Pure logic for building and sampling Markov chain models.
The mathematical engine for the Lead Melody generation.
"""

import random
import csv
from collections import defaultdict
from typing import List, Tuple, Optional, Set


class MarkovChain:
    """
    A Markov chain implementation for generating musical sequences.
    Supports training on pitch and duration data, with scale filtering.
    """
    
    def __init__(self, order: int = 2):
        """
        Initialize the Markov chain.
        
        Args:
            order: The order of the Markov chain (number of previous states to consider)
        """
        self.order = order
        self.pitch_chain = defaultdict(list)
        self.duration_chain = defaultdict(list)
        self.start_states = []
        self.is_trained = False
    
    def train(self, sequences: List[List[Tuple[int, int]]]):
        """
        Train the Markov chain on sequences of (pitch, duration) tuples.
        
        Args:
            sequences: List of melodies, each melody is a list of (pitch, duration) tuples
        """
        for sequence in sequences:
            if len(sequence) <= self.order:
                continue
            
            pitches = [note[0] for note in sequence]
            durations = [note[1] for note in sequence]
            
            if len(pitches) >= self.order:
                self.start_states.append(tuple(pitches[:self.order]))
            
            for i in range(len(pitches) - self.order):
                pitch_state = tuple(pitches[i:i + self.order])
                next_pitch = pitches[i + self.order]
                self.pitch_chain[pitch_state].append(next_pitch)
                
                duration_state = tuple(durations[i:i + self.order])
                next_duration = durations[i + self.order]
                self.duration_chain[duration_state].append(next_duration)
        
        self.is_trained = bool(self.pitch_chain)
    
    def train_from_csv(self, csv_path: str):
        """
        Load training data from a CSV file and train the model.
        
        Args:
            csv_path: Path to the CSV file
        """
        sequences = []
        current_sequence = []
        current_melody_id = None
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                
                for row in reader:
                    if len(row) >= 2:
                        try:
                            pitch = int(row[0])
                            duration = int(row[1])
                            melody_id = row[2] if len(row) > 2 else "0"
                            
                            if melody_id != current_melody_id:
                                if current_sequence:
                                    sequences.append(current_sequence)
                                current_sequence = []
                                current_melody_id = melody_id
                            
                            current_sequence.append((pitch, duration))
                        except ValueError:
                            continue
                
                if current_sequence:
                    sequences.append(current_sequence)
            
            if sequences:
                self.train(sequences)
                
        except FileNotFoundError:
            print(f"Warning: Training data not found at {csv_path}")
            self._create_default_training_data()
    
    def _create_default_training_data(self):
        """Create basic training data if no CSV is available."""
        default_sequences = [
            [(60, 480), (62, 480), (64, 480), (65, 480), (67, 960), (65, 480), (64, 480), (62, 480), (60, 960)],
            [(60, 240), (64, 240), (67, 480), (64, 240), (60, 240), (62, 960)],
            [(67, 480), (65, 480), (64, 480), (62, 480), (60, 960)],
            [(60, 480), (60, 480), (67, 480), (67, 480), (69, 480), (69, 480), (67, 960)],
            [(65, 480), (65, 480), (64, 480), (64, 480), (62, 480), (62, 480), (60, 960)],
        ]
        self.train(default_sequences)
    
    def generate_sequence(
        self,
        length: int,
        valid_scale_notes: Optional[Set[int]] = None,
        seed: Optional[Tuple[int, ...]] = None
    ) -> List[Tuple[int, int]]:
        """
        Generate a new melody sequence using the trained Markov chain.
        
        Args:
            length: Number of notes to generate
            valid_scale_notes: Set of MIDI notes that are valid for the current scale.
            seed: Starting pitch state (optional)
            
        Returns:
            List of (pitch, duration) tuples
        """
        if not self.is_trained:
            self._create_default_training_data()
        
        if not self.pitch_chain:
            return [(60, 480)] * length
        
        if seed is not None and seed in self.pitch_chain:
            current_pitch_state = seed
        elif self.start_states:
            current_pitch_state = random.choice(self.start_states)
        else:
            current_pitch_state = random.choice(list(self.pitch_chain.keys()))
        
        duration_states = list(self.duration_chain.keys())
        current_duration_state = random.choice(duration_states) if duration_states else (480,) * self.order
        
        pitches = list(current_pitch_state)
        durations = list(current_duration_state)
        
        for _ in range(length - self.order):
            if current_pitch_state in self.pitch_chain:
                next_pitch = random.choice(self.pitch_chain[current_pitch_state])
            else:
                next_pitch = pitches[-1] + random.choice([-2, -1, 0, 1, 2])
            
            if valid_scale_notes:
                next_pitch = self._snap_to_scale(next_pitch, valid_scale_notes)
            
            next_pitch = max(36, min(96, next_pitch))
            
            pitches.append(next_pitch)
            current_pitch_state = tuple(pitches[-self.order:])
            
            if current_duration_state in self.duration_chain:
                next_duration = random.choice(self.duration_chain[current_duration_state])
            else:
                next_duration = random.choice([240, 480, 960])
            
            durations.append(next_duration)
            current_duration_state = tuple(durations[-self.order:])
        
        return list(zip(pitches, durations))
    
    def _snap_to_scale(self, pitch: int, valid_notes: Set[int]) -> int:
        """Snap a pitch to the nearest note in the valid scale."""
        if pitch in valid_notes:
            return pitch
        closest = min(valid_notes, key=lambda x: abs(x - pitch))
        return closest
    
    def get_next_note(
        self,
        previous_notes: Tuple[int, ...],
        valid_scale_notes: Optional[Set[int]] = None
    ) -> int:
        """Get a single next note given previous context."""
        if previous_notes in self.pitch_chain:
            next_pitch = random.choice(self.pitch_chain[previous_notes])
        else:
            next_pitch = previous_notes[-1] + random.choice([-2, -1, 0, 1, 2])
        
        if valid_scale_notes:
            next_pitch = self._snap_to_scale(next_pitch, valid_scale_notes)
        
        return max(36, min(96, next_pitch))
