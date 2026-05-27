"""
JARVIS Watcher
===============
Always-on lightweight listener that launches the main assistant
when it hears the wake phrase "Start Jarvis" or "Wake up Jarvis".

Runs silently in the background on Windows startup via registry.
"""

import os
import sys
import time
import subprocess
import pyttsx3
import speech_recognition as sr
import requests
import sounddevice as sd
import numpy as np

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
PYTHON        = os.path.join(SCRIPT_DIR, "venv", "Scripts", "python.exe")
ASSISTANT     = os.path.join(SCRIPT_DIR, "assistant.py")
LOG_FILE      = os.path.join(SCRIPT_DIR, "watcher.log")

WAKE_PHRASES  = [
    "activate jarvis"
]

# ElevenLabs Voice Setup
ELEVENLABS_API_KEY   = ""  # <-- PASTE API KEY HERE
ELEVENLABS_VOICE_ID  = ""  # <-- PASTE VOICE ID HERE

jarvis_process = None


def log(msg: str):
    ts   = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def play_elevenlabs_tts(text: str) -> bool:
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        return False
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}?output_format=pcm_44100"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            audio_data = np.frombuffer(response.content, dtype=np.int16)
            audio_float = audio_data.astype(np.float32) / 32768.0
            sd.play(audio_float, samplerate=44100)
            sd.wait()
            return True
    except Exception:
        pass
    return False


def speak(text: str):
    if play_elevenlabs_tts(text):
        return
        
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        female = next((v for v in voices if "zira" in v.name.lower()), None)
        if female:
            engine.setProperty("voice", female.id)
        engine.setProperty("rate", 175)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception:
        pass


def is_running() -> bool:
    global jarvis_process
    return jarvis_process is not None and jarvis_process.poll() is None


def start_jarvis():
    global jarvis_process
    if is_running():
        speak("Jarvis is already running.")
        return
    log("Starting JARVIS...")
    speak("Starting Jarvis.")
    try:
        jarvis_process = subprocess.Popen([PYTHON, ASSISTANT], cwd=SCRIPT_DIR)
        log(f"JARVIS started (PID {jarvis_process.pid})")
    except Exception as e:
        log(f"Failed to start: {e}")
        speak("I had trouble starting Jarvis.")


def main():
    # Delay to let Windows fully boot before accessing microphone
    log("Watcher starting — waiting 10 s for system to settle...")
    time.sleep(10)
    log("Watcher active.")
    speak("Jarvis watcher is active. Say Activate Jarvis to begin.")

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    errors = 0

    while True:
        if is_running():
            time.sleep(2)
            errors = 0
            continue

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            text = recognizer.recognize_google(audio).lower()
            log(f"Heard: '{text}'")
            errors = 0

            if any(phrase in text for phrase in WAKE_PHRASES):
                start_jarvis()

        except (sr.WaitTimeoutError, sr.UnknownValueError):
            pass
        except sr.RequestError as e:
            errors += 1
            log(f"STT error: {e}")
            time.sleep(5)
        except OSError as e:
            errors += 1
            log(f"Mic error: {e}")
            time.sleep(10)
        except Exception as e:
            errors += 1
            log(f"Error: {e}")
            time.sleep(5)

        if errors > 10:
            log("Too many errors — pausing 30 s...")
            time.sleep(30)
            errors = 0


if __name__ == "__main__":
    main()
