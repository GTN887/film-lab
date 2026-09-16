# Director Bridge

Local agent page for Film Lab on this PC. **Not a hosted plugin. Not a credit meter. Not a paid subscription.**

The desk tab lists:

**ChatGPT | Claude | Grok Bot | Cursor | Claude Code | OpenClaw | Hermes**

plus an **MCP / CLI** toggle.

See the **Director Bridge** tab, `film_lab/bridge.py`, and `python -m film_lab.cli`.

## Connectors

| Agent | Status today | What it is |
| --- | --- | --- |
| **ChatGPT** | Ready with `FILM_LAB_OPENAI_API_KEY` or `OPENAI_API_KEY` | Writing + enhance. Your key. |
| **Claude** | Ready with `FILM_LAB_ANTHROPIC_API_KEY` or `ANTHROPIC_API_KEY` | Writing + enhance. Your key. |
| **Grok Bot** | Ready with `FILM_LAB_XAI_API_KEY` or `XAI_API_KEY` | Writing + enhance. Your key. |
| **Cursor** | Local | This Gradio desk + `docs/mcp/film-lab.mcp.json`. |
| **Claude Code** | Local CLI stub | Two-step: copy Film Lab setup prompt, then Connect and start creating. |
| **OpenClaw** | Coming soon | MCP / CLI **client** for a future Film Lab local server. Never Ready until that process exists. |
| **Hermes** | Coming soon | Same client target. |

Film Lab never sells tokens. A missing key leaves that writing connector **Off**. The rest of the studio still works.

## Claude Code CLI (two steps)

1. **Copy this prompt** and paste it into Claude Code to install Film Lab CLI and skills.
2. **Connect and start creating.**

Package name is **film-lab-cli** (`python -m film_lab.cli`). It is **not** a hosted npm CLI. No browser login. No Film Lab credits.

```bash
python -m film_lab.cli init
python -m film_lab.cli skills
```

Skill notes: [cli/SKILLS.md](cli/SKILLS.md).

## MCP toggle

```bash
python -m film_lab.mcp_stub
```

When a client wants stdio:

```bash
claude mcp add --transport stdio --scope user film-lab -- python -m film_lab.mcp_stub
```

Or drop [mcp/film-lab.mcp.json](mcp/film-lab.mcp.json) into the client. Bind is `127.0.0.1` only. Not a hosted MCP URL.

## OpenClaw and Hermes

Point those MCP **clients** at Film Lab's future local server. They stay **Coming soon** until that stdio process ships. Connect will not fake a live session.

## Planned local tools

`list_projects`, `list_shots`, `generate_shot`, `write_draft`, `list_connectors`, `enhance_prompt`.

Optional cloud LLMs stay **keys you own**.
