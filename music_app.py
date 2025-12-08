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

# CSV with columns: mood,n1,d1,n2,d2,... (nX=pitch, dX=duration in beats)
DATA_FILE = os.path.join(BASE_DIR, "dataset.csv")

# Path to fluidsynth.exe
FLUIDSYNTH_EXE = r"C:\tools\fluidsynth\bin\fluidsynth.exe"

# Path to SoundFont
SF2_FILE = os.path.join(BASE_DIR, "music_fonts", "FluidR3_GM.sf2")

OUTPUT_ROOT = os.path.join(BASE_DIR, "output")

# How many notes to generate per melody
GEN_LENGTH = 32

MOODS = ["sad", "happy", "bright", "blues", "jazz", "rock"]

# Ticks per beat for MIDI timing
TICKS_PER_BEAT = 480

# Per-mood BPM
MOOD_TEMPO = {
    "sad":   70,
    "happy": 115,
    "bright": 120,
    "blues": 95,
    "jazz":  110,
    "rock":  140,
}

# General MIDI program numbers (0-based) for distinct guitars
GUITAR_PROGRAMS = {
    "blues": 27,  # Electric Guitar (clean)
    "jazz":  26,  # Electric Guitar (jazz)
    "rock":  30,  # Distortion Guitar
}

# For non-rock moods, we randomly pick from these "non-rock" tones:
# 0: Acoustic Grand Piano
# 24: Nylon Guitar
# 25: Steel Guitar
# 26: Jazz Guitar
# 27: Clean Electric Guitar
# 31: Guitar Harmonics
OTHER_INSTRUMENT_CHOICES = [0, 24, 25, 26, 27, 31]


# ----------------- MARKOV MODEL LOGIC -----------------

def load_dataset(path):
    """
    Load melodies.csv and return list of (mood, pitches[], durations[]).

    Handles missing values gracefully.
    Expects columns like:
    mood,n1,d1,n2,d2, ... (any number of nX/dX pairs).
    """
    samples = []

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            mood = row.get("mood")
            if mood is None:
                continue

            pitches = []
            durs = []

            i = 1
            while True:
                n_key = f"n{i}"
                d_key = f"d{i}"

                # Stop if these keys don't exist in header
                if n_key not in row or d_key not in row:
                    break

                n_val = row[n_key]
                d_val = row[d_key]

                # Stop on empty or None (end of row content)
                if n_val is None or d_val is None:
                    break
                if str(n_val).strip() == "" or str(d_val).strip() == "":
                    break

                try:
                    pitch = int(float(n_val))   # e.g. "60" or "60.0"
                    dur   = float(d_val)
                except ValueError:
                    # Bad value; stop reading this row
                    break

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


def sample_from_distribution(prob_dict):
    """Sample a state according to probability distribution in prob_dict."""
    r = random.random()
    cum = 0.0
    items = list(prob_dict.items())
    for state, p in items:
        cum += p
        if r <= cum:
            return state
    return items[-1][0]


def combine_context_probabilities(mood_table, history, history_len, decay):
    """
    Combine transition probabilities from the last `history_len`
    states using exponential decay.

    mood_table: transition_probs[mood] -> state -> {next_state: p}
    history: list of states, last element is most recent
    history_len: how many past states to consider (N)
    decay: alpha in (0,1), e.g. 0.7

    Returns a normalized probability dict: {next_state: combined_prob}
    """
    combined = {}

    # Take up to history_len most recent states
    recent = history[-history_len:]
    # Iterate from most recent backwards
    for idx, state in enumerate(reversed(recent)):
        if state not in mood_table:
            continue
        # Exponential decay: w0=1, w1=decay, w2=decay^2, ...
        weight = decay ** idx if idx > 0 else 1.0
        for nxt, p in mood_table[state].items():
            combined[nxt] = combined.get(nxt, 0.0) + weight * p

    # Normalize
    total = sum(combined.values())
    if total <= 0:
        return {}

    for k in list(combined.keys()):
        combined[k] /= total

    return combined


def generate_melody(mood, length, transition_probs, history_len=3, decay=0.7):
    """
    Generate a sequence of (pitches, durations) for a given mood using
    cascading context (decaying weights over last N states).

    Returns (pitches_list, durations_list).
    """
    if mood not in transition_probs:
        raise ValueError(f"No Markov model available for mood '{mood}'")

    mood_table = transition_probs[mood]
    if not mood_table:
        raise ValueError(f"Empty transition table for mood '{mood}'")

    # Clamp parameters
    history_len = max(1, min(history_len, 10))
    decay = max(0.0, min(decay, 0.999))

    # Start from a random state that has outgoing transitions
    current_state = random.choice(list(mood_table.keys()))
    pitches = [current_state[0]]
    durs = [current_state[1]]

    history = [current_state]

    for _ in range(length - 1):
        # Combine probabilities from last N states
        combined_probs = combine_context_probabilities(
            mood_table, history, history_len, decay
        )

        if not combined_probs:
            # Fallback: random transition from current_state or random state
            if current_state in mood_table and mood_table[current_state]:
                combined_probs = mood_table[current_state]
            else:
                current_state = random.choice(list(mood_table.keys()))
                combined_probs = mood_table[current_state]

        next_state = sample_from_distribution(combined_probs)

        pitches.append(next_state[0])
        durs.append(next_state[1])
        history.append(next_state)
        current_state = next_state

    return pitches, durs


def choose_instrument_for_mood(mood: str) -> int:
    """
    Decide the MIDI program (instrument) for a given mood.

    - rock: heavy/distorted guitar
    - blues: clean electric guitar
    - jazz: jazz guitar
    - others: random "non-rock" tones (piano / gentler guitars etc.)
    """
    if mood in GUITAR_PROGRAMS:
        return GUITAR_PROGRAMS[mood]
    return random.choice(OTHER_INSTRUMENT_CHOICES)


def melody_to_midi(pitches, durations, mood, filename):
    """
    Write a monophonic melody with variable durations to a MIDI file.

    durations are in beats (0.25, 0.5, 1.0, 2.0, ...).
    Tempo depends on mood.
    Instrument depends on mood (guitar variants / piano / etc.).
    """
    mid = MidiFile()
    mid.ticks_per_beat = TICKS_PER_BEAT
    track = MidiTrack()
    mid.tracks.append(track)

    bpm = MOOD_TEMPO.get(mood, 100)
    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0))

    # Instrument selection per mood
    program = choose_instrument_for_mood(mood)
    track.append(Message("program_change", program=program, time=0))

    # Optional: set reverb send for some moods (GM CC 91)
    if mood == "blues":
        track.append(Message("control_change", control=91, value=80, time=0))
    elif mood == "jazz":
        track.append(Message("control_change", control=91, value=100, time=0))
    elif mood == "rock":
        track.append(Message("control_change", control=91, value=60, time=0))

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
        self.geometry("500x320")

        self.transition_probs = transition_probs
        self.last_wav = None

        # UI variables
        self.selected_mood = tk.StringVar(value=MOODS[0])
        self.status_text = tk.StringVar(value="Ready.")

        # Cascading Markov parameters
        self.history_len_var = tk.IntVar(value=3)     # N
        self.decay_var = tk.DoubleVar(value=0.7)      # alpha

        self._build_ui()

    def _build_ui(self):
        padding = {"padx": 10, "pady": 6}

        # Mood selector
        ttk.Label(self, text="Select mood / genre:").grid(
            row=0, column=0, sticky="w", **padding
        )
        mood_combo = ttk.Combobox(
            self,
            textvariable=self.selected_mood,
            values=MOODS,
            state="readonly"
        )
        mood_combo.grid(row=0, column=1, sticky="ew", **padding)

        # History length (N)
        ttk.Label(self, text="History length (N):").grid(
            row=1, column=0, sticky="w", **padding
        )
        history_spin = ttk.Spinbox(
            self,
            from_=1,
            to=5,
            textvariable=self.history_len_var,
            width=5
        )
        history_spin.grid(row=1, column=1, sticky="w", **padding)

        # Decay (alpha)
        ttk.Label(self, text="Decay factor (α):").grid(
            row=2, column=0, sticky="w", **padding
        )

        decay_frame = ttk.Frame(self)
        decay_frame.grid(row=2, column=1, sticky="ew", **padding)

        decay_scale = ttk.Scale(
            decay_frame,
            from_=0.5,
            to=0.95,
            orient="horizontal",
            variable=self.decay_var,
            command=lambda v: self._update_decay_label()
        )
        decay_scale.pack(side="left", fill="x", expand=True)

        self.decay_label = ttk.Label(decay_frame, text=f"{self.decay_var.get():.2f}")
        self.decay_label.pack(side="right", padx=4)

        # Generate button
        self.btn_generate = ttk.Button(
            self, text="Generate & Render", command=self.on_generate_clicked
        )
        self.btn_generate.grid(row=3, column=0, columnspan=2, sticky="ew", **padding)

        # Play button
        self.btn_play = ttk.Button(
            self, text="Play Last", command=self.on_play_clicked, state="disabled"
        )
        self.btn_play.grid(row=4, column=0, columnspan=2, sticky="ew", **padding)

        # Progress bar (buffering indicator)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.grid(row=5, column=0, columnspan=2, sticky="ew", **padding)

        # Status label
        ttk.Label(self, textvariable=self.status_text).grid(
            row=6, column=0, columnspan=2, sticky="w", **padding
        )

        # Make columns resize
        self.columnconfigure(1, weight=1)

    def _update_decay_label(self):
        self.decay_label.config(text=f"{self.decay_var.get():.2f}")

    # --------- UI event handlers & background work ---------

    def on_generate_clicked(self):
        mood = self.selected_mood.get()
        history_len = self.history_len_var.get()
        decay = self.decay_var.get()

        self.status_text.set(
            f"Generating {mood} melody (N={history_len}, α={decay:.2f})..."
        )
        self.btn_generate.config(state="disabled")
        self.btn_play.config(state="disabled")
        self.progress.start(10)  # start buffering animation

        # Run heavy work in a separate thread
        thread = threading.Thread(
            target=self._generate_and_render,
            args=(mood, history_len, decay),
            daemon=True
        )
        thread.start()

    def _generate_and_render(self, mood, history_len, decay):
        try:
            # 1. Generate melody (pitches + durations) with cascading context
            pitches, durs = generate_melody(
                mood, GEN_LENGTH, self.transition_probs,
                history_len=history_len,
                decay=decay
            )

            # 2. Prepare folder and filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mood_dir = os.path.join(OUTPUT_ROOT, mood)
            os.makedirs(mood_dir, exist_ok=True)

            midi_path = os.path.join(mood_dir, f"generated_{mood}_{timestamp}.mid")
            wav_path = os.path.join(mood_dir, f"generated_{mood}_{timestamp}.wav")

            # 3. Save MIDI with durations, tempo, and instrument
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
    if not samples:
        raise RuntimeError("No valid samples loaded from dataset. Check melodies.csv format.")

    transition_probs = build_markov_models(samples)

    # 2. Ensure output root exists
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    # 3. Start UI
    app = MusicApp(transition_probs)
    app.mainloop()


if __name__ == "__main__":
    main()
