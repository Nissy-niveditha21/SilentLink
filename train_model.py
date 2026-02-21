import os
import cv2
import numpy as np
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential

from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.optimizers import Adam

# Path to your dataset
DATASET_DIR = 'data/asl_alphabet_train'

# Load the dataset
#TEST_DIR = 'data/asl_alphabet_test'
# Use TEST_DIR for evaluation, prediction etc.


IMG_SIZE = 64

X = []
y = []
labels = sorted(os.listdir(DATASET_DIR))
label_dict = {label: idx for idx, label in enumerate(labels)}

# Load images
print("🔄 Loading and processing images...")
for label in labels:
    folder_path = os.path.join(DATASET_DIR, label)
    for img_name in os.listdir(folder_path)[:1000]:  # Limit to 1000 per class (optional)
        img_path = os.path.join(folder_path, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        X.append(img)
        y.append(label_dict[label])

X = np.array(X)
y = to_categorical(y, num_classes=len(labels))

# Normalize
X = X / 255.0

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# CNN model
print("📦 Building model...")
model = Sequential([
    Conv2D(32, (3,3), activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 3)),
    MaxPooling2D((2,2)),
    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D((2,2)),
    Flatten(),
    Dense(128, activation='relu'),
    Dense(len(labels), activation='softmax')
])

model.compile(optimizer=Adam(), loss='categorical_crossentropy', metrics=['accuracy'])

# Train
print("🚀 Training model...")
model.fit(X_train, y_train, epochs=5, validation_data=(X_test, y_test))

# Save model
model.save("asl_model.h5")
print("✅ Model saved as asl_model.h5")
