"""
Utilities for rendering and saving MIDI files.
Takes the raw note lists from the generators and writes them into a standard MIDI file.
"""

import os
from typing import List, Dict, Tuple
from mido import MidiFile, MidiTrack, Message, MetaMessage

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import TICKS_PER_BEAT, OUTPUT_DIR, INSTRUMENTS, DRUM_CHANNEL


class MidiRenderer:
    """
    Handles the creation and saving of MIDI files (Type 1 - Multi-track).
    """
    
    def __init__(self, bpm: int = 120, ticks_per_beat: int = TICKS_PER_BEAT):
        """
        Initialize the MIDI renderer.
        
        Args:
            bpm: Tempo in beats per minute
            ticks_per_beat: MIDI resolution (ticks per quarter note)
        """
        self.bpm = bpm
        self.ticks_per_beat = ticks_per_beat
        self.mid = MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    
    def create_tempo_track(self) -> MidiTrack:
        """Create a tempo/conductor track."""
        track = MidiTrack()
        tempo = int(60_000_000 / self.bpm)  # Microseconds per beat
        track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
        track.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
        track.append(MetaMessage('end_of_track', time=0))
        return track
    
    def create_instrument_track(
        self,
        name: str,
        events: List[Dict],
        channel: int,
        program: int = 0
    ) -> MidiTrack:
        """
        Create a MIDI track for an instrument.
        
        Args:
            name: Track name
            events: List of events.  Supported event types:
                    Note event (default):
                      - 'note': MIDI note number
                      - 'start': Start time in ticks
                      - 'duration': Duration in ticks
                      - 'velocity': Note velocity (optional, default 80)
                    Pitch-bend event (type='pitchbend'):
                      - 'value': Pitch-bend value (-8192 .. +8191)
                      - 'time':  Absolute tick position
                    Control-change event (type='control_change'):
                      - 'control': CC number
                      - 'value':   CC value (0-127)
                      - 'time':    Absolute tick position
            channel: MIDI channel (0-15)
            program: MIDI program number (instrument)
            
        Returns:
            MidiTrack object
        """
        track = MidiTrack()
        track.append(MetaMessage('track_name', name=name, time=0))
        
        # Set instrument (program change) - skip for drums
        if channel != DRUM_CHANNEL:
            track.append(Message('program_change', channel=channel, program=program, time=0))
        
        # Set channel volume (CC7) and pan center (CC10) for audibility
        track.append(Message('control_change', channel=channel, control=7, value=100, time=0))
        track.append(Message('control_change', channel=channel, control=10, value=64, time=0))
        
        # Set pitch-bend range to +/- 2 semitones via RPN 0 (GM default)
        # RPN MSB
        track.append(Message('control_change', channel=channel, control=101, value=0, time=0))
        # RPN LSB
        track.append(Message('control_change', channel=channel, control=100, value=0, time=0))
        # Data Entry MSB = 2 semitones
        track.append(Message('control_change', channel=channel, control=6, value=2, time=0))
        # Data Entry LSB = 0
        track.append(Message('control_change', channel=channel, control=38, value=0, time=0))
        
        # Convert events to MIDI messages
        # We need to sort by time and convert to delta times
        midi_events = []
        
        for event in events:
            evt_type = event.get('type', 'note')

            if evt_type == 'pitchbend':
                # Pitch-bend message
                midi_events.append({
                    'msg_type': 'pitchwheel',
                    'time': event['time'],
                    'pitch': max(-8192, min(8191, event['value'])),
                    'channel': channel,
                    '_sort_order': 0,  # PB before notes at same tick
                })

            elif evt_type == 'control_change':
                # Control-change message (CC1 modulation, CC11 expression, etc.)
                midi_events.append({
                    'msg_type': 'control_change',
                    'time': event['time'],
                    'control': event['control'],
                    'value': max(0, min(127, event['value'])),
                    'channel': channel,
                    '_sort_order': 0,
                })

            else:
                # Standard note event
                note = event['note']
                start = event['start']
                duration = event['duration']
                velocity = event.get('velocity', 80)

                midi_events.append({
                    'msg_type': 'note_on',
                    'time': start,
                    'note': note,
                    'velocity': velocity,
                    'channel': channel,
                    '_sort_order': 1,  # Notes after CC/PB at same tick
                })
                midi_events.append({
                    'msg_type': 'note_off',
                    'time': start + duration,
                    'note': note,
                    'velocity': 0,
                    'channel': channel,
                    '_sort_order': 2,
                })
        
        # Sort by absolute time, then by sort order (CC/PB before note_on before note_off)
        midi_events.sort(key=lambda x: (x['time'], x['_sort_order']))
        
        # Convert to delta times and build MIDI messages
        current_time = 0
        for event in midi_events:
            delta = max(0, event['time'] - current_time)
            msg_type = event['msg_type']

            if msg_type == 'pitchwheel':
                track.append(Message(
                    'pitchwheel',
                    channel=event['channel'],
                    pitch=event['pitch'],
                    time=delta,
                ))
            elif msg_type == 'control_change':
                track.append(Message(
                    'control_change',
                    channel=event['channel'],
                    control=event['control'],
                    value=event['value'],
                    time=delta,
                ))
            else:
                track.append(Message(
                    msg_type,
                    channel=event['channel'],
                    note=event['note'],
                    velocity=event['velocity'],
                    time=delta,
                ))

            current_time = event['time']
        
        track.append(MetaMessage('end_of_track', time=0))
        return track
    
    def render(
        self,
        tracks_data: Dict[str, Tuple[List[Dict], int, int]],
        filename: str = None
    ) -> str:
        """
        Render all tracks to a MIDI file.
        
        Args:
            tracks_data: Dictionary mapping track names to tuples of:
                        (events_list, channel, program)
            filename: Output filename (without path). If None, auto-generated.
            
        Returns:
            Full path to the saved MIDI file
        """
        # Create new MIDI file
        self.mid = MidiFile(type=1, ticks_per_beat=self.ticks_per_beat)
        
        # Add tempo track
        self.mid.tracks.append(self.create_tempo_track())
        
        # Add instrument tracks
        for name, (events, channel, program) in tracks_data.items():
            if events:  # Only add non-empty tracks
                track = self.create_instrument_track(name, events, channel, program)
                self.mid.tracks.append(track)
        
        # Generate filename if not provided
        if filename is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.mid"
        
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Full path
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Save
        self.mid.save(filepath)
        print(f"MIDI file saved: {filepath}")
        
        return filepath
    
    def render_single_track(
        self,
        name: str,
        events: List[Dict],
        channel: int,
        program: int,
        filename: str = None
    ) -> str:
        """
        Render a single instrument track to its own MIDI file.
        Used for per-track rendering when applying per-section effects.

        Args:
            name: Track name
            events: Note events list
            channel: MIDI channel
            program: MIDI program number
            filename: Output filename (auto-generated if None)

        Returns:
            Full path to the saved single-track MIDI file
        """
        mid = MidiFile(type=1, ticks_per_beat=self.ticks_per_beat)

        # Tempo track
        mid.tracks.append(self.create_tempo_track())

        # Single instrument track
        if events:
            track = self.create_instrument_track(name, events, channel, program)
            mid.tracks.append(track)

        if filename is None:
            filename = f"_temp_{name.lower()}.mid"

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)
        mid.save(filepath)
        return filepath

    def get_program_for_instrument(self, instrument_name: str) -> int:
        """Get MIDI program number for an instrument name."""
        return INSTRUMENTS.get(instrument_name, 0)
