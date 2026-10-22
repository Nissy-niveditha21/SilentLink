import os
import cv2
import numpy as np
from collections import Counter

# =========================
# SETTINGS
# =========================
DATASET_DIR = "data/asl_alphabet_train"

IMG_SIZE = 64

# =========================
# DATASET INFORMATION
# =========================
print("\n========== DATASET INFO ==========\n")

classes = sorted([
    d for d in os.listdir(DATASET_DIR)
    if os.path.isdir(os.path.join(DATASET_DIR, d))
])

print("Number of classes:", len(classes))
print("Classes:", classes)

all_pixels = []
image_count = 0
class_counts = {}

for cls in classes:

    class_path = os.path.join(DATASET_DIR, cls)

    images = [
        f for f in os.listdir(class_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    class_counts[cls] = len(images)
    image_count += len(images)

    for filename in images:
        path = os.path.join(class_path, filename)

        img = cv2.imread(path)

        if img is None:
            continue

        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

        # Convert 0-255 → 0-1
        img = img.astype(np.float32) / 255.0

        all_pixels.append(img)

print("\nTotal images:", image_count)

print("\nImages per class:")
for cls, count in class_counts.items():
    print(f"{cls:15} : {count}")

# =========================
# IMAGE STATISTICS
# =========================
print("\n========== IMAGE STATISTICS ==========\n")

data = np.array(all_pixels)

print("Dataset array shape:", data.shape)
print("Image shape:", data.shape[1:])

print("Pixel minimum:", data.min())
print("Pixel maximum:", data.max())
print("Pixel mean:", data.mean())
print("Pixel standard deviation:", data.std())

# =========================
# CLASS DISTRIBUTION
# =========================
counts = np.array(list(class_counts.values()))

print("\n========== CLASS DISTRIBUTION ==========\n")

print("Minimum images/class:", counts.min())
print("Maximum images/class:", counts.max())
print("Average images/class:", counts.mean())

print("\nSmallest classes:")
for cls, count in sorted(class_counts.items(), key=lambda x: x[1])[:5]:
    print(cls, count)

print("\nLargest classes:")
for cls, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(cls, count)

# =========================
# SAMPLE IMAGE
# =========================
sample_class = classes[0]
sample_folder = os.path.join(DATASET_DIR, sample_class)

sample_files = [
    f for f in os.listdir(sample_folder)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
]

if sample_files:
    sample_path = os.path.join(sample_folder, sample_files[0])
    sample = cv2.imread(sample_path)

    print("\n========== SAMPLE IMAGE ==========\n")
    print("Sample class:", sample_class)
    print("Original image shape:", sample.shape)
    print("After resize:", (IMG_SIZE, IMG_SIZE, 3))