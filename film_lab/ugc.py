"""UGC Ads Desk — local talking-head / product-ad workflow.

Mirrors a common creator-ad *job list* (hook → problem → product → proof → CTA),
not a paid hosted UGC model. No third-party brand names. Zero Film Lab credits.
Adults 18+ only. Motion runs on local AMD img2vid. Ken Burns is Advanced timing only.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from film_lab.characters import cast_prompt_block, load_selected_characters, parse_age_years
from film_lab.llm import (
    DEFAULT_PROVIDER,
    NO_CREDITS,
    PROVIDER_CLAUDE,
    PROVIDER_GEMINI,
    PROVIDER_GROK,
    PROVIDER_LOCAL,
    PROVIDER_OPENAI,
    complete_anthropic,
    complete_gemini,
    complete_openai,
    complete_xai,
    normalize_provider,
)
from film_lab.project import Project
from film_lab.shot_card import ShotCard, new_shot_id
from film_lab.util import new_id

UGC_ASPECT = "9:16"
UGC_TARGET_SECONDS = (8.0, 15.0)


@dataclass
class UgcBeat:
    key: str
    label: str
    duration: float
    camera_move: str
    body_notes: str
    line: str = ""


@dataclass
class UgcBrief:
    id: str = ""
    product_name: str = ""
    product_notes: str = ""
    product_still: str = ""
    creator_name: str = ""
    creator_look: str = ""
    creator_age: int = 28
    hook: str = ""
    problem: str = ""
    product: str = ""
    proof: str = ""
    cta: str = ""
    provider: str = DEFAULT_PROVIDER
    plan: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = new_id()
        years = parse_age_years(self.creator_age)
        self.creator_age = years if years is not None else 28
        self.provider = normalize_provider(self.provider)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> UgcBrief:
        if not isinstance(data, dict):
            return cls()
        known = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        return cls(**known)

    def script_text(self) -> str:
        return "\n\n".join(
            [
                f"HOOK: {self.hook}".strip(),
                f"PROBLEM: {self.problem}".strip(),
                f"PRODUCT: {self.product}".strip(),
                f"PROOF: {self.proof}".strip(),
                f"CTA: {self.cta}".strip(),
            ]
        )


class UgcError(ValueError):
    """Adult-age or brief errors."""


def assert_ugc_adult(age) -> int:
    years = parse_age_years(age)
    if years is None:
        raise UgcError("Creator Age (years) is required. Adults 18+ only.")
    if years < 18:
        raise UgcError("Creators must be adults 18+. No under-18 or teen-appearing talent.")
    return years


def ugc_dir(project: Project) -> Path:
    path = project.root / "ugc"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_brief(project: Project, brief: UgcBrief) -> Path:
    assert_ugc_adult(brief.creator_age)
    brief.id = brief.id or new_id()
    path = ugc_dir(project) / f"{brief.id}.json"
    path.write_text(json.dumps(brief.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_brief(project: Project, brief_id: str) -> UgcBrief:
    path = ugc_dir(project) / f"{brief_id}.json"
    return UgcBrief.from_dict(json.loads(path.read_text(encoding="utf-8")))


def list_briefs(project: Project) -> list[UgcBrief]:
    found: list[UgcBrief] = []
    for path in sorted(ugc_dir(project).glob("*.json")):
        try:
            found.append(UgcBrief.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return found


def brief_choices(project: Project) -> list[str]:
    return [f"{b.id} — {b.product_name or 'untitled ad'}" for b in list_briefs(project)]


def local_script(brief: UgcBrief) -> UgcBrief:
    """Always-on template. No network. Sounds like a handheld creator take."""
    product = (brief.product_name or "this").strip()
    notes = (brief.product_notes or "it actually works").strip()
    name = (brief.creator_name or "I").strip()
    brief.hook = brief.hook or f"Okay wait — {name.lower() if name != 'I' else 'I'} need to show you {product} before I talk myself out of it."
    brief.problem = brief.problem or (
        f"I kept buying the wrong thing and pretending it was fine. "
        f"The mess was still there in the morning."
    )
    brief.product = brief.product or (
        f"This is {product}. {notes}. I'm not reading a box at you — this is the one on my table."
    )
    brief.proof = brief.proof or (
        "I used it the way a tired adult actually uses it. Same room. Same light. It held up."
    )
    brief.cta = brief.cta or (
        f"If that's your problem too, start with {product}. Link's where you'd expect it. I'm going back to my night."
    )
    brief.provider = PROVIDER_LOCAL
    return brief


def _parse_labeled(text: str) -> dict[str, str]:
    keys = ("HOOK", "PROBLEM", "PRODUCT", "PROOF", "CTA")
    found = {k.lower(): "" for k in keys}
    current = None
    chunks: dict[str, list[str]] = {k.lower(): [] for k in keys}
    for raw in (text or "").splitlines():
        line = raw.strip()
        match = re.match(r"^(HOOK|PROBLEM|PRODUCT|PROOF|CTA)\s*[:\-—]\s*(.*)$", line, re.I)
        if match:
            current = match.group(1).upper()
            rest = match.group(2).strip()
            if rest:
                chunks[current.lower()].append(rest)
            continue
        if current and line:
            chunks[current.lower()].append(line)
    for key in found:
        found[key] = " ".join(chunks[key]).strip()
    return found


def apply_cast_to_brief(project: Project, brief: UgcBrief) -> UgcBrief:
    """Fill creator look from the active bible when the name matches."""
    ids = list(project.active_cast or ["alison", "bradley"])
    profiles = load_selected_characters(project, ids)
    name = (brief.creator_name or "").strip().lower()
    for profile in profiles:
        if name and profile.name.lower() == name:
            if not (brief.creator_look or "").strip():
                brief.creator_look = profile.injection_line()
            if parse_age_years(brief.creator_age) is None:
                brief.creator_age = profile.age_years or 28
            break
    if not (brief.creator_look or "").strip() and profiles:
        brief.creator_look = profiles[0].injection_line()
    return brief


def generate_script(brief: UgcBrief, *, provider: str | None = None, project: Project | None = None) -> UgcBrief:
    """Local templates always work. Optional Grok / Gemini / ChatGPT / Claude use keys you own."""
    if project is not None:
        brief = apply_cast_to_brief(project, brief)
    assert_ugc_adult(brief.creator_age)
    provider = normalize_provider(provider or brief.provider)
    brief.provider = provider
    if provider == PROVIDER_LOCAL:
        return local_script(brief)

    messages = [
        {
            "role": "system",
            "content": (
                "You write a vertical handheld creator ad for a private local film desk. "
                "Adults 18+ only. No minors, no teen-appearing talent. "
                "Return exactly five labeled lines: HOOK, PROBLEM, PRODUCT, PROOF, CTA. "
                "First-person, spoken, 8–15 seconds total. No hashtags, no brand of an AI video company. "
                + NO_CREDITS
            ),
        },
        {
            "role": "user",
            "content": (
                f"Product: {brief.product_name}\n"
                f"Notes: {brief.product_notes}\n"
                f"Creator: {brief.creator_name}, {brief.creator_age}, {brief.creator_look}\n"
                + (
                    f"Cast lock:\n{cast_prompt_block(project)}\n"
                    if project is not None
                    else ""
                )
                + "Write the five beats. Adults 18+ only."
            ),
        },
    ]
    try:
        if provider == PROVIDER_GEMINI:
            raw = complete_gemini(messages, temperature=0.8)
        elif provider == PROVIDER_GROK:
            raw = complete_xai(messages, temperature=0.8)
        elif provider == PROVIDER_OPENAI:
            raw = complete_openai(messages, temperature=0.8)
        elif provider == PROVIDER_CLAUDE:
            raw = complete_anthropic(messages, temperature=0.8)
        else:
            return local_script(brief)
    except RuntimeError:
        filled = local_script(brief)
        filled.provider = PROVIDER_LOCAL
        return filled
    parsed = _parse_labeled(raw)
    brief.hook = parsed["hook"] or brief.hook
    brief.problem = parsed["problem"] or brief.problem
    brief.product = parsed["product"] or brief.product
    brief.proof = parsed["proof"] or brief.proof
    brief.cta = parsed["cta"] or brief.cta
    if not brief.hook:
        return local_script(brief)
    return brief


def build_shot_plan(brief: UgcBrief) -> list[UgcBeat]:
    """Five 9:16 beats that stitch to ~12s. Each clip stays 6GB-friendly (2–3s)."""
    assert_ugc_adult(brief.creator_age)
    filled = brief if brief.hook else local_script(brief)
    beats = [
        UgcBeat("hook", "Hook", 2.0, "OTS", "handheld, look to lens, start talking", filled.hook),
        UgcBeat("problem", "Problem", 2.5, "slow push-in", "weight in the face, small head shake", filled.problem),
        UgcBeat("product", "Product", 3.0, "high", "hands in frame, product readable", filled.product),
        UgcBeat("proof", "Proof", 2.5, "pan R", "use it, no demo-smile", filled.proof),
        UgcBeat("cta", "CTA", 2.5, "pull-out", "back to lens, end the take", filled.cta),
    ]
    total = sum(b.duration for b in beats)
    assert UGC_TARGET_SECONDS[0] <= total <= UGC_TARGET_SECONDS[1]
    brief.plan = [asdict(b) for b in beats]
    return beats


def push_plan_to_shots(project: Project, brief: UgcBrief) -> list[ShotCard]:
    beats = build_shot_plan(brief)
    still = brief.product_still or None
    if still and not project.resolve_still(still):
        still = None
    created: list[ShotCard] = []
    for beat in beats:
        shot = ShotCard(
            id=new_shot_id(),
            name=f"{brief.product_name or 'UGC'} · {beat.label}",
            start_frame=still,
            duration=beat.duration,
            aspect_ratio=UGC_ASPECT,
            camera_move=beat.camera_move,
            subject_motion_strength=0.4,
            body_motion_notes=beat.body_notes,
            director_intent=beat.line,
            lighting="phone light / practical room",
            character_ids=list(project.active_cast or ["alison", "bradley"]),
            face_lock_strength=project.face_lock_strength,
        )
        project.save_shot(shot)
        created.append(shot)
    brief.plan = [asdict(b) for b in beats]
    save_brief(project, brief)
    return created


def plan_table(beats: list[UgcBeat]) -> list[list[str]]:
    return [
        [b.label, f"{b.duration:.1f}s", UGC_ASPECT, b.camera_move, b.line[:80]]
        for b in beats
    ]
