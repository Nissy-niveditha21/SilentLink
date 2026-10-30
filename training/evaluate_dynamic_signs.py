"""Evaluate a trained dynamic-sign model against the dataset's test split."""

import argparse
import json
import os
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.recognition.dynamic_sign_recognizer import DynamicSignRecognizer
from training.train_dynamic_signs import _load_seq_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seq-dataset", required=True, help="Dataset root with official split folders.")
    parser.add_argument("--model", default="models/dynamic_sign_lstm.json")
    parser.add_argument("--seq-len", type=int, default=None)
    parser.add_argument("--classes", default=None, help="Optional one-class-per-line filter file.")
    args = parser.parse_args()

    classes_filter = None
    if args.classes:
        with open(args.classes, "r", encoding="utf-8") as class_file:
            classes_filter = [line.strip() for line in class_file if line.strip()]

    with open(args.model, "r", encoding="utf-8") as model_file:
        payload = json.load(model_file)
    seq_len = int(payload["seq_len"])
    if args.seq_len is not None and args.seq_len != seq_len:
        raise SystemExit(f"--seq-len must match the model sequence length ({seq_len}).")

    X, y, dataset_classes, splits = _load_seq_dataset(
        args.seq_dataset, seq_len, classes_filter
    )
    if not np.any(splits == "test"):
        raise SystemExit("No official test split found. Evaluation requires held-out test sequences.")

    model_classes = [str(name) for name in payload["classes"]]
    model = DynamicSignRecognizer(
        max_seq_len=seq_len,
        model_path=args.model,
    )

    class_indices = {
        dataset_index: next(
            model_index for model_index, model_name in enumerate(model_classes)
            if model_name.upper() == name.upper()
        )
        for dataset_index, name in enumerate(dataset_classes)
        if any(model_name.upper() == name.upper() for model_name in model_classes)
    }
    test_indices = [
        index for index, label in enumerate(y)
        if splits[index] == "test" and int(label) in class_indices
    ]
    if not test_indices:
        raise SystemExit("No test samples match the classes present in this model.")

    predictions = []
    truth = []
    for index in test_indices:
        result = model.predict_sequence(X[index])
        predictions.append(next(
            class_index for class_index, name in enumerate(model_classes)
            if name.upper() == result["sign"].upper()
        ))
        truth.append(class_indices[int(y[index])])

    predictions = np.asarray(predictions, dtype=np.int64)
    truth = np.asarray(truth, dtype=np.int64)
    accuracy = float(np.mean(predictions == truth))
    per_class = {}
    for class_index, class_name in enumerate(model_classes):
        mask = truth == class_index
        if not np.any(mask):
            continue
        per_class[class_name] = {
            "samples": int(mask.sum()),
            "accuracy": round(float(np.mean(predictions[mask] == class_index)), 4),
        }

    payload["evaluation"] = {
        "split": "test",
        "samples": len(test_indices),
        "accuracy": round(accuracy, 4),
        "per_class": per_class,
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(args.model, "w", encoding="utf-8") as model_file:
        json.dump(payload, model_file, indent=2)

    print(f"Test samples: {len(test_indices)}")
    print(f"Test accuracy: {accuracy * 100:.2f}%")
    for class_name, metrics in per_class.items():
        print(f"{class_name}: {metrics['accuracy'] * 100:.2f}% ({metrics['samples']} samples)")


if __name__ == "__main__":
    main()
