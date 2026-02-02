"""
Global configuration and constants.
Central repository for hard-coded constants to avoid magic numbers.
"""

import os

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
DATASETS_DIR = os.path.join(ASSETS_DIR, 'datasets')
DATASET_PATH = os.path.join(ASSETS_DIR, 'dataset.csv')  # Legacy fallback
SOUNDFONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'FluidR3_GM.sf2')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

def get_dataset_path(mood: str) -> str:
    """Get the dataset path for a specific mood."""
    mood_dataset = os.path.join(DATASETS_DIR, f'{mood}.csv')
    if os.path.exists(mood_dataset):
        return mood_dataset
    return DATASET_PATH  # Fallback to generic dataset

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# AUDIO SETTINGS
# =============================================================================
SAMPLE_RATE = 44100
TICKS_PER_BEAT = 480  # MIDI resolution
DEFAULT_VELOCITY = 80
DRUM_VELOCITY = 100

# =============================================================================
# MIDI CHANNELS & PROGRAMS
# =============================================================================
DRUM_CHANNEL = 9  # Channel 10 in MIDI (0-indexed)

# General MIDI Program Numbers (0-indexed)
INSTRUMENTS = {
    'piano': 0,
    'electric_piano': 4,
    'acoustic_guitar': 25,
    'electric_guitar': 27,
    'distortion_guitar': 30,
    'acoustic_bass': 32,
    'electric_bass': 33,
    'slap_bass': 36,
    'synth_bass': 38,
    'strings': 48,
    'synth_pad': 88,
    'synth_lead': 80,
    'flute': 73,
    'saxophone': 65,
}

# Drum Note Numbers (General MIDI)
DRUM_NOTES = {
    'kick': 36,
    'snare': 38,
    'closed_hihat': 42,
    'open_hihat': 46,
    'ride': 51,
    'crash': 49,
    'tom_low': 45,
    'tom_mid': 47,
    'tom_high': 50,
    'clap': 39,
}

# =============================================================================
# SCALE DEFINITIONS (intervals from root)
# =============================================================================
SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor': [0, 2, 3, 5, 7, 9, 11],
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10],
    'blues': [0, 3, 5, 6, 7, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
}

# =============================================================================
# CHORD DEFINITIONS (intervals from root)
# =============================================================================
CHORD_TYPES = {
    'maj': [0, 4, 7],
    'min': [0, 3, 7],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dom7': [0, 4, 7, 10],
    'dim7': [0, 3, 6, 9],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
}

# =============================================================================
# MOOD CONFIGURATIONS
# =============================================================================
MOOD_CONFIGS = {
    'happy': {
        'bpm_range': (110, 140),
        'scale_type': 'major',
        'key_options': ['C', 'G', 'D', 'F'],
        'chord_progressions': [
            ['I', 'V', 'vi', 'IV'],
            ['I', 'IV', 'V', 'I'],
            ['I', 'ii', 'V', 'I'],
        ],
        'instruments': {
            'bass': 'electric_bass',
            'harmony': 'piano',
            'lead': 'synth_lead',
        },
        'drum_style': 'pop',
        'harmony_style': 'rhythmic',
    },
    'sad': {
        'bpm_range': (60, 85),
        'scale_type': 'minor',
        'key_options': ['Am', 'Em', 'Dm', 'Bm'],
        'chord_progressions': [
            ['i', 'VI', 'III', 'VII'],
            ['i', 'iv', 'v', 'i'],
            ['i', 'VI', 'iv', 'V'],
        ],
        'instruments': {
            'bass': 'acoustic_bass',
            'harmony': 'strings',
            'lead': 'piano',
        },
        'drum_style': 'ballad',
        'harmony_style': 'sustained',
    },
    'rock': {
        'bpm_range': (100, 130),
        'scale_type': 'pentatonic_minor',
        'key_options': ['E', 'A', 'G', 'D'],
        'chord_progressions': [
            ['I', 'IV', 'V', 'I'],
            ['I', 'bVII', 'IV', 'I'],
            ['i', 'bVII', 'bVI', 'V'],
        ],
        'instruments': {
            'bass': 'electric_bass',
            'harmony': 'distortion_guitar',
            'lead': 'distortion_guitar',
        },
        'drum_style': 'rock',
        'harmony_style': 'power',
    },
    'jazz': {
        'bpm_range': (90, 140),
        'scale_type': 'dorian',
        'key_options': ['Dm', 'Gm', 'Cm', 'Am'],
        'chord_progressions': [
            ['ii', 'V', 'I', 'vi'],
            ['I', 'vi', 'ii', 'V'],
            ['iii', 'VI', 'ii', 'V'],
        ],
        'instruments': {
            'bass': 'acoustic_bass',
            'harmony': 'electric_piano',
            'lead': 'saxophone',
        },
        'drum_style': 'jazz',
        'harmony_style': 'voicing',
    },
    'electronic': {
        'bpm_range': (120, 140),
        'scale_type': 'minor',
        'key_options': ['Am', 'Em', 'Dm', 'Cm'],
        'chord_progressions': [
            ['i', 'VI', 'III', 'VII'],
            ['i', 'iv', 'VI', 'V'],
            ['i', 'i', 'VI', 'VII'],
        ],
        'instruments': {
            'bass': 'synth_bass',
            'harmony': 'synth_pad',
            'lead': 'synth_lead',
        },
        'drum_style': 'electronic',
        'harmony_style': 'sustained',
    },
    'calm': {
        'bpm_range': (60, 80),
        'scale_type': 'major',
        'key_options': ['C', 'G', 'F', 'D'],
        'chord_progressions': [
            ['I', 'V', 'vi', 'IV'],
            ['I', 'iii', 'IV', 'V'],
            ['I', 'IV', 'I', 'V'],
        ],
        'instruments': {
            'bass': 'acoustic_bass',
            'harmony': 'acoustic_guitar',
            'lead': 'flute',
        },
        'drum_style': 'soft',
        'harmony_style': 'arpeggiated',
    },
}

# =============================================================================
# DRUM PATTERNS (16th note grid, 1 = hit, 0 = rest)
# =============================================================================
DRUM_PATTERNS = {
    'pop': {
        'kick':         [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        'snare':        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'closed_hihat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    'rock': {
        'kick':         [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        'snare':        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'closed_hihat': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        'crash':        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
    'ballad': {
        'kick':         [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'snare':        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        'closed_hihat': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    },
    'jazz': {
        'kick':         [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        'snare':        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'ride':         [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
    },
    'electronic': {
        'kick':         [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare':        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'closed_hihat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        'open_hihat':   [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    },
    'soft': {
        'kick':         [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'closed_hihat': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    },
}

# Drum fill pattern
DRUM_FILL = {
    'snare':   [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1],
    'tom_low': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    'tom_mid': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    'tom_high':[0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    'crash':   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
}
