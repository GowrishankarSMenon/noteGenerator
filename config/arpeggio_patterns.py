"""
Technique-annotated arpeggio patterns per guitarist / style.

Each arpeggio is a list of (interval_from_root, duration_in_ticks, technique)
tuples.  The lead generator can inject these at phrase boundaries; because
the technique is baked into every note the effects processor can apply
them deterministically — no random dice rolls needed.

TICKS_PER_BEAT = 480
  480 = quarter note
  240 = eighth note
  120 = sixteenth note
  960 = half note
  1920 = whole note
  160 = triplet eighth
"""

# =========================================================================
# GILMOUR — Spacious bends, wide vibrato, tasteful slides
# =========================================================================
GILMOUR_ARPEGGIOS = {
    'gilmour_soaring_phrase': [
        (0, 960, 'bend_whole'),
        (3, 480, 'normal'),
        (5, 480, 'slide_up'),
        (7, 1920, 'vibrato'),
    ],
    'gilmour_shine_phrase': [
        (7, 960, 'bend_half'),
        (5, 960, 'vibrato'),
        (3, 960, 'normal'),
        (0, 1920, 'vibrato'),
    ],
    'gilmour_breathe_arp': [
        (0, 480, 'normal'),
        (7, 480, 'normal'),
        (12, 480, 'slide_up'),
        (16, 480, 'vibrato'),
        (12, 480, 'normal'),
        (7, 480, 'normal'),
    ],
    'gilmour_time_climb': [
        (0, 480, 'normal'),
        (2, 480, 'normal'),
        (5, 960, 'bend_half'),
        (7, 480, 'normal'),
        (9, 480, 'slide_up'),
        (12, 1920, 'vibrato'),
    ],
}

# =========================================================================
# BB KING — Short phrases, vocal bends, sustain vibrato
# =========================================================================
BB_KING_ARPEGGIOS = {
    'bb_king_box_lick': [
        (0, 480, 'normal'),
        (3, 240, 'bend_half'),
        (5, 240, 'normal'),
        (3, 480, 'normal'),
        (0, 480, 'vibrato'),
        (-2, 480, 'normal'),
        (0, 1920, 'vibrato'),
    ],
    'bb_king_sustain': [
        (3, 960, 'bend_half'),
        (0, 480, 'normal'),
        (-2, 480, 'normal'),
        (0, 1920, 'vibrato'),
    ],
    'bb_king_call': [
        (0, 480, 'normal'),
        (3, 960, 'bend_half'),
        (0, 480, 'normal'),
        (-2, 480, 'normal'),
        (0, 960, 'vibrato'),
    ],
}

# =========================================================================
# VAN HALEN — Tapping arpeggios, eruption-style patterns
# =========================================================================
VANHALEN_ARPEGGIOS = {
    'vanhalen_tap_arp': [
        (0, 120, 'tap'),
        (5, 120, 'tap'),
        (12, 120, 'tap'),
        (0, 120, 'tap'),
        (4, 120, 'tap'),
        (12, 120, 'tap'),
        (0, 120, 'tap'),
        (3, 120, 'tap'),
        (12, 120, 'tap'),
        (0, 120, 'tap'),
        (5, 120, 'tap'),
        (12, 120, 'tap'),
    ],
    'vanhalen_tap_descend': [
        (12, 120, 'tap'),
        (7, 120, 'tap'),
        (0, 120, 'tap'),
        (12, 120, 'tap'),
        (5, 120, 'tap'),
        (0, 120, 'tap'),
        (12, 120, 'tap'),
        (4, 120, 'tap'),
        (0, 120, 'tap'),
    ],
    'vanhalen_melodic': [
        (0, 480, 'normal'),
        (0, 240, 'normal'),
        (2, 240, 'normal'),
        (5, 480, 'normal'),
        (5, 240, 'normal'),
        (4, 240, 'normal'),
        (2, 960, 'vibrato'),
    ],
}

# =========================================================================
# SLASH — Melodic rock runs, tasteful bends, pentatonic
# =========================================================================
SLASH_ARPEGGIOS = {
    'slash_pentatonic_ascend': [
        (0, 120, 'normal'),
        (3, 120, 'hammer_on'),
        (5, 120, 'hammer_on'),
        (7, 120, 'normal'),
        (10, 120, 'hammer_on'),
        (12, 240, 'bend_half'),
        (10, 120, 'normal'),
        (7, 120, 'pull_off'),
        (5, 120, 'pull_off'),
        (3, 120, 'normal'),
        (0, 480, 'vibrato'),
    ],
    'slash_november_phrase': [
        (0, 480, 'normal'),
        (3, 240, 'slide_up'),
        (5, 240, 'normal'),
        (7, 480, 'bend_half'),
        (8, 480, 'vibrato'),
        (7, 240, 'normal'),
        (5, 240, 'normal'),
        (3, 480, 'normal'),
        (0, 960, 'vibrato'),
    ],
    'slash_sweet_child_arp': [
        (0, 120, 'normal'),
        (12, 120, 'normal'),
        (7, 120, 'normal'),
        (8, 120, 'normal'),
        (5, 120, 'normal'),
        (12, 120, 'normal'),
        (7, 120, 'normal'),
        (8, 120, 'normal'),
    ],
}

# =========================================================================
# HENDRIX — Psychedelic bends, chord fragments, double-stops
# =========================================================================
HENDRIX_ARPEGGIOS = {
    'hendrix_tritone_phrase': [
        (0, 240, 'normal'),
        (6, 240, 'bend_half'),
        (7, 480, 'vibrato'),
        (0, 240, 'normal'),
        (6, 240, 'bend_half'),
        (7, 240, 'normal'),
        (8, 240, 'hammer_on'),
        (7, 480, 'vibrato'),
    ],
    'hendrix_little_wing_arp': [
        (0, 480, 'normal'),
        (4, 240, 'normal'),
        (5, 240, 'hammer_on'),
        (7, 480, 'bend_half'),
        (8, 240, 'normal'),
        (7, 240, 'normal'),
        (5, 480, 'normal'),
        (4, 240, 'normal'),
        (0, 240, 'normal'),
        (-2, 480, 'normal'),
        (0, 960, 'vibrato'),
    ],
}

# =========================================================================
# ANGUS YOUNG — Pull-off patterns, palm mute, raw energy
# =========================================================================
ANGUS_ARPEGGIOS = {
    'angus_thunderstruck_arp': [
        (0, 120, 'normal'),
        (12, 120, 'pull_off'),
        (0, 120, 'normal'),
        (12, 120, 'pull_off'),
        (0, 120, 'normal'),
        (11, 120, 'pull_off'),
        (0, 120, 'normal'),
        (11, 120, 'pull_off'),
        (0, 120, 'normal'),
        (10, 120, 'pull_off'),
        (0, 120, 'normal'),
        (10, 120, 'pull_off'),
    ],
    'angus_palm_mute_riff': [
        (0, 240, 'palm_mute'),
        (5, 120, 'normal'),
        (3, 120, 'normal'),
        (0, 240, 'palm_mute'),
        (7, 120, 'normal'),
        (5, 120, 'normal'),
        (0, 240, 'palm_mute'),
        (5, 120, 'normal'),
        (3, 120, 'normal'),
        (0, 480, 'normal'),
    ],
}

# =========================================================================
# IRON MAIDEN — Galloping legato, harmonic minor runs
# =========================================================================
MAIDEN_ARPEGGIOS = {
    'maiden_gallop_phrase': [
        (0, 160, 'normal'),
        (0, 160, 'legato'),
        (2, 160, 'legato'),
        (3, 160, 'normal'),
        (3, 160, 'legato'),
        (5, 160, 'legato'),
        (7, 160, 'normal'),
        (7, 160, 'legato'),
        (5, 160, 'legato'),
        (3, 160, 'normal'),
        (2, 160, 'legato'),
        (0, 160, 'normal'),
    ],
    'maiden_harmony_run': [
        (0, 120, 'normal'),
        (2, 120, 'hammer_on'),
        (3, 120, 'hammer_on'),
        (5, 120, 'hammer_on'),
        (7, 120, 'normal'),
        (9, 120, 'hammer_on'),
        (10, 120, 'hammer_on'),
        (12, 120, 'normal'),
        (10, 120, 'pull_off'),
        (9, 120, 'pull_off'),
        (7, 120, 'normal'),
        (5, 120, 'pull_off'),
        (3, 120, 'pull_off'),
        (2, 120, 'normal'),
        (0, 240, 'normal'),
    ],
}

# =========================================================================
# DIMEBAG — Aggressive bends, palm muted chugs, shred runs
# =========================================================================
DIMEBAG_ARPEGGIOS = {
    'dimebag_chug_riff': [
        (0, 120, 'palm_mute'),
        (0, 120, 'palm_mute'),
        (0, 120, 'palm_mute'),
        (-2, 240, 'normal'),
        (-3, 240, 'normal'),
        (0, 120, 'palm_mute'),
        (0, 120, 'palm_mute'),
        (0, 120, 'palm_mute'),
        (-5, 480, 'bend_whole'),
    ],
    'dimebag_shred_phrase': [
        (0, 120, 'normal'),
        (1, 120, 'hammer_on'),
        (3, 120, 'hammer_on'),
        (5, 120, 'hammer_on'),
        (6, 120, 'normal'),
        (8, 120, 'hammer_on'),
        (10, 120, 'hammer_on'),
        (12, 120, 'bend_half'),
        (10, 120, 'normal'),
        (8, 120, 'pull_off'),
        (6, 120, 'pull_off'),
        (5, 120, 'pull_off'),
        (3, 120, 'normal'),
        (1, 120, 'normal'),
        (0, 480, 'vibrato'),
    ],
}

# =========================================================================
# SRV — Texas blues bends, shuffle licks, intense vibrato
# =========================================================================
SRV_ARPEGGIOS = {
    'srv_shuffle_lick': [
        (0, 160, 'normal'),
        (3, 160, 'hammer_on'),
        (5, 160, 'normal'),
        (7, 160, 'bend_half'),
        (5, 160, 'normal'),
        (3, 160, 'pull_off'),
        (0, 160, 'normal'),
        (3, 160, 'normal'),
        (5, 160, 'normal'),
        (7, 480, 'vibrato'),
    ],
    'srv_texas_phrase': [
        (0, 960, 'normal'),
        (3, 480, 'slide_up'),
        (5, 480, 'normal'),
        (7, 960, 'bend_whole'),
        (5, 480, 'normal'),
        (3, 480, 'normal'),
        (0, 1920, 'vibrato'),
    ],
}

# =========================================================================
# CLAPTON — Woman tone, smooth bends, cream-era blues
# =========================================================================
CLAPTON_ARPEGGIOS = {
    'clapton_cream_lick': [
        (0, 240, 'normal'),
        (3, 120, 'hammer_on'),
        (5, 120, 'normal'),
        (7, 240, 'bend_half'),
        (5, 120, 'normal'),
        (3, 120, 'pull_off'),
        (0, 240, 'normal'),
        (3, 120, 'normal'),
        (0, 120, 'normal'),
        (-2, 480, 'vibrato'),
    ],
    'clapton_slow_phrase': [
        (0, 480, 'normal'),
        (3, 240, 'slide_up'),
        (5, 240, 'normal'),
        (7, 480, 'bend_half'),
        (5, 240, 'normal'),
        (3, 240, 'normal'),
        (0, 480, 'normal'),
        (-2, 960, 'vibrato'),
        (0, 1920, 'vibrato'),
    ],
}

# =========================================================================
# KNOPFLER — Fingerpicking, clean legato
# =========================================================================
KNOPFLER_ARPEGGIOS = {
    'knopfler_picking_phrase': [
        (0, 240, 'normal'),
        (4, 240, 'normal'),
        (7, 120, 'normal'),
        (4, 120, 'normal'),
        (0, 240, 'normal'),
        (3, 240, 'normal'),
        (7, 120, 'normal'),
        (3, 120, 'normal'),
    ],
    'knopfler_melodic': [
        (0, 480, 'normal'),
        (2, 240, 'legato'),
        (4, 240, 'normal'),
        (7, 480, 'slide_up'),
        (9, 480, 'vibrato'),
        (7, 240, 'normal'),
        (4, 240, 'normal'),
        (2, 480, 'normal'),
        (0, 960, 'normal'),
    ],
}


# =========================================================================
# STYLE → ARPEGGIO MAPPING
# =========================================================================
STYLE_ARPEGGIO_MAP = {
    # Rock styles
    'page_blues_rock':      list(GILMOUR_ARPEGGIOS.keys())[:1] + ['clapton_cream_lick'],
    'may_harmonic':         ['vanhalen_melodic', 'slash_sweet_child_arp'],
    'slash_hard_rock':      list(SLASH_ARPEGGIOS.keys()),
    'vanhalen_eruption':    list(VANHALEN_ARPEGGIOS.keys()),
    'hendrix_psychedelic':  list(HENDRIX_ARPEGGIOS.keys()),
    'dimebag_shred':        list(DIMEBAG_ARPEGGIOS.keys()),
    'angus_acdc':           list(ANGUS_ARPEGGIOS.keys()),
    'maiden_gallop':        list(MAIDEN_ARPEGGIOS.keys()),
    'cobain_grunge':        ['angus_palm_mute_riff'],
    'morello_riff':         ['dimebag_chug_riff'],
    'prog_rock':            ['maiden_harmony_run', 'slash_november_phrase'],

    # Sad styles
    'gilmour_soaring':      list(GILMOUR_ARPEGGIOS.keys()),
    'radiohead_angular':    ['knopfler_picking_phrase'],
    'clapton_weeping':      list(CLAPTON_ARPEGGIOS.keys()),
    'hendrix_little_wing':  ['hendrix_little_wing_arp'],

    # Jazz/blues styles
    'bb_king_blues':        list(BB_KING_ARPEGGIOS.keys()),
    'clapton_cream':        list(CLAPTON_ARPEGGIOS.keys()),
    'srv_texas_blues':      list(SRV_ARPEGGIOS.keys()),

    # Happy styles
    'may_anthem':           ['slash_sweet_child_arp', 'vanhalen_melodic'],
    'vanhalen_bright':      list(VANHALEN_ARPEGGIOS.keys()),

    # Calm styles
    'gilmour_ambient':      ['gilmour_soaring_phrase', 'gilmour_breathe_arp'],
    'knopfler_fingerstyle': list(KNOPFLER_ARPEGGIOS.keys()),

    # Electronic
    'floyd_echoes':         ['gilmour_shine_phrase', 'gilmour_time_climb'],
}

# All arpeggio pools collected into one lookup
ALL_ARPEGGIOS = {}
for _pool in [
    GILMOUR_ARPEGGIOS, BB_KING_ARPEGGIOS, VANHALEN_ARPEGGIOS,
    SLASH_ARPEGGIOS, HENDRIX_ARPEGGIOS, ANGUS_ARPEGGIOS,
    MAIDEN_ARPEGGIOS, DIMEBAG_ARPEGGIOS, SRV_ARPEGGIOS,
    CLAPTON_ARPEGGIOS, KNOPFLER_ARPEGGIOS,
]:
    ALL_ARPEGGIOS.update(_pool)


def get_arpeggio_for_style(style_name: str) -> list:
    """
    Get a random technique-annotated arpeggio for the given lead style.
    Returns list of (interval, duration, technique) or empty list.
    """
    import random as _rand
    arp_names = STYLE_ARPEGGIO_MAP.get(style_name, [])
    if not arp_names:
        return []
    arp_name = _rand.choice(arp_names)
    return ALL_ARPEGGIOS.get(arp_name, [])


def transpose_arpeggio(arpeggio: list, root_midi: int, octave: int = 5) -> list:
    """
    Transpose a technique-annotated arpeggio pattern to a specific root and octave.

    Args:
        arpeggio: list of (interval, duration, technique) tuples
        root_midi: MIDI note number of the root
        octave: Target octave

    Returns:
        list of (absolute_midi_note, duration, technique) tuples
    """
    base = octave * 12
    return [(base + root_midi % 12 + interval, dur, tech)
            for interval, dur, tech in arpeggio]
