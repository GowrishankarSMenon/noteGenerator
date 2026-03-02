"""
Logic for generating harmonic content including chords and pads.
The chordal backing (Piano/Pad/Rhythm Guitar).
"""

import sys
import os
import random
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.context import SongContext
from config.settings import TICKS_PER_BEAT, DEFAULT_VELOCITY
from utils.music_theory import get_chord_notes


class HarmonyGenerator:
    """
    Generates chords, pads, and harmonic accompaniment.
    """
    
    def __init__(self):
        self.chord_octave = 4  # Middle register
    
    def generate(self, ctx: SongContext, bass_track: List[Dict]) -> List[Dict]:
        """
        Generate harmonic content based on chord progression.
        
        Args:
            ctx: The SongContext with chord progression
            bass_track: Bass track (for avoiding frequency clashes)
            
        Returns:
            List of MIDI events for harmony/chords
        """
        style = ctx.harmony_style
        
        if style == 'sustained':
            return self._generate_sustained(ctx)
        elif style == 'rhythmic':
            return self._generate_rhythmic(ctx)
        elif style == 'arpeggiated':
            return self._generate_arpeggiated(ctx)
        elif style == 'power':
            return self._generate_power_chords(ctx)
        elif style == 'voicing':
            return self._generate_jazz_voicings(ctx)
        else:
            return self._generate_sustained(ctx)
    
    def _generate_sustained(self, ctx: SongContext) -> List[Dict]:
        """Generate long sustained pad chords."""
        events = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        
        for bar in ctx.timeline:
            bar_start = bar.bar_index * ticks_per_bar
            
            # Get chord notes
            root = (bar.root_note % 12) + (12 * (self.chord_octave + 1))
            chord_notes = get_chord_notes(root, bar.chord_type)
            
            # Sustained chord for entire bar
            for note in chord_notes:
                events.append({
                    'note': note,
                    'start': bar_start,
                    'duration': ticks_per_bar - 10,
                    'velocity': DEFAULT_VELOCITY - 20  # Quieter pads
                })
        
        return events
    
    def _generate_rhythmic(self, ctx: SongContext) -> List[Dict]:
        """Generate rhythmic chord stabs."""
        events = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        
        # Rhythm pattern: hit on 1, and, 3, and (8th notes)
        pattern = [1, 0, 1, 0, 1, 0, 1, 0]
        ticks_per_8th = TICKS_PER_BEAT // 2
        
        for bar in ctx.timeline:
            bar_start = bar.bar_index * ticks_per_bar
            
            # Get chord notes
            root = (bar.root_note % 12) + (12 * (self.chord_octave + 1))
            chord_notes = get_chord_notes(root, bar.chord_type)
            
            for step_idx, hit in enumerate(pattern):
                if hit:
                    step_time = bar_start + (step_idx * ticks_per_8th)
                    
                    for note in chord_notes:
                        events.append({
                            'note': note,
                            'start': step_time,
                            'duration': ticks_per_8th - 20,
                            'velocity': DEFAULT_VELOCITY if step_idx % 4 == 0 else DEFAULT_VELOCITY - 15
                        })
        
        return events
    
    def _generate_arpeggiated(self, ctx: SongContext) -> List[Dict]:
        """Generate arpeggiated chord patterns."""
        events = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        ticks_per_8th = TICKS_PER_BEAT // 2
        
        for bar in ctx.timeline:
            bar_start = bar.bar_index * ticks_per_bar
            
            # Get chord notes
            root = (bar.root_note % 12) + (12 * (self.chord_octave + 1))
            chord_notes = get_chord_notes(root, bar.chord_type)
            
            # Arpeggiate through the chord
            note_idx = 0
            for step in range(8):  # 8 eighth notes per bar
                step_time = bar_start + (step * ticks_per_8th)
                note = chord_notes[note_idx % len(chord_notes)]
                
                events.append({
                    'note': note,
                    'start': step_time,
                    'duration': ticks_per_8th - 10,
                    'velocity': DEFAULT_VELOCITY - 10
                })
                
                # Pattern: up and down
                if step < 4:
                    note_idx += 1
                else:
                    note_idx -= 1
        
        return events
    
    def _generate_power_chords(self, ctx: SongContext) -> List[Dict]:
        """Generate power chords (root + fifth) for rock style."""
        events = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        
        # Power chord pattern: hits on 1, 2+, 3, 4
        pattern = [1, 0, 0, 1, 1, 0, 1, 0]
        ticks_per_8th = TICKS_PER_BEAT // 2
        
        for bar in ctx.timeline:
            bar_start = bar.bar_index * ticks_per_bar
            
            # Power chord: root + fifth (+ octave for power)
            root = (bar.root_note % 12) + (12 * (self.chord_octave + 1))
            power_chord = [root, root + 7, root + 12]
            
            for step_idx, hit in enumerate(pattern):
                if hit:
                    step_time = bar_start + (step_idx * ticks_per_8th)
                    
                    for note in power_chord:
                        events.append({
                            'note': note,
                            'start': step_time,
                            'duration': ticks_per_8th - 10,
                            'velocity': DEFAULT_VELOCITY + 10
                        })
        
        return events
    
    def _generate_jazz_voicings(self, ctx: SongContext) -> List[Dict]:
        """Generate jazz-style chord voicings with extensions."""
        events = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        
        for bar in ctx.timeline:
            bar_start = bar.bar_index * ticks_per_bar
            
            # Jazz voicing: 3rd, 7th, and extensions
            root = (bar.root_note % 12) + (12 * (self.chord_octave + 1))
            
            # Build a rootless voicing
            if bar.chord_type in ['min', 'min7']:
                voicing = [root + 3, root + 10, root + 14]  # m3, m7, 9
            else:
                voicing = [root + 4, root + 10, root + 14]  # M3, m7, 9
            
            # Comping rhythm: syncopated
            hits = [(0, 1.0), (TICKS_PER_BEAT * 2 + TICKS_PER_BEAT // 2, 0.5)]
            
            for offset, duration_mult in hits:
                hit_time = bar_start + offset
                duration = int(TICKS_PER_BEAT * duration_mult)
                
                for note in voicing:
                    events.append({
                        'note': note,
                        'start': hit_time,
                        'duration': duration,
                        'velocity': DEFAULT_VELOCITY - 15
                    })
        
        return events
