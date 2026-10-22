"""
SilentLink — alphabet model evaluation + model-card finalization.

Loads the scikit-learn checkpoint (mmap-friendly) and the SAME data split +
seed used by train_alphabet.py, then:

  1. Recomputes the correct train/validation split (identical seed+kwargs).
  2. Runs the pure-NumPy forward pass used at runtime (softmax MLP) so the
     metrics reflect EXACTLY what the server will do — not a separate
     sk-learn inference path.
  3. Reports: held-out accuracy, per-class precision/recall, and a confusion
     matrix (top confusions listed).
  4. Writes all of it back into the exported JSON model card
     (models/alphabet_mlp.json["evaluation"]) so metrics live next to weights.

No numbers are fabricated here — everything printed comes from this run.

Usage:
    veenv\\Scripts\\python.exe training\\evaluate_alphabet.py \
        --model models/alphabet_mlp.json \
        --data data/asl_landmarks.npz \
        --seed 42 --val 0.15
"""

import argparse
import json
import time

import numpy as np


def forward(X, payload):
    """Exact runtime forward pass (mirror of backend/recognition/alphabet.py).
    Hand-rolled so the numbers we report are the numbers users get at runtime."""
    x = np.asarray(X, dtype=np.float64)
    x = (x - np.asarray(payload["scaler"]["mean"])) / np.asarray(payload["scaler"]["scale"])
    for layer in payload["layers"]:
        w = np.asarray(layer["weights"], dtype=np.float64)
        b = np.asarray(layer["bias"], dtype=np.float64)
        x = x @ w + b
        x = np.maximum(x, 0.0)
    e = np.exp(x - x.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/alphabet_mlp.json")
    parser.add_argument("--data", default="data/asl_landmarks.npz")
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with open(args.model, "r", encoding="utf-8") as f:
        payload = json.load(f)
    npz = np.load(args.data, allow_pickle=True)
    X = npz["X"].astype(np.float64)
    y = npz["y"].astype(np.int64)
    class_names = [str(c) for c in npz["class_names"]]

    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=int(1.0 / args.val), shuffle=True, random_state=args.seed)
    tr_idx, va_idx = next(skf.split(X, y))

    t0 = time.time()
    proba = forward(X[va_idx], payload)
    elapsed = time.time() - t0
    pred = proba.argmax(axis=1)
    truth = y[va_idx]

    acc = float((pred == truth).mean())
    confidences = proba.max(axis=1)

    per = {}
    for c in range(len(class_names)):
        mask = truth == c
        if mask.sum() == 0:
            per[class_names[c]] = {"n": 0, "precision": None, "recall": None}
            continue
        tp = int(((pred == c) & mask).sum())
        fp = int(((pred == c) & ~mask).sum())
        fn = int(mask.sum() - tp)
        per[class_names[c]] = {
            "n": int(mask.sum()),
            "precision": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
            "recall": round(tp / (tp + fn), 4) if (tp + fn) else 0.0,
        }

    cm = np.zeros((len(class_names), len(class_names)), dtype=int)
    for t, p in zip(truth, pred):
        cm[t, p] += 1
    confusions = []
    for t in range(len(class_names)):
        for p in range(len(class_names)):
            if t != p and cm[t, p] > 0:
                confusions.append((int(cm[t, p]), class_names[t], class_names[p]))
    confusions.sort(reverse=True)

    print("=" * 60)
    print("Alphabet model evaluation (pure-NumPy runtime forward path)")
    print("=" * 60)
    print(f"Validation samples : {len(truth)}")
    print(f"Held-out accuracy  : {acc * 100:.2f}%")
    print(f"Mean confidence    : {confidences.mean() * 100:.2f}%")
    print(f"Inference (val set): {elapsed:.1f}s")
    print("-" * 60)
    print("Per-class (n / precision / recall):")
    for k, v in per.items():
        print(f"  {k:<4} n={v['n']:<5} prec={v['precision']} recall={v['recall']}")
    print("-" * 60)
    print("Top confusions (true -> predicted):")
    for n, t, p in confusions[:10]:
        print(f"  {t} -> {p}  x{n}")
    print("-" * 60)

    payload["evaluation"] = {
        "held_out_val_fraction": args.val,
        "seed": args.seed,
        "samples": int(len(truth)),
        "accuracy": round(acc, 4),
        "mean_confidence": round(float(confidences.mean()), 4),
        "per_class": per,
        "top_confusions": [{"true": t, "pred": p, "n": n} for n, t, p in confusions[:10]],
        "confusion_matrix": cm.tolist(),
        "runtime_forward_path": "pure-numpy softmax MLP (backend/recognition/alphabet.py)",
        "evaluated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }
    with open(args.model, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("Evaluation metrics written into the model card JSON.")


if __name__ == "__main__":
    main()
