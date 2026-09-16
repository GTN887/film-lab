"""Unified Motion Desk feed — still → user command → enhanced paragraph → video.

Mirrors the grok.com/imagine chat rhythm without copying that product:
short command, visible expansion, then the clip under the text.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pathlib import Path

from film_lab.animate_ux import rewrite_cloud_safety


@dataclass
class FeedTurn:
    user_text: str
    enhanced_paragraph: str
    ref_name: str = ""
    created: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))

    def to_dict(self) -> dict[str, str]:
        return {
            "user_text": self.user_text,
            "enhanced_paragraph": self.enhanced_paragraph,
            "ref_name": self.ref_name,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> FeedTurn | None:
        if not isinstance(raw, dict):
            return None
        user = str(raw.get("user_text") or "").strip()
        para = str(raw.get("enhanced_paragraph") or "").strip()
        if not user and not para:
            return None
        return cls(
            user_text=user,
            enhanced_paragraph=para,
            ref_name=str(raw.get("ref_name") or ""),
            created=str(raw.get("created") or ""),
        )


def _esc(text: str) -> str:
    return html.escape(rewrite_cloud_safety(text or ""), quote=True)


def render_feed(turns: list[FeedTurn | dict[str, Any]] | None, *, generating: bool = False) -> str:
    """Safe HTML for the scrolling imagine feed."""
    parsed: list[FeedTurn] = []
    for item in turns or []:
        turn = item if isinstance(item, FeedTurn) else FeedTurn.from_dict(item)
        if turn:
            parsed.append(turn)
    if not parsed:
        return (
            '<div class="fl-feed" role="log" aria-live="polite">'
            '<div class="fl-feed-empty">'
            "<p>Attach a still with <strong>Add Prompt</strong>, type a short command, "
            "then <strong>Send</strong>. Film Lab expands it into a cinematic paragraph "
            "here — continuity, lighting on skin, micro-motions — then the clip appears underneath.</p>"
            "</div></div>"
        )

    blocks: list[str] = ['<div class="fl-feed" role="log" aria-live="polite">']
    last = len(parsed) - 1
    for i, turn in enumerate(parsed):
        live = " fl-feed-turn-live" if i == last and generating else ""
        ref = (
            f'<div class="fl-feed-ref">Ref attached · {_esc(turn.ref_name)}</div>'
            if turn.ref_name
            else ""
        )
        user = _esc(turn.user_text)
        para = _esc(turn.enhanced_paragraph)
        blocks.append(
            f'<article class="fl-feed-turn{live}">'
            f'<div class="fl-feed-user"><span class="fl-feed-role">You</span>'
            f"<p>{user}</p>{ref}</div>"
            f'<div class="fl-feed-enhance"><span class="fl-feed-role">Prompt Enhancement</span>'
            f'<p class="fl-feed-paragraph">{para}</p></div>'
            "</article>"
        )
    if generating:
        blocks.append(
            '<div class="fl-feed-stage-note">Clip generating under this paragraph — watch the overlay.</div>'
        )
    blocks.append("</div>")
    return "".join(blocks)


def ref_chip_html(path: str | None) -> str:
    """Composer chip after Add Prompt attaches the still."""
    text = (path or "").strip()
    if not text:
        return (
            '<div class="fl-ref-chip fl-ref-chip-empty">'
            "No still attached — Add Prompt on the frame above."
            "</div>"
        )
    name = Path(text).name
    return f'<div class="fl-ref-chip">Ref attached · {_esc(name)}</div>'


def append_turn(
    history: list[dict[str, Any]] | None,
    *,
    user_text: str,
    paragraph: str,
    ref_name: str = "",
    keep: int = 8,
) -> list[dict[str, Any]]:
    turns = [t for t in (history or []) if isinstance(t, dict)]
    turns.append(
        FeedTurn(
            user_text=user_text.strip(),
            enhanced_paragraph=paragraph.strip(),
            ref_name=ref_name,
        ).to_dict()
    )
    return turns[-keep:]
