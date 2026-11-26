# LinguaLive v1.2 — Japanese → English live captions

A small desktop app that translates Japanese speech from your computer's audio into floating English subtitles. Works with Twitch, YouTube and other audio-playing apps. No browser extension, account or API key required. Audio is processed locally; the app does not save audio recordings or send audio to a translation API. The initial setup downloads dependencies from PyPI and a Whisper model from Hugging Face. This is a source-code bundle with automatic setup, not a standalone EXE or offline installer.

## Windows 10 / 11 (64-bit x86)

1. Extract the entire ZIP into a normal writable folder.
2. Install 64-bit Python 3.13, 3.12 or 3.11 if needed: https://www.python.org/downloads/ (include the Python launcher and Tcl/Tk). Python 3.13 is preferred. You can keep other Python versions installed.
3. Double-click `Start_Windows.bat`. It selects a supported Python version, creates a private virtual environment, installs dependencies, and starts the app. No administrator privileges needed. Don't double-click the `.py` file, which might use the wrong Python version.
4. Wait for the first model download; then play Japanese audio on your default Windows playback device.
5. For future sessions, double-click the same launcher. Close the caption window to stop.

## Linux (experimental, 64-bit x86 desktop)

Requires PulseAudio or PipeWire with its PulseAudio compatibility service, `pactl`, `parec`, Python 3.11–3.13, Tk, and venv. Run as your normal desktop user, not root. Use the appropriate system packages for your distribution, with a supported Python version.

Ubuntu 24.04 / Debian 12 or 13 (typical default Python is supported):

```sh
sudo apt update
sudo apt install python3 python3-venv python3-tk pulseaudio-utils
```

Fedora (example using versioned Python 3.13, if available in your release):

```sh
sudo dnf install python3.13 python3.13-tkinter pulseaudio-utils
```

Arch / other rolling distributions: install `libpulse` (provides client tools on Arch) and a supported Python 3.11–3.13 with Tk and venv, using your distro's versioned packages or a trusted Python installation. If system Python is newer, don't force dependencies into it. Package availability varies by release. The app does not replace your audio server.

Extract the ZIP, open a terminal inside the extracted folder, then:

```sh
bash Start_Linux.sh
```

This captures the default output's monitor source (not the microphone). To select a different output, use `pactl list short sources` and copy a monitor source name, then:

```sh
bash Start_Linux.sh --source YOUR_MONITOR_SOURCE_NAME
```

If using Bluetooth/headphones or switching outputs, restart the app after selecting your desired default output. Some Wayland compositors may ignore the always-on-top request; the caption window is still usable as a separate window.

## Optional settings

Open CMD or a terminal in the extracted directory. Use one of the following:

Windows: `Start_Windows.bat --model base --seconds 4`

Linux: `bash Start_Linux.sh --model base --seconds 4`

Models: tiny, base, small (default), medium, large-v3. Smaller models may be faster but less accurate. Audio chunk duration: 3–15 seconds (default 5). Translation adds processing time and may fall behind, skip chunks or misinterpret slang, music and overlapping speech.

Optional NVIDIA GPU: add `--gpu` to your launcher command. It requires a compatible CUDA runtime, cuBLAS and cuDNN for the installed CTranslate2 release. See the upstream Faster-Whisper requirements: https://github.com/SYSTRAN/faster-whisper . CPU is the default and no GPU drivers are installed by this bundle.

## Troubleshooting

- `No module named numpy` or errors building `av`: use the launcher, not the `.py` file. Ensure a supported 64-bit Python version is installed. The installer uses prebuilt wheels only; no compiler needed. Do not use Python 3.15 for this release.
- On Windows, use `py -0p` in CMD to see available Python versions.
- If a dependency setup fails, keep the terminal open and copy the error. To rebuild the private environment, close the app and delete only `.venv-windows` or `.venv-linux` in the app directory, then start again.
- If the caption window is silent, confirm the stream is audible through the selected/default playback device. Restart the app after changing output. Linux users can check `pactl info` and `pactl list short sources`.
- First startup needs internet and disk space for packages and the model. Subsequent use can work offline when those files are cached.
- Runtime exceptions are shown in the window and written to `live_captions_error.log` in the app folder. Inspect logs for personal paths before sharing.
- If `tkinter` is unavailable, install the Tk component for your chosen Python version.

## Status and upstream projects

The previous Windows prototype was successfully used by its original tester on Python 3.13. This release changes the setup launcher and adds a Linux backend; the new launchers and live audio capture have not been tested on real Windows/Linux desktops. Linux support is experimental. No macOS support in this release.

- Faster-Whisper: https://github.com/SYSTRAN/faster-whisper
- PyAudioWPatch: https://github.com/s0d3s/PyAudioWPatch
- PulseAudio: https://www.freedesktop.org/wiki/Software/PulseAudio/

The source files are included for inspection. Third-party dependencies are installed separately under their respective licenses. No project license has been selected for the app source in this bundle.
