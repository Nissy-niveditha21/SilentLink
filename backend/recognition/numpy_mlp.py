import json
import os
import numpy as np


class ModelNotTrainedError(Exception):
    pass


class NumpyMLP:
    def __init__(self, model_path: str = os.path.join("models", "alphabet_mlp.json")):
        if not os.path.exists(model_path):
            raise ModelNotTrainedError(
                f"Model file not found at {model_path}. Run training pipeline."
            )
        with open(model_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        self.payload = payload
        self.class_names = payload["classes"]
        self.scaler_mean = np.asarray(payload["scaler"]["mean"], dtype=np.float32)
        self.scaler_scale = np.asarray(payload["scaler"]["scale"], dtype=np.float32)
        self.layers = payload["layers"]

    def forward(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x = (X.astype(np.float32) - self.scaler_mean) / self.scaler_scale
        n_layers = len(self.layers)
        for i, layer in enumerate(self.layers):
            W = np.asarray(layer["weights"], dtype=np.float32)
            b = np.asarray(layer["bias"], dtype=np.float32)
            x = x @ W + b
            if i < n_layers - 1:
                x = np.maximum(x, 0.0)
        logits = x
        shifted = logits - np.max(logits, axis=1, keepdims=True)
        exp_shifted = np.exp(shifted)
        proba = exp_shifted / np.sum(exp_shifted, axis=1, keepdims=True)
        return proba, logits

    def predict_proba(self, feat: np.ndarray):
        if feat.ndim == 1:
            X = feat.reshape(1, -1)
        else:
            X = feat
        proba, _logits = self.forward(X)
        if X.shape[0] == 1:
            p = proba[0]
            idx = int(np.argmax(p))
            return p, float(p[idx]), self.class_names[idx]
        return proba
