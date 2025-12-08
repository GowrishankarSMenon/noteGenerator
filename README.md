# Mood-based Melody Generator

Small Tkinter app that generates monophonic melodies using a Markov model trained from `melodies.csv`, writes MIDI files and renders WAV via FluidSynth.

## Requirements
- Windows
- Python 3.8+
- pip packages: `mido`
- FluidSynth CLI (`fluidsynth.exe`) installed (set path in `music_app.py`)
- A General MIDI SoundFont at `music_fonts/FluidR3_GM.sf2`
- `melodies.csv` in project root (CSV with columns: mood, n1,d1,n2,d2,...)

## Quick start
1. Install dependencies:
```bash
pip install mido
```
2. Configure paths in `music_app.py` if needed:
- `FLUIDSYNTH_EXE` → path to `fluidsynth.exe`
- `SF2_FILE` → soundfont path (default `music_fonts/FluidR3_GM.sf2`)

3. Run the app:
```bash
python music_app.py
```

Generated MIDI/WAV files are stored under `output/<mood>/`.

## Git: ignore output and soundfont folders
Ensure `.gitignore` contains:
```
output/
music_fonts/
```
If those folders were already tracked, remove them from the index (keeps files locally) before committing (commands below).

## Notes
- Tempo per mood is defined in `music_app.py` (MOOD_TEMPO).
- MIDI timing uses 480 ticks per beat (TICKS_PER_BEAT).