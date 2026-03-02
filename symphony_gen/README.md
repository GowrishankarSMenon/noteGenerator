# 🎵 Symphony Generator

## AI-Powered Mood-Based Music Composer

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FluidSynth](https://img.shields.io/badge/FluidSynth-2.0+-orange.svg)](https://www.fluidsynth.org/)

Symphony Generator is an intelligent music composition system that creates complete, multi-track musical arrangements based on user-selected moods. Using a **Sequential Hierarchical Architecture**, it generates cohesive songs with Drums, Bass, Harmony, and Lead Melody tracks that work together harmonically and rhythmically.

---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Data Flow](#-data-flow)
- [How It Works](#-how-it-works)
- [Installation](#-installation)
- [Usage](#-usage)
- [Output](#-output)
- [Configuration](#-configuration)
- [Technical Details](#-technical-details)
- [References](#-references)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### Core
- **6 Mood Presets**: Happy, Sad, Rock, Jazz, Electronic, Calm
- **Multi-Track Generation**: Drums, Bass, Harmony, Lead Melody
- **Sequential Hierarchical Architecture**: Each instrument "listens" to previous instruments
- **Markov Chain Melody**: AI-powered lead melody generation with per-mood datasets
- **Scale-Aware Composition**: Notes automatically snap to valid scales
- **MIDI & WAV Output**: Export to standard formats
- **GUI & CLI Modes**: Flexible user interfaces
- **Customizable Duration**: 8 to 64 bars
- **Humanized Output**: Velocity variations and rhythmic nuances

### Style System
- **30+ Named Drum Patterns**: Legendary drummer-inspired patterns (Bonham, Peart, Grohl, Moon, etc.)
- **36 Lead Melody Styles**: Guitarist/artist-inspired styles with unique parameters (Gilmour, Page, Slash, Hendrix, etc.)
- **25+ Transposable Riff Patterns**: Iconic rock, blues, and arpeggio patterns mapped to lead styles
- **20 Quick Presets**: One-click style combos (Classic Rock, Pink Floyd, Metal Thunder, Jazz Club, etc.)
- **3 Selection Modes**: Auto (mood-based), Random, or Manual pick for both drums and lead

### Audio Effects
- **5 Real-Time DSP Effects**: Reverb, Delay, Distortion, Phaser, Chorus — applied per-section
- **7 Effects Presets**: Gilmour Atmospheric, Van Halen Crunch, Space Rock, Clean Jazz, and more
- **Per-Section Control**: Independent effect levels (0–100) for Drums, Bass, Harmony, and Lead

### UI
- **6-Tab Interface**: Generate, Style Selection, Note Properties, Effects, Section View, Recent Tracks
- **Embedded Music Player**: Play/Pause, Stop, Seek, Skip ±5s, Loop, Volume, Prev/Next track
- **Auto-Play Toggle**: Optional auto-playback after generation
- **Section Properties Editor**: Per-track Volume, Attack, Sustain sliders
- **Recent Tracks Browser**: Browse and replay previously generated output

---

## 🏗 System Architecture

The Symphony Generator follows a **Sequential Hierarchical Architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                         (main.py / ui/main_window.py)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR                                    │
│                         (core/orchestrator.py)                              │
│                    Manages the sequential generation pipeline                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐
│      CONDUCTOR       │  │    GENERATORS    │  │       RENDERERS          │
│  (core/conductor.py) │  │ (core/generators)│  │ (utils/midi_renderer.py) │
│                      │  │                  │  │ (utils/audio_engine.py)  │
│  Plans song structure│  │  Create notes    │  │  Output files            │
└──────────────────────┘  └──────────────────┘  └──────────────────────────┘
          │                        │
          ▼                        ▼
┌──────────────────────┐  ┌──────────────────────────────────────────────────┐
│    SONG CONTEXT      │  │              GENERATOR CASCADE                   │
│   (models/context)   │  │                                                  │
│                      │  │  ┌─────────┐   ┌──────┐   ┌─────────┐   ┌──────┐│
│  • Key, Scale, BPM   │  │  │  DRUMS  │──▶│ BASS │──▶│ HARMONY │──▶│ LEAD ││
│  • Chord Progression │  │  └─────────┘   └──────┘   └─────────┘   └──────┘│
│  • Timeline          │  │   Foundation    Locks to   Adds chords   Markov │
└──────────────────────┘  │                  kick      /pads         Melody │
                          └──────────────────────────────────────────────────┘
```

### Architecture Layers

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Interface** | `main.py`, `ui/main_window.py` | User interaction, input collection |
| **Orchestration** | `orchestrator.py` | Pipeline management, coordinates all generators |
| **Planning** | `conductor.py` | Song structure, key selection, chord progressions |
| **Generation** | `drums.py`, `bass.py`, `harmony.py`, `lead.py` | Create MIDI events for each instrument |
| **Models** | `context.py`, `markov_chain.py` | Data structures, AI melody engine |
| **Utilities** | `music_theory.py`, `midi_renderer.py`, `audio_engine.py`, `effects_processor.py` | Helper functions, DSP effects, file I/O |
| **Config** | `settings.py`, `drum_patterns.py`, `lead_styles.py`, `riff_patterns.py`, `style_config.py` | Constants, mood definitions, style presets, patterns |

---

## 📁 Project Structure

```
symphony_gen/
│
├── assets/                          # Static data files
│   ├── dataset.csv                  # Master training data for Markov chain
│   ├── datasets/                    # Per-mood training data
│   │   ├── happy.csv
│   │   ├── sad.csv
│   │   ├── rock.csv
│   │   ├── jazz.csv
│   │   ├── electronic.csv
│   │   └── calm.csv
│   └── fonts/
│       └── FluidR3_GM.sf2          # SoundFont file (not in git - download separately)
│
├── config/                          # Configuration & Constants
│   ├── __init__.py
│   ├── settings.py                  # Global constants, mood configs, instrument map
│   ├── drum_patterns.py             # 30+ named drum patterns & fills
│   ├── lead_styles.py               # 36 lead melody styles per mood
│   ├── riff_patterns.py             # Transposable riff & arpeggio library
│   └── style_config.py              # Style selection modes & 20 quick presets
│
├── core/                            # Intelligence Layer
│   ├── __init__.py
│   ├── conductor.py                 # PLANNER: Creates SongContext (Key, Chords)
│   ├── orchestrator.py              # MANAGER: Runs the sequential generation cascade
│   │
│   └── generators/                  # THE BAND: Instrument-specific generators
│       ├── __init__.py
│       ├── drums.py                 # Drum patterns, fills, style-aware generation
│       ├── bass.py                  # Bass lines locked to kick drum
│       ├── harmony.py               # Chords, pads, arpeggios
│       └── lead.py                  # Markov chain melody with style parameters
│
├── models/                          # Data Structures
│   ├── __init__.py
│   ├── context.py                   # SongContext & BarContext dataclasses
│   └── markov_chain.py              # Markov chain training & sampling
│
├── utils/                           # Utility Functions
│   ├── __init__.py
│   ├── music_theory.py              # Note/MIDI conversion, scales, chords
│   ├── midi_renderer.py             # MIDI file creation (Type 1 multi-track)
│   ├── audio_engine.py              # FluidSynth/pyfluidsynth WAV rendering
│   └── effects_processor.py         # DSP effects (reverb, delay, distortion, phaser, chorus)
│
├── ui/                              # User Interface
│   ├── __init__.py
│   └── main_window.py               # Tkinter GUI (6-tab + embedded music player)
│
├── output/                          # Generated files (auto-created)
│   └── *.mid, *.wav                 # Generated music files
│
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🔄 Data Flow

The Symphony Generator uses a **sequential, hierarchical data flow** where each component builds upon the previous:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW DIAGRAM                                   │
└──────────────────────────────────────────────────────────────────────────────┘

 USER INPUT                         PROCESSING                         OUTPUT
 ──────────                         ──────────                         ──────
     │
     │  mood="happy"
     │  bars=16
     │  bpm=None (auto)
     │
     ▼
┌─────────────────┐
│   CONDUCTOR     │──────────────────────────────────────────────────────┐
│                 │                                                       │
│  Input:         │         Creates:                                      │
│  - mood         │         ┌─────────────────────────────────────────┐  │
│  - bars         │         │           SONG CONTEXT                  │  │
│                 │         │  ┌─────────────────────────────────────┐│  │
│  Process:       │         │  │ mood: "happy"                       ││  │
│  - Select key   │         │  │ key: "G"                            ││  │
│  - Choose BPM   │         │  │ bpm: 125                            ││  │
│  - Pick chords  │────────▶│  │ scale_type: "major"                 ││  │
│  - Build        │         │  │ drum_style: "pop"                   ││  │
│    timeline     │         │  │ harmony_style: "rhythmic"           ││  │
│                 │         │  │ timeline: [Bar0, Bar1, ... Bar15]   ││  │
│                 │         │  └─────────────────────────────────────┘│  │
│                 │         └─────────────────────────────────────────┘  │
└─────────────────┘                          │                           │
                                             ▼                           │
                              ┌─────────────────────────────┐            │
                              │       DRUMS GENERATOR       │            │
                              │                             │            │
                              │  Input: SongContext         │            │
                              │  Output: drum_track[]       │            │
                              │                             │            │
                              │  • Reads drum_style         │            │
                              │  • Loops pattern per bar    │            │
                              │  • Adds fills every 4 bars  │            │
                              └─────────────────────────────┘            │
                                             │                           │
                                             │ drum_track                │
                                             ▼                           │
                              ┌─────────────────────────────┐            │
                              │       BASS GENERATOR        │            │
                              │                             │            │
                              │  Input: SongContext,        │            │
                              │         drum_track          │            │
                              │  Output: bass_track[]       │            │
                              │                             │            │
                              │  • Finds kick drum times    │◀───────────┘
                              │  • Gets chord root notes    │
                              │  • Places bass on kicks     │
                              │  • Adds passing tones       │
                              └─────────────────────────────┘
                                             │
                                             │ bass_track
                                             ▼
                              ┌─────────────────────────────┐
                              │      HARMONY GENERATOR      │
                              │                             │
                              │  Input: SongContext,        │
                              │         bass_track          │
                              │  Output: harmony_track[]    │
                              │                             │
                              │  • Reads chord progression  │
                              │  • Selects voicing style    │
                              │  • Creates chord events     │
                              └─────────────────────────────┘
                                             │
                                             │ harmony_track
                                             ▼
                              ┌─────────────────────────────┐
                              │       LEAD GENERATOR        │
                              │                             │
                              │  Input: SongContext,        │
                              │         harmony_track       │
                              │  Output: lead_track[]       │
                              │                             │
                              │  • Loads Markov model       │
                              │  • Generates melody         │
                              │  • Snaps to current scale   │
                              │  • Adds humanization        │
                              └─────────────────────────────┘
                                             │
                                             │ All 4 tracks
                                             ▼
                              ┌─────────────────────────────┐
                              │       MIDI RENDERER         │
                              │                             │
                              │  Input: All tracks, BPM     │
                              │  Output: .mid file          │
                              │                             │
                              │  • Creates Type 1 MIDI      │
                              │  • Adds tempo track         │
                              │  • Adds instrument tracks   │
                              │  • Converts to delta times  │
                              └─────────────────────────────┘
                                             │
                                             │ MIDI file path
                                             ▼
                              ┌─────────────────────────────┐
                              │       AUDIO ENGINE          │
                              │                             │
                              │  Input: .mid file           │
                              │  Output: .wav file          │     ┌─────────────┐
                              │                             │────▶│  OUTPUT     │
                              │  • Calls FluidSynth CLI     │     │             │
                              │  • Renders with SoundFont   │     │  .mid file  │
                              │  • Outputs 44.1kHz WAV      │     │  .wav file  │
                              └─────────────────────────────┘     └─────────────┘
```

### Key Data Structures

#### SongContext
```python
@dataclass
class SongContext:
    mood: str              # "happy", "sad", "rock", etc.
    bpm: int               # Tempo (60-180)
    key: str               # "C", "Am", "F#", etc.
    key_root_midi: int     # MIDI note of key root
    scale_type: str        # "major", "minor", "pentatonic_minor"
    total_bars: int        # Song length
    timeline: List[BarContext]  # Bar-by-bar chord info
    instruments: dict      # Instrument assignments
    drum_style: str        # "pop", "rock", "jazz", etc.
    harmony_style: str     # "sustained", "rhythmic", "arpeggiated"
```

#### BarContext
```python
@dataclass
class BarContext:
    bar_index: int         # Position in song (0-indexed)
    chord_name: str        # "Am", "G", "C7"
    chord_type: str        # "min", "maj", "dom7"
    root_note: int         # MIDI note of chord root
    scale_notes: List[int] # Valid notes for melody filtering
```

#### MIDI Event
```python
{
    'note': 60,        # MIDI note number (0-127)
    'start': 0,        # Start time in ticks
    'duration': 480,   # Duration in ticks
    'velocity': 80     # Volume (0-127)
}
```

---

## ⚙️ How It Works

### 1. Planning Phase (Conductor)

The Conductor receives the mood and creates a complete song plan:

```python
# Example: Mood = "happy"
# Conductor selects:
#   - Key: "G" (from ['C', 'G', 'D', 'F'])
#   - BPM: 125 (from range 110-140)
#   - Progression: ["I", "V", "vi", "IV"] -> ["G", "D", "Em", "C"]
#   - Scale: Major
#   - Drum Style: Pop
#   - Harmony Style: Rhythmic
```

### 2. Drums Generation

Creates the rhythmic foundation using pre-defined patterns:

```
Pattern (16th notes per bar):
Kick:   [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
Snare:  [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
Hi-Hat: [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
```

- Loops pattern for each bar
- Adds drum fills at end of 4-bar phrases
- Adds crash cymbals at section starts

### 3. Bass Generation

Creates bass lines that "lock" to the kick drum:

```
Input: Kick hits at ticks [0, 960, 1920, 2880, ...]
       Current chord: "G" (root = G2 = MIDI 43)

Output: Bass note G2 plays at each kick hit
        Adds approach notes before chord changes
```

### 4. Harmony Generation

Creates chordal accompaniment based on the harmony style:

| Style | Description | Example |
|-------|-------------|---------|
| **Sustained** | Long pad chords | Hold chord for entire bar |
| **Rhythmic** | Short stabs | Hit on beats 1, &, 3, & |
| **Arpeggiated** | Broken chords | Play notes sequentially |
| **Power** | Root + 5th only | Rock power chords |
| **Voicing** | Jazz extensions | 3rd, 7th, 9th voicings |

### 5. Lead Melody (Markov Chain)

The lead melody uses a **2nd-order Markov Chain** trained on melodic patterns:

```
Markov Chain Process:
1. Current state: (previous_note_1, previous_note_2)
2. Look up transition probabilities
3. Sample next note from distribution
4. Check if note is in current scale
5. If not, snap to nearest valid note
6. Add to melody and update state
```

**Scale Snapping Example:**
```
Generated note: F# (66)
Current chord: Am (scale: A B C D E F G)
F# not in scale!
Snap to nearest: F (65) or G (67)
Result: G (67)
```

---

## 📥 Installation

### Prerequisites

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **FluidSynth** (for audio rendering) - See below
- **FluidR3_GM.sf2** SoundFont file - See below

### Step 1: Clone the Repository

```bash
git clone https://github.com/GowrishankarSMenon/noteGenerator.git
cd noteGenerator
git checkout iteration6
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs: `mido`, `python-rtmidi`, `numpy`, `pandas`, `pyfluidsynth`, `pygame`, `matplotlib`

### Step 3: Install FluidSynth

FluidSynth is required for rendering MIDI to WAV audio files.

#### Windows
1. Download from [FluidSynth Releases](https://github.com/FluidSynth/fluidsynth/releases)
2. Extract to a folder (e.g., `C:\FluidSynth`)
3. Add to PATH:
   - Open System Properties → Advanced → Environment Variables
   - Add `C:\FluidSynth\bin` to PATH

**Alternative (using Chocolatey):**
```powershell
choco install fluidsynth
```

#### macOS
```bash
brew install fluid-synth
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install fluidsynth
```

#### Linux (Fedora)
```bash
sudo dnf install fluidsynth
```

### Step 4: Download SoundFont

The SoundFont file provides the instrument sounds for audio rendering.

1. **Download FluidR3_GM.sf2** (~141 MB):
   - [Direct Download (MuseScore)](https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2)
   - [Alternative: FluidR3_GM](https://member.keymusician.com/Member/FluidR3_GM/FluidR3_GM.zip)
   - [SoundFont Collection](https://musical-artifacts.com/artifacts?formats=sf2)

2. **Place the file in:**
   ```
   symphony_gen/assets/fonts/FluidR3_GM.sf2
   ```

### Verify Installation

```bash
# Check Python
python --version

# Check mido
python -c "import mido; print('mido OK')"

# Check FluidSynth
fluidsynth --version
```

---

## 🚀 Usage

### GUI Mode (Default)

```bash
cd symphony_gen
python main.py
```

![GUI Screenshot](docs/gui_screenshot.png)

1. **Select Mood** - Choose from dropdown (happy, sad, rock, jazz, electronic, calm)
2. **Set Duration** - Use slider (8-64 bars)
3. **Optional BPM** - Enter specific tempo or leave empty for auto
4. **Master Volume** - Adjust output volume (0–127)
5. **Render to WAV** - Check to create audio file (requires FluidSynth)
6. **Auto-play** - Optionally auto-play after generation
7. **Style Selection Tab** - Pick drum patterns, lead styles, or use Quick Presets
8. **Note Properties Tab** - Adjust per-section volume, attack, sustain
9. **Effects Tab** - Configure per-section reverb, delay, distortion, phaser, chorus
10. **Click "Generate Music"** - Wait for generation
11. **Play** - Use Play MIDI, Play WAV, or the embedded music player bar

### CLI Mode

```bash
python main.py --cli
```

```
--- CLI Mode ---

Available moods: happy, sad, rock, jazz, electronic, calm

Enter mood [happy]: rock
Enter duration in bars [16]: 32
Enter BPM (leave empty for auto): 120
Render to WAV? [y/n]: y

Generating...

==================================================
ORCHESTRATOR: Generating rock song (32 bars)
==================================================

[1/6] Conductor planning song structure...
[2/6] Generating drums...
[3/6] Generating bass...
[4/6] Generating harmony...
[5/6] Generating lead melody...
[6/6] Rendering MIDI file...

Done! Files saved to:
  MIDI: output/rock_E_118bpm_20260202_143052.mid
  WAV:  output/rock_E_118bpm_20260202_143052.wav
```

### Python API

```python
from core.orchestrator import Orchestrator

# Create orchestrator
orch = Orchestrator()

# Generate a song
midi_path, wav_path, context = orch.generate(
    mood="jazz",
    length_in_bars=24,
    bpm=110,
    render_audio=True
)

print(f"Generated: {context}")
print(f"Key: {context.key}, BPM: {context.bpm}")
print(f"Chords: {[bar.chord_name for bar in context.timeline[:4]]}")
```

---

## 📤 Output

### Generated Files

Files are saved to the `output/` directory with the naming pattern:
```
{mood}_{key}_{bpm}bpm_{timestamp}.mid
{mood}_{key}_{bpm}bpm_{timestamp}.wav
```

**Example:** `happy_G_125bpm_20260202_143052.mid`

### MIDI File Structure (Type 1)

The generated MIDI file contains:

| Track | Channel | Content |
|-------|---------|---------|
| 0 | - | Tempo & Time Signature (Conductor Track) |
| 1 | 10 | Drums (General MIDI Channel 10) |
| 2 | 1 | Bass |
| 3 | 2 | Harmony (Chords/Pads) |
| 4 | 3 | Lead Melody |

### Audio Specifications

- **Format:** WAV (PCM)
- **Sample Rate:** 44,100 Hz
- **Bit Depth:** 16-bit
- **Channels:** Stereo

---

## ⚙️ Configuration

### Mood Configurations

Edit `config/settings.py` to customize moods:

```python
MOOD_CONFIGS = {
    'happy': {
        'bpm_range': (110, 140),          # Tempo range
        'scale_type': 'major',             # Scale to use
        'key_options': ['C', 'G', 'D', 'F'],  # Possible keys
        'chord_progressions': [            # Possible progressions
            ['I', 'V', 'vi', 'IV'],
            ['I', 'IV', 'V', 'I'],
        ],
        'instruments': {                   # MIDI programs
            'bass': 'electric_bass',
            'harmony': 'piano',
            'lead': 'synth_lead',
        },
        'drum_style': 'pop',              # Drum pattern
        'harmony_style': 'rhythmic',       # Chord style
    },
    # ... more moods
}
```

### Adding Custom Drum Patterns

```python
DRUM_PATTERNS = {
    'my_pattern': {
        'kick':         [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare':        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'closed_hihat': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    },
}
```

### Training Data Format

The Markov chain is trained from `assets/dataset.csv`:

```csv
pitch,duration,melody_id
60,480,1
62,480,1
64,480,1
...
```

- **pitch:** MIDI note number (0-127)
- **duration:** Length in ticks (480 = quarter note)
- **melody_id:** Groups notes into separate melodies

---

## 🔧 Technical Details

### MIDI Timing

- **Ticks Per Beat:** 480 (configurable)
- **Ticks Per 16th Note:** 120
- **Ticks Per Bar (4/4):** 1920

### General MIDI Instruments Used

| Instrument | Program # | Usage |
|------------|-----------|-------|
| Acoustic Grand Piano | 0 | Harmony (sad, calm) |
| Electric Piano | 4 | Harmony (jazz) |
| Acoustic Guitar | 25 | Harmony (calm) |
| Distortion Guitar | 30 | Harmony/Lead (rock) |
| Acoustic Bass | 32 | Bass (sad, jazz, calm) |
| Electric Bass | 33 | Bass (happy, rock) |
| Synth Bass | 38 | Bass (electronic) |
| Strings | 48 | Harmony (sad) |
| Synth Lead | 80 | Lead (happy, electronic) |
| Synth Pad | 88 | Harmony (electronic) |
| Saxophone | 65 | Lead (jazz) |
| Flute | 73 | Lead (calm) |

### General MIDI Drum Map

| Drum | Note # |
|------|--------|
| Kick | 36 |
| Snare | 38 |
| Closed Hi-Hat | 42 |
| Open Hi-Hat | 46 |
| Crash Cymbal | 49 |
| Ride Cymbal | 51 |

---

## 📚 References

### Libraries & Tools

- **Mido** - MIDI Objects for Python
  - [Documentation](https://mido.readthedocs.io/)
  - [GitHub](https://github.com/mido/mido)
  - [PyPI](https://pypi.org/project/mido/)

- **FluidSynth** - Real-time Software Synthesizer
  - [Official Website](https://www.fluidsynth.org/)
  - [GitHub](https://github.com/FluidSynth/fluidsynth)
  - [Documentation](https://www.fluidsynth.org/api/)

- **Tkinter** - Python GUI Library
  - [Documentation](https://docs.python.org/3/library/tkinter.html)
  - [TkDocs Tutorial](https://tkdocs.com/tutorial/)

### SoundFont Resources

- [FluidR3_GM SoundFont](https://member.keymusician.com/Member/FluidR3_GM/)
- [MuseScore General SoundFont](https://musescore.org/en/handbook/3/soundfonts-and-sfz-files)
- [Musical Artifacts - SF2 Collection](https://musical-artifacts.com/artifacts?formats=sf2)

### Music Theory References

- [MIDI Specification](https://www.midi.org/specifications)
- [General MIDI Specification](https://www.midi.org/specifications-old/item/general-midi)
- [Music Theory for Musicians and Normal People](https://tobyrush.com/theorypages/)

### Markov Chains in Music

- [Markov Chains for Algorithmic Composition](https://www.jstor.org/stable/40285340)
- [Wikipedia: Markov Chain Music](https://en.wikipedia.org/wiki/Markov_chain#Music)

---

## ❓ Troubleshooting

### Common Issues

#### "FluidSynth not found"
```
Solution: Install FluidSynth and add to PATH
Windows: Download from GitHub releases, add bin folder to PATH
macOS: brew install fluid-synth
Linux: sudo apt install fluidsynth
```

#### "SoundFont not found"
```
Solution: Download FluidR3_GM.sf2 and place in assets/fonts/
The file is ~141MB and cannot be included in the repository.
```

#### "ModuleNotFoundError: No module named 'mido'"
```
Solution: Install mido
pip install mido
```

#### "MIDI file plays but no sound"
```
Solution: Your media player may not have a MIDI synthesizer.
- Use the "Render to WAV" option to create an audio file
- Or install a software MIDI synthesizer
```

#### GUI not appearing (Linux)
```
Solution: Install tkinter
Ubuntu/Debian: sudo apt install python3-tk
Fedora: sudo dnf install python3-tkinter
```

---

## 🆕 What's New in Iteration 6

### Style Selection System
Full control over the musical style of generated tracks. Choose from **30+ legendary drummer-inspired drum patterns** (Bonham, Peart, Grohl, Moon, Phil Rudd, and more) and **36 lead melody styles** (Gilmour, Page, Slash, Hendrix, Dimebag, BB King, etc.). Use **Auto** mode for mood-based defaults, **Random** for surprise, or **Manual** to hand-pick exact styles. **20 Quick Presets** offer one-click combos like "Pink Floyd", "Classic Rock", "Metal Thunder", "Jazz Club".

### Audio Effects Engine
A full DSP effects chain applied per-section during WAV rendering:
- **Reverb** — Multi-tap Schroeder-style with early reflections
- **Delay** — Stereo ping-pong echo
- **Distortion** — Tanh waveshaping with harmonic warmth
- **Phaser** — 4-stage cascaded allpass modulation
- **Chorus** — 3-voice detuned delay with stereo spread

Effects are independently adjustable (0–100) for each section (Drums, Bass, Harmony, Lead), with 7 built-in presets.

### Per-Mood Datasets
Separate Markov chain training data for each mood (happy, sad, rock, jazz, electronic, calm) enables mood-specific melodic characteristics.

### Riff & Arpeggio Library
25+ transposable interval-based riff patterns mapped to lead styles, including iconic rock riffs, blues licks, and arpeggio patterns.

### Enhanced UI
- **6-tab notebook**: Generate, Style Selection, Note Properties, Effects, Section View, Recent Tracks
- **Note Properties editor**: Per-section Volume, Attack, Sustain sliders
- **Effects panel**: Per-section effect sliders + preset buttons
- **Section View**: Post-generation analysis showing overview, individual track details, and timeline
- **Recent Tracks**: Browse and replay previously generated output files
- **Auto-play toggle**: Optional auto-playback after generation (off by default)

### Playback Fixes
- Fixed `mixer not initialized` errors when switching between MIDI and WAV playback
- Pygame mixer state is now properly checked and re-initialized as needed
- Player controls are safely guarded against uninitialized audio state

### Updated Dependencies
Added `numpy`, `pandas`, `pyfluidsynth`, `pygame`, `python-rtmidi`, `matplotlib` to requirements.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Gowrishankar S Menon**

- GitHub: [@GowrishankarSMenon](https://github.com/GowrishankarSMenon)

---

## 🙏 Acknowledgments

- FluidSynth developers for the amazing synthesizer
- Mido library for making MIDI easy in Python
- The music theory community for scale and chord references

---

<p align="center">
  Made with ❤️ and 🎵
</p>
