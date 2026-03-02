"""import cv2
import threading

from modules.gesture_recognizer import HandGestureRecognition
from modules.tts import TextToSpeech
from modules.command_executor import CommandExecutor

gesture_model = HandGestureRecognition()
tts = TextToSpeech()
commands = CommandExecutor()

cap = cv2.VideoCapture(0)
prev_label = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame, label = gesture_model.detect_gesture(frame)

    cv2.putText(frame, f"Gesture: {label}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    if label != prev_label and label != "No Hand Detected":
        threading.Thread(target=tts.speak, args=(label,), daemon=True).start()
        threading.Thread(target=commands.run_command, args=(label,), daemon=True).start()
        prev_label = label

    cv2.imshow("Hand Gesture Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()"""
"""import cv2
import threading

from modules.gesture_recognizer import HandGestureRecognition
from modules.tts import TextToSpeech
from modules.command_executor import CommandExecutor

gesture_model = HandGestureRecognition()
tts = TextToSpeech()
commands = CommandExecutor()

cap = cv2.VideoCapture(0)
prev_label = None

# USER CHOICE
print("Press 1 for English voice, 2 for Hindi voice")
user_lang = input("Your choice: ").strip()
lang_code = "en" if user_lang == "1" else "hi"

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame, label = gesture_model.detect_gesture(frame)

    cv2.putText(frame, f"Gesture: {label}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    if label != prev_label and label != "No Hand Detected":
        threading.Thread(target=tts.speak, args=(label, lang_code), daemon=True).start()
        threading.Thread(target=commands.run_command, args=(label,), daemon=True).start()
        prev_label = label

    cv2.imshow("Hand Gesture Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()"""
"""import cv2
import threading
import time
import subprocess
import pyautogui
import psutil
import os

from modules.gesture_recognizer import HandGestureRecognition
from modules.tts import TextToSpeech
from modules.alphabet_recognizer import AlphabetRecognizer

gesture_model = HandGestureRecognition()
alphabet_model = AlphabetRecognizer()
tts = TextToSpeech()

lang_code = input("Press 1 for English voice, 2 for Hindi voice\nYour choice: ").strip()
lang_code = "hi" if lang_code == "2" else "en"

cap = cv2.VideoCapture(0)
prev_label = None
current_word = ""
last_pred_time = time.time()
notepad_opened = False
notepad_process = None

def is_notepad_open():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and 'notepad.exe' in proc.info['name'].lower():
            return proc
    return None

def open_notepad():
    global notepad_opened, notepad_process
    if not notepad_opened:
        notepad_process = subprocess.Popen(["notepad.exe"])
        notepad_opened = True
        time.sleep(1.5)  # Wait to open
        pyautogui.typewrite(current_word)

def close_notepad():
    global notepad_opened, notepad_process
    if notepad_opened:
        notepad_proc = is_notepad_open()
        if notepad_proc:
            notepad_proc.terminate()
            notepad_proc.wait()
        notepad_opened = False
        notepad_process = None

def toggle_notepad():
    if notepad_opened:
        close_notepad()
    else:
        open_notepad()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame, gesture_label, hand_crop = gesture_model.detect_gesture(frame)
    alphabet_label = alphabet_model.predict(hand_crop) if hand_crop is not None else ""

    # Show info
    cv2.putText(frame, f"Gesture: {gesture_label}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Alphabet: {alphabet_label}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, f"Word: {current_word}", (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # Add alphabet if stable
    

    prev_label = gesture_label
    cv2.imshow("Sign Language Translator", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
close_notepad()"""
"""
import cv2
import threading
import time
import subprocess
import pyautogui
import psutil

from modules.gesture_recognizer import HandGestureRecognition
from modules.tts import TextToSpeech
from modules.alphabet_recognizer import AlphabetRecognizer

# ----------------------- INIT -----------------------
gesture_model = HandGestureRecognition()
alphabet_model = AlphabetRecognizer()
tts = TextToSpeech()

lang_code = input("Press 1 for English voice, 2 for Hindi voice\nYour choice: ").strip()
lang_code = "hi" if lang_code == "2" else "en"

cap = cv2.VideoCapture(0)

prev_label = None
current_word = ""
last_pred_time = time.time()

notepad_opened = False
notepad_process = None

# ----------------------- HELPERS -----------------------
def is_notepad_open():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and 'notepad.exe' in proc.info['name'].lower():
            return proc
    return None

def open_notepad():
    global notepad_opened, notepad_process
    if not notepad_opened:
        notepad_process = subprocess.Popen(["notepad.exe"])
        notepad_opened = True
        time.sleep(1.5)  # Give time for Notepad to open

def close_notepad():
    global notepad_opened, notepad_process
    if notepad_opened:
        proc = is_notepad_open()
        if proc:
            proc.terminate()
            proc.wait()
        notepad_opened = False
        notepad_process = None

# ----------------------- MAIN LOOP -----------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detect gesture and crop hand
    frame, gesture_label, hand_crop = gesture_model.detect_gesture(frame)

    # Predict alphabet
    alphabet_label = alphabet_model.predict(hand_crop) if hand_crop is not None else ""

    # Display info on frame
    cv2.putText(frame, f"Gesture: {gesture_label}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Alphabet: {alphabet_label}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, f"Word: {current_word}", (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # ---------------- Add new letter if stable ----------------
    if (time.time() - last_pred_time > 1.2 and
        alphabet_label and
        len(alphabet_label) == 1):

        current_word += alphabet_label
        last_pred_time = time.time()

        if notepad_opened:
            pyautogui.typewrite(alphabet_label)

    # ---------------- Handle gestures ----------------
    if gesture_label != prev_label:
        # Thumb Up → Open Notepad & TTS
        if gesture_label == "Thumb Up":
            open_notepad()
            threading.Thread(target=tts.speak, args=(current_word, lang_code), daemon=True).start()

        # Thumb Down → Close Notepad
        elif gesture_label == "Thumb Down":
            close_notepad()

        
        elif gesture_label == "Fist" and notepad_opened:
            pyautogui.press('home')
            pyautogui.keyDown('shift')
            pyautogui.press('end')
            pyautogui.keyUp('shift')
            pyautogui.press('backspace')
            current_word = ""

        # Open Palm → New line
        elif gesture_label == "Open Palm" and notepad_opened:
            pyautogui.press('enter')
            current_word = ""

        # Thumb Left → Save
        elif gesture_label == "Thumb Left" and notepad_opened:
            pyautogui.hotkey('ctrl', 's')

        # Thumb Right → Save As
        elif gesture_label == "Thumb Right" and notepad_opened:
            pyautogui.hotkey('ctrl', 'shift', 's')

    prev_label = gesture_label

    cv2.imshow("Sign Language Translator", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ----------------------- CLEANUP -----------------------
cap.release()
cv2.destroyAllWindows()
close_notepad()
"""
"""import cv2
import threading
import time
import subprocess
import pyautogui
import psutil

from modules.gesture_recognizer import HandGestureRecognition
from modules.tts import TextToSpeech
from modules.alphabet_recognizer import AlphabetRecognizer

# ----------------------- INIT -----------------------
gesture_model = HandGestureRecognition()
alphabet_model = AlphabetRecognizer()
tts = TextToSpeech()

lang_choice = input("Press 1 for English voice, 2 for Hindi voice\nYour choice: ").strip()
lang_code = "hi" if lang_choice == "2" else "en"

tts.announce_language(lang_code)
cap = cv2.VideoCapture(0)

prev_label = None
current_word = ""
last_pred_time = time.time()

notepad_opened = False
notepad_process = None

# ----------------------- HELPERS -----------------------
def is_notepad_open():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and 'notepad.exe' in proc.info['name'].lower():
            return proc
    return None

def open_notepad():
    global notepad_opened, notepad_process
    if not notepad_opened:
        notepad_process = subprocess.Popen(["notepad.exe"])
        notepad_opened = True
        time.sleep(1.5)  

def close_notepad():
    global notepad_opened, notepad_process
    if notepad_opened:
        proc = is_notepad_open()
        if proc:
            proc.terminate()
            proc.wait()
        notepad_opened = False
        notepad_process = None

# ----------------------- MAIN LOOP -----------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame, gesture_label, hand_crop = gesture_model.detect_gesture(frame)

    alphabet_label = alphabet_model.predict(hand_crop) if hand_crop is not None else ""

    cv2.putText(frame, f"Gesture: {gesture_label}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Alphabet: {alphabet_label}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, f"Word: {current_word}", (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # ---------------- Add new letter ----------------
    if (time.time() - last_pred_time > 1.2 and
        alphabet_label and
        len(alphabet_label) == 1):

        current_word += alphabet_label
        last_pred_time = time.time()

        if notepad_opened:
            pyautogui.typewrite(alphabet_label)

    # ---------------- Gestures ----------------
    if gesture_label != prev_label:

        # Thumb Up → Open Notepad + TTS
        if gesture_label == "Thumb Up":
            open_notepad()
            threading.Thread(
                target=tts.speak,
                args=(current_word, lang_code),
                daemon=True
            ).start()

        # Thumb Down → Close Notepad
        elif gesture_label == "Thumb Down":
            close_notepad()

        # Fist → Clear line
        elif gesture_label == "Fist" and notepad_opened:
            pyautogui.press('home')
            pyautogui.keyDown('shift')
            pyautogui.press('end')
            pyautogui.keyUp('shift')
            pyautogui.press('backspace')
            current_word = ""

        # Open Palm → New line
        elif gesture_label == "Open Palm" and notepad_opened:
            pyautogui.press('enter')
            current_word = ""

        # Thumb Left → Save
        elif gesture_label == "Thumb Left" and notepad_opened:
            pyautogui.hotkey('ctrl', 's')

        # Thumb Right → Save As
        elif gesture_label == "Thumb Right" and notepad_opened:
            pyautogui.hotkey('ctrl', 'shift', 's')

    prev_label = gesture_label

    cv2.imshow("Sign Language Translator", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ----------------------- CLEANUP -----------------------
cap.release()
cv2.destroyAllWindows()
close_notepad()"""

import cv2
import threading
import time
import subprocess
import pyautogui
import psutil
import webbrowser

from modules.gesture_recognizer import HandGestureRecognition
from modules.tts import TextToSpeech
from modules.alphabet_recognizer import AlphabetRecognizer

# ----------------------- INIT -----------------------
gesture_model = HandGestureRecognition()
alphabet_model = AlphabetRecognizer()
tts = TextToSpeech()

lang_code = input("Press 1 for English voice, 2 for Hindi voice\nYour choice: ").strip()
lang_code = "hi" if lang_code == "2" else "en"

cap = cv2.VideoCapture(0)
prev_label = None
current_word = ""
last_pred_time = time.time()

notepad_opened = False
notepad_process = None

# ----------------------- HELPERS -----------------------
def is_notepad_open():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and 'notepad.exe' in proc.info['name'].lower():
            return proc
    return None

def open_notepad():
    global notepad_opened, notepad_process
    if not notepad_opened:
        notepad_process = subprocess.Popen(["notepad.exe"])
        notepad_opened = True
        time.sleep(1.5)  # Wait to open

def close_notepad():
    global notepad_opened, notepad_process
    if notepad_opened:
        proc = is_notepad_open()
        if proc:
            proc.terminate()
            proc.wait()
        notepad_opened = False
        notepad_process = None

def open_whatsapp():
    webbrowser.open("https://web.whatsapp.com")
    threading.Thread(
        target=tts.speak,
        args=("Opening WhatsApp", lang_code),
        daemon=True
    ).start()

def open_youtube():
    webbrowser.open("https://www.youtube.com")
    threading.Thread(
        target=tts.speak,
        args=("Opening YouTube", lang_code),
        daemon=True
    ).start()

# ----------------------- MAIN LOOP -----------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detect gesture and crop hand
    frame, gesture_label, hand_crop = gesture_model.detect_gesture(frame)

    # Predict alphabet
    alphabet_label = alphabet_model.predict(hand_crop) if hand_crop is not None else ""

    # Display info on frame
    cv2.putText(frame, f"Gesture: {gesture_label}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Alphabet: {alphabet_label}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, f"Word: {current_word}", (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # ---------------- Add new letter if stable ----------------
    if (time.time() - last_pred_time > 1.2 and
        alphabet_label and
        len(alphabet_label) == 1):

        current_word += alphabet_label
        last_pred_time = time.time()

        if notepad_opened:
            pyautogui.typewrite(alphabet_label)

    # ---------------- Handle gestures ----------------
    if gesture_label != prev_label:
        if gesture_label == "Thumb Up":
            open_notepad()
            threading.Thread(target=tts.speak, args=(current_word, lang_code), daemon=True).start()

        elif gesture_label == "Thumb Down":
            close_notepad()

        elif gesture_label == "Fist" and notepad_opened:
            pyautogui.press('home')
            pyautogui.keyDown('shift')
            pyautogui.press('end')
            pyautogui.keyUp('shift')
            pyautogui.press('backspace')
            current_word = ""

        elif gesture_label == "Open Palm" and notepad_opened:
            pyautogui.press('enter')
            current_word = ""

        elif gesture_label == "Thumb Left" and notepad_opened:
            pyautogui.hotkey('ctrl', 's')

        elif gesture_label == "Thumb Right":
            open_whatsapp()

        elif gesture_label == "2 Fingers":
            open_youtube()

    prev_label = gesture_label

    cv2.imshow("Sign Language Translator", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ----------------------- CLEANUP -----------------------
cap.release()
cv2.destroyAllWindows()
close_notepad()
