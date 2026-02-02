"""
Pure logic for building and sampling Markov chain models.
"""

import random
from collections import defaultdict


class MarkovChain:
    """
    A Markov chain implementation for generating musical sequences.
    """
    
    def __init__(self, order=1):
        """
        Initialize the Markov chain.
        
        Args:
            order (int): The order of the Markov chain (number of previous states to consider)
        """
        self.order = order
        self.chain = defaultdict(list)
    
    def train(self, sequence):
        """
        Train the Markov chain on a sequence of data.
        
        Args:
            sequence (list): Training sequence (e.g., list of notes)
        """
        for i in range(len(sequence) - self.order):
            state = tuple(sequence[i:i + self.order])
            next_state = sequence[i + self.order]
            self.chain[state].append(next_state)
    
    def generate(self, length, seed=None):
        """
        Generate a new sequence using the trained Markov chain.
        
        Args:
            length (int): Length of sequence to generate
            seed (tuple): Starting state (optional)
            
        Returns:
            list: Generated sequence
        """
        if not self.chain:
            return []
        
        if seed is None:
            current_state = random.choice(list(self.chain.keys()))
        else:
            current_state = seed
        
        result = list(current_state)
        
        for _ in range(length - self.order):
            if current_state not in self.chain:
                break
            
            next_note = random.choice(self.chain[current_state])
            result.append(next_note)
            current_state = tuple(result[-self.order:])
        
        return result
