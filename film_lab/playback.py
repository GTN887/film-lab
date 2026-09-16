"""Playback vs Direct — pause never edits.

Default on Take Board is PLAYBACK: play / pause / scrub only.
Pause freezes the player. It does not open tools, notes, or a rewrite.

DIRECT starts only from the **Mark & Direct** button (helper: Fix this frame).
While Directing, a banner states that Apply / Regenerate will fork a new take.
Exit Direct returns to Playback. The old take stays on the board.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from film_lab.ffmpeg_support import FFmpegError, run_ffmpeg
from film_lab.mark import MarkError, still_from_source
from film_lab.project import IMAGE_SUFFIXES, VIDEO_SUFFIXES, Project

MODE_PLAYBACK = "playback"
MODE_DIRECT = "direct"

DIRECT_BANNER = "Directing — changes will make a new take"
FIX_HELPER = "Fix this frame"
ENTER_LABEL = "Mark & Direct"
EXIT_LABEL = "Exit Direct"

PLAYBACK_HELP = (
    "PLAYBACK — play, pause, and scrub only. Pause freezes the take. "
    "It does not edit. To rewrite a region, press Mark & Direct."
)

DIRECT_HELP = (
    "DIRECT — pause or scrub to study the beat, set the second, "
    "circle / square / lasso the region, write the note, then Apply or Regenerate. "
    "A new take is forked. The old take stays on the board. Exit Direct to watch again."
)


def normalize_mode(raw: Any) -> str:
    text = str(raw or "").strip().lower()
    if text in {MODE_DIRECT, "directing", "mark", "fix"}:
        return MODE_DIRECT
    return MODE_PLAYBACK


def is_direct(mode: Any) -> bool:
    return normalize_mode(mode) == MODE_DIRECT


def banner_html(mode: Any) -> str:
    if not is_direct(mode):
        return ""
    return (
        '<div class="fl-direct-banner" role="status">'
        f"<strong>{DIRECT_BANNER}</strong>"
        "<span>Pause or scrub · mark the region · note · Apply / Regenerate. "
        "The take on the board stays. Exit Direct to play again.</span>"
        "</div>"
    )


def help_text(mode: Any) -> str:
    return DIRECT_HELP if is_direct(mode) else PLAYBACK_HELP


def mark_tools_visible(mode: Any) -> bool:
    return is_direct(mode)


def enter_direct() -> str:
    return MODE_DIRECT


def exit_direct() -> str:
    return MODE_PLAYBACK


def chrome(mode: Any) -> dict[str, Any]:
    """Visibility + copy for Take Board Play / Fix chrome."""
    direct = is_direct(mode)
    return {
        "mode": normalize_mode(mode),
        "banner": banner_html(mode),
        "help": help_text(mode),
        "panel": direct,
        "enter": not direct,
        "exit": direct,
    }


def clip_path(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, dict):
        raw = raw.get("path") or raw.get("name") or raw.get("video") or ""
    text = str(raw or "").strip()
    if not text:
        return ""
    path = Path(text)
    return str(path) if path.is_file() else ""


def pick_gallery_item(items: list[tuple[str, str]], index: Any) -> tuple[str, str] | None:
    if not items:
        return None
    idx = index
    if isinstance(idx, (list, tuple)):
        idx = idx[0] if idx else 0
    try:
        idx = int(idx or 0)
    except (TypeError, ValueError):
        idx = 0
    path, caption = items[max(0, min(idx, len(items) - 1))]
    return path, caption


def freeze_at(project: Project, clip: str | None, seconds: float = 0.0) -> str:
    """Write one frame so Direct can mark it. Pause on the player does not do this."""
    if not clip or not Path(str(clip)).is_file():
        raise FileNotFoundError("Play a take first, then press Mark & Direct.")
    dest = project.root / "direct_frame.png"
    src = Path(str(clip))
    suffix = src.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        still_from_source(src, dest)
        return str(dest)
    if suffix not in VIDEO_SUFFIXES:
        raise FileNotFoundError("Mark & Direct needs a take (mp4) or a still.")
    ss = max(0.0, float(seconds or 0))
    try:
        run_ffmpeg(
            ["-y", "-ss", f"{ss:.3f}", "-i", str(src), "-vframes", "1", str(dest)]
        )
    except (FFmpegError, MarkError) as exc:
        raise FileNotFoundError(f"Could not freeze that second. {exc}") from exc
    if not dest.is_file():
        raise FileNotFoundError("Could not freeze that second.")
    return str(dest)


def freeze_frame(project: Project, clip: str | None) -> str:
    return freeze_at(project, clip, 0.0)


def play_fix_legend_html() -> str:
    return (
        '<div class="fl-play-fix" role="group" aria-label="Play versus Fix">'
        '<div class="fl-play-fix-card is-play">'
        '<span class="fl-play-fix-kicker">Play</span>'
        "<strong>Playback</strong>"
        "<p>Click a take. Play, pause, scrub. Pause freezes. It does not edit.</p>"
        "</div>"
        '<div class="fl-play-fix-card is-fix">'
        '<span class="fl-play-fix-kicker">Fix</span>'
        f"<strong>{ENTER_LABEL}</strong>"
        f"<p>{FIX_HELPER}. {DIRECT_BANNER}.</p>"
        "</div>"
        "</div>"
    )


def playback_copy() -> str:
    return (
        f"**{ENTER_LABEL}** · {FIX_HELPER}. Default is Playback — pause never edits. "
        f"Direct banner: *{DIRECT_BANNER}*. Exit Direct returns to play; the old take stays."
    )
