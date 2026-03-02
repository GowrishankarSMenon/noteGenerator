"""
Logic for generating lead melodies using Markov chains.
The "Singer" or "Soloist" - the only part using Markov Chains.

Incorporates sub-styles inspired by legendary guitarists and iconic bands
from the 50s-90s for rich, varied lead generation.
"""

import sys
import os
import random
from typing import List, Dict, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.context import SongContext
from models.markov_chain import MarkovChain
from config.settings import TICKS_PER_BEAT, DEFAULT_VELOCITY, get_dataset_path
from config.lead_styles import LEAD_STYLES, get_random_substyle
from config.riff_patterns import get_riff_for_style, transpose_riff
from utils.music_theory import get_scale_notes


class LeadGenerator:
    """
    Generates lead melodies using Markov chain models.
    Loads mood-specific training data for each mood.
    Uses sub-styles inspired by legendary guitarists for variety.
    Supports 3 style modes: Auto (mood-based), Random, Manual Selection.
    """
    
    def __init__(self):
        self.lead_octave = 5  # Lead plays in upper register
        self.markov = MarkovChain(order=2)
        self._current_mood = None  # Track loaded mood
        self._current_style = None  # Current sub-style being used
        self._forced_style = None  # Set via set_style() for manual selection
        self._style_mode = 'auto'  # 'auto', 'random', or 'selection'
    
    def set_style(self, mode: str = 'auto', style_name: str = None):
        """
        Set the style selection mode for lead generation.
        
        Args:
            mode: 'auto' (mood-based), 'random' (any style), 'selection' (user picks)
            style_name: Specific style name when mode='selection'
        """
        self._style_mode = mode
        self._forced_style = style_name if mode == 'selection' else None
        # Reset mood to force re-selection on next generate
        self._current_mood = None
        print(f"[Lead] Style mode set to: {mode}" + (f" ({style_name})" if style_name else ""))
    
    def _load_markov_model(self, mood: str):
        """Load and train the Markov model from mood-specific dataset."""
        if self._current_mood == mood and self._style_mode == 'auto':
            return  # Already loaded for auto mode
        
        # Select sub-style based on mode
        if self._style_mode == 'selection' and self._forced_style:
            # User manually selected a specific style
            found = None
            for m, config in LEAD_STYLES.items():
                for sub in config['sub_styles']:
                    if sub['name'] == self._forced_style:
                        found = sub
                        break
                if found:
                    break
            self._current_style = found or get_random_substyle(mood)
            print(f"  [Lead] Using selected style: {self._current_style.get('name', 'default')}")
        elif self._style_mode == 'random':
            # Random: pick from all moods' sub-styles
            import random as _rand
            all_styles = []
            for m, config in LEAD_STYLES.items():
                all_styles.extend(config['sub_styles'])
            self._current_style = _rand.choice(all_styles)
            print(f"  [Lead] Random style: {self._current_style.get('name', 'default')}")
        else:
            # Auto: mood-based random selection (original behavior)
            self._current_style = get_random_substyle(mood)
            print(f"  [Lead] Auto style: {self._current_style.get('name', 'default')}")
        
        self.lead_octave = self._current_style.get('octave', 5)
        
        dataset_path = get_dataset_path(mood)
        if os.path.exists(dataset_path):
            self.markov = MarkovChain(order=2)  # Reset chain
            self.markov.train_from_csv(dataset_path)
            self._current_mood = mood
            print(f"Loaded {mood} dataset from {dataset_path}")
        else:
            print(f"Dataset not found at {dataset_path}, using default training data")
            self.markov._create_default_training_data()
    
    def get_current_instrument(self) -> str:
        """Return the instrument for the current sub-style."""
        if self._current_style:
            return self._current_style.get('instrument', 'clean_guitar')
        return 'clean_guitar'
    
    def generate(self, ctx: SongContext, harmony_track: List[Dict]) -> List[Dict]:
        """
        Generate lead melody using Markov chain sampling + riff injection.

        Riff injection: If the current sub-style has mapped riff patterns
        (in riff_patterns.py), those iconic riffs are woven in at phrase
        boundaries so the output is immediately identifiable.

        Args:
            ctx: The SongContext with key and scale
            harmony_track: Harmony track (for reference)

        Returns:
            List of MIDI events for lead melody
        """
        # Load mood-specific Markov model and style
        self._load_markov_model(ctx.mood)

        events = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        total_ticks = ctx.total_bars * ticks_per_bar

        # Get style parameters
        style = self._current_style
        style_name = style.get('name', '')
        note_density = style.get('note_density', 0.5)
        rest_probability = style.get('rest_probability', 0.15)
        swing = style.get('swing', 0.0)
        legato = style.get('legato', 0.7)
        preferred_intervals = style.get('preferred_intervals', [2, 3, 5, 7])

        # Calculate notes based on density
        avg_note_duration = TICKS_PER_BEAT / note_density
        estimated_notes = int(total_ticks / avg_note_duration) + 10

        # Generate base melody using Markov chain
        melody = self._generate_melody(ctx, estimated_notes, preferred_intervals)

        # Build a riff bank for injection (transposed to the song's key)
        riff_bank = self._build_riff_bank(style_name, ctx.key_root_midi, self.lead_octave)

        # Riff injection probability - higher for styles with strong riff identity
        riff_inject_prob = 0.5 if riff_bank else 0.0
        if style.get('tapping') or style.get('wah_wah'):
            riff_inject_prob = 0.65  # More riff-heavy for virtuoso styles
        if style.get('articulation') in ('shred', 'gallop'):
            riff_inject_prob = 0.60

        # Place notes across the song
        current_tick = 0
        note_idx = 0
        beat_counter = 0
        bars_since_riff = 0
        phrase_counter = 0

        while current_tick < total_ticks and note_idx < len(melody):
            # Get current bar context
            bar_idx = current_tick // ticks_per_bar
            if bar_idx >= len(ctx.timeline):
                break

            bar = ctx.timeline[bar_idx]
            scale_notes = set(bar.scale_notes)

            # ---- RIFF INJECTION at phrase boundaries ----
            # Every 4 bars (or 8 bars for spacey styles), try to inject a riff
            phrase_len = 8 if style.get('articulation') in ('legato', 'spacey', 'atmospheric', 'ethereal') else 4
            at_phrase_boundary = (bar_idx % phrase_len == 0) and bars_since_riff >= phrase_len

            if riff_bank and at_phrase_boundary and random.random() < riff_inject_prob:
                riff = random.choice(riff_bank)
                riff_events, riff_duration = self._place_riff(
                    riff, current_tick, total_ticks, scale_notes,
                    style, ticks_per_bar, beat_counter
                )
                events.extend(riff_events)
                current_tick += riff_duration
                beat_counter += len(riff_events)
                bars_since_riff = 0
                phrase_counter += 1

                # Optional rest after riff
                if random.random() < rest_probability * 1.5:
                    current_tick += random.choice([TICKS_PER_BEAT, TICKS_PER_BEAT * 2])
                continue

            bars_since_riff = max(bars_since_riff, (current_tick // ticks_per_bar) - bar_idx + 1)

            # ---- MARKOV NOTE ----
            # Get note from melody
            pitch, duration = melody[note_idx]

            # Adjust pitch to current scale (snap to scale)
            if scale_notes:
                pitch = self._snap_to_scale(pitch, scale_notes)

            # Ensure note is in lead octave range (allow 2 octaves for expression)
            pitch = self._adjust_to_range(pitch, self.lead_octave * 12, (self.lead_octave + 2) * 12)

            # Apply stylistic duration modification
            duration = self._humanize_duration(duration, ctx.mood, style)

            # Apply swing feel (shift offbeats)
            actual_tick = current_tick
            if swing > 0:
                beat_position = (current_tick % TICKS_PER_BEAT) / TICKS_PER_BEAT
                if 0.45 < beat_position < 0.55:  # Offbeat
                    actual_tick += int(TICKS_PER_BEAT * swing * 0.5)

            # Apply legato to note duration
            sounding_duration = int(duration * legato)

            # Check we don't go past end
            if actual_tick + duration > total_ticks:
                duration = total_ticks - actual_tick
                sounding_duration = int(duration * legato)

            # Get velocity based on style
            velocity = self._get_velocity(actual_tick, ticks_per_bar, ctx.mood, style, beat_counter)

            events.append({
                'note': pitch,
                'start': actual_tick,
                'duration': max(sounding_duration, TICKS_PER_BEAT // 8),
                'velocity': velocity
            })

            current_tick += duration
            note_idx += 1
            beat_counter += 1
            bars_since_riff += 1

            # Apply rest based on style's probability
            if random.random() < rest_probability:
                rest_options = self._get_rest_options(style, ctx.mood)
                rest_duration = random.choice(rest_options)
                current_tick += rest_duration

        return events

    # -----------------------------------------------------------------
    # Riff injection helpers
    # -----------------------------------------------------------------
    def _build_riff_bank(self, style_name: str, key_root_midi: int, octave: int) -> List[List[Tuple[int, int]]]:
        """Build a bank of transposed riff patterns for the current style."""
        bank = []
        # Try to get multiple riffs for variety
        for _ in range(6):
            riff = get_riff_for_style(style_name)
            if riff:
                transposed = transpose_riff(riff, key_root_midi, octave)
                bank.append(transposed)
        # De-duplicate (same riff can appear via random picks)
        seen = set()
        unique_bank = []
        for r in bank:
            key = tuple((p, d) for p, d in r)
            if key not in seen:
                seen.add(key)
                unique_bank.append(r)
        return unique_bank

    def _place_riff(
        self, riff: List[Tuple[int, int]], start_tick: int, total_ticks: int,
        scale_notes: Set[int], style: dict, ticks_per_bar: int, beat_counter: int
    ) -> Tuple[List[Dict], int]:
        """
        Place a riff pattern as MIDI events starting at start_tick.
        Returns (events, total_duration_consumed).
        """
        events = []
        current = start_tick
        legato = style.get('legato', 0.7)

        for pitch, dur in riff:
            if current + dur > total_ticks:
                break
            # Snap to scale for musical correctness
            if scale_notes:
                pitch = self._snap_to_scale(pitch, scale_notes)
            # Keep in range
            pitch = self._adjust_to_range(pitch, self.lead_octave * 12, (self.lead_octave + 2) * 12)
            sounding = max(int(dur * legato), TICKS_PER_BEAT // 8)
            vel = self._get_velocity(current, ticks_per_bar, '', style, beat_counter)
            # Riff notes get a slight velocity boost to stand out
            vel = min(127, vel + 5)
            events.append({
                'note': pitch,
                'start': current,
                'duration': sounding,
                'velocity': vel
            })
            current += dur
            beat_counter += 1

        total_dur = current - start_tick
        return events, total_dur
    
    def _get_rest_options(self, style: dict, mood: str) -> List[int]:
        """Get appropriate rest durations based on mood and style."""
        articulation = style.get('articulation', 'medium')
        
        if articulation == 'sparse' or mood == 'calm':
            # Longer rests for spacey, calm moods
            return [TICKS_PER_BEAT, TICKS_PER_BEAT * 2, TICKS_PER_BEAT * 3]
        elif articulation == 'staccato' or articulation == 'funky':
            # Short, punchy rests
            return [TICKS_PER_BEAT // 4, TICKS_PER_BEAT // 2]
        elif articulation == 'fast':
            # Minimal rests for bebop-style lines
            return [TICKS_PER_BEAT // 4, TICKS_PER_BEAT // 2]
        else:
            # Standard rests
            return [TICKS_PER_BEAT // 2, TICKS_PER_BEAT]
    
    def _generate_melody(self, ctx: SongContext, length: int, preferred_intervals: List[int]) -> List[Tuple[int, int]]:
        """
        Generate raw melody using Markov chain.
        Applies preferred intervals from the current style.
        
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
        
        # Apply interval preferences for stylistic shaping
        if preferred_intervals and random.random() < 0.6:  # 60% chance to shape intervals
            melody = self._shape_intervals(melody, preferred_intervals, scale_notes)
        
        return melody
    
    def _shape_intervals(self, melody: List[Tuple[int, int]], preferred_intervals: List[int], scale_notes: Set[int]) -> List[Tuple[int, int]]:
        """
        Subtly shape melodic intervals to match style preferences.
        Doesn't force changes but nudges melody toward preferred intervals.
        """
        shaped = [melody[0]]  # Keep first note
        
        for i in range(1, len(melody)):
            pitch, duration = melody[i]
            prev_pitch = shaped[i-1][0]
            
            # Calculate current interval (in semitones)
            current_interval = abs(pitch - prev_pitch) % 12
            
            # If interval is not preferred and we roll the dice, try to find a better note
            if current_interval not in preferred_intervals and random.random() < 0.4:
                # Try to find a scale note with preferred interval
                candidates = []
                for interval in preferred_intervals:
                    up_note = prev_pitch + interval
                    down_note = prev_pitch - interval
                    
                    # Check if these notes are in scale (pitch class)
                    if (up_note % 12) in {n % 12 for n in scale_notes}:
                        candidates.append(up_note)
                    if (down_note % 12) in {n % 12 for n in scale_notes}:
                        candidates.append(down_note)
                
                if candidates:
                    # Pick a candidate close to the original pitch
                    pitch = min(candidates, key=lambda x: abs(x - pitch))
            
            shaped.append((pitch, duration))
        
        return shaped
    
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
    
    def _humanize_duration(self, duration: int, mood: str, style: dict) -> int:
        """
        Apply mood and style-specific variation to note durations.
        Different styles use different rhythmic vocabularies.
        """
        articulation = style.get('articulation', 'medium')
        quantize = style.get('quantize', False)
        
        # Define duration options based on style
        if quantize:
            # Strict electronic quantization
            common_durations = [
                TICKS_PER_BEAT // 4,
                TICKS_PER_BEAT // 2,
                TICKS_PER_BEAT,
            ]
            closest = min(common_durations, key=lambda x: abs(x - duration))
            return closest  # No humanization for quantized styles
        
        if articulation == 'legato' or mood in ['sad', 'calm']:
            # Longer, more flowing notes
            common_durations = [
                TICKS_PER_BEAT // 2,
                TICKS_PER_BEAT,
                TICKS_PER_BEAT * 2,
                TICKS_PER_BEAT * 3,
            ]
        elif articulation == 'staccato':
            # Short, punchy notes
            common_durations = [
                TICKS_PER_BEAT // 8,
                TICKS_PER_BEAT // 4,
                TICKS_PER_BEAT // 2,
            ]
        elif articulation == 'fast':
            # Bebop-style rapid notes
            common_durations = [
                TICKS_PER_BEAT // 6,  # Triplets
                TICKS_PER_BEAT // 4,
                TICKS_PER_BEAT // 3,
                TICKS_PER_BEAT // 2,
            ]
        elif articulation == 'aggressive' and mood == 'rock':
            # Rock power - varied but punchy
            common_durations = [
                TICKS_PER_BEAT // 4,
                TICKS_PER_BEAT // 2,
                TICKS_PER_BEAT,
            ]
        elif articulation == 'shred':
            # Van Halen / Dimebag - extremely fast passages
            common_durations = [
                TICKS_PER_BEAT // 8,
                TICKS_PER_BEAT // 6,
                TICKS_PER_BEAT // 4,
            ]
        elif articulation == 'gallop':
            # Iron Maiden gallop - triplet feel
            common_durations = [
                TICKS_PER_BEAT // 6,   # Triplet sixteenth
                TICKS_PER_BEAT // 4,
                TICKS_PER_BEAT // 3,   # Triplet eighth
            ]
        elif articulation == 'expressive':
            # Blues expressive - more varied
            common_durations = [
                TICKS_PER_BEAT // 3,  # Triplet feel
                TICKS_PER_BEAT // 2,
                TICKS_PER_BEAT * 2 // 3,
                TICKS_PER_BEAT,
                TICKS_PER_BEAT * 2,
            ]
        else:
            # Standard medium articulation
            common_durations = [
                TICKS_PER_BEAT // 4,
                TICKS_PER_BEAT // 2,
                TICKS_PER_BEAT,
                TICKS_PER_BEAT * 2,
            ]
        
        # Find closest common duration
        closest = min(common_durations, key=lambda x: abs(x - duration))
        
        # Add slight humanization (rubato) for non-electronic styles
        rubato = style.get('rubato', 0.0)
        if rubato > 0 or articulation not in ['precise', 'quantize']:
            variation = random.randint(-25, 25)
            if rubato > 0:
                variation = int(variation * (1 + rubato * 2))
        else:
            variation = 0
        
        return max(TICKS_PER_BEAT // 8, closest + variation)
    
    def _get_velocity(self, tick: int, ticks_per_bar: int, mood: str, style: dict, beat_counter: int) -> int:
        """
        Get velocity based on position, mood, and style.
        Different styles have different dynamic patterns.
        """
        position_in_bar = tick % ticks_per_bar
        beat = position_in_bar // TICKS_PER_BEAT
        
        # Get velocity range from style
        vel_min, vel_max = style.get('velocity_range', (70, 100))
        base_velocity = (vel_min + vel_max) // 2
        vel_range = vel_max - vel_min
        
        articulation = style.get('articulation', 'medium')
        
        # Apply different dynamic patterns based on articulation/mood
        if articulation == 'aggressive':
            # Rock aggressive - heavy emphasis on backbeats
            if beat in [1, 3]:
                velocity = base_velocity + int(vel_range * 0.4)
            elif beat == 0:
                velocity = base_velocity + int(vel_range * 0.2)
            else:
                velocity = base_velocity + random.randint(-10, 10)

        elif articulation == 'shred':
            # Shred - consistently loud with accent every 4 notes
            if beat_counter % 4 == 0:
                velocity = vel_max
            else:
                velocity = base_velocity + int(vel_range * 0.3) + random.randint(-5, 5)

        elif articulation == 'gallop':
            # Gallop - accent on the downbeat of each triplet group
            if beat_counter % 3 == 0:
                velocity = base_velocity + int(vel_range * 0.35)
            else:
                velocity = base_velocity + random.randint(-8, 5)
                
        elif articulation == 'expressive':
            # Blues/jazz expressive - dynamic swells
            phrase_position = beat_counter % 8  # 8-note phrase
            if phrase_position < 2:
                velocity = base_velocity - int(vel_range * 0.2)  # Start soft
            elif phrase_position < 5:
                velocity = base_velocity + int(vel_range * 0.3)  # Build up
            else:
                velocity = base_velocity  # Settle
            velocity += random.randint(-8, 8)
            
        elif articulation == 'sparse':
            # Cool jazz/ambient - soft and even
            velocity = vel_min + random.randint(0, int(vel_range * 0.6))
            
        elif articulation == 'staccato' or articulation == 'funky':
            # Funk staccato - accents on upbeats
            sub_beat = (position_in_bar % TICKS_PER_BEAT) // (TICKS_PER_BEAT // 4)
            if sub_beat in [1, 3]:  # Upbeats
                velocity = base_velocity + int(vel_range * 0.35)
            else:
                velocity = base_velocity - int(vel_range * 0.1)
            velocity += random.randint(-5, 5)
            
        elif articulation == 'gentle' or articulation == 'ethereal':
            # Calm, gentle - consistent soft dynamics
            velocity = vel_min + random.randint(5, int(vel_range * 0.5))
            
        elif articulation == 'fast':
            # Bebop - slight accent variations for flow
            if beat_counter % 4 == 0:
                velocity = base_velocity + 10
            else:
                velocity = base_velocity + random.randint(-10, 5)
                
        else:
            # Default - standard beat emphasis
            if beat == 0:
                velocity = base_velocity + int(vel_range * 0.25)
            elif beat == 2:
                velocity = base_velocity + int(vel_range * 0.1)
            else:
                velocity = base_velocity + random.randint(-8, 5)
        
        # Clamp velocity to valid MIDI range
        return max(1, min(127, velocity))
