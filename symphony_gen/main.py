"""
Symphony Gen - Application Entry Point
Bootstraps the application and checks for required assets.
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import DATASET_PATH, SOUNDFONT_PATH, OUTPUT_DIR


def check_assets():
    """
    Check if required assets exist and provide helpful messages.
    
    Returns:
        bool: True if critical assets are available
    """
    print("=" * 50)
    print("Symphony Generator - Asset Check")
    print("=" * 50)
    
    all_good = True
    
    # Check dataset
    if os.path.exists(DATASET_PATH):
        print(f"✅ Dataset found: {DATASET_PATH}")
    else:
        print(f"⚠️  Dataset not found: {DATASET_PATH}")
        print("   Using built-in training data for Markov chain.")
        # Not critical - we have fallback
    
    # Check SoundFont
    if os.path.exists(SOUNDFONT_PATH):
        print(f"✅ SoundFont found: {SOUNDFONT_PATH}")
    else:
        print(f"⚠️  SoundFont not found: {SOUNDFONT_PATH}")
        print("   Audio rendering will be unavailable.")
        print("   Download FluidR3_GM.sf2 and place it in assets/fonts/")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✅ Output directory: {OUTPUT_DIR}")
    
    # Check for FluidSynth (pyfluidsynth library or CLI)
    fluidsynth_ok = False
    try:
        import fluidsynth
        fs = fluidsynth.Synth()
        fs.delete()
        print("✅ FluidSynth available (pyfluidsynth library)")
        fluidsynth_ok = True
    except (ImportError, Exception):
        pass
    
    if not fluidsynth_ok:
        import subprocess
        try:
            result = subprocess.run(['fluidsynth', '--version'], capture_output=True)
            if result.returncode == 0:
                print("✅ FluidSynth available (CLI)")
                fluidsynth_ok = True
        except FileNotFoundError:
            pass
    
    if not fluidsynth_ok:
        print("⚠️  FluidSynth not found")
        print("   Install pyfluidsynth: pip install pyfluidsynth")
    
    print("=" * 50)
    return all_good


def main():
    """Main entry point for the Symphony Generator application."""
    print("\n🎵 Symphony Generator - AI Music Composer 🎵\n")
    
    # Check assets
    check_assets()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--cli':
            # CLI mode
            run_cli()
        elif sys.argv[1] == '--help':
            print_help()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print_help()
    else:
        # Launch GUI
        launch_gui()


def launch_gui():
    """Launch the Tkinter GUI."""
    try:
        from ui.main_window import launch_ui
        print("\nLaunching GUI...\n")
        launch_ui()
    except ImportError as e:
        print(f"Error importing UI: {e}")
        print("Falling back to CLI mode...")
        run_cli()
    except Exception as e:
        print(f"Error launching GUI: {e}")
        print("Try running in CLI mode with: python main.py --cli")


def run_cli():
    """Run in command-line mode."""
    from core.orchestrator import Orchestrator
    
    print("\n--- CLI Mode ---\n")
    
    orchestrator = Orchestrator()
    moods = orchestrator.get_available_moods()
    
    print("Available moods:", ", ".join(moods))
    
    # Get user input
    mood = input(f"\nEnter mood [{moods[0]}]: ").strip() or moods[0]
    if mood not in moods:
        print(f"Invalid mood, using '{moods[0]}'")
        mood = moods[0]
    
    bars_input = input("Enter duration in bars [16]: ").strip()
    bars = int(bars_input) if bars_input.isdigit() else 16
    
    bpm_input = input("Enter BPM (leave empty for auto): ").strip()
    bpm = int(bpm_input) if bpm_input.isdigit() else None
    
    render_input = input("Render to WAV? [y/n]: ").strip().lower()
    render_audio = render_input != 'n'
    
    print("\nGenerating...")
    
    midi_path, wav_path, ctx = orchestrator.generate(
        mood=mood,
        length_in_bars=bars,
        bpm=bpm,
        render_audio=render_audio
    )
    
    print(f"\nDone! Files saved to:")
    print(f"  MIDI: {midi_path}")
    if wav_path:
        print(f"  WAV:  {wav_path}")


def print_help():
    """Print help information."""
    print("""
Symphony Generator - AI-Powered Music Composer

Usage:
    python main.py          Launch the GUI application
    python main.py --cli    Run in command-line mode
    python main.py --help   Show this help message

Requirements:
    - Python 3.8+
    - mido (pip install mido)
    - FluidSynth (for audio rendering)
    - FluidR3_GM.sf2 SoundFont file
    
For more information, see the README.md file.
""")


if __name__ == "__main__":
    main()
