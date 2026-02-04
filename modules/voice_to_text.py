"""import pyttsx3
engine = pyttsx3.init()
engine.say("Hello, testing text to speech")
engine.runAndWait()"""
import pyttsx3

engine = pyttsx3.init()

# Try to find a Hindi voice
for voice in engine.getProperty('voices'):
    if "hi" in str(voice.languages).lower() or "hindi" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

engine.say("नमस्ते! आप कैसे हैं?")
engine.runAndWait()
from gtts import gTTS
import playsound

text_hi = "नमस्ते! यह एक परीक्षण है।"
tts = gTTS(text=text_hi, lang='hi')
tts.save("output_hi.mp3")
playsound.playsound("output_hi.mp3")

