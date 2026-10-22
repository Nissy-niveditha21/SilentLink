from __future__ import annotations

from collections import deque
from typing import Optional

import numpy as np


class DynamicSignRecognizer:
    """
    Placeholder for dynamic (multi-frame) sign recognition.

    The live pipeline currently defers to StaticSignRecognizer because no
    LSTM/GRU sequence model has been trained yet for the dynamic-class set
    (e.g. HELLO/WHAT/WHERE motion-dependent variants).

    Integration hook:
      - self.seq_buffer accumulates `max_seq_len` frames of 63-feature vectors.
      - self.ready() becomes True once enough frames have been pushed.
      - self.predict() currently returns None and is the single place to swap
        for the trained sequence model once it exists.
    """

    def __init__(self, max_seq_len: int = 30, model_path: Optional[str] = None):
        self.max_seq_len = max_seq_len
        self.model_path = model_path
        self.seq_buffer: deque = deque(maxlen=max_seq_len)
        self.model = None

    def add_frame(self, feat_63) -> None:
        if feat_63 is None:
            return
        arr = np.asarray(feat_63, dtype=np.float32).reshape(-1)
        if arr.shape[0] >= 63:
            self.seq_buffer.append(arr[:63])

    def predict(self):
        # SWAP here for LSTM/GRU forward pass after training.
        # Currently defers to StaticSignRecognizer via argument.
        # Document seq_buffer inspection only. Return None.
        _ = list(self.seq_buffer)
        return None

    def ready(self) -> bool:
        return len(self.seq_buffer) >= self.max_seq_len

    def clear(self) -> None:
        self.seq_buffer.clear()
