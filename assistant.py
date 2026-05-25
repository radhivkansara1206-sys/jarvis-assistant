"""
JARVIS - AI Voice Assistant
============================
Author  : Rajiv Kansara
GitHub  : https://github.com/radhivkansara1206-sys/jarvis-ai-assistant
License : MIT

Features:
  - Voice authentication (speaker verification via SpeechBrain ECAPA-TDNN)
  - Natural language command routing
  - YouTube music playback, browser controls, system controls
  - Reminders, notes, weather, time/date
  - Female TTS voice (Microsoft Zira)
"""

import os
import re
import sys
import time
import datetime
import threading
import webbrowser
import urllib.parse
import urllib.request
import speech_recognition as sr
import pyttsx3
import torch
import requests
import soundfile as sf
import pyautogui

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
from speechbrain.inference.speaker import EncoderClassifier

# ──────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────
SCRIPT_DIR           = os.path.dirname(os.path.abspath(__file__))
EMBEDDING_FILE       = os.path.join(SCRIPT_DIR, "user_embedding.pt")
TEMP_WAV             = os.path.join(SCRIPT_DIR, ".tmp_auth.wav")
NOTES_FILE           = os.path.join(SCRIPT_DIR, "notes.txt")
SIMILARITY_THRESHOLD = 0.15   # Calibrated for user voice (scores: 0.15–0.46)
BRAVE_PATH           = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

# ──────────────────────────────────────────────
#  BROWSER SETUP (Brave → fallback to default)
# ──────────────────────────────────────────────
try:
    webbrowser.register("brave", None, webbrowser.BackgroundBrowser(BRAVE_PATH))
    browser = webbrowser.get("brave")
except Exception:
    browser = webbrowser

# ──────────────────────────────────────────────
#  TEXT-TO-SPEECH  (female voice – MS Zira)
# ──────────────────────────────────────────────
def speak(text: str):
    """Speak text using female TTS voice."""
    print(f"[JARVIS] {text}")
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        female = next((v for v in voices if "zira" in v.name.lower()), None)
        if female:
            engine.setProperty("voice", female.id)
        engine.setProperty("rate", 175)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[TTS ERROR] {e}")


def speak_async(text: str):
    """Thread-safe TTS via PowerShell (used inside background threads)."""
    safe = text.replace("'", "").replace('"', "")
    os.system(
        f'powershell -Command "'
        f'Add-Type -AssemblyName System.Speech; '
        f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        f'$s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female); '
        f'$s.Speak(\'{safe}\')"'
    )

# ──────────────────────────────────────────────
#  VOICE AUTHENTICATION
# ──────────────────────────────────────────────
def load_voice_profile():
    """Load the saved user voice embedding and SpeechBrain classifier."""
    if not os.path.exists(EMBEDDING_FILE):
        print("[ERROR] Voice profile not found. Run enroll.py first.")
        sys.exit(1)
    print("[INFO] Loading voice authentication model...")
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device": "cpu"}
    )
    user_embedding = torch.load(EMBEDDING_FILE, weights_only=False)
    print("[INFO] Voice profile loaded.")
    return classifier, user_embedding


def verify_speaker(audio_data: sr.AudioData, classifier, user_embedding):
    """
    Compare recorded audio against the enrolled voice profile.
    Returns (score: float, is_authorized: bool).
    """
    try:
        with open(TEMP_WAV, "wb") as f:
            f.write(audio_data.get_wav_data())

        data, sample_rate = sf.read(TEMP_WAV)
        if data.ndim > 1:
            data = data.mean(axis=1)          # stereo → mono

        signal = torch.tensor(data, dtype=torch.float32).unsqueeze(0)
        if sample_rate != 16000:
            import torchaudio.transforms as T
            signal = T.Resample(orig_freq=sample_rate, new_freq=16000)(signal)

        embedding = classifier.encode_batch(signal).squeeze()
        current  = torch.nn.functional.normalize(embedding, dim=0)
        enrolled = torch.nn.functional.normalize(user_embedding, dim=0)
        score    = torch.nn.functional.cosine_similarity(
            current.unsqueeze(0), enrolled.unsqueeze(0)
        ).item()

        print(f"[AUTH] Score: {score:.3f}  threshold: {SIMILARITY_THRESHOLD}")
        return score, score >= SIMILARITY_THRESHOLD

    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return 0.0, False
    finally:
        if os.path.exists(TEMP_WAV):
            os.remove(TEMP_WAV)

# ──────────────────────────────────────────────
#  COMMAND HELPERS
# ──────────────────────────────────────────────
def play_youtube(song: str):
    if not song:
        speak("What song would you like me to play?")
        return
    speak(f"Playing {song} on YouTube.")
    try:
        query = urllib.parse.urlencode({"search_query": song})
        with urllib.request.urlopen(
            f"https://www.youtube.com/results?{query}", timeout=8
        ) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        results = re.findall(r"watch\?v=(\S{11})", html)
        if results:
            browser.open(f"https://www.youtube.com/watch?v={results[0]}")
        else:
            speak("I could not find that on YouTube.")
    except Exception:
        speak("I had trouble connecting to YouTube.")


def get_weather():
    speak("Checking the weather.")
    try:
        resp = requests.get("https://wttr.in/?format=%C+%t", timeout=8)
        weather = resp.text.strip()
        print(f"[WEATHER] {weather}")
        speak(f"The current weather is {weather}.")
    except Exception:
        speak("I could not fetch the weather. Please check your internet connection.")


def save_note(note: str):
    if not note:
        speak("What would you like me to note?")
        return
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {note}\n")
    speak("Note saved.")


def set_reminder(cmd: str):
    match = re.search(r"(\d+)\s*(minute|min|hour|second|sec)", cmd)
    if not match:
        speak("I could not understand the time. Try: Jarvis remind me in 5 minutes to drink water.")
        return

    amount = int(match.group(1))
    unit   = match.group(2)
    if "hour" in unit:
        seconds, label = amount * 3600, f"{amount} hour{'s' if amount > 1 else ''}"
    elif "sec" in unit:
        seconds, label = amount, f"{amount} second{'s' if amount > 1 else ''}"
    else:
        seconds, label = amount * 60, f"{amount} minute{'s' if amount > 1 else ''}"

    # Support both "remind me in X min to Y" and "remind me to Y in X min"
    msg = ""
    m1 = re.search(r"\d+\s*(?:minute|min|hour|second|sec)s?\s+to\s+(.+)", cmd)
    m2 = re.search(r"remind\s+me\s+to\s+(.+?)\s+in\s+\d+", cmd)
    if m1:
        msg = m1.group(1).strip()
    elif m2:
        msg = m2.group(1).strip()

    speak(f"Reminder set for {label}{f' to {msg}' if msg else ''}.")

    def _fire():
        time.sleep(seconds)
        speak_async(f"Reminder! {msg}" if msg else "Your reminder is up!")

    threading.Thread(target=_fire, daemon=True).start()

# ──────────────────────────────────────────────
#  COMMAND ROUTER
# ──────────────────────────────────────────────
def execute_command(cmd: str):
    cmd = cmd.lower().strip()
    print(f"[CMD] {cmd}")

    if not cmd:
        speak("Yes? How can I help you?")

    # Greetings
    elif any(w in cmd for w in ["how are you", "how do you do", "whats up", "what's up"]):
        speak("I am fully operational and ready to assist you.")

    # ── YouTube ──────────────────────────────────────────────────────────────
    elif "play" in cmd:
        song = re.sub(r"\b(play|on youtube|youtube)\b", "", cmd).strip()
        play_youtube(song)

    elif "open youtube" in cmd:
        speak("Opening YouTube.")
        browser.open("https://www.youtube.com")

    # ── Google Search ─────────────────────────────────────────────────────────
    elif "search" in cmd:
        query = re.sub(r"\b(search|google|for)\b", "", cmd).strip()
        speak(f"Searching for {query}.")
        browser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")

    # ── Weather / Time / Date ─────────────────────────────────────────────────
    elif "weather" in cmd:
        get_weather()

    elif any(w in cmd for w in ["what time", "current time", "time"]):
        speak(f"The time is {time.strftime('%I:%M %p')}.")

    elif any(w in cmd for w in ["date", "today", "what day"]):
        speak(f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}.")

    # ── Notes (specific checks BEFORE generic 'note' keyword) ────────────────
    elif any(w in cmd for w in ["open notes", "show notes", "read notes", "open my notes"]):
        if os.path.exists(NOTES_FILE):
            os.startfile(NOTES_FILE)
            speak("Opening your notes.")
        else:
            speak("You have no saved notes yet.")

    elif any(w in cmd for w in ["open notepad", "open note pad"]):
        os.system("start notepad")
        speak("Opening Notepad.")

    elif any(w in cmd for w in ["take a note", "note that", "take note", "save note"]):
        note = re.sub(r"\b(take a note that|take a note|note that|take note|save note)\b", "", cmd).strip()
        save_note(note)

    # ── Reminders ─────────────────────────────────────────────────────────────
    elif any(w in cmd for w in ["reminder", "remind me", "set a reminder", "set reminder"]):
        set_reminder(cmd)

    # ── Media Controls (YouTube keyboard shortcuts) ───────────────────────────
    elif any(w in cmd for w in ["pause", "pose", "stop the video", "hold on"]):
        pyautogui.press("k")
        speak("Paused.")

    elif any(w in cmd for w in ["resume", "continue", "unpause"]):
        pyautogui.press("k")
        speak("Resuming.")

    elif any(w in cmd for w in ["fullscreen", "full screen"]):
        pyautogui.press("f")
        speak("Toggling fullscreen.")

    elif any(w in cmd for w in ["next video", "skip video", "skip"]):
        pyautogui.hotkey("shift", "n")
        speak("Next video.")

    elif any(w in cmd for w in ["rewind", "backward", "go back 10"]):
        pyautogui.press("j")
        speak("Rewinding.")

    elif any(w in cmd for w in ["forward", "skip ahead"]):
        pyautogui.press("l")
        speak("Skipping forward.")

    # ── Browser Tab Controls ──────────────────────────────────────────────────
    elif any(w in cmd for w in ["close all tabs", "close all the tabs", "close browser", "exit browser"]):
        os.system("taskkill /IM brave.exe /F 2>nul")
        os.system("taskkill /IM chrome.exe /F 2>nul")
        os.system("taskkill /IM msedge.exe /F 2>nul")
        speak("Browser closed.")

    elif any(w in cmd for w in ["close tab", "close this tab", "close the tab"]):
        pyautogui.hotkey("ctrl", "w")
        speak("Tab closed.")

    elif any(w in cmd for w in ["new tab", "open new tab"]):
        pyautogui.hotkey("ctrl", "t")
        speak("Opening a new tab.")

    elif any(w in cmd for w in ["refresh", "reload"]):
        pyautogui.hotkey("ctrl", "r")
        speak("Refreshing.")

    # ── System Volume ─────────────────────────────────────────────────────────
    elif any(w in cmd for w in ["volume up", "increase volume", "increase the volume", "louder"]):
        for _ in range(5):
            pyautogui.press("volumeup")
        speak("Volume increased.")

    elif any(w in cmd for w in ["volume down", "decrease volume", "decrease the volume", "quieter"]):
        for _ in range(5):
            pyautogui.press("volumedown")
        speak("Volume decreased.")

    elif any(w in cmd for w in ["mute", "silence"]):
        pyautogui.press("volumemute")
        speak("Muted.")

    elif "unmute" in cmd:
        pyautogui.press("volumemute")
        speak("Unmuted.")

    # ── Apps ──────────────────────────────────────────────────────────────────
    elif "spotify" in cmd:
        speak("Opening Spotify.")
        os.system("start spotify:")

    elif "discord" in cmd:
        speak("Opening Discord.")
        os.system("start discord:")

    elif "whatsapp" in cmd:
        speak("Opening WhatsApp Web.")
        browser.open("https://web.whatsapp.com")
        if any(w in cmd for w in ["type", "send", "message"]):
            msg = re.sub(r".*(type|send|message)\s*", "", cmd).strip()
            if msg:
                speak("Select a contact and I will type your message.")
                def _type():
                    time.sleep(6)
                    pyautogui.typewrite(msg, interval=0.05)
                threading.Thread(target=_type, daemon=True).start()

    elif any(w in cmd for w in ["open calculator", "calculator"]):
        os.system("start calc")
        speak("Opening Calculator.")

    elif any(w in cmd for w in ["file explorer", "my files", "open files"]):
        os.system("start explorer")
        speak("Opening File Explorer.")

    elif any(w in cmd for w in ["open settings", "settings"]):
        os.system("start ms-settings:")
        speak("Opening Settings.")

    elif any(w in cmd for w in ["task manager"]):
        os.system("start taskmgr")
        speak("Opening Task Manager.")

    # ── PC Power Controls ─────────────────────────────────────────────────────
    elif any(w in cmd for w in ["shut down", "turn off", "shutdown", "power off"]) and \
         any(w in cmd for w in ["pc", "computer", "system", "machine"]):
        speak("Shutting down your computer.")
        os.system("shutdown /s /t 5")

    elif any(w in cmd for w in ["restart my computer", "restart pc", "reboot"]):
        speak("Restarting your computer.")
        os.system("shutdown /r /t 5")

    # ── Exit JARVIS ───────────────────────────────────────────────────────────
    elif any(w in cmd for w in ["exit", "goodbye", "bye", "stop listening",
                                 "shut down jarvis", "turn off jarvis"]) \
            or cmd.strip() in ["stop", "shut down"]:
        speak("Goodbye. I will be here when you need me.")
        sys.exit(0)

    else:
        speak("Sorry, I did not understand that command.")

# ──────────────────────────────────────────────
#  MAIN LOOP
# ──────────────────────────────────────────────
def main():
    print("=" * 50)
    print("       JARVIS AI Assistant")
    print("=" * 50)

    classifier, user_embedding = load_voice_profile()

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    with sr.Microphone() as source:
        print("[INFO] Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=2)

    speak("Jarvis online. Ready for your commands.")
    print("\n[READY] Say 'Jarvis' followed by your command.\n")

    while True:
        try:
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)

            text = recognizer.recognize_google(audio).lower().strip()
            print(f"[HEARD] '{text}'")

            if "jarvis" not in text:
                continue

            score, authorized = verify_speaker(audio, classifier, user_embedding)

            # Calibrate command: always responds with score
            if "calibrate" in text:
                speak(f"Your voice score is {score:.2f}. Threshold is {SIMILARITY_THRESHOLD}.")
                continue

            if not authorized:
                speak("Unauthorized voice. Command ignored.")
                continue

            command = re.sub(r"\bjarvis\b", "", text).strip()
            execute_command(command)

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            print("[ERROR] Speech recognition unavailable. Check internet.")
        except SystemExit:
            raise
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
