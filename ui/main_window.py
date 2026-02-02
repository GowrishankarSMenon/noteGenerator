"""
Main Tkinter window for the Symphony Generator UI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


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
        self.root.title("Symphony Generator")
        self.root.geometry("800x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface components."""
        # Title
        title_label = tk.Label(
            self.root,
            text="Symphony Generator",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=20)
        
        # Controls Frame
        controls_frame = ttk.LabelFrame(self.root, text="Generation Controls", padding=20)
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        # BPM Control
        ttk.Label(controls_frame, text="BPM:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.bpm_var = tk.IntVar(value=120)
        bpm_spinbox = ttk.Spinbox(
            controls_frame,
            from_=60,
            to=180,
            textvariable=self.bpm_var,
            width=10
        )
        bpm_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Key Selection
        ttk.Label(controls_frame, text="Key:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.key_var = tk.StringVar(value="C")
        key_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.key_var,
            values=["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
            width=8
        )
        key_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Generate Button
        generate_btn = ttk.Button(
            self.root,
            text="Generate Music",
            command=self.generate_music
        )
        generate_btn.pack(pady=20)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief="sunken"
        )
        status_label.pack(fill="x", side="bottom", padx=10, pady=5)
    
    def generate_music(self):
        """Handle the generate music button click."""
        self.status_var.set("Generating music...")
        self.root.update()
        
        # TODO: Implement actual generation logic
        messagebox.showinfo("Info", "Music generation not yet implemented!")
        
        self.status_var.set("Ready")
    
    def run(self):
        """Start the UI event loop."""
        self.root.mainloop()


def launch_ui():
    """Launch the main UI window."""
    root = tk.Tk()
    app = MainWindow(root)
    app.run()
