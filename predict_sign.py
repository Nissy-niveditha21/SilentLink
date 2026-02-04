import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load model
model = load_model("asl_model.h5")

# Labels must match the training order
DATASET_DIR = 'data/asl_alphabet_train/asl_alphabet_train'
labels = sorted(os.listdir(DATASET_DIR))

label_dict = {idx: label for idx, label in enumerate(labels)}

# Path to test image
img_path = 'data/asl_alphabet_test/asl_alphabet_test/G_test.jpg'  # update this if needed

# Load and preprocess image
img = cv2.imread(img_path)
if img is None:
    raise Exception(f"Image not found at {img_path}")

img = cv2.resize(img, (64, 64))
img = img / 255.0
img = np.expand_dims(img, axis=0)  # (1, 64, 64, 3)

# Predict
pred = model.predict(img)
pred_label = label_dict[np.argmax(pred)]

print(f"📷 Image: {os.path.basename(img_path)}")
print(f"🔤 Predicted Sign: {pred_label}")
