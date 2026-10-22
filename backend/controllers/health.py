import sys
import time

from fastapi import APIRouter

router = APIRouter()


def _check_recognizer_loaded() -> bool:
    for mod_name, mod in sys.modules.items():
        if mod_name == "backend.main":
            app = getattr(mod, "app", None)
            if app is not None:
                return hasattr(app.state, "static_recognizer") and app.state.static_recognizer is not None
    return False


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "recognizer_loaded": _check_recognizer_loaded(),
        "mediapipe_ready": False,
        "tf_imported": "tensorflow" in sys.modules,
        "time": time.time(),
    }
