"""LinguaLive v1.2 — Japanese to English desktop audio captions.
Windows WASAPI or Linux PulseAudio/PipeWire-Pulse. No audio files are saved.
Use the included setup launcher for your operating system.
"""
import argparse
import math
import queue
import threading
import tkinter as tk

import traceback
import platform
import subprocess
from contextlib import contextmanager
from pathlib import Path
import atexit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large-v3'], default='small')
parser.add_argument('--gpu', action='store_true', help='Use CUDA (requires compatible cuBLAS and cuDNN libraries)')
parser.add_argument('--seconds', type=float, default=5.0, help='Seconds per audio block (3-15)')
parser.add_argument('--source', help='Linux only: PulseAudio source name (default: monitor of default output)')
args = parser.parse_args()
if not 3 <= args.seconds <= 15:
    parser.error('--seconds must be between 3 and 15')

stop = threading.Event()
audio = queue.Queue(maxsize=2)
updates = queue.Queue()


def push_latest(q, item):
    try:
        q.put_nowait(item)
    except queue.Full:
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        try:
            q.put_nowait(item)
        except queue.Full:
            pass


@contextmanager
def windows_capture():
    import pyaudiowpatch as pa
    with pa.PyAudio() as p:
        device = p.get_default_wasapi_loopback()
        rate = int(device['defaultSampleRate'])
        channels = int(device['maxInputChannels'])
        target = int(rate * args.seconds) * channels * 2
        pending = bytearray()

        def callback(data, frame_count, time_info, status_flags):
            if stop.is_set():
                return (None, pa.paComplete)
            pending.extend(data)
            while len(pending) >= target:
                push_latest(audio, bytes(pending[:target]))
                del pending[:target]
            return (None, pa.paContinue)

        with p.open(format=pa.paInt16, channels=channels, rate=rate,
                    input=True, input_device_index=int(device['index']),
                    frames_per_buffer=1024, stream_callback=callback):
            yield rate, channels, str(device['name']), None


@contextmanager
def linux_capture():
    # PulseAudio and PipeWire's PulseAudio-compatible server both expose
    # output monitor sources. No microphone is selected by default.
    if args.source:
        source = args.source
    else:
        sink = subprocess.check_output(['pactl', 'get-default-sink'], text=True).strip()
        if not sink:
            raise RuntimeError('No default audio output found. Check your sound settings.')
        source = sink + '.monitor'
    rate, channels = 16000, 1
    target = int(rate * args.seconds) * channels * 2
    process = subprocess.Popen([
        'parec', '--raw', '--device=' + source, '--format=s16le',
        '--rate=16000', '--channels=1'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def terminate():
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            except ProcessLookupError:
                pass

    atexit.register(terminate)
    errors = queue.Queue()

    def reader():
        try:
            while not stop.is_set():
                data = process.stdout.read(target)
                if len(data) != target:
                    if not stop.is_set():
                        details = process.stderr.read().decode('utf-8', errors='replace').strip()
                        errors.put(RuntimeError('Linux audio capture ended: ' + (details or source)))
                    return
                push_latest(audio, data)
        except Exception as exc:
            if not stop.is_set():
                errors.put(exc)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        yield rate, channels, source, errors
    finally:
        terminate()
        thread.join(timeout=2)
        atexit.unregister(terminate)
        if not thread.is_alive():
            process.stdout.close()
            process.stderr.close()


def worker():
    try:
        updates.put(('status', 'Loading audio and AI libraries…'))
        import numpy as np
        from scipy.signal import resample_poly
        from faster_whisper import WhisperModel
        system = platform.system()
        if system not in ('Windows', 'Linux'):
            raise RuntimeError('This release supports Windows and Linux only.')
        updates.put(('status', 'Loading model (first run downloads it)…'))
        model = WhisperModel(args.model, device='cuda' if args.gpu else 'cpu',
                             compute_type='int8_float16' if args.gpu else 'int8')
        if stop.is_set():
            return
        capture = windows_capture if system == 'Windows' else linux_capture
        with capture() as (rate, channels, name, errors):
            updates.put(('status', 'Listening: ' + name))
            gcd = math.gcd(rate, 16000)
            while not stop.is_set():
                if errors is not None:
                    try:
                        exc = errors.get_nowait()
                    except queue.Empty:
                        pass
                    else:
                        raise exc
                try:
                    data = audio.get(timeout=0.25)
                except queue.Empty:
                    continue
                samples = np.frombuffer(data, dtype='<i2').reshape(-1, channels)
                samples = samples.astype(np.float32).mean(axis=1) / 32768.0
                if np.sqrt(np.mean(samples ** 2)) < 0.0005:
                    continue
                if rate != 16000:
                    samples = resample_poly(samples, 16000 // gcd, rate // gcd).astype(np.float32)
                segments, _ = model.transcribe(samples, language='ja', task='translate',
                                               beam_size=3, vad_filter=True,
                                               condition_on_previous_text=False)
                caption = ' '.join(s.text.strip() for s in segments if s.text.strip())
                if caption:
                    updates.put(('caption', caption))
    except Exception as exc:
        if stop.is_set():
            return
        updates.put(('status', 'Error — details in live_captions_error.log'))
        updates.put(('caption', str(exc)))
        traceback.print_exc()
        try:
            Path(__file__).with_name('live_captions_error.log').write_text(traceback.format_exc(), encoding='utf-8')
        except OSError:
            pass


root = tk.Tk()
root.title('LinguaLive • Japanese → English')
root.attributes('-topmost', True)
root.configure(bg='#151515')
width = min(850, root.winfo_screenwidth() - 60)
root.geometry(f'{width}x160+{(root.winfo_screenwidth()-width)//2}+{max(0,root.winfo_screenheight()-260)}')
root.minsize(350, 110)
status_text = tk.StringVar(value='Starting…')
caption_text = tk.StringVar(value='Play Japanese speech through your default audio device.')
tk.Label(root, textvariable=status_text, bg='#151515', fg='#b8b8b8',
         font=('Segoe UI', 9), anchor='w').pack(fill='x', padx=14, pady=(8, 0))
label = tk.Label(root, textvariable=caption_text, bg='#151515', fg='white',
                 font=('Segoe UI', 17), justify='center', wraplength=width-30)
label.pack(fill='both', expand=True, padx=14, pady=8)
def resize(event):
    if event.widget is root:
        label.configure(wraplength=max(300, event.width-30))
root.bind('<Configure>', resize)

def poll():
    while True:
        try:
            kind, value = updates.get_nowait()
        except queue.Empty:
            break
        if kind == 'caption':
            caption_text.set(value)
        else:
            status_text.set(value)
    if not stop.is_set():
        root.after(100, poll)

def close():
    stop.set()
    root.destroy()

root.protocol('WM_DELETE_WINDOW', close)
threading.Thread(target=worker, daemon=True).start()
root.after(100, poll)
root.mainloop()
