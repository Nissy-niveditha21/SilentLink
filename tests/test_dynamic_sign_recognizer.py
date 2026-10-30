import json

import numpy as np

from backend.recognition.dynamic_sign_recognizer import DynamicSignRecognizer
from backend.recognition.temporal_processor import TemporalProcessor


def test_dynamic_recognizer_loads_export_and_predicts(tmp_path):
    state = []
    for direction in ("", "_reverse"):
        suffix = f"_l0{direction}"
        state.extend([
            [f"lstm.weight_ih{suffix}", np.zeros((4, 63)).tolist()],
            [f"lstm.weight_hh{suffix}", np.zeros((4, 1)).tolist()],
            [f"lstm.bias_ih{suffix}", np.zeros(4).tolist()],
            [f"lstm.bias_hh{suffix}", np.zeros(4).tolist()],
        ])
    state.extend([
        ["fc.weight", np.zeros((2, 2)).tolist()],
        ["fc.bias", [0.0, 1.0]],
    ])
    model_path = tmp_path / "dynamic.json"
    model_path.write_text(json.dumps({
        "format": "silentlink-dynamic-lstm-v1",
        "seq_len": 2,
        "classes": ["i", "you"],
        "hidden_sizes": [1],
        "num_layers": 1,
        "layers": state,
    }), encoding="utf-8")

    recognizer = DynamicSignRecognizer(model_path=str(model_path))
    result = recognizer.predict_sequence(np.zeros((2, 63), dtype=np.float32))

    assert result["sign"] == "YOU"
    assert result["kind"] == "phrase"
    assert result["confidence"] > 0.7


def test_dynamic_recognizer_waits_for_a_full_sequence():
    recognizer = DynamicSignRecognizer(max_seq_len=2, model_path=None)

    recognizer.add_frame(np.zeros(63, dtype=np.float32))

    assert recognizer.ready() is False
    assert recognizer.predict() is None


def test_dynamic_recognizer_session_has_an_independent_frame_buffer():
    recognizer = DynamicSignRecognizer(max_seq_len=2, model_path=None)
    session = recognizer.new_session()
    session.add_frame(np.zeros(63, dtype=np.float32))

    assert len(session.seq_buffer) == 1
    assert len(recognizer.seq_buffer) == 0


def test_dynamic_word_predictions_build_a_complete_sentence():
    processor = TemporalProcessor(min_hold_frames=1, conf_threshold=0.6)

    for sign in ("I", "LOVE", "YOU"):
        result = processor.step(
            {"sign": sign, "confidence": 0.9, "kind": "phrase"},
            now_ts=100.0,
        )

    assert result["sentence"] == "I LOVE YOU"
