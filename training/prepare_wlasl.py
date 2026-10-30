"""Extract WLASL videos from its ZIP archive into split-aware landmark sequences."""

import argparse
import json
import os
import tempfile
import zipfile
from collections import defaultdict
from shutil import copyfileobj

import cv2
import numpy as np


def _normalized_landmarks(hand_landmarks):
    points = np.asarray(
        [[point.x, point.y, point.z] for point in hand_landmarks.landmark],
        dtype=np.float32,
    )
    origin = points[0]
    scale = np.linalg.norm(points[9] - origin) + 1e-6
    return ((points - origin) / scale).reshape(-1)


def _extract_sequence(video_path, seq_len, hands):
    capture = cv2.VideoCapture(video_path)
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0:
            return None

        frame_indices = np.linspace(0, frame_count - 1, num=seq_len, dtype=int)
        sequence = np.zeros((seq_len, 63), dtype=np.float32)
        detected = False

        for index, frame_index in enumerate(frame_indices):
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
            ok, frame = capture.read()
            if not ok:
                continue
            result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if result.multi_hand_landmarks:
                sequence[index] = _normalized_landmarks(result.multi_hand_landmarks[0])
                detected = True

        return sequence if detected else None
    finally:
        capture.release()


def main():
    parser = argparse.ArgumentParser(
        description="Convert WLASL ZIP videos into train/val/test MediaPipe sequences."
    )
    parser.add_argument("--archive", required=True, help="Path to the WLASL ZIP archive.")
    parser.add_argument("--out", default="data/wlasl", help="Output dataset root.")
    parser.add_argument(
        "--classes",
        nargs="+",
        default=["i", "love", "you"],
        help="Glosses to extract (default: i love you); omit with --all-classes.",
    )
    parser.add_argument("--all-classes", action="store_true", help="Extract every WLASL gloss.")
    parser.add_argument("--seq-len", type=int, default=30)
    parser.add_argument("--max-per-class-split", type=int, default=500)
    args = parser.parse_args()

    if args.seq_len < 1 or args.max_per_class_split < 1:
        parser.error("--seq-len and --max-per-class-split must be positive")

    try:
        import mediapipe as mp
    except ImportError as error:
        raise SystemExit(
            "MediaPipe is required to extract WLASL landmarks. Install requirements.txt first."
        ) from error

    requested = None if args.all_classes else {name.lower() for name in args.classes}
    with zipfile.ZipFile(args.archive) as archive:
        annotations = json.loads(archive.read("WLASL_v0.3.json"))
        members = set(archive.namelist())
        hands = mp.solutions.hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        counts = defaultdict(int)
        extracted = 0
        missing = 0

        try:
            for entry in annotations:
                gloss = entry["gloss"].lower()
                if requested is not None and gloss not in requested:
                    continue

                split_counts = defaultdict(int)
                for instance in entry.get("instances", []):
                    split = instance.get("split")
                    video_id = str(instance.get("video_id", ""))
                    member = f"videos/{video_id}.mp4"
                    if split not in ("train", "val", "test"):
                        continue
                    if split_counts[split] >= args.max_per_class_split:
                        continue
                    if member not in members:
                        missing += 1
                        continue

                    temporary_path = None
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp:
                            temporary_path = temp.name
                            with archive.open(member) as video_stream:
                                copyfileobj(video_stream, temp)

                        sequence = _extract_sequence(temporary_path, args.seq_len, hands)
                        if sequence is None:
                            continue

                        output_dir = os.path.join(args.out, "sequences", gloss, split)
                        os.makedirs(output_dir, exist_ok=True)
                        output_path = os.path.join(output_dir, f"{video_id}.npy")
                        np.save(output_path, sequence)
                        split_counts[split] += 1
                        counts[split] += 1
                        extracted += 1
                    finally:
                        if temporary_path and os.path.exists(temporary_path):
                            os.remove(temporary_path)

                if sum(split_counts.values()):
                    print(f"{gloss}: {dict(split_counts)}")
        finally:
            hands.close()

    if requested is not None:
        found = {entry["gloss"].lower() for entry in annotations}
        unknown = sorted(requested - found)
        if unknown:
            raise SystemExit(f"Glosses not found in WLASL annotations: {', '.join(unknown)}")

    if not extracted:
        raise SystemExit("No WLASL landmarks were extracted. Check the archive and video visibility.")

    print(f"Extracted {extracted} sequences: {dict(counts)}")
    print(f"Skipped {missing} videos absent from the archive.")
    print(f"Saved split folders under {os.path.join(args.out, 'sequences')}")


if __name__ == "__main__":
    main()
