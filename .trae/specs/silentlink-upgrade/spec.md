# SilentLink — Complete Upgrade Product Requirements Document

## Overview
- **Summary**: Refactor the existing SilentLink codebase (Flask, duplicate scripts, MJPEG streaming, CNN + MLP dual model paths) into a single, professional, fully integrated real-time sign-language communication platform built on FastAPI + WebSockets, with temporal sentence recognition, visual sign demonstrations, a polished accessibility-first UI, and one-command startup on Windows.
- **Purpose**: Consolidate ~14 overlapping entry points (app.py, main.py ×7 versions, realtime_predict.py, predict_sign.py, gui.py, etc.) into one coherent application architecture. Upgrade raw per-frame alphabet classification into a genuine temporal recognition pipeline (stabilization → letter buffering → word segmentation → sentence building) with confidence scoring. Add sign visualization cards, a redesigned professional dashboard, proper gesture/computer-control mode separation, and honest documentation that describes *exactly* what is implemented.
- **Target Users**: Student developers (who must be able to explain every module in an interview), sign-language users / accessibility demonstrators, and evaluators reviewing the integrated end-to-end flow.

## Goals
1. **Unified Architecture**: Replace Flask + MJPEG + HTTP polling with FastAPI + WebSocket real-time recognition. Serve frontend static files from the same FastAPI process. Single entry point (`python run.py` or `.\Run-SilentLink.ps1`).
2. **Temporal Recognition Pipeline**: Per-frame raw predictions → confidence threshold → sliding-window stabilizer → debounced confirmed letter → word buffer → word-segmentation (pause or explicit gesture) → sentence buffer. Clearly label this as *fingerspelling word/sentence building*, not full ASL lexical sentence recognition.
3. **Static + Dynamic Recognizer Abstraction**: `StaticSignRecognizer` (single-frame landmark MLP for alphabet letters and rule-based phrase signs) and `DynamicSignRecognizer` / `TemporalProcessor` (sequence buffer for future LSTM/GRU plug-in, currently driving word/sentence assembly).
4. **Sign-to-Visual Demonstration**: Recognized words/phrases trigger a non-interrupting visual card showing a demonstration. Scalable asset metadata registry (`assets/signs.json`) with graceful fallback when no clip exists.
5. **Professional Accessibility-First Website**: Dashboard with nav (Dashboard | Live Translate | History | How It Works | Settings), live camera panel with landmarks + FPS + latency + status, current sign/word/sentence/confidence displays, visual demonstration panel, control buttons, translation output, history with search/filter/copy/replay, settings.
6. **Gesture Control Mode Preservation**: Keep existing mouse movement (index finger), pinch click, scroll, app launching (YouTube, Notepad, WhatsApp), gesture commands. Put them behind a clearly-separated *Computer Control* mode so communication gestures never accidentally click/launch.
7. **Multilingual Output**: English base + Hindi + Telugu + Spanish + French translations for recognized phrase signs (HI/THANKS/SORRY/BYE/PLEASE + extended vocabulary). Browser SpeechSynthesis with graceful degradation when voices unavailable.
8. **Honest Authentication Choice**: Keep the Flask-SQLAlchemy username/password gate, but *fix* the SECRET_KEY to read from `.env`, label it clearly as a demo convenience gate (not production security), and provide `.env.example`.
9. **Proper Error Handling**: Camera permission denied, camera unavailable, MediaPipe load failure, WebSocket disconnect, malformed payload, low-confidence recognition, missing visual asset, missing TTS voice, translation fallback.
10. **Honest README**: Document what is *actually* implemented. Distinguish fingerspelling sentence assembly from full ASL sign-language recognition. Describe model architecture, classes, sequence length, limitations, and training pipeline with no invented metrics.

## Non-Goals
- Training a new LSTM/Transformer sequence model on a dataset that does not ship with the repo (the architecture must be pluggable but runtime ships with the landmark-MLP alphabet recognizer + rule-based phrase signs only).
- Scraping or bundling copyrighted sign-language video clips (ship placeholder SVG/CSS animations + fallback text card).
- Production-grade authentication with JWTs, rate-limiting, CSRF protection (keep it a demo-local app, document the limitation).
- Microservices, Docker, Kubernetes, Redis, paid cloud APIs, huge remote AI models.
- Full ASL lexical sentence recognition (honestly label: "alphabet fingerspelling → word → sentence assembly + 20-item common phrase lexicon").
- Cross-platform Linux/macOS testing guarantees (primary target is Windows student laptop; code stays portable where cheap).

## Background & Context
Existing codebase inspected 2026-09-20:
- **app.py** — Active Flask server. Contains 2 additional entire commented-out servers (total 3 copies). Video uses `multipart/x-mixed-replace` MJPEG. Phrase recognition polls `/phrase_status` every 700 ms. Four modes: LAUNCH / CONTROL / SIGN / PHRASE. Phrase lexicon: HI/SORRY/THANKS/BYE/PLEASE with EN + FR translations. TTS uses gTTS via `/speak` endpoint returning MP3. User auth via Flask session + SQLite + werkzeug hashing. SECRET_KEY hardcoded `'your_secret_key'` then `os.environ.get('SECRET_KEY', 'dev_key')` on line 285. Routes `/`, `/about`, `/signup`, `/login`, `/app`, `/video_feed`, `/logout`, `/phrase_status`, `/set_mode/<mode>`, `/speak`. Bug: duplicate `main_app` routes at line 237 (`/app`) and line 256 (`/main`).
- **main.py** — Contains 6 commented-out standalone OpenCV scripts + 1 active script loading `asl_model.h5` TensorFlow CNN. Uses pyautogui for mouse + system-wide time.sleep(2) cooldowns blocking main loop.
- **modules/alphabet_recognizer.py** — 2 versions, active one loads `asl_model.h5` (image-CNN) plus its own duplicate MediaPipe Hands instance.
- **modules/gesture_recognizer.py** — Rule-based finger counting → Fist/Open Palm/Thumb Up/2 Fingers/3 Fingers/4 Fingers.
- **modules/tts.py** — gTTS temp-file approach.
- **modules/command_executor.py** — nircmd.exe volume + notepad.
- **modules/spell_word_mode.py + voice_to_text.py** — Standalone demos.
- **utils/stability.py** — `PredictionStabilizer`: deque window + majority vote with min_count. Usable as-is.
- **utils/sentence_builder.py** — `SentenceBuilder`: SPACE/DELETE/CLEAR/ENTER semantics. Usable as-is with minor extension.
- **utils/tts_engine.py** — pyttsx3 variant (unused by server).
- **training/** — *Excellent* honest landmark pipeline: `extract_landmarks.py` (wrist-relative, scale by wrist→middle-MCP, 63-dim features → `.npz`), `train_alphabet.py` (sklearn MLP [64,32] → pure-NumPy JSON export `models/alphabet_mlp.json`), `evaluate_alphabet.py` (exact same runtime forward path → metrics written back into model JSON).
- **static/style.css** — Professional dark design system: tokens, gradients, glassmorphism *within bounds*, Inter + Space Grotesk, full responsive breakpoints. Can be preserved and extended.
- **static/main.js** — Cursor ring + sparkle particle effects + spotlight card hover + fade-up IntersectionObserver.
- **templates/** — Jinja2: base, index, login, signup, main_app, about. main_app.html has polling for phrases. No MediaPipe on the client side (server does all inference).
- **requirements.txt** — tensorflow==2.15.0, flask==3.1.2, flask_sqlalchemy, opencv-*, mediapipe==0.10.32, numpy, matplotlib, pillow, pyttsx3, SpeechRecognition, sounddevice. Missing: fastapi, uvicorn, websockets, python-multipart, scikit-learn (needed for training path).
- **Empty files** — README.md, ui/gui.py.
- **.gitignore** — Ignores `*.h5` model files + venv. Missing `.env`, audio temp dir patterns.

Key insight: The **training pipeline** (landmark-normalized MLP → pure NumPy JSON) is the correct lightweight runtime path. The current server uses the opposite path (image-CNN + TensorFlow per-frame). The upgrade must switch the server to the landmark-MLP path so TensorFlow is only required for (optional) training, not runtime.

## Functional Requirements

### Application Architecture
- **FR-1**: One application server process (FastAPI) serves: static frontend, HTML pages, REST API, and WebSocket recognition.
- **FR-2**: One-command startup on Windows: `python run.py` and `.\Run-SilentLink.ps1` both work. Both check for venv and install deps on first run if missing.
- **FR-3**: Clean source tree: `backend/`, `frontend/`, `models/`, `assets/`, `training/`, `scripts/`. Old root-level duplicate scripts are either removed or refactored into the module tree (not left as broken zombie entry points).
- **FR-4**: `/health` endpoint returns JSON `{status: "ok", recognizer_loaded: bool, mediapipe_ready: bool}`.
- **FR-5**: Page routes: `/` (Landing), `/app` (Dashboard / Live Translate), `/history`, `/how-it-works`, `/settings`, `/login`, `/logout`, `/signup`.
- **FR-6**: Auth gate uses `SECRET_KEY` from `.env` (fallback: a generated per-instance warning-logs key). Demo-gate disclaimer shown on login page.

### Backend Recognition Pipeline
- **FR-7**: MediaPipe runs on the **server** inside the WebSocket handler or a shared process; clients send normalized 21×3 landmark arrays (reducing network) OR server does it (decision: server-side to keep client thin and consistent).
- **FR-8**: `StaticSignRecognizer` class: loads `models/alphabet_mlp.json`, runs pure-NumPy forward pass, returns `{sign: str|None, confidence: float, kind: "alphabet"|"phrase"|"gesture"}`.
- **FR-9**: Rule-based phrase sign recognizer for 20 common signs (HI, YES, NO, THANK_YOU, PLEASE, SORRY, HELP, GOOD, BAD, I, YOU, WE, WHAT, WHERE, HOW, NAME, FOOD, WATER, STOP, GO) integrated into StaticSignRecognizer with finger-state rules that do not overlap alphabet gestures.
- **FR-10**: `TemporalProcessor` owns: sliding-window stabilizer (PredictionStabilizer), confirmed-sign debounce, word buffer, word-boundary timeout (default 1.8 s pause → space), sentence buffer. Emits `{current_sign, current_word, sentence, confidence, status: "detecting"|"holding"|"confirmed"|"low_confidence"}`.
- **FR-11**: DynamicSignRecognizer skeleton: sequence buffer of N frames × 63 features, abstract `.predict()` that currently defers to StaticSignRecognizer but documents exactly where an LSTM/GRU would plug in. `models/dynamic_sign_placeholder.py`.
- **FR-12**: Word/sentence controls via WebSocket client messages: `{type:"control", action:"clear|undo|space|confirm_word|confirm_sentence|start|stop"}`.
- **FR-13**: Confidence threshold (default 0.6) + minimum hold duration (default 8 frames @ 30 FPS = 260 ms) before a sign is "confirmed" and enters the word buffer.
- **FR-14**: Duplicate suppression: holding the same letter must not repeat-append to the word buffer; a different confirmed letter clears the duplicate guard.

### WebSocket Schema
- **FR-15**: WebSocket at `/ws/recognize`. Client send messages:
  - `{type:"hand", landmarks:[{x,y,z}×21], timestamp:ms, session_id, mode:"communication"|"computer_control", target_language:"en"}`
  - `{type:"control", action, session_id}`
  - `{type:"ping", ts}`
- **FR-16**: Server messages:
  - `{type:"prediction", sign, confidence:0..1, status:"detecting|holding|confirmed|low_confidence|idle", current_word, sentence, visual_asset:{key,display,video|image|fallback,description}|null}`
  - `{type:"control_result", action, ok}`
  - `{type:"status", fps_server, latency_ms, backend_state}`
  - `{type:"error", code, message, suggestion}`
- **FR-17**: Graceful WebSocket reconnect: client attempts reconnect 10× with backoff; shows "Reconnecting…" banner.

### Visual Sign Demonstration
- **FR-18**: `assets/signs.json` metadata registry. Each entry: `{key, display, description, type:"phrase"|"letter", video:path|null, image:path|null, translations:{en,hi,te,es,fr}}`.
- **FR-19**: `assets/signs/<key>/` directory convention. At minimum: CSS/SVG placeholder animation rendered client-side for all 20+5 common signs (no video files required).
- **FR-20**: When a sign is confirmed, backend resolves its asset and broadcasts `visual_asset` in the prediction message. Frontend renders a card in the dashboard sidebar without interrupting camera or recognition state.
- **FR-21**: Fallback when asset missing: card shows "Visual demonstration unavailable" + recognized word + textual description (app never breaks).
- **FR-22**: `assets/ATTRIBUTIONS.md` present, listing sources/licenses even when all assets are project-created placeholders.

### UI / Dashboard
- **FR-23**: Navigation bar with: SilentLink logo, Dashboard | Live Translate | History | How It Works | Settings, Login/Logout (auth-aware).
- **FR-24**: Live Translate page layout: Camera panel (video, landmark overlay via MediaPipe on the client, FPS, latency, status badge, current sign overlay), Recognition sidebar (Current Sign, Current Word, Sentence, Confidence bar), Sign Visualization card, Controls row (Start/Pause/Clear/Undo/Space/Confirm Word/Confirm Sentence/Speak), Translation panel (5 languages), Mode toggle: Communication ↔ Computer Control.
- **FR-25**: **Client-side MediaPipe** for camera + landmark rendering + sending landmarks over WebSocket (so the server MJPEG is removed; the browser owns the camera). Server remains the authority for recognition (MLP inference + temporal state) so one consistent pipeline.
- **FR-26**: History page: session-scoped entries (timestamp, sign/word/sentence, confidence, translation). Actions: clear, search/filter, copy sentence, replay visual, speak. LocalStorage-backed with optional backend persistence via history endpoint.
- **FR-27**: Settings page: sensitivity (confidence threshold slider), stabilization window, word-boundary timeout, target TTS language, dark mode, reduced-motion toggle. Persists to localStorage.
- **FR-28**: How It Works page: explains the MediaPipe → normalized landmarks → MLP → stabilizer → word → sentence pipeline with simple diagrams/text; distinguishes fingerspelling vs. phrase signs vs. (future) dynamic signs; lists supported signs table.
- **FR-29**: Accessibility: semantic HTML, ARIA labels on live regions, keyboard navigable controls, visible focus, 4.5:1 text contrast, `prefers-reduced-motion` disables sparkles/spots/non-essential animations, captions/text next to every sign visualization.
- **FR-30**: Responsive: grid collapses to single column under 1024px; controls stack; touch-friendly tap targets ≥ 44px.

### Computer Control Mode (preserved, isolated)
- **FR-31**: Mode toggle in UI: Communication ↔ Computer Control. Only when Computer Control mode is active does the backend execute:
  - Index-finger position → `pyautogui.moveTo` (screen mapping).
  - Pinch (index-thumb distance < 0.03 normalized, 1 s debounce) → left click.
  - 2-finger (index + middle) vertical delta → scroll.
  - App-launch gestures: Index only → YouTube, 3 fingers → Notepad, 4 fingers → WhatsApp, Fist held 2 s → return to LAUNCH baseline.
- **FR-32**: In Communication mode, identical finger shapes NEVER trigger clicks/apps. Code paths are fully separated.
- **FR-33**: Computer Control action cooldowns and `pyautogui.FAILSAFE=False` only in that module's scope.

### Translation & TTS
- **FR-34**: Recognized phrase signs return translations for en, hi, te, es, fr. Alphabet-fingerspelled words return as-is in en with a "no automatic translation" message (honest: no paid MT API).
- **FR-35**: Browser SpeechSynthesis API for TTS; selects matching voice if available; gracefully falls back to default voice and shows "Voice unavailable for this language" badge if not.
- **FR-36**: Speak button per translation row + Speak All; client-side (avoids temp MP3 files and gTTS network dependency at runtime). Document that if offline gTTS is preferred, the backend `/speak` endpoint remains available as a fallback.

### Training Pipeline (preserved, documented)
- **FR-37**: `training/extract_landmarks.py` stays as-is (honest normalization docstring).
- **FR-38**: `training/train_alphabet.py` + `training/evaluate_alphabet.py` stay as-is (JSON model card with real evaluation metrics).
- **FR-39**: New `training/train_dynamic_signs.py` scaffold for sequence data → LSTM export. Documents: classes, sequence length, features, normalization, model architecture. Contains no invented weights; it raises "No sequence dataset bundled" with instructions.
- **FR-40**: `dataset/` folder placeholder README describing expected layout. `models/` folder contains the current alphabet MLP and placeholder for dynamic model.

### Error Handling
- **FR-41**: Camera permission denied → UI shows a descriptive card with browser-specific allow instructions + retry button; never crashes the page.
- **FR-42**: Camera unavailable (no device) → separate state from permission denied.
- **FR-43**: MediaPipe model loading failure → banner, "How It Works / Troubleshooting" link.
- **FR-44**: Backend unavailable / WebSocket disconnect → sticky "Disconnected" banner + automatic reconnect attempts + manual retry.
- **FR-45**: Malformed landmark payload (server) → `{type:"error", code:"bad_landmarks", …}`; server does not crash.
- **FR-46**: Low confidence (< threshold) → prediction `status: "low_confidence"`; visual dimmed, does not enter word buffer.
- **FR-47**: Missing visual asset → graceful fallback card.
- **FR-48**: Missing TTS voice for target language → inline badge, falls back to en.
- **FR-49**: Unsupported browser (no getUserMedia, no SpeechSynthesis) → detection + friendly message.

### Security
- **FR-50**: `.env.example` ships with required keys; `.env` is gitignored; no hardcoded secrets in source; default SECRET_KEY fallback logs a WARNING at startup.
- **FR-51**: Passwords hashed with werkzeug/itsdangerous equivalent; never logged; session cookie HttpOnly (FastAPI SameSite).
- **FR-52**: WebSocket payloads size-limited and schema-validated (pydantic).

## Non-Functional Requirements
- **NFR-1 (Runtime perf)**: On a typical student laptop (8 GB RAM, 4-core CPU, integrated GPU), recognition pipeline sustains ≥ 15 Hz end-to-end (client landmarks → server MLP → stabilizer → word state → WebSocket broadcast). UI jank free: DOM updates ≤ 60 FPS.
- **NFR-2 (Memory)**: Server steady-state RSS ≤ 400 MB with MediaPipe loaded. Client tab ≤ 500 MB during active camera.
- **NFR-3 (Build/install)**: `requirements.txt` split (runtime.txt vs. training.txt optional, or a single requirements with extras) so a first-time `pip install -r requirements.txt` + `python run.py` works on Windows in ≤ 5 minutes.
- **NFR-4 (Dependency honesty)**: TensorFlow is only required for the legacy CNN training path (not imported by the running app). Document in README and guard imports.
- **NFR-5 (Code quality)**: Each module ≤ ~400 lines; clear single responsibility; type hints on function signatures; no 1000-line god files.
- **NFR-6 (Maintainability)**: Codebase explainable in an interview by a student: each folder purpose, each class responsibility, data flow from webcam → sentence → TTS drawn clearly in architecture section of README.
- **NFR-7 (Robustness)**: No uncaught exceptions in the WebSocket loop; 500 errors return structured JSON; never a white screen of death on the frontend.
- **NFR-8 (Accessibility score target)**: Lighthouse a11y ≥ 90 or equivalent manual review of the 8 WCAG items in FR-29.

## Constraints
- **Technical**: Must run locally on Windows student laptop. No paid APIs. Frontend is plain HTML/CSS/JS (no build step, no React/Vite bundler — matches existing templates pattern so a student can reason about every file). Web server is FastAPI + Uvicorn. WebSocket schema hand-rolled for clarity.
- **Business**: Preserve all *working* existing functionality; remove only the duplicate dead copies. Do not fake sentence-level ASL lexical recognition.
- **Dependencies**: MediaPipe 0.10.x, NumPy, OpenCV, FastAPI, Uvicorn, Flask-SQLAlchemy-equivalent for auth (or keep the tiny SQLite auth module under backend with same SQLAlchemy), PyAutoGUI (optional import, lazy), scikit-learn (training-only optional).

## Assumptions
1. The ASL alphabet image dataset under `data/asl_alphabet_train/` and the trained `models/alphabet_mlp.json` will exist at runtime OR the app will gracefully degrade with "Model not trained yet — run training/ pipeline". (We do not ship image data; we ship code paths.)
2. No copyrighted video assets can be bundled. Placeholder assets are project-created SVG/CSS animations.
3. Browser SpeechSynthesis availability varies by OS; we never claim a specific voice is guaranteed.
4. PyAutoGUI on Windows may require elevated permissions or display-config tweaks; document in Troubleshooting.
5. User has Python 3.10–3.11 on Windows (TensorFlow 2.15 / MediaPipe 0.10 compatibility range).

## Open Questions
- [ ] Is the existing dataset folder present on the evaluator's machine? (Plan: the app must start cleanly even without `models/alphabet_mlp.json` and show a setup banner.)
- [ ] Preferred startup script name: keep both `run.py` and `Run-SilentLink.ps1` as specified.
- [ ] Auth: the user spec offered Option A (remove) vs Option B (real backend auth). We implement Option B but label it *honestly* as demo-grade — confirmed no fake claims.

## Acceptance Criteria

### AC-1: One FastAPI process serves everything
- **Type**: `rule`
- **Given**: A clean repo, dependencies installed, `.env` present
- **When**: User runs `python run.py` on Windows
- **Then**: One Uvicorn process starts, listening on a single port (default 8000), serving static frontend, HTML pages, REST, and WebSocket simultaneously
- **Pass Condition**: `curl http://localhost:8000/health` returns `{"status":"ok"}`; the dashboard page loads; a WebSocket to `ws://localhost:8000/ws/recognize` connects
- **Evidence**: Terminal output of startup + `curl` / browser screenshot

### AC-2: Landmark-MLP recognition path (no TensorFlow import at runtime)
- **Type**: `rule`
- **Given**: Running server, Python process
- **When**: Inspecting imported modules
- **Then**: `tensorflow` is NOT in `sys.modules` during normal operation (only the pure-NumPy `alphabet_mlp.json` path is active)
- **Pass Condition**: A health/info endpoint or debug command confirms `tensorflow_imported: false`
- **Evidence**: Server endpoint JSON or `python -c "import sys; …"` check output

### AC-3: Temporal stabilizer produces HELLO not HHHHEEELLLLOOO
- **Type**: `rule`
- **Given**: A synthetic stream of per-frame predictions: [H×10, E×10, L×10, L×10, O×10] above confidence threshold
- **When**: Processed through TemporalProcessor
- **Then**: Confirmed letters emitted are exactly H, E, L, L, O (no duplicates per hold); current_word builds "HELLO"; after word-boundary timeout, sentence becomes "HELLO"
- **Pass Condition**: A unit test or scripted simulation produces the expected sequence
- **Evidence**: Python test output / log showing confirmed-letter stream and word/sentence progression

### AC-4: Communication mode never clicks the mouse
- **Type**: `rule`
- **Given**: App in "Communication" mode, index finger moving + pinch gesture
- **When**: Sending landmarks that match the CONTROL-mode click/pinch pattern
- **Then**: pyautogui is never invoked; no `pyautogui.click` call occurs
- **Pass Condition**: Instrumented counter for `pyautogui` invocations stays at 0 while mode == communication
- **Evidence**: Counter log / assert in test

### AC-5: Missing visual asset degrades gracefully
- **Type**: `rule`
- **Given**: A sign key "ZEBRA" exists in the recognition output but has no `assets/signs/zebra/…` entry
- **When**: Frontend receives the prediction message
- **Then**: The visualization card renders with "Visual demonstration unavailable" + sign name + text description; page does not throw; console has no uncaught JS errors
- **Pass Condition**: Browser console clean; card visible with fallback copy
- **Evidence**: DOM screenshot + console logs

### AC-6: WebSocket reconnect after simulated disconnect
- **Type**: `rule`
- **Given**: Active dashboard page, connected WS, server briefly restarted
- **When**: Connection drops then server returns within 30 s
- **Then**: Client shows "Reconnecting…" banner, retries with backoff, recovers without a manual refresh, and recognition resumes
- **Pass Condition**: Manual test: restart server while page is open; after server up, page auto-recovers within 30 s
- **Evidence**: UI banner screenshots and WS frames in the browser Network tab

### AC-7: SECRET_KEY loaded from .env (not hardcoded)
- **Type**: `rule`
- **Given**: `.env` file with `SECRET_KEY=test-abc`, `.env.example` ships, `.env` is in `.gitignore`
- **When**: App starts
- **Then**: Session middleware uses `test-abc`; if `.env` is missing, a WARNING is logged and a per-instance ephemeral key is used (not a hardcoded string like `"your_secret_key"`)
- **Pass Condition**: grep of repo for hardcoded `SECRET_KEY.*=.*'[^']+'` → 0 matches in code paths; startup log line confirms env key
- **Evidence**: grep output + startup log snippet

### AC-8: History with clear/search persists across page reload
- **Type**: `rule`
- **Given**: Dashboard, history populated with 5 entries, user refreshes browser
- **When**: After reload, opens History page
- **Then**: 5 entries still present; clear-history button empties it; search filters match by text
- **Pass Condition**: localStorage read-back matches entries after reload
- **Evidence**: DevTools Application → Local Storage screenshot + UI before/after

### AC-9: Dashboard visual layout professionalism (rubric)
- **Type**: `rubric`
- **Dimension**: Visual polish, information hierarchy, and professional feel of the Live Translate dashboard
- **Scale**: 1–5
- **Anchors**: 1 = college-demo clutter (overlays, no hierarchy, broken centering); 3 = functional but generic (one big column, inconsistent spacing, random emoji); 5 = product-grade (clear sections, consistent typography, meaningful status indicators, deliberate whitespace, aligned with the existing design tokens)
- **Pass Threshold**: ≥ 4
- **Evidence**: Full-page screenshot + checklist vs. the 6 layout sections in the user spec (nav, camera, recognition, visualization, controls, translation)

### AC-10: Code structure explainability (rubric)
- **Type**: `rubric`
- **Dimension**: Modularization, separation of concerns, and folder-level clarity
- **Scale**: 1–5
- **Anchors**: 1 = everything in 2–3 monster files with dead commented copies; 3 = some separation but ambiguous boundaries; 5 = each folder/class has one clear job, data flow is traceable in a single read-through, and each module ≤ ~400 LOC
- **Pass Threshold**: ≥ 4
- **Evidence**: Final folder tree listing + per-module description in README architecture section

### AC-11: README honesty and completeness (rubric)
- **Type**: `rubric`
- **Dimension**: README matches actual implementation, honestly describes limitations, and contains every required section (overview, features, architecture, stack, structure, install, run, model setup, dataset/training, supported signs, WebSocket API, troubleshooting, limitations, future work, credits)
- **Scale**: 1–5
- **Anchors**: 1 = README empty or fabricates "full ASL sentence recognition"; 3 = describes parts but misses limitations / API; 5 = every required section present, capability labels are strictly accurate ("alphabet fingerspelling → word/sentence assembly + 20 phrase signs"), WebSocket schema fully documented, troubleshooting covers PyAutoGUI / MediaPipe / camera permission pain points
- **Pass Threshold**: ≥ 4
- **Evidence**: Final README.md content review

### AC-12: End-to-end happy-path integration
- **Type**: `rule`
- **Given**: Running app, camera permission granted, model loaded
- **When**: User (1) opens `/app`, (2) toggles to Communication mode, (3) simulates H-E-L-L-O letter signs via a test fixture or manual, (4) triggers Speak, (5) switches to Computer Control and confirms cursor moves without firing in Communication
- **Then**: Camera shows landmarks; Current Sign/Word/Sentence update; Visual card appears; Speak plays audio; History has entries; Computer Control moves cursor but Communication mode did not trigger pyautogui
- **Pass Condition**: Every step in the sequence produces the observable output described
- **Evidence**: Screen recording or annotated screenshots of the sequence
