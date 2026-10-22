import numpy as np

EPS = 1e-6


def landmarks_to_features(lm_list) -> np.ndarray | None:
    try:
        if len(lm_list) != 21:
            return None
        pts = np.array(
            [[p.x, p.y, getattr(p, "z", 0.0)] for p in lm_list],
            dtype=np.float32,
        )
        if pts.shape != (21, 3):
            return None
        origin = pts[0]
        scale = np.linalg.norm(pts[9] - origin) + EPS
        feat = (pts - origin) / scale
        return feat.reshape(-1)
    except (TypeError, ValueError, AttributeError, IndexError):
        return None
