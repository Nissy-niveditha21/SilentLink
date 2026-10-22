from __future__ import annotations

import math
import os
from typing import Optional

import numpy as np

from .features import landmarks_to_features
from .numpy_mlp import ModelNotTrainedError, NumpyMLP


# ---------------------------------------------------------------------------
# Basic geometry helpers
# ---------------------------------------------------------------------------

def _xy(p):
    return float(p.x), float(p.y)


def _distance(a, b) -> float:
    ax, ay = _xy(a)
    bx, by = _xy(b)
    return math.hypot(ax - bx, ay - by)


def _is_up(lm, tip_idx: int, pip_idx: int) -> bool:
    """
    Camera-space heuristic:
    smaller y means physically higher in the image.
    """
    return float(lm[tip_idx].y) < float(lm[pip_idx].y)


def _finger_states(lm):
    """
    Returns the four non-thumb finger states.

    MediaPipe indices:
      index  = 5,6,7,8
      middle = 9,10,11,12
      ring   = 13,14,15,16
      pinky  = 17,18,19,20
    """
    return {
        "index_up": _is_up(lm, 8, 6),
        "middle_up": _is_up(lm, 12, 10),
        "ring_up": _is_up(lm, 16, 14),
        "pinky_up": _is_up(lm, 20, 18),
    }


def _thumb_out(lm) -> bool:
    """
    Simple thumb extension heuristic.
    """
    return float(lm[4].x) < float(lm[3].x)


def _all_four_down(states) -> bool:
    return not (
        states["index_up"]
        or states["middle_up"]
        or states["ring_up"]
        or states["pinky_up"]
    )


def _all_four_up(states) -> bool:
    return (
        states["index_up"]
        and states["middle_up"]
        and states["ring_up"]
        and states["pinky_up"]
    )


def _all_five_up(lm, states) -> bool:
    return _all_four_up(states) and _thumb_out(lm)


# ---------------------------------------------------------------------------
# Phrase recognizer
# ---------------------------------------------------------------------------

def detect_phrase_gesture(landmarks) -> Optional[dict]:
    """
    Conservative prototype phrase detector for specific non-alphabet shapes.
    """
    if landmarks is None or len(landmarks) != 21:
        return None

    lm = landmarks
    states = _finger_states(lm)

    index_up = states["index_up"]
    middle_up = states["middle_up"]
    ring_up = states["ring_up"]
    pinky_up = states["pinky_up"]

    thumb_out = _thumb_out(lm)

    wrist = lm[0]
    middle_mcp = lm[9]
    hand_scale = _distance(wrist, middle_mcp) + 1e-6

    # GOOD: Thumb extended upwards, other fingers closed
    if (
        _all_four_down(states)
        and thumb_out
        and _distance(lm[4], lm[5]) / hand_scale > 0.75
    ):
        return {
            "sign": "GOOD",
            "confidence": 0.88,
            "kind": "phrase",
        }

    # BAD: Thumb down, other fingers closed
    if (
        _all_four_down(states)
        and not thumb_out
        and float(lm[4].y) > float(lm[3].y)
        and _distance(lm[4], lm[5]) / hand_scale > 0.70
    ):
        return {
            "sign": "BAD",
            "confidence": 0.88,
            "kind": "phrase",
        }

    # YOU: Isolated index finger
    if (
        index_up
        and not middle_up
        and not ring_up
        and not pinky_up
        and not thumb_out
    ):
        return {
            "sign": "YOU",
            "confidence": 0.72,
            "kind": "phrase",
        }

    # I: Isolated pinky finger
    if (
        not index_up
        and not middle_up
        and not ring_up
        and pinky_up
        and not thumb_out
    ):
        return {
            "sign": "I",
            "confidence": 0.72,
            "kind": "phrase",
        }

    # WE: Three middle fingers up
    if (
        index_up
        and middle_up
        and ring_up
        and not pinky_up
        and not thumb_out
    ):
        return {
            "sign": "WE",
            "confidence": 0.70,
            "kind": "phrase",
        }

    # STOP: Open palm
    if _all_five_up(lm, states):
        return {
            "sign": "STOP",
            "confidence": 0.70,
            "kind": "phrase",
        }

    return None


# ---------------------------------------------------------------------------
# Static recognizer
# ---------------------------------------------------------------------------

class StaticSignRecognizer:
    """
    Runtime recognizer for A-Z, del, space, and conservative phrase heuristics.
    """

    def __init__(
        self,
        model_path: str = os.path.join("models", "alphabet_mlp.json"),
        conf_threshold: float = 0.60,
        phrase_override_threshold: float = 0.75,
    ):
        self.model_path = model_path
        self.conf_threshold = float(conf_threshold)
        self.phrase_override_threshold = float(phrase_override_threshold)

        self.mlp: Optional[NumpyMLP] = None

        try:
            self.mlp = NumpyMLP(model_path)
        except (FileNotFoundError, KeyError, ValueError, ModelNotTrainedError):
            self.mlp = None

    def _predict_alphabet(self, landmarks) -> Optional[dict]:
        if self.mlp is None:
            return None

        features = landmarks_to_features(landmarks)

        if features is None or features.shape != (63,):
            return None

        try:
            _probs, conf, cls_name = self.mlp.predict_proba(features)
        except Exception:
            return None

        return {
            "sign": str(cls_name),
            "confidence": float(conf),
            "kind": "alphabet",
        }

    def predict(
        self,
        landmarks,
        conf_threshold: Optional[float] = None,mode=None
    ) -> Optional[dict]:
        """
        Recognition priority:
          1. Alphabet model prediction evaluated first.
          2. Phrase prediction evaluated second.
          3. If alphabet prediction is strong, keep alphabet.
          4. Otherwise, allow phrase prediction to override if alphabet is weak.
        """
        threshold = (
            self.conf_threshold
            if conf_threshold is None
            else float(conf_threshold)
        )

        if landmarks is None or len(landmarks) != 21:
            return None

        alphabet_pred = self._predict_alphabet(landmarks)
        phrase_pred = detect_phrase_gesture(landmarks)

        # 1. Strong alphabet prediction wins
        if alphabet_pred is not None:
            if alphabet_pred["confidence"] >= max(threshold, self.phrase_override_threshold):
                return alphabet_pred

        # 2. Phrase takes over if alphabet prediction is weak or non-existent
        if phrase_pred is not None:
            if alphabet_pred is None:
                return phrase_pred

            if alphabet_pred["confidence"] < self.phrase_override_threshold:
                return phrase_pred
    
        # 3. Fallback to standard alphabet threshold if applicable
        if alphabet_pred is not None and alphabet_pred["confidence"] >= threshold:
            return alphabet_pred
        
        return None