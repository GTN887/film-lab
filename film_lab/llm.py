"""Optional cloud writing backends. User-owned keys only. No Film Lab credits.

Local templates always work. Grok (xAI), Gemini (Google), ChatGPT (OpenAI),
and Claude (Anthropic) turn on only when you set a key in the environment.
This lab never invents a credit meter, quota, or paywall. If a provider bills
you, that is their account, not ours. Not a hosted “superagent” plugin.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROVIDER_LOCAL = "Local templates only"
PROVIDER_GROK = "Grok (xAI)"
PROVIDER_GEMINI = "Gemini (Google)"
PROVIDER_OPENAI = "ChatGPT (OpenAI)"
PROVIDER_CLAUDE = "Claude (Anthropic)"
PROVIDER_DUAL = "Dual (two providers)"

PROVIDERS: tuple[str, ...] = (
    PROVIDER_LOCAL,
    PROVIDER_GROK,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    PROVIDER_CLAUDE,
    PROVIDER_DUAL,
)

UGC_PROVIDERS: tuple[str, ...] = (
    PROVIDER_LOCAL,
    PROVIDER_GROK,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    PROVIDER_CLAUDE,
)

DUAL_GEMINI_SPINE = "Gemini: story spine · Grok: dialogue & roleplay"
DUAL_GROK_SPINE = "Grok: story spine · Gemini: dialogue & roleplay"
DUAL_GEMINI_THEN_GROK = "Sequential: Gemini full draft → Grok rewrite"
DUAL_GROK_THEN_GEMINI = "Sequential: Grok full draft → Gemini rewrite"
DUAL_COMPARE = "Grok + Gemini full pages (compare)"
DUAL_OPENAI_GROK = "ChatGPT: story spine · Grok: dialogue & roleplay"
DUAL_OPENAI_GEMINI = "ChatGPT: story spine · Gemini: dialogue & roleplay"
DUAL_OPENAI_THEN_GROK = "Sequential: ChatGPT full draft → Grok rewrite"
DUAL_COMPARE_OPENAI_GROK = "ChatGPT + Grok full pages (compare)"

DUAL_ROLES: tuple[str, ...] = (
    DUAL_GEMINI_SPINE,
    DUAL_GROK_SPINE,
    DUAL_OPENAI_GROK,
    DUAL_OPENAI_GEMINI,
    DUAL_GEMINI_THEN_GROK,
    DUAL_GROK_THEN_GEMINI,
    DUAL_OPENAI_THEN_GROK,
    DUAL_COMPARE,
    DUAL_COMPARE_OPENAI_GROK,
)

DEFAULT_PROVIDER = PROVIDER_LOCAL
DEFAULT_DUAL_ROLES = DUAL_GEMINI_SPINE

DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_XAI_BASE = "https://api.x.ai/v1"
# Current Gemini flash id (GA as of 2026-09 docs). Override if Google retires it.
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
# Chat Completions id — override if OpenAI retires it (fail soft on 404).
DEFAULT_OPENAI_MODEL = "gpt-4.1"
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
# Messages API id — override if Anthropic retires it (fail soft on 404).
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5"
DEFAULT_ANTHROPIC_BASE = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

NO_CREDITS = (
    "Film Lab has no credits, quotas, or paywalls. "
    "Optional APIs use keys you own. This studio never sells generation."
)
LEAVE_XAI = "Writing Studio API calls leave this machine to xAI."
LEAVE_GEMINI = "Writing Studio API calls leave this machine to Google Gemini."
LEAVE_OPENAI = "Writing Studio API calls leave this machine to OpenAI."
LEAVE_ANTHROPIC = "Writing Studio API calls leave this machine to Anthropic."
LEAVE_DUAL = "Writing Studio API calls leave this machine to the Dual providers you picked."

GEMINI_SAFETY = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
]


def normalize_provider(value: str | None) -> str:
    return value if value in PROVIDERS else DEFAULT_PROVIDER


def normalize_dual_roles(value: str | None) -> str:
    return value if value in DUAL_ROLES else DEFAULT_DUAL_ROLES


def get_xai_key() -> str | None:
    for name in ("FILM_LAB_XAI_API_KEY", "XAI_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def get_gemini_key() -> str | None:
    for name in ("FILM_LAB_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def xai_model() -> str:
    return os.environ.get("FILM_LAB_XAI_MODEL", DEFAULT_XAI_MODEL).strip() or DEFAULT_XAI_MODEL


def xai_base() -> str:
    return os.environ.get("FILM_LAB_XAI_BASE", DEFAULT_XAI_BASE).rstrip("/")


def gemini_model() -> str:
    return (
        os.environ.get("FILM_LAB_GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        or DEFAULT_GEMINI_MODEL
    )


def gemini_base() -> str:
    return os.environ.get("FILM_LAB_GEMINI_BASE", DEFAULT_GEMINI_BASE).rstrip("/")


def get_openai_key() -> str | None:
    for name in ("FILM_LAB_OPENAI_API_KEY", "OPENAI_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def openai_model() -> str:
    return (
        os.environ.get("FILM_LAB_OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
        or DEFAULT_OPENAI_MODEL
    )


def openai_base() -> str:
    return os.environ.get("FILM_LAB_OPENAI_BASE", DEFAULT_OPENAI_BASE).rstrip("/")


def get_anthropic_key() -> str | None:
    for name in ("FILM_LAB_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def anthropic_model() -> str:
    return (
        os.environ.get("FILM_LAB_ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL).strip()
        or DEFAULT_ANTHROPIC_MODEL
    )


def anthropic_base() -> str:
    return os.environ.get("FILM_LAB_ANTHROPIC_BASE", DEFAULT_ANTHROPIC_BASE).rstrip("/")


def probe_xai() -> tuple[str, str]:
    if not get_xai_key():
        return (
            "Off",
            "Set FILM_LAB_XAI_API_KEY (or XAI_API_KEY) for Grok. No Film Lab credits.",
        )
    return "Ready", f"model `{xai_model()}`. {LEAVE_XAI}"


def probe_gemini() -> tuple[str, str]:
    if not get_gemini_key():
        return (
            "Off",
            "Set FILM_LAB_GEMINI_API_KEY (or GEMINI_API_KEY / GOOGLE_API_KEY). "
            "No Film Lab credits.",
        )
    return "Ready", f"model `{gemini_model()}`. {LEAVE_GEMINI}"


def probe_openai() -> tuple[str, str]:
    if not get_openai_key():
        return (
            "Off",
            "Set FILM_LAB_OPENAI_API_KEY (or OPENAI_API_KEY) for ChatGPT. No Film Lab credits.",
        )
    return "Ready", f"model `{openai_model()}`. {LEAVE_OPENAI}"


def probe_anthropic() -> tuple[str, str]:
    if not get_anthropic_key():
        return (
            "Off",
            "Set FILM_LAB_ANTHROPIC_API_KEY (or ANTHROPIC_API_KEY) for Claude. "
            "No Film Lab credits.",
        )
    return "Ready", f"model `{anthropic_model()}`. {LEAVE_ANTHROPIC}"


def probe_writing_api() -> tuple[str, str]:
    """Overall (Off|Partial|Ready, message). Never echoes keys."""
    gx, gxm = probe_xai()
    gm, gmm = probe_gemini()
    go, gom = probe_openai()
    gc, gcm = probe_anthropic()
    named = (("Grok", gx), ("Gemini", gm), ("ChatGPT", go), ("Claude", gc))
    ready = [name for name, st in named if st == "Ready"]
    if not ready:
        return (
            "Off",
            "Local templates only. Set FILM_LAB_XAI_API_KEY (or XAI_API_KEY) and/or "
            "FILM_LAB_GEMINI_API_KEY (or GEMINI_API_KEY / GOOGLE_API_KEY) and/or "
            "FILM_LAB_OPENAI_API_KEY (or OPENAI_API_KEY) and/or "
            "FILM_LAB_ANTHROPIC_API_KEY (or ANTHROPIC_API_KEY) for live generation. "
            + NO_CREDITS,
        )
    if len(ready) == 4:
        return (
            "Ready",
            "Grok Ready · Gemini Ready · ChatGPT Ready · Claude Ready. "
            f"{LEAVE_DUAL} {NO_CREDITS}",
        )
    bits = []
    if gx == "Ready":
        bits.append(f"Grok Ready. {gxm}")
    else:
        bits.append("Grok Off.")
    if gm == "Ready":
        bits.append(f"Gemini Ready. {gmm}")
    else:
        bits.append("Gemini Off.")
    if go == "Ready":
        bits.append(f"ChatGPT Ready. {gom}")
    else:
        bits.append("ChatGPT Off.")
    if gc == "Ready":
        bits.append(f"Claude Ready. {gcm}")
    else:
        bits.append("Claude Off.")
    return "Partial", f"{' '.join(bits)} {NO_CREDITS}"


def leave_notice(provider: str) -> str:
    provider = normalize_provider(provider)
    if provider == PROVIDER_GROK:
        return LEAVE_XAI
    if provider == PROVIDER_GEMINI:
        return LEAVE_GEMINI
    if provider == PROVIDER_OPENAI:
        return LEAVE_OPENAI
    if provider == PROVIDER_CLAUDE:
        return LEAVE_ANTHROPIC
    if provider == PROVIDER_DUAL:
        return LEAVE_DUAL
    return "Prompt pack stays on this machine until you generate with a key."


def writing_api_markdown() -> str:
    gx, gxm = probe_xai()
    gm, gmm = probe_gemini()
    go, gom = probe_openai()
    gc, gcm = probe_anthropic()
    overall, _ = probe_writing_api()
    return (
        f"**Writing backends: {overall}** — {NO_CREDITS}\n\n"
        f"- **Grok (xAI):** {gx} — {gxm}\n"
        f"- **Gemini (Google):** {gm} — {gmm}\n"
        f"- **ChatGPT (OpenAI):** {go} — {gom}\n"
        f"- **Claude (Anthropic):** {gc} — {gcm}\n"
        f"- **Local templates:** always on. Build a prompt pack and paste from any chat.\n"
        "When you Generate with Grok, Gemini, ChatGPT, Claude, or Dual, the text leaves "
        "this machine to that provider. Film Lab does not meter, quota, or resell those calls."
    )


def dual_missing_keys(dual_roles: str) -> list[str]:
    first, second, _ = _dual_pair(normalize_dual_roles(dual_roles))
    return _missing_named_keys(first, second)


def _http_json(url: str, payload: dict[str, Any], headers: dict[str, str], *, label: str) -> dict[str, Any]:
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        hint = ""
        if exc.code == 404:
            hint = (
                " Model id not found — set FILM_LAB_XAI_MODEL, FILM_LAB_GEMINI_MODEL, "
                "FILM_LAB_OPENAI_MODEL, or FILM_LAB_ANTHROPIC_MODEL to an id your account lists."
            )
        raise RuntimeError(f"{label} HTTP {exc.code}: {detail}.{hint}") from exc
    except URLError as exc:
        raise RuntimeError(f"{label} request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"{label} request timed out.") from exc
    if not isinstance(raw, dict):
        raise RuntimeError(f"{label} response was not JSON object.")
    return raw


def complete_xai(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.85,
    model: str | None = None,
) -> str:
    key = get_xai_key()
    if not key:
        raise RuntimeError(
            "Grok is Off. Set FILM_LAB_XAI_API_KEY (or XAI_API_KEY). No Film Lab credits."
        )
    mid = (model or "").strip() or xai_model()
    raw = _http_json(
        f"{xai_base()}/chat/completions",
        {
            "model": mid,
            "messages": messages,
            "temperature": temperature,
        },
        {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "film-lab-writing-studio",
        },
        label="xAI",
    )
    choices = raw.get("choices")
    if not choices:
        raise RuntimeError("xAI response had no choices.")
    message = choices[0].get("message") or {}
    text = (message.get("content") or "").strip()
    if not text:
        raise RuntimeError("xAI response was empty.")
    return text


def complete_openai(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.85,
    model: str | None = None,
) -> str:
    key = get_openai_key()
    if not key:
        raise RuntimeError(
            "ChatGPT is Off. Set FILM_LAB_OPENAI_API_KEY (or OPENAI_API_KEY). No Film Lab credits."
        )
    mid = (model or "").strip() or openai_model()
    payload: dict[str, Any] = {
        "model": mid,
        "messages": messages,
    }
    if not mid.startswith("o1"):
        payload["temperature"] = temperature
    raw = _http_json(
        f"{openai_base()}/chat/completions",
        payload,
        {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "film-lab-writing-studio",
        },
        label="OpenAI",
    )
    choices = raw.get("choices")
    if not choices:
        raise RuntimeError("OpenAI response had no choices.")
    message = choices[0].get("message") or {}
    text = (message.get("content") or "").strip()
    if not text:
        raise RuntimeError("OpenAI response was empty.")
    return text


def messages_to_gemini(messages: list[dict[str, str]]) -> tuple[str, list[dict[str, Any]]]:
    """Split system text and map chat roles to Gemini user/model contents."""
    system_bits: list[str] = []
    contents: list[dict[str, Any]] = []
    for msg in messages:
        role = (msg.get("role") or "user").lower()
        text = (msg.get("content") or "").strip()
        if not text:
            continue
        if role == "system":
            system_bits.append(text)
            continue
        gem_role = "model" if role == "assistant" else "user"
        if contents and contents[-1]["role"] == gem_role:
            contents[-1]["parts"][0]["text"] += "\n\n" + text
        else:
            contents.append({"role": gem_role, "parts": [{"text": text}]})
    if not contents:
        contents.append({"role": "user", "parts": [{"text": "(continue)"}]})
    return "\n\n".join(system_bits), contents


def complete_gemini(messages: list[dict[str, str]], *, temperature: float = 0.85) -> str:
    key = get_gemini_key()
    if not key:
        raise RuntimeError(
            "Gemini is Off. Set FILM_LAB_GEMINI_API_KEY (or GEMINI_API_KEY / GOOGLE_API_KEY). "
            "No Film Lab credits."
        )
    system, contents = messages_to_gemini(messages)
    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"temperature": temperature},
        "safetySettings": GEMINI_SAFETY,
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    model = gemini_model()
    raw = _http_json(
        f"{gemini_base()}/models/{model}:generateContent",
        payload,
        {
            "x-goog-api-key": key,
            "Content-Type": "application/json",
            "User-Agent": "film-lab-writing-studio",
        },
        label="Gemini",
    )
    cands = raw.get("candidates") or []
    if not cands:
        feedback = raw.get("promptFeedback") or raw.get("error") or raw
        raise RuntimeError(f"Gemini returned no candidates: {str(feedback)[:400]}")
    parts = ((cands[0].get("content") or {}).get("parts")) or []
    text = "".join(str(p.get("text") or "") for p in parts).strip()
    if not text:
        raise RuntimeError("Gemini response was empty.")
    return text


def messages_to_anthropic(messages: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    """Split system text and keep user/assistant turns for the Messages API."""
    system_bits: list[str] = []
    out: list[dict[str, str]] = []
    for msg in messages:
        role = (msg.get("role") or "user").lower()
        text = (msg.get("content") or "").strip()
        if not text:
            continue
        if role == "system":
            system_bits.append(text)
            continue
        anth_role = "assistant" if role == "assistant" else "user"
        if out and out[-1]["role"] == anth_role:
            out[-1]["content"] += "\n\n" + text
        else:
            out.append({"role": anth_role, "content": text})
    if not out:
        out.append({"role": "user", "content": "(continue)"})
    if out[0]["role"] != "user":
        out.insert(0, {"role": "user", "content": "(continue)"})
    return "\n\n".join(system_bits), out


def complete_anthropic(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.85,
    model: str | None = None,
) -> str:
    key = get_anthropic_key()
    if not key:
        raise RuntimeError(
            "Claude is Off. Set FILM_LAB_ANTHROPIC_API_KEY (or ANTHROPIC_API_KEY). "
            "No Film Lab credits."
        )
    mid = (model or "").strip() or anthropic_model()
    system, contents = messages_to_anthropic(messages)
    payload: dict[str, Any] = {
        "model": mid,
        "max_tokens": 4096,
        "temperature": temperature,
        "messages": contents,
    }
    if system:
        payload["system"] = system
    raw = _http_json(
        f"{anthropic_base()}/messages",
        payload,
        {
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "film-lab-writing-studio",
        },
        label="Anthropic",
    )
    blocks = raw.get("content") or []
    text = "".join(
        str(block.get("text") or "") for block in blocks if isinstance(block, dict)
    ).strip()
    if not text:
        raise RuntimeError("Anthropic response was empty.")
    return text


def complete_named(name: str, messages: list[dict[str, str]], *, temperature: float = 0.85) -> str:
    if name == "gemini":
        return complete_gemini(messages, temperature=temperature)
    if name == "openai":
        return complete_openai(messages, temperature=temperature)
    if name == "anthropic":
        return complete_anthropic(messages, temperature=temperature)
    return complete_xai(messages, temperature=temperature)


def _spine_instruction(mode: str) -> str:
    base = (
        "FIRST PASS — story spine only. Adults 18+ only. "
        "Do not write high-school or teen-appearing sex. "
    )
    if mode == "screenplay":
        return base + "Numbered beats, headings, blocking. Hold full dialogue for the second pass."
    if mode == "novel":
        return base + "Chapter / scene outline and emotional turns. Hold finished prose for the second pass."
    if mode == "book_to_screenplay":
        return base + "Numbered adaptation breakdown. Hold Fountain pages for the second pass."
    if mode == "roleplay":
        return (
            base + "Situation spine: what each adult wants this take. "
            "Hold in-character lines for the second pass."
        )
    if mode == "director_rewrite":
        return base + "What changes and why. Hold the rewritten scene for the second pass."
    return base + "Outline only."


def _expand_instruction(mode: str) -> str:
    return (
        "SECOND PASS — expand the spine into finished pages for this mode "
        f"({mode}). Dialogue, roleplay, and playable talk are yours. "
        "Keep the locked adult bible. Adults 18+ only. No minors."
    )


def _rewrite_instruction(mode: str) -> str:
    return (
        "SECOND PASS — rewrite the draft below for voice, dialogue, and this mode "
        f"({mode}). Keep structure that works. Adults 18+ only."
    )


def run_generation(
    messages: list[dict[str, str]],
    *,
    provider: str,
    dual_roles: str,
    mode: str,
    api_model: str = "",
) -> tuple[str, str, str]:
    """Return (body, model_label, spine). Local provider must not be passed here."""
    provider = normalize_provider(provider)
    dual_roles = normalize_dual_roles(dual_roles)
    mid = (api_model or "").strip()
    if provider == PROVIDER_GROK:
        used = mid or xai_model()
        return complete_xai(messages, model=used), f"xAI:{used}", ""
    if provider == PROVIDER_GEMINI:
        return complete_gemini(messages), f"Gemini:{gemini_model()}", ""
    if provider == PROVIDER_OPENAI:
        used = mid or openai_model()
        return complete_openai(messages, model=used), f"OpenAI:{used}", ""
    if provider == PROVIDER_CLAUDE:
        used = mid or anthropic_model()
        return complete_anthropic(messages, model=used), f"Anthropic:{used}", ""
    if provider != PROVIDER_DUAL:
        raise RuntimeError(
            "Pick Grok, Gemini, ChatGPT, Claude, or Dual to generate. "
            "Local templates stay on-box."
        )

    first, second, first_kind = _dual_pair(dual_roles)
    missing = _missing_named_keys(first, second)
    if missing:
        raise RuntimeError(
            "Dual needs the keys for the two roles you pick. Missing: "
            + ", ".join(missing)
            + ". Off is not an error — the rest of the studio still works. No Film Lab credits."
        )

    if dual_roles in {DUAL_COMPARE, DUAL_COMPARE_OPENAI_GROK}:
        a = complete_named(first, messages)
        b = complete_named(second, messages)
        body = (
            f"## {_named_label(first)}\n\n{a}\n\n"
            f"## {_named_label(second)}\n\n{b}"
        )
        return body, f"{_named_label(first)} + {_named_label(second)}", ""

    extra = _spine_instruction(mode) if first_kind == "spine" else (
        "FIRST PASS — write a complete draft for this mode. Adults 18+ only."
    )
    first_msgs = list(messages) + [{"role": "user", "content": extra}]
    spine = complete_named(first, first_msgs)
    second_extra = (
        f"{_expand_instruction(mode) if first_kind == 'spine' else _rewrite_instruction(mode)}\n\n"
        f"--- {first} pass ---\n{spine}"
    )
    second_msgs = list(messages) + [{"role": "user", "content": second_extra}]
    body = complete_named(second, second_msgs)
    label = f"{_named_label(first)} → {_named_label(second)}"
    return body, label, spine


def _named_label(name: str) -> str:
    if name == "gemini":
        return f"Gemini:{gemini_model()}"
    if name == "openai":
        return f"OpenAI:{openai_model()}"
    if name == "anthropic":
        return f"Anthropic:{anthropic_model()}"
    return f"xAI:{xai_model()}"


def _missing_named_keys(*names: str) -> list[str]:
    missing: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        if name == "gemini" and not get_gemini_key():
            missing.append("FILM_LAB_GEMINI_API_KEY (or GEMINI_API_KEY / GOOGLE_API_KEY)")
        elif name == "openai" and not get_openai_key():
            missing.append("FILM_LAB_OPENAI_API_KEY (or OPENAI_API_KEY)")
        elif name == "anthropic" and not get_anthropic_key():
            missing.append("FILM_LAB_ANTHROPIC_API_KEY (or ANTHROPIC_API_KEY)")
        elif name == "grok" and not get_xai_key():
            missing.append("FILM_LAB_XAI_API_KEY (or XAI_API_KEY)")
    return missing


def _dual_pair(dual_roles: str) -> tuple[str, str, str]:
    """Return (first, second, first_kind) where first_kind is spine|full|compare."""
    if dual_roles == DUAL_GROK_SPINE:
        return "grok", "gemini", "spine"
    if dual_roles == DUAL_GEMINI_THEN_GROK:
        return "gemini", "grok", "full"
    if dual_roles == DUAL_GROK_THEN_GEMINI:
        return "grok", "gemini", "full"
    if dual_roles == DUAL_COMPARE:
        return "gemini", "grok", "compare"
    if dual_roles == DUAL_OPENAI_GROK:
        return "openai", "grok", "spine"
    if dual_roles == DUAL_OPENAI_GEMINI:
        return "openai", "gemini", "spine"
    if dual_roles == DUAL_OPENAI_THEN_GROK:
        return "openai", "grok", "full"
    if dual_roles == DUAL_COMPARE_OPENAI_GROK:
        return "openai", "grok", "compare"
    return "gemini", "grok", "spine"
