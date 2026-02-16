"""
Guitar technique definitions for MIDI articulation.

Defines how guitar-specific playing techniques translate to MIDI:
  - Pitch Bend:  bending, slides, vibrato
  - Note Overlap: hammer-on, pull-off, legato runs
  - Short Notes:  staccato, palm muting
  - Fast Runs:    tapping (two-hand), sweep picking
  - CC Messages:  expression (CC11), modulation/vibrato (CC1)

Each technique has parameters controlling its MIDI implementation.
Styles reference these by name; the GuitarEffectsProcessor converts
them into concrete MIDI events at render time.
"""

from config.settings import TICKS_PER_BEAT

# =============================================================================
# TECHNIQUE PARAMETER DEFINITIONS
# =============================================================================

BEND_PROFILES = {
    # Half-step bend (1 semitone) — blues standard
    'half': {
        'semitones': 1,
        'attack_ticks': TICKS_PER_BEAT // 4,   # How fast the bend rises
        'release_ticks': TICKS_PER_BEAT // 6,   # How fast it returns (0 = hold)
        'hold': True,                            # Hold at peak?
        'steps': 8,                              # PB interpolation resolution
    },
    # Whole-step bend (2 semitones) — rock/blues standard
    'whole': {
        'semitones': 2,
        'attack_ticks': TICKS_PER_BEAT // 3,
        'release_ticks': TICKS_PER_BEAT // 4,
        'hold': True,
        'steps': 12,
    },
    # Minor-third bend (3 semitones) — Gilmour / blues scream
    'minor_third': {
        'semitones': 3,
        'attack_ticks': TICKS_PER_BEAT // 2,
        'release_ticks': TICKS_PER_BEAT // 3,
        'hold': True,
        'steps': 16,
    },
    # Pre-bend + release — note starts bent, releases down
    'pre_bend_release': {
        'semitones': 2,
        'attack_ticks': 0,                       # Instant (pre-bent)
        'release_ticks': TICKS_PER_BEAT // 3,
        'hold': False,
        'pre_bent': True,
        'steps': 10,
    },
    # Quick grace-note bend — fast flick up
    'grace': {
        'semitones': 1,
        'attack_ticks': TICKS_PER_BEAT // 8,
        'release_ticks': 0,
        'hold': True,
        'steps': 4,
    },
    # Slow blues bend — BB King / Clapton
    'slow_blues': {
        'semitones': 2,
        'attack_ticks': TICKS_PER_BEAT,
        'release_ticks': TICKS_PER_BEAT // 2,
        'hold': True,
        'steps': 20,
    },
}

VIBRATO_PROFILES = {
    # Subtle — clean/jazz
    'subtle': {
        'depth_cents': 20,       # Peak deviation in cents (100 cents = 1 semitone)
        'rate_hz': 5.0,          # Oscillation speed
        'delay_ticks': TICKS_PER_BEAT // 2,  # Wait before vibrato starts
        'cc1_min': 0,
        'cc1_max': 40,
    },
    # Standard — rock/blues
    'standard': {
        'depth_cents': 40,
        'rate_hz': 5.5,
        'delay_ticks': TICKS_PER_BEAT // 4,
        'cc1_min': 0,
        'cc1_max': 70,
    },
    # Wide — Gilmour, BB King, SRV
    'wide': {
        'depth_cents': 70,
        'rate_hz': 5.0,
        'delay_ticks': TICKS_PER_BEAT // 4,
        'cc1_min': 0,
        'cc1_max': 100,
    },
    # Fast — metal shred vibrato
    'fast': {
        'depth_cents': 35,
        'rate_hz': 7.0,
        'delay_ticks': TICKS_PER_BEAT // 8,
        'cc1_min': 0,
        'cc1_max': 80,
    },
}

SLIDE_PROFILES = {
    # Short slide into note (2 semitones)
    'into': {
        'semitones': 2,
        'duration_ticks': TICKS_PER_BEAT // 4,
        'direction': 'up',       # 'up' or 'down'
        'steps': 6,
    },
    # Slide out of note
    'out_of': {
        'semitones': 3,
        'duration_ticks': TICKS_PER_BEAT // 3,
        'direction': 'down',
        'steps': 8,
    },
    # Long glissando between notes
    'glissando': {
        'semitones': 5,          # Max; actual adapts to interval
        'duration_ticks': TICKS_PER_BEAT // 2,
        'direction': 'auto',     # Follows melodic direction
        'steps': 12,
    },
}

# =============================================================================
# TECHNIQUE PROBABILITY PROFILES PER ARTICULATION TYPE
# =============================================================================
# Keys match 'articulation' values from lead_styles.py.
# Each maps technique names to a probability (0.0–1.0) and preferred variant.

TECHNIQUE_PROFILES = {
    'aggressive': {
        'bend':       {'prob': 0.25, 'variants': ['whole', 'half', 'grace']},
        'hammer_on':  {'prob': 0.30, 'max_run': 3},
        'pull_off':   {'prob': 0.25, 'max_run': 3},
        'vibrato':    {'prob': 0.20, 'profile': 'standard'},
        'slide':      {'prob': 0.15, 'variants': ['into', 'glissando']},
        'staccato':   {'prob': 0.10, 'duration_factor': 0.35},
        'legato':     {'prob': 0.20, 'overlap_ticks': 30},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.10, 'velocity_cut': 0.7},
    },
    'shred': {
        'bend':       {'prob': 0.15, 'variants': ['grace', 'half']},
        'hammer_on':  {'prob': 0.45, 'max_run': 6},
        'pull_off':   {'prob': 0.40, 'max_run': 6},
        'vibrato':    {'prob': 0.10, 'profile': 'fast'},
        'slide':      {'prob': 0.08, 'variants': ['into']},
        'staccato':   {'prob': 0.15, 'duration_factor': 0.25},
        'legato':     {'prob': 0.50, 'overlap_ticks': 20},
        'tapping':    {'prob': 0.35, 'interval_range': (7, 15)},
        'palm_mute':  {'prob': 0.05, 'velocity_cut': 0.6},
    },
    'gallop': {
        'bend':       {'prob': 0.10, 'variants': ['grace', 'half']},
        'hammer_on':  {'prob': 0.30, 'max_run': 4},
        'pull_off':   {'prob': 0.25, 'max_run': 4},
        'vibrato':    {'prob': 0.15, 'profile': 'standard'},
        'slide':      {'prob': 0.10, 'variants': ['into']},
        'staccato':   {'prob': 0.20, 'duration_factor': 0.30},
        'legato':     {'prob': 0.30, 'overlap_ticks': 25},
        'tapping':    {'prob': 0.05, 'interval_range': (5, 12)},
        'palm_mute':  {'prob': 0.25, 'velocity_cut': 0.65},
    },
    'expressive': {
        'bend':       {'prob': 0.40, 'variants': ['whole', 'slow_blues', 'half']},
        'hammer_on':  {'prob': 0.20, 'max_run': 2},
        'pull_off':   {'prob': 0.20, 'max_run': 2},
        'vibrato':    {'prob': 0.50, 'profile': 'wide'},
        'slide':      {'prob': 0.20, 'variants': ['into', 'glissando']},
        'staccato':   {'prob': 0.05, 'duration_factor': 0.40},
        'legato':     {'prob': 0.35, 'overlap_ticks': 40},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'legato': {
        'bend':       {'prob': 0.20, 'variants': ['whole', 'slow_blues']},
        'hammer_on':  {'prob': 0.25, 'max_run': 3},
        'pull_off':   {'prob': 0.20, 'max_run': 3},
        'vibrato':    {'prob': 0.40, 'profile': 'wide'},
        'slide':      {'prob': 0.15, 'variants': ['glissando', 'into']},
        'staccato':   {'prob': 0.0},
        'legato':     {'prob': 0.55, 'overlap_ticks': 50},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'staccato': {
        'bend':       {'prob': 0.05, 'variants': ['grace']},
        'hammer_on':  {'prob': 0.15, 'max_run': 2},
        'pull_off':   {'prob': 0.15, 'max_run': 2},
        'vibrato':    {'prob': 0.05, 'profile': 'subtle'},
        'slide':      {'prob': 0.05, 'variants': ['into']},
        'staccato':   {'prob': 0.60, 'duration_factor': 0.25},
        'legato':     {'prob': 0.0},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.20, 'velocity_cut': 0.6},
    },
    'funky': {
        'bend':       {'prob': 0.10, 'variants': ['grace', 'half']},
        'hammer_on':  {'prob': 0.25, 'max_run': 2},
        'pull_off':   {'prob': 0.25, 'max_run': 2},
        'vibrato':    {'prob': 0.05, 'profile': 'subtle'},
        'slide':      {'prob': 0.15, 'variants': ['into']},
        'staccato':   {'prob': 0.45, 'duration_factor': 0.30},
        'legato':     {'prob': 0.05, 'overlap_ticks': 15},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.30, 'velocity_cut': 0.55},
    },
    'gentle': {
        'bend':       {'prob': 0.10, 'variants': ['half', 'grace']},
        'hammer_on':  {'prob': 0.10, 'max_run': 2},
        'pull_off':   {'prob': 0.10, 'max_run': 2},
        'vibrato':    {'prob': 0.30, 'profile': 'subtle'},
        'slide':      {'prob': 0.15, 'variants': ['into', 'glissando']},
        'staccato':   {'prob': 0.0},
        'legato':     {'prob': 0.40, 'overlap_ticks': 40},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'sustained': {
        'bend':       {'prob': 0.15, 'variants': ['whole', 'slow_blues']},
        'hammer_on':  {'prob': 0.10, 'max_run': 2},
        'pull_off':   {'prob': 0.10, 'max_run': 2},
        'vibrato':    {'prob': 0.45, 'profile': 'wide'},
        'slide':      {'prob': 0.10, 'variants': ['into']},
        'staccato':   {'prob': 0.0},
        'legato':     {'prob': 0.40, 'overlap_ticks': 45},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'atmospheric': {
        'bend':       {'prob': 0.15, 'variants': ['slow_blues', 'whole']},
        'hammer_on':  {'prob': 0.05, 'max_run': 2},
        'pull_off':   {'prob': 0.05, 'max_run': 2},
        'vibrato':    {'prob': 0.35, 'profile': 'subtle'},
        'slide':      {'prob': 0.20, 'variants': ['glissando', 'into']},
        'staccato':   {'prob': 0.0},
        'legato':     {'prob': 0.50, 'overlap_ticks': 60},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'spacey': {
        'bend':       {'prob': 0.15, 'variants': ['slow_blues', 'whole']},
        'hammer_on':  {'prob': 0.05, 'max_run': 2},
        'pull_off':   {'prob': 0.05, 'max_run': 2},
        'vibrato':    {'prob': 0.30, 'profile': 'subtle'},
        'slide':      {'prob': 0.25, 'variants': ['glissando']},
        'staccato':   {'prob': 0.0},
        'legato':     {'prob': 0.45, 'overlap_ticks': 55},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'fast': {
        'bend':       {'prob': 0.05, 'variants': ['grace']},
        'hammer_on':  {'prob': 0.35, 'max_run': 4},
        'pull_off':   {'prob': 0.30, 'max_run': 4},
        'vibrato':    {'prob': 0.05, 'profile': 'fast'},
        'slide':      {'prob': 0.05, 'variants': ['into']},
        'staccato':   {'prob': 0.20, 'duration_factor': 0.30},
        'legato':     {'prob': 0.40, 'overlap_ticks': 20},
        'tapping':    {'prob': 0.10, 'interval_range': (5, 12)},
        'palm_mute':  {'prob': 0.0},
    },
    'sparse': {
        'bend':       {'prob': 0.15, 'variants': ['whole', 'slow_blues']},
        'hammer_on':  {'prob': 0.05, 'max_run': 2},
        'pull_off':   {'prob': 0.05, 'max_run': 2},
        'vibrato':    {'prob': 0.40, 'profile': 'subtle'},
        'slide':      {'prob': 0.10, 'variants': ['into']},
        'staccato':   {'prob': 0.0},
        'legato':     {'prob': 0.30, 'overlap_ticks': 40},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'warm': {
        'bend':       {'prob': 0.10, 'variants': ['half', 'grace']},
        'hammer_on':  {'prob': 0.15, 'max_run': 2},
        'pull_off':   {'prob': 0.15, 'max_run': 2},
        'vibrato':    {'prob': 0.35, 'profile': 'subtle'},
        'slide':      {'prob': 0.15, 'variants': ['into', 'glissando']},
        'staccato':   {'prob': 0.0},
        'legato':     {'prob': 0.35, 'overlap_ticks': 35},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'classical': {
        'bend':       {'prob': 0.0},
        'hammer_on':  {'prob': 0.15, 'max_run': 3},
        'pull_off':   {'prob': 0.15, 'max_run': 3},
        'vibrato':    {'prob': 0.25, 'profile': 'subtle'},
        'slide':      {'prob': 0.10, 'variants': ['glissando']},
        'staccato':   {'prob': 0.15, 'duration_factor': 0.40},
        'legato':     {'prob': 0.35, 'overlap_ticks': 30},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'precise': {
        'bend':       {'prob': 0.0},
        'hammer_on':  {'prob': 0.0},
        'pull_off':   {'prob': 0.0},
        'vibrato':    {'prob': 0.0},
        'slide':      {'prob': 0.0},
        'staccato':   {'prob': 0.10, 'duration_factor': 0.35},
        'legato':     {'prob': 0.10, 'overlap_ticks': 15},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'ethereal': {
        'bend':       {'prob': 0.10, 'variants': ['slow_blues']},
        'hammer_on':  {'prob': 0.0},
        'pull_off':   {'prob': 0.0},
        'vibrato':    {'prob': 0.25, 'profile': 'subtle'},
        'slide':      {'prob': 0.20, 'variants': ['glissando']},
        'staccato':   {'prob': 0.0},
        'legato':     {'prob': 0.50, 'overlap_ticks': 60},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.0},
    },
    'varied': {
        'bend':       {'prob': 0.15, 'variants': ['half', 'whole', 'grace']},
        'hammer_on':  {'prob': 0.15, 'max_run': 3},
        'pull_off':   {'prob': 0.15, 'max_run': 3},
        'vibrato':    {'prob': 0.20, 'profile': 'standard'},
        'slide':      {'prob': 0.15, 'variants': ['into', 'glissando']},
        'staccato':   {'prob': 0.10, 'duration_factor': 0.35},
        'legato':     {'prob': 0.20, 'overlap_ticks': 30},
        'tapping':    {'prob': 0.0},
        'palm_mute':  {'prob': 0.05, 'velocity_cut': 0.7},
    },
}


def get_technique_profile(articulation: str) -> dict:
    """
    Get the technique probability profile for an articulation type.
    Falls back to 'varied' for unknown articulations.
    """
    return TECHNIQUE_PROFILES.get(articulation, TECHNIQUE_PROFILES['varied'])
