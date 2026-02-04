"""import pyttsx3
import threading

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.lock = threading.Lock()  # 👈 Add a lock

    def speak(self, text):
        def _speak():
            with self.lock:  # 👈 Use the lock to prevent overlapping threads
                self.engine.say(text)
                self.engine.runAndWait()

        threading.Thread(target=_speak).start()"""
# modules/tts.py

import os
import uuid
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play

gesture_translations = {
    "Thumb Up": "अंगूठा ऊपर",
    "Fist": "मुट्ठी",
    "Open Palm": "खुली हथेली",
    "2 Fingers": "दो उंगलियां",
    "OK Sign": "ठीक है संकेत",
    # Add more as needed
}

"""class TextToSpeech:
    def __init__(self):
        self.temp_dir = os.path.join(os.getcwd(), "temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)

    def speak(self, text, lang_code='en'):
        try:
            if lang_code == 'hi' and text in gesture_translations:
                text = gesture_translations[text]

            print(f"[DEBUG] Speaking: '{text}' in '{lang_code}'")

            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(self.temp_dir, filename)

            tts = gTTS(text=text, lang=lang_code)
            tts.save(filepath)

            sound = AudioSegment.from_file(filepath, format="mp3")
            play(sound)

            os.remove(filepath)

        except Exception as e:
            print(f"[TTS ERROR] {e}")

"""
# modules/tts.py
"""
from gtts import gTTS
import os
import uuid
from playsound import playsound

class TextToSpeech:
    def __init__(self):
        self.temp_dir = os.path.join(os.getcwd(), "temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)

    def speak(self, text, lang="en"):
        try:
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(self.temp_dir, filename)

            tts = gTTS(text=text, lang=lang)
            tts.save(filepath)

            playsound(filepath)
            os.remove(filepath)

        except Exception as e:
            print(f"[TTS ERROR] {e}")
"""
from gtts import gTTS
from playsound import playsound
import tempfile
import os

class TextToSpeech:
    def __init__(self):
        pass

    def speak(self, text, lang="en"):
        if not text.strip():
            return

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_path = fp.name

            tts = gTTS(text=text, lang=lang)
            tts.save(temp_path)
            playsound(temp_path)

        except Exception as e:
            print(f"[TTS ERROR] {e}")

        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
