"""
SilentLink — alphabet model training (landmark features → letters).

Reads the .npz produced by `extract_landmarks.py` and trains a small
multi-layer perceptron with scikit-learn. The trained weights + scaler are
exported to a compact JSON file that the FastAPI backend loads at startup and
runs as a pure NumPy forward pass — the server therefore does NOT need
TensorFlow, scikit-learn or any large runtime dependency just to classify.

Key design point (why this stays small and honest):
  - Input  : 63 landmarks features (21 points x (x,y,z), wrist-relative, scaled).
  - Model  : MLP hidden [64, 32] -> 26 (or N) ASL letters via softmax.
  - Output : models/alphabet_mlp.json  {scaler_mean, scaler_scale, weights,
             biases, classes, confusion artifacts later added by evaluate}.

Metrics are ONLY reported by evaluate_alphabet.py after a real train/held-out
run. No numbers are invented here.

Usage:
    veenv\\Scripts\\python.exe training\\train_alphabet.py \
        --data data/asl_landmarks.npz \
        --out models/alphabet_mlp.json
"""

import argparse
import json
import os
import time

import numpy as np

try:
    from sklearn.neural_network import MLPClassifier
except Exception as e:
    raise SystemExit(f"scikit-learn not available: {e}")

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/asl_landmarks.npz")
    parser.add_argument("--out", default="models/alphabet_mlp.json")
    parser.add_argument("--val", type=float, default=0.15, help="Fraction held out as validation.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--hidden", default="64,32", help="Comma separated hidden sizes.")
    parser.add_argument("--min-samples", type=int, default=30,
                        help="Drop classes with fewer samples than this (honest guard for empty classes).")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        raise SystemExit(f"Missing landmark data: {args.data}. Run extract_landmarks.py first.")

    npz = np.load(args.data, allow_pickle=True)
    X = npz["X"].astype(np.float32)
    y = npz["y"].astype(np.int64)
    class_names = [str(c) for c in npz["class_names"]]
    print(f"Loaded {X.shape} features, {len(class_names)} classes: {class_names}")

    # Drop classes with too few samples (e.g. `nothing` had 0 detections).
    # StratifiedKFold needs >= 2 samples per class; an empty class would crash
    # the split. Kept classes are remapped 0..K-1 so the exported JSON is
    # contiguous and self-consistent.
    keep = [i for i in range(len(class_names)) if np.sum(y == i) >= args.min_samples]
    dropped = [class_names[i] for i in range(len(class_names)) if i not in keep]
    if dropped:
        print(f"Dropped {len(dropped)} low-sample class(es): {dropped}")
    X = X[np.isin(y, keep)]
    y = y[np.isin(y, keep)]
    remap = {old: new for new, old in enumerate(keep)}
    y = np.array([remap[int(v)] for v in y], dtype=np.int64)
    class_names = [class_names[i] for i in keep]
    print(f"Keeping {len(class_names)} classes: {class_names}")

    hidden_sizes = tuple(int(h) for h in args.hidden.split(",") if h.strip())
    print(f"Model: MLP hidden={hidden_sizes} softmax -> {len(class_names)} classes")

    skf = StratifiedKFold(n_splits=int(1.0 / args.val), shuffle=True, random_state=args.seed)
    tr_idx, va_idx = next(skf.split(X, y))

    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X[tr_idx])
    X_va = scaler.transform(X[va_idx])
    y_tr = y[tr_idx]
    y_va = y[va_idx]

    print(f"Train: {len(y_tr)} samples | Validate: {len(y_va)} samples")

    t0 = time.time()
    clf = MLPClassifier(
        hidden_layer_sizes=hidden_sizes,
        activation="relu",
        solver="adam",
        alpha=1e-3,
        batch_size="auto",
        learning_rate="adaptive",
        max_iter=200,
        early_stopping=True,
        n_iter_no_change=15,
        validation_fraction=0.12,
        random_state=args.seed,
    )
    clf.fit(X_tr, y_tr)
    train_time = time.time() - t0

    val_acc = float(clf.score(X_va, y_va))
    print(f"Training finished in {train_time:.1f}s")
    print(f"Validation accuracy: {val_acc * 100:.2f}%")

    layers = []
    for i, (w, b) in enumerate(zip(clf.coefs_, clf.intercepts_)):
        layers.append({"weights": w.astype(float).tolist(), "bias": b.astype(float).tolist()})

    payload = {
        "format": "silentlink-alphabet-mlp-v1",
        "trained_on": os.path.basename(args.data),
        "train_time_s": round(train_time, 2),
        "n_classes": len(class_names),
        "classes": class_names,
        "hidden_sizes": list(hidden_sizes),
        "scaler": {
            "mean": scaler.mean_.astype(float).tolist(),
            "scale": scaler.scale_.astype(float).tolist(),
        },
        "layers": layers,
        "evaluation": None,
    }

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    print(f"Exported runtime model to {args.out}")
    print("Next: run training/evaluate_alphabet.py to fill the metrics card.")


if __name__ == "__main__":
    main()
