"""
Main Tkinter window for the Symphony Generator UI.
Collects user intent and shows progress with section properties viewer.
Includes embedded music player and per-section effects controls.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.orchestrator import Orchestrator
from utils.audio_engine import AudioEngine
from config.settings import OUTPUT_DIR, SAMPLE_RATE
from config.style_config import (
    STYLE_MODES, ALL_DRUM_STYLES, get_all_lead_style_names,
    STYLE_PRESETS, get_preset_names, apply_preset, format_style_name,
    get_all_lead_styles, STANDARD_DRUM_STYLES, ROCK_STYLE_NAMES
)
from utils.effects_processor import (
    EFFECTS_LIST, EFFECTS_PRESETS, get_effects_preset_names, format_preset_name
)


class MainWindow:
    """
    Main application window for Symphony Generator.
    Features tabbed interface with generation controls, section properties,
    music player, and audio effects.
    """

    def __init__(self, root):
        """Initialize the main window."""
        self.root = root
        self.root.title("Symphony Generator - AI Music Composer")
        self.root.geometry("850x750")
        self.root.resizable(True, True)
        self.root.minsize(750, 650)

        # Initialize components
        self.orchestrator = Orchestrator()
        self.audio_engine = AudioEngine()

        # Store generated files and context
        self.last_midi_path = None
        self.last_wav_path = None
        self.last_context = None

        # Playback state
        self._pygame_inited = False
        self._is_playing = False
        self._is_paused = False
        self._playback_length = 0  # total seconds
        self._playback_pos = 0.0   # current seconds
        self._tick_job = None
        self._current_track_path = None  # path currently loaded
        self._seeking = False  # True while user is dragging seek bar

        # Note properties (volume, attack, sustain)
        self.note_properties = {
            'drums':   {'volume': 110, 'attack': 10, 'sustain': 85},
            'bass':    {'volume': 100, 'attack': 15, 'sustain': 75},
            'harmony': {'volume': 90,  'attack': 25, 'sustain': 90},
            'lead':    {'volume': 105, 'attack': 10, 'sustain': 90}
        }

        self.volume_floors = {
            'drums': 70, 'bass': 65, 'harmony': 55, 'lead': 60
        }

        # Effects state (per section, each effect 0-100)
        self.effects_config = {
            'drums':   {fx: 0 for fx in EFFECTS_LIST},
            'bass':    {fx: 0 for fx in EFFECTS_LIST},
            'harmony': {fx: 0 for fx in EFFECTS_LIST},
            'lead':    {fx: 0 for fx in EFFECTS_LIST},
        }

        # Build UI
        self.setup_ui()

        # Load recent tracks on startup
        self.refresh_recent_tracks()

    # =====================================================================
    # UI SETUP
    # =====================================================================
    def setup_ui(self):
        """Setup the user interface with notebook tabs."""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            title_frame,
            text="🎵 Symphony Generator",
            font=("Helvetica", 22, "bold")
        ).pack()
        tk.Label(
            title_frame,
            text="AI-Powered Mood-Based Music Composer",
            font=("Helvetica", 10), fg="gray"
        ).pack()

        # Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)

        # Tab 1: Generate
        self.generate_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.generate_tab, text="🎼 Generate")
        self.setup_generate_tab()

        # Tab 2: Style Selection
        self.style_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.style_tab, text="🎨 Style Selection")
        self.setup_style_tab()

        # Tab 3: Note Properties
        self.properties_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.properties_tab, text="🎛️ Note Properties")
        self.setup_properties_tab()

        # Tab 4: Effects
        self.effects_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.effects_tab, text="🎸 Effects")
        self.setup_effects_tab()

        # Tab 5: Section View
        self.section_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.section_tab, text="📊 Section View")
        self.setup_section_tab()

        # Tab 6: Recent Tracks
        self.recent_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.recent_tab, text="📁 Recent Tracks")
        self.setup_recent_tab()

        # Status Bar (before player so player is bottom-most)
        self.setup_status_bar(main_frame)

        # Music Player bar (always visible at bottom)
        self.setup_player_bar(main_frame)

    # =====================================================================
    # GENERATE TAB
    # =====================================================================
    def setup_generate_tab(self):
        """Setup the main generation controls tab."""
        controls_frame = ttk.LabelFrame(self.generate_tab, text="Generation Settings", padding=15)
        controls_frame.pack(fill="x", pady=10)
        controls_frame.columnconfigure(1, weight=1)

        # Mood
        ttk.Label(controls_frame, text="Mood:", font=("Helvetica", 11)).grid(
            row=0, column=0, sticky="w", padx=5, pady=8)
        self.mood_var = tk.StringVar(value="happy")
        moods = self.orchestrator.get_available_moods()
        ttk.Combobox(controls_frame, textvariable=self.mood_var,
                     values=moods, state="readonly", width=20
                     ).grid(row=0, column=1, sticky="w", padx=5, pady=8)

        # Duration
        ttk.Label(controls_frame, text="Duration (bars):", font=("Helvetica", 11)).grid(
            row=1, column=0, sticky="w", padx=5, pady=8)
        dur_frame = ttk.Frame(controls_frame)
        dur_frame.grid(row=1, column=1, sticky="w", padx=5, pady=8)
        self.duration_var = tk.IntVar(value=16)
        ttk.Scale(dur_frame, from_=8, to=64, variable=self.duration_var,
                  orient="horizontal", length=200,
                  command=lambda v: self.duration_label.config(text=f"{int(float(v))} bars")
                  ).pack(side="left")
        self.duration_label = ttk.Label(dur_frame, text="16 bars", width=10)
        self.duration_label.pack(side="left", padx=10)

        # BPM
        ttk.Label(controls_frame, text="BPM (optional):", font=("Helvetica", 11)).grid(
            row=2, column=0, sticky="w", padx=5, pady=8)
        bpm_frame = ttk.Frame(controls_frame)
        bpm_frame.grid(row=2, column=1, sticky="w", padx=5, pady=8)
        self.bpm_var = tk.StringVar(value="")
        ttk.Entry(bpm_frame, textvariable=self.bpm_var, width=10).pack(side="left")
        ttk.Label(bpm_frame, text="(leave empty for auto)",
                  font=("Helvetica", 9), foreground="gray").pack(side="left", padx=10)

        # Master Volume
        ttk.Label(controls_frame, text="Master Volume:", font=("Helvetica", 11)).grid(
            row=3, column=0, sticky="w", padx=5, pady=8)
        vol_frame = ttk.Frame(controls_frame)
        vol_frame.grid(row=3, column=1, sticky="w", padx=5, pady=8)
        self.master_volume_var = tk.IntVar(value=100)
        ttk.Scale(vol_frame, from_=0, to=127, variable=self.master_volume_var,
                  orient="horizontal", length=200,
                  command=lambda v: self.volume_label.config(text=f"{int(float(v))}")
                  ).pack(side="left")
        self.volume_label = ttk.Label(vol_frame, text="100", width=5)
        self.volume_label.pack(side="left", padx=10)

        # Render WAV
        self.render_audio_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, text="Render to WAV (requires FluidSynth)",
                        variable=self.render_audio_var
                        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=8)

        # Auto-play after generation
        self.auto_play_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls_frame, text="Auto-play after generation",
                        variable=self.auto_play_var
                        ).grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # Buttons
        btn_frame = ttk.Frame(self.generate_tab)
        btn_frame.pack(fill="x", pady=15)

        self.generate_btn = ttk.Button(btn_frame, text="🎼 Generate Music",
                                       command=self.on_generate_click, width=20)
        self.generate_btn.pack(side="left", padx=5)

        self.play_wav_btn = ttk.Button(btn_frame, text="▶️ Play WAV",
                                       command=self.on_play_wav_click, width=14)
        self.play_wav_btn.pack(side="left", padx=5)

        self.play_midi_btn = ttk.Button(btn_frame, text="🎹 Play MIDI",
                                        command=self.on_play_midi_click, width=14)
        self.play_midi_btn.pack(side="left", padx=5)

        self.stop_playback_btn = ttk.Button(btn_frame, text="⏹ Stop",
                                            command=self._player_stop, width=8)
        self.stop_playback_btn.pack(side="left", padx=5)

        # Progress
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.generate_tab, variable=self.progress_var,
                                            mode="indeterminate", length=400)
        self.progress_bar.pack(pady=10)

        # Output info
        self.output_frame = ttk.LabelFrame(self.generate_tab, text="Output Files", padding=10)
        self.output_frame.pack(fill="x", pady=10)

        self.midi_path_var = tk.StringVar(value="No file generated yet")
        ttk.Label(self.output_frame, text="MIDI:").grid(row=0, column=0, sticky="w")
        ttk.Label(self.output_frame, textvariable=self.midi_path_var,
                  foreground="blue").grid(row=0, column=1, sticky="w", padx=10)

        self.wav_path_var = tk.StringVar(value="No file generated yet")
        ttk.Label(self.output_frame, text="WAV:").grid(row=1, column=0, sticky="w")
        ttk.Label(self.output_frame, textvariable=self.wav_path_var,
                  foreground="blue").grid(row=1, column=1, sticky="w", padx=10)

    # =====================================================================
    # STYLE SELECTION TAB
    # =====================================================================
    def setup_style_tab(self):
        canvas = tk.Canvas(self.style_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.style_tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(scroll_frame,
                  text="Choose how each track's style is selected during generation:",
                  font=("Helvetica", 11)).pack(pady=(0, 10), anchor="w", padx=5)
        ttk.Label(scroll_frame,
                  text="Auto = mood-based  |  Random = any style  |  Custom = you pick",
                  font=("Helvetica", 9), foreground="gray"
                  ).pack(pady=(0, 15), anchor="w", padx=5)

        self._setup_drum_style_section(scroll_frame)
        self._setup_lead_style_section(scroll_frame)
        self._setup_presets_section(scroll_frame)

        self.style_summary_var = tk.StringVar(value="Drums: Auto  |  Lead: Auto")
        summary_frame = ttk.LabelFrame(scroll_frame, text="Active Style Summary", padding=10)
        summary_frame.pack(fill="x", pady=10, padx=5)
        ttk.Label(summary_frame, textvariable=self.style_summary_var,
                  font=("Consolas", 10), foreground="green").pack(anchor="w")

    def _setup_drum_style_section(self, parent):
        drum_frame = ttk.LabelFrame(parent, text="🥁 Drum Style", padding=10)
        drum_frame.pack(fill="x", pady=5, padx=5)
        self.drum_mode_var = tk.StringVar(value="auto")
        mode_frame = ttk.Frame(drum_frame)
        mode_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(mode_frame, text="Mode:", font=("Helvetica", 10, "bold")).pack(side="left", padx=(0, 10))
        for val, lbl in [('auto', 'Auto (Mood-Based)'), ('random', 'Random'), ('selection', 'Custom Selection')]:
            ttk.Radiobutton(mode_frame, text=lbl, variable=self.drum_mode_var,
                            value=val, command=self._on_drum_mode_change).pack(side="left", padx=8)
        self.drum_custom_frame = ttk.Frame(drum_frame)
        self.drum_custom_frame.pack(fill="x", pady=5)
        ttk.Label(self.drum_custom_frame, text="Select Style:").pack(side="left", padx=(0, 10))
        drum_display = []
        self._drum_style_map = {}
        for s in STANDARD_DRUM_STYLES:
            d = f"[Standard] {format_style_name(s)}"
            drum_display.append(d); self._drum_style_map[d] = s
        for s in ROCK_STYLE_NAMES:
            d = f"[Rock] {format_style_name(s)}"
            drum_display.append(d); self._drum_style_map[d] = s
        self.drum_style_var = tk.StringVar(value=drum_display[0] if drum_display else "")
        self.drum_style_combo = ttk.Combobox(self.drum_custom_frame, textvariable=self.drum_style_var,
                                             values=drum_display, state="readonly", width=35)
        self.drum_style_combo.pack(side="left", padx=5)
        self.drum_style_combo.bind("<<ComboboxSelected>>", lambda e: self._update_style_summary())
        self.drum_custom_frame.pack_forget()

    def _setup_lead_style_section(self, parent):
        lead_frame = ttk.LabelFrame(parent, text="🎵 Lead Style", padding=10)
        lead_frame.pack(fill="x", pady=5, padx=5)
        self.lead_mode_var = tk.StringVar(value="auto")
        mode_frame = ttk.Frame(lead_frame)
        mode_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(mode_frame, text="Mode:", font=("Helvetica", 10, "bold")).pack(side="left", padx=(0, 10))
        for val, lbl in [('auto', 'Auto (Mood-Based)'), ('random', 'Random'), ('selection', 'Custom Selection')]:
            ttk.Radiobutton(mode_frame, text=lbl, variable=self.lead_mode_var,
                            value=val, command=self._on_lead_mode_change).pack(side="left", padx=8)
        self.lead_custom_frame = ttk.Frame(lead_frame)
        self.lead_custom_frame.pack(fill="x", pady=5)
        ttk.Label(self.lead_custom_frame, text="Select Style:").pack(side="left", padx=(0, 10))
        lead_display = []
        self._lead_style_map = {}
        for mood_name, style_names in get_all_lead_styles().items():
            for sn in style_names:
                d = f"[{mood_name.title()}] {format_style_name(sn)}"
                lead_display.append(d); self._lead_style_map[d] = sn
        self.lead_style_var = tk.StringVar(value=lead_display[0] if lead_display else "")
        self.lead_style_combo = ttk.Combobox(self.lead_custom_frame, textvariable=self.lead_style_var,
                                             values=lead_display, state="readonly", width=35)
        self.lead_style_combo.pack(side="left", padx=5)
        self.lead_style_combo.bind("<<ComboboxSelected>>", lambda e: self._update_style_summary())
        self.lead_custom_frame.pack_forget()

    def _setup_presets_section(self, parent):
        preset_frame = ttk.LabelFrame(parent, text="⚡ Quick Presets", padding=10)
        preset_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(preset_frame, text="Apply a curated drum + lead combination:",
                  font=("Helvetica", 9), foreground="gray").pack(anchor="w", pady=(0, 8))
        btn_frame = ttk.Frame(preset_frame)
        btn_frame.pack(fill="x")
        cols = 3
        for idx, name in enumerate(get_preset_names()):
            ttk.Button(btn_frame, text=name,
                       command=lambda n=name: self._apply_preset(n), width=18
                       ).grid(row=idx // cols, column=idx % cols, padx=4, pady=3, sticky="ew")
        for c in range(cols):
            btn_frame.columnconfigure(c, weight=1)

    def _on_drum_mode_change(self):
        mode = self.drum_mode_var.get()
        if mode == 'selection':
            self.drum_custom_frame.pack(fill="x", pady=5)
        else:
            self.drum_custom_frame.pack_forget()
        self._update_style_summary()

    def _on_lead_mode_change(self):
        mode = self.lead_mode_var.get()
        if mode == 'selection':
            self.lead_custom_frame.pack(fill="x", pady=5)
        else:
            self.lead_custom_frame.pack_forget()
        self._update_style_summary()

    def _apply_preset(self, preset_name):
        preset = apply_preset(preset_name)
        if not preset:
            return
        self.drum_mode_var.set('selection'); self._on_drum_mode_change()
        self.lead_mode_var.set('selection'); self._on_lead_mode_change()
        for display, raw in self._drum_style_map.items():
            if raw == preset.get('drums', ''):
                self.drum_style_var.set(display); break
        for display, raw in self._lead_style_map.items():
            if raw == preset.get('lead', ''):
                self.lead_style_var.set(display); break
        self._update_style_summary()
        desc = STYLE_PRESETS.get(preset_name, {}).get('description', '')
        self.status_var.set(f"⚡ Preset applied: {preset_name} - {desc}")

    def _update_style_summary(self):
        drum_mode = self.drum_mode_var.get()
        lead_mode = self.lead_mode_var.get()
        dt = drum_mode.title()
        if drum_mode == 'selection':
            dt = format_style_name(self._drum_style_map.get(self.drum_style_var.get(), 'Unknown'))
        lt = lead_mode.title()
        if lead_mode == 'selection':
            lt = format_style_name(self._lead_style_map.get(self.lead_style_var.get(), 'Unknown'))
        self.style_summary_var.set(f"Drums: {dt}  |  Lead: {lt}")

    def get_style_settings(self) -> dict:
        settings = {}
        dm = self.drum_mode_var.get()
        dc = {'mode': dm}
        if dm == 'selection':
            dc['style'] = self._drum_style_map.get(self.drum_style_var.get())
        settings['drums'] = dc
        lm = self.lead_mode_var.get()
        lc = {'mode': lm}
        if lm == 'selection':
            lc['style'] = self._lead_style_map.get(self.lead_style_var.get())
        settings['lead'] = lc
        return settings

    # =====================================================================
    # NOTE PROPERTIES TAB
    # =====================================================================
    def setup_properties_tab(self):
        ttk.Label(self.properties_tab,
                  text="Adjust note properties for each instrument section:",
                  font=("Helvetica", 11)).pack(pady=(0, 15))
        self.property_widgets = {}
        for key, name in [('drums', '🥁 Drums'), ('bass', '🎸 Bass'),
                          ('harmony', '🎹 Harmony'), ('lead', '🎵 Lead')]:
            self._create_section_properties(key, name)
        ttk.Button(self.properties_tab, text="✓ Apply Properties",
                   command=self.apply_note_properties, width=20).pack(pady=20)
        ttk.Button(self.properties_tab, text="↺ Reset to Defaults",
                   command=self.reset_note_properties, width=20).pack()

    def _create_section_properties(self, section_key, section_name):
        frame = ttk.LabelFrame(self.properties_tab, text=section_name, padding=10)
        frame.pack(fill="x", pady=5, padx=10)
        self.property_widgets[section_key] = {}
        for prop, (lo, hi, default, suffix) in {
            'volume':  (50, 127, self.note_properties[section_key]['volume'], ''),
            'attack':  (0, 127, self.note_properties[section_key]['attack'], ''),
            'sustain': (10, 100, self.note_properties[section_key]['sustain'], '%'),
        }.items():
            row = ttk.Frame(frame); row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"{prop.title()}:", width=10).pack(side="left")
            var = tk.IntVar(value=default)
            slider = ttk.Scale(row, from_=lo, to=hi, variable=var,
                               orient="horizontal", length=200)
            slider.pack(side="left", padx=5)
            lbl = ttk.Label(row, text=f"{default}{suffix}", width=5)
            lbl.pack(side="left")
            slider.configure(command=lambda v, l=lbl, s=suffix: l.config(text=f"{int(float(v))}{s}"))
            self.property_widgets[section_key][prop] = var

    def apply_note_properties(self):
        for sk in self.note_properties:
            for pk in self.note_properties[sk]:
                self.note_properties[sk][pk] = self.property_widgets[sk][pk].get()
        self.status_var.set("✓ Note properties applied!")
        messagebox.showinfo("Properties Applied", "Properties saved for next generation.")

    def reset_note_properties(self):
        defaults = {
            'drums':   {'volume': 110, 'attack': 10, 'sustain': 85},
            'bass':    {'volume': 100, 'attack': 15, 'sustain': 75},
            'harmony': {'volume': 90,  'attack': 25, 'sustain': 90},
            'lead':    {'volume': 105, 'attack': 10, 'sustain': 90}
        }
        for sk in defaults:
            for pk in defaults[sk]:
                self.property_widgets[sk][pk].set(defaults[sk][pk])
            self.note_properties[sk] = defaults[sk].copy()
        self.status_var.set("↺ Note properties reset to defaults")

    # =====================================================================
    # EFFECTS TAB
    # =====================================================================
    def setup_effects_tab(self):
        """Setup the per-section audio effects tab."""
        canvas = tk.Canvas(self.effects_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.effects_tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(scroll_frame,
                  text="Per-section audio effects (applied during WAV rendering):",
                  font=("Helvetica", 11)).pack(pady=(0, 5), anchor="w", padx=5)
        ttk.Label(scroll_frame,
                  text="Set each effect level 0-100 per section. 0 = off.",
                  font=("Helvetica", 9), foreground="gray"
                  ).pack(pady=(0, 10), anchor="w", padx=5)

        # Effects presets
        preset_frame = ttk.LabelFrame(scroll_frame, text="⚡ Effects Presets", padding=10)
        preset_frame.pack(fill="x", pady=(0, 10), padx=5)

        btn_grid = ttk.Frame(preset_frame)
        btn_grid.pack(fill="x")
        cols = 3
        for idx, pname in enumerate(get_effects_preset_names()):
            ttk.Button(btn_grid, text=format_preset_name(pname),
                       command=lambda n=pname: self._apply_effects_preset(n), width=20
                       ).grid(row=idx // cols, column=idx % cols, padx=4, pady=3, sticky="ew")
        for c in range(cols):
            btn_grid.columnconfigure(c, weight=1)

        # Per-section sliders
        self.effects_widgets = {}
        for section_key, section_name in [('drums', '🥁 Drums'), ('bass', '🎸 Bass'),
                                           ('harmony', '🎹 Harmony'), ('lead', '🎵 Lead')]:
            self._create_effects_section(scroll_frame, section_key, section_name)

        # Apply / Reset buttons
        btn_row = ttk.Frame(scroll_frame)
        btn_row.pack(fill="x", pady=15, padx=5)
        ttk.Button(btn_row, text="✓ Apply Effects",
                   command=self._apply_effects_values, width=18).pack(side="left", padx=5)
        ttk.Button(btn_row, text="↺ Reset All",
                   command=self._reset_effects, width=18).pack(side="left", padx=5)

    def _create_effects_section(self, parent, section_key, section_name):
        frame = ttk.LabelFrame(parent, text=section_name, padding=8)
        frame.pack(fill="x", pady=4, padx=5)
        self.effects_widgets[section_key] = {}
        for fx_name in EFFECTS_LIST:
            row = ttk.Frame(frame); row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{fx_name.title()}:", width=12).pack(side="left")
            var = tk.IntVar(value=self.effects_config[section_key].get(fx_name, 0))
            slider = ttk.Scale(row, from_=0, to=100, variable=var,
                               orient="horizontal", length=180)
            slider.pack(side="left", padx=5)
            lbl = ttk.Label(row, text="0", width=4)
            lbl.pack(side="left")
            slider.configure(command=lambda v, l=lbl: l.config(text=str(int(float(v)))))
            self.effects_widgets[section_key][fx_name] = var

    def _apply_effects_preset(self, preset_name):
        preset = EFFECTS_PRESETS.get(preset_name)
        if not preset:
            return
        for section_key in ['drums', 'bass', 'harmony', 'lead']:
            section_fx = preset.get(section_key, {})
            for fx_name in EFFECTS_LIST:
                val = section_fx.get(fx_name, 0)
                if section_key in self.effects_widgets and fx_name in self.effects_widgets[section_key]:
                    self.effects_widgets[section_key][fx_name].set(val)
        self._apply_effects_values()
        desc = preset.get('description', '')
        self.status_var.set(f"⚡ Effects preset: {format_preset_name(preset_name)} - {desc}")

    def _apply_effects_values(self):
        for sk in self.effects_config:
            for fx in EFFECTS_LIST:
                self.effects_config[sk][fx] = self.effects_widgets[sk][fx].get()
        self.status_var.set("✓ Effects settings applied!")

    def _reset_effects(self):
        for sk in self.effects_config:
            for fx in EFFECTS_LIST:
                self.effects_config[sk][fx] = 0
                self.effects_widgets[sk][fx].set(0)
        self.status_var.set("↺ Effects reset (all off)")

    def _collect_effects_config(self) -> dict:
        """Collect current effects slider values for the orchestrator."""
        cfg = {}
        for sk in self.effects_config:
            cfg[sk] = {}
            for fx in EFFECTS_LIST:
                cfg[sk][fx] = self.effects_widgets[sk][fx].get()
        return cfg

    # =====================================================================
    # SECTION VIEW TAB
    # =====================================================================
    def setup_section_tab(self):
        ttk.Label(self.section_tab,
                  text="View properties of each section in the generated track:",
                  font=("Helvetica", 11)).pack(pady=(0, 10))
        self.section_notebook = ttk.Notebook(self.section_tab)
        self.section_notebook.pack(fill="both", expand=True)
        self.section_frames = {}
        for section in ['Overview', 'Drums', 'Bass', 'Harmony', 'Lead', 'Timeline']:
            frame = ttk.Frame(self.section_notebook, padding=10)
            self.section_notebook.add(frame, text=section)
            self.section_frames[section] = frame
            tw = tk.Text(frame, wrap="word", height=15, font=("Consolas", 10))
            tw.pack(fill="both", expand=True, side="left")
            sb = ttk.Scrollbar(frame, orient="vertical", command=tw.yview)
            sb.pack(side="right", fill="y"); tw.configure(yscrollcommand=sb.set)
            setattr(self, f"section_text_{section.lower()}", tw)
            tw.insert("1.0", "Generate a track to see section details...")
            tw.config(state="disabled")

    def update_section_view(self, ctx, tracks_info):
        if not ctx:
            return
        # Overview
        tw = self.section_text_overview; tw.config(state="normal"); tw.delete("1.0", "end")
        tw.insert("end", f"{'═'*39}\n        SONG OVERVIEW\n{'═'*39}\n\n")
        tw.insert("end", f"  Mood:           {ctx.mood.upper()}\n  Key:            {ctx.key}\n")
        tw.insert("end", f"  Scale:          {ctx.scale_type}\n  BPM:            {ctx.bpm}\n")
        tw.insert("end", f"  Time Signature: {ctx.time_signature[0]}/{ctx.time_signature[1]}\n  Total Bars:     {ctx.total_bars}\n")
        tw.insert("end", f"  Drum Style:     {ctx.drum_style}\n  Harmony Style:  {ctx.harmony_style}\n")
        tw.insert("end", f"\n  INSTRUMENTS\n{'─'*39}\n")
        for instr, prog in ctx.instruments.items():
            tw.insert("end", f"  {instr:12s}  →  Program {prog}\n")
        tw.config(state="disabled")

        # Drums
        tw = self.section_text_drums; tw.config(state="normal"); tw.delete("1.0", "end")
        pn = getattr(self.orchestrator.drums_gen, 'current_pattern_name', ctx.drum_style)
        dm = self.drum_mode_var.get() if hasattr(self, 'drum_mode_var') else 'auto'
        tw.insert("end", f"🥁 DRUMS\n{'═'*39}\n\nStyle: {ctx.drum_style}\nPattern: {format_style_name(pn)}\nMode: {dm.title()}\n")
        tw.insert("end", f"Channel: 10  |  Volume: {self.note_properties['drums']['volume']}\n")
        if 'drums' in tracks_info: tw.insert("end", f"Notes: {tracks_info['drums']['count']}\n")
        tw.config(state="disabled")

        # Bass
        tw = self.section_text_bass; tw.config(state="normal"); tw.delete("1.0", "end")
        tw.insert("end", f"🎸 BASS\n{'═'*39}\n\nInstrument: {ctx.instruments.get('bass', 'Electric Bass')}\n")
        tw.insert("end", f"Technique: Locks to kick drum\nVolume: {self.note_properties['bass']['volume']}\n")
        if 'bass' in tracks_info: tw.insert("end", f"Notes: {tracks_info['bass']['count']}\n")
        tw.config(state="disabled")

        # Harmony
        tw = self.section_text_harmony; tw.config(state="normal"); tw.delete("1.0", "end")
        tw.insert("end", f"🎹 HARMONY\n{'═'*39}\n\nInstrument: {ctx.instruments.get('harmony', 'Piano')}\n")
        tw.insert("end", f"Style: {ctx.harmony_style}\nVolume: {self.note_properties['harmony']['volume']}\n")
        if 'harmony' in tracks_info: tw.insert("end", f"Notes: {tracks_info['harmony']['count']}\n")
        tw.config(state="disabled")

        # Lead
        tw = self.section_text_lead; tw.config(state="normal"); tw.delete("1.0", "end")
        ls_obj = getattr(self.orchestrator.lead_gen, '_current_style', None)
        ls_name = ls_obj.get('name', 'default') if ls_obj else 'default'
        ls_inst = ls_obj.get('instrument', 'clean_guitar') if ls_obj else 'Synth Lead'
        lm = self.lead_mode_var.get() if hasattr(self, 'lead_mode_var') else 'auto'
        tw.insert("end", f"🎵 LEAD\n{'═'*39}\n\nSub-Style: {format_style_name(ls_name)}\nMode: {lm.title()}\n")
        tw.insert("end", f"Instrument: {ls_inst}\nScale: {ctx.scale_type}\nVolume: {self.note_properties['lead']['volume']}\n")
        if 'lead' in tracks_info: tw.insert("end", f"Notes: {tracks_info['lead']['count']}\n")
        tw.config(state="disabled")

        # Timeline
        tw = self.section_text_timeline; tw.config(state="normal"); tw.delete("1.0", "end")
        tw.insert("end", f"📊 CHORD TIMELINE\n{'═'*39}\n\nBar  │ Chord    │ Scale\n{'─'*5}┼{'─'*10}┼{'─'*16}\n")
        for bar in ctx.timeline[:32]:
            tw.insert("end", f" {bar.bar_index+1:3d} │ {bar.chord_name:8s} │ {bar.scale_type}\n")
        if len(ctx.timeline) > 32:
            tw.insert("end", f"\n... and {len(ctx.timeline) - 32} more bars\n")
        tw.config(state="disabled")

    # =====================================================================
    # RECENT TRACKS TAB
    # =====================================================================
    def setup_recent_tab(self):
        header = ttk.Frame(self.recent_tab); header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="Recently Generated Tracks:",
                  font=("Helvetica", 11, "bold")).pack(side="left")
        ttk.Button(header, text="🔄 Refresh",
                   command=self.refresh_recent_tracks, width=10).pack(side="right")

        columns = ('filename', 'mood', 'key', 'bpm', 'date')
        self.recent_tree = ttk.Treeview(self.recent_tab, columns=columns, show='headings', height=12)
        for col, w in [('filename', 250), ('mood', 80), ('key', 60), ('bpm', 60), ('date', 120)]:
            self.recent_tree.heading(col, text=col.title())
            self.recent_tree.column(col, width=w)
        sb = ttk.Scrollbar(self.recent_tab, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=sb.set)
        self.recent_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        action_frame = ttk.Frame(self.recent_tab)
        action_frame.pack(fill="x", pady=10, side="bottom")
        ttk.Button(action_frame, text="▶️ Play Selected",
                   command=self.play_selected_track, width=15).pack(side="left", padx=5)
        ttk.Button(action_frame, text="📂 Open Output Folder",
                   command=self.open_output_folder, width=18).pack(side="left", padx=5)

    def refresh_recent_tracks(self):
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        if not os.path.exists(OUTPUT_DIR):
            return
        midi_files = []
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith('.mid'):
                fp = os.path.join(OUTPUT_DIR, f)
                midi_files.append((f, os.path.getmtime(fp), fp))
        midi_files.sort(key=lambda x: x[1], reverse=True)
        for fn, mtime, fp in midi_files[:50]:
            parts = fn.replace('.mid', '').split('_')
            mood = parts[0] if len(parts) >= 4 else '?'
            key = parts[1] if len(parts) >= 4 else '?'
            bpm = parts[2].replace('bpm', '') if len(parts) >= 4 else '?'
            date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            self.recent_tree.insert('', 'end', values=(fn, mood, key, bpm, date_str), tags=(fp,))

    def play_selected_track(self):
        sel = self.recent_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a track to play.")
            return
        fn = self.recent_tree.item(sel[0])['values'][0]
        wav_path = os.path.join(OUTPUT_DIR, fn.replace('.mid', '.wav'))
        mid_path = os.path.join(OUTPUT_DIR, fn)
        if os.path.exists(wav_path):
            self._player_load_and_play(wav_path)
        elif os.path.exists(mid_path):
            self.status_var.set(f"Playing MIDI: {fn}")
            threading.Thread(target=lambda: self.audio_engine.play_midi(mid_path), daemon=True).start()

    def open_output_folder(self):
        if os.path.exists(OUTPUT_DIR):
            os.startfile(OUTPUT_DIR)

    # =====================================================================
    # MUSIC PLAYER BAR (always visible at bottom)
    # =====================================================================
    def setup_player_bar(self, parent):
        """Create a prominent music-player control bar at the bottom of the window."""
        # ── Outer container with visible border ──
        player_frame = tk.LabelFrame(
            parent, text="  🎧  MUSIC PLAYER  ",
            font=("Helvetica", 11, "bold"), padx=10, pady=8,
            relief="groove", bd=2
        )
        player_frame.pack(fill="x", side="bottom", pady=(8, 0))

        # ── Row 1: Now Playing + song navigation ──
        info_row = tk.Frame(player_frame)
        info_row.pack(fill="x", pady=(0, 4))

        tk.Label(info_row, text="Now Playing:",
                 font=("Helvetica", 9, "bold"), fg="#555").pack(side="left")
        self.player_track_var = tk.StringVar(value="No track loaded")
        tk.Label(info_row, textvariable=self.player_track_var,
                 font=("Helvetica", 10, "italic"), fg="#1a73e8",
                 anchor="w", width=45).pack(side="left", padx=(6, 0))

        # Loop toggle
        self._loop_var = tk.BooleanVar(value=False)
        self.btn_loop = tk.Checkbutton(
            info_row, text="🔁 Loop", variable=self._loop_var,
            font=("Helvetica", 9), relief="flat",
            command=self._on_loop_toggle
        )
        self.btn_loop.pack(side="right", padx=4)

        # ── Row 2: Main transport controls ──
        ctrl_row = tk.Frame(player_frame)
        ctrl_row.pack(fill="x", pady=(2, 4))

        btn_style = {"font": ("Helvetica", 12), "width": 4, "relief": "raised", "bd": 1}
        wide_btn  = {"font": ("Helvetica", 11), "width": 7, "relief": "raised", "bd": 1}

        # Prev song
        self.btn_prev_song = tk.Button(
            ctrl_row, text="⏮", command=self._player_prev_song, **btn_style)
        self.btn_prev_song.pack(side="left", padx=2)

        # Skip back 5s
        self.btn_prev = tk.Button(
            ctrl_row, text="⏪ -5s", command=self._player_skip_back, **wide_btn)
        self.btn_prev.pack(side="left", padx=2)

        # Play / Pause  (larger, accent colour)
        self.btn_play = tk.Button(
            ctrl_row, text="▶  Play", command=self._player_play_pause,
            font=("Helvetica", 13, "bold"), width=10,
            relief="raised", bd=2, bg="#e0f0ff"
        )
        self.btn_play.pack(side="left", padx=6)

        # Stop
        self.btn_stop = tk.Button(
            ctrl_row, text="⏹ Stop", command=self._player_stop, **wide_btn)
        self.btn_stop.pack(side="left", padx=2)

        # Skip forward 5s
        self.btn_next = tk.Button(
            ctrl_row, text="⏩ +5s", command=self._player_skip_forward, **wide_btn)
        self.btn_next.pack(side="left", padx=2)

        # Next song
        self.btn_next_song = tk.Button(
            ctrl_row, text="⏭", command=self._player_next_song, **btn_style)
        self.btn_next_song.pack(side="left", padx=2)

        # ── Row 3: Seek bar + time ──
        seek_row = tk.Frame(player_frame)
        seek_row.pack(fill="x", pady=(0, 2))

        self.player_time_cur_var = tk.StringVar(value="0:00")
        tk.Label(seek_row, textvariable=self.player_time_cur_var,
                 font=("Consolas", 10), width=6).pack(side="left")

        self.seek_var = tk.DoubleVar(value=0)
        self.seek_bar = ttk.Scale(seek_row, from_=0, to=100, variable=self.seek_var,
                                  orient="horizontal", command=self._on_seek)
        self.seek_bar.pack(side="left", fill="x", expand=True, padx=4)

        self.player_time_tot_var = tk.StringVar(value="0:00")
        tk.Label(seek_row, textvariable=self.player_time_tot_var,
                 font=("Consolas", 10), width=6).pack(side="right")

        # ── Row 4: Volume slider ──
        vol_row = tk.Frame(player_frame)
        vol_row.pack(fill="x", pady=(0, 2))

        tk.Label(vol_row, text="🔊 Volume:", font=("Helvetica", 9)).pack(side="left")
        self.playback_vol_var = tk.DoubleVar(value=80)
        ttk.Scale(vol_row, from_=0, to=100, variable=self.playback_vol_var,
                  orient="horizontal", length=140,
                  command=self._on_playback_volume_change).pack(side="left", padx=4)
        self.vol_pct_var = tk.StringVar(value="80%")
        tk.Label(vol_row, textvariable=self.vol_pct_var,
                 font=("Consolas", 9), width=5).pack(side="left")

    # ----- Player internals -----
    def _ensure_pygame(self):
        try:
            import pygame
            # Always check actual mixer state, not just our flag
            # (play_midi in audio_engine may have called mixer.quit())
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, channels=2)
            self._pygame_inited = True
            return True
        except Exception as e:
            self._pygame_inited = False
            print(f"pygame init failed: {e}")
            return False

    def _on_loop_toggle(self):
        """Called when user toggles the Loop checkbox."""
        if self._loop_var.get():
            self.status_var.set("🔁 Loop ON")
        else:
            self.status_var.set("Loop OFF")

    def _player_load_and_play(self, wav_path: str):
        """Load a WAV file into the player and start playing."""
        if not self._ensure_pygame():
            self.status_var.set("pygame not available for playback")
            return
        try:
            import pygame
            import wave as _wave

            if self._is_playing:
                pygame.mixer.music.stop()

            try:
                with _wave.open(wav_path, 'r') as wf:
                    self._playback_length = wf.getnframes() / wf.getframerate()
            except Exception:
                self._playback_length = 0

            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.set_volume(self.playback_vol_var.get() / 100.0)
            pygame.mixer.music.play()

            self._is_playing = True
            self._is_paused = False
            self._playback_pos = 0.0
            self._current_track_path = wav_path

            self.btn_play.config(text="⏸  Pause")
            self.player_track_var.set(os.path.basename(wav_path))
            self.seek_bar.config(to=max(1, int(self._playback_length)))
            self._start_tick()
            self.status_var.set(f"▶ Playing: {os.path.basename(wav_path)}")

        except Exception as e:
            print(f"Player load error: {e}")
            self.status_var.set(f"Playback error: {e}")

    def _player_play_pause(self):
        if not self._ensure_pygame():
            return
        import pygame

        if not self._is_playing:
            # Nothing loaded — try the last generated WAV
            if self._current_track_path and os.path.exists(self._current_track_path):
                self._player_load_and_play(self._current_track_path)
            elif self.last_wav_path and os.path.exists(self.last_wav_path):
                self._player_load_and_play(self.last_wav_path)
            return

        if self._is_playing and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            self.btn_play.config(text="▶  Play")
            self._stop_tick()
        elif self._is_playing and self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            self.btn_play.config(text="⏸  Pause")
            self._start_tick()

    def _player_stop(self):
        if not self._pygame_inited:
            return
        import pygame
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self._is_playing = False
        self._is_paused = False
        self._playback_pos = 0.0
        self.btn_play.config(text="▶  Play")
        self.seek_var.set(0)
        self._update_time_label()
        self._stop_tick()

    def _player_skip_forward(self):
        """Skip 5 seconds forward."""
        if not self._is_playing or not self._pygame_inited:
            return
        import pygame
        new_pos = min(self._playback_pos + 5.0, self._playback_length)
        self._playback_pos = new_pos
        try:
            pygame.mixer.music.play(start=new_pos)
            pygame.mixer.music.set_volume(self.playback_vol_var.get() / 100.0)
            if self._is_paused:
                pygame.mixer.music.pause()
        except Exception:
            pass
        self.seek_var.set(new_pos)
        self._update_time_label()

    def _player_skip_back(self):
        """Skip 5 seconds backward."""
        if not self._is_playing or not self._pygame_inited:
            return
        import pygame
        new_pos = max(self._playback_pos - 5.0, 0.0)
        self._playback_pos = new_pos
        try:
            pygame.mixer.music.play(start=new_pos)
            pygame.mixer.music.set_volume(self.playback_vol_var.get() / 100.0)
            if self._is_paused:
                pygame.mixer.music.pause()
        except Exception:
            pass
        self.seek_var.set(new_pos)
        self._update_time_label()

    def _player_prev_song(self):
        """Load the previous WAV from the output folder."""
        wav_list = self._get_wav_list()
        if not wav_list:
            return
        current = self._current_track_path
        if current in wav_list:
            idx = wav_list.index(current)
            new_idx = (idx - 1) % len(wav_list)
        else:
            new_idx = len(wav_list) - 1
        self._player_load_and_play(wav_list[new_idx])

    def _player_next_song(self):
        """Load the next WAV from the output folder."""
        wav_list = self._get_wav_list()
        if not wav_list:
            return
        current = self._current_track_path
        if current in wav_list:
            idx = wav_list.index(current)
            new_idx = (idx + 1) % len(wav_list)
        else:
            new_idx = 0
        self._player_load_and_play(wav_list[new_idx])

    def _get_wav_list(self):
        """Get sorted list of WAV files in the output directory."""
        if not os.path.exists(OUTPUT_DIR):
            return []
        files = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith('.wav')]
        files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        return files

    def _on_seek(self, value):
        """User dragged the seek bar."""
        if not self._is_playing or not self._pygame_inited:
            return
        import pygame
        pos = float(value)
        self._playback_pos = pos
        try:
            pygame.mixer.music.play(start=pos)
            pygame.mixer.music.set_volume(self.playback_vol_var.get() / 100.0)
            if self._is_paused:
                pygame.mixer.music.pause()
        except Exception:
            pass
        self._update_time_label()

    def _on_playback_volume_change(self, value):
        vol = float(value)
        self.vol_pct_var.set(f"{int(vol)}%")
        if self._pygame_inited:
            try:
                import pygame
                if pygame.mixer.get_init():
                    pygame.mixer.music.set_volume(vol / 100.0)
            except Exception:
                pass

    def _start_tick(self):
        self._stop_tick()
        self._tick_job = self.root.after(500, self._tick)

    def _stop_tick(self):
        if self._tick_job:
            self.root.after_cancel(self._tick_job)
            self._tick_job = None

    def _tick(self):
        if not self._is_playing or self._is_paused:
            return
        try:
            import pygame
            if not pygame.mixer.music.get_busy():
                # Song finished
                if self._loop_var.get() and self._current_track_path:
                    # Loop: replay same track
                    self._player_load_and_play(self._current_track_path)
                else:
                    self._player_stop()
                return
        except Exception:
            pass
        self._playback_pos += 0.5
        if self._playback_pos > self._playback_length:
            self._playback_pos = self._playback_length
        self.seek_var.set(self._playback_pos)
        self._update_time_label()
        self._tick_job = self.root.after(500, self._tick)

    def _update_time_label(self):
        cur = int(self._playback_pos)
        tot = int(self._playback_length)
        self.player_time_cur_var.set(f"{cur // 60}:{cur % 60:02d}")
        self.player_time_tot_var.set(f"{tot // 60}:{tot % 60:02d}")

    # =====================================================================
    # STATUS BAR
    # =====================================================================
    def setup_status_bar(self, parent):
        sf = ttk.Frame(parent); sf.pack(fill="x", side="bottom", pady=5)
        self.status_var = tk.StringVar(value="Ready to generate music!")
        ttk.Label(sf, textvariable=self.status_var,
                  font=("Helvetica", 10), relief="sunken", padding=5).pack(fill="x")

    # =====================================================================
    # GENERATION LOGIC
    # =====================================================================
    def on_play_wav_click(self):
        """Play the last generated WAV file."""
        if self.last_wav_path and os.path.exists(self.last_wav_path):
            self._player_load_and_play(self.last_wav_path)
        else:
            messagebox.showinfo("No WAV", "No WAV file generated yet.\nGenerate a track with 'Render to WAV' enabled first.")

    def on_play_midi_click(self):
        """Play the last generated MIDI file."""
        if self.last_midi_path and os.path.exists(self.last_midi_path):
            self.status_var.set(f"🎹 Playing MIDI: {os.path.basename(self.last_midi_path)}")
            threading.Thread(
                target=lambda: self.audio_engine.play_midi(self.last_midi_path),
                daemon=True
            ).start()
        else:
            messagebox.showinfo("No MIDI", "No MIDI file generated yet.\nGenerate a track first.")

    def on_generate_click(self):
        self.generate_btn.config(state="disabled")
        self.progress_bar.start(10)
        self.status_var.set("Generating music... Please wait.")

        mood = self.mood_var.get()
        duration = self.duration_var.get()
        bpm_str = self.bpm_var.get().strip()
        bpm = int(bpm_str) if bpm_str.isdigit() else None
        render_audio = self.render_audio_var.get()

        thread = threading.Thread(
            target=self._generate_thread,
            args=(mood, duration, bpm, render_audio), daemon=True)
        thread.start()

    def _generate_thread(self, mood, duration, bpm, render_audio):
        try:
            style_settings = self.get_style_settings()
            effects_cfg = self._collect_effects_config()

            midi_path, wav_path, ctx = self.orchestrator.generate(
                mood=mood,
                length_in_bars=duration,
                bpm=bpm,
                render_audio=render_audio,
                note_properties=self.note_properties,
                master_volume=self.master_volume_var.get(),
                style_settings=style_settings,
                effects_config=effects_cfg
            )

            tracks_info = {
                'drums':   {'count': len(getattr(self.orchestrator, 'drums_track', []))},
                'bass':    {'count': len(getattr(self.orchestrator, 'bass_track', []))},
                'harmony': {'count': len(getattr(self.orchestrator, 'harmony_track', []))},
                'lead':    {'count': len(getattr(self.orchestrator, 'lead_track', []))},
            }

            self.root.after(0, lambda: self._on_generation_complete(
                midi_path, wav_path, ctx, tracks_info))

        except Exception as e:
            import traceback; traceback.print_exc()
            self.root.after(0, lambda: self._on_generation_error(str(e)))

    def _on_generation_complete(self, midi_path, wav_path, ctx, tracks_info):
        self.progress_bar.stop()
        self.progress_var.set(100)

        self.last_midi_path = midi_path
        self.last_wav_path = wav_path
        self.last_context = ctx

        self.status_var.set(f"✅ Generated {ctx.mood} song in {ctx.key} at {ctx.bpm} BPM!")
        self.midi_path_var.set(os.path.basename(midi_path) if midi_path else "N/A")
        self.wav_path_var.set(os.path.basename(wav_path) if wav_path else "N/A (FluidSynth not available)")

        self.generate_btn.config(state="normal")

        # Update section view
        self.update_section_view(ctx, tracks_info)
        self.refresh_recent_tracks()

        # Auto-play if option is enabled
        if self.auto_play_var.get() and wav_path and os.path.exists(wav_path):
            self._player_load_and_play(wav_path)

    def _on_generation_error(self, error_msg):
        self.progress_bar.stop()
        self.status_var.set(f"❌ Error: {error_msg}")
        self.generate_btn.config(state="normal")
        messagebox.showerror("Generation Error", f"An error occurred:\n{error_msg}")

    # =====================================================================
    # RUN
    # =====================================================================
    def run(self):
        self.root.mainloop()


def launch_ui():
    """Launch the main UI window."""
    root = tk.Tk()
    app = MainWindow(root)
    app.run()


if __name__ == "__main__":
    launch_ui()
