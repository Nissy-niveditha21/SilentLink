from backend.recognition.static_sign_recognizer import detect_phrase_gesture


def test_empty_landmarks_returns_none():
    result = detect_phrase_gesture([])
    assert result is None, "Empty list should return None"


def test_none_landmarks_returns_none():
    result = detect_phrase_gesture(None)
    assert result is None, "None should return None"


def test_bogus_short_returns_none():
    class P:
        def __init__(self, x, y, z=0.0):
            self.x = x
            self.y = y
            self.z = z

    bogus = [P(0.0, 0.0) for _ in range(5)]
    result = detect_phrase_gesture(bogus)
    assert result is None, "Shorter than 21 landmarks should return None"


if __name__ == "__main__":
    test_empty_landmarks_returns_none()
    test_none_landmarks_returns_none()
    test_bogus_short_returns_none()
    print("smoke ok")
