import logging
import sys
import time
import os
from typing import Optional

from fastapi import FastAPI, Request, Query, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response, RedirectResponse

from backend.db import init_db
from backend.config import settings
from backend.controllers.health import router as health_router
from backend.controllers.auth import router as auth_router, templates as auth_templates
from backend.controllers.pages import router as pages_router, templates as pages_templates
from backend.websocket import websocket_router, manager
from backend.recognition.static_sign_recognizer import StaticSignRecognizer
from backend.recognition.dynamic_sign_recognizer import DynamicSignRecognizer
from backend.recognition.temporal_processor import TemporalProcessor
from backend.recognition.features import landmarks_to_features
from backend.services.asset_resolver import AssetResolver
from backend.services.translation import TranslationService
from backend.services.computer_control import ComputerControlService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("silentlink.main")

app = FastAPI(
    title="SilentLink",
    description="SilentLink Sign Language Communication Platform — real-time MediaPipe landmark recognition over WebSocket, 5-language translation, and optional computer control mode.",
    version="2.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=*, microphone=*")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    return response


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    path = request.url.path
    if path.startswith("/api/") or path.startswith("/ws") or path.startswith("/static/") or path.startswith("/assets/"):
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "path": path, "message": "The requested endpoint does not exist."},
        )
    return RedirectResponse(url="/")


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    log.exception("500 on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred. Please check the server logs."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "status_code": exc.status_code, "message": exc.detail},
    )


_static_app = StaticFiles(directory="frontend/static", html=True)
_assets_app = StaticFiles(directory="assets", html=True)
app.mount("/static", _static_app, name="static")
app.mount("/assets", _assets_app, name="assets")


_ROUTE_ALIASES = {
    "login": "login_form",
    "signup": "signup_form",
    "app": "app_page",
    "history": "history",
    "how_it_works": "how_it_works",
    "settings": "settings_page",
    "logout": "logout",
    "about": "about",
    "home": "index",
}


def _jinja_url_for(endpoint: str, **kwargs):
    if endpoint == "static":
        filename = kwargs.get("filename", "")
        return f"/static/{filename.lstrip('/')}"
    if endpoint == "assets":
        filename = kwargs.get("filename", "")
        return f"/assets/{filename.lstrip('/')}"
    real = _ROUTE_ALIASES.get(endpoint, endpoint)
    try:
        return app.url_path_for(real, **kwargs)
    except Exception:
        fallback_map = {
            "login": "/login",
            "signup": "/signup",
            "logout": "/logout",
            "app": "/app",
            "about": "/about",
            "history": "/history",
            "how_it_works": "/how-it-works",
            "settings": "/settings",
            "home": "/",
            "index": "/",
        }
        if endpoint in fallback_map:
            return fallback_map[endpoint]
        raise


for _templates in (auth_templates, pages_templates):
    _templates.env.globals["url_for"] = _jinja_url_for

app.include_router(health_router, prefix="")
app.include_router(auth_router, prefix="")
app.include_router(pages_router, prefix="")
app.include_router(websocket_router, prefix="")


@app.get("/api/sign/{sign_key}", tags=["assets"])
async def resolve_sign(sign_key: str):
    resolver: Optional[AssetResolver] = getattr(app.state, "asset_resolver", None)
    if resolver is None:
        raise HTTPException(status_code=503, detail="AssetResolver not initialized")
    resolved = resolver.resolve(sign_key)
    return resolved


@app.get("/api/translate", tags=["translation"])
async def translate_api(
    phrase: str = Query("", description="Phrase string to translate (alias for sentence)"),
    sentence: str = Query("", description="Sentence to translate"),
    signs: str = Query("", description="Comma-separated sign keys"),
    kinds: str = Query("", description="Comma-separated kinds (phrase|alphabet)"),
):
    svc: Optional[TranslationService] = getattr(app.state, "translation_service", None)
    if svc is None:
        raise HTTPException(status_code=503, detail="TranslationService not initialized")
    text = phrase or sentence
    signs_arr = [s.strip() for s in signs.split(",") if s.strip()] if signs else []
    kinds_arr = [k.strip() for k in kinds.split(",") if k.strip()] if kinds else []
    return svc.translate_sentence(text, signs_arr=signs_arr, kind_arr=kinds_arr)


from typing import Literal  # noqa: E402

_SetModeBody = dict


@app.post("/api/mode", tags=["control"])
async def set_mode(
    mode_q: Optional[str] = Query(None, pattern="^(COMMUNICATION|CONTROL|PHRASE)$", alias="mode"),
    body: _SetModeBody = Body(default=None),
):
    mode = mode_q or (body.get("mode") if isinstance(body, dict) else None)
    if not mode or mode not in ("COMMUNICATION", "CONTROL", "PHRASE"):
        raise HTTPException(status_code=400, detail="mode must be one of COMMUNICATION, CONTROL, PHRASE")
    app.state.current_mode = mode
    cc: Optional[ComputerControlService] = getattr(app.state, "computer_control", None)
    cc_active = bool(cc) and mode == "CONTROL"
    if cc is not None:
        cc.set_active(cc_active)
    return {"mode": mode, "computer_control_active": cc_active}


@app.get("/api/phrase_status", tags=["translation"])
async def phrase_status_api():
    temporal = getattr(app.state, "temporal_processor", None)
    last = getattr(app.state, "last_phrase_broadcast", None)
    if temporal is not None:
        sb = getattr(temporal, "builder", None)
        current_sentence = sb.sentence if sb is not None else ""
        current_word = getattr(sb, "current_word", "") or ""
        status = getattr(temporal, "_last_status", "idle") or "idle"
        last_sign = getattr(temporal, "_last_sign", None)
        last_conf = getattr(temporal, "_last_confidence", None)
    else:
        current_sentence = ""
        current_word = ""
        status = "idle"
        last_sign = None
        last_conf = None
    return {
        "sentence": current_sentence,
        "current_word": current_word,
        "status": status,
        "last_sign": last_sign,
        "last_confidence": last_conf,
        "last_broadcast": last,
    }


@app.post("/api/audio_to_sign", tags=["audio"])
async def audio_to_sign(request: Request):
    phrase = ""
    try:
        form = await request.form()
        if "phrase" in form:
            phrase = str(form["phrase"])
    except Exception:
        pass
    if not phrase:
        phrase = request.query_params.get("phrase", "HELLO")
    resolver = getattr(app.state, "asset_resolver", None)
    sign_info = resolver.resolve(phrase) if resolver else {"video": f"/assets/signs/{phrase.upper()}/clip.gif", "display": phrase}
    return {"ok": True, "phrase": phrase, "sign": sign_info}


@app.get("/speak", tags=["audio"])
@app.post("/speak", tags=["audio"])
async def speak_audio(
    text_q: Optional[str] = Query(None, min_length=1, max_length=400, alias="text"),
    lang_q: Optional[str] = Query("en", pattern="^(en|hi|te|es|fr)$", alias="lang"),
    body: Optional[dict] = Body(default=None),
):
    text = text_q or (body.get("text") if isinstance(body, dict) else None)
    lang = lang_q if lang_q else (body.get("lang") if isinstance(body, dict) else "en")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    try:
        import asyncio
        from utils.tts_engine import TTSEngine  # type: ignore
        tts = TTSEngine()
        await asyncio.to_thread(tts.speak, text)
        return {"ok": True, "text": text, "lang": lang}
    except Exception as e:
        log.warning("tts fallback err %s", e)
        return {"ok": False, "text": text, "lang": lang, "warning": str(e)}


@app.on_event("startup")
async def on_startup():
    init_db()

    app.state.static_recognizer = StaticSignRecognizer()
    app.state.dynamic_recognizer = DynamicSignRecognizer(max_seq_len=30)
    app.state.temporal_processor = TemporalProcessor()
    app.state.features_to_63_fn = landmarks_to_features

    try:
        app.state.asset_resolver = AssetResolver()
        if app.state.asset_resolver.gif_agent:
            app.state.asset_resolver.gif_agent.ensure_all_gifs()
    except Exception as e:
        log.error("AssetResolver init failed: %s", e)
        app.state.asset_resolver = None

    if getattr(app.state, "asset_resolver", None) is not None:
        app.state.translation_service = TranslationService(app.state.asset_resolver)
    else:
        app.state.translation_service = None

    app.state.computer_control = ComputerControlService()
    app.state.current_mode = "COMMUNICATION"
    app.state.history_store = []

    banner = (
        "\033[95m"
        "  ____  _ _            _   _     _       _    \n"
        " / ___|(_) | ___ _ __ | | | |   (_)_ __ | | __\n"
        " \\___ \\| | |/ _ \\ '_ \\| |_| |   | | '_ \\| |/ /\n"
        "  ___) | | |  __/ | | |  _  |___| | | | |   < \n"
        " |____/|_|_|\\___|_| |_|_| |_____|_|_| |_|_|\\_\\\n"
        "\033[0m"
    )
    print(banner)
    print("\033[92mSilentLink v2.1 starting…\033[0m")
    print(
        f"  StaticSignRecognizer: {'loaded' if app.state.static_recognizer.mlp is not None else 'rules-only (no MLP weights)'}"
    )
    print(
        f"  AssetResolver: {'loaded' if app.state.asset_resolver is not None else 'unavailable'}"
    )
    print(
        f"  TranslationService: {'loaded' if app.state.translation_service is not None else 'unavailable'}"
    )
    print(
        f"  ComputerControl: {('pyautogui ready' if app.state.computer_control.pyautogui_imported else 'disabled (pyautogui missing)')}"
    )
    print(f"  Listening on http://{settings.HOST}:{settings.PORT}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
