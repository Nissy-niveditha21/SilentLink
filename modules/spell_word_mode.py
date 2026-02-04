import cv2
import threading
from modules.gesture_recognizer import HandGestureRecognition
from modules.tts import TextToSpeech

gesture_model = HandGestureRecognition()
tts = TextToSpeech()

cap = cv2.VideoCapture(0)
prev_label = None
word_buffer = ""  # to store letters

# You can define gestures used for confirmation
confirm_gesture = "Open Palm"
clear_gesture = "Fist"

# Set language
lang_code = input("Press 1 for English, 2 for Hindi: ") == "2" and "hi" or "en"

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame, label = gesture_model.detect_gesture(frame)

    # Show the built word on screen
    cv2.putText(frame, f"Detected: {label}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Word: {word_buffer}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

    # Process gesture
    if label != prev_label:
        if len(label) == 1 and label.isalpha():
            word_buffer += label.upper()

        elif label == confirm_gesture and word_buffer:
            threading.Thread(target=tts.speak, args=(word_buffer, lang_code), daemon=True).start()
            word_buffer = ""

        elif label == clear_gesture:
            word_buffer = ""

        prev_label = label

    cv2.imshow("Spell Word Mode", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
