from __future__ import annotations

from typing import List, Optional, Literal, Any

from pydantic import BaseModel, Field, ConfigDict


Point3D = tuple[float, float, float]


class LandmarkFrame(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    hand_landmarks: List[Point3D] = Field(
        ...,
        description="21 MediaPipe (x,y,z) landmark tuples for one hand in normalized image coordinates.",
        min_length=21,
        max_length=21,
    )
    timestamp_ms: Optional[float] = Field(
        default=None,
        description="Optional client-side timestamp in milliseconds for drift-aware temporal alignment.",
    )
    handedness: Optional[Literal["Left", "Right"]] = Field(
        default=None,
        description="MediaPipe-detected handedness label if available.",
    )
    camera_width: Optional[int] = None
    camera_height: Optional[int] = None


class ClientControl(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    action: Literal[
        "start", "stop", "clear", "undo", "space",
        "confirm_word", "confirm_sentence", "set_mode", "set_threshold",
    ]
    mode: Optional[Literal["COMMUNICATION", "CONTROL", "PHRASE"]] = None
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ClientMessage(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    type: Literal["frame", "control", "ping"]
    frame: Optional[LandmarkFrame] = None
    control: Optional[ClientControl] = None
    echo_id: Optional[str] = None


class RecognitionResult(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    status: Literal["idle", "detecting", "holding", "confirmed", "low_confidence", "error"]
    sign: Optional[str] = None
    kind: Optional[Literal["alphabet", "phrase"]] = None
    confidence: float = 0.0
    current_word: str = ""
    sentence: str = ""
    changed: bool = False
    mode: Literal["COMMUNICATION", "CONTROL", "PHRASE"] = "COMMUNICATION"


class TranslationPayload(BaseModel):
    key: str
    display: str
    description: str
    translations: dict
    image: str
    auto_translated: bool = False


class ComputerControlPayload(BaseModel):
    moved: bool = False
    clicked: bool = False
    scrolled_clicks: int = 0
    launched_app: Optional[str] = None


class ServerMessage(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    type: Literal[
        "recognition", "translation", "phrase_status",
        "control_status", "pong", "error", "welcome",
    ]
    recognition: Optional[RecognitionResult] = None
    translation: Optional[TranslationPayload] = None
    control: Optional[ComputerControlPayload] = None
    phrase_status: Optional[dict] = None
    message: Optional[str] = None
    echo_id: Optional[str] = None
    session_id: Optional[str] = None
    ts: float = 0.0


class SignAssetResponse(BaseModel):
    key: str
    display: str
    description: str
    type: str
    image: str
    translations: dict
    fallback: str
