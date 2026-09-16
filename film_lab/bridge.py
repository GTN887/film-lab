"""Director Bridge — Film Lab's own local agent page (MCP / CLI).

This is not a hosted MCP, not a third-party plugin, and not a paid agent.
A later local MCP can expose these tool names on 127.0.0.1 only.
Claude / ChatGPT / Grok Bot use keys you already own. OpenClaw and Hermes
are MCP *client* targets for that future local server — never Ready until
the process exists. Film Lab never sells seats or credits.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from typing import Any

from film_lab.cli import INVOKE, PACKAGE_NAME, SKILLS_CMD
from film_lab.llm import (
    NO_CREDITS,
    probe_anthropic,
    probe_openai,
    probe_xai,
)

TOOL_MANIFEST: list[dict[str, Any]] = [
    {
        "name": "list_projects",
        "summary": "List Film Lab project folders under ./data/projects/",
    },
    {
        "name": "list_shots",
        "summary": "List shot cards in the open project",
    },
    {
        "name": "generate_shot",
        "summary": "Run local AMD img2vid on the selected shot (ComfyUI sidecar)",
    },
    {
        "name": "write_draft",
        "summary": "Build or generate a Writing Studio draft with local templates or a key you own",
    },
    {
        "name": "list_connectors",
        "summary": "List Director Bridge connectors and their local Ready / Off / Coming soon status",
    },
    {
        "name": "enhance_prompt",
        "summary": "Expand a short idea with local templates or a key you own (Writing / Motion)",
    },
]

DESK_URL = "http://127.0.0.1:43123"
BRIDGE_MODES: tuple[str, ...] = ("MCP", "CLI")
DEFAULT_AGENT = "Claude Code"
DEFAULT_MODE = "CLI"


@dataclass(frozen=True)
class Connector:
    id: str
    name: str
    kind: str
    summary: str
    coming_soon: bool = False


# Tab order matches the agent integration page.
CONNECTORS: tuple[Connector, ...] = (
    Connector(
        id="chatgpt",
        name="ChatGPT",
        kind="writing",
        summary=(
            "Writing Studio + Prompt Enhance. Optional FILM_LAB_OPENAI_API_KEY "
            "or OPENAI_API_KEY. Your key only."
        ),
    ),
    Connector(
        id="claude",
        name="Claude",
        kind="writing",
        summary=(
            "Writing Studio + Prompt Enhance. Optional FILM_LAB_ANTHROPIC_API_KEY "
            "or ANTHROPIC_API_KEY. Your key — Film Lab never sells tokens."
        ),
    ),
    Connector(
        id="grok",
        name="Grok Bot",
        kind="writing",
        summary=(
            "Writing Studio + Prompt Enhance. Optional FILM_LAB_XAI_API_KEY "
            "or XAI_API_KEY. Your key only."
        ),
    ),
    Connector(
        id="cursor",
        name="Cursor",
        kind="local_ide",
        summary=(
            "This Gradio desk is already the Film Lab surface. Drop "
            "docs/mcp/film-lab.mcp.json into a local MCP client. Local."
        ),
    ),
    Connector(
        id="claude-code",
        name="Claude Code",
        kind="local_cli",
        summary=(
            "CLI tab: copy the Film Lab setup prompt, then Connect and start creating. "
            f"Package `{PACKAGE_NAME}` via `{INVOKE}`. Local stub. No hosted login."
        ),
    ),
    Connector(
        id="openclaw",
        name="OpenClaw",
        kind="mcp_client",
        coming_soon=True,
        summary=(
            "MCP / CLI client target for a future Film Lab local server "
            "(stdio / 127.0.0.1). Not Ready until that process exists. Not a paid cloud."
        ),
    ),
    Connector(
        id="hermes",
        name="Hermes",
        kind="mcp_client",
        coming_soon=True,
        summary=(
            "MCP / CLI client target for the same future Film Lab local server. "
            "Coming soon. Zero Film Lab credits."
        ),
    ),
)

AGENT_TAB_LABELS: tuple[str, ...] = tuple(item.name for item in CONNECTORS)

_last_connect: dict[str, str] = {}


def connector_by_id_or_name(value: str | None) -> Connector | None:
    needle = (value or "").strip()
    if not needle:
        return None
    low = needle.lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "grok-bot": "grok",
        "grok": "grok",
        "claude-code": "claude-code",
        "claudecode": "claude-code",
    }
    mapped = aliases.get(low, low)
    for item in CONNECTORS:
        if item.id == mapped or item.name.lower() == needle.lower():
            return item
    return None


def connector_labels() -> list[str]:
    return list(AGENT_TAB_LABELS)


def normalize_mode(value: str | None) -> str:
    text = (value or "").strip().upper()
    return text if text in BRIDGE_MODES else DEFAULT_MODE


def connector_status(item: Connector) -> tuple[str, str]:
    """Return (badge, detail). Never fakes Ready for a coming-soon MCP client."""
    if item.coming_soon:
        return (
            "Coming soon",
            item.summary + " Film Lab will not pretend this session is live.",
        )
    if item.id == "claude":
        state, detail = probe_anthropic()
        return state, detail
    if item.id == "chatgpt":
        state, detail = probe_openai()
        return state, detail
    if item.id == "grok":
        state, detail = probe_xai()
        return state, detail
    if item.kind in {"local_ide", "local_cli"}:
        return "Local", item.summary
    return "Off", item.summary


def connectors_status_markdown() -> str:
    lines = [
        "### Connector status",
        "",
        f"{NO_CREDITS}",
        "",
    ]
    for item in CONNECTORS:
        badge, detail = connector_status(item)
        extra = _last_connect.get(item.id)
        note = f" Last connect: {extra}" if extra else ""
        lines.append(f"- **{item.name}:** {badge} — {detail}{note}")
    lines.extend(
        [
            "",
            "OpenClaw and Hermes stay **Coming soon** until Film Lab ships a local "
            "stdio MCP process. Connect never marks them Ready.",
        ]
    )
    return "\n".join(lines)


def connectors_html() -> str:
    cards: list[str] = []
    for item in CONNECTORS:
        badge, detail = connector_status(item)
        tone = {
            "Ready": "ready",
            "Off": "off",
            "Local": "local",
            "Coming soon": "soon",
        }.get(badge, "off")
        cards.append(
            "<article class='fl-bridge-card'>"
            f"<div class='fl-bridge-kicker'>{html.escape(item.kind.replace('_', ' '))}</div>"
            f"<h3>{html.escape(item.name)}</h3>"
            f"<span class='fl-bridge-badge fl-bridge-{tone}'>{html.escape(badge)}</span>"
            f"<p>{html.escape(detail)}</p>"
            "</article>"
        )
    return (
        "<section class='fl-bridge-shelf' aria-label='Director Bridge connectors'>"
        "<div class='fl-bridge-grid'>"
        + "".join(cards)
        + "</div></section>"
    )


def setup_prompt(agent: str | None, mode: str | None = DEFAULT_MODE) -> str:
    """Copyable setup prompt. Film Lab original package — never a hosted CLI."""
    item = connector_by_id_or_name(agent) or connector_by_id_or_name(DEFAULT_AGENT)
    assert item is not None
    transport = normalize_mode(mode)
    if transport == "CLI":
        return _cli_setup_prompt(item)
    return _mcp_setup_prompt(item)


def _cli_setup_prompt(item: Connector) -> str:
    target = item.name
    return (
        f"Set up Film Lab for me so I can write pages and generate local shots from here.\n"
        f"\n"
        f"1. Install the Film Lab CLI stub: from the Film Lab repo run `{INVOKE} init`. "
        f"The package name is `{PACKAGE_NAME}` (Python module `film_lab.cli`). "
        f"Do not install a hosted video-product CLI.\n"
        f"2. Point tools at this machine only: `{DESK_URL}`. "
        f"Do not open a browser sign-in for a cloud studio. Film Lab has no credits "
        f"and does not require a paid subscription.\n"
        f"3. Install companion skills: run `{SKILLS_CMD}` "
        f"(notes in docs/cli/SKILLS.md).\n"
        f"\n"
        f"I am using **{target}**. Optional keys I already own may be in the environment "
        f"(FILM_LAB_ANTHROPIC_API_KEY, FILM_LAB_OPENAI_API_KEY, FILM_LAB_XAI_API_KEY). "
        f"Never paste secrets into chat.\n"
        f"\n"
        f"Once that's done, let me know when it's ready."
    )


def _mcp_setup_prompt(item: Connector) -> str:
    add_cmd = (
        "claude mcp add --transport stdio --scope user film-lab -- python -m film_lab.mcp_stub"
    )
    return (
        f"Add the **local Film Lab MCP stub** for {item.name}. "
        f"This is not a hosted cloud MCP and not a paid plugin.\n"
        f"\n"
        f"Print the stub:\n"
        f"  python -m film_lab.mcp_stub\n"
        f"\n"
        f"When you want a stdio client entry (Claude Code / Cursor / later OpenClaw):\n"
        f"  {add_cmd}\n"
        f"\n"
        f"Or drop `docs/mcp/film-lab.mcp.json` into the client's MCP config. "
        f"Bind is `127.0.0.1` only. Desk: `{DESK_URL}`.\n"
        f"\n"
        f"Zero Film Lab credits. Optional keys you already own stay in the environment. "
        f"Do not authenticate to a hosted video product."
    )


def agent_panel_html(agent: str | None = DEFAULT_AGENT, mode: str | None = DEFAULT_MODE) -> str:
    item = connector_by_id_or_name(agent) or connector_by_id_or_name(DEFAULT_AGENT)
    assert item is not None
    transport = normalize_mode(mode)
    badge, detail = connector_status(item)
    tone = {
        "Ready": "ready",
        "Off": "off",
        "Local": "local",
        "Coming soon": "soon",
    }.get(badge, "off")
    if transport == "CLI":
        step1_title = (
            f"Copy this prompt and paste it into {item.name} to install "
            "Film Lab CLI and skills"
        )
        step1_body = (
            f"Uses `{PACKAGE_NAME}` via `{INVOKE}`. Local stub on this PC. "
            "Not a hosted package. Zero Film Lab credits."
        )
        step2_title = "Connect and start creating"
        step2_body = (
            f"No hosted account. The desk is already at `{DESK_URL}`. "
            "Press Connect and start creating when the prompt is in the agent."
        )
    else:
        step1_title = f"Add the local Film Lab MCP stub in {item.name}"
        step1_body = (
            "stdio / 127.0.0.1 only. Copy the MCP command below. "
            "Not a hosted connector URL. Not a paid plugin."
        )
        step2_title = "Connect and start creating"
        step2_body = (
            f"{detail} Status stays honest — Coming soon clients never flip to Ready."
        )
    return (
        "<section class='fl-bridge-page' aria-label='Director Bridge agent'>"
        "<header class='fl-bridge-hero'>"
        "<p class='fl-bridge-kicker'>Director Bridge · agent page</p>"
        f"<h2>Connect {html.escape(item.name)}</h2>"
        "<p>Personal Film Lab MCP / CLI on this machine. Optional keys you already own. "
        "No hosted sign-in. No Film Lab credits.</p>"
        f"<span class='fl-bridge-badge fl-bridge-{tone}'>"
        f"{html.escape(transport)} · {html.escape(badge)}</span>"
        "</header>"
        "<ol class='fl-bridge-steps'>"
        "<li>"
        "<div class='fl-bridge-num'>1</div>"
        "<div>"
        f"<h3>{html.escape(step1_title)}</h3>"
        f"<p>{html.escape(step1_body)}</p>"
        "</div>"
        "</li>"
        "<li>"
        "<div class='fl-bridge-num'>2</div>"
        "<div>"
        f"<h3>{html.escape(step2_title)}</h3>"
        f"<p>{html.escape(step2_body)}</p>"
        "</div>"
        "</li>"
        "</ol>"
        "</section>"
    )


def connect_connector(value: str | None, mode: str | None = DEFAULT_MODE) -> str:
    """Refresh a connector. Coming-soon MCP clients stay Coming soon."""
    item = connector_by_id_or_name(value)
    transport = normalize_mode(mode)
    if item is None:
        return (
            "Pick ChatGPT, Claude, Grok Bot, Cursor, Claude Code, OpenClaw, or Hermes. "
            + NO_CREDITS
        )
    badge, detail = connector_status(item)
    if item.coming_soon:
        note = (
            f"**{item.name}** · {transport}: Coming soon. When Film Lab's local MCP "
            "process exists, point this client at stdio or `127.0.0.1` using "
            "`docs/mcp/film-lab.mcp.json` or the CLI stub (`python -m film_lab.cli init`). "
            "Not a paid cloud. Status stays Coming soon — Film Lab will not fake a session."
        )
        _last_connect[item.id] = f"Coming soon ({transport}, not Ready)"
        return note + "\n\n" + connectors_status_markdown()
    if item.kind == "local_cli":
        note = (
            f"**{item.name}** · {transport}: Local. Paste the setup prompt into the CLI, "
            f"then run `{INVOKE} init` and `{SKILLS_CMD}`. "
            f"Desk stays at `{DESK_URL}`. Film Lab will not open a hosted sign-in."
        )
        _last_connect[item.id] = f"Local {transport}"
        return note + "\n\n" + connectors_status_markdown()
    if item.kind == "local_ide":
        note = (
            f"**{item.name}** · {transport}: Local. This desk is already on `{DESK_URL}`. "
            "Use `docs/mcp/film-lab.mcp.json` for MCP, or the CLI stub for CLI mode."
        )
        _last_connect[item.id] = f"Local {transport}"
        return note + "\n\n" + connectors_status_markdown()
    note = (
        f"**{item.name}** · {transport}: {badge}. {detail} "
        "Connect re-reads your environment. Never paste a key into this page."
    )
    _last_connect[item.id] = f"{badge} {transport}"
    return note + "\n\n" + connectors_status_markdown()


def mcp_stub() -> dict[str, Any]:
    """Local Film Lab MCP document. Personal use. Localhost only."""
    return {
        "name": "film-lab",
        "version": "1.0.0",
        "description": (
            "Local Film Lab tools on this machine. Not a hosted third-party MCP. "
            "Zero Film Lab credits. Not a paid subscription."
        ),
        "transport": "stdio (planned)",
        "bind": "127.0.0.1",
        "port_note": f"The Gradio desk stays at {DESK_URL}",
        "cli_package": PACKAGE_NAME,
        "cli_invoke": INVOKE,
        "clients": list(AGENT_TAB_LABELS),
        "tools": TOOL_MANIFEST,
        "connectors": [
            {
                "id": item.id,
                "name": item.name,
                "kind": item.kind,
                "status": connector_status(item)[0],
                "coming_soon": item.coming_soon,
            }
            for item in CONNECTORS
        ],
    }


def mcp_stub_pretty() -> str:
    return json.dumps(mcp_stub(), indent=2)


def bridge_markdown() -> str:
    lines = [
        "# Director Bridge",
        "",
        "A **local** agent page so ChatGPT, Claude, Grok Bot, Cursor, Claude Code, "
        "OpenClaw, and Hermes can sit on this PC. Toggle **MCP** or **CLI**. "
        "It is not a cloud plugin, not a credit meter, and not somebody else's MCP. "
        "No paid subscription is required.",
        "",
        "Claude / ChatGPT / Grok Bot turn **Ready** only when you set a key you already own. "
        "OpenClaw and Hermes stay Coming soon. Cursor and Claude Code are local stubs.",
        "",
        "Claude Code **CLI** is two steps: (1) copy the Film Lab setup prompt "
        f"(`{PACKAGE_NAME}` / `{INVOKE}` — not a hosted package) into the CLI, "
        "(2) Connect and start creating.",
        "",
        "CLI coding agents can call Film Lab the same way you do: "
        f"HTTP to `{DESK_URL}`, or tools from this manifest once the local MCP "
        "server exists. Film Lab does not sell seats to those products.",
        "",
        "## Planned local tools",
        "",
    ]
    for tool in TOOL_MANIFEST:
        lines.append(f"- `{tool['name']}` — {tool['summary']}")
    lines.extend(
        [
            "",
            "## How it will run (later)",
            "",
            f"1. Film Lab stays the desk at `{DESK_URL}`.",
            "2. An optional local process may speak MCP on localhost (stdio).",
            "3. Tools call the same generators you already use: ComfyUI img2vid, Writing Studio.",
            "4. Optional Grok / Gemini / ChatGPT / Claude keys remain **yours**. "
            "Film Lab never sells tokens.",
            "5. Point OpenClaw or Hermes at that local process when it exists — "
            "they are clients, not a hosted Film Lab cloud.",
            "",
            "Until that process exists, use the home cards by hand. You are the director.",
        ]
    )
    return "\n".join(lines)
