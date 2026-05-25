# JARVIS — AI Voice Assistant

> A fully offline, voice-authenticated, personal AI assistant for Windows.
> Built with Python, SpeechBrain, and pyttsx3.

---

## Features

| Category | Commands |
|---|---|
| 🎵 **YouTube** | Play song, pause, resume, skip, forward, rewind, fullscreen |
| 🌐 **Browser** | Google search, close/new tab, refresh |
| 💬 **Apps** | WhatsApp Web, Spotify, Discord, Calculator, Notepad, File Explorer, Settings |
| 🔊 **System** | Volume up/down, mute/unmute, shut down PC, restart PC |
| 📝 **Notes** | Take a note, open notes |
| ⏰ **Reminders** | Set timed voice reminders |
| ℹ️ **Info** | Weather, time, date |
| 🔐 **Security** | Voice biometric authentication (SpeechBrain ECAPA-TDNN) |

---

## Requirements

- Windows 10 / 11
- Python 3.10+
- Brave Browser (optional — falls back to default browser)
- A working microphone

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/radhivkansara1206-sys/jarvis-ai-assistant.git
cd jarvis-ai-assistant
```

### 2. Run the setup (creates venv + installs deps + enrolls voice)
```bash
setup.bat
```

### 3. Start JARVIS
```bash
jarvis.bat
```

---

## Voice Commands

```
Jarvis play [song name]
Jarvis search for [query]
Jarvis weather
Jarvis what is the time
Jarvis remind me in 5 minutes to drink water
Jarvis take a note that [text]
Jarvis open notes
Jarvis pause
Jarvis resume
Jarvis volume up / volume down / mute / unmute
Jarvis close tab / new tab / refresh
Jarvis open WhatsApp
Jarvis open Spotify
Jarvis shut down my computer
Jarvis exit
```

---

## Auto-Start on Boot

JARVIS uses a two-layer system:

1. **Watcher** (`watcher.py`) — starts silently on login, listens for the wake phrase
2. **Assistant** (`assistant.py`) — starts when you say *"Start Jarvis"*

To register the auto-start:
```powershell
powershell -ExecutionPolicy Bypass -File register_startup.ps1
```

---

## Re-enroll Voice

```bash
venv\Scripts\python.exe enroll.py
```

---

## Voice Threshold Calibration

Say **"Jarvis calibrate"** to hear your current voice match score.
Edit `SIMILARITY_THRESHOLD` in `assistant.py` if needed.

---

## Project Structure

```
jarvis-ai-assistant/
├── assistant.py          # Main voice assistant
├── enroll.py             # Voice enrollment (run once)
├── watcher.py            # Always-on wake phrase listener
├── setup.bat             # First-time setup script
├── jarvis.bat            # Quick launcher
├── register_startup.ps1  # Register auto-start in Windows
├── requirements.txt      # Python dependencies
└── .gitignore
```

---

## License

MIT © Rajiv Kansara
