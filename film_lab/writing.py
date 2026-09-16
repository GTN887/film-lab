"""Writing Studio: local pages plus optional Grok / Gemini / ChatGPT / Claude.

Original Film Lab desk. Not a scrape of any proprietary chat UI.
Local templates always write pages on this machine. Cloud keys are yours.
Import + Fuse (Grok online + Gemini, or PDF / Word / PowerPoint / Excel / text)
is local — see write_fuse.py and office.py. Export typed pages as Word, PDF,
PowerPoint, Excel, or plain text.
There is no Film Lab credit meter, subscription, or quota.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from film_lab.characters import (
    CharacterError,
    assert_adult_cast,
    list_characters,
    load_selected_characters,
    resolved_living,
)
from film_lab.constants import EXPLICIT_INTIMACY, INTIMACY_MODES
from film_lab.genres import (
    DEFAULT_PRIMARY,
    check_genre_intimacy,
    genre_line,
    genre_prompt_block,
    parse_custom_tags,
    youth_shelf_active,
)
from film_lab.intensity import (
    DEFAULT_INTENSITY,
    DEFAULT_PRESET,
    INTENSITY_PRESETS,
    clamp_content_intensity,
    intensity_prompt_block,
    nearest_intensity_preset,
)
from film_lab.intimacy import intimacy_writing_block
from film_lab.llm import (
    DEFAULT_DUAL_ROLES,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_XAI_BASE,
    DEFAULT_XAI_MODEL,
    LEAVE_XAI,
    NO_CREDITS,
    PROVIDER_LOCAL,
    PROVIDERS,
    get_xai_key,
    leave_notice,
    normalize_dual_roles,
    normalize_provider,
    probe_writing_api as probe_providers,
    run_generation,
    xai_model,
)
from film_lab.living import LivingBrief, living_prompt_block
from film_lab.senses import (
    DEFAULT_SENSES,
    SensoryBrief,
    clamp_intensity,
    parse_enabled_senses,
    sensory_prompt_block,
    sensory_system_addendum,
)
from film_lab.project import Project
from film_lab.script import DialogueLine, Scene, load_scene, save_scene
from film_lab.util import new_id, read_json, slugify, utc_now, write_json

WRITING_MODES = (
    "screenplay",
    "novel",
    "book_to_screenplay",
    "roleplay",
    "director_rewrite",
)

ROLEPLAY_SPEAKERS = ("Alison", "Bradley", "Director")

API_LEAVE_NOTICE = "Writing Studio API calls leave this machine to the selected provider."
OFFLINE_NOTICE = (
    "Set FILM_LAB_XAI_API_KEY (or XAI_API_KEY) and/or FILM_LAB_GEMINI_API_KEY "
    "(or GEMINI_API_KEY / GOOGLE_API_KEY) and/or FILM_LAB_OPENAI_API_KEY "
    "(or OPENAI_API_KEY) and/or FILM_LAB_ANTHROPIC_API_KEY "
    "(or ANTHROPIC_API_KEY) for live generation; "
    "or paste drafts from chat. Import + Fuse merges pasted or uploaded pages locally "
    "(no API). Prompt pack below stays local until you generate. "
    "Film Lab has no credits, quotas, or paywalls."
)


class WritingError(RuntimeError):
    """Draft or API failure."""


@dataclass
class ChatTurn:
    role: str  # user | assistant | system
    speaker: str = ""
    content: str = ""

    def to_api(self) -> dict[str, str]:
        prefix = f"{self.speaker}: " if self.speaker and self.role != "system" else ""
        return {"role": self.role, "content": prefix + self.content}


@dataclass
class WritingDraft:
    id: str
    mode: str = "screenplay"
    provider: str = DEFAULT_PROVIDER
    api_model: str = ""
    dual_roles: str = DEFAULT_DUAL_ROLES
    dual_spine: str = ""
    title: str = "Untitled draft"
    scene_id: str | None = None
    character_ids: list[str] = field(default_factory=lambda: ["alison", "bradley"])
    source: str = ""
    notes: str = ""
    tone: str = ""
    pacing: str = ""
    intimacy_mode: str = "covered sheets"
    intensity_preset: str = DEFAULT_PRESET
    content_intensity: float = DEFAULT_INTENSITY
    roleplay_speaker: str = "Director"
    primary_genre: str = DEFAULT_PRIMARY
    secondary_genres: list[str] = field(default_factory=list)
    custom_genre_tags: list[str] = field(default_factory=list)
    tropes_checklist: str = ""
    primary_emotion: str = "tenderness"
    secondary_emotion: str = "longing"
    emotion_intensity: float = 0.55
    inner_state: str = ""
    outer_behavior: str = ""
    relationship_temp: str = "newlywed tenderness"
    enabled_senses: list[str] = field(default_factory=lambda: list(DEFAULT_SENSES))
    touch_notes: str = ""
    smell_notes: str = ""
    taste_notes: str = ""
    hearing_notes: str = ""
    sight_notes: str = ""
    sensory_pass: bool = False
    env_location: str = "INT. BEDROOM - NIGHT"
    env_time: str = "night"
    env_weather: str = "clear"
    env_light: str = "warm lamp"
    env_ambient: str = ""
    env_blocking: str = ""
    env_props: str = ""
    living: dict[str, Any] = field(default_factory=dict)
    living_override: bool = False
    body: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    turns: list[ChatTurn] = field(default_factory=list)
    used_api: bool = False
    model: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        parsed: list[ChatTurn] = []
        for turn in self.turns:
            if isinstance(turn, ChatTurn):
                parsed.append(turn)
            elif isinstance(turn, dict):
                parsed.append(
                    ChatTurn(
                        role=str(turn.get("role", "user")),
                        speaker=str(turn.get("speaker", "")),
                        content=str(turn.get("content", "")),
                    )
                )
        self.turns = parsed
        if self.mode not in WRITING_MODES:
            self.mode = "screenplay"
        self.provider = normalize_provider(self.provider)
        self.dual_roles = normalize_dual_roles(self.dual_roles)
        if self.intimacy_mode not in INTIMACY_MODES:
            self.intimacy_mode = "covered sheets"
        self.content_intensity = clamp_content_intensity(self.content_intensity)
        if self.intensity_preset not in INTENSITY_PRESETS:
            self.intensity_preset = nearest_intensity_preset(self.content_intensity)
        if self.scene_id == "":
            self.scene_id = None
        if not (self.primary_genre or "").strip():
            self.primary_genre = DEFAULT_PRIMARY
        if isinstance(self.custom_genre_tags, str):
            self.custom_genre_tags = parse_custom_tags(self.custom_genre_tags)
        self.secondary_genres = [s for s in (self.secondary_genres or []) if s]
        self.emotion_intensity = clamp_intensity(self.emotion_intensity)
        self.enabled_senses = parse_enabled_senses(self.enabled_senses) or list(DEFAULT_SENSES)
        self.sensory_pass = bool(self.sensory_pass)
        if not isinstance(self.living, dict):
            self.living = {}
        self.living_override = bool(self.living_override)

    def living_brief(self) -> LivingBrief:
        brief = LivingBrief.from_dict(self.living)
        brief.override = self.living_override
        return brief

    def set_living(self, brief: LivingBrief) -> None:
        self.living_override = bool(brief.override)
        payload = brief.to_dict()
        payload["override"] = self.living_override
        self.living = payload

    def sensory_brief(self) -> SensoryBrief:
        return SensoryBrief(
            primary_emotion=self.primary_emotion,
            secondary_emotion=self.secondary_emotion,
            intensity=self.emotion_intensity,
            inner_state=self.inner_state,
            outer_behavior=self.outer_behavior,
            relationship_temp=self.relationship_temp,
            enabled_senses=list(self.enabled_senses),
            touch_notes=self.touch_notes,
            smell_notes=self.smell_notes,
            taste_notes=self.taste_notes,
            hearing_notes=self.hearing_notes,
            sight_notes=self.sight_notes,
            sensory_pass=self.sensory_pass,
            location=self.env_location,
            time_of_day=self.env_time,
            weather=self.env_weather,
            light=self.env_light,
            ambient_sound=self.env_ambient,
            blocking=self.env_blocking,
            props=self.env_props,
        )

    def touch(self) -> None:
        self.updated_at = utc_now()

    def label(self) -> str:
        return f"{self.id} — {self.title} ({self.mode})"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def writing_dir(project: Project) -> Path:
    return project.root / "writing"


def get_api_key() -> str | None:
    """xAI key (legacy name). Prefer get_xai_key / probe_providers."""
    return get_xai_key()


def probe_writing_api() -> tuple[str, str]:
    """Return (Off|Partial|Ready, message). Never echoes keys."""
    return probe_providers()


def bible_block(project: Project, character_ids: list[str] | None = None) -> str:
    wanted = {c.lower() for c in (character_ids or [])}
    lines = [
        "Characters are adults (late 20s). Wedding bands are a story prop.",
        "Adult explicit / pornographic sex is allowed. Adults 18+ only. Do not invent minors.",
    ]
    for profile in list_characters(project):
        if wanted and profile.id not in wanted and profile.name.lower() not in wanted:
            continue
        desc = profile.injection_line()
        voice = (profile.voice_notes or "").strip()
        years = profile.age_years
        age_bit = profile.age_band
        if years is not None:
            age_bit = f"{profile.age_band}, {years}"
        chunk = f"- {profile.name} ({age_bit}): {desc}"
        if voice:
            chunk += f" Voice: {voice}"
        voice_id = (profile.voice_id or "").strip()
        if voice_id:
            chunk += f" Voice id: {voice_id}."
        nest = profile.living_brief()
        if nest.has_content():
            chunk += (
                f" Living: {nest.style_line()} · {nest.housing_quality} · "
                f"{nest.privacy} · {nest.income_band} (story)."
            )
        lines.append(chunk)
    from film_lab.lighting import lighting_bible_line

    lock = lighting_bible_line(project.active_lighting)
    if lock:
        lines.append(lock)
    return "\n".join(lines)


def _scene_source(project: Project, scene_id: str | None) -> str:
    if not scene_id:
        return ""
    try:
        return load_scene(project, scene_id).to_fountain(title=project.name)
    except (OSError, ValueError, FileNotFoundError):
        return ""


def build_prompt_pack(
    project: Project,
    *,
    mode: str,
    source: str,
    notes: str,
    scene_id: str | None,
    character_ids: list[str],
    tone: str = "",
    pacing: str = "",
    intimacy_mode: str = "covered sheets",
    intensity_preset: str = DEFAULT_PRESET,
    content_intensity: float = DEFAULT_INTENSITY,
    roleplay_speaker: str = "Director",
    turns: list[ChatTurn] | None = None,
    primary_genre: str = DEFAULT_PRIMARY,
    secondary_genres: list[str] | None = None,
    custom_genre_tags: list[str] | str = "",
    tropes_checklist: str = "",
    sensory: SensoryBrief | None = None,
    living: LivingBrief | None = None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt). Local until Generate is used with a key."""
    tags = parse_custom_tags(custom_genre_tags) if isinstance(custom_genre_tags, str) else list(custom_genre_tags or [])
    secondary = list(secondary_genres or [])
    intensity = clamp_content_intensity(content_intensity)
    named = intensity_preset if intensity_preset in INTENSITY_PRESETS else nearest_intensity_preset(intensity)
    check_genre_intimacy(
        primary_genre,
        secondary,
        tags,
        intimacy_mode,
        source,
        notes,
        tropes_checklist,
        content_intensity=intensity,
    )
    profiles = load_selected_characters(project, character_ids)
    from film_lab.filming import FilmingError, assert_filming_safe

    filming_mode = getattr(project, "filming_mode", None)
    try:
        assert_filming_safe(
            filming_mode,
            profiles,
            intimacy=intimacy_mode,
            intensity=intensity,
            context="building this writing pack",
        )
        assert_adult_cast(
            profiles,
            intimacy_mode=intimacy_mode,
            content_intensity=intensity,
            require_age=youth_shelf_active(primary_genre, secondary),
            context="building this writing pack",
        )
    except FilmingError as exc:
        raise CharacterError(str(exc)) from exc
    bible = bible_block(project, character_ids)
    scene_text = _scene_source(project, scene_id)
    material = (source or "").strip() or scene_text
    extra = (notes or "").strip()
    intimacy = intimacy_mode if intimacy_mode in INTIMACY_MODES else "covered sheets"
    genre_block = genre_prompt_block(
        primary_genre,
        secondary,
        tags,
        tropes_checklist,
        mode=mode,
    )
    genre_contract = genre_line(primary_genre, secondary, tags)
    brief = sensory or SensoryBrief()
    sense_block = sensory_prompt_block(
        brief,
        mode=mode,
        intimacy_mode=intimacy,
        content_intensity=intensity,
    )
    heat_block = intensity_prompt_block(intensity, named, intimacy_mode=intimacy)
    scene_living = None
    if scene_id:
        try:
            scene_living = load_scene(project, scene_id).living_brief()
        except (OSError, ValueError, FileNotFoundError, TypeError):
            scene_living = None
    nest = resolved_living(
        project,
        character_ids,
        scene_living=scene_living,
        draft_living=living,
    )
    live_source = "draft override" if living and living.override else "bible / scene / project nest"
    live_block = living_prompt_block(
        nest,
        mode=mode,
        source=live_source,
        sensory_pass=brief.sensory_pass,
    )

    if mode == "screenplay":
        system = (
            "You are a private film-school writing partner. Continue or expand a screenplay "
            "in Fountain-ish form: SCENE HEADING, action, CHARACTER, (parenthetical), dialogue. "
            "Keep Alison and Bradley consistent with the locked bible. Adults only. "
            "No ratings lecture, no content filter preamble. "
            "Explicit adult sex is in scope when the intimacy knob says so."
        )
        user = (
            f"{bible}\n\n{intimacy_writing_block(intimacy, write_mode='screenplay')}\n"
            f"Director notes: {extra or '(none)'}\n\n"
            f"Existing pages:\n{material or '(blank — open INT. BEDROOM - NIGHT)'}\n\n"
            "Continue the scene with heading, action, and dialogue. Stay in the room unless the notes say otherwise."
        )
    elif mode == "novel":
        system = (
            "You are drafting private novel prose for a story bible. Close third or limited, "
            "sensory, adult characters only. Explicit adult sex is allowed. No lecture."
        )
        user = (
            f"{bible}\n\nChapter / scene intent: {extra or 'bedroom study, lamp, after the door closes.'}\n"
            f"{intimacy_writing_block(intimacy, write_mode='novel')}\n\n"
            f"Seed / previous prose:\n{material or '(start a chapter)'}\n\n"
            "Write the next passage. Keep wedding bands and late-20s bodies in the texture, not as a checklist."
        )
    elif mode == "book_to_screenplay":
        system = (
            "You adapt a book excerpt into (1) a numbered scene breakdown and (2) Fountain screenplay pages. "
            "Preserve adult character names and blocking. Keep explicit sex on the page when the source or intimacy knob asks for it."
        )
        user = (
            f"{bible}\n\nAdaptation notes: {extra or 'Keep the lamp, the bed, the bands.'}\n"
            f"{intimacy_writing_block(intimacy, write_mode='book_to_screenplay')}\n\n"
            f"BOOK EXCERPT:\n{material or '(paste excerpt)'}\n\n"
            "Output:\n## Breakdown\n- numbered beats\n## Screenplay\nFountain pages"
        )
    elif mode == "roleplay":
        system = (
            "You are in a private rehearsal. Speak in-character as Alison, Bradley, or the Director "
            "as asked. Adults late 20s. Stay consistent with the bible. Short takes, playable aloud. "
            "No OOC safety lecture. Explicit adult sex is in scope when asked."
        )
        history = _turns_as_text(turns or [])
        user = (
            f"{bible}\n\nYou are answering as: {roleplay_speaker}\n"
            f"{intimacy_writing_block(intimacy, write_mode='roleplay')}\n"
            f"Notes: {extra or '(none)'}\n"
            f"Scene pages:\n{material or scene_text or '(empty room)'}\n\n"
            f"Rehearsal so far:\n{history or '(first take)'}\n\n"
            f"Write the next line(s) as {roleplay_speaker}."
        )
    elif mode == "director_rewrite":
        system = (
            "You rewrite an existing scene to the director's notes. Keep character voice. "
            "Adjust tone, pacing, and intimacy level. Adults only. Fountain-ish output."
        )
        user = (
            f"{bible}\n\nTone: {tone or 'held, warm'}\nPacing: {pacing or 'let the lamp work'}\n"
            f"{intimacy_writing_block(intimacy, write_mode='director_rewrite')}\n"
            f"Other notes: {extra or '(none)'}\n\n"
            f"SCENE TO REWRITE:\n{material or scene_text or '(no scene loaded)'}\n\n"
            "Rewrite the full scene. Do not summarize."
        )
    else:
        system = "Private film-school writing partner. Adults only."
        user = f"{bible}\n\n{extra}\n\n{material}"
    system = (
        f"{system} Follow the genre contract: {genre_contract}. "
        f"{sensory_system_addendum(brief, mode)}"
    )
    tone_line = (tone or "").strip()
    pace_line = (pacing or "").strip()
    extras = [
        genre_block,
        sense_block,
        intimacy_writing_block(intimacy, write_mode=mode),
        heat_block,
    ]
    if live_block:
        extras.append(live_block)
    if tone_line and mode != "director_rewrite":
        extras.append(f"Tone: {tone_line}")
    if pace_line and mode != "director_rewrite":
        extras.append(f"Pacing: {pace_line}")
    user = "\n\n".join(extras) + "\n\n" + user
    return system, user


def _turns_as_text(turns: list[ChatTurn]) -> str:
    lines = []
    for turn in turns:
        who = turn.speaker or turn.role
        lines.append(f"{who}: {turn.content}")
    return "\n".join(lines)


def save_draft(project: Project, draft: WritingDraft) -> Path:
    project.ensure_dirs()
    writing_dir(project).mkdir(parents=True, exist_ok=True)
    draft.touch()
    path = writing_dir(project) / f"{draft.id}.json"
    write_json(path, draft.to_dict())
    return path


def load_draft(project: Project, draft_id: str) -> WritingDraft:
    data = read_json(writing_dir(project) / f"{draft_id}.json")
    if not isinstance(data, dict):
        raise WritingError(f"Draft {draft_id} is not a JSON object")
    return WritingDraft(**{k: data[k] for k in WritingDraft.__dataclass_fields__ if k in data})


def list_drafts(project: Project) -> list[WritingDraft]:
    folder = writing_dir(project)
    if not folder.exists():
        return []
    drafts: list[WritingDraft] = []
    for path in sorted(folder.glob("*.json")):
        try:
            drafts.append(load_draft(project, path.stem))
        except (OSError, TypeError, ValueError):
            continue
    drafts.sort(key=lambda d: d.updated_at, reverse=True)
    return drafts


def draft_choices(project: Project) -> list[str]:
    return [d.label() for d in list_drafts(project)]


def export_draft(project: Project, draft: WritingDraft, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    suffix = dest.suffix.lower()
    if suffix == ".md":
        dest.write_text(_draft_markdown(draft), encoding="utf-8")
        return dest
    if suffix in {".fountain", ".txt"}:
        dest.write_text(draft.body or draft.user_prompt or "", encoding="utf-8")
        return dest
    from film_lab.office import OfficeError, export_typed

    try:
        return export_typed(
            draft.body or draft.user_prompt or "",
            dest,
            title=draft.title or "Draft",
        )
    except OfficeError as exc:
        raise WritingError(str(exc)) from exc


def _draft_markdown(draft: WritingDraft) -> str:
    bits = [
        f"# {draft.title}",
        "",
        f"- mode: `{draft.mode}`",
        f"- scene: `{draft.scene_id or ''}`",
        f"- intimacy: {draft.intimacy_mode}",
        f"- content intensity: {draft.content_intensity:.2f} ({draft.intensity_preset})",
        f"- genre: {genre_line(draft.primary_genre, draft.secondary_genres, draft.custom_genre_tags)}",
        f"- emotion: {draft.primary_emotion} / {draft.secondary_emotion} @ {draft.emotion_intensity:.2f}",
        f"- relationship: {draft.relationship_temp}",
        f"- environment: {draft.env_location} · {draft.env_light} · {draft.env_weather}",
        f"- living: {draft.living_brief().style_line()} ({'override' if draft.living_override else 'inherit'})",
        f"- sensory pass: {'on' if draft.sensory_pass else 'off'}",
        f"- provider: {draft.provider}",
        f"- dual roles: {draft.dual_roles}",
        f"- api: {'yes · ' + (draft.model or '') if draft.used_api else 'no (local draft)'}",
        "",
        "## Emotion, senses, environment",
        "",
        sensory_prompt_block(draft.sensory_brief(), mode=draft.mode),
        "",
        "## Tropes checklist",
        "",
        draft.tropes_checklist.strip() or "—",
        "",
        "## Body",
        "",
        draft.body or "_(empty)_",
        "",
        "## Prompt pack (local)",
        "",
        "### System",
        "",
        draft.system_prompt,
        "",
        "### User",
        "",
        draft.user_prompt,
        "",
    ]
    return "\n".join(bits)


def complete_chat(messages: list[dict[str, str]], *, temperature: float = 0.85) -> str:
    """Grok-only helper kept for older callers."""
    from film_lab.llm import complete_xai

    try:
        return complete_xai(messages, temperature=temperature)
    except RuntimeError as exc:
        raise WritingError(str(exc)) from exc


def generate_draft(project: Project, draft: WritingDraft) -> WritingDraft:
    system, user = build_prompt_pack(
        project,
        mode=draft.mode,
        source=draft.source,
        notes=draft.notes,
        scene_id=draft.scene_id,
        character_ids=draft.character_ids,
        tone=draft.tone,
        pacing=draft.pacing,
        intimacy_mode=draft.intimacy_mode,
        intensity_preset=draft.intensity_preset,
        content_intensity=draft.content_intensity,
        roleplay_speaker=draft.roleplay_speaker,
        turns=draft.turns,
        primary_genre=draft.primary_genre,
        secondary_genres=draft.secondary_genres,
        custom_genre_tags=draft.custom_genre_tags,
        tropes_checklist=draft.tropes_checklist,
        sensory=draft.sensory_brief(),
        living=draft.living_brief(),
    )
    draft.system_prompt = system
    draft.user_prompt = user
    messages = [{"role": "system", "content": system}]
    for turn in draft.turns:
        messages.append(turn.to_api())
    if draft.mode != "roleplay" or not draft.turns:
        messages.append({"role": "user", "content": user})
    if normalize_provider(draft.provider) == PROVIDER_LOCAL:
        draft.body = compose_local_pages(project, draft)
        draft.used_api = False
        draft.model = "local-templates"
        draft.dual_spine = ""
        if draft.mode == "roleplay":
            draft.turns.append(
                ChatTurn(role="assistant", speaker=draft.roleplay_speaker, content=draft.body)
            )
        save_draft(project, draft)
        return draft
    try:
        body, model_label, spine = run_generation(
            messages,
            provider=draft.provider,
            dual_roles=draft.dual_roles,
            mode=draft.mode,
            api_model=draft.api_model or "",
        )
    except RuntimeError as exc:
        raise WritingError(str(exc)) from exc
    draft.body = body
    draft.dual_spine = spine
    draft.used_api = True
    draft.model = model_label
    if draft.mode == "roleplay":
        draft.turns.append(
            ChatTurn(role="assistant", speaker=draft.roleplay_speaker, content=draft.body)
        )
    save_draft(project, draft)
    return draft


def compose_local_pages(project: Project, draft: WritingDraft) -> str:
    """Zero-cost Fountain / prose / rehearsal pages. No network. Adults 18+ only."""
    profiles = load_selected_characters(project, draft.character_ids)
    assert_adult_cast(
        profiles,
        intimacy_mode=draft.intimacy_mode,
        content_intensity=draft.content_intensity,
        context="local writing pages",
    )
    check_genre_intimacy(
        draft.primary_genre,
        draft.secondary_genres,
        draft.custom_genre_tags,
        draft.intimacy_mode,
        draft.source,
        draft.notes,
        draft.body,
        content_intensity=draft.content_intensity,
    )
    names = [p.name for p in profiles]
    lead = names[0] if names else "Alison"
    pair = names[1] if len(names) > 1 else ("Bradley" if lead.lower() != "bradley" else "Alison")
    heading = (draft.env_location or "INT. BEDROOM - NIGHT").strip().upper()
    if draft.source and re.match(r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)", draft.source.strip(), re.I):
        heading = draft.source.strip().splitlines()[0].upper()
    lamp = (draft.env_light or "warm lamp").strip() or "warm lamp"
    time_of = (draft.env_time or "night").strip() or "night"
    weather = (draft.env_weather or "clear").strip()
    emotion = (draft.primary_emotion or "tenderness").strip()
    conflict = (draft.secondary_emotion or "longing").strip()
    notes = (draft.notes or "Stay on faces. Let the lamp work.").strip()
    genre = (draft.primary_genre or "romance").strip()
    intimacy = draft.intimacy_mode
    heat = draft.content_intensity
    living = draft.living_brief()
    nest_bits = [x for x in (living.housing_quality, living.privacy) if x and x != "unspecified"]
    nest = nest_bits[0] if nest_bits else "a lived-in room"
    inner = (draft.inner_state or f"{emotion}, held").strip()
    outer = (draft.outer_behavior or "quiet, close").strip()

    if intimacy == EXPLICIT_INTIMACY or heat >= 0.9:
        action = (
            f"The {lamp} holds. {lead} and {pair} are adults, already undressed under the sheet. "
            f"Wedding bands catch once. {lead} pulls {pair} in — mouth, hips, the wet sound of it. "
            f"No fade. The room stays {time_of}, {weather}."
        )
        a_line = "Don't stop. I want you in me."
        b_line = "I've got you. Stay open."
        a_paren = "breath against his mouth"
        b_paren = "close, wrecked"
    elif intimacy == "intimate sex" or heat >= 0.6:
        action = (
            f"The {lamp} holds. {lead} and {pair}, both late twenties, are in the bed. "
            f"The sheet slips. Weight, breath, hips. {outer.capitalize()} on the outside; "
            f"{inner} underneath. {weather}, {time_of}."
        )
        a_line = "Stay like that."
        b_line = "I wasn't going anywhere."
        a_paren = "almost not a question"
        b_paren = "close"
    elif intimacy == "artistic nude":
        action = (
            f"The {lamp} holds. {lead} and {pair} are bare in the {nest}. "
            f"Skin is the wardrobe. Wedding bands catch once. {emotion} against {conflict}."
        )
        a_line = "Look at me."
        b_line = "I am."
        a_paren = "quiet"
        b_paren = "not performing"
    else:
        action = (
            f"A cheap {lamp} holds the room. {lead} and {pair}, both late twenties, "
            f"are already in the bed. Wedding bands catch once. The city is elsewhere. "
            f"{emotion} under {conflict}. {notes}"
        )
        a_line = "Stay like that."
        b_line = "I wasn't going anywhere."
        a_paren = "almost not a question"
        b_paren = "close"

    fountain = (
        f"{heading}\n\n"
        f"{action}\n\n"
        f"{lead.upper()}\n"
        f"({a_paren})\n"
        f"{a_line}\n\n"
        f"{pair.upper()}\n"
        f"({b_paren})\n"
        f"{b_line}\n\n"
        f"= Director: {genre}. Intensity {heat:.2f}. Adults 18+ only. {notes}\n"
    )

    if draft.mode == "screenplay":
        return fountain.strip() + "\n"
    if draft.mode == "novel":
        return (
            f"{lead} felt the {lamp} on the ceiling before she felt {pair}. "
            f"The {nest} kept their secret the way thin rooms do — close, ordinary, adult. "
            f"{action} {a_line} {b_line} "
            f"They were both past twenty. The scene does not invent a child.\n"
        )
    if draft.mode == "book_to_screenplay":
        excerpt = (draft.source or action).strip()
        return (
            f"# Adaptation breakdown — {draft.title}\n\n"
            f"SOURCE (held):\n{excerpt[:800]}\n\n"
            f"SHOOTABLE PAGES:\n\n{fountain}"
        )
    if draft.mode == "roleplay":
        speaker = draft.roleplay_speaker or lead
        if speaker.lower() == pair.lower():
            return f"{b_line} ({b_paren}. {lamp}. Adults 18+.)"
        if speaker.lower() == "director":
            return (
                f"Hold on {lead}'s mouth, then {pair}'s hands. {lamp}. "
                f"Do not cut away. Adults 18+ only. {notes}"
            )
        return f"{a_line} ({a_paren}. The {lamp} does not move.)"
    # director_rewrite
    source = (draft.source or fountain).strip()
    return (
        f"# Rewrite — {draft.title}\n\n"
        f"What changes: keep the locked adult bible. Tighten blocking. "
        f"{emotion} vs {conflict}. {notes}\n\n"
        f"{source}\n\n"
        f"REVISED BEAT:\n{action}\n\n{lead.upper()}\n{a_line}\n\n{pair.upper()}\n{b_line}\n"
    )


def fountain_to_scene(text: str, *, scene_id: str | None = None, heading: str | None = None) -> Scene:
    """Best-effort Fountain parse so a draft can land on the Script desk."""
    scene = Scene(id=scene_id or new_id(), heading=heading or "INT. BEDROOM - NIGHT")
    action_bits: list[str] = []
    lines: list[DialogueLine] = []
    pending_char: str | None = None
    pending_paren = ""
    for raw in (text or "").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.match(r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)", stripped, re.IGNORECASE):
            scene.heading = stripped.upper()
            pending_char = None
            continue
        if stripped.startswith("="):
            scene.director_notes = (scene.director_notes + " " + stripped.lstrip("= ")).strip()
            continue
        if stripped.startswith("(") and stripped.endswith(")") and pending_char:
            pending_paren = stripped.strip("()")
            continue
        if re.match(r"^[A-Z][A-Z0-9 .\-']{1,30}$", stripped) and not stripped.endswith("."):
            pending_char = stripped
            pending_paren = ""
            continue
        if pending_char:
            lines.append(DialogueLine(character=pending_char, parenthetical=pending_paren, text=stripped))
            pending_char = None
            pending_paren = ""
            continue
        action_bits.append(stripped)
    scene.action = "\n".join(action_bits)
    scene.lines = lines
    return scene


def push_draft_to_scene(project: Project, draft: WritingDraft) -> Scene:
    existing_id = draft.scene_id
    scene = fountain_to_scene(draft.body or draft.source, scene_id=existing_id)
    if existing_id:
        try:
            old = load_scene(project, existing_id)
            scene.shot_ids = old.shot_ids
            scene.status = old.status
            if not scene.director_notes:
                scene.director_notes = old.director_notes
        except (OSError, ValueError, FileNotFoundError):
            scene.id = existing_id
    scene.primary_genre = draft.primary_genre or scene.primary_genre
    scene.secondary_genres = list(draft.secondary_genres or scene.secondary_genres)
    scene.custom_genre_tags = list(draft.custom_genre_tags or scene.custom_genre_tags)
    scene.tropes_checklist = draft.tropes_checklist or scene.tropes_checklist
    nest = resolved_living(
        project,
        draft.character_ids,
        scene_living=scene.living_brief(),
        draft_living=draft.living_brief(),
    )
    if nest.has_content():
        scene.set_living(nest)
    save_scene(project, scene)
    draft.scene_id = scene.id
    save_draft(project, draft)
    return scene


def extract_dialogue_takes(text: str) -> list[DialogueLine]:
    scene = fountain_to_scene(text)
    if scene.lines:
        return scene.lines
    # Roleplay "ALISON: stay." fallback
    takes: list[DialogueLine] = []
    for raw in (text or "").splitlines():
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9 \-]+)\s*:\s*(.+)$", raw)
        if match:
            takes.append(DialogueLine(character=match.group(1).strip(), text=match.group(2).strip()))
    return takes


def apply_sensory_brief(draft: WritingDraft, brief: SensoryBrief) -> WritingDraft:
    draft.primary_emotion = brief.primary_emotion
    draft.secondary_emotion = brief.secondary_emotion
    draft.emotion_intensity = brief.intensity
    draft.inner_state = brief.inner_state
    draft.outer_behavior = brief.outer_behavior
    draft.relationship_temp = brief.relationship_temp
    draft.enabled_senses = list(brief.enabled_senses)
    draft.touch_notes = brief.touch_notes
    draft.smell_notes = brief.smell_notes
    draft.taste_notes = brief.taste_notes
    draft.hearing_notes = brief.hearing_notes
    draft.sight_notes = brief.sight_notes
    draft.sensory_pass = brief.sensory_pass
    draft.env_location = brief.location
    draft.env_time = brief.time_of_day
    draft.env_weather = brief.weather
    draft.env_light = brief.light
    draft.env_ambient = brief.ambient_sound
    draft.env_blocking = brief.blocking
    draft.env_props = brief.props
    return draft


def new_draft(title: str = "Untitled draft", mode: str = "screenplay") -> WritingDraft:
    from film_lab.senses import DEFAULT_SENSE_PRESET, preset_brief

    draft = WritingDraft(id=new_id(), title=title.strip() or "Untitled draft", mode=mode)
    return apply_sensory_brief(draft, preset_brief(DEFAULT_SENSE_PRESET))
