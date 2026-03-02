import cv2
import os
import numpy as np
import time
from tensorflow.keras.models import load_model

from utils.stability import PredictionStabilizer
from utils.sentence_builder import SentenceBuilder
from utils.tts_engine import TTSEngine

IMG_SIZE = 64
MODEL_PATH = "asl_model.h5"

# Make sure this path matches your dataset folder
LABELS = sorted(os.listdir("data/asl_alphabet_train"))

# Load model
model = load_model(MODEL_PATH)

# Initialize systems
stabilizer = PredictionStabilizer(window_size=15, min_count=10)
builder = SentenceBuilder()
tts = TTSEngine()

# Timeout system (auto space)
TIMEOUT_SECONDS = 2
last_detection_time = time.time()

# FPS calculation
prev_frame_time = 0
new_frame_time = 0

cap = cv2.VideoCapture(0)

print("📷 Webcam loaded. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    # FPS calculation
    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time) if prev_frame_time != 0 else 0
    prev_frame_time = new_frame_time

    # ROI box
    x1, y1, x2, y2 = 100, 100, 300, 300
    roi = frame[y1:y2, x1:x2]

    # Preprocess ROI
    img = cv2.resize(roi, (IMG_SIZE, IMG_SIZE))
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)

    # Predict
    prediction = model.predict(img, verbose=0)
    confidence = np.max(prediction)
    predicted_label = LABELS[np.argmax(prediction)]

    stable_letter = None
    current_time = time.time()

    # Accept only confident predictions
    if confidence > 0.7:
        stable_letter = stabilizer.add_prediction(predicted_label)

    # If stable letter detected
    if stable_letter:
        last_detection_time = current_time
        completed_sentence = builder.process_input(stable_letter)

        if completed_sentence:
            tts.speak(completed_sentence)

    # Auto-space if no gesture for TIMEOUT_SECONDS
    if current_time - last_detection_time > TIMEOUT_SECONDS:
        if builder.current_word != "":
            builder.process_input("SPACE")
        last_detection_time = current_time

    # Draw ROI
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Display live prediction
    cv2.putText(frame,
                f"Live: {predicted_label} ({confidence:.2f})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2)

    # Display constructed text
    display_text = builder.get_display_text()
    cv2.putText(frame,
                f"Text: {display_text}",
                (50, 400),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2)

    # Display FPS
    cv2.putText(frame,
                f"FPS: {int(fps)}",
                (450, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2)

    cv2.imshow("Sign Detection", frame)

    # Keyboard controls
    key = cv2.waitKey(1) & 0xFF

    # Quit
    if key == ord('q'):
        break

    # Manual delete (Backspace key)
    if key == 8:
        builder.process_input("DELETE")

    # Manual clear (c key)
    if key == ord('c'):
        builder.process_input("CLEAR")

    # Manual speak (Enter key)
    if key == 13:
        text_to_speak = builder.get_display_text().strip()
        if text_to_speak:
            tts.speak(text_to_speak)
            builder.process_input("CLEAR")

cap.release()
cv2.destroyAllWindows()
