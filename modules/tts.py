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
from gtts import gTTS
import tempfile
import os
import time
import subprocess
import platform

class TextToSpeech:
    def speak(self, text, lang="en"):
        if not text.strip():
            return

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_path = fp.name

            tts = gTTS(text=text, lang=lang)
            tts.save(temp_path)

            # Cross-platform audio play
            if platform.system() == "Windows":
                os.startfile(temp_path)
            else:
                subprocess.call(["mpg123", temp_path])

            time.sleep(2)

        except Exception as e:
            print(f"[TTS ERROR] {e}")

        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    # 🔹 New function for language confirmation
    def announce_language(self, lang_code):
        if lang_code == "hi":
            self.speak("हिंदी आवाज़ चुनी गई है", "hi")
        else:
            self.speak("English voice selected", "en")
