#!/usr/bin/env python3
"""SilentLink — top-level launcher.

Usage:
    python run.py                 # default host/port from .env
    python run.py --host 0.0.0.0  # override host
    python run.py --port 9000     # override port
    python run.py --no-reload     # disable uvicorn auto-reload

This script simply delegates to `uvicorn backend.main:app` and ensures
the working directory and imports line up correctly.
"""
from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    os.chdir(here)

    from backend.config import settings

    parser = argparse.ArgumentParser(description="Run the SilentLink FastAPI server.")
    parser.add_argument("--host", default=settings.HOST, help=f"Bind host (default: {settings.HOST})")
    parser.add_argument("--port", type=int, default=settings.PORT, help=f"Bind port (default: {settings.PORT})")
    parser.add_argument("--no-reload", action="store_true", help="Disable uvicorn auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of uvicorn workers (default 1)")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as e:
        print("[SilentLink] uvicorn not installed. Run:  pip install -r requirements.txt", file=sys.stderr)
        raise SystemExit(1) from e

    print(f"[SilentLink] launching on http://{args.host}:{args.port}  (reload={'ON' if not args.no_reload else 'OFF'}, workers={args.workers})")
    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        workers=args.workers if args.workers > 1 else None,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
