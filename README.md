# SilentLink — Intelligent Sign Language Communication Platform

SilentLink bridges sign language and spoken/written language using **MediaPipe Hands**, a deterministic 25-phrase rule engine, a pure-NumPy fingerspelling MLP, bidirectional LSTM placeholders for dynamic signs, and an end-to-end FastAPI + WebSocket frontend. Everything runs in the browser except the landmark→classification pass, so raw video never leaves your device.

```
                  ┌───────────────────────────┐
  webcam ───────▶ │  MediaPipe Hands (WASM)   │
                  │  21 xyz landmarks / frame │
                  └─────────────┬─────────────┘
                                │   WebSocket /ws/sign
                                ▼
              ┌────────────────────────────────────────┐
              │          FastAPI backend               │
              │  ┌────────────┐   ┌─────────────────┐ │
              │  │ Phrase 25  │──▶│  TemporalProc   │ │
              │  │ rule engine│   │  + stabilizer   │ │
              │  └────────────┘   └────────┬────────┘ │
              │  ┌────────────┐            │          │
              │  │ NumPy MLP  │──26 letters│ sentences│
              │  └────┬───────┘            ▼          │
              │       Phrase + letters   Translator   │── 5 langs + fingerspell
              │                              │         │
              │              asset_resolver (SVG)     │
              │                              │         │
              │          ComputerControlService       │ ← opt-in cursor control
              └────────────────────────────────────────┘
                                │
            Jinja2 Templates (7 pages) + CSS + MediaPipe client JS
```

## Quick Start (Windows — recommended)

```powershell
.\Run-SilentLink.ps1
```

The PowerShell launcher automatically:
- creates `veenv\` virtual environment if missing
- installs `requirements.txt` on first run
- copies `.env.example` → `.env` so the app boots without hand edits
- opens your browser to the dashboard

## Quick Start (macOS / Linux / manual)

```bash
python -m venv veenv
source veenv/bin/activate            # Windows: veenv\Scripts\activate
pip install -r requirements.txt
[ ! -f .env ] && cp .env.example .env
python run.py                         # or: uvicorn backend.main:app --reload
```

Then open **http://127.0.0.1:8000** in a Chromium-based browser, sign up/in, and allow the camera.

## Feature Matrix

| Area            | What ships                                                                                               |
|-----------------|----------------------------------------------------------------------------------------------------------|
| **Project**     | folder tree per spec, `.env.example`, `.gitignore`, deduped files (`utils/` duplicates removed), `requirements.txt` + `requirements-training.txt` |
| **Backend**     | FastAPI, pydantic-settings config, itsdangerous cookie auth (SQLAlchemy user table), CSP/gzip middleware, Jinja2 templates mounted from `frontend/`, error handlers, static asset mounts |
| **Recognition** | wrist-relative 63-d normalization (`features.py`), pure-NumPy softmax MLP (`numpy_mlp.py`), 25-rule phrase engine + `StaticSignRecognizer`, seq-buffer `DynamicSignRecognizer` (BiLSTM swap point), `TemporalProcessor` with `PredictionStabilizer` + `SentenceBuilder` + hold/timeout debounce |
| **Computer Ctrl** | isolated `ComputerControlService` (pyautogui try-import + FAILSAFE off), move/pinch-click/2-finger-scroll/4-app launcher, strictly gated behind `CONTROL` mode in `/api/mode` |
| **Visual assets** | `signs.json` 5-language metadata, 28 SVG placeholder hands (`assets/signs/KEY/placeholder.svg`), `ATTRIBUTIONS.md`, `AssetResolver` with UNKNOWN fallback |
| **Translation** | 5 languages (`en/hi/te/es/fr`) via `TranslationService.translate_phrase`, fingerspell fallback for alphabet words, per-language sentence re-assembly |
| **Training**    | `extract_landmarks.py` → `train_alphabet.py` (sklearn MLP → JSON weights) → `evaluate_alphabet.py` (writes metrics back into model card JSON), `train_dynamic_signs.py` (PyTorch BiLSTM → JSON weights). See `dataset/README.md` + `models/README.md` |
| **WebSocket**   | Pydantic schemas (`schemas.py`), `ConnectionManager` + session ids + stale purge, `/ws/sign` route plumbing frame→recognizer→temporal→translation→history store, exponential-backoff reconnect on the client |
| **HTML**        | 7 pages: `index`, `about`, `login`, `signup`, `app` (translator dashboard), `history`, `how_it_works`, `settings` with semantic landmarks + ARIA a11y + sr-only labels where appropriate |
| **JS**          | MediaPipe Hands via jsDelivr + getUserMedia camera, canvas landmark overlay, WebSocket reconnect, mode switcher (COMMUNICATION/CONTROL/PHRASE), undo/space/clear controls, sentence word indicators, 5-language phrase card, local history persistence, settings panel |
| **CSS**         | custom design system (tokens, gradients, glass surfaces, spotlight hover), responsive breakpoints (1024/900/640px), keyboard focus rings via native `:focus-visible`, reduced-motion hooks, custom cursor + spark FX |
| **Scripts**     | `run.py` (cross-platform launcher) + `Run-SilentLink.ps1` (Windows launcher with venv/bootstrap/browser-open) |
| **Tests**       | `tests/test_static_sign_rules.py` smoke tests (empty/None/short landmarks); add your pytest suite here |
| **Errors**      | Middleware security headers, JSON 404/500 + HTTPException handlers, try/except around every recognizer stage, WS parse/validation errors surfaced to client |

## Folder Layout

```
SilentLink/
├─ backend/
│  ├─ controllers/         # pages, health, auth (cookie sessions)
│  ├─ recognition/         # features.py · numpy_mlp.py · static/dynamic/temporal/stability/sentence_builder
│  ├─ services/            # asset_resolver.py · translation.py · computer_control.py
│  ├─ websocket/           # schemas.py · manager.py · routes.py
│  ├─ config/__init__.py   # pydantic-settings SECRET_KEY / DATABASE_URL / HOST / PORT
│  ├─ db/__init__.py       # SQLAlchemy engine + get_db/init_db (SQLite default)
│  ├─ models/user.py       # User(username, password_hash)
│  └─ main.py              # FastAPI app, mounts, endpoints, startup banner
├─ frontend/
│  ├─ templates/           # base + 7 Jinja2 pages
│  └─ static/              # style.css · main.js
├─ assets/
│  ├─ signs.json           # 5-lang phrase metadata + image paths + type tags
│  ├─ ATTRIBUTIONS.md      # CC0 1.0 placeholder SVG declaration
│  └─ signs/<KEY>/placeholder.svg   # 28 SVG hand placeholders
├─ training/               # extract_landmarks · train_alphabet · evaluate_alphabet · train_dynamic_signs
├─ scripts/                # train_alphabet.ps1 · _run_pipeline.ps1 · asset_resolver_stub.py
├─ dataset/README.md       # expected layout + public download pointers
├─ models/                 # alphabet_mlp.json (after training) · README.md
├─ tests/                  # test_static_sign_rules.py · __init__.py
├─ utils/tts_engine.py     # optional pyttsx3 wrapper
├─ requirements.txt
├─ requirements-training.txt   # + tensorflow / scikit-learn for training machines
├─ .env.example
├─ .gitignore
├─ run.py
├─ Run-SilentLink.ps1
└─ README.md
```

## Train Your Own Fingerspelling MLP

```powershell
# 1. Download a public ASL alphabet dataset (Kaggle "ASL Alphabet" CC0-style)
#    into data/asl_alphabet_train/<A-Z>/<image>.jpg
#
# 2. Extract landmarks → compressed npz:
veenv\Scripts\python.exe training\extract_landmarks.py --data data\asl_alphabet_train --out data\asl_landmarks.npz --samples 400

# 3. Train sklearn MLP → JSON weights:
veenv\Scripts\python.exe training\train_alphabet.py --data data\asl_landmarks.npz --out models\alphabet_mlp.json

# 4. Evaluate (pure-NumPy forward pass matches runtime) and write metrics into the model card:
veenv\Scripts\python.exe training\evaluate_alphabet.py --model models\alphabet_mlp.json --data data\asl_landmarks.npz
```

Or one-click on Windows: `scripts\train_alphabet.ps1`.

## Train the Dynamic BiLSTM (future)

```powershell
veenv\Scripts\python.exe training\train_dynamic_signs.py --seq-dataset dataset\sequences --out models\dynamic_sign_lstm.json --hidden 64 --layers 2 --epochs 30
```

Expected dataset layout is documented in `dataset/README.md` (`sequences/<sign>/sample_XXXX.npy` of shape `(seq_len, 21, 3)`).

## Endpoints Summary

| Method | Path                    | Purpose                                                          |
|--------|-------------------------|------------------------------------------------------------------|
| GET    | `/`, `/about`, `/history`, `/how-it-works`, `/settings` | pages |
| GET/POST | `/login`, `/signup`, `/logout`  | itsdangerous cookie auth                        |
| GET    | `/app`                  | translator dashboard (authenticated redirect)                   |
| GET    | `/health`               | liveness + recognizer-loaded booleans                            |
| WS     | `/ws/sign`              | bidirectional landmark→recognition stream                        |
| GET    | `/api/sign/{sign_key}`  | resolve `signs.json` entry → asset payload                       |
| GET    | `/api/translate`        | sentence translation across 5 languages                          |
| POST   | `/api/mode?mode=…`      | set `COMMUNICATION` / `CONTROL` / `PHRASE` mode                  |
| GET    | `/api/phrase_status`    | last detected phrase translations (for polling fallbacks)        |
| GET    | `/speak?text=…&lang=…`  | optional server-side pyttsx3 utterance (WebTTS also available)   |
| GET    | `/api/docs`, `/api/redoc` | auto-generated OpenAPI UI                                      |

## Accessibility Notes

- Every interactive page has semantic `<main>/<nav>/<section>/<article>` landmarks.
- Mode buttons use `role="tablist"` / `role="tab"` / `aria-selected`.
- Live sentences and recognition status are bound to `aria-live="polite"`.
- All inputs have real `<label>` elements and visible `:focus-visible` outlines.
- Reduced-motion / custom-cursor / text-size toggles are on the Settings page.
- Icons never convey information on their own — every icon has an adjacent text label.

## License & Attribution

All bundled SVG hand placeholders are released under **CC0 1.0 Universal** — see `assets/ATTRIBUTIONS.md`.
Real demo videos may be added under `assets/signs/<KEY>/demo.mp4` by contributors provided their license is compatible (document sources there).

SilentLink code is released under the MIT license. Enjoy signing. 💙
