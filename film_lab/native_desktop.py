"""Film Lab native desktop shell.

Starts the existing Gradio application as a child process and hosts its localhost UI
inside a dedicated native window when pywebview is available. Browser mode remains
an explicit backup, not the normal Creator experience.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

HOST = os.getenv("FILM_LAB_HOST", "127.0.0.1")
PORT = int(os.getenv("FILM_LAB_PORT", "43123"))
URL = f"http://{HOST}:{PORT}"
ROOT = Path(__file__).resolve().parents[1]


def _ready(timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def _already_running() -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=0.25):
            return True
    except OSError:
        return False


def main() -> int:
    child: subprocess.Popen[str] | None = None
    if not _already_running():
        env = os.environ.copy()
        env["FILM_LAB_HOST"] = HOST
        env["FILM_LAB_PORT"] = str(PORT)
        log_dir = ROOT / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log = (log_dir / "desktop-app.log").open("a", encoding="utf-8")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        child = subprocess.Popen(
            [sys.executable, str(ROOT / "app.py")],
            cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT,
            text=True, creationflags=flags,
        )
    if not _ready():
        if child and child.poll() is None:
            child.terminate()
        raise SystemExit("Film Lab could not start. See data/logs/desktop-app.log")

    try:
        import webview  # type: ignore
    except ImportError:
        webbrowser.open(URL)
        print("Native window component is unavailable; opened Browser Backup mode.")
        return 0

    webview.create_window(
        "Film Lab — Create · Direct · Produce", URL,
        width=1500, height=930, min_size=(1100, 700),
        background_color="#0f1113",
    )
    try:
        webview.start(debug=False)
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
