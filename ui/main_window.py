"""
Main Tkinter window for the Symphony Generator UI.
Collects user intent and shows progress.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.orchestrator import Orchestrator
from utils.audio_engine import AudioEngine


class MainWindow:
    """
    Main application window for Symphony Generator.
    """
    
    def __init__(self, root):
        """
        Initialize the main window.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Symphony Generator - AI Music Composer")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Set minimum size
        self.root.minsize(500, 400)
        
        # Initialize components
        self.orchestrator = Orchestrator()
        self.audio_engine = AudioEngine()
        
        # Store generated files
        self.last_midi_path = None
        self.last_wav_path = None
        
        # Build UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface components."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🎵 Symphony Generator",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        subtitle = tk.Label(
            main_frame,
            text="AI-Powered Mood-Based Music Composer",
            font=("Helvetica", 10),
            fg="gray"
        )
        subtitle.pack(pady=(0, 20))
        
        # Controls Frame
        controls_frame = ttk.LabelFrame(main_frame, text="Generation Settings", padding=20)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        # Grid layout for controls
        controls_frame.columnconfigure(1, weight=1)
        
        # Mood Selection
        ttk.Label(controls_frame, text="Mood:", font=("Helvetica", 11)).grid(
            row=0, column=0, sticky="w", padx=5, pady=10
        )
        self.mood_var = tk.StringVar(value="happy")
        moods = self.orchestrator.get_available_moods()
        mood_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.mood_var,
            values=moods,
            state="readonly",
            width=20
        )
        mood_combo.grid(row=0, column=1, sticky="w", padx=5, pady=10)
        
        # Duration Slider
        ttk.Label(controls_frame, text="Duration (bars):", font=("Helvetica", 11)).grid(
            row=1, column=0, sticky="w", padx=5, pady=10
        )
        
        duration_frame = ttk.Frame(controls_frame)
        duration_frame.grid(row=1, column=1, sticky="w", padx=5, pady=10)
        
        self.duration_var = tk.IntVar(value=16)
        duration_slider = ttk.Scale(
            duration_frame,
            from_=8,
            to=64,
            variable=self.duration_var,
            orient="horizontal",
            length=200,
            command=lambda v: self.duration_label.config(text=f"{int(float(v))} bars")
        )
        duration_slider.pack(side="left")
        
        self.duration_label = ttk.Label(duration_frame, text="16 bars", width=10)
        self.duration_label.pack(side="left", padx=10)
        
        # BPM (optional override)
        ttk.Label(controls_frame, text="BPM (optional):", font=("Helvetica", 11)).grid(
            row=2, column=0, sticky="w", padx=5, pady=10
        )
        self.bpm_var = tk.StringVar(value="")
        bpm_entry = ttk.Entry(controls_frame, textvariable=self.bpm_var, width=10)
        bpm_entry.grid(row=2, column=1, sticky="w", padx=5, pady=10)
        ttk.Label(controls_frame, text="(leave empty for auto)", font=("Helvetica", 9), foreground="gray").grid(
            row=2, column=1, sticky="w", padx=80, pady=10
        )
        
        # Render Audio Checkbox
        self.render_audio_var = tk.BooleanVar(value=True)
        render_check = ttk.Checkbutton(
            controls_frame,
            text="Render to WAV (requires FluidSynth)",
            variable=self.render_audio_var
        )
        render_check.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=10)
        
        # Buttons Frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", padx=10, pady=20)
        
        # Generate Button
        self.generate_btn = ttk.Button(
            buttons_frame,
            text="🎼 Generate Music",
            command=self.on_generate_click,
            width=20
        )
        self.generate_btn.pack(side="left", padx=5)
        
        # Play MIDI Button
        self.play_midi_btn = ttk.Button(
            buttons_frame,
            text="▶️ Play MIDI",
            command=self.on_play_midi_click,
            state="disabled",
            width=15
        )
        self.play_midi_btn.pack(side="left", padx=5)
        
        # Play WAV Button
        self.play_wav_btn = ttk.Button(
            buttons_frame,
            text="🔊 Play WAV",
            command=self.on_play_wav_click,
            state="disabled",
            width=15
        )
        self.play_wav_btn.pack(side="left", padx=5)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            mode="indeterminate",
            length=400
        )
        self.progress_bar.pack(pady=10)
        
        # Status Label
        self.status_var = tk.StringVar(value="Ready to generate music!")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Helvetica", 10)
        )
        status_label.pack(pady=10)
        
        # Output Info
        self.output_frame = ttk.LabelFrame(main_frame, text="Output Files", padding=10)
        self.output_frame.pack(fill="x", padx=10, pady=10)
        
        self.midi_path_var = tk.StringVar(value="No file generated yet")
        ttk.Label(self.output_frame, text="MIDI:").grid(row=0, column=0, sticky="w")
        ttk.Label(self.output_frame, textvariable=self.midi_path_var, foreground="blue").grid(
            row=0, column=1, sticky="w", padx=10
        )
        
        self.wav_path_var = tk.StringVar(value="No file generated yet")
        ttk.Label(self.output_frame, text="WAV:").grid(row=1, column=0, sticky="w")
        ttk.Label(self.output_frame, textvariable=self.wav_path_var, foreground="blue").grid(
            row=1, column=1, sticky="w", padx=10
        )
    
    def on_generate_click(self):
        """Handle the generate music button click."""
        # Disable button during generation
        self.generate_btn.config(state="disabled")
        self.play_midi_btn.config(state="disabled")
        self.play_wav_btn.config(state="disabled")
        
        # Start progress animation
        self.progress_bar.start(10)
        self.status_var.set("Generating music... Please wait.")
        
        # Get parameters
        mood = self.mood_var.get()
        duration = self.duration_var.get()
        bpm_str = self.bpm_var.get().strip()
        bpm = int(bpm_str) if bpm_str.isdigit() else None
        render_audio = self.render_audio_var.get()
        
        # Run generation in background thread
        thread = threading.Thread(
            target=self._generate_thread,
            args=(mood, duration, bpm, render_audio)
        )
        thread.daemon = True
        thread.start()
    
    def _generate_thread(self, mood, duration, bpm, render_audio):
        """Background thread for music generation."""
        try:
            midi_path, wav_path, ctx = self.orchestrator.generate(
                mood=mood,
                length_in_bars=duration,
                bpm=bpm,
                render_audio=render_audio
            )
            
            # Update UI from main thread
            self.root.after(0, lambda: self._on_generation_complete(midi_path, wav_path, ctx))
            
        except Exception as e:
            self.root.after(0, lambda: self._on_generation_error(str(e)))
    
    def _on_generation_complete(self, midi_path, wav_path, ctx):
        """Called when generation completes successfully."""
        self.progress_bar.stop()
        self.progress_var.set(100)
        
        self.last_midi_path = midi_path
        self.last_wav_path = wav_path
        
        # Update status
        self.status_var.set(f"✅ Generated {ctx.mood} song in {ctx.key} at {ctx.bpm} BPM!")
        
        # Update file paths
        self.midi_path_var.set(os.path.basename(midi_path) if midi_path else "N/A")
        self.wav_path_var.set(os.path.basename(wav_path) if wav_path else "N/A (FluidSynth not available)")
        
        # Enable buttons
        self.generate_btn.config(state="normal")
        if midi_path:
            self.play_midi_btn.config(state="normal")
        if wav_path:
            self.play_wav_btn.config(state="normal")
    
    def _on_generation_error(self, error_msg):
        """Called when generation fails."""
        self.progress_bar.stop()
        self.status_var.set(f"❌ Error: {error_msg}")
        self.generate_btn.config(state="normal")
        messagebox.showerror("Generation Error", f"An error occurred:\n{error_msg}")
    
    def on_play_midi_click(self):
        """Play the generated MIDI file."""
        if self.last_midi_path:
            self.status_var.set("Playing MIDI...")
            threading.Thread(
                target=lambda: self.audio_engine.play_midi(self.last_midi_path),
                daemon=True
            ).start()
    
    def on_play_wav_click(self):
        """Play the generated WAV file."""
        if self.last_wav_path:
            self.status_var.set("Playing WAV...")
            threading.Thread(
                target=lambda: self.audio_engine.play_wav(self.last_wav_path),
                daemon=True
            ).start()
    
    def run(self):
        """Start the UI event loop."""
        self.root.mainloop()


def launch_ui():
    """Launch the main UI window."""
    root = tk.Tk()
    app = MainWindow(root)
    app.run()


if __name__ == "__main__":
    launch_ui()
