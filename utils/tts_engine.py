# utils/tts_engine.py

import pyttsx3


class TTSEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 150)

    def speak(self, text):
        if text:
            self.engine.say(text)
            self.engine.runAndWait()