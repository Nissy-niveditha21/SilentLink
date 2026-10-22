from __future__ import annotations

import time
from typing import Optional

from .sentence_builder import SentenceBuilder
from .stability import PredictionStabilizer


class TemporalProcessor:
    def __init__(
        self,
        conf_threshold: float = 0.6,
        min_hold_frames: int = 8,
        word_timeout_s: float = 1.8,
        stabilizer_window: int = 15,
        stabilizer_min_count: int = 10,
    ):
        self.conf_threshold = conf_threshold
        self.min_hold_frames = min_hold_frames
        self.word_timeout_s = word_timeout_s

        self.stabilizer = PredictionStabilizer(
            window_size=stabilizer_window,
            min_count=stabilizer_min_count,
        )

        self.builder = SentenceBuilder()

        self.last_pending_sign: Optional[str] = None
        self.hold_counter: int = 0
        self.hold_current: Optional[str] = None

        self.last_confirmed_sign: Optional[str] = None
        self.last_confirmed_kind: Optional[str] = None
        self.last_confirm_ts: Optional[float] = None
        
        self.last_pending_kind: Optional[str] = None

        self._last_sign: Optional[str] = None
        self._last_confidence: float = 0.0
        self._last_kind: Optional[str] = None
        self._changed: bool = False

    def _reset_pending(self):
        self.last_pending_sign = None
        self.hold_counter = 0
        self.hold_current = None

    def step(
        self,
        raw_prediction: dict | None,
        now_ts: float | None = None,
    ) -> dict:
        now = now_ts if now_ts is not None else time.time()
        self._changed = False

        status = "idle"
        sign = None
        confidence = 0.0

        if raw_prediction is None:
            self._reset_pending()

            sign = None
            confidence = 0.0
            status = "idle"

            # Re-arm the recognizer once the hand/sign disappears
            self.last_confirmed_sign = None
            self.last_confirmed_kind = None

        else:
            sign = raw_prediction.get("sign")
            confidence = float(raw_prediction.get("confidence", 0.0))
            kind = raw_prediction.get("kind", "alphabet")

            self._last_sign = sign
            self._last_confidence = confidence
            self._last_kind = kind

            # -----------------------------------------------------------
            # Hold detection
            # -----------------------------------------------------------
            if (
                sign == self.last_pending_sign
                and kind == self.last_pending_kind
            ):
                self.hold_counter += 1
            else:
                self.hold_counter = 1 if sign is not None else 0
                self.hold_current = sign
                self.last_pending_sign = sign
                self.last_pending_kind = kind

            meets_conf = confidence >= self.conf_threshold
            meets_hold = self.hold_counter >= self.min_hold_frames

            # Same sign cannot immediately trigger twice without re-arming
            not_dup = (
                sign != self.last_confirmed_sign
                or kind != self.last_confirmed_kind
            )

            if (
                meets_hold
                and meets_conf
                and not_dup
                and sign is not None
            ):
                self.last_confirmed_sign = sign
                self.last_confirmed_kind = kind
                self.last_confirm_ts = now
                self._changed = True
                status = "confirmed"

                # -------------------------------------------------------
                # Alphabet
                # -------------------------------------------------------
                if kind == "alphabet":
                    normalized = str(sign).lower()

                    if len(sign) == 1 and sign.isalpha():
                        self.builder.process_input(sign.upper())

                    elif normalized == "space":
                        self.builder.process_input("SPACE")

                    elif normalized == "del":
                        self.builder.process_input("DELETE")

                # -------------------------------------------------------
                # Phrase
                # -------------------------------------------------------
                elif kind == "phrase":
                    if self.builder.current_word:
                        self.builder.process_input("SPACE")

                    self.builder.sentence += str(sign) + " "

                    # Keep last_confirmed_sign set to prevent repeated firing
                    # until hand disappears or changes sign.
                    self.last_confirmed_sign = sign
                    self.last_confirmed_kind = kind

            else:
                if confidence < self.conf_threshold and sign is not None:
                    status = "low_confidence"

                elif sign is not None and self.hold_counter > 0:
                    status = (
                        "holding"
                        if self.hold_counter > 1
                        else "detecting"
                    )

                else:
                    status = "detecting" if sign is not None else "idle"

        # ---------------------------------------------------------------
        # Automatic word completion timeout
        # ---------------------------------------------------------------
        if (
            self.last_confirm_ts is not None
            and self.builder.current_word
        ):
            if (now - self.last_confirm_ts) > self.word_timeout_s:
                self.builder.process_input("SPACE")
                self._changed = True
                self.last_confirm_ts = now

        return {
            "status": status,
            "sign": sign,
            "confidence": confidence,
            "current_word": self.builder.current_word,
            "sentence": self.builder.sentence.rstrip(),
            "changed": self._changed,
        }

    def control(self, action: str) -> str:
        action = (action or "").strip().lower()

        try:
            if action == "clear":
                self.builder.process_input("CLEAR")

                self.last_confirmed_sign = None
                self.last_confirmed_kind = None
                self.last_confirm_ts = None

                self._reset_pending()

                self.stabilizer.window.clear()
                self.stabilizer.last_confirmed = None

                return "ok"

            if action == "undo":
                self.builder.process_input("DELETE")
                return "ok"

            if action in ("space", "confirm_word"):
                self.builder.process_input("SPACE")

                self.last_confirmed_sign = None
                self.last_confirmed_kind = None
                self.last_confirm_ts = time.time()

                self._reset_pending()

                return "ok"

            if action == "confirm_sentence":
                self.builder.process_input("ENTER")

                self.last_confirmed_sign = None
                self.last_confirmed_kind = None
                self.last_confirm_ts = None

                self._reset_pending()

                return "ok"

            if action in ("start", "stop"):
                return "ok"

            return "err"

        except Exception:
            return "err"