"""
PLANNER: Creates the SongContext (Key, Chords, Structure).
The Conductor determines what the song is before any notes are generated.

Now plans explicit song sections (intro, verse, chorus, bridge, outro)
with per-bar energy curves so every generator can react to structure.

Sections are built in execution order and their durations can be
specified in seconds (converted to bars via BPM).
"""

import math
import random
from typing import Optional, List, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.context import SongContext, BarContext
from config.settings import MOOD_CONFIGS, TICKS_PER_BEAT
from utils.music_theory import (
    parse_key, roman_to_chord, get_scale_notes, name_to_midi, NOTE_NAMES
)

# ----------------------------------------------------------------
# Section energy presets (0.0 = silence, 1.0 = full intensity)
# ----------------------------------------------------------------
SECTION_ENERGY = {
    'intro':      0.25,
    'verse':      0.50,
    'pre_chorus': 0.65,
    'chorus':     0.85,
    'bridge':     0.55,
    'solo':       0.80,
    'outro':      0.30,
    'buildup':    0.70,
}

# Default section execution order and durations (seconds)
DEFAULT_SECTION_ORDER = ['intro', 'verse', 'chorus', 'bridge', 'outro']

DEFAULT_SECTION_SECONDS: Dict[str, float] = {
    'intro':   8.0,
    'verse':  12.0,
    'chorus': 12.0,
    'bridge':  8.0,
    'outro':   8.0,
}

# ----------------------------------------------------------------
# Fallback template system (used when no custom durations given)
# ----------------------------------------------------------------
SECTION_TEMPLATES = {
    8:  [('intro', 2), ('verse', 2), ('chorus', 2), ('outro', 2)],
    12: [('intro', 2), ('verse', 4), ('chorus', 4), ('outro', 2)],
    16: [('intro', 2), ('verse', 4), ('chorus', 4), ('verse', 4), ('outro', 2)],
    20: [('intro', 2), ('verse', 4), ('chorus', 4), ('bridge', 4), ('chorus', 4), ('outro', 2)],
    24: [('intro', 4), ('verse', 4), ('chorus', 4), ('verse', 4), ('chorus', 4), ('outro', 4)],
    32: [('intro', 4), ('verse', 4), ('chorus', 4), ('verse', 4), ('chorus', 4),
         ('bridge', 4), ('chorus', 4), ('outro', 4)],
}


def _pick_template(total_bars: int) -> list:
    """Pick or build a section template that fits *total_bars*."""
    if total_bars in SECTION_TEMPLATES:
        return list(SECTION_TEMPLATES[total_bars])

    keys = sorted(SECTION_TEMPLATES.keys())
    best = keys[0]
    for k in keys:
        if k <= total_bars:
            best = k
    template = list(SECTION_TEMPLATES[best])
    deficit = total_bars - sum(length for _, length in template)

    if deficit > 0:
        idx = max(0, len(template) - 1)
        if deficit >= 8:
            template.insert(idx, ('chorus', 4))
            deficit -= 4
        if deficit >= 4:
            template.insert(idx, ('verse', deficit))
            deficit = 0
        if deficit > 0:
            for i in range(len(template) - 1, -1, -1):
                if template[i][0] in ('verse', 'chorus'):
                    template[i] = (template[i][0], template[i][1] + deficit)
                    deficit = 0
                    break
        if deficit > 0:
            template[-1] = (template[-1][0], template[-1][1] + deficit)
    elif deficit < 0:
        for i in range(len(template) - 1, -1, -1):
            if template[i][0] in ('verse', 'chorus'):
                new_len = template[i][1] + deficit
                if new_len >= 2:
                    template[i] = (template[i][0], new_len)
                    deficit = 0
                    break
        if deficit < 0:
            template[-1] = (template[-1][0], max(1, template[-1][1] + deficit))

    return template


def _seconds_to_bars(seconds: float, bpm: int, beats_per_bar: int = 4) -> int:
    """Convert a duration in seconds to a bar count (minimum 1)."""
    seconds_per_bar = (beats_per_bar * 60.0) / bpm
    return max(1, math.ceil(seconds / seconds_per_bar))


def _build_template_from_durations(
    section_durations: Dict[str, float],
    section_order: List[str],
    bpm: int,
    beats_per_bar: int = 4,
) -> list:
    """
    Build a section template from user-specified durations (in seconds).
    Sections with 0 seconds are skipped.
    Returns list of (section_name, bar_count) in execution order.
    """
    template: list = []
    for name in section_order:
        secs = section_durations.get(name, 0.0)
        if secs <= 0:
            continue
        bars = _seconds_to_bars(secs, bpm, beats_per_bar)
        template.append((name, bars))
    return template


class Conductor:
    """
    The Conductor is responsible for high-level musical planning.
    It creates the overall song structure, key, chord progression,
    **and** maps out sections with energy curves.
    """

    def __init__(self):
        self.available_moods = list(MOOD_CONFIGS.keys())

    def create_song_context(
        self,
        mood: str,
        length_in_bars: int = 16,
        bpm: Optional[int] = None,
        key: Optional[str] = None,
        section_durations: Optional[Dict[str, float]] = None,
        section_order: Optional[List[str]] = None,
    ) -> SongContext:
        """
        Create the full song context.

        If *section_durations* is provided (seconds per section name),
        the section template is built from those durations and total bars
        is derived from them.  Otherwise the old bar-count + template
        system is used.
        """
        if mood not in MOOD_CONFIGS:
            print(f"Unknown mood '{mood}', defaulting to 'happy'")
            mood = 'happy'

        config = MOOD_CONFIGS[mood]

        if bpm is None:
            bpm_min, bpm_max = config['bpm_range']
            bpm = random.randint(bpm_min, bpm_max)

        if key is None:
            key = random.choice(config['key_options'])

        root_name, key_root_midi, scale_type = parse_key(key)
        mood_scale = config.get('scale_type', scale_type)
        progression = random.choice(config['chord_progressions'])
        is_minor_key = key.endswith('m') or mood_scale in ['minor', 'dorian']

        beats_per_bar = 4  # 4/4 time

        # ---------- Build section template ----------
        if section_durations:
            order = section_order or DEFAULT_SECTION_ORDER
            section_template = _build_template_from_durations(
                section_durations, order, bpm, beats_per_bar
            )
            if not section_template:
                # All durations zero — fallback
                section_template = _pick_template(length_in_bars)
            # Derive total bars from the template
            length_in_bars = sum(b for _, b in section_template)
        else:
            section_template = _pick_template(length_in_bars)

        section_map = self._build_section_map(section_template)

        # ---------- Build bar timeline (section-aware) ----------
        timeline = self._build_timeline(
            progression=progression,
            key_root_midi=key_root_midi,
            is_minor_key=is_minor_key,
            scale_type=mood_scale,
            total_bars=length_in_bars,
            section_map=section_map,
        )

        ctx = SongContext(
            mood=mood,
            bpm=bpm,
            key=key,
            key_root_midi=key_root_midi,
            scale_type=mood_scale,
            time_signature=(beats_per_bar, 4),
            total_bars=length_in_bars,
            timeline=timeline,
            instruments=config['instruments'],
            drum_style=config['drum_style'],
            harmony_style=config['harmony_style'],
            section_map=section_map,
        )

        section_names = " | ".join(
            f"{s['name']}({s['length']})" for s in section_map
        )
        print(f"Conductor created: {ctx}")
        print(f"  Progression: {' -> '.join([bar.chord_name for bar in timeline[:4]])}")
        print(f"  Sections: {section_names}")

        return ctx

    # ----------------------------------------------------------------
    # Section helpers
    # ----------------------------------------------------------------
    @staticmethod
    def _build_section_map(template: list) -> list:
        """Convert a template list into a section_map with start offsets."""
        smap: list = []
        cursor = 0
        for name, length in template:
            smap.append({
                'name': name,
                'start': cursor,
                'length': length,
                'energy': SECTION_ENERGY.get(name, 0.5),
            })
            cursor += length
        return smap

    @staticmethod
    def _section_for_bar(bar_idx: int, section_map: list) -> tuple:
        """Return (section_name, section_bar_idx, energy, is_transition)."""
        for sec in section_map:
            sec_end = sec['start'] + sec['length']
            if sec['start'] <= bar_idx < sec_end:
                section_bar = bar_idx - sec['start']
                is_last = (section_bar == sec['length'] - 1)
                is_transition = is_last and sec_end < (section_map[-1]['start'] + section_map[-1]['length'])
                base = sec['energy']
                if sec['name'] == 'intro':
                    frac = (section_bar + 1) / sec['length']
                    energy = 0.1 + (base - 0.1) * frac
                elif sec['name'] == 'outro':
                    frac = 1.0 - (section_bar / max(1, sec['length']))
                    energy = base * frac
                elif is_transition:
                    energy = min(1.0, base + 0.15)
                else:
                    energy = base
                return sec['name'], section_bar, round(energy, 2), is_transition
        return 'verse', 0, 0.5, False

    # ----------------------------------------------------------------
    # Timeline builder
    # ----------------------------------------------------------------
    def _build_timeline(
        self,
        progression: list,
        key_root_midi: int,
        is_minor_key: bool,
        scale_type: str,
        total_bars: int,
        section_map: list,
    ) -> list:
        timeline: List[BarContext] = []

        prev_chord_name = ""
        prev_root = 0
        prev_energy = 0.5

        for bar_idx in range(total_bars):
            section_name, section_bar, energy, is_trans = self._section_for_bar(
                bar_idx, section_map
            )

            if section_name in ('intro', 'outro') and section_bar == 0:
                roman = progression[0]
            else:
                chord_idx = section_bar % len(progression)
                roman = progression[chord_idx]

            chord_name, root_midi, chord_type = roman_to_chord(
                roman, key_root_midi, is_minor_key
            )
            root_name = NOTE_NAMES[root_midi % 12]
            scale_notes = list(get_scale_notes(root_midi, scale_type))

            bar = BarContext(
                bar_index=bar_idx,
                chord_name=chord_name,
                chord_type=chord_type,
                root_note=root_midi,
                root_name=root_name,
                scale_type=scale_type,
                scale_notes=scale_notes,
                section=section_name,
                section_bar=section_bar,
                energy=energy,
                is_transition=is_trans,
                prev_chord=prev_chord_name,
                prev_root=prev_root,
                prev_energy=prev_energy,
            )
            timeline.append(bar)

            # Pass context forward
            prev_chord_name = chord_name
            prev_root = root_midi
            prev_energy = energy

        return timeline

    def get_available_moods(self) -> list:
        return self.available_moods
