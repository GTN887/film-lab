"""Motion Desk duration lock.

Short presets (5–30s) are one SVD-XT pass at that length.
Long presets (1 min / 2 min) are a multi-shot last-frame chain + stitch.
Zero Film Lab credits. Hardware OOM is not a paywall — shorten or drop res.
"""

from __future__ import annotations

from dataclasses import dataclass

DURATION_PRESETS: tuple[str, ...] = (
    "5s",
    "10s",
    "15s",
    "20s",
    "30s",
    "1 min",
    "2 min",
)
DEFAULT_DURATION_PRESET = "5s"
LONG_PRESETS: frozenset[str] = frozenset({"1 min", "2 min", "60s reel", "120s reel"})


@dataclass(frozen=True)
class DurationPick:
    label: str
    seconds: int
    is_long: bool


def normalize_duration_preset(value: str | None) -> str:
    pick = parse_duration_preset(value)
    if pick.seconds == 60:
        return "1 min"
    if pick.seconds == 120:
        return "2 min"
    label = f"{pick.seconds}s"
    return label if label in DURATION_PRESETS else DEFAULT_DURATION_PRESET


def parse_duration_preset(value: str | int | float | None) -> DurationPick:
    """Map a rail label (or legacy 60s/120s reel) to seconds + chain flag."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = int(value)
        if seconds >= 90:
            return DurationPick("2 min", 120, True)
        if seconds >= 45:
            return DurationPick("1 min", 60, True)
        for preset in (30, 20, 15, 10, 5):
            if seconds >= preset:
                return DurationPick(f"{preset}s", preset, False)
        return DurationPick(DEFAULT_DURATION_PRESET, 5, False)

    text = str(value or DEFAULT_DURATION_PRESET).strip().lower()
    if "120" in text or text in {"2 min", "2min", "2m"}:
        return DurationPick("2 min", 120, True)
    if "60" in text or text in {"1 min", "1min", "1m"}:
        return DurationPick("1 min", 60, True)
    if text.startswith("30"):
        return DurationPick("30s", 30, False)
    if text.startswith("20"):
        return DurationPick("20s", 20, False)
    if text.startswith("15"):
        return DurationPick("15s", 15, False)
    if text.startswith("10"):
        return DurationPick("10s", 10, False)
    if text.startswith("5"):
        return DurationPick("5s", 5, False)
    return DurationPick(DEFAULT_DURATION_PRESET, 5, False)


def is_long_duration(value: str | int | float | None) -> bool:
    return parse_duration_preset(value).is_long
