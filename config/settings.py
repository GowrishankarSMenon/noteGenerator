"""
Global configuration and constants.
"""

import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
DATASET_PATH = os.path.join(ASSETS_DIR, 'dataset.csv')
SOUNDFONT_PATH = os.path.join(ASSETS_DIR, 'fonts', 'FluidR3_GM.sf2')

# BPM ranges
MIN_BPM = 60
MAX_BPM = 180
DEFAULT_BPM = 120

# Scales
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]
PENTATONIC_SCALE = [0, 2, 4, 7, 9]

# MIDI settings
DEFAULT_VELOCITY = 80
DEFAULT_DURATION = 480  # Ticks
