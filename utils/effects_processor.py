"""
Audio effects processor for post-rendering DSP.
Provides reverb, delay, distortion, phaser, and chorus effects.
All operations work on numpy float32 stereo arrays of shape (samples, 2).
"""

import numpy as np

# Available effects and their display info
EFFECTS_LIST = ['reverb', 'delay', 'distortion', 'phaser', 'chorus']

EFFECTS_PRESETS = {
    'gilmour_atmospheric': {
        'description': 'Gilmour-style atmospheric: lush reverb + warm delay',
        'drums':   {'reverb': 35, 'delay': 0,  'distortion': 0,  'phaser': 0,  'chorus': 0},
        'bass':    {'reverb': 30, 'delay': 10, 'distortion': 8,  'phaser': 0,  'chorus': 10},
        'harmony': {'reverb': 75, 'delay': 40, 'distortion': 0,  'phaser': 25, 'chorus': 30},
        'lead':    {'reverb': 90, 'delay': 65, 'distortion': 15, 'phaser': 30, 'chorus': 10},
    },
    'vanhalen_crunch': {
        'description': 'Van Halen crunch: heavy distortion + tight reverb',
        'drums':   {'reverb': 25, 'delay': 0,  'distortion': 0,  'phaser': 0,  'chorus': 0},
        'bass':    {'reverb': 20, 'delay': 0,  'distortion': 45, 'phaser': 0,  'chorus': 0},
        'harmony': {'reverb': 35, 'delay': 15, 'distortion': 60, 'phaser': 0,  'chorus': 10},
        'lead':    {'reverb': 40, 'delay': 25, 'distortion': 85, 'phaser': 10, 'chorus': 0},
    },
    'clean_jazz': {
        'description': 'Clean jazz: warm reverb + lush chorus',
        'drums':   {'reverb': 30, 'delay': 0,  'distortion': 0, 'phaser': 0,  'chorus': 0},
        'bass':    {'reverb': 25, 'delay': 0,  'distortion': 0, 'phaser': 0,  'chorus': 15},
        'harmony': {'reverb': 55, 'delay': 10, 'distortion': 0, 'phaser': 0,  'chorus': 40},
        'lead':    {'reverb': 60, 'delay': 20, 'distortion': 0, 'phaser': 10, 'chorus': 30},
    },
    'space_rock': {
        'description': 'Space rock: massive reverb + delay + phaser',
        'drums':   {'reverb': 50, 'delay': 25, 'distortion': 0,  'phaser': 20, 'chorus': 0},
        'bass':    {'reverb': 45, 'delay': 20, 'distortion': 25, 'phaser': 15, 'chorus': 0},
        'harmony': {'reverb': 85, 'delay': 55, 'distortion': 0,  'phaser': 45, 'chorus': 35},
        'lead':    {'reverb': 90, 'delay': 70, 'distortion': 30, 'phaser': 50, 'chorus': 20},
    },
    'classic_rock': {
        'description': 'Classic rock: crunchy distortion + room reverb',
        'drums':   {'reverb': 35, 'delay': 0,  'distortion': 0,  'phaser': 0,  'chorus': 0},
        'bass':    {'reverb': 20, 'delay': 0,  'distortion': 35, 'phaser': 0,  'chorus': 0},
        'harmony': {'reverb': 45, 'delay': 20, 'distortion': 40, 'phaser': 10, 'chorus': 0},
        'lead':    {'reverb': 50, 'delay': 35, 'distortion': 65, 'phaser': 20, 'chorus': 0},
    },
    'ambient_pad': {
        'description': 'Ambient pad: deep reverb + chorus + slow phaser',
        'drums':   {'reverb': 25, 'delay': 10, 'distortion': 0, 'phaser': 0,  'chorus': 10},
        'bass':    {'reverb': 55, 'delay': 30, 'distortion': 0, 'phaser': 0,  'chorus': 25},
        'harmony': {'reverb': 90, 'delay': 45, 'distortion': 0, 'phaser': 30, 'chorus': 55},
        'lead':    {'reverb': 85, 'delay': 55, 'distortion': 0, 'phaser': 40, 'chorus': 45},
    },
    'dry_clean': {
        'description': 'Dry / Clean: no effects applied',
        'drums':   {'reverb': 0, 'delay': 0, 'distortion': 0, 'phaser': 0, 'chorus': 0},
        'bass':    {'reverb': 0, 'delay': 0, 'distortion': 0, 'phaser': 0, 'chorus': 0},
        'harmony': {'reverb': 0, 'delay': 0, 'distortion': 0, 'phaser': 0, 'chorus': 0},
        'lead':    {'reverb': 0, 'delay': 0, 'distortion': 0, 'phaser': 0, 'chorus': 0},
    },
}


def get_effects_preset_names():
    """Return list of preset names."""
    return list(EFFECTS_PRESETS.keys())


def format_preset_name(name: str) -> str:
    """Format a preset internal name for display."""
    return name.replace('_', ' ').title()


class EffectsProcessor:
    """Applies audio effects to numpy audio arrays (float32, stereo)."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def apply_effects_chain(self, audio: np.ndarray, effects: dict) -> np.ndarray:
        """
        Apply a chain of effects to audio data.

        Args:
            audio: Stereo float32 array of shape (samples, 2)
            effects: Dict mapping effect_name -> level (0-100)
                     e.g., {'reverb': 50, 'delay': 30, 'distortion': 0}

        Returns:
            Processed audio array
        """
        if not effects or all(v <= 0 for v in effects.values()):
            return audio

        result = audio.copy()

        # Apply in musically logical order: distortion -> phaser -> chorus -> delay -> reverb
        order = ['distortion', 'phaser', 'chorus', 'delay', 'reverb']

        for fx_name in order:
            level = effects.get(fx_name, 0)
            if level <= 0:
                continue

            wet = level / 100.0  # Convert 0-100 to 0.0-1.0

            if fx_name == 'reverb':
                result = self._reverb(result, wet)
            elif fx_name == 'delay':
                result = self._delay(result, wet)
            elif fx_name == 'distortion':
                result = self._distortion(result, wet)
            elif fx_name == 'phaser':
                result = self._phaser(result, wet)
            elif fx_name == 'chorus':
                result = self._chorus(result, wet)

        return result

    # -----------------------------------------------------------------
    # REVERB - Dense multi-tap Schroeder-style with long tail
    # -----------------------------------------------------------------
    def _reverb(self, audio: np.ndarray, wet: float) -> np.ndarray:
        """Dense multi-tap reverb with early reflections and long tail."""
        # Early reflections (short, bright)
        early_taps = [
            (0.011, 0.40), (0.019, 0.35), (0.029, 0.55), (0.043, 0.50),
            (0.061, 0.45), (0.079, 0.40),
        ]
        # Late reverb tail (longer, diffuse)
        late_taps = [
            (0.103, 0.38), (0.139, 0.32), (0.179, 0.26), (0.223, 0.20),
            (0.281, 0.16), (0.347, 0.12), (0.419, 0.09), (0.503, 0.06),
            (0.601, 0.04), (0.709, 0.03), (0.837, 0.02), (1.001, 0.015),
        ]
        all_taps = early_taps + late_taps

        reverb_buf = np.zeros_like(audio, dtype=np.float64)

        for delay_sec, gain in all_taps:
            delay_samp = int(delay_sec * self.sample_rate)
            if delay_samp >= len(audio):
                continue
            src = audio[:len(audio) - delay_samp].astype(np.float64)
            reverb_buf[delay_samp:delay_samp + len(src)] += src * gain

        # Stronger wet/dry mix: at wet=1.0, dry drops to 0.35 and reverb at full
        dry_amount = 1.0 - wet * 0.65
        output = audio.astype(np.float64) * dry_amount + reverb_buf * (wet * 1.6)
        return np.clip(output, -1.0, 1.0).astype(np.float32)

    # -----------------------------------------------------------------
    # DELAY - Echo with feedback taps (prominent)
    # -----------------------------------------------------------------
    def _delay(self, audio: np.ndarray, wet: float) -> np.ndarray:
        """Echo/delay with prominent feedback and stereo ping-pong feel."""
        delay_samp = int(0.35 * self.sample_rate)  # ~350ms
        feedback = 0.55  # Higher feedback for longer echo trail

        output = audio.astype(np.float64).copy()

        for tap in range(1, 10):  # More taps for longer trail
            offset = delay_samp * tap
            if offset >= len(audio):
                break
            gain = wet * 1.3 * (feedback ** (tap - 1))  # Boosted initial level
            end = min(offset + len(audio), len(audio))
            src_len = end - offset
            echo = audio[:src_len].astype(np.float64) * gain
            # Alternate panning for stereo width
            if echo.ndim == 2 and echo.shape[1] == 2 and tap % 2 == 0:
                echo[:, 0] *= 0.7
                echo[:, 1] *= 1.3
            elif echo.ndim == 2 and echo.shape[1] == 2:
                echo[:, 0] *= 1.3
                echo[:, 1] *= 0.7
            output[offset:end] += echo

        return np.clip(output, -1.0, 1.0).astype(np.float32)

    # -----------------------------------------------------------------
    # DISTORTION - Soft-clip (tanh waveshaping) with harmonic warmth
    # -----------------------------------------------------------------
    def _distortion(self, audio: np.ndarray, wet: float) -> np.ndarray:
        """Soft-clip distortion using tanh waveshaping with warm overtones."""
        gain = 1.0 + wet * 20.0  # Stronger drive range
        driven = audio.astype(np.float64) * gain
        clipped = np.tanh(driven)

        # Add subtle second-harmonic warmth for low-mid body
        if wet > 0.15:
            harmonic = np.tanh(driven * 0.5) * 0.3
            clipped = clipped * 0.8 + harmonic * 0.2

        # Tone roll-off for darker overdrive at higher settings
        if wet > 0.25:
            kernel_size = max(2, int(wet * 8))
            kernel = np.ones(kernel_size) / kernel_size
            for ch in range(clipped.shape[1]):
                clipped[:, ch] = np.convolve(clipped[:, ch], kernel, mode='same')

        # More aggressive wet/dry: distortion fully replaces dry at wet=1
        output = audio.astype(np.float64) * (1.0 - wet * 0.85) + clipped * wet
        return np.clip(output, -1.0, 1.0).astype(np.float32)

    # -----------------------------------------------------------------
    # PHASER - Multi-stage vectorised modulated allpass
    # -----------------------------------------------------------------
    def _phaser(self, audio: np.ndarray, wet: float) -> np.ndarray:
        """Multi-stage phaser with deep sweep (fully vectorised)."""
        n = len(audio)
        t = np.arange(n, dtype=np.float64) / self.sample_rate

        phased = audio.astype(np.float64).copy()

        # 4 cascaded stages with staggered LFO phases for notch depth
        stages = [
            (0.30, 0.0,    0.001, 0.007),  # (rate_hz, phase_offset, min_delay, max_delay)
            (0.30, 0.25,   0.0015, 0.008),
            (0.30, 0.50,   0.002, 0.009),
            (0.30, 0.75,   0.001, 0.010),
        ]
        indices = np.arange(n, dtype=np.int64)

        for rate, phase, min_d_sec, max_d_sec in stages:
            lfo = (np.sin(2.0 * np.pi * rate * t + phase * 2.0 * np.pi) + 1.0) / 2.0
            min_d = int(min_d_sec * self.sample_rate)
            max_d = int(max_d_sec * self.sample_rate)
            delays = (min_d + lfo * (max_d - min_d)).astype(np.int64)
            source_idx = np.clip(indices - delays, 0, n - 1)
            delayed = phased[source_idx] if phased.ndim == 1 else phased[source_idx]
            phased = phased + delayed * 0.75

        # Strong mix: at wet=1, phased dominates
        output = audio.astype(np.float64) * (1.0 - wet * 0.6) + phased * (wet * 0.6)
        return np.clip(output, -1.0, 1.0).astype(np.float32)

    # -----------------------------------------------------------------
    # CHORUS - Rich multi-voice modulated-delay
    # -----------------------------------------------------------------
    def _chorus(self, audio: np.ndarray, wet: float) -> np.ndarray:
        """Rich chorus with 3 detuned voices and stereo spread."""
        n = len(audio)
        t = np.arange(n, dtype=np.float64) / self.sample_rate

        output = audio.astype(np.float64).copy()
        indices = np.arange(n, dtype=np.int64)

        # Three detuned voices with different rates for richness
        voices = [
            (0.18, 0.008, 0.002, 0.8, 1.2),  # (rate, max_d, min_d, L_gain, R_gain)
            (0.27, 0.010, 0.003, 1.2, 0.8),
            (0.35, 0.012, 0.004, 1.0, 1.0),
        ]

        for rate, max_d, min_d, lg, rg in voices:
            lfo = (np.sin(2.0 * np.pi * rate * t) + 1.0) / 2.0
            min_samp = int(min_d * self.sample_rate)
            max_samp = int(max_d * self.sample_rate)
            delays = (min_samp + lfo * (max_samp - min_samp)).astype(np.int64)
            source_idx = np.clip(indices - delays, 0, n - 1)

            voice = audio[source_idx].astype(np.float64) * (wet * 0.65)
            # Apply stereo spread
            if voice.ndim == 2 and voice.shape[1] == 2:
                voice[:, 0] *= lg
                voice[:, 1] *= rg
            output += voice

        # Gentle normalise
        output /= (1.0 + wet * 0.7)
        return np.clip(output, -1.0, 1.0).astype(np.float32)
