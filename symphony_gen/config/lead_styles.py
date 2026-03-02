"""
Lead melody style parameters.
Sub-styles inspired by legendary guitarists and iconic bands from 50s-2000s.

Each mood has multiple variations to prevent repetitive sounds.
Every sub-style is tuned so the output is IDENTIFIABLE —
you should be able to hear the difference between Gilmour and Slash, or
Van Halen tapping vs BB King bends.

Key parameters that differentiate styles:
  - note_density: how many notes per beat (high = shreddy, low = spacey)
  - rest_probability: gaps between phrases
  - velocity_range: dynamic range (hard rock loud, ambient soft)
  - legato: note overlap (1.0 = fully connected, 0.3 = choppy)
  - swing: rhythmic swing feel (jazz/blues high, rock/metal 0)
  - bend_probability: guitar-like pitch bends
  - vibrato_intensity: note wobble (blues high, punk 0)
  - preferred_intervals: which intervals are favored (defines the "sound")
  - articulation: controls duration/dynamic behavior engine
  - instrument: General MIDI instrument mapping
"""

import random

# =============================================================================
# LEAD MELODY STYLE PARAMETERS
# =============================================================================
LEAD_STYLES = {
    # =========================================================================
    # HAPPY - Uplifting, energetic lead styles
    # =========================================================================
    'happy': {
        'sub_styles': [
            {
                # Beatles-inspired bright pop melodies
                'name': 'beatles_pop',
                'note_density': 0.5,
                'rest_probability': 0.15,
                'velocity_range': (75, 100),
                'octave': 5,
                'legato': 0.75,
                'swing': 0.0,
                'preferred_intervals': [2, 4, 5, 7],
                'articulation': 'medium',
                'instrument': 'clean_guitar',
            },
            {
                # Nile Rodgers funk rhythm style
                'name': 'funk_rhythm',
                'note_density': 0.6,
                'rest_probability': 0.2,
                'velocity_range': (80, 110),
                'octave': 5,
                'legato': 0.5,
                'swing': 0.1,
                'preferred_intervals': [0, 3, 4, 7],
                'articulation': 'staccato',
                'instrument': 'clean_guitar',
            },
            {
                # 80s synth pop lead
                'name': 'synth_pop',
                'note_density': 0.55,
                'rest_probability': 0.12,
                'velocity_range': (85, 105),
                'octave': 5,
                'legato': 0.7,
                'swing': 0.0,
                'preferred_intervals': [2, 3, 5, 7],
                'articulation': 'medium',
                'instrument': 'synth_lead',
            },
            {
                # Queen - Brian May melodic harmony leads (happy/anthem)
                'name': 'may_anthem',
                'note_density': 0.45,
                'rest_probability': 0.1,
                'velocity_range': (85, 115),
                'octave': 5,
                'legato': 0.85,
                'swing': 0.0,
                'vibrato_intensity': 0.6,
                'preferred_intervals': [3, 4, 5, 7, 12],
                'articulation': 'sustained',
                'instrument': 'overdrive_guitar',
            },
            {
                # Van Halen - bright tapping & harmonics (party rock)
                'name': 'vanhalen_bright',
                'note_density': 0.7,
                'rest_probability': 0.08,
                'velocity_range': (90, 120),
                'octave': 5,
                'legato': 0.55,
                'swing': 0.0,
                'tapping': True,
                'preferred_intervals': [3, 4, 5, 7, 12],
                'articulation': 'staccato',
                'instrument': 'distortion_guitar',
            },
        ],
    },

    # =========================================================================
    # SAD - Melancholic, emotional lead styles
    # =========================================================================
    'sad': {
        'sub_styles': [
            {
                # David Gilmour (Pink Floyd) - long, soaring bends
                'name': 'gilmour_soaring',
                'note_density': 0.18,
                'rest_probability': 0.35,
                'velocity_range': (50, 82),
                'octave': 5,
                'legato': 0.95,
                'swing': 0.0,
                'bend_probability': 0.4,
                'vibrato_intensity': 0.85,
                'preferred_intervals': [2, 3, 5, 7, 12],
                'articulation': 'legato',
                'instrument': 'overdrive_guitar',
            },
            {
                # Radiohead - Thom Yorke angular, dissonant melancholy
                'name': 'radiohead_angular',
                'note_density': 0.32,
                'rest_probability': 0.28,
                'velocity_range': (45, 78),
                'octave': 4,
                'legato': 0.55,
                'swing': 0.0,
                'preferred_intervals': [1, 2, 6, 7, 11],
                'articulation': 'varied',
                'instrument': 'clean_guitar',
            },
            {
                # The Smiths - Johnny Marr jangly arpeggios
                'name': 'smiths_jangle',
                'note_density': 0.5,
                'rest_probability': 0.15,
                'velocity_range': (60, 85),
                'octave': 5,
                'legato': 0.4,
                'swing': 0.05,
                'preferred_intervals': [3, 4, 5, 7],
                'articulation': 'staccato',
                'instrument': 'clean_guitar',
            },
            {
                # Classical piano ballad - Chopin-inspired
                'name': 'piano_ballad',
                'note_density': 0.22,
                'rest_probability': 0.22,
                'velocity_range': (40, 72),
                'octave': 5,
                'legato': 0.9,
                'swing': 0.0,
                'rubato': 0.2,
                'preferred_intervals': [2, 3, 4, 5],
                'articulation': 'legato',
                'instrument': 'piano',
            },
            {
                # Eric Clapton "Tears in Heaven" - gentle blues weeping
                'name': 'clapton_weeping',
                'note_density': 0.25,
                'rest_probability': 0.3,
                'velocity_range': (50, 80),
                'octave': 5,
                'legato': 0.8,
                'swing': 0.1,
                'bend_probability': 0.35,
                'vibrato_intensity': 0.7,
                'preferred_intervals': [2, 3, 5, 7, 10],
                'articulation': 'expressive',
                'instrument': 'nylon_guitar',
            },
            {
                # Hendrix - "Little Wing" clean chord-melody
                'name': 'hendrix_little_wing',
                'note_density': 0.35,
                'rest_probability': 0.2,
                'velocity_range': (55, 85),
                'octave': 5,
                'legato': 0.75,
                'swing': 0.08,
                'bend_probability': 0.2,
                'preferred_intervals': [2, 3, 4, 5, 7],
                'articulation': 'medium',
                'instrument': 'clean_guitar',
            },
        ],
    },

    # =========================================================================
    # ROCK - Powerful, driving lead styles across decades
    # =========================================================================
    'rock': {
        'sub_styles': [
            {
                # Jimmy Page (Led Zeppelin) - blues-rock riffs
                'name': 'page_blues_rock',
                'note_density': 0.45,
                'rest_probability': 0.1,
                'velocity_range': (90, 120),
                'octave': 4,
                'legato': 0.65,
                'swing': 0.08,
                'bend_probability': 0.25,
                'hammer_on_probability': 0.2,
                'preferred_intervals': [3, 5, 7, 10],
                'articulation': 'aggressive',
                'instrument': 'distortion_guitar',
            },
            {
                # Brian May (Queen) - layered harmonized leads
                'name': 'may_harmonic',
                'note_density': 0.4,
                'rest_probability': 0.12,
                'velocity_range': (85, 110),
                'octave': 5,
                'legato': 0.8,
                'swing': 0.0,
                'vibrato_intensity': 0.7,
                'preferred_intervals': [3, 4, 5, 7, 12],
                'articulation': 'sustained',
                'instrument': 'overdrive_guitar',
            },
            {
                # Slash (Guns N' Roses) - 80s hard rock wailing
                'name': 'slash_hard_rock',
                'note_density': 0.5,
                'rest_probability': 0.08,
                'velocity_range': (95, 125),
                'octave': 5,
                'legato': 0.6,
                'swing': 0.0,
                'bend_probability': 0.4,
                'preferred_intervals': [2, 3, 5, 7, 10],
                'articulation': 'aggressive',
                'instrument': 'distortion_guitar',
            },
            {
                # Eddie Van Halen - tapping, harmonics, virtuoso shred
                'name': 'vanhalen_eruption',
                'note_density': 0.8,
                'rest_probability': 0.05,
                'velocity_range': (95, 127),
                'octave': 5,
                'legato': 0.45,
                'swing': 0.0,
                'tapping': True,
                'hammer_on_probability': 0.4,
                'preferred_intervals': [3, 4, 5, 7, 12],
                'articulation': 'shred',
                'instrument': 'distortion_guitar',
            },
            {
                # Jimi Hendrix - psychedelic wah-wah / fuzz
                'name': 'hendrix_psychedelic',
                'note_density': 0.5,
                'rest_probability': 0.12,
                'velocity_range': (85, 115),
                'octave': 5,
                'legato': 0.65,
                'swing': 0.1,
                'bend_probability': 0.35,
                'vibrato_intensity': 0.7,
                'wah_wah': True,
                'preferred_intervals': [3, 4, 5, 7, 10],
                'articulation': 'expressive',
                'instrument': 'overdrive_guitar',
            },
            {
                # Dimebag Darrell (Pantera) - heavy groove shred
                'name': 'dimebag_shred',
                'note_density': 0.7,
                'rest_probability': 0.05,
                'velocity_range': (100, 127),
                'octave': 4,
                'legato': 0.5,
                'swing': 0.0,
                'bend_probability': 0.3,
                'hammer_on_probability': 0.35,
                'preferred_intervals': [1, 2, 3, 5, 6],
                'articulation': 'shred',
                'instrument': 'distortion_guitar',
            },
            {
                # Angus Young (AC/DC) - blues-pentatonic rock
                'name': 'angus_acdc',
                'note_density': 0.55,
                'rest_probability': 0.08,
                'velocity_range': (95, 120),
                'octave': 5,
                'legato': 0.55,
                'swing': 0.05,
                'bend_probability': 0.3,
                'preferred_intervals': [3, 5, 7, 10],
                'articulation': 'aggressive',
                'instrument': 'distortion_guitar',
            },
            {
                # Dave Murray/Adrian Smith (Iron Maiden) - galloping harmonies
                'name': 'maiden_gallop',
                'note_density': 0.6,
                'rest_probability': 0.08,
                'velocity_range': (90, 115),
                'octave': 5,
                'legato': 0.6,
                'swing': 0.0,
                'preferred_intervals': [2, 3, 4, 5, 7],
                'articulation': 'gallop',
                'instrument': 'distortion_guitar',
            },
            {
                # 50s rock n roll - Chuck Berry style
                'name': 'berry_rockabilly',
                'note_density': 0.55,
                'rest_probability': 0.1,
                'velocity_range': (85, 105),
                'octave': 5,
                'legato': 0.5,
                'swing': 0.15,
                'preferred_intervals': [2, 3, 4, 5, 7],
                'articulation': 'staccato',
                'instrument': 'clean_guitar',
            },
            {
                # 70s prog rock - complex patterns (Yes/Genesis)
                'name': 'prog_rock',
                'note_density': 0.5,
                'rest_probability': 0.15,
                'velocity_range': (80, 105),
                'octave': 5,
                'legato': 0.7,
                'swing': 0.0,
                'preferred_intervals': [2, 4, 5, 6, 7, 9],
                'articulation': 'varied',
                'instrument': 'overdrive_guitar',
            },
            {
                # Tom Morello (RATM) - avant-garde noise/funk
                'name': 'morello_riff',
                'note_density': 0.45,
                'rest_probability': 0.15,
                'velocity_range': (90, 125),
                'octave': 4,
                'legato': 0.4,
                'swing': 0.1,
                'preferred_intervals': [1, 3, 5, 7],
                'articulation': 'staccato',
                'instrument': 'distortion_guitar',
            },
            {
                # Kurt Cobain (Nirvana) - grunge raw power
                'name': 'cobain_grunge',
                'note_density': 0.4,
                'rest_probability': 0.12,
                'velocity_range': (90, 120),
                'octave': 4,
                'legato': 0.5,
                'swing': 0.0,
                'preferred_intervals': [3, 5, 7, 10],
                'articulation': 'aggressive',
                'instrument': 'distortion_guitar',
            },
        ],
    },

    # =========================================================================
    # JAZZ - Sophisticated, improvisational styles
    # =========================================================================
    'jazz': {
        'sub_styles': [
            {
                # B.B. King - expressive blues bends, "singing" guitar
                'name': 'bb_king_blues',
                'note_density': 0.3,
                'rest_probability': 0.3,
                'velocity_range': (60, 95),
                'octave': 5,
                'legato': 0.8,
                'swing': 0.25,
                'bend_probability': 0.5,
                'vibrato_intensity': 0.95,
                'preferred_intervals': [3, 5, 7, 10],
                'articulation': 'expressive',
                'instrument': 'clean_guitar',
            },
            {
                # Wes Montgomery - octave melodies, warm tone
                'name': 'wes_octaves',
                'note_density': 0.4,
                'rest_probability': 0.2,
                'velocity_range': (60, 90),
                'octave': 4,
                'legato': 0.7,
                'swing': 0.33,
                'preferred_intervals': [5, 7, 12],
                'articulation': 'warm',
                'instrument': 'jazz_guitar',
            },
            {
                # Charlie Parker bebop - fast chromatic lines
                'name': 'bebop_lines',
                'note_density': 0.75,
                'rest_probability': 0.12,
                'velocity_range': (70, 100),
                'octave': 5,
                'legato': 0.6,
                'swing': 0.2,
                'preferred_intervals': [1, 2, 3, 4, 5],
                'articulation': 'fast',
                'instrument': 'saxophone',
            },
            {
                # Cool jazz - Miles Davis trumpet style
                'name': 'cool_jazz',
                'note_density': 0.25,
                'rest_probability': 0.4,
                'velocity_range': (48, 75),
                'octave': 5,
                'legato': 0.88,
                'swing': 0.15,
                'preferred_intervals': [2, 4, 5, 7],
                'articulation': 'sparse',
                'instrument': 'muted_trumpet',
            },
            {
                # Eric Clapton "woman tone" - Cream-era blues-jazz
                'name': 'clapton_cream',
                'note_density': 0.4,
                'rest_probability': 0.2,
                'velocity_range': (70, 100),
                'octave': 5,
                'legato': 0.75,
                'swing': 0.2,
                'bend_probability': 0.35,
                'vibrato_intensity': 0.8,
                'preferred_intervals': [3, 5, 7, 10],
                'articulation': 'expressive',
                'instrument': 'overdrive_guitar',
            },
            {
                # SRV (Stevie Ray Vaughan) - Texas blues fire
                'name': 'srv_texas_blues',
                'note_density': 0.5,
                'rest_probability': 0.12,
                'velocity_range': (80, 115),
                'octave': 4,
                'legato': 0.6,
                'swing': 0.2,
                'bend_probability': 0.45,
                'vibrato_intensity': 0.85,
                'hammer_on_probability': 0.25,
                'preferred_intervals': [3, 5, 7, 10, 12],
                'articulation': 'aggressive',
                'instrument': 'overdrive_guitar',
            },
        ],
    },

    # =========================================================================
    # ELECTRONIC - Modern synth-driven styles
    # =========================================================================
    'electronic': {
        'sub_styles': [
            {
                # Kraftwerk - robotic precision
                'name': 'kraftwerk_robotic',
                'note_density': 0.5,
                'rest_probability': 0.1,
                'velocity_range': (80, 100),
                'octave': 5,
                'legato': 0.4,
                'swing': 0.0,
                'quantize': True,
                'preferred_intervals': [2, 4, 5, 7],
                'articulation': 'precise',
                'instrument': 'square_lead',
            },
            {
                # Daft Punk - funky vocoder melodies
                'name': 'daft_funk',
                'note_density': 0.55,
                'rest_probability': 0.15,
                'velocity_range': (85, 110),
                'octave': 5,
                'legato': 0.6,
                'swing': 0.1,
                'quantize': True,
                'preferred_intervals': [3, 4, 5, 7],
                'articulation': 'funky',
                'instrument': 'synth_lead',
            },
            {
                # Ambient/Blade Runner - atmospheric pads
                'name': 'vangelis_ambient',
                'note_density': 0.15,
                'rest_probability': 0.35,
                'velocity_range': (45, 75),
                'octave': 4,
                'legato': 0.95,
                'swing': 0.0,
                'preferred_intervals': [5, 7, 12],
                'articulation': 'atmospheric',
                'instrument': 'warm_pad',
            },
            {
                # Trance arpeggio style
                'name': 'trance_arp',
                'note_density': 0.8,
                'rest_probability': 0.03,
                'velocity_range': (75, 105),
                'octave': 5,
                'legato': 0.3,
                'swing': 0.0,
                'quantize': True,
                'preferred_intervals': [3, 4, 7, 12],
                'articulation': 'staccato',
                'instrument': 'sawtooth_lead',
            },
            {
                # Pink Floyd - Gilmour delay/echo synth texture
                'name': 'floyd_echoes',
                'note_density': 0.2,
                'rest_probability': 0.3,
                'velocity_range': (50, 80),
                'octave': 5,
                'legato': 0.9,
                'swing': 0.0,
                'delay_feel': True,
                'bend_probability': 0.15,
                'preferred_intervals': [5, 7, 12],
                'articulation': 'atmospheric',
                'instrument': 'warm_pad',
            },
        ],
    },

    # =========================================================================
    # CALM - Peaceful, ambient styles
    # =========================================================================
    'calm': {
        'sub_styles': [
            {
                # Mark Knopfler (Dire Straits) - fingerpicked clean
                'name': 'knopfler_fingerstyle',
                'note_density': 0.25,
                'rest_probability': 0.3,
                'velocity_range': (45, 70),
                'octave': 5,
                'legato': 0.8,
                'swing': 0.05,
                'preferred_intervals': [2, 4, 5, 7],
                'articulation': 'gentle',
                'instrument': 'nylon_guitar',
            },
            {
                # Enya/New Age ambient
                'name': 'new_age_ambient',
                'note_density': 0.12,
                'rest_probability': 0.45,
                'velocity_range': (35, 60),
                'octave': 5,
                'legato': 0.95,
                'swing': 0.0,
                'preferred_intervals': [5, 7, 12],
                'articulation': 'ethereal',
                'instrument': 'new_age_pad',
            },
            {
                # Classical guitar - Spanish/Segovia
                'name': 'classical_guitar',
                'note_density': 0.3,
                'rest_probability': 0.2,
                'velocity_range': (50, 75),
                'octave': 4,
                'legato': 0.7,
                'swing': 0.0,
                'rubato': 0.1,
                'preferred_intervals': [2, 3, 4, 5, 7],
                'articulation': 'classical',
                'instrument': 'nylon_guitar',
            },
            {
                # David Gilmour ambient solos - spacey delay
                'name': 'gilmour_ambient',
                'note_density': 0.12,
                'rest_probability': 0.4,
                'velocity_range': (40, 65),
                'octave': 5,
                'legato': 0.92,
                'swing': 0.0,
                'bend_probability': 0.25,
                'delay_feel': True,
                'preferred_intervals': [2, 5, 7, 12],
                'articulation': 'spacey',
                'instrument': 'clean_guitar',
            },
            {
                # Jeff Beck - gentle jazz-rock dynamics
                'name': 'beck_gentle',
                'note_density': 0.2,
                'rest_probability': 0.3,
                'velocity_range': (40, 70),
                'octave': 5,
                'legato': 0.85,
                'swing': 0.05,
                'bend_probability': 0.2,
                'vibrato_intensity': 0.5,
                'preferred_intervals': [2, 4, 5, 7],
                'articulation': 'gentle',
                'instrument': 'clean_guitar',
            },
        ],
    },
}


def get_random_substyle(mood: str) -> dict:
    """Get a random sub-style configuration for the given mood."""
    if mood in LEAD_STYLES:
        sub_styles = LEAD_STYLES[mood]['sub_styles']
        return random.choice(sub_styles)
    return LEAD_STYLES['happy']['sub_styles'][0]
