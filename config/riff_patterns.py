"""
Riff and arpeggio pattern library.
Contains MIDI note sequences inspired by iconic bands and guitarists.

Each riff is a list of (interval_from_root, duration_in_ticks, technique) tuples.
Intervals are in semitones from the root note. This makes them
transposable to any key. The technique string tells the effects processor
how to articulate each note.

Valid techniques:
  normal, bend_half, bend_whole, bend_slow, vibrato,
  hammer_on, pull_off, slide_up, slide_down,
  tap, palm_mute, staccato, legato

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
        (0, 240, 'normal'), (3, 120, 'hammer_on'), (5, 120, 'hammer_on'), (7, 240, 'bend_half'),
        (5, 240, 'pull_off'), (3, 120, 'pull_off'), (0, 120, 'normal'), (-2, 480, 'vibrato'),
    ],
    'page_kashmir': [
        # "Kashmir" descending chromatic riff
        (0, 360, 'normal'), (-1, 120, 'slide_down'), (-2, 360, 'normal'), (-3, 120, 'slide_down'),
        (-4, 360, 'normal'), (-5, 120, 'slide_down'), (-7, 480, 'vibrato'),
    ],
    'page_blackdog': [
        # "Black Dog" bluesy syncopated riff
        (0, 120, 'normal'), (3, 120, 'hammer_on'), (5, 120, 'hammer_on'), (7, 120, 'bend_half'),
        (5, 120, 'pull_off'), (3, 120, 'pull_off'), (0, 240, 'normal'), (5, 120, 'hammer_on'),
        (3, 120, 'pull_off'), (0, 480, 'vibrato'),
    ],

    # ---- QUEEN / BRIAN MAY ----
    'may_bohemian_arp': [
        # Bohemian Rhapsody-style ascending arpeggio
        (0, 240, 'legato'), (4, 240, 'legato'), (7, 240, 'legato'), (12, 240, 'legato'),
        (16, 240, 'legato'), (19, 240, 'legato'), (24, 480, 'vibrato'),
    ],
    'may_brighton_rock': [
        # Brighton Rock tapping pattern - fast harmonics
        (0, 120, 'tap'), (7, 120, 'tap'), (12, 120, 'tap'), (7, 120, 'tap'),
        (0, 120, 'tap'), (4, 120, 'tap'), (7, 120, 'tap'), (4, 120, 'tap'),
        (0, 120, 'tap'), (3, 120, 'tap'), (7, 120, 'tap'), (3, 120, 'tap'),
        (0, 120, 'tap'), (7, 120, 'tap'), (12, 480, 'vibrato'),
    ],
    'may_we_will_rock': [
        # "We Will Rock You" guitar solo melody shape
        (0, 480, 'normal'), (2, 240, 'slide_up'), (3, 240, 'normal'),
        (5, 480, 'vibrato'), (3, 240, 'slide_down'), (2, 240, 'normal'),
        (0, 960, 'vibrato'),
    ],

    # ---- GUNS N' ROSES / SLASH ----
    'slash_sweet_child': [
        # "Sweet Child O' Mine" arpeggio riff
        (0, 120, 'normal'), (12, 120, 'hammer_on'), (7, 120, 'pull_off'), (8, 120, 'normal'),
        (5, 120, 'normal'), (12, 120, 'hammer_on'), (7, 120, 'pull_off'), (8, 120, 'normal'),
    ],
    'slash_paradise': [
        # "Paradise City" fast run
        (0, 120, 'hammer_on'), (2, 120, 'hammer_on'), (3, 120, 'hammer_on'), (5, 120, 'hammer_on'),
        (7, 120, 'hammer_on'), (8, 120, 'hammer_on'), (10, 120, 'hammer_on'), (12, 120, 'bend_half'),
        (10, 120, 'pull_off'), (8, 120, 'pull_off'), (7, 120, 'pull_off'), (5, 120, 'pull_off'),
        (3, 240, 'normal'), (0, 240, 'vibrato'),
    ],
    'slash_november': [
        # "November Rain" melodic solo shape
        (0, 480, 'normal'), (3, 240, 'slide_up'), (5, 240, 'normal'),
        (7, 480, 'bend_half'), (8, 480, 'vibrato'),
        (7, 240, 'slide_down'), (5, 240, 'normal'), (3, 480, 'vibrato'),
        (0, 960, 'vibrato'),
    ],

    # ---- PINK FLOYD / DAVID GILMOUR ----
    'gilmour_comfortably': [
        # "Comfortably Numb" solo opening shape - huge bends
        (0, 960, 'bend_whole'), (3, 480, 'vibrato'), (5, 480, 'bend_half'),
        (7, 1920, 'vibrato'),
        (5, 480, 'slide_down'), (3, 480, 'vibrato'), (0, 960, 'vibrato'),
    ],
    'gilmour_time': [
        # "Time" solo - ascending with space
        (0, 480, 'normal'), (2, 480, 'slide_up'),
        (5, 960, 'vibrato'),
        (7, 480, 'bend_half'), (9, 480, 'vibrato'),
        (12, 1920, 'vibrato'),
    ],
    'gilmour_shine_on': [
        # "Shine On You Crazy Diamond" 4-note motif
        (7, 960, 'bend_slow'), (5, 960, 'vibrato'),
        (3, 960, 'vibrato'), (0, 1920, 'vibrato'),
    ],

    # ---- PANTERA / DIMEBAG DARRELL ----
    'dimebag_walk': [
        # "Walk" grinding riff
        (0, 240, 'palm_mute'), (0, 120, 'palm_mute'), (0, 120, 'palm_mute'),
        (-2, 240, 'palm_mute'), (-3, 240, 'bend_half'),
        (0, 240, 'palm_mute'), (0, 120, 'palm_mute'), (0, 120, 'palm_mute'),
        (-5, 480, 'bend_whole'),
    ],
    'dimebag_cowboys': [
        # "Cowboys from Hell" shred run
        (0, 120, 'hammer_on'), (1, 120, 'hammer_on'), (3, 120, 'hammer_on'), (5, 120, 'hammer_on'),
        (6, 120, 'hammer_on'), (8, 120, 'hammer_on'), (10, 120, 'hammer_on'), (12, 120, 'bend_half'),
        (11, 120, 'pull_off'), (10, 120, 'pull_off'), (8, 120, 'pull_off'), (6, 120, 'pull_off'),
        (5, 120, 'pull_off'), (3, 120, 'pull_off'), (1, 120, 'pull_off'), (0, 120, 'palm_mute'),
    ],
    'dimebag_floods': [
        # "Floods" melodic outro solo shape
        (0, 480, 'normal'), (3, 240, 'slide_up'), (5, 240, 'hammer_on'),
        (7, 480, 'bend_half'), (10, 480, 'vibrato'),
        (12, 960, 'vibrato'), (10, 240, 'slide_down'), (7, 240, 'pull_off'),
        (5, 480, 'vibrato'), (3, 480, 'slide_down'), (0, 960, 'vibrato'),
    ],

    # ---- VAN HALEN / EDDIE VAN HALEN ----
    'vanhalen_eruption': [
        # "Eruption" tapping pattern - rapid arpeggios
        (0, 120, 'tap'), (5, 120, 'tap'), (12, 120, 'tap'),
        (0, 120, 'tap'), (4, 120, 'tap'), (12, 120, 'tap'),
        (0, 120, 'tap'), (3, 120, 'tap'), (12, 120, 'tap'),
        (0, 120, 'tap'), (5, 120, 'tap'), (12, 120, 'tap'),
    ],
    'vanhalen_jump': [
        # "Jump" synth riff transposed to guitar
        (0, 480, 'normal'), (0, 240, 'normal'), (2, 240, 'hammer_on'),
        (5, 480, 'vibrato'), (5, 240, 'normal'), (4, 240, 'pull_off'),
        (2, 960, 'vibrato'),
    ],
    'vanhalen_hot_teacher': [
        # "Hot for Teacher" tapping
        (0, 120, 'tap'), (7, 120, 'tap'), (12, 120, 'tap'), (19, 120, 'tap'),
        (12, 120, 'tap'), (7, 120, 'tap'), (0, 120, 'tap'), (7, 120, 'tap'),
        (12, 120, 'tap'), (15, 120, 'tap'), (12, 120, 'tap'), (7, 120, 'tap'),
    ],

    # ---- JIMI HENDRIX ----
    'hendrix_purple_haze': [
        # "Purple Haze" tritone riff shape
        (0, 240, 'normal'), (6, 240, 'bend_half'), (7, 480, 'vibrato'),
        (0, 240, 'normal'), (6, 240, 'bend_half'), (7, 240, 'hammer_on'), (8, 240, 'vibrato'),
        (7, 480, 'vibrato'),
    ],
    'hendrix_voodoo_child': [
        # "Voodoo Child" wah-wah riff
        (0, 360, 'bend_half'), (3, 120, 'hammer_on'), (5, 240, 'vibrato'), (3, 120, 'pull_off'),
        (0, 120, 'normal'), (-2, 240, 'bend_half'), (0, 480, 'vibrato'),
        (3, 240, 'hammer_on'), (5, 240, 'bend_half'), (7, 480, 'vibrato'),
    ],
    'hendrix_foxy': [
        # "Foxy Lady" feedback riff shape
        (0, 480, 'normal'), (0, 240, 'normal'), (3, 240, 'hammer_on'),
        (5, 480, 'bend_half'), (3, 480, 'vibrato'),
        (0, 960, 'vibrato'),
    ],

    # ---- AC/DC / ANGUS YOUNG ----
    'angus_thunderstruck': [
        # "Thunderstruck" rapid pull-off pattern
        (0, 120, 'pull_off'), (12, 120, 'hammer_on'), (0, 120, 'pull_off'), (12, 120, 'hammer_on'),
        (0, 120, 'pull_off'), (11, 120, 'hammer_on'), (0, 120, 'pull_off'), (11, 120, 'hammer_on'),
        (0, 120, 'pull_off'), (10, 120, 'hammer_on'), (0, 120, 'pull_off'), (10, 120, 'hammer_on'),
        (0, 120, 'pull_off'), (9, 120, 'hammer_on'), (0, 120, 'pull_off'), (9, 120, 'hammer_on'),
    ],
    'angus_back_in_black': [
        # "Back in Black" riff shape
        (0, 240, 'normal'), (5, 120, 'hammer_on'), (3, 120, 'pull_off'),
        (0, 240, 'normal'), (7, 120, 'hammer_on'), (5, 120, 'pull_off'),
        (0, 240, 'normal'), (5, 120, 'hammer_on'), (3, 120, 'pull_off'),
        (0, 480, 'palm_mute'),
    ],
    'angus_highway': [
        # "Highway to Hell" chord riff shape
        (0, 480, 'normal'), (0, 240, 'palm_mute'), (0, 240, 'palm_mute'),
        (5, 480, 'normal'), (3, 480, 'normal'),
        (0, 960, 'vibrato'),
    ],

    # ---- IRON MAIDEN / DAVE MURRAY ----
    'maiden_trooper': [
        # "The Trooper" galloping melody
        (0, 160, 'legato'), (0, 160, 'legato'), (2, 160, 'hammer_on'),
        (3, 160, 'legato'), (3, 160, 'legato'), (5, 160, 'hammer_on'),
        (7, 160, 'legato'), (7, 160, 'legato'), (5, 160, 'pull_off'),
        (3, 160, 'legato'), (2, 160, 'pull_off'), (0, 160, 'legato'),
    ],
    'maiden_aces': [
        # "Aces High" speed run
        (0, 120, 'legato'), (2, 120, 'hammer_on'), (3, 120, 'hammer_on'), (5, 120, 'hammer_on'),
        (7, 120, 'hammer_on'), (9, 120, 'hammer_on'), (10, 120, 'hammer_on'), (12, 120, 'hammer_on'),
        (14, 120, 'pull_off'), (12, 120, 'pull_off'), (10, 120, 'pull_off'), (9, 120, 'pull_off'),
        (7, 120, 'pull_off'), (5, 120, 'pull_off'), (3, 120, 'pull_off'), (2, 120, 'pull_off'),
    ],

    # ---- RADIOHEAD / JONNY GREENWOOD ----
    'radiohead_creep': [
        # "Creep" clean arpeggio
        (0, 480, 'normal'), (4, 480, 'normal'), (7, 480, 'normal'), (12, 480, 'normal'),
        (11, 480, 'normal'), (7, 480, 'normal'), (4, 480, 'normal'), (0, 480, 'normal'),
    ],
    'radiohead_paranoid': [
        # "Paranoid Android" angular riff
        (0, 240, 'staccato'), (1, 240, 'staccato'), (3, 120, 'staccato'), (4, 120, 'staccato'),
        (7, 240, 'normal'), (6, 240, 'normal'), (4, 240, 'staccato'),
        (3, 120, 'staccato'), (1, 120, 'staccato'), (0, 480, 'normal'),
    ],

    # ---- NIRVANA / KURT COBAIN ----
    'cobain_teen_spirit': [
        # "Smells Like Teen Spirit" power chord riff shape
        (0, 240, 'palm_mute'), (0, 120, 'palm_mute'), (0, 120, 'palm_mute'),
        (3, 240, 'palm_mute'), (3, 120, 'palm_mute'), (3, 120, 'palm_mute'),
        (5, 240, 'palm_mute'), (5, 120, 'palm_mute'), (5, 120, 'palm_mute'),
        (3, 240, 'normal'), (3, 240, 'normal'),
    ],
    'cobain_lithium': [
        # "Lithium" verse riff
        (0, 480, 'normal'), (5, 480, 'normal'),
        (7, 480, 'normal'), (5, 480, 'normal'),
        (3, 480, 'normal'), (0, 480, 'palm_mute'),
    ],
}


# =============================================================================
# BLUES RIFFS - For jazz/blues styles
# =============================================================================
BLUES_RIFFS = {
    'bb_king_thrill': [
        # B.B. King "The Thrill Is Gone" opening lick
        (0, 480, 'normal'), (3, 960, 'bend_half'),
        (0, 480, 'normal'), (-2, 480, 'vibrato'),
        (0, 1920, 'vibrato'),
    ],
    'bb_king_lucille': [
        # "Lucille" vibrato phrase
        (7, 960, 'vibrato'), (5, 480, 'slide_down'), (3, 480, 'vibrato'),
        (0, 960, 'bend_half'), (3, 240, 'hammer_on'), (0, 240, 'pull_off'),
        (-2, 1920, 'vibrato'),
    ],
    'clapton_crossroads': [
        # "Crossroads" blues-rock lick
        (0, 240, 'normal'), (3, 120, 'hammer_on'), (5, 120, 'hammer_on'), (7, 240, 'bend_half'),
        (5, 120, 'pull_off'), (3, 120, 'pull_off'), (0, 240, 'normal'), (3, 120, 'slide_up'),
        (0, 120, 'pull_off'), (-2, 480, 'vibrato'),
    ],
    'clapton_layla': [
        # "Layla" main riff shape
        (0, 240, 'normal'), (3, 240, 'slide_up'), (5, 480, 'vibrato'),
        (3, 240, 'slide_down'), (0, 240, 'normal'), (-2, 480, 'bend_half'),
        (0, 960, 'vibrato'),
    ],
    'srv_pride_joy': [
        # "Pride and Joy" Texas shuffle lick
        (0, 160, 'hammer_on'), (3, 160, 'hammer_on'), (5, 160, 'hammer_on'),
        (7, 160, 'bend_half'), (5, 160, 'pull_off'), (3, 160, 'pull_off'),
        (0, 160, 'normal'), (3, 160, 'hammer_on'), (5, 160, 'hammer_on'),
        (7, 480, 'vibrato'),
    ],
    'srv_texas_flood': [
        # "Texas Flood" slow blues
        (0, 960, 'bend_whole'), (3, 480, 'vibrato'),
        (5, 480, 'bend_half'), (7, 960, 'vibrato'),
        (5, 480, 'slide_down'), (3, 480, 'vibrato'),
        (0, 1920, 'vibrato'),
    ],
}


# =============================================================================
# ARPEGGIO PATTERNS - For electronic/calm styles
# =============================================================================
ARPEGGIO_PATTERNS = {
    'ascending_triad': [
        (0, 240, 'legato'), (4, 240, 'legato'), (7, 240, 'legato'), (12, 240, 'legato'),
    ],
    'descending_triad': [
        (12, 240, 'legato'), (7, 240, 'legato'), (4, 240, 'legato'), (0, 240, 'legato'),
    ],
    'broken_minor': [
        (0, 240, 'normal'), (3, 240, 'legato'), (7, 240, 'legato'), (12, 240, 'legato'),
        (7, 240, 'legato'), (3, 240, 'legato'),
    ],
    'broken_seventh': [
        (0, 240, 'normal'), (4, 240, 'legato'), (7, 240, 'legato'), (10, 240, 'legato'),
        (12, 240, 'legato'), (10, 240, 'legato'), (7, 240, 'legato'), (4, 240, 'legato'),
    ],
    'sus4_shimmer': [
        (0, 480, 'normal'), (5, 480, 'vibrato'), (7, 480, 'normal'), (12, 480, 'vibrato'),
    ],
    'floyd_arpeggio': [
        # Pink Floyd "Breathe" style
        (0, 480, 'normal'), (7, 480, 'slide_up'), (12, 480, 'vibrato'),
        (16, 480, 'vibrato'), (12, 480, 'slide_down'), (7, 480, 'normal'),
    ],
    'knopfler_picking': [
        # "Sultans of Swing" fingerpicking feel
        (0, 240, 'normal'), (4, 240, 'normal'), (7, 120, 'normal'), (4, 120, 'normal'),
        (0, 240, 'normal'), (3, 240, 'normal'), (7, 120, 'normal'), (3, 120, 'normal'),
    ],
    'trance_gate': [
        # Gated trance arpeggio
        (0, 120, 'staccato'), (0, 120, 'staccato'), (7, 120, 'staccato'), (7, 120, 'staccato'),
        (12, 120, 'staccato'), (12, 120, 'staccato'), (7, 120, 'staccato'), (7, 120, 'staccato'),
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
    Returns list of (interval, duration, technique) or empty list if no riffs mapped.
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
        riff: list of (interval, duration[, technique]) tuples
        root_midi: MIDI note number of the root (e.g. 60 for C4)
        octave: Target octave

    Returns:
        list of (absolute_midi_note, duration[, technique]) tuples
    """
    base = octave * 12
    result = []
    for item in riff:
        interval = item[0]
        dur = item[1]
        technique = item[2] if len(item) > 2 else 'normal'
        result.append((base + root_midi % 12 + interval, dur, technique))
    return result
