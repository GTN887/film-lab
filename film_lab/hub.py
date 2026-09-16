"""Film Lab home hub — studio jobs, not a hosted product clone.

A public AI video homepage is a UX *jobs* reference only (card grid, shelves, lot).
This module uses original Film Lab names. No third-party brand, logo, or model names.
Zero credits. Local folders only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from film_lab.project import Project, default_data_root


@dataclass(frozen=True)
class HubCard:
    tab_id: str
    title: str
    kicker: str
    blurb: str
    button: str
    index: str = "01"
    tone: str = "#2a1848"


@dataclass(frozen=True)
class EffectLook:
    label: str
    blurb: str
    lut: str
    vfx: str
    strength: float


HUB_CARDS: tuple[HubCard, ...] = (
    HubCard(
        tab_id="pipeline",
        title="AI Production Pipeline",
        kicker="Enhance · Pose · Animate",
        blurb=(
            "One shot, one desk. Enhance, pose, then animate the same still — "
            "no re-upload. Any still (people, products, cans, posters). "
            "Back to Home when you are done."
        ),
        button="Open Pipeline",
        index="01",
        tone="#4a2a78",
    ),
    HubCard(
        tab_id="still",
        title="Still Desk",
        kicker="Frames",
        blurb="Ingest rehearsal stills. Notes stay in this folder. Adults 18+ only.",
        button="Open Still Desk",
        index="02",
        tone="#1c2a48",
    ),
    HubCard(
        tab_id="takes",
        title="Take Board",
        kicker="Variations",
        blurb="Play a take. Pause, click the person, Dream about… Linked child scenes under that sleeper. Mark & Direct forks a new take.",
        button="Open Take Board",
        index="03",
        tone="#3a2468",
    ),
    HubCard(
        tab_id="bridge",
        title="Director Bridge",
        kicker="Local tools",
        blurb="ChatGPT, Claude, Grok Bot, Cursor, Claude Code, OpenClaw, Hermes — MCP / CLI. Not a paid plugin.",
        button="Open Director Bridge",
        index="04",
        tone="#243048",
    ),
    HubCard(
        tab_id="cinema",
        title="Cinema Desk",
        kicker="Reel",
        blurb="Auto-stitch the extend sequence with crossfades into one MP4. Grade and assemble. Nothing leaves the disk.",
        button="Open Cinema Desk",
        index="05",
        tone="#322058",
    ),
    HubCard(
        tab_id="brain",
        title="Director Brain",
        kicker="Pages",
        blurb="Local writing pages always. Import PDF, Word, PowerPoint, Excel; Fuse drafts; Export what you type. Dream beat sheet, then Plan shots to Motion. Optional Grok, Gemini, or ChatGPT with keys you own.",
        button="Open Director Brain",
        index="06",
        tone="#3a2860",
    ),
    HubCard(
        tab_id="ugc",
        title="UGC Ads Desk",
        kicker="Product ads",
        blurb="Product ref + avatar + prompt → Enhance → Animate. Local still. Mark & Direct the take.",
        button="Open UGC Ads Desk",
        index="07",
        tone="#1c2848",
    ),
    HubCard(
        tab_id="characters",
        title="Character Consistency",
        kicker="Bible + face lock",
        blurb="Character sheet + Word/PDF bio import/export + micro-expressions + Family Genetics (Regular / story kids). InstantID/FaceID stubs, Pose Desk, Environment/Set lock.",
        button="Open Character Consistency",
        index="08",
        tone="#3a2460",
    ),
    HubCard(
        tab_id="lighting",
        title="Lighting Desk",
        kicker="Practicals + chips",
        blurb="Studio / natural plus cinematic pack (anamorphic night, teal & orange, prestige-TV night…). Pick one or skip.",
        button="Open Lighting Desk",
        index="09",
        tone="#3a2080",
    ),
    HubCard(
        tab_id="score",
        title="Score Desk",
        kicker="Cue + mux",
        blurb="Import music first. Local synth always. MusicGen-small optional later. Cinema muxes the bed.",
        button="Open Score Desk",
        index="10",
        tone="#1c3850",
    ),
    HubCard(
        tab_id="voice",
        title="Voice Desk",
        kicker="Acting, not TTS",
        blurb="Per-character bible voices. Micro-expression folds into breath. Tagged lines route to Alison / Bradley. Local TTS or import.",
        button="Open Voice Desk",
        index="11",
        tone="#2a1858",
    ),
    HubCard(
        tab_id="effects",
        title="Effects Desk",
        kicker="Preset shelf",
        blurb="Character still, optional location and product, descriptive motion presets. Local Comfy. Zero credits.",
        button="Open Effects Desk",
        index="12",
        tone="#322060",
    ),
    HubCard(
        tab_id="pose",
        title="Pose Desk",
        kicker="Still-first pose",
        blurb="OpenPose-style body / hands / face + micro-expression / behavior on the still. Face lock stays. Then Motion Animate.",
        button="Open Pose Desk",
        index="13",
        tone="#2a2058",
    ),
    HubCard(
        tab_id="set",
        title="3D Set Desk",
        kicker="Orbit · aerial",
        blurb="LOCKED Environment from photo plus Pointer / Go-to: Actor A walks to a bathroom or locked room. Take lands on Take Board. Stored in sets/stills/takes. Not a 3D engine.",
        button="Open 3D Set Desk",
        index="14",
        tone="#1c3858",
    ),
    HubCard(
        tab_id="mark",
        title="Mark & Direct",
        kicker="Region edit",
        blurb="On Take Board: Mark & Direct · Fix this frame. Mark the head to Enter dream. Circle a book, pick up book, Apply. Regenerate forks a new take.",
        button="Open Mark & Direct",
        index="15",
        tone="#2a1848",
    ),
)

EFFECT_LOOKS: tuple[EffectLook, ...] = (
    EffectLook("Warm lamp hold", "Amber bedroom print", "warm_lamp.cube", "grain", 0.35),
    EffectLook("Cool moonlight", "Blue shadow grade", "cool_shadow.cube", "letterbox", 0.45),
    EffectLook("Soft print fade", "Gentle in/out", "soft_print.cube", "fade", 0.5),
    EffectLook("Afterglow bloom", "Lamp bloom on skin", "warm_lamp.cube", "bloom", 0.4),
    EffectLook("Street wet night", "Cool grade, grain", "cool_shadow.cube", "grain", 0.55),
    EffectLook("Thin-wall hush", "Lived-in print, slow", "soft_print.cube", "speed", 0.85),
)

# Strings that must never appear in hub UI copy.
FORBIDDEN_BRANDS: tuple[str, ...] = (
    "higgsfield",
    "seedance",
    "nano banana",
    "genjutsu",
    "astra",
    "cinema studio 4.0",
    "supercomputer",
    "gpt-6",
    "arcads",
    "sora",
    "kling",
)


def hub_chrome_html() -> str:
    return (
        "<div class='fl-chrome'>"
        "<div class='fl-mark'>FILM LAB</div>"
        "<div class='fl-pills'>"
        "<span class='fl-pill fl-pill-hot'>LOCAL ONLY</span>"
        "<span class='fl-pill fl-pill-hot'>OFFLINE</span>"
        "<span class='fl-pill'>ONLINE OPTIONAL</span>"
        "<span class='fl-pill'>FILM SCHOOL</span>"
        "<span class='fl-pill'>ADULTS 18+</span>"
        "<span class='fl-pill'>NO CREDITS</span>"
        "</div>"
        "</div>"
    )


def hub_tile_html(card: HubCard) -> str:
    return (
        "<article class='hub-card'>"
        f"<div class='hub-poster' style='--tone:{_esc(card.tone)}'>"
        f"<span class='hub-index'>{_esc(card.index)}</span>"
        "</div>"
        f"<div class='hub-kicker'>{_esc(card.kicker)}</div>"
        f"<h3>{_esc(card.title)}</h3>"
        f"<p>{_esc(card.blurb)}</p>"
        "</article>"
    )


def hub_cards_html() -> str:
    return "<div class='hub-grid'>" + "".join(hub_tile_html(card) for card in HUB_CARDS) + "</div>"


def hub_hero_html() -> str:
    return (
        "<header class='film-lab-hero'>"
        "<p class='hero-kicker'>Private film school on this machine</p>"
        "<h1>FILM LAB</h1>"
        "<p class='hero-lede'>A local purple studio. Still to motion, preset effects, pages, and a reel — "
        "then lighting, score, voice, and a 3D set. Regular vs 18+ Explicit is a filming-mode toggle — "
        "one Film Lab theme, not two apps. Not a subscription.</p>"
        "</header>"
    )


def craft_shelf_html() -> str:
    return (
        "<div class='craft-head'>"
        "<p class='section-kicker'>Craft desks</p>"
        "<h2>LIGHT · SCORE · VOICE · EFFECTS · POSE · SET · MARK</h2>"
        "<p class='section-lede'>School techniques on this machine. Zero credits. No hosted shops.</p>"
        "</div>"
    )


def looks_shelf_html() -> str:
    chips = "".join(
        f"<span class='look-chip'><b>{_esc(look.label)}</b>{_esc(look.blurb)}</span>"
        for look in EFFECT_LOOKS
    )
    return (
        "<div class='looks-head'>"
        "<p class='section-kicker'>Looks shelf</p>"
        "<h2>LOCAL FINISH</h2>"
        "<p class='section-lede'>LUT + VFX on this machine. Not a preset shop.</p>"
        f"<div class='look-chips'>{chips}</div>"
        "</div>"
    )


def effect_labels() -> list[str]:
    return [look.label for look in EFFECT_LOOKS]


def effect_by_label(label: str) -> EffectLook:
    for look in EFFECT_LOOKS:
        if look.label == label:
            return look
    return EFFECT_LOOKS[0]


def local_lot_markdown(*, data_root: Path | None = None) -> str:
    """Plain-text lot list (tests + fallback)."""
    cards = _lot_cards(data_root=data_root)
    lines = [
        "### Local lot",
        "Projects on **this machine** only. Not a public community feed. Nothing is uploaded.",
        "",
    ]
    if not cards:
        lines.append("_No projects yet. Create one above or import the studio bundle._")
        return "\n".join(lines)
    for name, stills, shots, clips, desc in cards:
        lines.append(f"- **{name}** — {stills} still(s), {shots} shot(s), {clips} clip(s). {desc}")
    return "\n".join(lines)


def local_lot_html(*, data_root: Path | None = None) -> str:
    """Poster-style project strip. Local folders only — not a community feed."""
    cards = _lot_cards(data_root=data_root)
    head = (
        "<div class='looks-head'>"
        "<p class='section-kicker'>Local lot</p>"
        "<h2>ON THIS MACHINE</h2>"
        "<p class='section-lede'>Private film-school folders. Nothing is uploaded. Not a public feed.</p>"
        "</div>"
    )
    if not cards:
        return head + "<p class='lot-empty'>No projects yet. Create a folder above or import the studio bundle.</p>"
    tiles = "".join(
        (
            "<div class='lot-card'>"
            f"<b>{_esc(name)}</b>"
            f"<span>{stills} still(s) · {shots} shot(s) · {clips} clip(s)<br>{_esc(desc)}</span>"
            "</div>"
        )
        for name, stills, shots, clips, desc in cards
    )
    return head + f"<div class='lot-grid'>{tiles}</div>"


def _lot_cards(*, data_root: Path | None = None) -> list[tuple[str, int, int, int, str]]:
    root = data_root or default_data_root()
    names = Project.list_names(data_root=root)
    found: list[tuple[str, int, int, int, str]] = []
    for name in names:
        try:
            project = Project.load(name, data_root=root)
        except (OSError, ValueError, FileNotFoundError):
            continue
        stills = len(project.list_stills())
        shots = len(project.list_shots())
        clips = sum(1 for c in project.load_gallery() if Path(c.path).is_file())
        desc = (project.description or "Private film-school folder").strip()
        found.append((project.name, stills, shots, clips, desc))
    return found


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
