"""Locate ffmpeg/ffprobe and run them without a shell."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    """ffmpeg or ffprobe failed or is missing."""


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise FFmpegError(
            "ffmpeg is not on PATH. Install it, then restart Film Lab.\n"
            "  Windows: winget install Gyan.FFmpeg\n"
            "  Debian/Ubuntu: sudo apt install ffmpeg\n"
            "  macOS: brew install ffmpeg"
        )
    return exe


def find_ffprobe() -> str | None:
    return shutil.which("ffprobe")


def ffmpeg_available() -> tuple[bool, str]:
    try:
        exe = find_ffmpeg()
    except FFmpegError as exc:
        return False, str(exc)
    try:
        proc = subprocess.run(
            [exe, "-version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return False, f"ffmpeg found but failed to run: {exc}"
    first = (proc.stdout or "").splitlines()[:1]
    banner = first[0] if first else exe
    return True, banner


def run_ffmpeg(args: list[str], *, cwd: Path | None = None) -> None:
    exe = find_ffmpeg()
    cmd = [exe, "-hide_banner", "-loglevel", "error", *args]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
        raise FFmpegError(f"ffmpeg failed: {detail}")


def probe_duration_seconds(path: Path) -> float | None:
    ffprobe = find_ffprobe()
    if not ffprobe:
        return None
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def probe_has_audio(path: Path) -> bool | None:
    """Return True/False when ffprobe can inspect audio streams, else None."""
    ffprobe = find_ffprobe()
    if not ffprobe:
        return None
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    return "audio" in (proc.stdout or "").lower()


def ffmpeg_filter_available(filter_name: str) -> tuple[bool, str]:
    """Return whether this ffmpeg build exposes an exact video/audio filter name."""
    try:
        exe = find_ffmpeg()
        proc = subprocess.run([exe, "-hide_banner", "-filters"], capture_output=True, text=True)
    except OSError as exc:
        return False, f"ffmpeg filter discovery failed: {exc}"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "ffmpeg -filters failed").strip()
    wanted = str(filter_name or "").strip()
    for line in (proc.stdout or "").splitlines():
        parts=line.split()
        if len(parts) >= 2 and parts[1] == wanted:
            return True, line.strip()
    return False, f"ffmpeg filter `{wanted}` is unavailable in this build."
