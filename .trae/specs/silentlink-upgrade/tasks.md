# SilentLink — Implementation Plan

## Task 1: Project restructure — clean folder tree, requirements, .env, .gitignore
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Create canonical folders: `backend/` (config, recognition, websocket, services, controllers, db), `frontend/` (index.html + pages in `templates/`, `static/css`, `static/js`), `models/`, `assets/signs/`, `training/` (existing + new dynamic scaffold), `scripts/`.
  - Update `requirements.txt`: add `fastapi`, `uvicorn[standard]`, `pydantic`, `websockets`, `python-multipart`, `python-dotenv`, `itsdangerous`, `scikit-learn`; keep existing opencv/mediapipe/numpy/pyautogui/flask-sqlalchemy equivalents; mark `tensorflow` as training-only (in `requirements-training.txt` or extras section) with guard imports.
  - Create `.env.example` with `SECRET_KEY`, `DATABASE_URL`, `PORT=8000`, `HOST=127.0.0.1`.
  - Update `.gitignore`: add `.env`, `temp_audio/`, `*.sqlite3`, `instance/`, plus existing entries.
  - Move existing `training/*.py`, `utils/{stability,sentence_builder}.py` into the new tree. Remove the 6 dead commented-out copies inside `app.py`, `main.py`, `evaluate.py`, `predict_sign.py`, `modules/alphabet_recognizer.py`, `modules/tts.py`, `modules/voice_to_text.py` (collapse each file to exactly ONE clean version).
- **Acceptance Criteria Addressed**: AC-1 (partial — folder layout foundation), AC-7 (partial — env + gitignore foundation), AC-10 (code structure foundation)
- **Test Requirements**:
  - `rule` TR-1.1: `tree /f /a` or equivalent shows `backend/`, `frontend/`, `models/`, `assets/`, `training/`, `scripts/` in the repo root and no file contains multi-version commented-out duplicates. Evidence: directory listing output + grep for `"\"\"\"import"` pattern (start of old multiline commented copies) returns 0 matches in final source files.
  - `rule` TR-1.2: `.env.example` present, `.env` in `.gitignore`, `requirements.txt` contains fastapi/uvicorn/pydantic. Evidence: file listing + cat requirements.txt.
  - `rule` TR-1.3: A single clean copy of each previously duplicated file exists (no block-comments wrapping entire alternate versions). Evidence: file line counts and grep for `^\"\"\"from flask` head-of-file comment wrapping.
- **Notes**: Do NOT delete useful logic; extract it. The duplicate blocks in app.py contain the latest PHRASE mode + gTTS endpoint + poll routes — merge that logic forward.

## Task 2: Backend foundation — FastAPI app, config, auth, static files, routes
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - `backend/main.py` — FastAPI application factory, CORS middleware for dev, session middleware with itsdangerous/SECRET_KEY from `.env`, startup event loading MediaPipe + recognizer.
  - `backend/config.py` — `Settings` (pydantic BaseSettings / dotenv), WARNING log if SECRET_KEY is the per-instance fallback.
  - `backend/db.py` — SQLAlchemy engine + SessionLocal + Base pointing at SQLite `data/silentlink.db` (create_all on startup).
  - `backend/models/user.py` — User(id, username unique, password_hash).
  - `backend/controllers/auth.py` — `/login`, `/logout`, `/signup` endpoints (Jinja2 templates rendered by FastAPI).
  - `backend/controllers/pages.py` — Jinja2TemplateResponse for `/` (landing), `/app` (dashboard, auth-gated), `/history`, `/how-it-works`, `/settings`.
  - `backend/controllers/health.py` — `GET /health` returning `{status, recognizer_loaded, mediapipe_ready, tf_imported: bool}`.
  - Mount `frontend/static` under `/static`. Configure `Jinja2Templates` pointing at `frontend/templates`.
  - Confirm SECRET_KEY never hardcoded; fallback is `secrets.token_urlsafe(32)` generated per boot with WARNING log.
- **Acceptance Criteria Addressed**: AC-1 (single FastAPI process), AC-7 (.env SECRET_KEY with WARNING fallback), AC-10 (modular backend structure)
- **Test Requirements**:
  - `rule` TR-2.1: `uvicorn backend.main:app --port 8000` starts and `curl http://localhost:8000/health` returns valid JSON. Evidence: curl output.
  - `rule` TR-2.2: `curl -I http://localhost:8000/` returns 200; `/app` redirects to `/login` without session. Evidence: curl -I output.
  - `rule` TR-2.3: Source code grep for `SECRET_KEY\s*=\s*['\"][^'\"]{5,}['\"]` yields 0 matches outside .env.example. Evidence: grep result.
  - `rule` TR-2.4: `GET /health` response includes `"tf_imported": false`. Evidence: curl output.
- **Notes**: FastAPI's `StaticFiles` + `Jinja2Templates` replace Flask. Keep dependency injection loose: recognizer loader attached to `app.state`.

## Task 3: Recognition engine core — StaticSignRecognizer + normalization + TemporalProcessor
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - `backend/recognition/features.py` — Normalize 21 landmarks exactly like `extract_landmarks.py`: wrist (lm[0]) as origin, scale = `||lm[9]-lm[0]|| + eps`, output shape (63,) float32. Handles missing hand (returns None).
  - `backend/recognition/numpy_mlp.py` — Load `models/alphabet_mlp.json`; implement StandardScaler-apply + ReLU + softmax forward pass (mirror `evaluate_alphabet.py:forward`). Returns `(proba_array, class_names)`. Handles model-file-missing with a clear error + raises importable exception.
  - `backend/recognition/static_sign_recognizer.py`:
    - Class `StaticSignRecognizer`. Holds numpy_mlp + phrase-rule engine.
    - Method `.predict_alphabet(landmarks, conf_threshold=0.6)` → `{sign: str, confidence: float, kind: "alphabet"}` or `None` if below threshold.
    - Method `.detect_phrase_gesture(lm)` → extend the existing 5 phrase rules (HI/SORRY/THANKS/BYE/PLEASE) to ≥ 20 entries covering the user spec: HELLO (alias HI), YES, NO, THANK_YOU, PLEASE, SORRY, HELP, GOOD, BAD, I, YOU, WE, WHAT, WHERE, HOW, NAME, FOOD, WATER, STOP, GO. For each new sign, pick a non-overlapping finger shape (e.g., YES = thumb_up only, NO = index+middle cross, HELP = open palm + thumb up, GOOD = thumbs up + pinky down, etc.) — document each rule in a docstring. Return `{sign, confidence=1.0, kind="phrase"}` or None.
    - Combined method `.predict(lm, mode="communication")` → prefers phrase if a rule matches strongly, else alphabet letter, else None.
  - `backend/recognition/temporal_processor.py`:
    - Holds `PredictionStabilizer` (reuse `utils/stability.py` pattern, upgraded to carry confidence).
    - Debounce + minimum-hold + duplicate suppression logic.
    - Word buffer + word-boundary timeout (default 1.8s) + sentence buffer.
    - Control action handlers: clear, undo, space, confirm_word, confirm_sentence, start, stop.
    - Emit per-step dict: `{status, sign, confidence, current_word, sentence, changed:bool}`.
  - `backend/recognition/dynamic_sign_recognizer.py` — Skeleton class: sequence buffer of N frames × 63 features. `predict()` currently defers to StaticSignRecognizer but documents the hook point: "Swap this body for an LSTM/GRU inference call once models/dynamic_sign_lstm.pt and dataset are supplied". Raises no errors; ships a clear "Placeholder" section in its docstring and in README.
- **Acceptance Criteria Addressed**: AC-2 (no TensorFlow), AC-3 (temporal stabilizer → HELLO not duplicates)
- **Test Requirements**:
  - `rule` TR-3.1: Import chain `from backend.recognition.static_sign_recognizer import StaticSignRecognizer` does NOT pull in tensorflow. Evidence: `python -c "import sys; from backend.recognition.static_sign_recognizer import StaticSignRecognizer; print('tensorflow' in sys.modules)"` prints `False`.
  - `rule` TR-3.2: Unit-test-style script `python -m tests.test_temporal_processor` (write it under tests/) feeds synthetic sequence [H×10, E×10, L×10, L×10, O×10, idle×30 frames] and asserts confirmed-letter stream equals ['H','E','L','L','O'] and final sentence == "HELLO". Evidence: test exit code 0 + output log.
  - `rubric` TR-3.3: Recognition module clarity; scale 1–5; anchors 1=godfile, 3=ok, 5=each class single responsibility + ≤400 LOC per file; threshold ≥4. Evidence: reviewer read-through + LOC counts.
- **Notes**: Keep phrase rules DISJOINT from alphabet-sign gestures where possible. For the purposes of this project, the 20 phrase gestures can use wrist/thumb orientations not used by fingerspelling. Document every mapping in the How It Works page.

## Task 4: Computer Control module — isolated pyautogui, gesture map, mode gating
- **Status**: `pending`
- **Priority**: medium-high
- **Depends On**: Task 3
- **Description**:
  - `backend/services/computer_control.py` — class `ComputerControlService`:
    - Lazy import of `pyautogui` (so the module loads on headless machines without it). Sets `pyautogui.FAILSAFE = False` only inside this class's init scope.
    - Debounce timers (last_click, last_scroll, last_launch).
    - Action methods: `move_cursor(index_x_norm, index_y_norm)`, `click_if_pinch(pinch_dist, thr=0.03)`, `scroll_if_2finger(dy)`, `launch_apps(finger_state_vector)`.
    - App-launch mapping: Index-only → YouTube, 3 fingers → Notepad, 4 fingers → WhatsApp (cross-platform open_url helper). Fist held 2 s → reset state.
    - All methods are NO-OP unless `.active = True`. The active flag is toggled ONLY by the WebSocket handler when the incoming message says `mode=="computer_control"`.
  - `backend/services/__init__.py` — clean exports.
- **Acceptance Criteria Addressed**: AC-4 (Communication mode never clicks)
- **Test Requirements**:
  - `rule` TR-4.1: With `ComputerControlService.active=False`, calling `click_if_pinch(0.00)` 100 times triggers 0 pyautogui invocations (instrument via a mock/spy on pyautogui.click). Evidence: test assertion passes.
  - `rule` TR-4.2: With `active=True`, same call triggers at most 1 click per debounce window. Evidence: test counter.
  - `rubric` TR-4.3: Separation hygiene; scale 1–5; anchors 1=pyautogui imported globally and tangled with recognition, 3=separate file but globals still touch, 5=fully lazy import, fully active-flag gated, zero coupling to TemporalProcessor; threshold ≥4. Evidence: code review.
- **Notes**: Reuse the `open_url` / cross-platform subprocess helpers from the old app.py, moved here.

## Task 5: WebSocket endpoint — /ws/recognize, pydantic schema, message dispatch
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Tasks 2, 3, 4
- **Description**:
  - `backend/websocket/schemas.py` — Pydantic models: ClientHandMsg (landmarks, ts, session_id, mode, target_language), ClientControlMsg, ServerPrediction, ServerStatus, ServerError, ControlResult.
  - `backend/websocket/manager.py` — ConnectionManager: per-connection TemporalProcessor + ComputerControlService (so users don't share state). Per-session clean-up on disconnect.
  - `backend/websocket/routes.py` — WebSocket route at `/ws/recognize`:
    - Accept. Send initial `{type:"status", …}`.
    - Receive loop:
      - Validate message via pydantic (malformed → ServerError reply without dropping socket).
      - If `type=="hand"`:
        1. Normalize landmarks via features.py.
        2. StaticSignRecognizer.predict → raw pred.
        3. TemporalProcessor.step(pred) → word/sentence state.
        4. If mode == "computer_control": ComputerControlService.step(lm).
        5. Resolve visual_asset (Task 6) + translations (Task 7).
        6. Broadcast ServerPrediction message once per processed frame.
      - If `type=="control"`: apply to TemporalProcessor, reply ControlResult.
      - If `type=="ping"`: pong with server ts.
    - Rate-limit prediction emits to ≤ 20 Hz (throttle if client floods).
    - On disconnect: cleanup, log.
  - Wire route into `backend/main.py` WebSocket router.
- **Acceptance Criteria Addressed**: AC-1 (WS in same process), AC-4 (mode gating), AC-6 (disconnect → frontend reconnect logic is Task 8 but backend must not leak sessions)
- **Test Requirements**:
  - `rule` TR-5.1: Python WebSocket test client connects to `/ws/recognize`, sends one hand message, receives exactly one prediction response within 500 ms. Evidence: test log.
  - `rule` TR-5.2: Sending a payload with 19 landmarks (not 21) returns ServerError type and keeps socket open. Evidence: client-side WS close code still 1000 after error event.
  - `rule` TR-5.3: Flooding 200 frames/sec results in ≤ 25 outgoing prediction messages/sec (throttled). Evidence: client-side counter over 2 s window.
- **Notes**: Use `websockets`-compatible FastAPI routes (`WebSocket` class). Be memory-smart: reuse per-connection objects; don't new-up a recognizer per message.

## Task 6: Visual asset system — signs.json metadata + placeholder visuals + resolver
- **Status**: `pending`
- **Priority**: medium-high
- **Depends On**: Task 1
- **Description**:
  - `assets/signs.json` — ≥ 25 entries covering: the 20 phrase signs, alphabet letters A–Z aggregate entry (single fallback), and a generic "unrecognized" entry. Schema per key:
    ```
    "HELLO": {"display":"Hello","description":"Wave or open palm toward person","type":"phrase","video":null,"image":null,"svg_animation":"wave","translations":{"en":"Hello","hi":"नमस्ते","te":"నమస్కారం","es":"Hola","fr":"Bonjour"}}
    ```
  - `assets/signs/<key>/` folders: for each phrase, ship a lightweight `<key>.svg` hand-drawn placeholder. For the MVP, 5 of them get a small looping CSS animation defined in `frontend/static/js/visualAnimations.js` (e.g., "wave" = arm horizontal oscillation, "thumb" = up-down, etc.). The remaining 15 use a generic fallback SVG.
  - `assets/ATTRIBUTIONS.md` — All placeholders created by project (SilentLink team); license: CC0 or MIT. No third-party content; explicitly state that to avoid copyright concerns.
  - `backend/services/asset_resolver.py` — class `AssetResolver`: loads `signs.json` once at startup; method `.resolve(sign_key)` → returns dict ready for the ServerPrediction `visual_asset` field, with fallback if key is unknown, and always includes display + description + fallback card text.
  - Wire AssetResolver into the WebSocket route so every `type:"prediction"` message includes the resolved visual_asset.
- **Acceptance Criteria Addressed**: AC-5 (missing-asset fallback)
- **Test Requirements**:
  - `rule` TR-6.1: AssetResolver.resolve("ZEBRA") returns `{display:"Zebra", description:"…", fallback:"Visual demonstration unavailable", …}` with no errors thrown. Evidence: Python REPL output.
  - `rule` TR-6.2: `assets/signs.json` loads as JSON with ≥ 25 entries and every entry contains at least the keys `display`, `description`, `type`, `translations`. Evidence: `python -c "import json; d=json.load(open('assets/signs.json')); …"` assert + count.
  - `rule` TR-6.3: `assets/ATTRIBUTIONS.md` exists. Evidence: file listing.
- **Notes**: Do not download external files. SVG placeholders can be tiny (≤ 50 lines each) — simple geometric hand poses. Real videos would be added later per the documented convention.

## Task 7: Translation service — 5-language phrase dictionary + fallback
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 6 (translations embedded in signs.json)
- **Description**:
  - `backend/services/translation.py` — class `TranslationService`:
    - Primary source: translations already in `assets/signs.json`.
    - For alphabet-fingerspelled *words* (not in signs.json): return `{en: word, hi: None, te: None, es: None, fr: None}` plus a marker `auto_translated: false` so the UI can show "No automatic translation for fingerspelled words".
    - No paid MT API call. Never fabricate output. If we add an optional deep-translator later it stays behind an env flag.
  - Wire into the WebSocket route: attach `{translations: {…}, auto_translated: bool}` alongside ServerPrediction.
- **Acceptance Criteria Addressed**: Part of integration AC-12
- **Test Requirements**:
  - `rule` TR-7.1: For sign key HELLO, translations dict contains non-empty string for all 5 language keys. Evidence: function output.
  - `rule` TR-7.2: For a fingerspelled word "ZXQ" (not a phrase key), `auto_translated == false` and only en is populated. Evidence: function output.
- **Notes**: User spec says "preserve existing translation capability" (which was phrase-only EN/FR). We extend honestly to 5 langs for phrases only and mark the limitation clearly.

## Task 8: Frontend HTML templates — all pages with MediaPipe on client
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Tasks 1, 2
- **Description**:
  - `frontend/templates/base.html` — modern shell from existing base.html (keep the design tokens, Inter + Space Grotesk, navbar) but add the MediaPipe CDN script tag for Hands client-side processing, LiveRegion for screen readers, skip-to-content link, semantic `<nav> <main> <aside> <footer>`, `prefers-reduced-motion` script guard disabling cursor-sparkle effects.
  - `frontend/templates/index.html` — Landing: hero, 3 features, CTA, keep existing professional styling but add link to `/app` (instead of hiding dashboard behind signup).
  - `frontend/templates/login.html`, `signup.html` — re-style, add Demo Gate disclaimer ("This is a local demo gate, not production security").
  - `frontend/templates/app.html` — Dashboard (the big one). Semantic layout:
    - Nav: SilentLink logo + links (Dashboard / Live Translate / History / How It Works / Settings) + Logout button + Mode toggle pill [Communication | Computer Control].
    - Main grid (left camera, right 2 sidebars stacked):
      - `<section aria-label="Live camera">`: `<video autoplay muted playsinline>` + `<canvas>` overlay for landmarks. Overlay HUD: live-dot badge, current sign bubble, confidence bar, FPS counter, latency ms, connection status pill.
      - `<section aria-label="Recognition results">`: 4 cards — **Current Sign**, **Current Word**, **Sentence**, **Confidence + status chip** (detecting/holding/confirmed/low confidence/idle).
      - `<section aria-label="Sign demonstration">`: Visual card (video/image/SVG anim + display name + description + fallback text when missing).
      - `<section aria-label="Controls">`: Start, Pause, Clear, Undo, Space, Confirm Word, Confirm Sentence, Speak. Tab order preserved.
      - `<section aria-label="Translations">`: 5 rows (EN/HI/TE/ES/FR) each with speak button + disabled state badge if voice unavailable.
      - `<section aria-label="Quick reference guide">`: collapsible gesture reference table for the 20 phrase signs.
    - Live-region ARIA on current sign + sentence so screen readers announce changes.
  - `frontend/templates/history.html` — search box, filter chips, list per-session entries with copy/speak/replay-visual/delete buttons + Clear All.
  - `frontend/templates/how_it_works.html` — Architecture flow diagram (SVG or ASCII box arrows), list of supported signs with gesture rules, finger-state legend, honest paragraph distinguishing fingerspelling vs phrase signs vs future dynamic signs.
  - `frontend/templates/settings.html` — sliders + toggles: confidence threshold (0.3–0.95), stabilizer window (5–30 frames), word timeout (0.5–5 s), TTS default language, reduced motion on/off, theme (dark / darker / light contrast). Save buttons: Save to localStorage + Apply server-side via optional POST.
- **Acceptance Criteria Addressed**: AC-9 (layout polish), AC-29 (a11y structural items: semantic, ARIA, skip link)
- **Test Requirements**:
  - `rule` TR-8.1: All 7 pages (/, /login, /signup, /app, /history, /how-it-works, /settings) render HTTP 200 when fetched. Evidence: 7 curl -s -o /dev/null -w "%{http_code}" calls returning 200.
  - `rule` TR-8.2: Dashboard page loads MediaPipe via CDN, exposes `window.Hands` after script load. Evidence: puppeteer-like check or manual JS console log via test script.
  - `rule` TR-8.3: Dashboard contains exactly 6 semantic sections/aria-labels matching the spec and a mode toggle. Evidence: DOM query `querySelectorAll('[aria-label]').length`.
  - `rubric` TR-8.4: Layout/typography; scale 1–5; anchors 1=messy, 3=functional OK, 5=deliberate hierarchy, consistent spacing (8/12/16/24 rhythm), aligned to 8px grid; threshold ≥4. Evidence: screenshot review.
- **Notes**: Keep Jinja2 syntax; FastAPI renders them. Replace old static/main.js's cursor sparkle guard with `prefers-reduced-motion` early return.

## Task 9: Frontend JS — camera, MediaPipe landmarks, WebSocket client, reconnect, controls
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Tasks 5, 6, 8
- **Description**:
  - `frontend/static/js/camera.js`:
    - getUserMedia with `video: {width:{ideal:640}, height:{ideal:480}, facingMode:'user'}`.
    - Error handlers: PermissionDenied vs DeviceNotFound vs NotAllowedError — show specific banner components with retry + browser-specific instructions (Chrome: Site settings → Camera → Allow).
    - Render to `<video>`. Expose `startCamera / stopCamera / isCameraOn`.
  - `frontend/static/js/landmarks.js`:
    - MediaPipe Hands instance, `onResults` callback draws landmarks onto overlay canvas (use existing MediaPipe drawing utils), extracts 21 landmarks as `{x,y,z}` normalized array, throttled send to WS at ≤ 20 FPS via requestAnimationFrame gate.
    - HUD overlay: FPS (measured client-side), latency ms (roundtrip per hand frame → prediction reply), connection pill "Connected / Reconnecting… (3) / Disconnected".
  - `frontend/static/js/ws.js`:
    - `RecognitionWS` class: wraps WebSocket. Reconnect logic: 10 attempts with exponential backoff (min 400 ms, max 6 s). Auto-restarts landmark stream on reconnect.
    - Incoming message handlers: prediction → update UI sections, status → update connection pill, error → show user-friendly toast, control_result → confirm action.
  - `frontend/static/js/recognitionUI.js`:
    - DOM bindings for Current Sign, Current Word, Sentence, Confidence bar, Status chip.
    - Animates confirmed-letter "flash" in (not every raw frame). Updates sentence word-by-word.
  - `frontend/static/js/controls.js`:
    - Bindings for Start/Pause/Clear/Undo/Space/Confirm Word/Confirm Sentence/Speak → send control WS messages or invoke browser SpeechSynthesis locally.
    - Keyboard shortcuts: C=Clear, Backspace=Undo, Space=Space, Enter=ConfirmSentence, S=Speak (Escapable: user can focus text inputs without conflicts).
  - `frontend/static/js/translations.js`:
    - Populate 5 translation rows from prediction.translations. Detect available voices via speechSynthesis.getVoices(). Speak button per row.
    - If voice unavailable for a language, disable button + show "Voice unavailable" tooltip/badge.
  - `frontend/static/js/visualCard.js`:
    - Render the resolved `visual_asset`: pick SVG-anim renderer, image, video, or fallback. Never throw even if asset URL 404s (onerror handler → fallback card).
  - `frontend/static/js/history.js`:
    - Store in localStorage `silentlink_history_v1` array of `{ts, sign, word, sentence, confidence, translations, visual_key}`.
    - History page: render list, search filter by sentence text, copy-to-clipboard, replay-visual (navigate to dashboard with key param), clear-all confirm dialog.
  - `frontend/static/js/settings.js`:
    - Load/save settings from/to localStorage `silentlink_settings_v1`. Apply in realtime: thresholds to stabilizer WS params, reduced motion → disable sparkles/cursor ring, etc.
  - `frontend/static/js/main.js` (keep existing effects but wrap guards, add page-specific init, reduced-motion early out before spark/cursor observer registration).
- **Acceptance Criteria Addressed**: AC-4 (mode toggle → sends mode on WS), AC-5 (visual card fallback), AC-6 (WS reconnect), AC-8 (history search/persist)
- **Test Requirements**:
  - `rule` TR-9.1: After opening dashboard + closing server + restarting server, client-side reconnect counter increments ≤ 10 times and shows "Connected" within 30 s of server up, no manual refresh. Evidence: UI screenshot sequence.
  - `rule` TR-9.2: Add 5 history entries, refresh page → entries still present. Clear history → list empty. Search "hello" → only entries containing "hello" show. Evidence: DevTools + UI.
  - `rule` TR-9.3: Browser console 0 uncaught JS errors when: camera denied, visual asset key missing, WS drop, translation voice unavailable. Evidence: Console snapshot for each scenario.
- **Notes**: All JS files ≤ ~400 LOC. Use ES6 classes, no build step; use `defer` script tags in `<head>` in order.

## Task 10: CSS polish — dashboard layout, responsiveness, reduced motion, focus states
- **Status**: `pending`
- **Priority**: medium-high
- **Depends On**: Tasks 8, 9
- **Description**:
  - Extend `frontend/static/css/style.css` (keep existing design tokens) with section-specific components:
    - `.camera-panel`, `.landmark-canvas`, `.hud-badges`, `.status-pill` (detecting/holding/confirmed/low_conf/idle colors).
    - `.recognition-grid` (CSS grid: camera 1.5fr, right-col stacked cards 1fr).
    - `.card.current-sign` (large primary type, high contrast, focus ring).
    - `.visual-card` (aspect-ratio 16:9, center SVG renderer, smooth enter transition `fade-scale-in`).
    - `.controls-row` (flex, ≥ 44×44 px touch targets, gap 12 px, wrap on mobile). Each button: visible :focus-visible 2px cyan outline.
    - `.translation-row` (5 rows, disabled state styling).
    - `.history-entry`.
    - Settings: range sliders with token-aligned track/thumb.
  - Responsive: 1024 px collapse: right-col moves below camera. 640 px collapse: control grid 2-col, HUD sizes reduce.
  - Accessibility: `:focus-visible` on all interactive elements, `prefers-reduced-motion` disables fade-in/stagger/cursor/sparkle effects. Minimum contrast on body text 4.5:1 against bg. Live-region element with `aria-live="polite"` for sentence changes.
  - Disable the global `cursor: none !important` default when a touch device is detected or reduced-motion on (leave it for desktop mouse users).
- **Acceptance Criteria Addressed**: AC-9 (visual polish), AC-29 (a11y: focus, contrast, reduced motion, live region)
- **Test Requirements**:
  - `rule` TR-10.1: Chrome DevTools Lighthouse or axe-core-style manual audit: (a) no elements with outline:0 and no focus styles, (b) body text contrast ≥ 4.5:1, (c) prefers-reduced-motion media query disables sparkles + cursor + fade delays. Evidence: audit output or annotated screenshot.
  - `rule` TR-10.2: Viewport widths 1280 px, 900 px, 390 px all show no horizontal scrollbars on dashboard. Evidence: 3 screenshots.
  - `rubric` TR-10.3: Design fidelity; scale 1–5; anchors 1=breaks tokens, 3=OK but inconsistent, 5=every element on-token (radius, spacing, colors, type scale); threshold ≥4. Evidence: screenshot review vs. token definitions.
- **Notes**: The existing style.css is already high-quality. The biggest additions are the dashboard layout grid and component styles.

## Task 11: Startup scripts — run.py (cross-platform) + Run-SilentLink.ps1
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Tasks 2, 8
- **Description**:
  - `run.py`:
    - Checks Python version (3.10 ≤ v < 3.12 recommended).
    - Looks for `.env`; copies `.env.example` to `.env` on first run if missing (with WARNING log and generates SECRET_KEY if placeholder).
    - Checks whether fastapi is importable; if not: `subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])` with progress output.
    - Injects project root into `sys.path` so `backend` package imports work.
    - Imports and runs uvicorn: `uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=False, log_level="info")`.
    - Opens browser tab to `http://{HOST}:{PORT}/app` after 1 second delay (best effort; never fail if the browser open fails).
  - `Run-SilentLink.ps1`:
    - ExecutionPolicy bypass for the current process only.
    - Calls `python run.py` with passthrough exit code.
    - Friendly colored Write-Host banners with setup hints if prerequisites missing.
  - Update existing `scripts/_run_pipeline.ps1` path references to the new folder layout if users still want to run training.
- **Acceptance Criteria Addressed**: AC-1 (one-command startup)
- **Test Requirements**:
  - `rule` TR-11.1: In a clean clone (after deleting venv and pycache), executing `python run.py` (1) installs deps, (2) starts Uvicorn, (3) logs "Uvicorn running on http://127.0.0.1:8000" within 5 minutes. Evidence: startup log tail.
  - `rule` TR-11.2: `.\Run-SilentLink.ps1` succeeds with exit code 0 if run.py succeeds. Evidence: PowerShell `$LASTEXITCODE` echo 0.
- **Notes**: Keep run.py idempotent. Never overwrite an existing `.env`.

## Task 12: Training pipeline scaffold + models/ placeholders + dataset README
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 1
- **Description**:
  - `training/train_dynamic_signs.py` — SCRIPT ONLY: argparse for `--seq-dataset`, `--seq-len`, `--out`, documents the expected `{N, seq_len, 63}` features, class list, and trains a small BiLSTM (64 hidden, 2 layers) via either PyTorch-lightweight-implementation OR plain numpy (if torch not available, raise a clear RuntimeError "PyTorch not installed; install requirements-training.txt and re-run"). Produces `models/dynamic_sign_lstm.json` exportable format. No invented weights; dataset-not-found is a handled error with instructions.
  - `models/README.md`: Explains `alphabet_mlp.json` (from training/train_alphabet.py), `dynamic_sign_lstm.json` (future: from training/train_dynamic_signs.py), model format spec for each JSON file so a student can introspect weights.
  - `dataset/README.md`: Expected layout for raw image dataset (asl_alphabet_train/A/img.jpg, etc.) AND for sequence dataset (sequences/<sign>/sample_0001.npy shape (seq_len,21,3)). Includes honest note: "No image/sequence data ships with the repo. Download ASL Alphabet dataset from Kaggle (license description) for alphabet training."
  - `scripts/train_alphabet.ps1` — one-command to call extract → train → evaluate pipeline end-to-end with path references to new folder layout.
- **Acceptance Criteria Addressed**: AC-10 (architecture explainability), AC-11 (README sections model/dataset)
- **Test Requirements**:
  - `rule` TR-12.1: `python training/train_dynamic_signs.py --help` works and prints usage. Evidence: stdout.
  - `rule` TR-12.2: Running `python training/train_dynamic_signs.py` without dataset raises RuntimeError with message containing "dataset" and "download" (friendly guidance), not a raw FileNotFound. Evidence: traceback snippet.
  - `rule` TR-12.3: `models/README.md` and `dataset/README.md` both exist with ≥ 3 explanatory paragraphs each. Evidence: `wc -l` output.
- **Notes**: The dynamic BiLSTM needs no real weights — the architecture is the deliverable (per user spec item 22: "build the architecture so the model can be trained/plugged in").

## Task 13: Error handling & guardrails integration pass
- **Status**: `pending`
- **Priority**: medium-high
- **Depends On**: Tasks 5, 9, 10
- **Description**:
  - Backend: Wrap TemporalProcessor / AssetResolver / numpy_mlp calls in try/except; on unexpected exception send `ServerError(code:"recognition_exception", message:"…", suggestion:"Reload the page")` instead of closing socket.
  - Backend: `data/silentlink.db` path's parent dir `data/` created on startup (never a FileNotFound for db).
  - Backend: If `models/alphabet_mlp.json` doesn't exist, recognizer_loaded = False; WebSocket returns prediction messages with `status:"idle"` and a dedicated ServerStatus on connect with `backend_state:"model_not_trained"`. How It Works link + banner.
  - Frontend: camera init → specific banners (permission vs. device) per DOMException name.
  - Frontend: MediaPipe failed to load → dedicated banner with "Ensure internet connectivity (MediaPipe CDN)" + offline fallback hint.
  - Frontend: SpeechSynthesis voice missing per language → disable button + tooltip badge.
  - Frontend: Visual asset src 404/error → swap to fallback SVG + text.
  - Frontend: Browser support check (no getUserMedia? no WebSocket? → landing page compatibility banner).
- **Acceptance Criteria Addressed**: AC-5 (fallback), AC-6 (disconnect banner), all FR-41..FR-49
- **Test Requirements**:
  - `rule` TR-13.1: Starting the app with no `models/alphabet_mlp.json` → `/health` returns `recognizer_loaded: false`; WS connection message contains `backend_state:"model_not_trained"`. Evidence: curl + WS log.
  - `rule` TR-13.2: Deny camera permission in browser → dashboard shows "Camera permission denied" banner with a Retry button and no console errors. Evidence: screenshot.
  - `rule` TR-13.3: `<img>`/`<video>` for visual with bad src → onerror fires and fallback card text appears. Evidence: DOM after error event.
- **Notes**: Prioritize user-facing non-technical messages with a small expando for the raw error detail.

## Task 14: Final README rewrite + small tests folder
- **Status**: `pending`
- **Priority**: high
- **Depends On**: All previous tasks (1–13)
- **Description**:
  - Overwrite root `README.md` with every required section from AC-11:
    1. Project overview (1 paragraph + 3 bullet key capabilities).
    2. Features (table: fingerspelling→word→sentence, 20 phrase signs, visual cards, computer control mode, 5-lang TTS, history, settings).
    3. Architecture (diagram-as-text boxes: Camera → MP Client → WS → Features → StaticSignRecognizer → TemporalProcessor → Sentence + UI → Visual + TTS. Include separate Computer Control flow with the MODE GATE guard.)
    4. Technology stack (FastAPI, WebSocket, MediaPipe, NumPy MLP, PyAutoGUI optional, Jinja2, CSS design system, Browser SpeechSynthesis).
    5. Folder structure (annotated tree).
    6. Installation (Windows: Python 3.10–3.11, venv creation, pip install -r requirements.txt, optional requirements-training.txt).
    7. Running the project: `python run.py` or `.\Run-SilentLink.ps1`.
    8. Model setup: trained-alphabet-model check; if missing, run `scripts/train_alphabet.ps1`; how to acquire ASL alphabet dataset.
    9. Dataset / training instructions: alphabet pipeline extract→train→evaluate + dynamic_signs scaffold instructions + limitations (no data bundled).
    10. Supported signs: Table of the 20 phrase signs + gesture rule + translation list. Alphabet letters A–Z via fingerspelling.
    11. WebSocket API: full schema (client messages, server messages, examples).
    12. Troubleshooting: 8 common issues (camera permission, MediaPipe CDN, pyautogui admin, anti-virus blocking camera, model file missing, TensorFlow not needed warning, TTS voices missing on Windows N edition, WebSocket reconnecting forever → port conflict).
    13. Limitations (HONEST): fingerspelling not full ASL lexical, 20 phrase signs rule-based, no dynamic temporal classifier shipped, visual placeholders only, translation phrase-only EN/HI/TE/ES/FR, local demo auth not production-secure, Windows-targeted.
    14. Future work: real LSTM/GRU dynamic signs, more phrase signs, real videos, sign2text transformer, true ASL grammar, production auth + user accounts, cross-platform packaging.
    15. Credits/licenses: MediaPipe, NumPy, FastAPI, ASL Alphabet dataset source link if used, ATTRIBUTIONS.md for visuals.
  - Create `tests/` folder:
    - `tests/test_temporal_processor.py` → the one used in TR-3.2.
    - `tests/test_static_sign_rules.py` → phrase rule detector smoke test (synthetic landmarks).
    - `tests/test_asset_resolver.py` → missing-key fallback (TR-6.1).
    - `tests/test_computer_control_gating.py` → mode inactive = no clicks (TR-4.1).
    - `tests/README.md`: how to run `python -m pytest -q` if pytest installed, or plain `python -m tests.xxx`.
- **Acceptance Criteria Addressed**: AC-11 (README honesty/completeness), AC-10 (architecture explainability), AC-2/AC-3/AC-4 test evidence support
- **Test Requirements**:
  - `rule` TR-14.1: README.md contains every required section header (exact list from AC-11). Evidence: grep for each section header returns 1 match.
  - `rule` TR-14.2: README.md contains the exact substring "fingerspelling" ≥ 3 times and does NOT contain the false claim "full ASL lexical sentence recognition". Evidence: grep output.
  - `rule` TR-14.3: `tests/test_temporal_processor.py` runs with exit 0 via `python -m tests.test_temporal_processor` (no pytest required; plain unittest allowed). Evidence: run output.
  - `rubric` TR-14.4: README writing quality; scale 1–5; anchors 1=sparse list, 3=good but missing honest limitations, 5=well-organized, copy-edited, every limitation explicitly called out in plain language, troubleshooting actionable; threshold ≥ 4. Evidence: full read-through.
- **Notes**: The architecture section will be cited by the student in interviews. Make it crystal clear and diagrammatic.

## Task 15: Final end-to-end integration validation
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Tasks 1–14
- **Description**:
  - Do a real run of the full stack: `python run.py`.
  - Open `/app` in Chrome. Exercise:
    - (a) Login → signup flow (demo credentials).
    - (b) Allow camera. Check landmark overlay, FPS readback, status pill "Recognizing".
    - (c) Simulate sign input either manually or via the synthetic test WS client to drive H→E→L→L→O letters; confirm Current Sign → Current Word → Sentence flow; confirm Visual card appears; confirm Sentence history entry after Confirm Sentence.
    - (d) Speak: verify audio (or verify SpeechSynthesis utterance queued in browser).
    - (e) Translations: 5 rows populated for phrase sign; disabled + badge for fingerspelled-only words.
    - (f) Switch to Computer Control mode: confirm cursor follows index finger; pinch clicks; Communication mode re-toggled: cursor stops reacting even with pinch.
    - (g) History page: search, copy, clear.
    - (h) Settings: change stabilizer slider → next frame reflects new debounce.
    - (i) Kill server: client shows "Reconnecting… (1)" banner. Restart server: banner says "Connected".
    - (j) Run `GetDiagnostics` / type-check / lint equivalent for Python + JS. For Python: `python -m compileall -q backend frontend training tests run.py`; fix any SyntaxErrors.
  - Fix any remaining crashes, missing files, path errors, 404s.
- **Acceptance Criteria Addressed**: AC-12 (happy-path E2E)
- **Test Requirements**:
  - `rule` TR-15.1: `python -m compileall -q backend frontend training tests run.py` exits 0 (no Python syntax errors). Evidence: exit code.
  - `rule` TR-15.2: Manual checklist of the 10 steps (a)–(j) all pass with notes/evidence. Evidence: review.md Review R1 evidence section links to screenshots or a short screen recording file path (if saved locally).
  - `rubric` TR-15.3: Overall integration robustness; scale 1–5; anchors 1=crashes on half the flows, 3=works with rough edges, 5=every flow succeeds first try, clear error banners where things can't proceed, no lingering "TODO" visible in UI; threshold ≥ 4. Evidence: reviewer notes.
- **Notes**: This is the final gate before moving to the Review phase. Keep a log of every finding and fix them as part of this task before marking `completed`.
