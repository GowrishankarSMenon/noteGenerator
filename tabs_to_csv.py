"""
tab_to_dataset.py

Convert TAB text into dataset.csv (mood,n1,d1,... format).

Features:
- Auto-creates dataset.csv with header if it doesn't exist.
- If dataset.csv exists, user is asked whether to:
    1. APPEND new rows, or
    2. OVERWRITE the file completely.
- Supports tunings (standard, Eb, custom).
- Converts TAB to MIDI notes.
- Splits into fixed-length chunks for ML dataset.

Run:
    python tab_to_dataset.py
"""

import os
import re
from typing import List

# ---------------------------------------------------------------------
# CONFIG (EDIT THESE FOR EACH TAB YOU PROCESS)
# ---------------------------------------------------------------------

TAB_TEXT = r"""
your tab here
"""

MOOD = "your mood here"            # label in the dataset
CHUNK_LEN = 16           # notes per training example
NOTE_DURATION = 0.5      # uniform duration (beats)
TUNING_NAME = "your tuning here"       # "standard", "eb", or custom defined below

DATASET_FILE = "dataset.csv"

# Tunings: top-to-bottom order for TAB
TUNINGS_TOP_TO_BOTTOM = {
    "standard": [64, 59, 55, 50, 45, 40],  # E4,B3,G3,D3,A2,E2
    "eb":       [63, 58, 54, 49, 44, 39],  # Eb4,Bb3,Gb3,Db3,Ab2,Eb2
}

# ---------------------------------------------------------------------
# TAB PARSER CORE
# ---------------------------------------------------------------------

def parse_tab_block(block_lines: List[str], tuning_notes: List[int]) -> List[int]:
    """Parse 1 block (6 TAB lines) into MIDI pitches."""
    string_tabs = []

    for line in block_lines:
        if "|" not in line:
            continue
        after_bar = line.split("|", 1)[1]
        string_tabs.append(after_bar.rstrip())

    if not string_tabs:
        return []

    # Normalize TAB line lengths
    max_len = max(len(s) for s in string_tabs)
    strings = [s.ljust(max_len, "-") for s in string_tabs]

    events = []

    for string_index, line in enumerate(strings):
        open_midi = tuning_notes[string_index]
        x = 0
        while x < max_len:
            ch = line[x]

            if not ch.isdigit():
                x += 1
                continue

            # multi-digit fret
            fret_str = ch
            x2 = x + 1
            while x2 < max_len and line[x2].isdigit():
                fret_str += line[x2]
                x2 += 1

            try:
                fret = int(fret_str)
            except:
                x = x2
                continue

            midi = open_midi + fret
            events.append((x, midi))

            x = x2

    events.sort(key=lambda em: (em[0], em[1]))
    return [m for _, m in events]


def parse_tab_text(tab_text: str, tuning_notes: List[int]) -> List[int]:
    """Convert entire TAB into a flat sequence of MIDI notes."""
    all_pitches = []
    current_block = []

    lines = tab_text.splitlines()

    for line in lines + [""]:
        is_tab_line = ("|" in line and "-" in line)

        if is_tab_line:
            current_block.append(line)
        else:
            if current_block:
                block = current_block[:len(tuning_notes)]
                pitches = parse_tab_block(block, tuning_notes)
                all_pitches.extend(pitches)
                current_block = []

    return all_pitches


def pitches_to_rows(mood: str, pitches: List[int], duration: float, chunk_len: int) -> List[str]:
    """Chunk into CSV rows."""
    rows = []
    for i in range(0, len(pitches), chunk_len):
        chunk = pitches[i:i + chunk_len]
        if len(chunk) < chunk_len:
            break

        row = [mood]
        for p in chunk:
            row.append(str(p))
            row.append(str(duration))

        rows.append(",".join(row))

    return rows


def make_header(chunk_len: int) -> str:
    cols = ["mood"]
    for i in range(1, chunk_len + 1):
        cols.append(f"n{i}")
        cols.append(f"d{i}")
    return ",".join(cols)


# ---------------------------------------------------------------------
# DATASET FILE LOGIC
# ---------------------------------------------------------------------

def ensure_dataset_file(path: str, chunk_len: int):
    """Create dataset.csv with header if missing, else ask user for append/overwrite."""
    if not os.path.exists(path):
        print(f"[INFO] {path} not found. Creating new dataset with header.")
        with open(path, "w", encoding="utf-8") as f:
            f.write(make_header(chunk_len) + "\n")
        return "append"

    # If exists → ask user
    while True:
        print(f"[INFO] {path} already exists.")
        choice = input("Choose: [A]ppend or [O]verwrite? ").strip().lower()
        if choice == "a":
            return "append"
        if choice == "o":
            with open(path, "w", encoding="utf-8") as f:
                f.write(make_header(chunk_len) + "\n")
            return "append"
        print("Invalid choice. Type A or O.")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    if TUNING_NAME not in TUNINGS_TOP_TO_BOTTOM:
        raise ValueError(f"Unknown tuning '{TUNING_NAME}'")

    tuning_notes = TUNINGS_TOP_TO_BOTTOM[TUNING_NAME]

    mode = ensure_dataset_file(DATASET_FILE, CHUNK_LEN)

    pitches = parse_tab_text(TAB_TEXT, tuning_notes)
    if not pitches:
        print("No notes found in TAB.")
        return

    rows = pitches_to_rows(MOOD, pitches, NOTE_DURATION, CHUNK_LEN)

    with open(DATASET_FILE, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(r + "\n")

    print(f"[DONE] Added {len(rows)} samples to {DATASET_FILE}.")


if __name__ == "__main__":
    main()
