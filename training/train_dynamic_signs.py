"""
SilentLink — dynamic sign model training (sequence landmarks -> words/signs).

Reads a folder of per-sign .npy sequences produced by a landmark extractor
and trains a small BiLSTM classifier with PyTorch. The trained weights are
exported to a compact JSON file that the FastAPI backend can load at startup
and run as a pure NumPy forward pass — the server therefore does NOT need
PyTorch or any large runtime dependency just to classify dynamic signs.

Key design point (why this stays small and honest):
  - Input  : (seq_len, 63) per sample — 63 normalized landmarks per frame.
  - Model  : BiLSTM hidden=H layers=L -> linear classifier -> N classes.
  - Output : models/dynamic_sign_lstm.json  {format, seq_len, classes,
             hidden_sizes, num_layers, layers:[[weights,biases],...]}

The dataset layout is documented in dataset/README.md under the "sequences"
section. Users must supply their own data; none is packaged with the repo.

Usage:
    veenv\\Scripts\\python.exe training\\train_dynamic_signs.py \
        --seq-dataset dataset/sequences \
        --out models/dynamic_sign_lstm.json
"""

import argparse
import json
import os
import time

import numpy as np


def _import_torch_or_die():
    """Guard PyTorch import with a clear, friendly RuntimeError."""
    try:
        import torch
        return torch
    except Exception as e:
        raise RuntimeError(
            "PyTorch not installed. Install requirements-training.txt then re-run. "
            "You can still run alphabet fingerspelling recognition using the "
            "StaticSignRecognizer (MLP) without this model."
        ) from e


def _load_classes_txt(path):
    """Load optional class filter from a one-class-per-line text file."""
    if not os.path.exists(path):
        raise RuntimeError(f"Classes file not found: {path!r}")
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _load_seq_dataset(seq_dataset, seq_len, classes_filter=None):
    """Scan `seq_dataset/sequences/<sign>/sample_XXXX.npy`, pad/trim to seq_len.

    Returns (X, y, class_names) where X has shape (N, seq_len, 63).
    """
    sequences_root = os.path.join(seq_dataset, "sequences")
    if not os.path.isdir(sequences_root):
        raise RuntimeError(
            f"Dataset folder not found: {seq_dataset!r}. The expected layout is "
            f"described in dataset/README.md. Please download or prepare a sequences "
            f"dataset first — no sample data ships with the SilentLink repository. "
            f"Tip: search keywords 'WLASL' 'ASLLVD' 'sign language video dataset' to "
            f"find public downloads, then extract per-frame MediaPipe landmarks to "
            f"the layout <seq_dataset>/sequences/<sign>/sample_XXXX.npy."
        )

    sign_names = sorted(os.listdir(sequences_root))
    sign_names = [s for s in sign_names if os.path.isdir(os.path.join(sequences_root, s))]

    if classes_filter is not None:
        sign_names = [s for s in sign_names if s in set(classes_filter)]

    X_list = []
    y_list = []

    for ci, sign in enumerate(sign_names):
        sign_dir = os.path.join(sequences_root, sign)
        samples = sorted(
            f for f in os.listdir(sign_dir)
            if f.lower().endswith(".npy")
        )
        for fname in samples:
            fpath = os.path.join(sign_dir, fname)
            try:
                arr = np.load(fpath)
            except Exception as e:
                raise RuntimeError(f"Failed to read {fpath!r}: {e}") from e

            if arr.ndim == 3 and arr.shape[1:] == (21, 3):
                arr = arr.reshape(arr.shape[0], -1)

            if arr.ndim != 2 or arr.shape[1] != 63:
                raise RuntimeError(
                    f"Unexpected shape in {fpath!r}: got {arr.shape}, "
                    f"expected (seq_len, 63) or (seq_len, 21, 3)."
                )

            T = arr.shape[0]
            if T >= seq_len:
                arr = arr[:seq_len]
            else:
                pad = np.zeros((seq_len - T, 63), dtype=arr.dtype)
                arr = np.concatenate([arr, pad], axis=0)

            X_list.append(arr.astype(np.float32))
            y_list.append(ci)

    if not X_list:
        raise RuntimeError(
            f"No .npy samples found under {sequences_root!r}. Check the dataset "
            f"layout described in dataset/README.md and download/prepare your data."
        )

    X = np.stack(X_list, axis=0)
    y = np.asarray(y_list, dtype=np.int64)
    return X, y, sign_names


def main():
    parser = argparse.ArgumentParser(
        description="Train a BiLSTM dynamic sign classifier on MediaPipe landmark sequences.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--seq-dataset",
        default=None,
        help="Root folder containing sequences/<sign>/sample_XXXX.npy of shape (seq_len, 63) or (seq_len, 21, 3).",
    )
    parser.add_argument("--seq-len", type=int, default=30, help="Frames per sample (truncated or zero-padded).")
    parser.add_argument(
        "--classes",
        default=None,
        help="Optional .txt file with one class name per line to restrict training to a subset.",
    )
    parser.add_argument("--out", default="models/dynamic_sign_lstm.json", help="Output JSON model path.")
    parser.add_argument("--hidden", type=int, default=64, help="BiLSTM hidden size per direction.")
    parser.add_argument("--layers", type=int, default=2, help="Number of stacked BiLSTM layers.")
    parser.add_argument("--epochs", type=int, default=30, help="Maximum training epochs.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--val", type=float, default=0.15, help="Fraction of samples held out for validation.")
    args = parser.parse_args()

    if args.seq_dataset is None:
        raise RuntimeError(
            "Missing --seq-dataset argument. No dataset folder was provided. "
            "Please download or prepare a sequences dataset as described in dataset/README.md, "
            "then re-run with --seq-dataset pointing at the root folder containing "
            "sequences/<sign>/sample_XXXX.npy files. No sample data ships with SilentLink — "
            "see dataset/README.md for public download links (keywords: WLASL, ASLLVD, MS-ASL)."
        )

    torch = _import_torch_or_die()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    if not os.path.isdir(args.seq_dataset):
        raise RuntimeError(
            f"Dataset folder not found: {args.seq_dataset!r}. The expected layout is "
            f"described in dataset/README.md. Please download or prepare a sequences "
            f"dataset first — no sample data ships with the SilentLink repository."
        )

    classes_filter = None
    if args.classes is not None:
        classes_filter = _load_classes_txt(args.classes)

    X, y, class_names = _load_seq_dataset(args.seq_dataset, args.seq_len, classes_filter)
    n_classes = len(class_names)
    print(f"Loaded {X.shape[0]} sequences of shape {X.shape[1:]} -> {n_classes} classes: {class_names}")

    try:
        from sklearn.model_selection import train_test_split
        X_tr, X_va, y_tr, y_va = train_test_split(
            X, y, test_size=args.val, random_state=args.seed, stratify=y
        )
    except Exception:
        rng = np.random.default_rng(args.seed)
        idx = rng.permutation(len(X))
        n_va = max(1, int(len(X) * args.val))
        va_idx = idx[:n_va]
        tr_idx = idx[n_va:]
        X_tr, X_va = X[tr_idx], X[va_idx]
        y_tr, y_va = y[tr_idx], y[va_idx]

    print(f"Train: {len(y_tr)} | Validate: {len(y_va)}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    X_tr_t = torch.from_numpy(X_tr).float().to(device)
    X_va_t = torch.from_numpy(X_va).float().to(device)
    y_tr_t = torch.from_numpy(y_tr).long().to(device)
    y_va_t = torch.from_numpy(y_va).long().to(device)

    class BiLSTMClassifier(torch.nn.Module):
        def __init__(self, input_dim, hidden_size, num_layers, num_classes):
            super().__init__()
            self.lstm = torch.nn.LSTM(
                input_size=input_dim,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                bidirectional=True,
            )
            self.dropout = torch.nn.Dropout(0.3)
            self.fc = torch.nn.Linear(hidden_size * 2, num_classes)

        def forward(self, x):
            out, _ = self.lstm(x)
            out = out[:, -1, :]
            out = self.dropout(out)
            return self.fc(out)

    model = BiLSTMClassifier(
        input_dim=63,
        hidden_size=args.hidden,
        num_layers=args.layers,
        num_classes=n_classes,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.CrossEntropyLoss()

    batch_size = 32
    best_val_acc = -1.0
    best_state = None

    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        perm = torch.randperm(len(X_tr_t), device=device)
        total_loss = 0.0
        n_batches = 0
        for start in range(0, len(X_tr_t), batch_size):
            bi = perm[start:start + batch_size]
            xb = X_tr_t[bi]
            yb = y_tr_t[bi]
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())
            n_batches += 1

        model.eval()
        with torch.no_grad():
            va_logits = model(X_va_t)
            va_pred = va_logits.argmax(dim=1)
            val_acc = float((va_pred == y_va_t).float().mean().item())

        avg_loss = total_loss / max(n_batches, 1)
        print(f"epoch {epoch + 1}/{args.epochs}  loss={avg_loss:.4f}  val_acc={val_acc * 100:.2f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    train_time = time.time() - t0
    print(f"Training finished in {train_time:.1f}s  |  best val_acc={best_val_acc * 100:.2f}%")

    if best_state is None:
        best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    layers_json = []
    for k in sorted(best_state.keys()):
        tensor = best_state[k]
        layers_json.append([k, tensor.numpy().tolist()])

    payload = {
        "format": "silentlink-dynamic-lstm-v1",
        "seq_len": int(args.seq_len),
        "classes": class_names,
        "hidden_sizes": [int(args.hidden)] * int(args.layers),
        "num_layers": int(args.layers),
        "bidirectional": True,
        "input_dim": 63,
        "best_val_acc": round(best_val_acc, 6),
        "train_time_s": round(train_time, 2),
        "epochs_trained": args.epochs,
        "layers": layers_json,
    }

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    print(f"Exported runtime model to {args.out}")


if __name__ == "__main__":
    main()
