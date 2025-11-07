#!/usr/bin/env python3
"""
Enhanced PySimpleGUI front-end.
- Saves persistent settings (~/.beast_config.json)
- Exposes voice, rate and output format controls
- Writes per-run timestamped logs to ./logs/
- Parses "PROGRESS:" lines in wrapper output to update progress bar
- Download tab for downloading videos from URLs
"""
import os
import sys
import subprocess
import threading
import queue
from datetime import datetime
import PySimpleGUI as sg
from beast_config import load_config, save_config

SCRIPT = "auto_srt_all_tts_wrapper.py"
DOWNLOAD_SCRIPT = "download_beast.py"

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
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1)
    with open(log_path, "w", encoding="utf-8") as lf:
        t = threading.Thread(
            target=enqueue_output, args=(
                proc.stdout, q), daemon=True)
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
            log_line = q.get()
            lf.write(log_line)
            lf.flush()
            window.write_event_value('-LOG-', log_line)
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
        [sg.Text('Input file or folder'), sg.Input(default_text=cfg.get("last_input", ""), key='-INPUT-'), sg.FolderBrowse(), sg.FileBrowse(file_types=(("SRT/Video", "*.srt;*.mp4;*.mkv;*.mov"),))],
        [sg.Text('Output folder'), sg.Input(default_text=cfg.get("last_output", ""), key='-OUTPUT-'), sg.FolderBrowse()],
        [sg.Text('Voice'), sg.Combo(values=cfg.get("voices", ["default"]), default_value=cfg.get("last_voice", "default"), key='-VOICE-'),
         sg.Text('Format'), sg.Combo(values=["mp3", "wav"], default_value=cfg.get("last_format", "mp3"), key='-FMT-'),
         sg.Text('Rate'), sg.Slider(range=(0.5, 2.0), default_value=cfg.get("last_rate", 1.0), resolution=0.05, orientation='h', size=(20, 15), key='-RATE-')],
        [sg.Text('Extra args (optional)'), sg.Input(key='-ARGS-')],
        [sg.Button('Run', key='-RUN-'), sg.Button('Stop', key='-STOP-', disabled=True), sg.Button('Open Output', key='-OPEN-', disabled=True), sg.Button('Open Log', key='-OPENLOG-', disabled=True)],
        [sg.ProgressBar(100, orientation='h', size=(60, 10), key='-PROG-')],
        [sg.Multiline('', size=(100, 12), key='-TTS-OUTPUT-', autoscroll=True, disabled=True)]
    ]

    # Download Tab
    download_tab = [
        [sg.Text('Video URL'), sg.Input(default_text=cfg.get("last_url", ""), key='-URL-', size=(70, 1))],
        [sg.Text('Download folder'), sg.Input(default_text=cfg.get("last_download_dir", "downloads"), key='-DL-OUTPUT-'), sg.FolderBrowse()],
        [sg.Checkbox('Audio only', default=cfg.get("audio_only", False), key='-AUDIO-ONLY-'),
         sg.Text('Audio format'), sg.Combo(values=["mp3", "wav", "flac", "m4a"], default_value=cfg.get("audio_format", "mp3"), key='-AUDIO-FMT-')],
        [sg.Checkbox('Download subtitles', default=cfg.get("download_subs", False), key='-DL-SUBS-'),
         sg.Checkbox('Auto-generated subs', default=False, key='-AUTO-SUBS-'),
         sg.Checkbox('Embed subtitles', default=False, key='-EMBED-SUBS-')],
        [sg.Checkbox('Download as playlist', default=False, key='-PLAYLIST-'),
         sg.Text('Max videos'), sg.Input(default_text='', key='-MAX-VIDEOS-', size=(5, 1))],
        [sg.Button('Download', key='-DOWNLOAD-'), sg.Button('Stop Download', key='-STOP-DL-', disabled=True), sg.Button('Open Download Folder', key='-OPEN-DL-')],
        [sg.ProgressBar(100, orientation='h', size=(60, 10), key='-DL-PROG-')],
        [sg.Multiline('', size=(100, 12), key='-DL-OUTPUT-', autoscroll=True, disabled=True)]
    ]

    layout = [
        [sg.Text('Beast - Video Processing Toolkit', font=('Segoe UI', 14))],
        [sg.TabGroup([
            [sg.Tab('TTS / Auto-SRT', tts_tab), sg.Tab('Download', download_tab)]
        ])],
        [sg.Button('Exit')]
    ]

    window = sg.Window('Beast GUI', layout, finalize=True, resizable=True)
    q = queue.Queue()
    worker = None
    stop_event = threading.Event()
    current_log = None
    active_process = None  # Track which process is running: 'tts' or 'download'

    script_path = find_script()
    download_script = os.path.join(os.getcwd(), DOWNLOAD_SCRIPT)
    if not script_path:
        window['-TTS-OUTPUT-'].update(
            "Warning: wrapper script not found. Make sure auto_srt_all_tts_wrapper.py exists in repo root or Modules/\n")

    while True:
        event, values = window.read(timeout=100)
        if event in (sg.WIN_CLOSED, 'Exit'):
            if worker and worker.is_alive():
                stop_event.set()
                worker.join(timeout=2)
            break
        if event == '-RUN-':
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

            cmd = [
                sys.executable,
                script_path or SCRIPT,
                '--input',
                input_path,
                '--format',
                fmt,
                '--rate',
                str(rate)]
            if output_path:
                cmd += ['--output', output_path]
            if voice:
                cmd += ['--voice', voice]
            if args_extra:
                cmd += args_extra.split()

            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            current_log = os.path.join(LOGS_DIR, f"run_{timestamp}.log")
            window['-TTS-OUTPUT-'].update('')
            window['-PROG-'].update(0)
            window['-RUN-'].update(disabled=True)
            window['-STOP-'].update(disabled=False)
            window['-OPEN-'].update(disabled=True)
            window['-OPENLOG-'].update(disabled=True)
            stop_event.clear()
            active_process = 'tts'
            worker = threading.Thread(
                target=run_process,
                args=(
                    cmd,
                    window,
                    q,
                    stop_event,
                    current_log),
                daemon=True)
            worker.start()
        if event == '-DOWNLOAD-':
            url = values['-URL-'] or ''
            download_dir = values['-DL-OUTPUT-'] or 'downloads'
            audio_only = values['-AUDIO-ONLY-']
            audio_fmt = values['-AUDIO-FMT-'] or 'mp3'
            download_subs = values['-DL-SUBS-']
            auto_subs = values['-AUTO-SUBS-']
            embed_subs = values['-EMBED-SUBS-']
            is_playlist = values['-PLAYLIST-']
            max_videos = values['-MAX-VIDEOS-'] or ''

            if not url:
                sg.popup_ok('Please enter a video URL first.')
                continue

            if not os.path.exists(download_script):
                sg.popup_error(f'Download script not found: {download_script}')
                continue

            # Save config
            cfg['last_url'] = url
            cfg['last_download_dir'] = download_dir
            cfg['audio_only'] = audio_only
            cfg['audio_format'] = audio_fmt
            cfg['download_subs'] = download_subs
            save_config(cfg)

            # Build command
            cmd = [
                sys.executable,
                download_script,
                url,
                '--output',
                download_dir]
            if audio_only:
                cmd += ['--audio-only', '--audio-format', audio_fmt]
            if download_subs:
                cmd += ['--subtitles']
            if auto_subs:
                cmd += ['--auto-subs']
            if embed_subs:
                cmd += ['--embed-subs']
            if is_playlist:
                cmd += ['--playlist']
                if max_videos:
                    try:
                        cmd += ['--max', str(int(max_videos))]
                    except ValueError:
                        pass

            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            current_log = os.path.join(LOGS_DIR, f"download_{timestamp}.log")
            window['-DL-OUTPUT-'].update('')
            window['-DL-PROG-'].update(0)
            window['-DOWNLOAD-'].update(disabled=True)
            window['-STOP-DL-'].update(disabled=False)
            stop_event.clear()
            active_process = 'download'
            worker = threading.Thread(
                target=run_process,
                args=(
                    cmd,
                    window,
                    q,
                    stop_event,
                    current_log),
                daemon=True)
            worker.start()
        if event == '-STOP-':
            stop_event.set()
            window['-STOP-'].update(disabled=True)
        if event == '-STOP-DL-':
            stop_event.set()
            window['-STOP-DL-'].update(disabled=True)
        if event == '-LOG-':
            txt = values[event]
            # Route logs based on active process
            if active_process == 'download':
                window['-DL-OUTPUT-'].update(window['-DL-OUTPUT-'].get() + txt)
            else:
                window['-TTS-OUTPUT-'].update(
                    window['-TTS-OUTPUT-'].get() + txt)
            if "PROGRESS:" in txt:
                try:
                    p = int(txt.split("PROGRESS:")[-1].strip().split()[0])
                    # Update only the relevant progress bar
                    if active_process == 'download':
                        window['-DL-PROG-'].update(min(max(p, 0), 100))
                    else:
                        window['-PROG-'].update(min(max(p, 0), 100))
                except Exception:
                    pass
        if event == '-DONE-':
            rc = values[event]
            active_process = None  # Reset active process
            window['-RUN-'].update(disabled=False)
            window['-STOP-'].update(disabled=True)
            window['-DOWNLOAD-'].update(disabled=False)
            window['-STOP-DL-'].update(disabled=True)
            window['-OPEN-'].update(disabled=False)
            window['-OPENLOG-'].update(disabled=False)
            if rc == 0:
                sg.popup_ok('Process finished successfully.')
            else:
                sg.popup_error(
                    f'Process exited with code {rc}. See log for details.')
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
        if event == '-OPEN-DL-':
            download_dir = values['-DL-OUTPUT-'] or 'downloads'
            candidate = os.path.abspath(download_dir)
            try:
                if sys.platform.startswith('win'):
                    os.startfile(candidate)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', candidate])
                else:
                    subprocess.Popen(['xdg-open', candidate])
            except Exception as e:
                sg.popup_error(f'Could not open folder: {e}')

    window.close()


if __name__ == '__main__':
    main()
