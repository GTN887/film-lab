"""Director / Voice / image provider menus. UI pickers only.

Local is always the default. Cloud families are optional and use keys the user
owns. Film Lab never hardcodes secrets, never meters credits, and never fakes
a cloud result. Unwired APIs fail soft: set API key / coming soon.

Picker labels match Liam's desk words. Hub chrome stays original Film Lab names.
"""

from __future__ import annotations

from dataclasses import dataclass

from film_lab.llm import (
    DEFAULT_PROVIDER,
    NO_CREDITS,
    PROVIDER_CLAUDE,
    PROVIDER_DUAL,
    PROVIDER_GEMINI,
    PROVIDER_GROK,
    PROVIDER_LOCAL,
    PROVIDER_OPENAI,
    get_anthropic_key,
    get_gemini_key,
    get_openai_key,
    get_xai_key,
)

# --- Voice Desk -------------------------------------------------------------

VOICE_LOCAL = "Local TTS"
VOICE_ELEVENLABS = "ElevenLabs"
VOICE_SEED_AUDIO = "Seed Audio"
VOICE_SEED_SPEECH = "Seed Speech"

VOICE_PROVIDERS: tuple[str, ...] = (
    VOICE_LOCAL,
    VOICE_ELEVENLABS,
    VOICE_SEED_AUDIO,
    VOICE_SEED_SPEECH,
)
VOICE_DEFAULT = VOICE_LOCAL

# --- Image / generation (Motion, Still, Effects) ----------------------------

IMAGE_LOCAL = "Local / ComfyUI"
IMAGE_NANO = "Nano Banana"
IMAGE_GROK = "Grok"
IMAGE_IDEOGRAM = "Ideogram"
IMAGE_OPENAI = "OpenAI"
IMAGE_SEEDREAM = "Seedream"

IMAGE_FAMILIES: tuple[str, ...] = (
    IMAGE_LOCAL,
    IMAGE_NANO,
    IMAGE_GROK,
    IMAGE_IDEOGRAM,
    IMAGE_OPENAI,
    IMAGE_SEEDREAM,
)
IMAGE_FAMILY_DEFAULT = IMAGE_LOCAL

IMAGE_MODELS: dict[str, tuple[str, ...]] = {
    IMAGE_LOCAL: ("Local img2vid (ComfyUI · SVD-XT)",),
    IMAGE_NANO: (
        "Nano Banana Pro",
        "Nano Banana",
        "Nano Banana 2",
        "Nano Banana 2 Lite",
    ),
    IMAGE_GROK: (
        "Grok Imagine",
        "Grok Imagine Edit",
        "Grok Imagine 2.0",
        "Grok Imagine 2.0 Edit",
    ),
    IMAGE_IDEOGRAM: (
        "Ideogram 2.0",
        "Ideogram 2.0 Turbo",
        "Ideogram 1.0",
    ),
    IMAGE_OPENAI: (
        "GPT-4o",
        "GPT-4o mini",
        "GPT-4 Turbo",
        "GPT-3.5 Turbo",
    ),
    IMAGE_SEEDREAM: (
        "Seedream 5.0 Pro",
        "Seedream 5.0 Lite",
        "Seedream 4.5",
    ),
}

# --- Video / Motion generate (nested picker) --------------------------------
# Featured labels are Film Lab originals (multi-take / grounded mix). Not a
# third-party wordmark. Cloud families are pickers only until a user key exists.

VIDEO_LOCAL = "Local / ComfyUI"
VIDEO_FEATURED = "Featured"
VIDEO_HAILUO = "Minimax Hailuo"
VIDEO_FLUX = "FLUX.1 Video"
VIDEO_KLING = "Kling"
VIDEO_WAN = "Wan 3.0"
VIDEO_SORA = "OpenAI Sora 2"
VIDEO_VEO = "Google Veo"

VIDEO_FAMILIES: tuple[str, ...] = (
    VIDEO_LOCAL,
    VIDEO_FEATURED,
    VIDEO_HAILUO,
    VIDEO_FLUX,
    VIDEO_KLING,
    VIDEO_WAN,
    VIDEO_SORA,
    VIDEO_VEO,
)
VIDEO_FAMILY_DEFAULT = VIDEO_LOCAL

VIDEO_FEATURED_MODELS: tuple[str, ...] = ("Multi-Version", "Reality Mix")

VIDEO_MODELS: dict[str, tuple[str, ...]] = {
    VIDEO_LOCAL: ("Local img2vid (ComfyUI · SVD-XT)",),
    VIDEO_FEATURED: VIDEO_FEATURED_MODELS,
    VIDEO_HAILUO: (
        "Minimax H3 Max",
        "Hailuo 2.5 Fast",
        "H2",
        "Hailuo 3.0",
        "Hailuo G2",
    ),
    VIDEO_FLUX: ("FLUX.1 Video",),
    VIDEO_KLING: (
        "Kling 3.0 Motion Control",
        "Kling 3.0",
        "Kling V1 Video",
        "Kling V1 Video Edit",
    ),
    VIDEO_WAN: ("Wan 3.0",),
    VIDEO_SORA: ("OpenAI Sora 2",),
    VIDEO_VEO: (
        "Veo 3.1 Lite",
        "Veo 3.1 Fast",
        "Veo 3.1",
        "Veo 3",
        "Veo 2",
    ),
}

VIDEO_RESOLUTIONS: tuple[str, ...] = ("720", "1080")

# --- Text / director (Prompt Enhance, Writing Studio, UGC) ------------------

TEXT_LOCAL = "Local templates only"
TEXT_GROK = "Grok"
TEXT_GEMINI = "Gemini"
TEXT_OPENAI = "OpenAI"
TEXT_CLAUDE = "Claude"
TEXT_DUAL = "Dual (two providers)"

TEXT_FAMILIES: tuple[str, ...] = (
    TEXT_LOCAL,
    TEXT_GROK,
    TEXT_GEMINI,
    TEXT_OPENAI,
    TEXT_CLAUDE,
    TEXT_DUAL,
)
TEXT_FAMILY_DEFAULT = TEXT_LOCAL

TEXT_MODELS: dict[str, tuple[str, ...]] = {
    TEXT_LOCAL: ("Local templates only",),
    TEXT_GROK: ("Grok 2", "Grok mini", "Grok Beta"),
    TEXT_GEMINI: ("Gemini (Google)",),
    TEXT_OPENAI: (
        "GPT-4o",
        "GPT-4o mini",
        "GPT-4 Turbo",
        "GPT-3.5 Turbo",
        "o1",
        "o1-mini",
    ),
    TEXT_CLAUDE: (
        "Claude Sonnet",
        "Claude Opus",
        "Claude Haiku",
    ),
    TEXT_DUAL: (TEXT_DUAL,),
}

OPENAI_API_IDS: dict[str, str] = {
    "GPT-4o": "gpt-4o",
    "GPT-4o mini": "gpt-4o-mini",
    "GPT-4 Turbo": "gpt-4-turbo",
    "GPT-3.5 Turbo": "gpt-3.5-turbo",
    "o1": "o1",
    "o1-mini": "o1-mini",
}

GROK_CHAT_API_IDS: dict[str, str] = {
    "Grok 2": "grok-2",
    "Grok mini": "grok-2-mini",
    "Grok Beta": "grok-beta",
}

CLAUDE_API_IDS: dict[str, str] = {
    "Claude Sonnet": "claude-sonnet-4-5",
    "Claude Opus": "claude-opus-4-1",
    "Claude Haiku": "claude-haiku-4-5",
}

_FAMILY_TO_PROVIDER = {
    TEXT_LOCAL: PROVIDER_LOCAL,
    TEXT_GROK: PROVIDER_GROK,
    TEXT_GEMINI: PROVIDER_GEMINI,
    TEXT_OPENAI: PROVIDER_OPENAI,
    TEXT_CLAUDE: PROVIDER_CLAUDE,
    TEXT_DUAL: PROVIDER_DUAL,
}

_PROVIDER_TO_FAMILY = {
    PROVIDER_LOCAL: TEXT_LOCAL,
    PROVIDER_GROK: TEXT_GROK,
    PROVIDER_GEMINI: TEXT_GEMINI,
    PROVIDER_OPENAI: TEXT_OPENAI,
    PROVIDER_CLAUDE: TEXT_CLAUDE,
    PROVIDER_DUAL: TEXT_DUAL,
}


@dataclass(frozen=True)
class VoiceRoute:
    label: str
    local: bool
    wired: bool
    message: str


@dataclass(frozen=True)
class ImageRoute:
    family: str
    model: str
    local_i2v: bool
    wired: bool
    message: str


@dataclass(frozen=True)
class TextRoute:
    family: str
    model: str
    backend: str
    api_id: str
    wired: bool
    message: str


def image_models_for(family: str) -> list[str]:
    return list(IMAGE_MODELS.get(family, IMAGE_MODELS[IMAGE_LOCAL]))


def video_models_for(family: str) -> list[str]:
    return list(VIDEO_MODELS.get(family, VIDEO_MODELS[VIDEO_LOCAL]))


def default_video_model(family: str) -> str:
    models = video_models_for(family)
    return models[0] if models else VIDEO_MODELS[VIDEO_LOCAL][0]


def text_models_for(family: str) -> list[str]:
    return list(TEXT_MODELS.get(family, TEXT_MODELS[TEXT_LOCAL]))


def family_to_provider(family: str) -> str:
    return _FAMILY_TO_PROVIDER.get(family, DEFAULT_PROVIDER)


def provider_to_family(provider: str) -> str:
    return _PROVIDER_TO_FAMILY.get(provider, TEXT_LOCAL)


def default_text_model(family: str) -> str:
    models = text_models_for(family)
    return models[0] if models else TEXT_LOCAL


def default_image_model(family: str) -> str:
    models = image_models_for(family)
    return models[0] if models else IMAGE_MODELS[IMAGE_LOCAL][0]


def _coming_soon(name: str, key_hint: str = "") -> str:
    hint = f" Set {key_hint}." if key_hint else ""
    return (
        f"{name}: set API key / coming soon.{hint} "
        f"Film Lab will not fake this generation. Local stays the zero-credit path. {NO_CREDITS}"
    )


def resolve_voice_provider(label: str | None) -> VoiceRoute:
    from film_lab.offline import offline_forced

    name = (label or "").strip() or VOICE_DEFAULT
    if offline_forced() and name != VOICE_LOCAL:
        return VoiceRoute(
            label=VOICE_LOCAL,
            local=True,
            wired=True,
            message=f"Offline-first: Local TTS. ElevenLabs is online optional. {NO_CREDITS}",
        )
    if name == VOICE_LOCAL or name not in VOICE_PROVIDERS:
        if name not in VOICE_PROVIDERS and name != VOICE_LOCAL:
            name = VOICE_DEFAULT
        return VoiceRoute(
            label=VOICE_LOCAL,
            local=True,
            wired=True,
            message=f"Local TTS (pyttsx3 / Piper / espeak / import / placeholder). {NO_CREDITS}",
        )
    if name == VOICE_ELEVENLABS:
        return VoiceRoute(
            label=name,
            local=False,
            wired=False,
            message=_coming_soon(name, "FILM_LAB_ELEVENLABS_API_KEY (optional later)"),
        )
    return VoiceRoute(
        label=name,
        local=False,
        wired=False,
        message=_coming_soon(name),
    )


def resolve_video_pick(family: str | None, model: str | None = None) -> ImageRoute:
    """Motion Desk generate path. Local / Featured aliases use SVD-XT. Else fail-soft."""
    fam = family if family in VIDEO_FAMILIES else VIDEO_FAMILY_DEFAULT
    models = video_models_for(fam)
    pick = model if model in models else models[0]
    if fam == VIDEO_LOCAL:
        return ImageRoute(
            family=fam,
            model=pick,
            local_i2v=True,
            wired=True,
            message=f"Local ComfyUI SVD-XT img2vid. {NO_CREDITS}",
        )
    if fam == VIDEO_FEATURED:
        return ImageRoute(
            family=fam,
            model=pick,
            local_i2v=True,
            wired=True,
            message=(
                f"Featured `{pick}` is a Film Lab desk alias — local SVD-XT "
                f"(multi-take / mix on this box). {NO_CREDITS}"
            ),
        )
    return ImageRoute(
        family=fam,
        model=pick,
        local_i2v=False,
        wired=False,
        message=_coming_soon(f"{fam} · {pick}"),
    )


def resolve_image_pick(family: str | None, model: str | None = None) -> ImageRoute:
    fam = family if family in IMAGE_FAMILIES else IMAGE_FAMILY_DEFAULT
    models = image_models_for(fam)
    pick = model if model in models else models[0]
    if fam == IMAGE_LOCAL:
        return ImageRoute(
            family=fam,
            model=pick,
            local_i2v=True,
            wired=True,
            message=f"Local ComfyUI SVD-XT img2vid. {NO_CREDITS}",
        )
    return ImageRoute(
        family=fam,
        model=pick,
        local_i2v=False,
        wired=False,
        message=_coming_soon(f"{fam} · {pick}"),
    )


def resolve_text_pick(family: str | None, model: str | None = None) -> TextRoute:
    """Map a nested picker to a wired text backend, or fail-soft."""
    from film_lab.offline import offline_forced

    if offline_forced():
        return TextRoute(
            family=TEXT_LOCAL,
            model=TEXT_LOCAL,
            backend=PROVIDER_LOCAL,
            api_id="",
            wired=True,
            message=f"Offline-first: local templates. Online optional is off. {NO_CREDITS}",
        )
    if family in (
        PROVIDER_LOCAL,
        PROVIDER_GROK,
        PROVIDER_GEMINI,
        PROVIDER_OPENAI,
        PROVIDER_CLAUDE,
        PROVIDER_DUAL,
    ):
        family = provider_to_family(family)
    fam = family if family in TEXT_FAMILIES else TEXT_FAMILY_DEFAULT
    models = text_models_for(fam)
    pick = model if model in models else models[0]
    backend = family_to_provider(fam)

    if backend == PROVIDER_LOCAL:
        return TextRoute(
            family=fam,
            model=pick,
            backend=PROVIDER_LOCAL,
            api_id="",
            wired=True,
            message=f"Local templates. {NO_CREDITS}",
        )
    if backend == PROVIDER_DUAL:
        return TextRoute(
            family=fam,
            model=pick,
            backend=PROVIDER_DUAL,
            api_id="",
            wired=True,
            message=f"Dual uses the two keys you already set. {NO_CREDITS}",
        )
    if backend == PROVIDER_GEMINI:
        if get_gemini_key():
            return TextRoute(
                family=fam,
                model=pick,
                backend=PROVIDER_GEMINI,
                api_id="",
                wired=True,
                message=f"Gemini with your key. {NO_CREDITS}",
            )
        return TextRoute(
            family=fam,
            model=pick,
            backend=PROVIDER_GEMINI,
            api_id="",
            wired=False,
            message=_coming_soon("Gemini", "FILM_LAB_GEMINI_API_KEY (or GEMINI_API_KEY)"),
        )
    if backend == PROVIDER_GROK:
        api_id = GROK_CHAT_API_IDS.get(pick, "")
        if get_xai_key():
            return TextRoute(
                family=fam,
                model=pick,
                backend=PROVIDER_GROK,
                api_id=api_id,
                wired=True,
                message=f"Grok chat `{pick}` via your xAI key. {NO_CREDITS}",
            )
        return TextRoute(
            family=fam,
            model=pick,
            backend=PROVIDER_GROK,
            api_id=api_id,
            wired=False,
            message=_coming_soon(f"Grok · {pick}", "FILM_LAB_XAI_API_KEY (or XAI_API_KEY)"),
        )
    if backend == PROVIDER_OPENAI:
        api_id = OPENAI_API_IDS.get(pick, "")
        if get_openai_key():
            return TextRoute(
                family=fam,
                model=pick,
                backend=PROVIDER_OPENAI,
                api_id=api_id,
                wired=True,
                message=f"OpenAI `{pick}` via your key. {NO_CREDITS}",
            )
        return TextRoute(
            family=fam,
            model=pick,
            backend=PROVIDER_OPENAI,
            api_id=api_id,
            wired=False,
            message=_coming_soon(f"OpenAI · {pick}", "FILM_LAB_OPENAI_API_KEY (or OPENAI_API_KEY)"),
        )
    if backend == PROVIDER_CLAUDE:
        api_id = CLAUDE_API_IDS.get(pick, "")
        if get_anthropic_key():
            return TextRoute(
                family=fam,
                model=pick,
                backend=PROVIDER_CLAUDE,
                api_id=api_id,
                wired=True,
                message=f"Claude `{pick}` via your Anthropic key. {NO_CREDITS}",
            )
        return TextRoute(
            family=fam,
            model=pick,
            backend=PROVIDER_CLAUDE,
            api_id=api_id,
            wired=False,
            message=_coming_soon(
                f"Claude · {pick}",
                "FILM_LAB_ANTHROPIC_API_KEY (or ANTHROPIC_API_KEY)",
            ),
        )
    return TextRoute(
        family=TEXT_LOCAL,
        model=TEXT_LOCAL,
        backend=PROVIDER_LOCAL,
        api_id="",
        wired=True,
        message=f"Local templates. {NO_CREDITS}",
    )


def providers_markdown() -> str:
    return (
        "### Provider menus\n"
        "Local is the default. **Works offline for local generation.** "
        "Zero Film Lab credits. Cloud picks are **online optional** and need **your** keys "
        "and fail soft when an API is not wired — Film Lab will not fake a clip, still, or take.\n\n"
        "- **Voice** — Local TTS (default), then ElevenLabs / Seed Audio / Seed Speech.\n"
        "- **Video / Motion** — Local / ComfyUI SVD-XT (default), Featured aliases, "
        "then nested cloud families. Unwired clips fail soft.\n"
        "- **Image / generation** — Local / ComfyUI (SVD-XT), then nested families "
        "on Motion, Still, and Effects.\n"
        "- **Director / enhance / writing** — Local templates, Grok chat, Gemini, OpenAI, Claude, Dual.\n"
        "Never paste a secret into a field. Environment keys only."
    )
