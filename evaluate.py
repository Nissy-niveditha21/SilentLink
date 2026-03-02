"""import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix

# --- Load model ---
model = load_model("asl_model.h5")

# --- Prepare test data ---
test_dir = "data/asl_alphabet_test"

datagen = ImageDataGenerator(rescale=1./255)

test_gen = datagen.flow_from_directory(
    test_dir,
    target_size=(64, 64),
    batch_size=32,
    class_mode='categorical',
    shuffle=False
)

# --- Evaluate model ---
loss, acc = model.evaluate(test_gen, verbose=1)
print(f"\n✅ Test Accuracy: {acc*100:.2f}%")

# --- Detailed metrics (optional) ---
y_pred = model.predict(test_gen)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true = test_gen.classes

print("\n📊 Classification Report:")
print(classification_report(y_true, y_pred_classes, target_names=list(test_gen.class_indices.keys())))

# --- Confusion matrix (optional visualization) ---
cm = confusion_matrix(y_true, y_pred_classes)
print("\n🔢 Confusion Matrix shape:", cm.shape)"""

import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model

IMG_SIZE = 64
MODEL_PATH = "asl_model.h5"
TEST_PATH = "data/asl_alphabet_test"

model = load_model(MODEL_PATH)

correct = 0
total = 0

for img_name in os.listdir(TEST_PATH):
    img_path = os.path.join(TEST_PATH, img_name)

    # Extract true label from filename
    # Example: A_test.jpg → A
    true_label = img_name.split("_")[0]

    img = cv2.imread(img_path)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)

    prediction = model.predict(img, verbose=0)
    predicted_label = chr(np.argmax(prediction) + ord('A'))

    if predicted_label == true_label:
        correct += 1

    total += 1

accuracy = correct / total * 100
print(f"\nModel Accuracy on Test Set: {accuracy:.2f}%")