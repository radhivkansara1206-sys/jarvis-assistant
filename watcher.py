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
import pygame
import edge_tts
import asyncio
import tempfile

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
PYTHON        = os.path.join(SCRIPT_DIR, "venv", "Scripts", "python.exe")
ASSISTANT     = os.path.join(SCRIPT_DIR, "assistant.py")
LOG_FILE      = os.path.join(SCRIPT_DIR, "watcher.log")

WAKE_PHRASES  = [
    "activate jarvis"
]

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


os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

def play_edge_tts(text: str) -> bool:
    try:
        temp_mp3 = os.path.join(tempfile.gettempdir(), "jarvis_tts_watcher.mp3")
        
        async def _generate():
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            await communicate.save(temp_mp3)
            
        asyncio.run(_generate())
        
        pygame.mixer.init()
        pygame.mixer.music.load(temp_mp3)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        
        try:
            os.remove(temp_mp3)
        except OSError:
            pass
            
        return True
    except Exception:
        return False


def speak(text: str):
    if play_edge_tts(text):
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


last_system_check_time = 0
last_system_check_result = False

def is_running() -> bool:
    global jarvis_process, last_system_check_time, last_system_check_result
    if jarvis_process is not None and jarvis_process.poll() is None:
        return True
    
    # Throttle system process checks to once every 10 seconds to save battery
    now = time.time()
    if now - last_system_check_time > 10:
        try:
            output = subprocess.check_output('wmic process where "name=\'python.exe\'" get commandline', shell=True).decode()
            last_system_check_result = "assistant.py" in output
        except:
            last_system_check_result = False
        last_system_check_time = now
        
    return last_system_check_result


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

    with sr.Microphone() as source:
        log("Calibrating ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2.0)
        log("Calibration complete. Listening efficiently...")
        
        while True:
            if is_running():
                time.sleep(2)
                continue

            try:
                # timeout=None blocks cleanly using 0 CPU until someone speaks
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
                
                # Double check before sending to cloud to save battery/bandwidth
                if is_running():
                    continue
                    
                text = recognizer.recognize_google(audio).lower()
                log(f"Heard: '{text}'")

                if any(phrase in text for phrase in WAKE_PHRASES):
                    start_jarvis()

            except (sr.WaitTimeoutError, sr.UnknownValueError):
                pass
            except sr.RequestError as e:
                log(f"STT error: {e}")
                time.sleep(5)
            except OSError as e:
                log(f"Mic error: {e}")
                time.sleep(10)
            except Exception as e:
                log(f"Error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    main()
