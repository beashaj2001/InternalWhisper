# 🎙️ InternalWhisper

> **Push-to-talk voice dictation for Windows** — speak anywhere, text appears everywhere.

InternalWhisper lets you dictate text into **any application** on Windows using a global hotkey. Hold the hotkey, speak, release — your words are instantly transcribed and pasted wherever your cursor is, completely **free and offline** using OpenAI's Whisper model running locally on your machine.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Offline](https://img.shields.io/badge/Works-Offline-brightgreen)
![Free](https://img.shields.io/badge/100%25-Free-gold)

---

## ✨ Features

- 🎤 **Push-to-Talk** — hold `Ctrl+Alt` (or any custom hotkey) to record; release to transcribe and paste
- 🔁 **Toggle Mode** — press once to start, press again to stop
- 🚀 **Works in any app** — VS Code, Notepad, browser, Word, Slack, Teams, Discord, and more
- 🧠 **Free & Offline** — uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) locally, no API key needed
- 🌐 **Cloud backends too** — optional OpenAI or Groq API for higher accuracy
- 🪟 **Floating HUD overlay** — sleek translucent pill widget with live audio waveform animation
- 📋 **Smart clipboard** — backs up and restores your clipboard after pasting
- 🧹 **AI formatting** — optional cleanup of filler words (`um`, `uh`), punctuation, and custom formatting prompts
- 🔧 **Settings GUI** — dark-mode control panel with mic tester, hotkey config, API keys, and dictation history
- 🔔 **System tray** — runs silently in the background, always ready

---

## 🖥️ Demo

```
1. Open any text editor or input field
2. Hold Ctrl + Alt  →  HUD shows "Listening..." with live waveform
3. Speak your text
4. Release keys     →  HUD shows "Transcribing..." then "Pasted! ✓"
5. Your words appear at the cursor instantly
```

---

## 📦 Installation

### Requirements
- Windows 10 / 11
- Python 3.10+

### Quick Setup

```bash
# Clone the repo
git clone https://github.com/beashaj2001/InternalWhisper.git
cd InternalWhisper

# Install dependencies
pip install -r requirements.txt
```

> On first run, the Whisper `tiny` model (~75 MB) downloads automatically from HuggingFace. This is a one-time download — all future transcriptions are instant and fully offline.

### Or use the setup script

```batch
setup.bat
```

---

## 🚀 Running

```bash
python main.py
```

Or double-click **`run.bat`**.

The app starts silently in the **Windows system tray** (bottom-right corner near the clock). Look for the 🎤 mic icon.

---

## 🎛️ Usage

| Action | How |
|---|---|
| Start recording | Hold `Ctrl + Alt` |
| Stop & paste | Release `Ctrl + Alt` |
| Open settings | Right-click tray icon → Settings & History |
| View history | Settings → Dictation History tab |
| Change hotkey | Settings → General tab |
| Pause/Resume | Right-click tray icon → Pause Hotkeys |
| Quit | Right-click tray icon → Exit |

---

## ⚙️ Configuration

Settings are stored in `config.json` and can be edited via the GUI (right-click tray → **Settings & History**).

### Hotkey
Any combination of modifier keys and regular keys:
```
ctrl+alt      (default)
ctrl+shift
f9
alt+space
```

### Recording Mode
- **Push-to-Talk** *(default)* — hold to record, release to paste
- **Toggle** — press once to start, press again to stop

### STT Backend

| Backend | Cost | Speed | Requires |
|---|---|---|---|
| **Local Whisper** *(default)* | 🆓 Free | ~2-5s | Nothing (offline) |
| OpenAI Whisper API | 💰 Paid | ~1s | OpenAI API key |
| Groq Whisper API | 🆓 Free tier | <1s | Groq API key |

### Local Model Sizes

| Model | Size | Speed | Accuracy |
|---|---|---|---|
| `tiny` *(default)* | ~75 MB | Fastest | Good for phrases |
| `base` | ~142 MB | Fast | Balanced |
| `small` | ~461 MB | Medium | High |
| `medium` | ~1.4 GB | Slow | Best |

---

## 🗂️ Project Structure

```
InternalWhisper/
├── main.py              # App entry point, system tray, event coordinator
├── config.py            # JSON config management
├── audio_recorder.py    # Microphone capture (sounddevice + numpy)
├── hotkey_manager.py    # Global hotkey listener (pynput)
├── transcriber.py       # Speech-to-text (faster-whisper / OpenAI / Groq)
├── formatter.py         # Filler word removal & AI text formatting
├── paster.py            # Clipboard backup & Ctrl+V auto-paste
├── ui/
│   ├── floating_hud.py      # Translucent always-on-top overlay widget
│   └── settings_window.py   # Dark-mode settings & history panel
├── requirements.txt
├── run.bat              # One-click launcher
└── setup.bat            # Dependency installer + launcher
```

---

## 🔑 Using API Keys (Optional)

If you prefer faster or more accurate cloud-based transcription:

1. Right-click the tray icon → **Settings & History**
2. Go to the **AI & STT Engine** tab
3. Select your backend and paste your API key

- **OpenAI key**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Groq key** (free): [console.groq.com](https://console.groq.com)

---

## 🛠️ Dependencies

| Package | Purpose |
|---|---|
| `PyQt6` | UI framework (HUD overlay, settings window, tray) |
| `sounddevice` | Low-latency microphone audio capture |
| `pynput` | Global keyboard hook for hotkeys |
| `faster-whisper` | Free offline speech-to-text |
| `pyperclip` | Clipboard read/write |
| `openai` | Optional OpenAI / Groq API transcription |
| `numpy` | Audio buffer processing |
| `pystray` | System tray integration |
| `Pillow` | Tray icon generation |

---

## ❓ FAQ

**Q: The Fn key doesn't work as a hotkey. Why?**  
A: The `Fn` key is a hardware-level key handled by laptop firmware — no software on Windows can intercept it. Use `Ctrl+Alt`, `Ctrl+Shift`, or `F9` instead.

**Q: Will this work without internet?**  
A: Yes! The default Local Whisper backend is 100% offline after the one-time model download.

**Q: Where does my audio go?**  
A: Nowhere — when using the local backend, all audio is processed on your device and immediately deleted. Nothing is sent to any server.

**Q: How do I change the language?**  
A: The transcriber defaults to English. You can edit `transcriber.py` and change `language="en"` to any [supported Whisper language code](https://github.com/openai/whisper#available-models-and-languages).

**Q: The text pasting doesn't work in some apps. Why?**  
A: Some apps (e.g. games, certain admin windows) block simulated keyboard input. Try increasing the **Paste Delay** slider in Settings → General.

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) — the speech recognition model powering this app
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — optimized local Whisper inference
- [pynput](https://github.com/moses-palmer/pynput) — global keyboard listener
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — UI framework

---

<p align="center">Built with ❤️ for anyone who types too much</p>
