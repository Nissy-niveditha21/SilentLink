# Silentlink

A futuristic gesture-control experience that turns your webcam into a hands-free command center.

Silentlink blends computer vision, real-time hand tracking, and a polished web dashboard to let you control your PC with natural gestures. From cursor movement and clicks to scrolling, dragging, and launch actions, the system turns your hand motions into intuitive digital commands.

![Silentlink](https://img.shields.io/badge/status-active-brightgreen)
![Silentlink](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20Vite-blue)

---

## Why Silentlink?

Imagine interacting with your computer without touching a mouse or keyboard:

- Move the cursor with your index finger
- Click, drag, and scroll with simple gestures
- Trigger app launches like WhatsApp or YouTube
- Use hold-to-confirm actions for safer command execution
- Translate and display gesture-based text in the UI

This project is built for experimentation, demos, accessibility, and the thrill of creating a genuinely hands-free interface.

---

## ✨ Core Features

- Real-time webcam hand tracking
- Gesture-driven cursor control
- Click, drag, scroll, and drop actions
- Hold-to-confirm interaction flow
- ASL-inspired symbol recognition
- WebSocket-powered live processing
- Clean React + Tailwind dashboard

---

## 🧠 How It Works

1. The webcam feed is processed in the frontend.
2. Hand landmark data is sent to the backend over WebSockets.
3. The gesture engine interprets the motion and returns a command result.
4. The backend executes the command and updates the connected interface.

This makes the app feel responsive, modular, and easy to extend as more gestures are added.

---

## 🛠️ Tech Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- Framer Motion

### Backend
- FastAPI
- Python
- WebSockets
- PyAutoGUI
- Deep Translator

---

## 📁 Project Structure

```text
Silentlink/
├── backend/         # FastAPI server, gesture logic, command execution
├── frontend/        # React/Vite dashboard UI
├── standalone_frontend/  # Lightweight standalone web interface
└── Run-Silentlink.ps1    # One-click local launcher
```

---

## 🚀 Quick Start

### 1. Install frontend dependencies

```powershell
cd frontend
npm install
```

### 2. Set up the Python backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn pyautogui deep-translator
```

### 3. Run the app

Option A — use the bundled launcher:

```powershell
powershell -ExecutionPolicy Bypass -File .\Run-Silentlink.ps1
```

Option B — manual start:

```powershell
cd frontend
npm run build

cd ..\backend
uvicorn main:app --reload --port 8000
```

Then open:

```text
http://localhost:8000
```

---

## 🎯 What You Can Do

- Use hand gestures to navigate and interact with your screen
- Launch apps with simple pose patterns
- Send commands through the live dashboard
- Explore gesture-driven messaging and control workflows

---

## 🔮 Future Improvements

- More gesture vocabulary and better ASL recognition
- Better accuracy with advanced hand-tracking models
- Voice + gesture hybrid control
- Multi-language command support
- Custom gesture profiles for different users

---

## Contributing

Contributions are welcome. If you want to improve the gesture model, UI, or command system, feel free to open an issue or submit a pull request.

---

## License

This project is currently under active development.
