import cv2
import os
import numpy as np
from tensorflow.keras.models import load_model

IMG_SIZE = 64
MODEL_PATH = "asl_model.h5"
LABELS = sorted(os.listdir("data/asl_alphabet_train/asl_alphabet_train"))

# Load the trained model
model = load_model(MODEL_PATH)

cap = cv2.VideoCapture(0)

print("📷 Webcam loaded. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Define the region of interest (ROI) box
    x1, y1, x2, y2 = 100, 100, 300, 300
    roi = frame[y1:y2, x1:x2]

    # Preprocess ROI
    img = cv2.resize(roi, (IMG_SIZE, IMG_SIZE))
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)

    # Predict
    prediction = model.predict(img)
    predicted_label = LABELS[np.argmax(prediction)]

    # Show prediction on frame
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
    cv2.putText(frame, f"Prediction: {predicted_label}", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.imshow("Sign Detection", frame)

    # Quit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
