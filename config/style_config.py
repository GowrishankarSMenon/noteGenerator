"""
Style configuration and selection modes.
Provides centralized access to all available styles for drums and lead.
Supports 3 modes: Auto (mood-based), Random (any style), Selection (user picks)
"""

import random
from typing import Optional, Dict, List, Tuple
from config.lead_styles import LEAD_STYLES
from config.drum_patterns import ROCK_DRUM_PATTERNS, ROCK_DRUM_FILLS

# =============================================================================
# STYLE SELECTION MODES
# =============================================================================
STYLE_MODES = {
    'auto': 'Auto (Mood-Based)',      # Current behavior - picks based on mood
    'random': 'Random (Any Style)',    # Picks from all styles regardless of mood
    'selection': 'Manual Selection',   # User selects specific styles
}

# =============================================================================
# DRUM STYLE DEFINITIONS
# =============================================================================
# Standard drum patterns (non-rock)
STANDARD_DRUM_STYLES = ['pop', 'ballad', 'jazz', 'electronic', 'soft']

# Rock-specific patterns with names
ROCK_STYLE_NAMES = [p['name'] for p in ROCK_DRUM_PATTERNS]

# All available drum styles grouped
DRUM_STYLES = {
    'standard': STANDARD_DRUM_STYLES,
    'rock': ROCK_STYLE_NAMES,
}

# All drum styles flattened for dropdown
ALL_DRUM_STYLES = STANDARD_DRUM_STYLES + ROCK_STYLE_NAMES


# =============================================================================
# LEAD STYLE DEFINITIONS
# =============================================================================
def get_all_lead_styles() -> Dict[str, List[str]]:
    """Get all lead styles organized by mood."""
    styles = {}
    for mood, config in LEAD_STYLES.items():
        styles[mood] = [s['name'] for s in config['sub_styles']]
    return styles


def get_all_lead_style_names() -> List[str]:
    """Get flat list of all lead style names."""
    names = []
    for mood, config in LEAD_STYLES.items():
        for sub in config['sub_styles']:
            names.append(sub['name'])
    return names


def get_lead_style_by_name(name: str) -> Optional[dict]:
    """Find a lead style by its name across all moods."""
    for mood, config in LEAD_STYLES.items():
        for sub in config['sub_styles']:
            if sub['name'] == name:
                return sub
    return None


def get_lead_style_mood(name: str) -> Optional[str]:
    """Find which mood a lead style belongs to."""
    for mood, config in LEAD_STYLES.items():
        for sub in config['sub_styles']:
            if sub['name'] == name:
                return mood
    return None


# =============================================================================
# ROCK DRUM PATTERN ACCESS
# =============================================================================
def get_rock_pattern_by_name(name: str) -> Optional[dict]:
    """Get a rock drum pattern by its name."""
    for pattern in ROCK_DRUM_PATTERNS:
        if pattern.get('name') == name:
            return {k: v for k, v in pattern.items() if k != 'name'}
    return None


def get_rock_fill_by_name(name: str) -> Optional[dict]:
    """Get a rock drum fill by its name."""
    for fill in ROCK_DRUM_FILLS:
        if fill.get('name') == name:
            return {k: v for k, v in fill.items() if k != 'name'}
    return None


# =============================================================================
# STYLE SELECTION FUNCTIONS
# =============================================================================
def select_drum_style(
    mode: str,
    mood: str,
    selected_style: Optional[str] = None
) -> Tuple[str, Optional[dict]]:
    """
    Select a drum style based on mode and optionally return pattern data.
    
    Args:
        mode: 'auto', 'random', or 'selection'
        mood: Current mood (for auto mode)
        selected_style: User-selected style name (for selection mode)
        
    Returns:
        Tuple of (style_name, pattern_data or None)
    """
    if mode == 'selection' and selected_style:
        # User picked a specific style
        if selected_style in STANDARD_DRUM_STYLES:
            return selected_style, None  # Will use standard pattern
        elif selected_style in ROCK_STYLE_NAMES:
            pattern = get_rock_pattern_by_name(selected_style)
            return selected_style, pattern
    
    elif mode == 'random':
        # Pick any style randomly
        all_styles = ALL_DRUM_STYLES
        choice = random.choice(all_styles)
        if choice in STANDARD_DRUM_STYLES:
            return choice, None
        else:
            pattern = get_rock_pattern_by_name(choice)
            return choice, pattern
    
    # Auto mode - use mood-based selection (default behavior)
    # Map mood to appropriate drum style
    mood_to_drum_style = {
        'happy': 'pop',
        'sad': 'ballad',
        'rock': 'rock',  # Will randomly pick from rock patterns
        'jazz': 'jazz',
        'electronic': 'electronic',
        'calm': 'soft',
    }
    style = mood_to_drum_style.get(mood, 'pop')
    
    if style == 'rock':
        # Random rock pattern
        pattern_data = random.choice(ROCK_DRUM_PATTERNS)
        name = pattern_data.get('name', 'rock')
        return name, {k: v for k, v in pattern_data.items() if k != 'name'}
    
    return style, None


def select_lead_style(
    mode: str,
    mood: str,
    selected_style: Optional[str] = None
) -> dict:
    """
    Select a lead style based on mode.
    
    Args:
        mode: 'auto', 'random', or 'selection'
        mood: Current mood (for auto mode)
        selected_style: User-selected style name (for selection mode)
        
    Returns:
        Lead style configuration dict
    """
    if mode == 'selection' and selected_style:
        # User picked a specific style
        style = get_lead_style_by_name(selected_style)
        if style:
            return style
    
    elif mode == 'random':
        # Pick any lead style randomly across all moods
        all_moods = list(LEAD_STYLES.keys())
        random_mood = random.choice(all_moods)
        return random.choice(LEAD_STYLES[random_mood]['sub_styles'])
    
    # Auto mode - use mood-based selection
    if mood in LEAD_STYLES:
        return random.choice(LEAD_STYLES[mood]['sub_styles'])
    
    # Fallback
    return LEAD_STYLES['happy']['sub_styles'][0]


# =============================================================================
# STYLE DISPLAY HELPERS
# =============================================================================
def get_style_display_info() -> Dict:
    """Get organized style info for UI display."""
    return {
        'drum_styles': {
            'Standard Patterns': STANDARD_DRUM_STYLES,
            'Rock Patterns': ROCK_STYLE_NAMES,
        },
        'lead_styles': get_all_lead_styles(),
        'modes': STYLE_MODES,
    }


def format_style_name(name: str) -> str:
    """Format a style name for display (e.g., 'gilmour_soaring' -> 'Gilmour Soaring')."""
    return name.replace('_', ' ').title()


# =============================================================================
# PRESETS - Curated style combinations
# =============================================================================
STYLE_PRESETS = {
    'Classic Rock': {
        'drums': 'bonham_heavy',
        'lead': 'page_blues_rock',
        'description': 'Led Zeppelin inspired classic rock',
    },
    'Blues Master': {
        'drums': 'texas_shuffle',
        'lead': 'bb_king_blues',
        'description': 'Texas blues with expressive bends',
    },
    'Pink Floyd': {
        'drums': 'mason_floyd',
        'lead': 'gilmour_soaring',
        'description': 'Atmospheric prog rock soundscapes',
    },
    'Metal Thunder': {
        'drums': 'thrash_power',
        'lead': 'dimebag_shred',
        'description': 'Pantera-style heavy groove metal',
    },
    'Punk Energy': {
        'drums': 'punk_blast',
        'lead': 'cobain_grunge',
        'description': 'Fast and aggressive punk/grunge',
    },
    'Arena Rock': {
        'drums': 'stadium_rock',
        'lead': 'may_harmonic',
        'description': 'Queen-style epic stadium rock',
    },
    '90s Grunge': {
        'drums': 'grunge_smash',
        'lead': 'cobain_grunge',
        'description': 'Seattle grunge - Nirvana sound',
    },
    'Jazz Club': {
        'drums': 'jazz',
        'lead': 'cool_jazz',
        'description': 'Smoky jazz club atmosphere',
    },
    'Synthwave': {
        'drums': 'electronic',
        'lead': 'kraftwerk_robotic',
        'description': 'Retro electronic vibes',
    },
    'Chill Acoustic': {
        'drums': 'soft',
        'lead': 'knopfler_fingerstyle',
        'description': 'Relaxed fingerpicked acoustic',
    },
    'Van Halen': {
        'drums': 'vanhalen_jump',
        'lead': 'vanhalen_eruption',
        'description': 'Eddie Van Halen tapping virtuosity',
    },
    'Hendrix Experience': {
        'drums': 'mitchell_hendrix',
        'lead': 'hendrix_psychedelic',
        'description': 'Psychedelic wah-wah fuzz guitar',
    },
    'GNR Paradise': {
        'drums': 'gnr_shuffle',
        'lead': 'slash_hard_rock',
        'description': 'Guns N\' Roses hard rock swagger',
    },
    'Iron Maiden': {
        'drums': 'maiden_trooper',
        'lead': 'maiden_gallop',
        'description': 'Galloping heavy metal twin leads',
    },
    'AC/DC Highway': {
        'drums': 'acdc_drive',
        'lead': 'angus_acdc',
        'description': 'AC/DC straight-ahead rock power',
    },
    'Clapton Blues': {
        'drums': 'baker_cream',
        'lead': 'clapton_cream',
        'description': 'Cream-era blues-rock with woman tone',
    },
    'SRV Texas': {
        'drums': 'texas_shuffle',
        'lead': 'srv_texas_blues',
        'description': 'Stevie Ray Vaughan Texas blues fire',
    },
    'Pantera Groove': {
        'drums': 'pantera_walk',
        'lead': 'dimebag_shred',
        'description': 'Pantera heavy groove with shred solos',
    },
    'Floyd Echoes': {
        'drums': 'mason_floyd',
        'lead': 'gilmour_ambient',
        'description': 'Pink Floyd ambient delay textures',
    },
    'Rush Prog': {
        'drums': 'peart_prog',
        'lead': 'prog_rock',
        'description': 'Rush-style progressive complexity',
    },
}


def get_preset_names() -> List[str]:
    """Get list of available preset names."""
    return list(STYLE_PRESETS.keys())


def apply_preset(preset_name: str) -> Optional[Dict]:
    """Get style configuration for a preset."""
    return STYLE_PRESETS.get(preset_name)
