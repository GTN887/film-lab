"""One Production Pipeline desk — Enhance | Pose | Animate on the same shot.

Liam UX: the home card opens this workspace, not three separate desks.
The still is uploaded once. Steps share that frame. No re-upload when
you move Enhance → Pose → Animate. Back to Home when you are done.
"""

from __future__ import annotations

STEPS = ("Enhance", "Pose", "Animate")

DEFAULT_STEP = "Enhance"


def step_visibilities(step: str) -> tuple[bool, bool, bool]:
    """Show Enhance / Pose / Animate panels for the selected step."""
    name = (step or DEFAULT_STEP).strip()
    if name not in STEPS:
        name = DEFAULT_STEP
    return (
        name == "Enhance",
        name == "Pose",
        name == "Animate",
    )


def arm_shot(
    still: str | None,
    prompt: str,
    enhanced: str,
) -> tuple[str | None, str | None, str, str]:
    """Copy the pipeline still + prompt onto Motion Desk so Animate can fire.

    Gradio cannot put one Image in two tabs. This is the same shot by path,
    not a second upload.
    """
    path = (still or "").strip() or None
    short = (prompt or "").strip()
    line = (enhanced or "").strip() or short
    return path, path, short, line


def stepper_html(step: str | None = None) -> str:
    """Enhance | Pose | Animate strip. Same shot. No re-upload."""
    current = (step or DEFAULT_STEP).strip()
    if current not in STEPS:
        current = DEFAULT_STEP
    parts: list[str] = ["<ol class='fl-steps fl-pipe-steps'>"]
    for i, label in enumerate(STEPS, start=1):
        if i > 1:
            parts.append("<li class='fl-step-arrow' aria-hidden='true'>→</li>")
        on = " is-on" if label == current else ""
        parts.append(
            f"<li class='fl-step{on}'>"
            f"<span class='fl-step-num'>{i}</span><b>{label}</b></li>"
        )
    parts.append("</ol>")
    parts.append(
        "<p class='fl-step-later'>Same shot. No re-upload. "
        "Back to Home when you are done. Zero credits.</p>"
    )
    return "".join(parts)
