#!/usr/bin/env python3
"""
Enhanced PySimpleGUI front-end.
- Saves persistent settings (~/.beast_config.json)
- Exposes voice, rate and output format controls
- Writes per-run timestamped logs to ./logs/
- Parses "PROGRESS:" lines in wrapper output to update progress bar
"""
import os
import sys
import subprocess
import threading
import queue
import time
import json
from datetime import datetime
import PySimpleGUI as sg
from beast_config import load_config, save_config, default_config
from voice_config import get_available_languages, get_language_display_name, get_voice

# Import network utilities for connectivity testing
try:
    from network_utils import test_edge_tts_connection
    NETWORK_UTILS_AVAILABLE = True
except ImportError:
    NETWORK_UTILS_AVAILABLE = False

SCRIPT = "auto_srt_all_tts_wrapper.py"

LOGS_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

def enqueue_output(pipe, q):
    try:
        for line in iter(pipe.readline, b''):
            if not line:
                break
            q.put(line.decode(errors='replace'))
    finally:
        pipe.close()

def find_script():
    candidates = [
        os.path.join(os.getcwd(), SCRIPT),
        os.path.join(os.getcwd(), "Modules", SCRIPT),
        os.path.join(os.getcwd(), "modules", SCRIPT),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def run_process(cmd, window, q, stop_event, log_path):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    with open(log_path, "w", encoding="utf-8") as lf:
        t = threading.Thread(target=enqueue_output, args=(proc.stdout, q), daemon=True)
        t.start()
        while proc.poll() is None and not stop_event.is_set():
            try:
                line = q.get(timeout=0.1)
            except Exception:
                line = None
            if line:
                lf.write(line)
                lf.flush()
                window.write_event_value('-LOG-', line)
        while not q.empty():
            l = q.get()
            lf.write(l)
            lf.flush()
            window.write_event_value('-LOG-', l)
        if proc.poll() is None:
            proc.terminate()
        rc = proc.wait()
        window.write_event_value('-DONE-', rc)

def safe_float(v, default):
    try:
        return float(v)
    except Exception:
        return default

def main():
    cfg = load_config()

    # Get available languages and format them for display
    available_langs = get_available_languages()
    lang_display_list = [f"{lang} - {get_language_display_name(lang)}" for lang in available_langs]
    
    # Get current profile settings
    current_profile = cfg.get("current_profile", "User 1")
    profiles = cfg.get("profiles", default_config["profiles"])
    profile_list = list(profiles.keys())
    profile_data = profiles.get(current_profile, default_config["profiles"]["User 1"])
    
    current_language = profile_data.get("language", "en-US")
    current_gender = profile_data.get("gender", "female")
    voice_index = profile_data.get("voice_index", 0)
    
    # Find the display string for current language
    current_lang_display = f"{current_language} - {get_language_display_name(current_language)}"
    
    sg.theme(cfg.get("theme", "SystemDefault"))
    layout = [
        [sg.Text('Beast TTS / auto-SRT GUI', font=('Segoe UI', 14)), sg.Push(), sg.Button('Test Connection', key='-TEST_CONN-', size=(14, 1))],
        [sg.HorizontalSeparator()],
        [sg.Text('User Profile', font=('Segoe UI', 11, 'bold'))],
        [sg.Text('Profile'), sg.Combo(values=profile_list, default_value=current_profile, key='-PROFILE-', enable_events=True, size=(15, 1)),
         sg.Button('Add Profile', key='-ADD_PROFILE-', size=(10, 1)),
         sg.Button('Remove Profile', key='-REMOVE_PROFILE-', size=(12, 1))],
        [sg.Text('Language'), sg.Combo(values=lang_display_list, default_value=current_lang_display, key='-LANGUAGE-', enable_events=True, size=(30, 1)),
         sg.Text('Gender'), sg.Combo(values=["female", "male"], default_value=current_gender, key='-GENDER-', enable_events=True, size=(10, 1))],
        [sg.HorizontalSeparator()],
        [sg.Text('Input/Output Settings', font=('Segoe UI', 11, 'bold'))],
        [sg.Text('Input file or folder'), sg.Input(default_text=cfg.get("last_input",""), key='-INPUT-'), sg.FolderBrowse(), sg.FileBrowse(file_types=(("SRT/Video","*.srt;*.mp4;*.mkv;*.mov"),))],
        [sg.Text('Output folder'), sg.Input(default_text=cfg.get("last_output",""), key='-OUTPUT-'), sg.FolderBrowse()],
        [sg.Text('Voice'), sg.Combo(values=cfg.get("voices", ["default"]), default_value=cfg.get("last_voice","default"), key='-VOICE-'),
         sg.Text('Format'), sg.Combo(values=["mp3","wav"], default_value=cfg.get("last_format","mp3"), key='-FMT-'),
         sg.Text('Rate'), sg.Slider(range=(0.5,2.0), default_value=cfg.get("last_rate",1.0), resolution=0.05, orientation='h', size=(20,15), key='-RATE-')],
        [sg.Text('Extra args (optional)'), sg.Input(key='-ARGS-')],
        [sg.Button('Run', key='-RUN-'), sg.Button('Stop', key='-STOP-', disabled=True), sg.Button('Open Output', key='-OPEN-', disabled=True), sg.Button('Open Log', key='-OPENLOG-', disabled=True), sg.Button('Exit')],
        [sg.ProgressBar(100, orientation='h', size=(60, 10), key='-PROG-')],
        [sg.Multiline('', size=(100, 18), key='-OUTPUT-', autoscroll=True, disabled=True)]
    ]

    window = sg.Window('Beast GUI', layout, finalize=True, resizable=True)
    q = queue.Queue()
    worker = None
    stop_event = threading.Event()
    current_log = None

    script_path = find_script()
    if not script_path:
        window['-OUTPUT-'].update("Warning: wrapper script not found. Make sure auto_srt_all_tts_wrapper.py exists in repo root or Modules/\n")

    while True:
        event, values = window.read(timeout=100)
        if event in (sg.WIN_CLOSED, 'Exit'):
            if worker and worker.is_alive():
                stop_event.set()
                worker.join(timeout=2)
            break
        
        if event == '-PROFILE-':
            # Profile changed - update language and gender
            selected_profile = values['-PROFILE-']
            if selected_profile in cfg.get("profiles", {}):
                profile_data = cfg["profiles"][selected_profile]
                new_lang = profile_data.get("language", "en-US")
                new_gender = profile_data.get("gender", "female")
                new_lang_display = f"{new_lang} - {get_language_display_name(new_lang)}"
                window['-LANGUAGE-'].update(value=new_lang_display)
                window['-GENDER-'].update(value=new_gender)
                cfg["current_profile"] = selected_profile
                save_config(cfg)
        
        if event == '-ADD_PROFILE-':
            # Add a new profile
            profile_name = sg.popup_get_text('Enter a name for the new profile:', 'Add Profile')
            if profile_name and profile_name.strip():
                profile_name = profile_name.strip()
                if "profiles" not in cfg:
                    cfg["profiles"] = {}
                if profile_name in cfg["profiles"]:
                    sg.popup_error(f'Profile "{profile_name}" already exists.')
                else:
                    # Create new profile with default settings
                    cfg["profiles"][profile_name] = {
                        "language": "en-US",
                        "gender": "female",
                        "voice_index": 0
                    }
                    cfg["current_profile"] = profile_name
                    save_config(cfg)
                    # Update UI
                    profile_list = list(cfg["profiles"].keys())
                    window['-PROFILE-'].update(values=profile_list, value=profile_name)
                    window['-LANGUAGE-'].update(value="en-US - English (US)")
                    window['-GENDER-'].update(value="female")
                    sg.popup_ok(f'Profile "{profile_name}" created successfully.')
        
        if event == '-REMOVE_PROFILE-':
            # Remove the current profile
            current_profile = cfg.get("current_profile", "User 1")
            profiles = cfg.get("profiles", {})
            
            if len(profiles) <= 1:
                sg.popup_error('Cannot remove the last profile. At least one profile must exist.')
            elif current_profile not in profiles:
                sg.popup_error(f'Profile "{current_profile}" not found.')
            else:
                confirm = sg.popup_yes_no(f'Are you sure you want to remove profile "{current_profile}"?', 'Confirm Removal')
                if confirm == 'Yes':
                    del cfg["profiles"][current_profile]
                    # Switch to another profile
                    remaining_profiles = list(cfg["profiles"].keys())
                    if remaining_profiles:
                        new_profile = remaining_profiles[0]
                        cfg["current_profile"] = new_profile
                        profile_data = cfg["profiles"][new_profile]
                        new_lang = profile_data.get("language", "en-US")
                        new_gender = profile_data.get("gender", "female")
                        new_lang_display = f"{new_lang} - {get_language_display_name(new_lang)}"
                        window['-PROFILE-'].update(values=remaining_profiles, value=new_profile)
                        window['-LANGUAGE-'].update(value=new_lang_display)
                        window['-GENDER-'].update(value=new_gender)
                    save_config(cfg)
                    sg.popup_ok(f'Profile "{current_profile}" removed.')
        
        if event == '-TEST_CONN-':
            # Test edge-tts connectivity
            if not NETWORK_UTILS_AVAILABLE:
                sg.popup_error(
                    'Network utilities not available.\n\n'
                    'Make sure network_utils.py is in the same directory as this script.',
                    title='Network Test Unavailable'
                )
            else:
                # Show testing message
                window['-OUTPUT-'].update('Testing connection to edge-tts service...\n')
                window.refresh()
                
                try:
                    results = test_edge_tts_connection()
                    
                    # Build message
                    msg = "Connection Test Results\n" + "="*50 + "\n\n"
                    msg += f"Internet Connected: {'✓ Yes' if results['internet_connected'] else '✗ No'}\n"
                    msg += f"Edge-TTS Accessible: {'✓ Yes' if results['edge_tts_accessible'] else '✗ No'}\n\n"
                    
                    if results['error_message']:
                        msg += f"Error: {results['error_message']}\n\n"
                    
                    if results['recommendations']:
                        msg += "Recommendations:\n"
                        for rec in results['recommendations']:
                            msg += f"  • {rec}\n"
                    
                    window['-OUTPUT-'].update(msg)
                    
                    if results['edge_tts_accessible']:
                        sg.popup_ok(
                            '✓ Connection Successful!\n\n'
                            'Edge-TTS service is accessible.\n'
                            'You can proceed with TTS generation.',
                            title='Connection Test - Success'
                        )
                    else:
                        sg.popup_error(
                            '✗ Connection Failed\n\n'
                            f'{results["error_message"]}\n\n'
                            'See the output window for recommendations.\n'
                            'For detailed help, see FIREWALL_TROUBLESHOOTING.md',
                            title='Connection Test - Failed'
                        )
                except Exception as e:
                    error_msg = f"Test failed with error: {str(e)}"
                    window['-OUTPUT-'].update(error_msg)
                    sg.popup_error(error_msg, title='Connection Test Error')
        
        if event == '-LANGUAGE-':
            # Language changed - update profile
            lang_display = values['-LANGUAGE-']
            if lang_display and ' - ' in lang_display:
                lang_code = lang_display.split(' - ')[0]
                current_profile = cfg.get("current_profile", "User 1")
                if "profiles" not in cfg:
                    cfg["profiles"] = default_config["profiles"].copy()
                if current_profile not in cfg["profiles"]:
                    cfg["profiles"][current_profile] = {"language": "en-US", "gender": "female", "voice_index": 0}
                cfg["profiles"][current_profile]["language"] = lang_code
                # Update the voice combo to show the selected voice
                gender = cfg["profiles"][current_profile].get("gender", "female")
                voice_name = get_voice(lang_code, gender, 0)
                window['-VOICE-'].update(value=voice_name)
                save_config(cfg)
        
        if event == '-GENDER-':
            # Gender changed - update profile
            new_gender = values['-GENDER-']
            current_profile = cfg.get("current_profile", "User 1")
            if "profiles" not in cfg:
                cfg["profiles"] = default_config["profiles"].copy()
            if current_profile not in cfg["profiles"]:
                cfg["profiles"][current_profile] = {"language": "en-US", "gender": "female", "voice_index": 0}
            cfg["profiles"][current_profile]["gender"] = new_gender
            # Update the voice combo to show the selected voice
            lang_code = cfg["profiles"][current_profile].get("language", "en-US")
            voice_name = get_voice(lang_code, new_gender, 0)
            window['-VOICE-'].update(value=voice_name)
            save_config(cfg)
        
        if event == '-RUN-':
            input_path = values['-INPUT-'] or ''
            output_path = values['-OUTPUT-'] or ''
            args_extra = values['-ARGS-'] or ''
            voice = values['-VOICE-'] or ''
            fmt = values['-FMT-'] or 'mp3'
            rate = safe_float(values['-RATE-'], 1.0)
            
            # Get voice from profile if not explicitly set
            if not voice or voice == "default":
                current_profile = cfg.get("current_profile", "User 1")
                profile_data = cfg.get("profiles", {}).get(current_profile, {})
                lang_code = profile_data.get("language", "en-US")
                gender = profile_data.get("gender", "female")
                voice_index = profile_data.get("voice_index", 0)
                voice = get_voice(lang_code, gender, voice_index)
            
            if not input_path:
                sg.popup_ok('Please select an input file or folder first.')
                continue

            cfg['last_input'] = input_path
            cfg['last_output'] = output_path
            cfg['last_voice'] = voice
            cfg['last_format'] = fmt
            cfg['last_rate'] = rate
            save_config(cfg)

            cmd = [sys.executable, script_path or SCRIPT, '--input', input_path, '--format', fmt, '--rate', str(rate)]
            if output_path:
                cmd += ['--output', output_path]
            if voice:
                cmd += ['--voice', voice]
            if args_extra:
                cmd += args_extra.split()

            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            current_log = os.path.join(LOGS_DIR, f"run_{timestamp}.log")
            window['-OUTPUT-'].update('')
            window['-PROG-'].update(0)
            window['-RUN-'].update(disabled=True)
            window['-STOP-'].update(disabled=False)
            window['-OPEN-'].update(disabled=True)
            window['-OPENLOG-'].update(disabled=True)
            stop_event.clear()
            worker = threading.Thread(target=run_process, args=(cmd, window, q, stop_event, current_log), daemon=True)
            worker.start()
        if event == '-STOP-':
            stop_event.set()
            window['-STOP-'].update(disabled=True)
        if event == '-LOG-':
            txt = values[event]
            window['-OUTPUT-'].update(window['-OUTPUT-'].get() + txt)
            if "PROGRESS:" in txt:
                try:
                    p = int(txt.split("PROGRESS:")[-1].strip().split()[0])
                    window['-PROG-'].update(min(max(p,0),100))
                except Exception:
                    pass
        if event == '-DONE-':
            rc = values[event]
            window['-RUN-'].update(disabled=False)
            window['-STOP-'].update(disabled=True)
            window['-OPEN-'].update(disabled=False)
            window['-OPENLOG-'].update(disabled=False)
            if rc == 0:
                sg.popup_ok('Process finished successfully.')
            else:
                sg.popup_error(f'Process exited with code {rc}. See log for details.')
        if event == '-OPEN-':
            inp = values['-OUTPUT-'] or values['-INPUT-'] or ''
            candidate = os.path.abspath(inp)
            if os.path.isfile(candidate):
                candidate = os.path.dirname(candidate)
            try:
                if sys.platform.startswith('win'):
                    os.startfile(candidate)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', candidate])
                else:
                    subprocess.Popen(['xdg-open', candidate])
            except Exception as e:
                sg.popup_error(f'Could not open folder: {e}')
        if event == '-OPENLOG-':
            if current_log and os.path.exists(current_log):
                try:
                    if sys.platform.startswith('win'):
                        os.startfile(current_log)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', current_log])
                    else:
                        subprocess.Popen(['xdg-open', current_log])
                except Exception as e:
                    sg.popup_error(f'Could not open log: {e}')

    window.close()

if __name__ == '__main__':
    main()
