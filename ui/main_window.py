"""
Main Tkinter window for the Symphony Generator UI.
Collects user intent and shows progress with section properties viewer.
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
from config.settings import OUTPUT_DIR


class MainWindow:
    """
    Main application window for Symphony Generator.
    Features tabbed interface with generation controls, section properties, and recent tracks.
    """
    
    def __init__(self, root):
        """Initialize the main window."""
        self.root = root
        self.root.title("Symphony Generator - AI Music Composer")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.root.minsize(700, 600)
        
        # Initialize components
        self.orchestrator = Orchestrator()
        self.audio_engine = AudioEngine()
        
        # Store generated files and context
        self.last_midi_path = None
        self.last_wav_path = None
        self.last_context = None
        
        # Note properties (volume, attack, sustain)
        self.note_properties = {
            'drums': {'volume': 100, 'attack': 10, 'sustain': 80},
            'bass': {'volume': 90, 'attack': 20, 'sustain': 70},
            'harmony': {'volume': 75, 'attack': 30, 'sustain': 90},
            'lead': {'volume': 85, 'attack': 15, 'sustain': 85}
        }
        
        # Build UI
        self.setup_ui()
        
        # Load recent tracks on startup
        self.refresh_recent_tracks()
    
    def setup_ui(self):
        """Setup the user interface with notebook tabs."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text="🎵 Symphony Generator",
            font=("Helvetica", 22, "bold")
        )
        title_label.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="AI-Powered Mood-Based Music Composer",
            font=("Helvetica", 10),
            fg="gray"
        )
        subtitle.pack()
        
        # Create Notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)
        
        # Tab 1: Generate
        self.generate_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.generate_tab, text="🎼 Generate")
        self.setup_generate_tab()
        
        # Tab 2: Note Properties
        self.properties_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.properties_tab, text="🎛️ Note Properties")
        self.setup_properties_tab()
        
        # Tab 3: Section View
        self.section_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.section_tab, text="📊 Section View")
        self.setup_section_tab()
        
        # Tab 4: Recent Tracks
        self.recent_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.recent_tab, text="📁 Recent Tracks")
        self.setup_recent_tab()
        
        # Status Bar at bottom
        self.setup_status_bar(main_frame)
    
    def setup_generate_tab(self):
        """Setup the main generation controls tab."""
        # Controls Frame
        controls_frame = ttk.LabelFrame(self.generate_tab, text="Generation Settings", padding=15)
        controls_frame.pack(fill="x", pady=10)
        controls_frame.columnconfigure(1, weight=1)
        
        # Mood Selection
        ttk.Label(controls_frame, text="Mood:", font=("Helvetica", 11)).grid(
            row=0, column=0, sticky="w", padx=5, pady=8
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
        mood_combo.grid(row=0, column=1, sticky="w", padx=5, pady=8)
        
        # Duration Slider
        ttk.Label(controls_frame, text="Duration (bars):", font=("Helvetica", 11)).grid(
            row=1, column=0, sticky="w", padx=5, pady=8
        )
        
        duration_frame = ttk.Frame(controls_frame)
        duration_frame.grid(row=1, column=1, sticky="w", padx=5, pady=8)
        
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
        
        # BPM Entry
        ttk.Label(controls_frame, text="BPM (optional):", font=("Helvetica", 11)).grid(
            row=2, column=0, sticky="w", padx=5, pady=8
        )
        bpm_frame = ttk.Frame(controls_frame)
        bpm_frame.grid(row=2, column=1, sticky="w", padx=5, pady=8)
        self.bpm_var = tk.StringVar(value="")
        bpm_entry = ttk.Entry(bpm_frame, textvariable=self.bpm_var, width=10)
        bpm_entry.pack(side="left")
        ttk.Label(bpm_frame, text="(leave empty for auto)", font=("Helvetica", 9), foreground="gray").pack(side="left", padx=10)
        
        # Master Volume
        ttk.Label(controls_frame, text="Master Volume:", font=("Helvetica", 11)).grid(
            row=3, column=0, sticky="w", padx=5, pady=8
        )
        volume_frame = ttk.Frame(controls_frame)
        volume_frame.grid(row=3, column=1, sticky="w", padx=5, pady=8)
        
        self.master_volume_var = tk.IntVar(value=100)
        volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=127,
            variable=self.master_volume_var,
            orient="horizontal",
            length=200,
            command=lambda v: self.volume_label.config(text=f"{int(float(v))}")
        )
        volume_slider.pack(side="left")
        self.volume_label = ttk.Label(volume_frame, text="100", width=5)
        self.volume_label.pack(side="left", padx=10)
        
        # Render Audio Checkbox
        self.render_audio_var = tk.BooleanVar(value=True)
        render_check = ttk.Checkbutton(
            controls_frame,
            text="Render to WAV (requires FluidSynth)",
            variable=self.render_audio_var
        )
        render_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=8)
        
        # Buttons Frame
        buttons_frame = ttk.Frame(self.generate_tab)
        buttons_frame.pack(fill="x", pady=15)
        
        self.generate_btn = ttk.Button(
            buttons_frame,
            text="🎼 Generate Music",
            command=self.on_generate_click,
            width=20
        )
        self.generate_btn.pack(side="left", padx=5)
        
        self.play_midi_btn = ttk.Button(
            buttons_frame,
            text="▶️ Play MIDI",
            command=self.on_play_midi_click,
            state="disabled",
            width=15
        )
        self.play_midi_btn.pack(side="left", padx=5)
        
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
            self.generate_tab,
            variable=self.progress_var,
            mode="indeterminate",
            length=400
        )
        self.progress_bar.pack(pady=10)
        
        # Output Info
        self.output_frame = ttk.LabelFrame(self.generate_tab, text="Output Files", padding=10)
        self.output_frame.pack(fill="x", pady=10)
        
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
    
    def setup_properties_tab(self):
        """Setup the note properties tab with volume, attack, sustain controls."""
        info_label = ttk.Label(
            self.properties_tab,
            text="Adjust note properties for each instrument section:",
            font=("Helvetica", 11)
        )
        info_label.pack(pady=(0, 15))
        
        # Create a frame for each instrument section
        self.property_widgets = {}
        
        sections = [
            ('drums', '🥁 Drums'),
            ('bass', '🎸 Bass'),
            ('harmony', '🎹 Harmony'),
            ('lead', '🎵 Lead')
        ]
        
        for section_key, section_name in sections:
            self._create_section_properties(section_key, section_name)
        
        # Apply button
        apply_btn = ttk.Button(
            self.properties_tab,
            text="✓ Apply Properties",
            command=self.apply_note_properties,
            width=20
        )
        apply_btn.pack(pady=20)
        
        # Reset button
        reset_btn = ttk.Button(
            self.properties_tab,
            text="↺ Reset to Defaults",
            command=self.reset_note_properties,
            width=20
        )
        reset_btn.pack()
    
    def _create_section_properties(self, section_key, section_name):
        """Create property controls for a single section."""
        frame = ttk.LabelFrame(self.properties_tab, text=section_name, padding=10)
        frame.pack(fill="x", pady=5, padx=10)
        
        self.property_widgets[section_key] = {}
        
        # Volume slider
        vol_frame = ttk.Frame(frame)
        vol_frame.pack(fill="x", pady=3)
        ttk.Label(vol_frame, text="Volume:", width=10).pack(side="left")
        
        vol_var = tk.IntVar(value=self.note_properties[section_key]['volume'])
        vol_slider = ttk.Scale(
            vol_frame,
            from_=0,
            to=127,
            variable=vol_var,
            orient="horizontal",
            length=200
        )
        vol_slider.pack(side="left", padx=5)
        vol_label = ttk.Label(vol_frame, text=str(vol_var.get()), width=5)
        vol_label.pack(side="left")
        vol_slider.configure(command=lambda v, l=vol_label: l.config(text=str(int(float(v)))))
        self.property_widgets[section_key]['volume'] = vol_var
        
        # Attack slider (0-127, controls note-on velocity ramp)
        att_frame = ttk.Frame(frame)
        att_frame.pack(fill="x", pady=3)
        ttk.Label(att_frame, text="Attack:", width=10).pack(side="left")
        
        att_var = tk.IntVar(value=self.note_properties[section_key]['attack'])
        att_slider = ttk.Scale(
            att_frame,
            from_=0,
            to=127,
            variable=att_var,
            orient="horizontal",
            length=200
        )
        att_slider.pack(side="left", padx=5)
        att_label = ttk.Label(att_frame, text=str(att_var.get()), width=5)
        att_label.pack(side="left")
        att_slider.configure(command=lambda v, l=att_label: l.config(text=str(int(float(v)))))
        self.property_widgets[section_key]['attack'] = att_var
        
        # Sustain slider (percentage of note duration)
        sus_frame = ttk.Frame(frame)
        sus_frame.pack(fill="x", pady=3)
        ttk.Label(sus_frame, text="Sustain:", width=10).pack(side="left")
        
        sus_var = tk.IntVar(value=self.note_properties[section_key]['sustain'])
        sus_slider = ttk.Scale(
            sus_frame,
            from_=10,
            to=100,
            variable=sus_var,
            orient="horizontal",
            length=200
        )
        sus_slider.pack(side="left", padx=5)
        sus_label = ttk.Label(sus_frame, text=f"{sus_var.get()}%", width=5)
        sus_label.pack(side="left")
        sus_slider.configure(command=lambda v, l=sus_label: l.config(text=f"{int(float(v))}%"))
        self.property_widgets[section_key]['sustain'] = sus_var
    
    def apply_note_properties(self):
        """Apply the current note properties."""
        for section_key in self.note_properties:
            self.note_properties[section_key]['volume'] = self.property_widgets[section_key]['volume'].get()
            self.note_properties[section_key]['attack'] = self.property_widgets[section_key]['attack'].get()
            self.note_properties[section_key]['sustain'] = self.property_widgets[section_key]['sustain'].get()
        
        self.status_var.set("✓ Note properties applied!")
        messagebox.showinfo("Properties Applied", "Note properties have been saved and will be used in the next generation.")
    
    def reset_note_properties(self):
        """Reset note properties to defaults."""
        defaults = {
            'drums': {'volume': 100, 'attack': 10, 'sustain': 80},
            'bass': {'volume': 90, 'attack': 20, 'sustain': 70},
            'harmony': {'volume': 75, 'attack': 30, 'sustain': 90},
            'lead': {'volume': 85, 'attack': 15, 'sustain': 85}
        }
        
        for section_key in defaults:
            for prop_key in defaults[section_key]:
                self.property_widgets[section_key][prop_key].set(defaults[section_key][prop_key])
            self.note_properties[section_key] = defaults[section_key].copy()
        
        self.status_var.set("↺ Note properties reset to defaults")
    
    def setup_section_tab(self):
        """Setup the section view tab to display generated track details."""
        info_label = ttk.Label(
            self.section_tab,
            text="View properties of each section in the generated track:",
            font=("Helvetica", 11)
        )
        info_label.pack(pady=(0, 10))
        
        # Section info display
        self.section_notebook = ttk.Notebook(self.section_tab)
        self.section_notebook.pack(fill="both", expand=True)
        
        # Create sub-tabs for each section
        self.section_frames = {}
        sections = ['Overview', 'Drums', 'Bass', 'Harmony', 'Lead', 'Timeline']
        
        for section in sections:
            frame = ttk.Frame(self.section_notebook, padding=10)
            self.section_notebook.add(frame, text=section)
            self.section_frames[section] = frame
            
            # Add text widget for each section
            text_widget = tk.Text(frame, wrap="word", height=15, font=("Consolas", 10))
            text_widget.pack(fill="both", expand=True, side="left")
            
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
            scrollbar.pack(side="right", fill="y")
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            setattr(self, f"section_text_{section.lower()}", text_widget)
            text_widget.insert("1.0", "Generate a track to see section details...")
            text_widget.config(state="disabled")
    
    def update_section_view(self, ctx, tracks_info):
        """Update the section view with generated track information."""
        if not ctx:
            return
        
        # Overview
        overview_text = self.section_text_overview
        overview_text.config(state="normal")
        overview_text.delete("1.0", "end")
        overview_text.insert("end", f"═══════════════════════════════════════\n")
        overview_text.insert("end", f"        SONG OVERVIEW\n")
        overview_text.insert("end", f"═══════════════════════════════════════\n\n")
        overview_text.insert("end", f"  Mood:           {ctx.mood.upper()}\n")
        overview_text.insert("end", f"  Key:            {ctx.key}\n")
        overview_text.insert("end", f"  Scale:          {ctx.scale_type}\n")
        overview_text.insert("end", f"  BPM:            {ctx.bpm}\n")
        overview_text.insert("end", f"  Time Signature: {ctx.time_signature[0]}/{ctx.time_signature[1]}\n")
        overview_text.insert("end", f"  Total Bars:     {ctx.total_bars}\n")
        overview_text.insert("end", f"  Drum Style:     {ctx.drum_style}\n")
        overview_text.insert("end", f"  Harmony Style:  {ctx.harmony_style}\n")
        overview_text.insert("end", f"\n───────────────────────────────────────\n")
        overview_text.insert("end", f"  INSTRUMENTS\n")
        overview_text.insert("end", f"───────────────────────────────────────\n")
        for instr, prog in ctx.instruments.items():
            overview_text.insert("end", f"  {instr:12s}  →  Program {prog}\n")
        overview_text.config(state="disabled")
        
        # Drums
        drums_text = self.section_text_drums
        drums_text.config(state="normal")
        drums_text.delete("1.0", "end")
        drums_text.insert("end", f"🥁 DRUMS SECTION\n")
        drums_text.insert("end", f"═══════════════════════════════════════\n\n")
        drums_text.insert("end", f"Style:    {ctx.drum_style}\n")
        drums_text.insert("end", f"Channel:  10 (MIDI Percussion)\n")
        drums_text.insert("end", f"Volume:   {self.note_properties['drums']['volume']}\n")
        drums_text.insert("end", f"Attack:   {self.note_properties['drums']['attack']}\n")
        drums_text.insert("end", f"Sustain:  {self.note_properties['drums']['sustain']}%\n\n")
        if 'drums' in tracks_info:
            drums_text.insert("end", f"Notes Generated: {tracks_info['drums']['count']}\n")
        drums_text.config(state="disabled")
        
        # Bass
        bass_text = self.section_text_bass
        bass_text.config(state="normal")
        bass_text.delete("1.0", "end")
        bass_text.insert("end", f"🎸 BASS SECTION\n")
        bass_text.insert("end", f"═══════════════════════════════════════\n\n")
        bass_text.insert("end", f"Instrument: {ctx.instruments.get('bass', 'Electric Bass')}\n")
        bass_text.insert("end", f"Technique:  Locks to kick drum pattern\n")
        bass_text.insert("end", f"Volume:     {self.note_properties['bass']['volume']}\n")
        bass_text.insert("end", f"Attack:     {self.note_properties['bass']['attack']}\n")
        bass_text.insert("end", f"Sustain:    {self.note_properties['bass']['sustain']}%\n\n")
        if 'bass' in tracks_info:
            bass_text.insert("end", f"Notes Generated: {tracks_info['bass']['count']}\n")
        bass_text.config(state="disabled")
        
        # Harmony
        harmony_text = self.section_text_harmony
        harmony_text.config(state="normal")
        harmony_text.delete("1.0", "end")
        harmony_text.insert("end", f"🎹 HARMONY SECTION\n")
        harmony_text.insert("end", f"═══════════════════════════════════════\n\n")
        harmony_text.insert("end", f"Instrument: {ctx.instruments.get('harmony', 'Piano')}\n")
        harmony_text.insert("end", f"Style:      {ctx.harmony_style}\n")
        harmony_text.insert("end", f"Volume:     {self.note_properties['harmony']['volume']}\n")
        harmony_text.insert("end", f"Attack:     {self.note_properties['harmony']['attack']}\n")
        harmony_text.insert("end", f"Sustain:    {self.note_properties['harmony']['sustain']}%\n\n")
        if 'harmony' in tracks_info:
            harmony_text.insert("end", f"Notes Generated: {tracks_info['harmony']['count']}\n")
        harmony_text.config(state="disabled")
        
        # Lead
        lead_text = self.section_text_lead
        lead_text.config(state="normal")
        lead_text.delete("1.0", "end")
        lead_text.insert("end", f"🎵 LEAD SECTION\n")
        lead_text.insert("end", f"═══════════════════════════════════════\n\n")
        lead_text.insert("end", f"Instrument:   {ctx.instruments.get('lead', 'Synth Lead')}\n")
        lead_text.insert("end", f"Technique:    Markov Chain (2nd order)\n")
        lead_text.insert("end", f"Scale Filter: {ctx.scale_type}\n")
        lead_text.insert("end", f"Volume:       {self.note_properties['lead']['volume']}\n")
        lead_text.insert("end", f"Attack:       {self.note_properties['lead']['attack']}\n")
        lead_text.insert("end", f"Sustain:      {self.note_properties['lead']['sustain']}%\n\n")
        if 'lead' in tracks_info:
            lead_text.insert("end", f"Notes Generated: {tracks_info['lead']['count']}\n")
        lead_text.config(state="disabled")
        
        # Timeline
        timeline_text = self.section_text_timeline
        timeline_text.config(state="normal")
        timeline_text.delete("1.0", "end")
        timeline_text.insert("end", f"📊 CHORD TIMELINE\n")
        timeline_text.insert("end", f"═══════════════════════════════════════\n\n")
        timeline_text.insert("end", f"Bar  │ Chord    │ Scale\n")
        timeline_text.insert("end", f"─────┼──────────┼────────────────\n")
        for bar in ctx.timeline[:32]:  # Show first 32 bars
            timeline_text.insert("end", f" {bar.bar_index+1:3d} │ {bar.chord_name:8s} │ {bar.scale_type}\n")
        if len(ctx.timeline) > 32:
            timeline_text.insert("end", f"\n... and {len(ctx.timeline) - 32} more bars\n")
        timeline_text.config(state="disabled")
    
    def setup_recent_tab(self):
        """Setup the recent tracks tab."""
        # Header
        header_frame = ttk.Frame(self.recent_tab)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text="Recently Generated Tracks:",
            font=("Helvetica", 11, "bold")
        ).pack(side="left")
        
        refresh_btn = ttk.Button(
            header_frame,
            text="🔄 Refresh",
            command=self.refresh_recent_tracks,
            width=10
        )
        refresh_btn.pack(side="right")
        
        # Treeview for recent tracks
        columns = ('filename', 'mood', 'key', 'bpm', 'date')
        self.recent_tree = ttk.Treeview(self.recent_tab, columns=columns, show='headings', height=12)
        
        self.recent_tree.heading('filename', text='Filename')
        self.recent_tree.heading('mood', text='Mood')
        self.recent_tree.heading('key', text='Key')
        self.recent_tree.heading('bpm', text='BPM')
        self.recent_tree.heading('date', text='Date')
        
        self.recent_tree.column('filename', width=250)
        self.recent_tree.column('mood', width=80)
        self.recent_tree.column('key', width=60)
        self.recent_tree.column('bpm', width=60)
        self.recent_tree.column('date', width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.recent_tab, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recent_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons
        action_frame = ttk.Frame(self.recent_tab)
        action_frame.pack(fill="x", pady=10, side="bottom")
        
        play_selected_btn = ttk.Button(
            action_frame,
            text="▶️ Play Selected",
            command=self.play_selected_track,
            width=15
        )
        play_selected_btn.pack(side="left", padx=5)
        
        open_folder_btn = ttk.Button(
            action_frame,
            text="📂 Open Output Folder",
            command=self.open_output_folder,
            width=18
        )
        open_folder_btn.pack(side="left", padx=5)
    
    def refresh_recent_tracks(self):
        """Refresh the list of recent tracks from output folder."""
        # Clear existing items
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        
        if not os.path.exists(OUTPUT_DIR):
            return
        
        # Get MIDI files sorted by modification time
        midi_files = []
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith('.mid'):
                full_path = os.path.join(OUTPUT_DIR, f)
                mtime = os.path.getmtime(full_path)
                midi_files.append((f, mtime, full_path))
        
        # Sort by modification time (newest first)
        midi_files.sort(key=lambda x: x[1], reverse=True)
        
        # Parse filename and add to tree
        for filename, mtime, full_path in midi_files[:50]:  # Show last 50
            # Parse: mood_key_bpm_timestamp.mid
            parts = filename.replace('.mid', '').split('_')
            if len(parts) >= 4:
                mood = parts[0]
                key = parts[1]
                bpm = parts[2].replace('bpm', '')
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            else:
                mood = key = bpm = "?"
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            
            self.recent_tree.insert('', 'end', values=(filename, mood, key, bpm, date_str), tags=(full_path,))
    
    def play_selected_track(self):
        """Play the selected track from the list."""
        selection = self.recent_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a track to play.")
            return
        
        item = self.recent_tree.item(selection[0])
        filename = item['values'][0]
        full_path = os.path.join(OUTPUT_DIR, filename)
        
        if os.path.exists(full_path):
            self.status_var.set(f"Playing: {filename}")
            threading.Thread(
                target=lambda: self.audio_engine.play_midi(full_path),
                daemon=True
            ).start()
    
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        if os.path.exists(OUTPUT_DIR):
            os.startfile(OUTPUT_DIR)
        else:
            messagebox.showwarning("Folder Not Found", "Output folder does not exist yet.")
    
    def setup_status_bar(self, parent):
        """Setup the status bar at the bottom."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", side="bottom", pady=5)
        
        self.status_var = tk.StringVar(value="Ready to generate music!")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Helvetica", 10),
            relief="sunken",
            padding=5
        )
        status_label.pack(fill="x")
    
    def on_generate_click(self):
        """Handle the generate music button click."""
        self.generate_btn.config(state="disabled")
        self.play_midi_btn.config(state="disabled")
        self.play_wav_btn.config(state="disabled")
        
        self.progress_bar.start(10)
        self.status_var.set("Generating music... Please wait.")
        
        mood = self.mood_var.get()
        duration = self.duration_var.get()
        bpm_str = self.bpm_var.get().strip()
        bpm = int(bpm_str) if bpm_str.isdigit() else None
        render_audio = self.render_audio_var.get()
        
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
                render_audio=render_audio,
                note_properties=self.note_properties,
                master_volume=self.master_volume_var.get()
            )
            
            # Collect track info
            tracks_info = {
                'drums': {'count': len(self.orchestrator.drums_track) if hasattr(self.orchestrator, 'drums_track') else 0},
                'bass': {'count': len(self.orchestrator.bass_track) if hasattr(self.orchestrator, 'bass_track') else 0},
                'harmony': {'count': len(self.orchestrator.harmony_track) if hasattr(self.orchestrator, 'harmony_track') else 0},
                'lead': {'count': len(self.orchestrator.lead_track) if hasattr(self.orchestrator, 'lead_track') else 0}
            }
            
            self.root.after(0, lambda: self._on_generation_complete(midi_path, wav_path, ctx, tracks_info))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self._on_generation_error(str(e)))
    
    def _on_generation_complete(self, midi_path, wav_path, ctx, tracks_info):
        """Called when generation completes successfully."""
        self.progress_bar.stop()
        self.progress_var.set(100)
        
        self.last_midi_path = midi_path
        self.last_wav_path = wav_path
        self.last_context = ctx
        
        self.status_var.set(f"✅ Generated {ctx.mood} song in {ctx.key} at {ctx.bpm} BPM!")
        
        self.midi_path_var.set(os.path.basename(midi_path) if midi_path else "N/A")
        self.wav_path_var.set(os.path.basename(wav_path) if wav_path else "N/A (FluidSynth not available)")
        
        self.generate_btn.config(state="normal")
        if midi_path:
            self.play_midi_btn.config(state="normal")
        if wav_path:
            self.play_wav_btn.config(state="normal")
        
        # Update section view
        self.update_section_view(ctx, tracks_info)
        
        # Refresh recent tracks
        self.refresh_recent_tracks()
        
        # Switch to section view tab to show details
        self.notebook.select(self.section_tab)
    
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
