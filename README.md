# 🎵 Mood-Based Melody Generator

A genre-aware melody generation system that uses Markov chains to create music based on mood selection, featuring real-time MIDI synthesis and audio playback.

## ✨ Features

- **Markov-based melody generation** - Each mood builds its own transition table from a rhythm-aware dataset
- **Rhythm variation** - Durations vary between 0.25, 0.5, 1.0, 2.0 beats depending on genre
- **Guitar tones per genre** - Rock (distortion), Blues (clean), Jazz (jazz guitar), with soft tones for other moods
- **Mood-specific BPM** - Every genre has its own tempo setting
- **FluidSynth WAV rendering** - Generated MIDI rendered to WAV via FluidSynth CLI
- **GUI interface** - Simple Tkinter interface for mood selection, generation, and playback

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- FluidSynth
- SoundFont file (FluidR3_GM.sf2)

### Installation

1. **Install Python dependencies**

```bash
pip install mido
```

*Note: Tkinter is included with Python on Windows*

2. **Install FluidSynth**

Download FluidSynth for Windows from the [official releases](https://github.com/FluidSynth/fluidsynth/releases)

- Download the Windows x64 zip release (`fluidsynth-2.x.x-win64.zip`)
- Extract and create the folder structure:
  ```
  C:\tools\fluidsynth\
  ```
- Move extracted files so that `C:\tools\fluidsynth\bin\fluidsynth.exe` exists

3. **Download SoundFont**

Download `FluidR3_GM.sf2` from:
https://ftp.osuosl.org/pub/musescore/soundfont/FluidR3_GM/

Place it in your project:
```
your_project/music_fonts/FluidR3_GM.sf2
```

> **Note:** The `music_fonts/` directory is gitignored - you must manually place the `.sf2` file

4. **Create output folder**

Generated WAV and MIDI files will appear in:
```
your_project/output/
```

*This folder is also gitignored*

## 📁 Project Structure

```
project/
│
├── music_app.py            # Main Tkinter application
├── melodies.csv            # Training dataset (pitch + duration)
├── generate_dataset.py     # Optional dataset generator
│
├── music_fonts/            # (gitignored) Put FluidR3_GM.sf2 here
│   └── FluidR3_GM.sf2
│
├── output/                 # (gitignored) Generated WAV/MIDI files
│   ├── rock/
│   ├── jazz/
│   ├── blues/
│   └── ...
│
└── README.md
```

## 🎹 Dataset Format

The `melodies.csv` file uses the following format:

```csv
mood,n1,d1,n2,d2,n3,d3,...,n16,d16
```

**Example:**
```csv
sad,60,1.0,62,1.0,64,2.0,62,0.5,60,0.5,59,2.0
```

You may include any number of `(nX, dX)` pairs where `n` is the note and `d` is the duration.

## 🎮 Usage

Run the application:

```bash
python music_app.py
```

**GUI Workflow:**

1. Select mood (blues / jazz / rock / sad / happy / bright)
2. Click "Generate & Render"
3. Wait for buffering animation
4. Click "Play Last"
5. WAV file appears in `output/<mood>/generated_<mood>_<timestamp>.wav`

## ⚙️ Customization

### Change Instrument Patches

Edit `music_app.py`:

```python
GUITAR_PROGRAMS = {
    "blues": 27,   # Clean guitar
    "jazz": 26,    # Jazz guitar
    "rock": 30,    # Distortion guitar
}
```

### Change Tempos

Edit `music_app.py`:

```python
MOOD_TEMPO = {
    "sad": 70,
    "happy": 115,
    "bright": 120,
    "blues": 95,
    "jazz": 110,
    "rock": 140,
}
```

## 🔧 Troubleshooting

**Error: "fluidsynth.exe not found"**
- Verify that `C:\tools\fluidsynth\bin\fluidsynth.exe` exists

**Error: "Could not open SoundFont"**
- Check that `music_fonts/FluidR3_GM.sf2` is present

**Audio not playing**
- Try opening the generated WAV file manually with your system audio player

## 🛠️ Built With

- **Python** - Core language
- **Mido** - MIDI file manipulation
- **FluidSynth** - Audio synthesis
- **Tkinter** - GUI interface
- **Markov Chains** - Melody generation algorithm

## 📝 License

For educational and academic use. Modify freely for your project.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

*Built with ❤️ for music generation enthusiasts*