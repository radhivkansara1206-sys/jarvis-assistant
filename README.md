# 🤖 JARVIS — AI Voice Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows" />
  <img src="https://img.shields.io/badge/Voice-SpeechBrain-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

> A fully offline, voice-authenticated personal AI assistant for Windows.
> Built with Python and SpeechBrain — no cloud APIs, no subscriptions.

---

## ✨ What Can JARVIS Do?

| Category | Commands |
|---|---|
| 🎵 **YouTube** | Play songs, pause, resume, skip, forward, rewind, fullscreen |
| 🌐 **Browser** | Google search, open/close tabs, refresh page |
| 💬 **Messaging** | Open WhatsApp Web, type a message |
| 📱 **Apps** | Spotify, Discord, Calculator, Notepad, File Explorer, Settings, Task Manager |
| 🔊 **System** | Volume up/down, mute/unmute, shut down PC, restart PC |
| 📝 **Notes** | Save notes by voice, open your notes file |
| ⏰ **Reminders** | Set timed voice reminders (e.g. "in 5 minutes to drink water") |
| ℹ️ **Info** | Weather, current time, today's date |
| 🔐 **Security** | Voice biometric authentication — only YOUR voice works |

---

## 🖥️ System Requirements

- **OS:** Windows 10 or Windows 11
- **Python:** 3.10 or higher → [Download Python](https://www.python.org/downloads/)
- **Microphone:** Any working microphone
- **Internet:** Required for Google Speech Recognition and weather
- **Browser:** [Brave Browser](https://brave.com) *(recommended — falls back to your default browser if not installed)*

---

## 📦 Installation Guide

### Step 1 — Clone the Repository

Open **PowerShell** or **Command Prompt** and run:

```bash
git clone https://github.com/radhivkansara1206-sys/jarvis-assistant.git
cd jarvis-assistant
```

> Don't have Git? [Download Git for Windows](https://git-scm.com/download/win)

---

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv
```

---

### Step 3 — Install Dependencies

```bash
venv\Scripts\pip install -r requirements.txt
```

> ⚠️ This will download ~1–2 GB of AI model files (PyTorch + SpeechBrain) on first run. Please be patient.

---

### Step 4 — Enroll Your Voice

This records 3 samples of your voice to build a unique voice profile. **This is how JARVIS knows it's you.**

```bash
venv\Scripts\python.exe enroll.py
```

You will be asked to say 3 different sentences, one at a time. Speak naturally and clearly after each countdown.

> 💡 Re-run `enroll.py` anytime if JARVIS stops recognizing your voice.

---

### Step 5 — Start JARVIS

```bash
jarvis.bat
```

Or directly:

```bash
venv\Scripts\python.exe assistant.py
```

Wait for the female voice to say **"Jarvis online. Ready for your commands."**

Then say any command starting with the wake word **"Jarvis"**:

```
Jarvis what is the time
Jarvis play Blinding Lights
Jarvis weather
```

---

## 🚀 Auto-Start on Windows Boot (Optional)

JARVIS has a two-layer startup system:

1. **Watcher** — starts silently in the background when you log in
2. **Assistant** — wakes up when you say *"Activate Jarvis"*

To enable auto-start, run this once in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File register_startup.ps1
```

After your next reboot:
- Watcher starts automatically in the background
- Say **"Activate Jarvis"** → JARVIS wakes up
- Say **"Jarvis exit"** → JARVIS sleeps (Watcher keeps listening)
- Say **"Activate Jarvis"** again → JARVIS wakes up again

---

## 🗣️ Full Command Reference

### 🎵 Music & YouTube
```
Jarvis play [song name]
Jarvis open YouTube
Jarvis pause
Jarvis resume
Jarvis skip
Jarvis forward
Jarvis rewind
Jarvis fullscreen
```

### 🌐 Browser Controls
```
Jarvis search for [anything]
Jarvis new tab
Jarvis close tab
Jarvis close all tabs (or Jarvis close browser)
Jarvis refresh
```

### 📱 Open Apps
```
Jarvis open WhatsApp
Jarvis open WhatsApp and type [message]
Jarvis open Spotify
Jarvis open Discord
Jarvis open calculator
Jarvis open notepad
Jarvis file explorer
Jarvis open settings
Jarvis task manager
```

### 🔊 Volume & System
```
Jarvis increase volume
Jarvis decrease volume
Jarvis mute
Jarvis unmute
Jarvis shut down my computer
Jarvis restart my computer
```

### 📝 Notes
```
Jarvis take a note that [your text]
Jarvis open notes
```

### ⏰ Reminders
```
Jarvis remind me in 5 minutes to drink water
Jarvis remind me to call mom in 1 hour
Jarvis set a reminder for 30 seconds
```

### ℹ️ Info
```
Jarvis what is the time
Jarvis what is the date
Jarvis weather
Jarvis how are you
```

### 🔴 Control
```
Jarvis exit         → shuts down JARVIS only
Jarvis goodbye      → same as exit
Activate Jarvis     → wakes JARVIS up (via Watcher)
```

---

## 🔧 Troubleshooting

### ❌ JARVIS says "Unauthorized voice"
Your voice score is below the threshold.
- Try re-enrolling: `venv\Scripts\python.exe enroll.py`
- Say **"Jarvis calibrate"** to hear your current voice score
- If your score is consistently below `0.15`, lower the `SIMILARITY_THRESHOLD` in `assistant.py`

### ❌ "Could not understand audio"
- Check your microphone is selected as the default input in Windows Sound Settings
- Reduce background noise
- Speak clearly after a brief pause

### ❌ Dependencies failed to install
Make sure you are using Python 3.10+:
```bash
python --version
```
Then retry:
```bash
venv\Scripts\pip install -r requirements.txt
```

### ❌ YouTube is not playing
JARVIS opens YouTube in **Brave Browser** by default. If Brave is not installed at the default path, it falls back to your system default browser. You can change the path in `assistant.py`:
```python
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
```

### ❌ Watcher not starting on boot
Run this command again in PowerShell:
```powershell
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'JarvisWatcher' -Value '"C:\path\to\jarvis-assistant\venv\Scripts\pythonw.exe" "C:\path\to\jarvis-assistant\watcher.py"'
```
Replace `C:\path\to\jarvis-assistant` with your actual folder path.

---

## 📁 Project Structure

```
jarvis-assistant/
├── assistant.py          # Main voice assistant
├── enroll.py             # Voice enrollment (run once)
├── watcher.py            # Always-on wake phrase listener
├── setup.bat             # Automated first-time setup
├── jarvis.bat            # Quick launcher
├── register_startup.ps1  # Windows auto-start registration
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── .gitignore            # Excludes venv, voice profile, notes
```

> **Note:** `user_embedding.pt` (your voice profile) and `notes.txt` are created locally and are excluded from git for privacy.

---

## 🛡️ Privacy & Security

- All voice processing happens **on your machine** — nothing is sent to any server
- Google Speech Recognition is used **only to transcribe text** (not for authentication)
- Your voice biometric (`user_embedding.pt`) is stored **locally only** and is not committed to git
- Only your enrolled voice can execute commands

---

## 📄 License

MIT © [Radhiv Kansara](https://github.com/radhivkansara1206-sys)
