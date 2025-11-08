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

    sg.theme(cfg.get("theme", "SystemDefault"))
    
    # TTS/Auto-SRT Tab
    tts_tab = [
        [sg.Text('Input file or folder'), sg.Input(default_text=cfg.get("last_input",""), key='-INPUT-'), sg.FolderBrowse(), sg.FileBrowse(file_types=(("SRT/Video","*.srt;*.mp4;*.mkv;*.mov"),))],
        [sg.Text('Output folder'), sg.Input(default_text=cfg.get("last_output",""), key='-OUTPUT-'), sg.FolderBrowse()],
        [sg.Text('Voice'), sg.Combo(values=cfg.get("voices", ["default"]), default_value=cfg.get("last_voice","default"), key='-VOICE-'),
         sg.Text('Format'), sg.Combo(values=["mp3","wav"], default_value=cfg.get("last_format","mp3"), key='-FMT-'),
         sg.Text('Rate'), sg.Slider(range=(0.5,2.0), default_value=cfg.get("last_rate",1.0), resolution=0.05, orientation='h', size=(20,15), key='-RATE-')],
        [sg.Text('Extra args (optional)'), sg.Input(key='-ARGS-')],
    ]
    
    # Translation Tab
    common_langs = ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh-CN", "ar", "hi"]
    translation_tab = [
        [sg.Text('Input SRT file'), sg.Input(default_text="", key='-TRANS-INPUT-'), sg.FileBrowse(file_types=(("SRT Files","*.srt"),))],
        [sg.Text('Output SRT file'), sg.Input(default_text="", key='-TRANS-OUTPUT-'), sg.FileSaveAs(file_types=(("SRT Files","*.srt"),))],
        [sg.Text('Source Language'), sg.Combo(values=common_langs, default_value=cfg.get("translation_source_lang", "auto"), key='-TRANS-SOURCE-'),
         sg.Text('Target Language'), sg.Combo(values=common_langs, default_value=cfg.get("translation_target_lang", "en"), key='-TRANS-TARGET-')],
        [sg.Checkbox('Use cache', default=cfg.get("translation_cache_enabled", True), key='-TRANS-CACHE-')],
        [sg.Text('Translation will process the SRT file and create a translated version.')],
    ]
    
    # Main layout with tabs
    layout = [
        [sg.Text('Beast - TTS, Translation & Subtitles', font=('Segoe UI', 14))],
        [sg.TabGroup([[
            sg.Tab('TTS / Auto-SRT', tts_tab),
            sg.Tab('Translation', translation_tab)
        ]])],
        [sg.Button('Run', key='-RUN-'), sg.Button('Stop', key='-STOP-', disabled=True), sg.Button('Open Output', key='-OPEN-', disabled=True), sg.Button('Open Log', key='-OPENLOG-', disabled=True), sg.Button('Exit')],
        [sg.ProgressBar(100, orientation='h', size=(60, 10), key='-PROG-')],
        [sg.Multiline('', size=(100, 18), key='-OUTPUTLOG-', autoscroll=True, disabled=True)]
    ]

    window = sg.Window('Beast GUI', layout, finalize=True, resizable=True)
    q = queue.Queue()
    worker = None
    stop_event = threading.Event()
    current_log = None

    script_path = find_script()
    if not script_path:
        window['-OUTPUTLOG-'].update("Warning: wrapper script not found. Make sure auto_srt_all_tts_wrapper.py exists in repo root or Modules/\n")

    while True:
        event, values = window.read(timeout=100)
        if event in (sg.WIN_CLOSED, 'Exit'):
            if worker and worker.is_alive():
                stop_event.set()
                worker.join(timeout=2)
            break
        if event == '-RUN-':
            # Check if we're in translation tab
            trans_input = values.get('-TRANS-INPUT-', '').strip()
            trans_output = values.get('-TRANS-OUTPUT-', '').strip()
            
            if trans_input and trans_output:
                # Translation mode
                source_lang = values['-TRANS-SOURCE-'] or 'auto'
                target_lang = values['-TRANS-TARGET-'] or 'en'
                use_cache = values['-TRANS-CACHE-']
                
                if not os.path.exists(trans_input):
                    sg.popup_error('Input file does not exist.')
                    continue
                
                cfg['translation_source_lang'] = source_lang
                cfg['translation_target_lang'] = target_lang
                cfg['translation_cache_enabled'] = use_cache
                save_config(cfg)
                
                # Build translation command
                translation_script = os.path.join(os.getcwd(), "translation_run.py")
                if not os.path.exists(translation_script):
                    sg.popup_error('translation_run.py not found in repository root.')
                    continue
                
                cmd = [sys.executable, translation_script, 
                       '--input', trans_input, 
                       '--output', trans_output,
                       '--source-lang', source_lang,
                       '--target-lang', target_lang]
                if not use_cache:
                    cmd.append('--no-cache')
                
                timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                current_log = os.path.join(LOGS_DIR, f"translation_{timestamp}.log")
                window['-OUTPUTLOG-'].update(f"Starting translation: {trans_input} -> {trans_output}\n")
                window['-PROG-'].update(0)
                window['-RUN-'].update(disabled=True)
                window['-STOP-'].update(disabled=False)
                window['-OPEN-'].update(disabled=True)
                window['-OPENLOG-'].update(disabled=True)
                stop_event.clear()
                worker = threading.Thread(target=run_process, args=(cmd, window, q, stop_event, current_log), daemon=True)
                worker.start()
            else:
                # TTS/Auto-SRT mode
                input_path = values['-INPUT-'] or ''
                output_path = values['-OUTPUT-'] or ''
                args_extra = values['-ARGS-'] or ''
                voice = values['-VOICE-'] or ''
                fmt = values['-FMT-'] or 'mp3'
                rate = safe_float(values['-RATE-'], 1.0)
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
                window['-OUTPUTLOG-'].update('')
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
            window['-OUTPUTLOG-'].update(window['-OUTPUTLOG-'].get() + txt)
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
