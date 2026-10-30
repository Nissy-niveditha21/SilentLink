from __future__ import annotations

from copy import copy
import json
import logging
import os
from collections import deque
from typing import Optional

import numpy as np


log = logging.getLogger(__name__)


class DynamicSignRecognizer:
    """NumPy runtime for the exported bidirectional LSTM sign classifier."""

    def __init__(
        self,
        max_seq_len: int = 30,
        model_path: Optional[str] = os.path.join("models", "dynamic_sign_lstm.json"),
    ):
        self.max_seq_len = max_seq_len
        self.model_path = model_path
        self.seq_buffer: deque = deque(maxlen=max_seq_len)
        self._frames_since_prediction = 0
        self._last_prediction: Optional[dict] = None
        self.model = None
        self.class_names: list[str] = []
        self.state: dict[str, np.ndarray] = {}
        self.hidden_size = 0
        self.num_layers = 0

        if model_path is None or not os.path.isfile(model_path):
            log.warning("Dynamic sign model not found at %s; dynamic recognition is disabled.", model_path)
            return

        with open(model_path, "r", encoding="utf-8") as model_file:
            payload = json.load(model_file)
        if payload.get("format") != "silentlink-dynamic-lstm-v1":
            raise ValueError(f"Unsupported dynamic sign model format in {model_path!r}.")

        self.max_seq_len = int(payload["seq_len"])
        self.seq_buffer = deque(maxlen=self.max_seq_len)
        self.class_names = [str(name) for name in payload["classes"]]
        self.num_layers = int(payload["num_layers"])
        self.hidden_size = int(payload["hidden_sizes"][0])
        self.state = {
            name: np.asarray(value, dtype=np.float32)
            for name, value in payload["layers"]
        }
        self._validate_model()
        self.model = payload
        log.info("Loaded dynamic sign model with %d classes.", len(self.class_names))

    def _validate_model(self) -> None:
        expected = {"fc.weight", "fc.bias"}
        for layer in range(self.num_layers):
            for direction in ("", "_reverse"):
                suffix = f"_l{layer}{direction}"
                expected.update({
                    f"lstm.weight_ih{suffix}",
                    f"lstm.weight_hh{suffix}",
                    f"lstm.bias_ih{suffix}",
                    f"lstm.bias_hh{suffix}",
                })
        missing = expected - self.state.keys()
        if missing:
            raise ValueError(f"Dynamic sign model is missing weights: {sorted(missing)}")
        if len(self.class_names) != self.state["fc.bias"].shape[0]:
            raise ValueError("Dynamic sign model class list does not match its output layer.")

    def add_frame(self, feat_63) -> None:
        if feat_63 is None:
            return
        arr = np.asarray(feat_63, dtype=np.float32).reshape(-1)
        if arr.shape[0] == 63:
            self.seq_buffer.append(arr)
            self._frames_since_prediction += 1

    def _run_lstm_direction(
        self,
        sequence: np.ndarray,
        layer: int,
        reverse: bool,
    ) -> np.ndarray:
        direction = "_reverse" if reverse else ""
        suffix = f"_l{layer}{direction}"
        weight_ih = self.state[f"lstm.weight_ih{suffix}"]
        weight_hh = self.state[f"lstm.weight_hh{suffix}"]
        bias_ih = self.state[f"lstm.bias_ih{suffix}"]
        bias_hh = self.state[f"lstm.bias_hh{suffix}"]
        hidden = np.zeros(self.hidden_size, dtype=np.float32)
        cell = np.zeros(self.hidden_size, dtype=np.float32)
        outputs = np.zeros((len(sequence), self.hidden_size), dtype=np.float32)
        timesteps = range(len(sequence) - 1, -1, -1) if reverse else range(len(sequence))

        for timestep in timesteps:
            gates = (
                weight_ih @ sequence[timestep]
                + bias_ih
                + weight_hh @ hidden
                + bias_hh
            )
            input_gate, forget_gate, cell_gate, output_gate = np.split(gates, 4)
            input_gate = 1.0 / (1.0 + np.exp(-np.clip(input_gate, -60.0, 60.0)))
            forget_gate = 1.0 / (1.0 + np.exp(-np.clip(forget_gate, -60.0, 60.0)))
            output_gate = 1.0 / (1.0 + np.exp(-np.clip(output_gate, -60.0, 60.0)))
            cell_gate = np.tanh(cell_gate)
            cell = forget_gate * cell + input_gate * cell_gate
            hidden = output_gate * np.tanh(cell)
            outputs[timestep] = hidden

        return outputs

    def predict_sequence(self, sequence) -> Optional[dict]:
        if self.model is None:
            return None

        values = np.asarray(sequence, dtype=np.float32)
        if values.shape != (self.max_seq_len, 63):
            raise ValueError(
                f"Expected a sequence of shape {(self.max_seq_len, 63)}, got {values.shape}."
            )

        layer_input = values
        for layer in range(self.num_layers):
            forward = self._run_lstm_direction(layer_input, layer, reverse=False)
            backward = self._run_lstm_direction(layer_input, layer, reverse=True)
            layer_input = np.concatenate((forward, backward), axis=1)

        logits = self.state["fc.weight"] @ layer_input[-1] + self.state["fc.bias"]
        probabilities = np.exp(logits - np.max(logits))
        probabilities /= probabilities.sum()
        index = int(np.argmax(probabilities))
        return {
            "sign": self.class_names[index].upper(),
            "confidence": float(probabilities[index]),
            "kind": "phrase",
        }

    def predict(self) -> Optional[dict]:
        if not self.ready() or self.model is None:
            return None
        if self._last_prediction is not None and self._frames_since_prediction < 3:
            return self._last_prediction
        self._frames_since_prediction = 0
        self._last_prediction = self.predict_sequence(np.stack(tuple(self.seq_buffer)))
        return self._last_prediction

    def ready(self) -> bool:
        return len(self.seq_buffer) >= self.max_seq_len

    def clear(self) -> None:
        self.seq_buffer.clear()
        self._frames_since_prediction = 0
        self._last_prediction = None

    def new_session(self) -> DynamicSignRecognizer:
        session = copy(self)
        session.seq_buffer = deque(maxlen=self.max_seq_len)
        session._frames_since_prediction = 0
        session._last_prediction = None
        return session
