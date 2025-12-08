# Mood-Based Melody Generator

A Markov Chain-based melody generator with FluidSynth rendering that creates music based on different moods and genres.

## Overview

This project generates melodies based on musical "moods" (genres) such as **rock**, **blues**, **jazz**, **sad**, **happy**, and **bright**. It uses a Markov Chain model trained on a CSV dataset of melodies and rhythms, with a Tkinter GUI for easy interaction.

### Key Capabilities

- Select a genre/mood
- Generate a melody using trained Markov models
- Convert to MIDI format
- Render to WAV using FluidSynth
- Play the result directly
- Save files organized by genre in `output/<genre>/`

## Features

### 1. Markov Melody Generation

Learns probabilities of note transitions per mood, supporting both pitch transitions and rhythmic durations. This produces realistic stylistic patterns characteristic of each genre.

### 2. Rhythm-Aware Dataset

The CSV dataset includes pitch and duration information:
- `nX` = pitch (MIDI number)
- `dX` = duration (beats)

Example format:

```csv
mood,n1,d1,n2,d2,n3,d3,n4,d4,...
rock,60,0.5,62,0.5,64,1.0,67,0.5,...
```

### 3. FluidSynth Audio Rendering

MIDI files are rendered to WAV using SoundFont technology. The default SoundFont is **FluidR3_GM.sf2**, and you can configure different instruments based on genre (clean guitar, jazz guitar, distorted guitar, piano, etc.).

### 4. Tkinter GUI

User-friendly interface featuring:
- Mood selector dropdown
- Generate & render button
- Playback controls
- Output file management
- Loading spinner during rendering

### 5. TAB-to-Dataset Converter

The `tab_to_dataset.py` script converts guitar TABs directly into dataset entries, making it easy to expand training data.

Features:
- Reads text-based guitar TABs
- Supports multiple tunings (standard, Eb, drop tunings, etc.)
- Converts fret positions to MIDI pitches
- Assigns configurable durations
- Splits notes into training chunks (default: 16 notes per row)
- Appends or overwrites `dataset.csv`

Usage:

```bash
python tab_to_dataset.py
```

The script will prompt whether to append or overwrite existing data.

## Dataset Format

All datasets follow this structure:

```csv
mood,n1,d1,n2,d2,...,n16,d16
```

### Format Parameters

| Parameter | Meaning | Example |
|-----------|---------|---------|
| `mood` | Genre tag | `rock`, `jazz` |
| `nX` | MIDI pitch number | `60` (Middle C) |
| `dX` | Duration in beats | `0.5`, `1.0` |
| 16 notes | Training chunk size | Configurable |

### TAB Converter Settings

Configure these in `tab_to_dataset.py`:

| Setting | Description | Default |
|---------|-------------|---------|
| `MOOD` | Mood label for generated samples | `"rock"` |
| `TUNING_NAME` | Guitar tuning preset | `"eb"` |
| `CHUNK_LEN` | Notes per dataset entry | `16` |
| `NOTE_DURATION` | Duration applied to each pitch | `0.5` beats |
| `DATASET_FILE` | Master dataset path | `dataset.csv` |

## Installation

### Requirements

- Python 3.9+
- `mido` library
- `tkinter` (usually included with Python)
- FluidSynth installed on your system
- A valid `.sf2` SoundFont file

### SoundFont Setup

1. Download **FluidR3 GM SoundFont** (`FluidR3_GM.sf2`) from a publicly available General MIDI SoundFont archive

2. Create a directory in the project folder:

```bash
mkdir music_fonts
```

3. Place the SoundFont file:

```
music_fonts/FluidR3_GM.sf2
```

4. Verify the config points to it correctly:

```python
SF2_FILE = os.path.join(BASE_DIR, "music_fonts", "FluidR3_GM.sf2")
```

## Running the Application

```bash
python music_app.py
```

## Quick Start: Adding Your First TAB

Here's how to quickly add a guitar TAB to the dataset:

### 1. Prepare Your TAB

Copy your guitar tablature in standard text format. Example:

```
e|------------------0------------0--------0----------------------------------|
B|--2-----2-----2---2--2---------2--------2------2---------------------------|
G|--2-----2-----2---2--2------2--2----2---2--2---2---------------------------|
D|--2-----2-----2---2--2------0--0----0---0--0---0---------------------------|
A|--------------0------0------0-------0------0---0---------------------------|
E|----------------------------2-------2------2---2---------------------------|
```

### 2. Edit the Converter Script

Open `tab_to_dataset.py` and modify the configuration section:

```python
# ---------------------------------------------------------------------
# CONFIG (EDIT THESE FOR EACH TAB YOU PROCESS)
# ---------------------------------------------------------------------

TAB_TEXT = r"""
e|------------------0------------0--------0----------------------------------|
B|--2-----2-----2---2--2---------2--------2------2---------------------------|
G|--2-----2-----2---2--2------2--2----2---2--2---2---------------------------|
D|--2-----2-----2---2--2------0--0----0---0--0---0---------------------------|
A|--------------0------0------0-------0------0---0---------------------------|
E|----------------------------2-------2------2---2---------------------------|
"""

MOOD = "sad"             # Change this: "rock", "blues", "jazz", "sad", "happy", "bright"
CHUNK_LEN = 16           # Notes per training example (default: 16)
NOTE_DURATION = 0.5      # Duration in beats (default: 0.5)
TUNING_NAME = "standard" # "standard" or "eb" (Eb tuning)

DATASET_FILE = "dataset.csv"
```

**Configuration Parameters:**
- `TAB_TEXT` - Paste your complete TAB here (between the triple quotes)
- `MOOD` - Genre label for this TAB
- `CHUNK_LEN` - How many notes per training row (16 recommended)
- `NOTE_DURATION` - Rhythm value assigned to each note (0.5 = eighth note)
- `TUNING_NAME` - Guitar tuning used in the TAB

### 3. Run the Converter

```bash
python tab_to_dataset.py
```

You'll be prompted:

```
[INFO] dataset.csv already exists.
Choose: [A]ppend or [O]verwrite?
```

- Type `A` to add to existing data
- Type `O` to start fresh (deletes old data)

### 4. Verify the Output

The script will report:

```
[DONE] Added 12 samples to dataset.csv.
```

Your TAB is now part of the training dataset!

## Contributing to the Dataset

The quality of generated melodies depends heavily on the training dataset. Contributions are highly encouraged!

### Ways to Contribute

#### 1. Add Guitar Solos or Riffs

Use `tab_to_dataset.py` to convert:
- Rock riffs
- Blues licks
- Jazz lines
- Metal or fusion patterns
- Original pop melodies

#### 2. Add Your Own Compositions

Any style is welcome, as long as it's your original work.

#### 3. Generate CSV Rows Manually

If you have MIDI files or sheet music, extract notes and durations and format them as:

```csv
mood,n1,d1,n2,d2,...,n16,d16
```

#### 4. Share High-Quality Samples

More data leads to better note transitions and more realistic melodies.

## Project Structure

```
.
├── music_app.py          # Main application
├── tab_to_dataset.py     # TAB converter script
├── dataset.csv           # Training data
├── music_fonts/          # SoundFont directory (not in git)
└── output/               # Generated audio files (not in git)
```

### Excluded from Version Control

The following directories are in `.gitignore`:

- `output/` - User-generated audio files
- `music_fonts/` - May contain copyright-restricted SoundFonts

Users must supply their own `.sf2` file.

## Technical Overview

This project combines:
- **Music theory** - Understanding of melodic structure and genre characteristics
- **Machine learning** - Markov Chain modeling for sequence generation
- **Audio synthesis** - FluidSynth for high-quality audio rendering
- **UI/UX** - Tkinter-based graphical interface
- **Data engineering** - CSV dataset creation and management

The TAB-to-dataset converter enables users to expand the dataset with their own musical contributions, continuously improving melody quality and stylistic realism.