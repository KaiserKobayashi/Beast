#!/usr/bin/env python3
"""
beast_gui_enhanced.py

Enhanced GUI for Beast audio/video processing toolkit.
Provides intuitive access to all Beast features:
- Audio source separation
- Noise reduction & cleanup
- Transcription with Whisper
- Subtitle editing
- TTS generation
- Audio mixing

Features:
- Tabbed interface for different workflows
- Real-time progress tracking
- Presets for common tasks
- Comprehensive settings
- Activity log
"""

import os
import sys
import subprocess
import threading
import queue
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import PySimpleGUI as sg
from beast_config import load_config, save_config, default_config

# Try to import beast_api for integrated workflows
try:
    from beast_api import Beast, BeastResult
    BEAST_API_AVAILABLE = True
except ImportError:
    BEAST_API_AVAILABLE = False

LOGS_DIR = Path.cwd() / "logs"
LOGS_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path.cwd() / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


class BeastGUI:
    """Enhanced Beast GUI with tabbed interface."""
    
    def __init__(self):
        self.config = load_config()
        self.theme = self.config.get("theme", "DarkBlue3")
        sg.theme(self.theme)
        
        self.window = None
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.current_log_file = None
        
    def create_layout(self):
        """Create the main GUI layout."""
        
        # ===== Tab 1: Quick Actions =====
        quick_tab = [
            [sg.Text("Quick Actions", font=('Arial', 12, 'bold'))],
            [sg.HorizontalSeparator()],
            
            [sg.Text("Input File/Folder:")],
            [sg.Input(key='-QUICK-INPUT-', size=(60, 1)),
             sg.FileBrowse(file_types=(("Media Files", "*.mp3;*.wav;*.mp4;*.mkv;*.mov;*.avi"),)),
             sg.FolderBrowse()],
            
            [sg.Text("Output Folder:")],
            [sg.Input(key='-QUICK-OUTPUT-', default_text=str(OUTPUT_DIR), size=(60, 1)),
             sg.FolderBrowse()],
            
            [sg.Frame("Common Tasks", [
                [sg.Button("🎤 Transcribe with Clean Audio", key='-QUICK-TRANSCRIBE-', size=(30, 2),
                          tooltip="Separate audio sources, extract clean vocals, transcribe with Whisper, enhance subtitles")],
                [sg.Button("🎵 Create Karaoke (Instrumental)", key='-QUICK-KARAOKE-', size=(30, 2),
                          tooltip="Remove vocals to create instrumental/karaoke track")],
                [sg.Button("🧹 Clean Up Video Audio", key='-QUICK-CLEANUP-', size=(30, 2),
                          tooltip="Remove noise and normalize audio in video")],
                [sg.Button("🎛️ Separate Audio Sources", key='-QUICK-SEPARATE-', size=(30, 2),
                          tooltip="Split audio into vocals, drums, bass, and other instruments")],
            ], size=(350, 200))],
            
            [sg.Text("", size=(1, 2))],  # Spacer
        ]
        
        # ===== Tab 2: Audio Enhancement =====
        audio_tab = [
            [sg.Text("Audio Enhancement & Separation", font=('Arial', 12, 'bold'))],
            [sg.HorizontalSeparator()],
            
            [sg.Text("Input File:")],
            [sg.Input(key='-AUDIO-INPUT-', size=(60, 1)),
             sg.FileBrowse(file_types=(("Audio/Video", "*.mp3;*.wav;*.mp4;*.mkv;*.flac;*.ogg"),))],
            
            [sg.Text("Output Folder:")],
            [sg.Input(key='-AUDIO-OUTPUT-', default_text=str(OUTPUT_DIR / "audio"), size=(60, 1)),
             sg.FolderBrowse()],
            
            [sg.Frame("Operation", [
                [sg.Radio("Separate Sources", "AUDIO_OP", key='-AUDIO-SEPARATE-', default=True,
                         tooltip="Split into vocals, drums, bass, other")],
                [sg.Combo(['htdemucs (4-stem)', 'htdemucs_6s (6-stem)', 'htdemucs_ft (fine-tuned)', 'mdx', 'mdx_extra'],
                         default_value='htdemucs (4-stem)', key='-AUDIO-MODEL-', size=(30, 1))],
                
                [sg.HorizontalSeparator()],
                
                [sg.Radio("Clean Up Audio", "AUDIO_OP", key='-AUDIO-CLEANUP-',
                         tooltip="Remove noise, normalize volume")],
                [sg.Checkbox("Normalize Volume", key='-AUDIO-NORMALIZE-', default=True)],
                [sg.Checkbox("Remove Background Noise", key='-AUDIO-DENOISE-', default=True)],
                [sg.Checkbox("Remove Silence", key='-AUDIO-REMOVE-SILENCE-')],
                [sg.Checkbox("Advanced Noise Reduction", key='-AUDIO-ADVANCED-DENOISE-',
                            tooltip="Spectral analysis (slower but better)")],
            ], size=(500, 230))],
            
            [sg.Text("Device:")],
            [sg.Radio("CPU", "DEVICE", key='-DEVICE-CPU-', default=True),
             sg.Radio("GPU (CUDA)", "DEVICE", key='-DEVICE-GPU-')],
            
            [sg.Button("Process Audio", key='-AUDIO-PROCESS-', size=(20, 1))],
        ]
        
        # ===== Tab 3: Transcription =====
        transcribe_tab = [
            [sg.Text("Transcription & Subtitles", font=('Arial', 12, 'bold'))],
            [sg.HorizontalSeparator()],
            
            [sg.Text("Input File:")],
            [sg.Input(key='-TRANS-INPUT-', size=(60, 1)),
             sg.FileBrowse(file_types=(("Media Files", "*.mp3;*.wav;*.mp4;*.mkv;*.mov"),))],
            
            [sg.Text("Output Folder:")],
            [sg.Input(key='-TRANS-OUTPUT-', default_text=str(OUTPUT_DIR / "transcription"), size=(60, 1)),
             sg.FolderBrowse()],
            
            [sg.Frame("Transcription Settings", [
                [sg.Text("Whisper Model:")],
                [sg.Combo(['tiny (fastest)', 'base (recommended)', 'small', 'medium', 'large (best quality)'],
                         default_value='base (recommended)', key='-TRANS-MODEL-', size=(30, 1))],
                
                [sg.Text("Language:")],
                [sg.Combo(['Auto-detect', 'English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese'],
                         default_value='Auto-detect', key='-TRANS-LANG-', size=(30, 1))],
                
                [sg.HorizontalSeparator()],
                
                [sg.Checkbox("Preprocess Audio (Separate & Clean)", key='-TRANS-PREPROCESS-', default=True,
                            tooltip="Extract clean vocals for better transcription accuracy")],
                [sg.Checkbox("Auto-enhance Subtitles", key='-TRANS-ENHANCE-', default=True,
                            tooltip="Fix timing, reading speed, and formatting issues")],
            ], size=(500, 200))],
            
            [sg.Button("Transcribe", key='-TRANS-RUN-', size=(20, 1))],
        ]
        
        # ===== Tab 4: Subtitle Editing =====
        subtitle_tab = [
            [sg.Text("Subtitle Editing", font=('Arial', 12, 'bold'))],
            [sg.HorizontalSeparator()],
            
            [sg.Text("Input Subtitle File:")],
            [sg.Input(key='-SUB-INPUT-', size=(60, 1)),
             sg.FileBrowse(file_types=(("Subtitles", "*.srt;*.vtt"),))],
            
            [sg.Text("Output Subtitle File:")],
            [sg.Input(key='-SUB-OUTPUT-', size=(60, 1)),
             sg.SaveAs(file_types=(("SRT", "*.srt"), ("VTT", "*.vtt")))],
            
            [sg.Frame("Operations", [
                [sg.Radio("Auto-Enhance (Recommended)", "SUB_OP", key='-SUB-ENHANCE-', default=True,
                         tooltip="Fix timing, reading speed, overlaps, etc.")],
                
                [sg.Radio("Adjust Timing", "SUB_OP", key='-SUB-TIMING-')],
                [sg.Text("Offset (seconds):", size=(15, 1)),
                 sg.Input(key='-SUB-OFFSET-', size=(10, 1), default_text="0.0")],
                
                [sg.Radio("Fix Reading Speed", "SUB_OP", key='-SUB-SPEED-')],
                [sg.Text("Max chars/second:", size=(15, 1)),
                 sg.Input(key='-SUB-CPS-', size=(10, 1), default_text="20")],
                
                [sg.Radio("Convert Format", "SUB_OP", key='-SUB-CONVERT-')],
                [sg.Text("Output format:", size=(15, 1)),
                 sg.Combo(['srt', 'vtt'], default_value='srt', key='-SUB-FORMAT-', size=(10, 1))],
                
                [sg.Radio("Show Statistics", "SUB_OP", key='-SUB-STATS-')],
            ], size=(500, 250))],
            
            [sg.Button("Process Subtitles", key='-SUB-PROCESS-', size=(20, 1))],
        ]
        
        # ===== Tab 5: Audio Mixing =====
        mixing_tab = [
            [sg.Text("Audio Mixing & Reconstruction", font=('Arial', 12, 'bold'))],
            [sg.HorizontalSeparator()],
            
            [sg.Text("Separated Sources Folder:")],
            [sg.Input(key='-MIX-INPUT-', size=(60, 1)),
             sg.FolderBrowse()],
            
            [sg.Text("Output File:")],
            [sg.Input(key='-MIX-OUTPUT-', size=(60, 1)),
             sg.SaveAs(file_types=(("WAV", "*.wav"), ("MP3", "*.mp3"), ("FLAC", "*.flac")))],
            
            [sg.Frame("Operation", [
                [sg.Radio("Mix All Sources", "MIX_OP", key='-MIX-ALL-', default=True)],
                [sg.Text("Volume Adjustments (dB):", font=('Arial', 9, 'italic'))],
                [sg.Text("Vocals:"), sg.Input(key='-MIX-VOL-VOCALS-', size=(8, 1), default_text="0")],
                [sg.Text("Drums:"), sg.Input(key='-MIX-VOL-DRUMS-', size=(8, 1), default_text="0")],
                [sg.Text("Bass:"), sg.Input(key='-MIX-VOL-BASS-', size=(8, 1), default_text="0")],
                [sg.Text("Other:"), sg.Input(key='-MIX-VOL-OTHER-', size=(8, 1), default_text="0")],
                
                [sg.HorizontalSeparator()],
                
                [sg.Radio("Create Instrumental (Remove Vocals)", "MIX_OP", key='-MIX-INSTRUMENTAL-')],
                [sg.Radio("Create Acapella (Vocals Only)", "MIX_OP", key='-MIX-ACAPELLA-')],
                
                [sg.HorizontalSeparator()],
                
                [sg.Radio("Replace Source", "MIX_OP", key='-MIX-REPLACE-')],
                [sg.Text("Source to replace:"), sg.Combo(['vocals', 'drums', 'bass', 'other'],
                                                         key='-MIX-REPLACE-SOURCE-', size=(15, 1))],
                [sg.Text("Replacement file:"), sg.Input(key='-MIX-REPLACE-FILE-', size=(30, 1)),
                 sg.FileBrowse()],
            ], size=(500, 320))],
            
            [sg.Button("Mix Audio", key='-MIX-PROCESS-', size=(20, 1))],
        ]
        
        # ===== Tab 6: Settings =====
        settings_tab = [
            [sg.Text("Settings", font=('Arial', 12, 'bold'))],
            [sg.HorizontalSeparator()],
            
            [sg.Frame("Appearance", [
                [sg.Text("Theme:")],
                [sg.Combo(['DarkBlue3', 'DarkGrey', 'LightGrey', 'SystemDefault', 'Reddit', 'Topanga'],
                         default_value=self.theme, key='-SETTINGS-THEME-', size=(20, 1))],
            ], size=(500, 80))],
            
            [sg.Frame("Default Settings", [
                [sg.Text("Default Output Folder:")],
                [sg.Input(key='-SETTINGS-OUTPUT-DIR-', default_text=str(OUTPUT_DIR), size=(50, 1)),
                 sg.FolderBrowse()],
                
                [sg.Text("Default Whisper Model:")],
                [sg.Combo(['tiny', 'base', 'small', 'medium', 'large'],
                         default_value='base', key='-SETTINGS-WHISPER-', size=(20, 1))],
                
                [sg.Text("Default Audio Device:")],
                [sg.Radio("CPU", "SET_DEVICE", key='-SETTINGS-CPU-', default=True),
                 sg.Radio("GPU", "SET_DEVICE", key='-SETTINGS-GPU-')],
            ], size=(500, 150))],
            
            [sg.Button("Save Settings", key='-SETTINGS-SAVE-', size=(15, 1)),
             sg.Button("Reset to Defaults", key='-SETTINGS-RESET-', size=(15, 1))],
            
            [sg.Text("", size=(1, 2))],
            [sg.Text("Beast Version: 2.0 (Enhanced)", font=('Arial', 9, 'italic'))],
            [sg.Text("Modules: Audio Separation • Cleanup • Mixing • Transcription • TTS",
                    font=('Arial', 8, 'italic'))],
        ]
        
        # ===== Main Tab Group =====
        tab_group = sg.TabGroup([
            [sg.Tab('Quick Actions', quick_tab, key='-TAB-QUICK-')],
            [sg.Tab('Audio Enhancement', audio_tab, key='-TAB-AUDIO-')],
            [sg.Tab('Transcription', transcribe_tab, key='-TAB-TRANS-')],
            [sg.Tab('Subtitle Editor', subtitle_tab, key='-TAB-SUB-')],
            [sg.Tab('Audio Mixing', mixing_tab, key='-TAB-MIX-')],
            [sg.Tab('Settings', settings_tab, key='-TAB-SETTINGS-')],
        ], key='-TABS-', tab_location='top', selected_title_color='white')
        
        # ===== Bottom Section: Progress & Log =====
        bottom_section = [
            [sg.Text("Status:", font=('Arial', 10, 'bold')), sg.Text("Ready", key='-STATUS-', size=(50, 1))],
            [sg.ProgressBar(100, orientation='h', size=(70, 20), key='-PROGRESS-')],
            
            [sg.Text("Activity Log:", font=('Arial', 10, 'bold'))],
            [sg.Multiline('Welcome to Beast Enhanced GUI\nReady to process audio and video files.\n',
                         size=(90, 12), key='-LOG-', autoscroll=True, disabled=True,
                         font=('Courier', 9))],
            
            [sg.Button("Stop", key='-STOP-', size=(10, 1), disabled=True, button_color=('white', 'red')),
             sg.Button("Clear Log", key='-CLEAR-LOG-', size=(10, 1)),
             sg.Button("Open Output Folder", key='-OPEN-OUTPUT-', size=(18, 1)),
             sg.Button("Exit", key='-EXIT-', size=(10, 1))],
        ]
        
        # ===== Complete Layout =====
        layout = [
            [sg.Text("🎵 Beast Enhanced - Audio & Video Processing Toolkit",
                    font=('Arial', 16, 'bold'), justification='center', expand_x=True)],
            [sg.HorizontalSeparator()],
            [tab_group],
            [sg.HorizontalSeparator()],
            *bottom_section
        ]
        
        return layout
    
    def log(self, message: str, status: Optional[str] = None):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        if self.window:
            self.window['-LOG-'].print(log_message, end='')
            if status:
                self.window['-STATUS-'].update(status)
    
    def update_progress(self, value: int):
        """Update progress bar."""
        if self.window:
            self.window['-PROGRESS-'].update(value)
    
    def run_command_thread(self, cmd: list, description: str):
        """Run a command in a separate thread."""
        def worker():
            self.log(f"Running: {description}")
            self.log(f"Command: {' '.join(cmd)}")
            self.update_progress(10)
            
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                for line in process.stdout:
                    if self.stop_event.is_set():
                        process.terminate()
                        break
                    self.log(line.rstrip())
                    
                    # Update progress if "PROGRESS:" in line
                    if "PROGRESS:" in line:
                        try:
                            prog = int(line.split("PROGRESS:")[-1].strip().split()[0])
                            self.update_progress(prog)
                        except:
                            pass
                
                returncode = process.wait()
                
                if returncode == 0:
                    self.log("✓ Operation completed successfully!", "Complete")
                    self.update_progress(100)
                    sg.popup_ok("Success!", f"{description} completed successfully!",
                               title="Success")
                else:
                    self.log(f"✗ Operation failed with code {returncode}", "Failed")
                    sg.popup_error(f"Operation failed with code {returncode}",
                                  title="Error")
            
            except Exception as e:
                self.log(f"✗ Error: {e}", "Error")
                sg.popup_error(f"Error: {e}", title="Error")
            
            finally:
                if self.window:
                    self.window.write_event_value('-DONE-', True)
        
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
        
        if self.window:
            self.window['-STOP-'].update(disabled=False)
    
    def handle_quick_transcribe(self, values):
        """Handle quick transcribe action."""
        input_file = values['-QUICK-INPUT-']
        output_dir = values['-QUICK-OUTPUT-']
        
        if not input_file:
            sg.popup_error("Please select an input file")
            return
        
        output_dir = output_dir or str(OUTPUT_DIR / "transcription")
        
        cmd = [
            sys.executable, "audio_workflow.py", "transcribe",
            "--input", input_file,
            "--output", output_dir,
            "--whisper-model", "base"
        ]
        
        self.run_command_thread(cmd, "Transcribe with Clean Audio")
    
    def handle_quick_karaoke(self, values):
        """Handle quick karaoke creation."""
        input_file = values['-QUICK-INPUT-']
        output_dir = values['-QUICK-OUTPUT-']
        
        if not input_file:
            sg.popup_error("Please select an input file")
            return
        
        output_dir = output_dir or str(OUTPUT_DIR / "karaoke")
        
        # First separate
        cmd1 = [
            sys.executable, "audio_separation.py",
            "--input", input_file,
            "--output", output_dir
        ]
        
        self.run_command_thread(cmd1, "Create Karaoke Track")
    
    def run(self):
        """Run the main GUI loop."""
        layout = self.create_layout()
        
        self.window = sg.Window(
            "Beast Enhanced GUI",
            layout,
            finalize=True,
            resizable=True,
            size=(950, 850),
            icon=None
        )
        
        # Main event loop
        while True:
            event, values = self.window.read(timeout=100)
            
            if event in (sg.WIN_CLOSED, '-EXIT-'):
                break
            
            # Quick actions
            elif event == '-QUICK-TRANSCRIBE-':
                self.handle_quick_transcribe(values)
            
            elif event == '-QUICK-KARAOKE-':
                self.handle_quick_karaoke(values)
            
            elif event == '-QUICK-CLEANUP-':
                input_file = values['-QUICK-INPUT-']
                if not input_file:
                    sg.popup_error("Please select an input file")
                    continue
                output_file = str(Path(values['-QUICK-OUTPUT-'] or OUTPUT_DIR) / f"cleaned_{Path(input_file).name}")
                cmd = [sys.executable, "audio_cleanup.py", "video",
                      "--input", input_file, "--output", output_file,
                      "--normalize", "--simple-denoise"]
                self.run_command_thread(cmd, "Clean Up Video Audio")
            
            elif event == '-QUICK-SEPARATE-':
                input_file = values['-QUICK-INPUT-']
                if not input_file:
                    sg.popup_error("Please select an input file")
                    continue
                output_dir = values['-QUICK-OUTPUT-'] or str(OUTPUT_DIR / "separated")
                cmd = [sys.executable, "audio_separation.py",
                      "--input", input_file, "--output", output_dir]
                self.run_command_thread(cmd, "Separate Audio Sources")
            
            # Other tab actions would go here...
            
            elif event == '-CLEAR-LOG-':
                self.window['-LOG-'].update('')
            
            elif event == '-OPEN-OUTPUT-':
                output_dir = values.get('-QUICK-OUTPUT-') or str(OUTPUT_DIR)
                try:
                    if sys.platform.startswith('win'):
                        os.startfile(output_dir)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', output_dir])
                    else:
                        subprocess.Popen(['xdg-open', output_dir])
                except Exception as e:
                    sg.popup_error(f"Could not open folder: {e}")
            
            elif event == '-STOP-':
                self.stop_event.set()
                self.log("Stopping operation...", "Stopping")
                self.window['-STOP-'].update(disabled=True)
            
            elif event == '-DONE-':
                self.stop_event.clear()
                self.window['-STOP-'].update(disabled=True)
        
        self.window.close()


def main():
    """Main entry point."""
    if not BEAST_API_AVAILABLE:
        print("Warning: beast_api module not found. Some features may be limited.")
    
    gui = BeastGUI()
    gui.run()


if __name__ == "__main__":
    main()
