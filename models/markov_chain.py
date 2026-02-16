"""
Pure logic for building and sampling Markov chain models.
The mathematical engine for the Lead Melody generation.

Technique-aware: trains on (pitch, duration, technique) triples so the
generated sequences carry guitar-articulation hints that the effects
processor can apply deterministically instead of randomly.
"""

import random
import csv
from collections import defaultdict
from typing import List, Tuple, Optional, Set


# Canonical technique vocabulary — used in CSV datasets and Markov output.
VALID_TECHNIQUES = {
    'normal', 'bend_half', 'bend_whole', 'bend_slow',
    'vibrato', 'hammer_on', 'pull_off',
    'slide_up', 'slide_down',
    'tap', 'palm_mute', 'staccato', 'legato',
}


class MarkovChain:
    """
    A Markov chain implementation for generating musical sequences.
    Supports training on pitch, duration, and technique data, with scale filtering.
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
        self.technique_chain = defaultdict(list)   # NEW: technique transitions
        self.start_states = []
        self.start_techniques = []                  # NEW: starting technique states
        self.is_trained = False
    
    def train(self, sequences: List[List[Tuple]]):
        """
        Train the Markov chain on sequences of (pitch, duration[, technique]) tuples.
        
        Args:
            sequences: List of melodies, each melody is a list of tuples.
                       Tuples may be (pitch, duration) or (pitch, duration, technique).
        """
        for sequence in sequences:
            if len(sequence) <= self.order:
                continue
            
            pitches = [note[0] for note in sequence]
            durations = [note[1] for note in sequence]
            techniques = [note[2] if len(note) > 2 else 'normal' for note in sequence]
            
            if len(pitches) >= self.order:
                self.start_states.append(tuple(pitches[:self.order]))
                self.start_techniques.append(tuple(techniques[:self.order]))
            
            for i in range(len(pitches) - self.order):
                pitch_state = tuple(pitches[i:i + self.order])
                next_pitch = pitches[i + self.order]
                self.pitch_chain[pitch_state].append(next_pitch)
                
                duration_state = tuple(durations[i:i + self.order])
                next_duration = durations[i + self.order]
                self.duration_chain[duration_state].append(next_duration)

                # Technique chain: previous techniques → next technique
                tech_state = tuple(techniques[i:i + self.order])
                next_technique = techniques[i + self.order]
                self.technique_chain[tech_state].append(next_technique)
        
        self.is_trained = bool(self.pitch_chain)
    
    def train_from_csv(self, csv_path: str):
        """
        Load training data from a CSV file and train the model.
        Supports both old format (pitch,duration,melody_id) and new
        format (pitch,duration,melody_id,technique).
        
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
                # Detect whether the file has a technique column
                has_technique = header is not None and len(header) >= 4 and 'technique' in header[-1].lower()
                
                for row in reader:
                    if len(row) >= 2:
                        try:
                            pitch = int(row[0])
                            duration = int(row[1])
                            melody_id = row[2] if len(row) > 2 else "0"
                            technique = row[3].strip() if has_technique and len(row) > 3 else 'normal'
                            # Validate technique
                            if technique not in VALID_TECHNIQUES:
                                technique = 'normal'
                            
                            if melody_id != current_melody_id:
                                if current_sequence:
                                    sequences.append(current_sequence)
                                current_sequence = []
                                current_melody_id = melody_id
                            
                            current_sequence.append((pitch, duration, technique))
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
            [(60, 480, 'normal'), (62, 480, 'normal'), (64, 480, 'normal'), (65, 480, 'normal'),
             (67, 960, 'vibrato'), (65, 480, 'normal'), (64, 480, 'normal'), (62, 480, 'normal'), (60, 960, 'normal')],
            [(60, 240, 'normal'), (64, 240, 'normal'), (67, 480, 'normal'), (64, 240, 'normal'),
             (60, 240, 'normal'), (62, 960, 'normal')],
            [(67, 480, 'normal'), (65, 480, 'normal'), (64, 480, 'normal'), (62, 480, 'normal'), (60, 960, 'normal')],
            [(60, 480, 'normal'), (60, 480, 'normal'), (67, 480, 'normal'), (67, 480, 'normal'),
             (69, 480, 'normal'), (69, 480, 'normal'), (67, 960, 'vibrato')],
            [(65, 480, 'normal'), (65, 480, 'normal'), (64, 480, 'normal'), (64, 480, 'normal'),
             (62, 480, 'normal'), (62, 480, 'normal'), (60, 960, 'normal')],
        ]
        self.train(default_sequences)
    
    def generate_sequence(
        self,
        length: int,
        valid_scale_notes: Optional[Set[int]] = None,
        seed: Optional[Tuple[int, ...]] = None
    ) -> List[Tuple[int, int, str]]:
        """
        Generate a new melody sequence using the trained Markov chain.
        
        Args:
            length: Number of notes to generate
            valid_scale_notes: Set of MIDI notes that are valid for the current scale.
            seed: Starting pitch state (optional)
            
        Returns:
            List of (pitch, duration, technique) tuples
        """
        if not self.is_trained:
            self._create_default_training_data()
        
        if not self.pitch_chain:
            return [(60, 480, 'normal')] * length
        
        if seed is not None and seed in self.pitch_chain:
            current_pitch_state = seed
        elif self.start_states:
            current_pitch_state = random.choice(self.start_states)
        else:
            current_pitch_state = random.choice(list(self.pitch_chain.keys()))
        
        duration_states = list(self.duration_chain.keys())
        current_duration_state = random.choice(duration_states) if duration_states else (480,) * self.order

        # Technique state
        if self.start_techniques:
            current_technique_state = random.choice(self.start_techniques)
        elif self.technique_chain:
            current_technique_state = random.choice(list(self.technique_chain.keys()))
        else:
            current_technique_state = ('normal',) * self.order
        
        pitches = list(current_pitch_state)
        durations = list(current_duration_state)
        techniques = list(current_technique_state)
        
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

            # Generate technique
            if current_technique_state in self.technique_chain:
                next_technique = random.choice(self.technique_chain[current_technique_state])
            else:
                next_technique = 'normal'
            techniques.append(next_technique)
            current_technique_state = tuple(techniques[-self.order:])
        
        return list(zip(pitches, durations, techniques))
    
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
