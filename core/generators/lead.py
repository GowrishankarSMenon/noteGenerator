"""
Logic for generating lead melodies using Markov chains.
The "Singer" or "Soloist" - the only part using Markov Chains.

Incorporates sub-styles inspired by legendary guitarists and iconic bands
from the 50s-90s for rich, varied lead generation.

Technique-aware:  The Markov chain now outputs (pitch, duration, technique)
triples.  Technique-annotated arpeggio patterns are injected at phrase
boundaries.  The GuitarEffectsProcessor reads these hints and applies
effects deterministically, eliminating chaotic randomness.
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
from config.arpeggio_patterns import get_arpeggio_for_style, transpose_arpeggio
from utils.music_theory import get_scale_notes
from core.generators.guitar_effects import GuitarEffectsProcessor


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
        self._guitar_fx = GuitarEffectsProcessor()
    
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
    
    # ------------------------------------------------------------------
    # Section-aware parameter overrides
    # ------------------------------------------------------------------
    _SECTION_PARAMS = {
        'intro':      {'density_mult': 0.35, 'rest_mult': 2.5, 'riff_mult': 0.0,  'range_octaves': 1},
        'verse':      {'density_mult': 0.80, 'rest_mult': 1.0, 'riff_mult': 0.6,  'range_octaves': 2},
        'pre_chorus': {'density_mult': 0.90, 'rest_mult': 0.8, 'riff_mult': 0.7,  'range_octaves': 2},
        'chorus':     {'density_mult': 1.20, 'rest_mult': 0.5, 'riff_mult': 1.0,  'range_octaves': 2},
        'bridge':     {'density_mult': 0.60, 'rest_mult': 1.5, 'riff_mult': 0.3,  'range_octaves': 1},
        'solo':       {'density_mult': 1.40, 'rest_mult': 0.3, 'riff_mult': 1.2,  'range_octaves': 2},
        'buildup':    {'density_mult': 1.00, 'rest_mult': 0.7, 'riff_mult': 0.8,  'range_octaves': 2},
        'outro':      {'density_mult': 0.40, 'rest_mult': 2.0, 'riff_mult': 0.0,  'range_octaves': 1},
    }

    def _get_section_overrides(self, section: str) -> dict:
        return self._SECTION_PARAMS.get(section, self._SECTION_PARAMS['verse'])

    def generate(self, ctx: SongContext, harmony_track: List[Dict]) -> List[Dict]:
        """
        Generate lead melody using Markov chain sampling + riff injection.

        Section-aware: adapts density, rest probability, riff injection, and
        velocity to the current section/energy of each bar.
        """
        # Load mood-specific Markov model and style
        self._load_markov_model(ctx.mood)

        events = []
        ticks_per_bar = TICKS_PER_BEAT * ctx.time_signature[0]
        total_ticks = ctx.total_bars * ticks_per_bar

        # Get style parameters (base values — overridden per section)
        style = self._current_style
        style_name = style.get('name', '')
        base_note_density = style.get('note_density', 0.5)
        base_rest_probability = style.get('rest_probability', 0.15)
        swing = style.get('swing', 0.0)
        legato = style.get('legato', 0.7)
        preferred_intervals = style.get('preferred_intervals', [2, 3, 5, 7])

        # Calculate notes needed (over-estimate; we'll stop when ticks run out)
        avg_note_duration = TICKS_PER_BEAT / base_note_density
        estimated_notes = int(total_ticks / avg_note_duration) + 30

        # Generate base melody (now returns (pitch, duration, technique))
        melody = self._generate_melody(ctx, estimated_notes, preferred_intervals)

        # Build riff/arpeggio banks
        riff_bank = self._build_riff_bank(style_name, ctx.key_root_midi, self.lead_octave)
        arp_bank = self._build_arpeggio_bank(style_name, ctx.key_root_midi, self.lead_octave)

        # Base riff injection probability
        base_riff_prob = 0.5 if (riff_bank or arp_bank) else 0.0
        if style.get('tapping') or style.get('wah_wah'):
            base_riff_prob = 0.65
        if style.get('articulation') in ('shred', 'gallop'):
            base_riff_prob = 0.60

        # Place notes across the song
        current_tick = 0
        note_idx = 0
        beat_counter = 0
        bars_since_riff = 0
        phrase_counter = 0
        prev_section = None

        while current_tick < total_ticks and note_idx < len(melody):
            # ---- Current bar context ----
            bar_idx = current_tick // ticks_per_bar
            if bar_idx >= len(ctx.timeline):
                break

            bar = ctx.timeline[bar_idx]
            scale_notes = set(bar.scale_notes)
            section = bar.section
            energy = bar.energy

            # Section overrides
            sec = self._get_section_overrides(section)
            rest_probability = min(0.9, base_rest_probability * sec['rest_mult'])
            riff_inject_prob = base_riff_prob * sec['riff_mult']
            range_octs = sec['range_octaves']

            # Log section transitions
            if section != prev_section:
                prev_section = section

            # ---- RIFF INJECTION at phrase boundaries ----
            phrase_len = 8 if style.get('articulation') in ('legato', 'spacey', 'atmospheric', 'ethereal') else 4
            at_phrase_boundary = (bar_idx % phrase_len == 0) and bars_since_riff >= phrase_len

            if riff_bank and at_phrase_boundary and random.random() < riff_inject_prob:
                if arp_bank and random.random() < 0.6:
                    arp = random.choice(arp_bank)
                    arp_events, arp_duration = self._place_arpeggio(
                        arp, current_tick, total_ticks, scale_notes,
                        style, ticks_per_bar, beat_counter
                    )
                    # Scale velocity by energy
                    for ev in arp_events:
                        ev['velocity'] = max(30, int(ev['velocity'] * energy))
                    events.extend(arp_events)
                    current_tick += arp_duration
                    beat_counter += len(arp_events)
                else:
                    riff = random.choice(riff_bank)
                    riff_events, riff_duration = self._place_riff(
                        riff, current_tick, total_ticks, scale_notes,
                        style, ticks_per_bar, beat_counter
                    )
                    for ev in riff_events:
                        ev['velocity'] = max(30, int(ev['velocity'] * energy))
                    events.extend(riff_events)
                    current_tick += riff_duration
                    beat_counter += len(riff_events)
                bars_since_riff = 0
                phrase_counter += 1
                if random.random() < rest_probability * 1.5:
                    current_tick += random.choice([TICKS_PER_BEAT, TICKS_PER_BEAT * 2])
                continue

            elif arp_bank and at_phrase_boundary and random.random() < riff_inject_prob:
                arp = random.choice(arp_bank)
                arp_events, arp_duration = self._place_arpeggio(
                    arp, current_tick, total_ticks, scale_notes,
                    style, ticks_per_bar, beat_counter
                )
                for ev in arp_events:
                    ev['velocity'] = max(30, int(ev['velocity'] * energy))
                events.extend(arp_events)
                current_tick += arp_duration
                beat_counter += len(arp_events)
                bars_since_riff = 0
                phrase_counter += 1
                if random.random() < rest_probability * 1.5:
                    current_tick += random.choice([TICKS_PER_BEAT, TICKS_PER_BEAT * 2])
                continue

            bars_since_riff = max(bars_since_riff, (current_tick // ticks_per_bar) - bar_idx + 1)

            # ---- EXTRA REST for sparse sections (intro / outro) ----
            if section in ('intro', 'outro', 'bridge') and random.random() < rest_probability:
                current_tick += random.choice([TICKS_PER_BEAT, TICKS_PER_BEAT * 2])
                continue

            # ---- MARKOV NOTE ----
            melody_item = melody[note_idx]
            pitch = melody_item[0]
            duration = melody_item[1]
            technique = melody_item[2] if len(melody_item) > 2 else 'normal'

            # Snap to scale
            if scale_notes:
                pitch = self._snap_to_scale(pitch, scale_notes)

            # Restrict range based on section
            min_pitch = self.lead_octave * 12
            max_pitch = min_pitch + 12 * range_octs
            pitch = self._adjust_to_range(pitch, min_pitch, max_pitch)

            # Duration: stretch in sparse sections, compress in dense
            duration = self._humanize_duration(duration, ctx.mood, style)
            if sec['density_mult'] < 0.5:
                duration = int(duration * 1.6)
            elif sec['density_mult'] > 1.1:
                duration = max(TICKS_PER_BEAT // 8, int(duration * 0.8))

            # Swing feel
            actual_tick = current_tick
            if swing > 0:
                beat_position = (current_tick % TICKS_PER_BEAT) / TICKS_PER_BEAT
                if 0.45 < beat_position < 0.55:
                    actual_tick += int(TICKS_PER_BEAT * swing * 0.5)

            # Legato
            sounding_duration = int(duration * legato)

            # Bounds check
            if actual_tick + duration > total_ticks:
                duration = total_ticks - actual_tick
                sounding_duration = int(duration * legato)

            # Velocity — style-based then scaled by section energy
            velocity = self._get_velocity(actual_tick, ticks_per_bar, ctx.mood, style, beat_counter)
            velocity = max(30, int(velocity * energy))

            events.append({
                'note': pitch,
                'start': actual_tick,
                'duration': max(sounding_duration, TICKS_PER_BEAT // 8),
                'velocity': velocity,
                'technique': technique,
            })

            current_tick += duration
            note_idx += 1
            beat_counter += 1
            bars_since_riff += 1

            # Rest
            if random.random() < rest_probability:
                rest_options = self._get_rest_options(style, ctx.mood)
                rest_duration = random.choice(rest_options)
                current_tick += rest_duration

        # Apply guitar techniques (bends, hammer-ons, slides, vibrato, etc.)
        scale_notes_set = set(get_scale_notes(ctx.key_root_midi, ctx.scale_type))
        events = self._guitar_fx.process(events, style, scale_notes_set)
        technique_count = sum(1 for e in events if e.get('type') in ('pitchbend', 'control_change'))
        if technique_count > 0:
            print(f"  [Lead] Applied guitar techniques: {technique_count} articulation events")

        return events

    # -----------------------------------------------------------------
    # Riff injection helpers
    # -----------------------------------------------------------------
    def _build_riff_bank(self, style_name: str, key_root_midi: int, octave: int) -> list:
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
            key = tuple(tuple(item) for item in r)
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

        for item in riff:
            pitch = item[0]
            dur = item[1]
            technique = item[2] if len(item) > 2 else 'normal'
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
                'velocity': vel,
                'technique': technique,
            })
            current += dur
            beat_counter += 1

        total_dur = current - start_tick
        return events, total_dur

    # -----------------------------------------------------------------
    # Arpeggio injection helpers (technique-annotated)
    # -----------------------------------------------------------------
    def _build_arpeggio_bank(self, style_name: str, key_root_midi: int, octave: int) -> list:
        """Build a bank of transposed technique-annotated arpeggio patterns."""
        bank = []
        for _ in range(6):
            arp = get_arpeggio_for_style(style_name)
            if arp:
                transposed = transpose_arpeggio(arp, key_root_midi, octave)
                bank.append(transposed)
        # De-duplicate
        seen = set()
        unique = []
        for a in bank:
            key = tuple((p, d, t) for p, d, t in a)
            if key not in seen:
                seen.add(key)
                unique.append(a)
        return unique

    def _place_arpeggio(
        self, arpeggio: list, start_tick: int, total_ticks: int,
        scale_notes: Set[int], style: dict, ticks_per_bar: int, beat_counter: int
    ) -> Tuple[List[Dict], int]:
        """
        Place a technique-annotated arpeggio as MIDI events.
        Each note carries its technique hint for the effects processor.
        Returns (events, total_duration_consumed).
        """
        events = []
        current = start_tick
        legato = style.get('legato', 0.7)

        for pitch, dur, technique in arpeggio:
            if current + dur > total_ticks:
                break
            if scale_notes:
                pitch = self._snap_to_scale(pitch, scale_notes)
            pitch = self._adjust_to_range(pitch, self.lead_octave * 12, (self.lead_octave + 2) * 12)
            sounding = max(int(dur * legato), TICKS_PER_BEAT // 8)
            vel = self._get_velocity(current, ticks_per_bar, '', style, beat_counter)
            vel = min(127, vel + 5)
            events.append({
                'note': pitch,
                'start': current,
                'duration': sounding,
                'velocity': vel,
                'technique': technique,
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
    
    def _generate_melody(self, ctx: SongContext, length: int, preferred_intervals: List[int]) -> list:
        """
        Generate raw melody using Markov chain.
        Applies preferred intervals from the current style.
        
        Returns:
            List of (pitch, duration, technique) tuples
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
    
    def _shape_intervals(self, melody: list, preferred_intervals: List[int], scale_notes: Set[int]) -> list:
        """
        Subtly shape melodic intervals to match style preferences.
        Doesn't force changes but nudges melody toward preferred intervals.
        Preserves technique hints from Markov output.
        """
        shaped = [melody[0]]  # Keep first note
        
        for i in range(1, len(melody)):
            item = melody[i]
            pitch = item[0]
            duration = item[1]
            technique = item[2] if len(item) > 2 else 'normal'
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
            
            shaped.append((pitch, duration, technique))
        
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
