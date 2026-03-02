import cv2
import os
import numpy as np
import time
import mediapipe as mp
from tensorflow.keras.models import load_model

from utils.stability import PredictionStabilizer
from utils.sentence_builder import SentenceBuilder
from utils.tts_engine import TTSEngine

IMG_SIZE = 64
MODEL_PATH = "asl_model.h5"

LABELS = sorted(os.listdir("data/asl_alphabet_train/asl_alphabet_train"))

model = load_model(MODEL_PATH)

stabilizer = PredictionStabilizer(window_size=15, min_count=10)
builder = SentenceBuilder()
tts = TTSEngine()

TIMEOUT_SECONDS = 2
last_detection_time = time.time()

prev_frame_time = 0

# MediaPipe initialization
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

print("📷 Webcam loaded. Press 'q' or ctrl C to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time) if prev_frame_time != 0 else 0
    prev_frame_time = new_frame_time

    stable_letter = None
    current_time = time.time()

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            h, w, _ = frame.shape
            x_coords = []
            y_coords = []

            for lm in hand_landmarks.landmark:
                x_coords.append(int(lm.x * w))
                y_coords.append(int(lm.y * h))

            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)

            padding = 20
            x_min = max(0, x_min - padding)
            y_min = max(0, y_min - padding)
            x_max = min(w, x_max + padding)
            y_max = min(h, y_max + padding)

            roi = frame[y_min:y_max, x_min:x_max]

            if roi.size == 0:
                continue

            img = cv2.resize(roi, (IMG_SIZE, IMG_SIZE))
            img = img.astype("float32") / 255.0
            img = np.expand_dims(img, axis=0)

            prediction = model.predict(img, verbose=0)
            confidence = np.max(prediction)
            predicted_label = LABELS[np.argmax(prediction)]

            if confidence > 0.8:
                stable_letter = stabilizer.add_prediction(predicted_label)

            if stable_letter:
                last_detection_time = current_time
                completed_sentence = builder.process_input(stable_letter)

                if completed_sentence:
                    tts.speak(completed_sentence)

            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0,255,0), 2)

            cv2.putText(frame,
                        f"{predicted_label} ({confidence:.2f})",
                        (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0,255,0),
                        2)

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Auto space
    if current_time - last_detection_time > TIMEOUT_SECONDS:
        if builder.current_word != "":
            builder.process_input("SPACE")
        last_detection_time = current_time

    display_text = builder.get_display_text()

    cv2.putText(frame,
                f"Text: {display_text}",
                (30, 450),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,255),
                2)

    cv2.putText(frame,
                f"FPS: {int(fps)}",
                (500, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,0,0),
                2)

    cv2.imshow("Sign Detection", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    if key == 8:
        builder.process_input("DELETE")
    if key == ord('c'):
        builder.process_input("CLEAR")
    if key == 13:
        text_to_speak = builder.get_display_text().strip()
        if text_to_speak:
            tts.speak(text_to_speak)
            builder.process_input("CLEAR")

cap.release()
cv2.destroyAllWindows()