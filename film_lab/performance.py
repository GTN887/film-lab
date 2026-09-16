"""Micro-expressions, full-body behavior, and prop / environment actions.

Wired through Character Bible, Director Note, Pose, Voice, Writing Studio,
Mark & Direct, and World Note. Regular / story actions are everyday
(pick up a book, swallow, glance). Intimate routes stay adult 18+ only.
Not a hosted face-puppet. Zero credits.
"""

from __future__ import annotations

NONE = "none"

MICRO_EXPRESSIONS: tuple[str, ...] = (
    NONE,
    "held look",
    "soft glance",
    "brow flick",
    "eye dart",
    "swallow",
    "lip press",
    "half smile",
    "flinch",
    "blink hold",
    "jaw set",
    "tear well",
    "nostril flare",
    "smirk then drop",
)

BEHAVIORS: tuple[str, ...] = (
    NONE,
    "still breath",
    "weight shift",
    "hands live",
    "fidget then stop",
    "reach then hold",
    "walk then settle",
    "listen with the body",
    "cover then uncover",
    "lean in / pull back",
    "pick up then pause",
    "put down carefully",
)

PROP_ACTIONS: tuple[str, ...] = (
    NONE,
    "pick up book",
    "put down book",
    "open book",
    "pick up glass",
    "set glass down",
    "open door",
    "close door",
    "switch lamp",
    "pick up phone",
    "set phone down",
    "fold cloth",
    "move chair",
)

DEFAULT_MICRO = NONE
DEFAULT_BEHAVIOR = NONE
DEFAULT_PROP = NONE

PERFORMANCE_HELP = (
    "**Micro-expression** is the face (glance, swallow, brow). "
    "**Behavior** is the whole body. **Prop action** is the room "
    "(pick up book from the still or a paused frame). "
    "Director Note / Pose / Character Bible / Voice / Writing share the same catalog. "
    "Mark & Direct or World Note for the book / glass / door. "
    "Regular / story only for under-18 roles. Intimate / explicit: adult 18+ ONLY. "
    "Zero credits."
)


def normalize_choice(raw: str | None, allowed: tuple[str, ...], default: str = NONE) -> str:
    text = (raw or "").strip()
    if text in allowed:
        return text
    low = text.lower()
    for item in allowed:
        if item.lower() == low:
            return item
    return default


def active(value: str | None) -> str:
    text = (value or "").strip()
    if not text or text.lower() == NONE:
        return ""
    return text


def compose_performance(
    micro: str | None = "",
    behavior: str | None = "",
    *,
    extra: str = "",
) -> str:
    bits = [b for b in (active(micro), active(behavior), (extra or "").strip()) if b]
    if not bits:
        return ""
    return "performance: " + "; ".join(bits)


def compose_prop_action(action: str | None = "", *, extra: str = "") -> str:
    bits = [b for b in (active(action), (extra or "").strip()) if b]
    if not bits:
        return ""
    return "prop action: " + "; ".join(bits)


def compose_writing_line(
    micro: str | None = "",
    behavior: str | None = "",
    prop: str | None = "",
) -> str:
    parts = [p for p in (compose_performance(micro, behavior), compose_prop_action(prop)) if p]
    return " ".join(parts)


def merge_prop_note(note: str | None, action: str | None) -> str:
    """Fill a Mark region note from the prop-action picker when the box is empty."""
    text = (note or "").strip()
    prop = active(action)
    if text and prop and prop.lower() not in text.lower():
        return f"{prop}. {text}"
    return text or prop


def fold_micro_into_breath(breath: str | None, micro: str | None) -> str:
    face = active(micro)
    current = (breath or "").strip()
    if not face:
        return current
    if face.lower() in current.lower():
        return current
    if not current:
        return f"micro-expression {face}"
    return f"{current}; micro-expression {face}"
