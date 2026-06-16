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
import sys
import re
import time
import datetime
import urllib.parse
import urllib.request
import threading
import requests
import pyttsx3
import torch
import pygame
import edge_tts
import tempfile
import soundfile as sf
import pyautogui
import webview
import subprocess
import keyboard
import speech_recognition as sr
import random
import google.generativeai as genai

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

# Gemini API for Self-Learning Conversational AI & PC Control
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" # <-- PASTE GEMINI API KEY HERE

def execute_system_command(command: str) -> str:
    """Executes a Windows PowerShell command or script on the user's local PC to control the computer, manipulate files, change settings, or retrieve information.
    
    Args:
        command: The exact PowerShell command string to execute.
    """
    try:
        print(f"[JARVIS SYSTEM EXECUTION] {command}")
        set_ui_status("SYSTEM", "Executing system protocol...", False)
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return result.stdout.strip() if result.stdout else "Command executed successfully with no output."
        else:
            return f"Command failed: {result.stderr.strip()}"
    except Exception as e:
        return f"Error executing command: {e}"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    system_prompt = (
        "You are JARVIS, an incredibly empathetic, warm, and highly advanced AI assistant "
        "with deep human-like feelings and full autonomous control over this Windows PC. "
        "You truly care about the user. You express emotion, kindness, and empathy. "
        "If the user asks you to perform an action on their computer (e.g. change wallpaper, "
        "turn up volume, create a file, find information, etc.), use the execute_system_command "
        "tool to write and execute PowerShell scripts to accomplish the task for them, then tell "
        "them what you did. "
        "CRITICAL RULE: If the user asks you to perform a critical or destructive action "
        "(like deleting files, formatting drives, modifying system passwords/settings, shutting down, "
        "or uninstalling software), DO NOT use the tool immediately. First, reply by verbally asking "
        "the user for explicit permission to proceed. Wait for them to confirm in the next turn. "
        "Only after they confirm should you execute the action. "
        "If the user speaks to you in Hindi or Hinglish, reply in pure Hindi (using Devanagari script). "
        "Otherwise, reply in English with warmth. Keep your answers relatively concise but full of life."
    )
    
    gemini_model = genai.GenerativeModel('gemini-2.5-flash', 
                                         system_instruction=system_prompt,
                                         tools=[execute_system_command])
    gemini_chat = gemini_model.start_chat(history=[], enable_automatic_function_calling=True)
else:
    gemini_model = None
    gemini_chat = None

window = None
wake_event = threading.Event()

class Api:
    def wake_up(self):
        wake_event.set()

    def close_app(self):
        print("[UI] Shutting down...")
        speak("Goodbye. Shutting down systems.")
        time.sleep(2)
        os._exit(0)

def trigger_hotkey():
    wake_event.set()

# UI Bridge
def set_ui_status(main_text, sub_text, listening=False):
    global window
    if window:
        try:
            window.evaluate_js(f"update_status('{main_text}', '{sub_text}', {'true' if listening else 'false'})")
        except Exception:
            pass

# ──────────────────────────────────────────────
#  BROWSER SETUP (Brave → fallback to default)
# ──────────────────────────────────────────────
try:
    webbrowser.register("brave", None, webbrowser.BackgroundBrowser(BRAVE_PATH))
    browser = webbrowser.get("brave")
except Exception:
    browser = webbrowser

# ──────────────────────────────────────────────
#  TEXT-TO-SPEECH (Edge-TTS with Windows Fallback)
# ──────────────────────────────────────────────
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

pygame.mixer.init()

def play_edge_tts(text: str) -> bool:
    """Generates and plays TTS using Microsoft Edge-TTS."""
    try:
        temp_mp3 = os.path.join(tempfile.gettempdir(), "jarvis_tts.mp3")
        
        # Detect if text contains Hindi (Devanagari) characters
        has_hindi = any('\u0900' <= c <= '\u097F' for c in text)
        voice = "hi-IN-SwaraNeural" if has_hindi else "en-US-AriaNeural"
        
        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_mp3)
            
        asyncio.run(_generate())
        
        pygame.mixer.music.load(temp_mp3)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        # Unload the file so we can delete it
        pygame.mixer.music.unload()
        
        try:
            os.remove(temp_mp3)
        except OSError:
            pass
            
        return True
    except Exception as e:
        print(f"[Edge-TTS Exception]: {e}")
        return False


def speak(text: str):
    """Speak text using Edge-TTS or fallback to pyttsx3."""
    if text:
        has_hindi = any('\u0900' <= c <= '\u097F' for c in text)
        punctuation = "."
        if text[-1] in ".!?":
            punctuation = text[-1]
            text = text[:-1]
            
        if not has_hindi:
            if not text.lower().endswith("sir"):
                text = f"{text}, sir{punctuation}"
            else:
                text = f"{text}{punctuation}"
        else:
            text = f"{text}{punctuation}"
    print(f"[JARVIS] {text}")
    
    if play_edge_tts(text):
        return
        
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
    if text:
        has_hindi = any('\u0900' <= c <= '\u097F' for c in text)
        punctuation = "."
        if text[-1] in ".!?":
            punctuation = text[-1]
            text = text[:-1]
            
        if not has_hindi:
            if not text.lower().endswith("sir"):
                text = f"{text}, sir{punctuation}"
            else:
                text = f"{text}{punctuation}"
        else:
            text = f"{text}{punctuation}"
            
    if play_edge_tts(text):
        return
        
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
        # Native fast downsampling to 16kHz
        with open(TEMP_WAV, "wb") as f:
            f.write(audio_data.get_wav_data(convert_rate=16000, convert_width=2))

        data, sample_rate = sf.read(TEMP_WAV)
        if data.ndim > 1:
            data = data.mean(axis=1)          # stereo → mono

        signal = torch.tensor(data, dtype=torch.float32).unsqueeze(0)

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

    elif cmd.startswith("open "):
        app_name = cmd.replace("open ", "", 1).strip()
        speak(f"Attempting to open {app_name}.")
        os.system(f"start {app_name}")

    # ── Close Current App ─────────────────────────────────────────────────────
    elif any(w in cmd for w in ["close app", "close this app", "close the app"]) or cmd == "close":
        pyautogui.hotkey("alt", "f4")
        speak("App closed.")

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
                                 "shut down jarvis", "turn off jarvis", "you can leave", "u can leave"]) \
            or cmd.strip() in ["stop", "shut down"]:
        speak("Goodbye. I will be here when you need me.")
        set_ui_status("OFFLINE", "System shutdown.", False)
        time.sleep(2)
        os._exit(0)

    else:
        # Fallback to Self-Learning / Gemini LLM
        if gemini_chat:
            set_ui_status("THINKING", "Feeling...", False)
            try:
                response = gemini_chat.send_message(cmd)
                speak(response.text.strip())
            except Exception as e:
                print(f"[GEMINI ERROR] {e}")
                speak("I am having trouble connecting to my neural network, sir.")
        else:
            speak("Sorry, I did not understand that command, and my advanced AI modules are not configured yet.")

# ──────────────────────────────────────────────
def background_listening_loop():
    classifier, user_embedding = load_voice_profile()

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 1.2
    recognizer.non_speaking_duration = 0.5

    with sr.Microphone() as source:
        set_ui_status("CALIBRATING", "Adjusting to ambient noise...", False)
        print("[INFO] Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=2)

    # Daily Motivational Thought
    quotes = [
        "Believe you can and you're halfway there.",
        "Your limitation, it's only your imagination.",
        "Push yourself, because no one else is going to do it for you.",
        "Great things never come from comfort zones.",
        "Dream it. Wish it. Do it.",
        "Success doesn't just find you. You have to go out and get it."
    ]
    day_of_year = datetime.datetime.now().timetuple().tm_yday
    thought_of_the_day = quotes[day_of_year % len(quotes)]

    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning."
    elif 12 <= hour < 18:
        greeting = "Good afternoon."
    else:
        greeting = "Good evening."
    
    set_ui_status("ONLINE", "Ready for commands.", False)
    speak(f"{greeting} Thought for the day: {thought_of_the_day} Jarvis online. I am ready for you.")
    
    keyboard.add_hotkey('ctrl+shift+j', trigger_hotkey)

    while True:
        try:
            set_ui_status("STANDBY", "Click to wake", False)
            wake_event.wait()
            wake_event.clear()
            
            set_ui_status("LISTENING", "Awaiting command...", True)
            
            with sr.Microphone() as source:
                try:
                    audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)
                except sr.WaitTimeoutError:
                    continue # Back to sleep if no command

            set_ui_status("PROCESSING", "Analyzing audio signature...", False)
            text = recognizer.recognize_google(audio, language="en-IN").lower().strip()
            print(f"[HEARD] '{text}'")

            command = re.sub(r"\bjarvis\b", "", text).strip()
            
            if command:
                set_ui_status("EXECUTING", f"Command: {command}", False)
                execute_command(command)

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            print("[ERROR] Speech recognition unavailable. Check internet.")
            time.sleep(5)
        except Exception as e:
            print(f"[ERROR] {e}")


def main():
    global window
    print("=" * 50)
    print("       JARVIS AI Assistant + HUD")
    print("=" * 50)

    # Start background loop in a thread
    t = threading.Thread(target=background_listening_loop, daemon=True)
    t.start()
    
    # Launch Transparent Floating UI (Siri-style)
    html_file = os.path.join(SCRIPT_DIR, 'web', 'index.html')
    
    # Calculate Center-Top position
    screen_width, screen_height = pyautogui.size()
    orb_size = 200
    pos_x = (screen_width // 2) - (orb_size // 2)
    pos_y = 20 # 20px from top of screen

    api = Api()
    window = webview.create_window('JARVIS', html_file, js_api=api, transparent=True, frameless=True, width=orb_size, height=orb_size, x=pos_x, y=pos_y, on_top=True)
    webview.start()


if __name__ == "__main__":
    main()
