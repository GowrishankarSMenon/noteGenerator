"""
Riff and arpeggio pattern library.
Contains MIDI note sequences inspired by iconic bands and guitarists.

Each riff is a list of (interval_from_root, duration_in_ticks) tuples.
Intervals are in semitones from the root note. This makes them
transposable to any key.

The lead generator can inject these riffs instead of pure Markov output,
making the style instantly recognizable.

TICKS_PER_BEAT = 480
  480 = quarter note
  240 = eighth note
  120 = sixteenth note
  960 = half note
  1920 = whole note
  160 = triplet eighth
"""

# =============================================================================
# ROCK RIFFS - Power riffs and iconic patterns
# =============================================================================
ROCK_RIFFS = {
    # ---- LED ZEPPELIN / JIMMY PAGE ----
    'page_whole_lotta': [
        # "Whole Lotta Love" opening riff feel
        (0, 240), (3, 120), (5, 120), (7, 240),
        (5, 240), (3, 120), (0, 120), (-2, 480),
    ],
    'page_kashmir': [
        # "Kashmir" descending chromatic riff
        (0, 360), (-1, 120), (-2, 360), (-3, 120),
        (-4, 360), (-5, 120), (-7, 480),
    ],
    'page_blackdog': [
        # "Black Dog" bluesy syncopated riff
        (0, 120), (3, 120), (5, 120), (7, 120),
        (5, 120), (3, 120), (0, 240), (5, 120),
        (3, 120), (0, 480),
    ],

    # ---- QUEEN / BRIAN MAY ----
    'may_bohemian_arp': [
        # Bohemian Rhapsody-style ascending arpeggio
        (0, 240), (4, 240), (7, 240), (12, 240),
        (16, 240), (19, 240), (24, 480),
    ],
    'may_brighton_rock': [
        # Brighton Rock tapping pattern - fast harmonics
        (0, 120), (7, 120), (12, 120), (7, 120),
        (0, 120), (4, 120), (7, 120), (4, 120),
        (0, 120), (3, 120), (7, 120), (3, 120),
        (0, 120), (7, 120), (12, 480),
    ],
    'may_we_will_rock': [
        # "We Will Rock You" guitar solo melody shape
        (0, 480), (2, 240), (3, 240),
        (5, 480), (3, 240), (2, 240),
        (0, 960),
    ],

    # ---- GUNS N' ROSES / SLASH ----
    'slash_sweet_child': [
        # "Sweet Child O' Mine" arpeggio riff
        (0, 120), (12, 120), (7, 120), (8, 120),
        (5, 120), (12, 120), (7, 120), (8, 120),
    ],
    'slash_paradise': [
        # "Paradise City" fast run
        (0, 120), (2, 120), (3, 120), (5, 120),
        (7, 120), (8, 120), (10, 120), (12, 120),
        (10, 120), (8, 120), (7, 120), (5, 120),
        (3, 240), (0, 240),
    ],
    'slash_november': [
        # "November Rain" melodic solo shape
        (0, 480), (3, 240), (5, 240),
        (7, 480), (8, 480),
        (7, 240), (5, 240), (3, 480),
        (0, 960),
    ],

    # ---- PINK FLOYD / DAVID GILMOUR ----
    'gilmour_comfortably': [
        # "Comfortably Numb" solo opening shape - huge bends
        (0, 960), (3, 480), (5, 480),
        (7, 1920),
        (5, 480), (3, 480), (0, 960),
    ],
    'gilmour_time': [
        # "Time" solo - ascending with space
        (0, 480), (2, 480),
        (5, 960),
        (7, 480), (9, 480),
        (12, 1920),
    ],
    'gilmour_shine_on': [
        # "Shine On You Crazy Diamond" 4-note motif
        (7, 960), (5, 960),
        (3, 960), (0, 1920),
    ],

    # ---- PANTERA / DIMEBAG DARRELL ----
    'dimebag_walk': [
        # "Walk" grinding riff
        (0, 240), (0, 120), (0, 120),
        (-2, 240), (-3, 240),
        (0, 240), (0, 120), (0, 120),
        (-5, 480),
    ],
    'dimebag_cowboys': [
        # "Cowboys from Hell" shred run
        (0, 120), (1, 120), (3, 120), (5, 120),
        (6, 120), (8, 120), (10, 120), (12, 120),
        (11, 120), (10, 120), (8, 120), (6, 120),
        (5, 120), (3, 120), (1, 120), (0, 120),
    ],
    'dimebag_floods': [
        # "Floods" melodic outro solo shape
        (0, 480), (3, 240), (5, 240),
        (7, 480), (10, 480),
        (12, 960), (10, 240), (7, 240),
        (5, 480), (3, 480), (0, 960),
    ],

    # ---- VAN HALEN / EDDIE VAN HALEN ----
    'vanhalen_eruption': [
        # "Eruption" tapping pattern - rapid arpeggios
        (0, 120), (5, 120), (12, 120),
        (0, 120), (4, 120), (12, 120),
        (0, 120), (3, 120), (12, 120),
        (0, 120), (5, 120), (12, 120),
    ],
    'vanhalen_jump': [
        # "Jump" synth riff transposed to guitar
        (0, 480), (0, 240), (2, 240),
        (5, 480), (5, 240), (4, 240),
        (2, 960),
    ],
    'vanhalen_hot_teacher': [
        # "Hot for Teacher" tapping
        (0, 120), (7, 120), (12, 120), (19, 120),
        (12, 120), (7, 120), (0, 120), (7, 120),
        (12, 120), (15, 120), (12, 120), (7, 120),
    ],

    # ---- JIMI HENDRIX ----
    'hendrix_purple_haze': [
        # "Purple Haze" tritone riff shape
        (0, 240), (6, 240), (7, 480),
        (0, 240), (6, 240), (7, 240), (8, 240),
        (7, 480),
    ],
    'hendrix_voodoo_child': [
        # "Voodoo Child" wah-wah riff
        (0, 360), (3, 120), (5, 240), (3, 120),
        (0, 120), (-2, 240), (0, 480),
        (3, 240), (5, 240), (7, 480),
    ],
    'hendrix_foxy': [
        # "Foxy Lady" feedback riff shape
        (0, 480), (0, 240), (3, 240),
        (5, 480), (3, 480),
        (0, 960),
    ],

    # ---- AC/DC / ANGUS YOUNG ----
    'angus_thunderstruck': [
        # "Thunderstruck" rapid pull-off pattern
        (0, 120), (12, 120), (0, 120), (12, 120),
        (0, 120), (11, 120), (0, 120), (11, 120),
        (0, 120), (10, 120), (0, 120), (10, 120),
        (0, 120), (9, 120), (0, 120), (9, 120),
    ],
    'angus_back_in_black': [
        # "Back in Black" riff shape
        (0, 240), (5, 120), (3, 120),
        (0, 240), (7, 120), (5, 120),
        (0, 240), (5, 120), (3, 120),
        (0, 480),
    ],
    'angus_highway': [
        # "Highway to Hell" chord riff shape
        (0, 480), (0, 240), (0, 240),
        (5, 480), (3, 480),
        (0, 960),
    ],

    # ---- IRON MAIDEN / DAVE MURRAY ----
    'maiden_trooper': [
        # "The Trooper" galloping melody
        (0, 160), (0, 160), (2, 160),
        (3, 160), (3, 160), (5, 160),
        (7, 160), (7, 160), (5, 160),
        (3, 160), (2, 160), (0, 160),
    ],
    'maiden_aces': [
        # "Aces High" speed run
        (0, 120), (2, 120), (3, 120), (5, 120),
        (7, 120), (9, 120), (10, 120), (12, 120),
        (14, 120), (12, 120), (10, 120), (9, 120),
        (7, 120), (5, 120), (3, 120), (2, 120),
    ],

    # ---- RADIOHEAD / JONNY GREENWOOD ----
    'radiohead_creep': [
        # "Creep" clean arpeggio
        (0, 480), (4, 480), (7, 480), (12, 480),
        (11, 480), (7, 480), (4, 480), (0, 480),
    ],
    'radiohead_paranoid': [
        # "Paranoid Android" angular riff
        (0, 240), (1, 240), (3, 120), (4, 120),
        (7, 240), (6, 240), (4, 240),
        (3, 120), (1, 120), (0, 480),
    ],

    # ---- NIRVANA / KURT COBAIN ----
    'cobain_teen_spirit': [
        # "Smells Like Teen Spirit" power chord riff shape
        (0, 240), (0, 120), (0, 120),
        (3, 240), (3, 120), (3, 120),
        (5, 240), (5, 120), (5, 120),
        (3, 240), (3, 240),
    ],
    'cobain_lithium': [
        # "Lithium" verse riff
        (0, 480), (5, 480),
        (7, 480), (5, 480),
        (3, 480), (0, 480),
    ],
}


# =============================================================================
# BLUES RIFFS - For jazz/blues styles
# =============================================================================
BLUES_RIFFS = {
    'bb_king_thrill': [
        # B.B. King "The Thrill Is Gone" opening lick
        (0, 480), (3, 960),
        (0, 480), (-2, 480),
        (0, 1920),
    ],
    'bb_king_lucille': [
        # "Lucille" vibrato phrase
        (7, 960), (5, 480), (3, 480),
        (0, 960), (3, 240), (0, 240),
        (-2, 1920),
    ],
    'clapton_crossroads': [
        # "Crossroads" blues-rock lick
        (0, 240), (3, 120), (5, 120), (7, 240),
        (5, 120), (3, 120), (0, 240), (3, 120),
        (0, 120), (-2, 480),
    ],
    'clapton_layla': [
        # "Layla" main riff shape
        (0, 240), (3, 240), (5, 480),
        (3, 240), (0, 240), (-2, 480),
        (0, 960),
    ],
    'srv_pride_joy': [
        # "Pride and Joy" Texas shuffle lick
        (0, 160), (3, 160), (5, 160),
        (7, 160), (5, 160), (3, 160),
        (0, 160), (3, 160), (5, 160),
        (7, 480),
    ],
    'srv_texas_flood': [
        # "Texas Flood" slow blues
        (0, 960), (3, 480),
        (5, 480), (7, 960),
        (5, 480), (3, 480),
        (0, 1920),
    ],
}


# =============================================================================
# ARPEGGIO PATTERNS - For electronic/calm styles
# =============================================================================
ARPEGGIO_PATTERNS = {
    'ascending_triad': [
        (0, 240), (4, 240), (7, 240), (12, 240),
    ],
    'descending_triad': [
        (12, 240), (7, 240), (4, 240), (0, 240),
    ],
    'broken_minor': [
        (0, 240), (3, 240), (7, 240), (12, 240),
        (7, 240), (3, 240),
    ],
    'broken_seventh': [
        (0, 240), (4, 240), (7, 240), (10, 240),
        (12, 240), (10, 240), (7, 240), (4, 240),
    ],
    'sus4_shimmer': [
        (0, 480), (5, 480), (7, 480), (12, 480),
    ],
    'floyd_arpeggio': [
        # Pink Floyd "Breathe" style
        (0, 480), (7, 480), (12, 480),
        (16, 480), (12, 480), (7, 480),
    ],
    'knopfler_picking': [
        # "Sultans of Swing" fingerpicking feel
        (0, 240), (4, 240), (7, 120), (4, 120),
        (0, 240), (3, 240), (7, 120), (3, 120),
    ],
    'trance_gate': [
        # Gated trance arpeggio
        (0, 120), (0, 120), (7, 120), (7, 120),
        (12, 120), (12, 120), (7, 120), (7, 120),
    ],
}


# =============================================================================
# STYLE → RIFF MAPPING
# =============================================================================
# Maps lead style names to their associated riff pool
STYLE_RIFF_MAP = {
    # Rock styles
    'page_blues_rock':      ['page_whole_lotta', 'page_kashmir', 'page_blackdog'],
    'may_harmonic':         ['may_bohemian_arp', 'may_brighton_rock', 'may_we_will_rock'],
    'slash_hard_rock':      ['slash_sweet_child', 'slash_paradise', 'slash_november'],
    'vanhalen_eruption':    ['vanhalen_eruption', 'vanhalen_jump', 'vanhalen_hot_teacher'],
    'hendrix_psychedelic':  ['hendrix_purple_haze', 'hendrix_voodoo_child', 'hendrix_foxy'],
    'dimebag_shred':        ['dimebag_walk', 'dimebag_cowboys', 'dimebag_floods'],
    'angus_acdc':           ['angus_thunderstruck', 'angus_back_in_black', 'angus_highway'],
    'maiden_gallop':        ['maiden_trooper', 'maiden_aces'],
    'cobain_grunge':        ['cobain_teen_spirit', 'cobain_lithium'],
    'morello_riff':         ['cobain_teen_spirit', 'hendrix_foxy'],
    'berry_rockabilly':     ['angus_back_in_black'],
    'prog_rock':            ['radiohead_paranoid', 'may_bohemian_arp'],

    # Sad styles
    'gilmour_soaring':      ['gilmour_comfortably', 'gilmour_time', 'gilmour_shine_on'],
    'radiohead_angular':    ['radiohead_creep', 'radiohead_paranoid'],
    'clapton_weeping':      ['clapton_layla', 'clapton_crossroads'],
    'hendrix_little_wing':  ['hendrix_voodoo_child'],

    # Jazz/blues styles
    'bb_king_blues':        ['bb_king_thrill', 'bb_king_lucille'],
    'clapton_cream':        ['clapton_crossroads', 'clapton_layla'],
    'srv_texas_blues':      ['srv_pride_joy', 'srv_texas_flood'],

    # Happy styles
    'may_anthem':           ['may_bohemian_arp', 'may_we_will_rock'],
    'vanhalen_bright':      ['vanhalen_jump', 'vanhalen_eruption'],

    # Electronic styles
    'floyd_echoes':         ['gilmour_shine_on', 'gilmour_time'],
    'trance_arp':           ['trance_gate'],

    # Calm styles
    'gilmour_ambient':      ['gilmour_shine_on', 'gilmour_comfortably'],
    'knopfler_fingerstyle': ['knopfler_picking'],
}


def get_riff_for_style(style_name: str) -> list:
    """
    Get a random riff pattern for the given lead style.
    Returns list of (interval, duration) or empty list if no riffs mapped.
    """
    import random as _rand
    riff_names = STYLE_RIFF_MAP.get(style_name, [])
    if not riff_names:
        return []
    riff_name = _rand.choice(riff_names)

    # Look in all riff dictionaries
    for pool in [ROCK_RIFFS, BLUES_RIFFS, ARPEGGIO_PATTERNS]:
        if riff_name in pool:
            return pool[riff_name]
    return []


def transpose_riff(riff: list, root_midi: int, octave: int = 5) -> list:
    """
    Transpose a riff pattern to a specific root note and octave.

    Args:
        riff: list of (interval, duration) tuples
        root_midi: MIDI note number of the root (e.g. 60 for C4)
        octave: Target octave

    Returns:
        list of (absolute_midi_note, duration) tuples
    """
    base = octave * 12
    return [(base + root_midi % 12 + interval, dur) for interval, dur in riff]
