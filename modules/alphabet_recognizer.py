import cv2
import numpy as np
import os
from tensorflow.keras.models import load_model

class AlphabetRecognizer:
    def __init__(self):
        # Load the model
        self.model = load_model("asl_model.h5")

        # Load label dictionary from folder
        dataset_path = "data/asl_alphabet_train"
        self.labels = sorted(os.listdir(dataset_path))
        self.label_dict = {idx: label for idx, label in enumerate(self.labels)}

    def predict(self, frame):
        # Crop or resize to match model input
        img = cv2.resize(frame, (64, 64))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)  # (1, 64, 64, 3)

        # Make prediction
        pred = self.model.predict(img, verbose=0)
        index = np.argmax(pred)
        return self.label_dict.get(index, "?")
