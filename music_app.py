import os
import csv
import random
import threading
import subprocess
from datetime import datetime
from collections import defaultdict

import tkinter as tk
from tkinter import ttk, messagebox

from mido import Message, MidiFile, MidiTrack, bpm2tempo, MetaMessage


# ----------------------- CONFIG -----------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CSV with mood, n1,d1,n2,d2,... columns
DATA_FILE = os.path.join(BASE_DIR, "melodies.csv")

# Path to fluidsynth.exe
FLUIDSYNTH_EXE = r"C:\tools\fluidsynth\bin\fluidsynth.exe"

# Path to SoundFont
SF2_FILE = os.path.join(BASE_DIR, "music_fonts", "FluidR3_GM.sf2")

OUTPUT_ROOT = os.path.join(BASE_DIR, "output")

# How many notes to generate (can differ from training length)
GEN_LENGTH = 32

MOODS = ["sad", "happy", "bright", "blues", "jazz", "rock"]

# Ticks per beat for MIDI timing
TICKS_PER_BEAT = 480

# Per-mood BPM (you can tweak these)
MOOD_TEMPO = {
    "sad":   70,
    "happy": 115,
    "bright": 120,
    "blues": 95,
    "jazz":  110,
    "rock":  140,
}


# ----------------- MARKOV MODEL LOGIC -----------------

def load_dataset(path):
    """
    Load melodies.csv and return list of (mood, pitches[], durations[]).

    Handles missing values gracefully.
    Only loads pairs where BOTH nX and dX are present and valid numbers.
    """
    samples = []
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            mood = row.get("mood")
            if mood is None:
                continue  # skip bad rows

            pitches = []
            durs = []

            i = 1
            while True:
                n_key = f"n{i}"
                d_key = f"d{i}"

                # Stop if either field is missing from the header
                if n_key not in row or d_key not in row:
                    break

                n_val = row[n_key]
                d_val = row[d_key]

                # Stop when blank or None values are found (end of row)
                if n_val is None or d_val is None:
                    break
                if n_val.strip() == "" or d_val.strip() == "":
                    break

                # Convert safely
                try:
                    pitch = int(float(n_val))   # works for "60" or "60.0"
                    dur   = float(d_val)
                except ValueError:
                    break  # invalid value, stop reading this row

                pitches.append(pitch)
                durs.append(dur)

                i += 1

            if len(pitches) > 1:
                samples.append((mood, pitches, durs))

    return samples


def build_markov_models(samples):
    """
    Build transition probabilities over (pitch, duration) states:

    transition_probs[mood][(p1,d1)][(p2,d2)] = probability
    """
    transition_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for mood, pitches, durs in samples:
        for i in range(len(pitches) - 1):
            cur_state = (pitches[i], durs[i])
            next_state = (pitches[i + 1], durs[i + 1])
            transition_counts[mood][cur_state][next_state] += 1

    transition_probs = {}
    for mood, cur_dict in transition_counts.items():
        transition_probs[mood] = {}
        for cur_state, next_dict in cur_dict.items():
            total = sum(next_dict.values())
            transition_probs[mood][cur_state] = {
                nxt: cnt / total for nxt, cnt in next_dict.items()
            }

    return transition_probs


def sample_next_state(prob_dict):
    """Sample (pitch, duration) according to probability distribution."""
    r = random.random()
    cum = 0.0
    items = list(prob_dict.items())
    for state, p in items:
        cum += p
        if r <= cum:
            return state
    return items[-1][0]


def generate_melody(mood, length, transition_probs):
    """
    Generate a sequence of (pitches, durations) for a given mood.

    Returns (pitches_list, durations_list).
    """
    if mood not in transition_probs:
        raise ValueError(f"No Markov model available for mood '{mood}'")

    mood_table = transition_probs[mood]
    if not mood_table:
        raise ValueError(f"Empty transition table for mood '{mood}'")

    # Start from a random state that has outgoing transitions
    current_state = random.choice(list(mood_table.keys()))
    pitches = [current_state[0]]
    durs = [current_state[1]]

    for _ in range(length - 1):
        if current_state not in mood_table or not mood_table[current_state]:
            current_state = random.choice(list(mood_table.keys()))
        next_state = sample_next_state(mood_table[current_state])
        pitches.append(next_state[0])
        durs.append(next_state[1])
        current_state = next_state

    return pitches, durs


def melody_to_midi(pitches, durations, mood, filename):
    """
    Write a monophonic piano melody with variable durations to a MIDI file.

    durations are in beats (0.25, 0.5, 1.0, 2.0, ...).
    Tempo depends on mood.
    """
    mid = MidiFile()
    mid.ticks_per_beat = TICKS_PER_BEAT
    track = MidiTrack()
    mid.tracks.append(track)

    bpm = MOOD_TEMPO.get(mood, 100)
    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0))
    track.append(Message("program_change", program=0, time=0))  # Piano

    velocity = 80

    for pitch, dur_beats in zip(pitches, durations):
        dur_ticks = max(1, int(dur_beats * TICKS_PER_BEAT))
        track.append(Message("note_on", note=pitch, velocity=velocity, time=0))
        track.append(Message("note_off", note=pitch, velocity=64, time=dur_ticks))

    mid.save(filename)


# --------------- FLUIDSYNTH CLI RENDER ----------------

def midi_to_wav_cli(midi_path: str, wav_path: str, sf2_path: str) -> None:
    """
    Convert MIDI -> WAV by calling fluidsynth.exe as a subprocess.
    Works with FluidSynth 2.5.x; options must precede soundfont and MIDI.
    """
    if not os.path.isfile(FLUIDSYNTH_EXE):
        raise FileNotFoundError(f"fluidsynth.exe not found at: {FLUIDSYNTH_EXE}")
    if not os.path.isfile(midi_path):
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")
    if not os.path.isfile(sf2_path):
        raise FileNotFoundError(f"SoundFont not found: {sf2_path}")

    cmd = [
        FLUIDSYNTH_EXE,
        "-ni",
        "-F", wav_path,
        "-r", "44100",
        sf2_path,
        midi_path,
    ]

    subprocess.run(cmd, check=True)


# ---------------------- UI CLASS ----------------------

class MusicApp(tk.Tk):
    def __init__(self, transition_probs):
        super().__init__()
        self.title("Mood-based Melody Generator")
        self.geometry("450x260")

        self.transition_probs = transition_probs
        self.last_wav = None

        # UI variables
        self.selected_mood = tk.StringVar(value=MOODS[0])
        self.status_text = tk.StringVar(value="Ready.")

        self._build_ui()

    def _build_ui(self):
        padding = {"padx": 10, "pady": 8}

        # Mood selector
        ttk.Label(self, text="Select mood / genre:").grid(row=0, column=0, sticky="w", **padding)

        mood_combo = ttk.Combobox(self, textvariable=self.selected_mood, values=MOODS, state="readonly")
        mood_combo.grid(row=0, column=1, sticky="ew", **padding)

        # Generate button
        self.btn_generate = ttk.Button(self, text="Generate & Render", command=self.on_generate_clicked)
        self.btn_generate.grid(row=1, column=0, columnspan=2, sticky="ew", **padding)

        # Play button
        self.btn_play = ttk.Button(self, text="Play Last", command=self.on_play_clicked, state="disabled")
        self.btn_play.grid(row=2, column=0, columnspan=2, sticky="ew", **padding)

        # Progress bar (buffering indicator)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew", **padding)

        # Status label
        ttk.Label(self, textvariable=self.status_text).grid(row=4, column=0, columnspan=2, sticky="w", **padding)

        # Make columns resize
        self.columnconfigure(1, weight=1)

    # --------- UI event handlers & background work ---------

    def on_generate_clicked(self):
        mood = self.selected_mood.get()
        self.status_text.set(f"Generating {mood} melody...")
        self.btn_generate.config(state="disabled")
        self.btn_play.config(state="disabled")
        self.progress.start(10)  # start buffering animation

        # Run heavy work in a separate thread
        thread = threading.Thread(target=self._generate_and_render, args=(mood,), daemon=True)
        thread.start()

    def _generate_and_render(self, mood):
        try:
            # 1. Generate melody (pitches + durations)
            pitches, durs = generate_melody(mood, GEN_LENGTH, self.transition_probs)

            # 2. Prepare folder and filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mood_dir = os.path.join(OUTPUT_ROOT, mood)
            os.makedirs(mood_dir, exist_ok=True)

            midi_path = os.path.join(mood_dir, f"generated_{mood}_{timestamp}.mid")
            wav_path = os.path.join(mood_dir, f"generated_{mood}_{timestamp}.wav")

            # 3. Save MIDI with durations and mood tempo
            melody_to_midi(pitches, durs, mood, midi_path)

            # 4. Render to WAV
            midi_to_wav_cli(midi_path, wav_path, SF2_FILE)

            # On success, update UI from main thread
            self.after(0, self._on_generation_success, mood, wav_path)
        except Exception as e:
            self.after(0, self._on_generation_error, str(e))

    def _on_generation_success(self, mood, wav_path):
        self.progress.stop()
        self.status_text.set(f"Done. Saved in folder: output/{mood}/")
        self.btn_generate.config(state="normal")
        self.btn_play.config(state="normal")
        self.last_wav = wav_path

    def _on_generation_error(self, message):
        self.progress.stop()
        self.status_text.set("Error during generation.")
        self.btn_generate.config(state="normal")
        self.btn_play.config(state="disabled")
        messagebox.showerror("Error", message)

    def on_play_clicked(self):
        if not self.last_wav or not os.path.isfile(self.last_wav):
            messagebox.showwarning("No file", "No audio file to play.")
            return
        # On Windows this opens with the default audio player
        try:
            os.startfile(self.last_wav)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open audio player:\n{e}")


# ------------------------- MAIN -----------------------

def main():
    # 1. Load dataset & build Markov models once
    if not os.path.isfile(DATA_FILE):
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    samples = load_dataset(DATA_FILE)
    transition_probs = build_markov_models(samples)

    # 2. Ensure output root exists
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    # 3. Start UI
    app = MusicApp(transition_probs)
    app.mainloop()


if __name__ == "__main__":
    main()
