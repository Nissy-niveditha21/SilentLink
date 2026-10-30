"""
SilentLink — landmark extraction from the ASL alphabet image dataset.

For every image we:
  1. Run MediaPipe Hands in static image mode to detect a single hand.
  2. If a hand is found, collect its 21 xyz hand landmarks.
  3. Normalize features (wrist-relative origin + scale) so the training signal is
     robust to hand size, distance from camera and position in the frame.
  4. Save the resulting (features, class_index) pairs to a compressed .npz file.

The .npz file then feeds train_alphabet.py. This is a one-time / repeatable
offline step; the running app never needs this script nor the raw images.

Normalization details (see feature plumbing used at runtime too):
  - Origin  : wrist landmark (index 0).
  - Scale   : distance from wrist to middle-finger MCP (index 9) plus a tiny
              epsilon so coordinates are invariant to hand size / camera distance.
  - Output  : 21 points x 3 (x, y, z) = 63 float features per hand.

Usage:
    veenv\\Scripts\\python.exe training\\extract_landmarks.py \
        --data data/asl_alphabet_train \
        --out data/asl_landmarks.npz \
        --samples 400

Notes:
  - `--samples` caps the number of images read per class. The dataset has ~3000
    images per class, but a few hundred per class is plenty for a 63-feature MLP
    and keeps extraction time reasonable on a student laptop.
  - Non-alphabet helper folders (del / nothing / space) are mapped to dedicated
    pseudo-classes so a "no letter / rest pose" can be recognized. Only folders
    present in `--data` are used.
"""

import argparse
import os
import time

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Extract normalized hand landmarks from ASL alphabet images.")
    parser.add_argument("--data", default="data/asl_alphabet_train", help="Root of per-class image folders.")
    parser.add_argument("--test-data", default=None, help="Optional test folder (class folders or files named A_test.jpg).")
    parser.add_argument("--out", default="data/asl_landmarks.npz", help="Output .npz path.")
    parser.add_argument("--samples", type=int, default=400, help="Max images used per class.")
    parser.add_argument("--pad", type=int, default=40, help="Bounding-box padding in px (unused here, kept for parity).")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.samples < 1:
        parser.error("--samples must be positive")
    rng = np.random.default_rng(args.seed)

    if not os.path.isdir(args.data):
        raise SystemExit(f"Dataset folder not found: {args.data!r}")

    try:
        import mediapipe as mp
    except ImportError as error:
        raise SystemExit(
            "MediaPipe is required to extract alphabet landmarks. Install requirements.txt first."
        ) from error

    class_names = sorted(os.listdir(args.data))
    class_names = [c for c in class_names if os.path.isdir(os.path.join(args.data, c))]
    print(f"Classes ({len(class_names)}): {class_names}")

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.6,
    )
    mp_draw = mp.solutions.drawing_utils

    features_list = []
    labels_list = []
    test_features = []
    test_labels = []

    t_start = time.time()
    total_imgs = 0
    total_ok = 0
    per_class = {}

    for ci, cls in enumerate(class_names):
        cls_dir = os.path.join(args.data, cls)
        all_files = sorted(
            f for f in os.listdir(cls_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        )
        if len(all_files) > args.samples:
            selected = rng.choice(len(all_files), size=args.samples, replace=False)
            files = [all_files[index] for index in sorted(selected)]
        else:
            files = all_files

        ok = 0
        for fname in files:
            path = os.path.join(cls_dir, fname)
            img = cv2.imread(path)
            if img is None:
                continue
            total_imgs += 1

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            if not res.multi_hand_landmarks:
                continue

            lm = res.multi_hand_landmarks[0].landmark
            pts = np.array([[p.x, p.y, p.z] for p in lm], dtype=np.float32)

            origin = pts[0]
            scale = np.linalg.norm(pts[9] - pts[0]) + 1e-6
            feat = (pts - origin) / scale
            features_list.append(feat.reshape(-1))
            labels_list.append(ci)
            ok += 1

        total_ok += ok
        per_class[cls] = ok
        print(f"[{time.time() - t_start:6.1f}s] {cls}: {ok}/{len(files)} images with a detected hand")

    if args.test_data:
        if not os.path.isdir(args.test_data):
            hands.close()
            raise SystemExit(f"Test dataset folder not found: {args.test_data!r}")

        class_indices = {name.upper(): index for index, name in enumerate(class_names)}
        test_images = []
        for entry in sorted(os.listdir(args.test_data)):
            entry_path = os.path.join(args.test_data, entry)
            if os.path.isdir(entry_path):
                label = entry.upper()
                files = sorted(
                    filename for filename in os.listdir(entry_path)
                    if filename.lower().endswith((".jpg", ".jpeg", ".png"))
                )
                test_images.extend((os.path.join(entry_path, filename), label) for filename in files)
            elif entry.lower().endswith((".jpg", ".jpeg", ".png")):
                label = os.path.splitext(entry)[0].split("_")[0].upper()
                test_images.append((entry_path, label))

        for path, label in test_images:
            if label not in class_indices:
                continue
            image = cv2.imread(path)
            if image is None:
                continue
            result = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            if not result.multi_hand_landmarks:
                continue
            points = np.array(
                [[point.x, point.y, point.z] for point in result.multi_hand_landmarks[0].landmark],
                dtype=np.float32,
            )
            origin = points[0]
            scale = np.linalg.norm(points[9] - origin) + 1e-6
            test_features.append(((points - origin) / scale).reshape(-1))
            test_labels.append(class_indices[label])

    hands.close()

    if not features_list:
        raise SystemExit("No landmarks were extracted — nothing to train on.")
    if args.test_data and not test_features:
        raise SystemExit(
            "No test landmarks were extracted. Check the test labels and hand visibility."
        )

    X = np.asarray(features_list, dtype=np.float32)
    y = np.asarray(labels_list, dtype=np.int64)

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    payload = {
        "X": X,
        "y": y,
        "class_names": np.asarray(class_names, dtype=object),
    }
    if test_features:
        payload["X_test"] = np.asarray(test_features, dtype=np.float32)
        payload["y_test"] = np.asarray(test_labels, dtype=np.int64)
        print(f"Extracted {len(test_features)} test samples with detected hands.")
    np.savez_compressed(args.out, **payload)

    print("-" * 60)
    print(f"Extracted {len(features_list)} landmark samples from {total_imgs} images")
    print(f"Detection rate: {100.0 * total_ok / max(total_imgs, 1):.1f}%")
    print(f"Saved to: {args.out}")
    print(f"Elapsed: {time.time() - t_start:.1f}s")
    print("Per-class sample counts:")
    for cls in class_names:
        print(f"  {cls:<3} {per_class.get(cls, 0)}")


if __name__ == "__main__":
    main()
