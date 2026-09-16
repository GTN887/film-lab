"""Offline-first Film Lab. Local Comfy generation needs no internet.

Core desks (Motion, Still, Take Board, Character, Mark & Direct, UGC)
run on local models once they are installed. Grok / Gemini / ChatGPT /
Claude / ElevenLabs are online optional. Zero credits.
"""

from __future__ import annotations

import os
from pathlib import Path

from film_lab.duration import DEFAULT_DURATION_PRESET
from film_lab.quality import DEFAULT_QUALITY, QUALITY_480

CORE_DESKS: tuple[str, ...] = (
    "Motion",
    "Still",
    "Take Board",
    "Character",
    "Mark & Direct",
    "UGC",
)
ONLINE_OPTIONAL: tuple[str, ...] = (
    "Grok",
    "Gemini",
    "ChatGPT",
    "Claude",
    "ElevenLabs",
)

WORKS_OFFLINE = "Works offline for local generation"


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def logs_dir() -> Path:
    path = data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_mode_flag() -> Path:
    return data_dir() / "safe_mode.flag"


def offline_forced() -> bool:
    """User asked to skip cloud keys this session."""
    return _truthy("FILM_LAB_OFFLINE")


def safe_mode() -> bool:
    return _truthy("FILM_LAB_SAFE_MODE") or safe_mode_flag().is_file()


def set_safe_mode(on: bool) -> None:
    flag = safe_mode_flag()
    if on:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text("480p / 5s\n", encoding="utf-8")
        os.environ["FILM_LAB_SAFE_MODE"] = "1"
        return
    if flag.is_file():
        flag.unlink()
    os.environ.pop("FILM_LAB_SAFE_MODE", None)


def boot_quality() -> str:
    return QUALITY_480 if safe_mode() else DEFAULT_QUALITY


def boot_duration() -> str:
    return "5s" if safe_mode() else DEFAULT_DURATION_PRESET


def offline_banner_html() -> str:
    """Always-on strip: Offline | Online optional."""
    desks = " · ".join(CORE_DESKS)
    online = " / ".join(ONLINE_OPTIONAL)
    safe = " · Safe mode 480p / short clip" if safe_mode() else ""
    return (
        "<div class='fl-offline-banner' role='status'>"
        "<span class='fl-offline-chip'>Offline</span>"
        f"<span>Core desks ({desks}) use local Comfy models only.{safe} "
        f"{WORKS_OFFLINE}.</span>"
        "<span class='fl-offline-chip fl-offline-chip-dim'>Online optional</span>"
        f"<span>{online} — keys you own, never required.</span>"
        "</div>"
    )


def repair_markdown() -> str:
    return (
        "### Repair (desktop, works offline)\n"
        "Double-click **REPAIR.bat** — no internet, no PowerShell:\n"
        "1. **Restart Film Lab**\n"
        "2. **Restart Comfy** (GPU1 / `--cuda-device 1`)\n"
        "3. **Kill ports** `43123` and `8188`\n"
        "4. **Open logs** (`data/logs/`)\n"
        "5. **Safe mode** — 480p + 5s clip, then START\n\n"
        "First launch: **Install Film Lab** (`INSTALL_FILM_LAB.bat`) places files "
        "and the Desktop / Start Menu icon. Daily: **START_FILM_LAB.bat**. "
        "Uninstall: **UNINSTALL_FILM_LAB.bat**. "
        "Grok Bot can patch in place in the install folder. "
        f"{WORKS_OFFLINE}."
    )


def offline_status_line() -> str:
    mode = "forced" if offline_forced() else "first"
    safe = "on" if safe_mode() else "off"
    return (
        f"Offline-{mode}. Safe mode {safe}. {WORKS_OFFLINE}. "
        "Online optional: Grok / Gemini / ChatGPT / Claude / ElevenLabs."
    )
