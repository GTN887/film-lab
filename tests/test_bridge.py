#!/usr/bin/env python3
"""Director Bridge connectors, local MCP/CLI stub, no paid third-party."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.bridge import (
    AGENT_TAB_LABELS,
    BRIDGE_MODES,
    CONNECTORS,
    TOOL_MANIFEST,
    agent_panel_html,
    bridge_markdown,
    connect_connector,
    connector_labels,
    connector_status,
    connectors_html,
    connectors_status_markdown,
    mcp_stub,
    mcp_stub_pretty,
    setup_prompt,
)
from film_lab.cli import INVOKE, PACKAGE_NAME, init_text, skills_text
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.llm import PROVIDER_CLAUDE, get_anthropic_key, probe_anthropic


class BridgeConnectorTests(unittest.TestCase):
    def setUp(self) -> None:
        for key in (
            "FILM_LAB_ANTHROPIC_API_KEY",
            "ANTHROPIC_API_KEY",
            "FILM_LAB_OPENAI_API_KEY",
            "OPENAI_API_KEY",
            "FILM_LAB_XAI_API_KEY",
            "XAI_API_KEY",
        ):
            os.environ.pop(key, None)

    def test_shelf_order_and_labels(self) -> None:
        names = [c.name for c in CONNECTORS]
        self.assertEqual(
            names,
            [
                "ChatGPT",
                "Claude",
                "Grok Bot",
                "Cursor",
                "Claude Code",
                "OpenClaw",
                "Hermes",
            ],
        )
        self.assertEqual(list(AGENT_TAB_LABELS), names)
        self.assertEqual(connector_labels(), names)
        self.assertEqual(tuple(BRIDGE_MODES), ("MCP", "CLI"))

    def test_claude_off_without_key(self) -> None:
        self.assertIsNone(get_anthropic_key())
        self.assertEqual(probe_anthropic()[0], "Off")
        claude = next(c for c in CONNECTORS if c.id == "claude")
        badge, detail = connector_status(claude)
        self.assertEqual(badge, "Off")
        self.assertIn("ANTHROPIC", detail.upper())
        self.assertNotIn("sk-", detail.lower())

    def test_openclaw_hermes_never_ready(self) -> None:
        for cid in ("openclaw", "hermes"):
            item = next(c for c in CONNECTORS if c.id == cid)
            badge, detail = connector_status(item)
            self.assertEqual(badge, "Coming soon")
            self.assertNotEqual(badge, "Ready")
            note = connect_connector(item.name, "CLI")
            self.assertIn("Coming soon", note)
            self.assertNotIn("**Ready**", note)
            self.assertIn("will not fake", note.lower() + detail.lower())

    def test_cursor_and_claude_code_are_local(self) -> None:
        cursor = next(c for c in CONNECTORS if c.id == "cursor")
        self.assertEqual(connector_status(cursor)[0], "Local")
        self.assertIn("127.0.0.1", connect_connector("Cursor", "MCP"))
        code = next(c for c in CONNECTORS if c.id == "claude-code")
        self.assertEqual(connector_status(code)[0], "Local")
        note = connect_connector("Claude Code", "CLI")
        self.assertIn("film_lab.cli", note)
        self.assertIn("will not open a hosted sign-in", note.lower())

    def test_html_and_markdown_clean(self) -> None:
        html = connectors_html() + agent_panel_html("Claude Code", "CLI")
        md = connectors_status_markdown() + bridge_markdown()
        for name in AGENT_TAB_LABELS:
            self.assertIn(name, html + md)
        blob = (html + md + mcp_stub_pretty() + setup_prompt("Claude Code", "CLI")).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, blob, banned)
        self.assertNotIn("sk-", blob)
        self.assertNotIn("npm i -g", blob)
        self.assertIn("no credits", md.lower() + bridge_markdown().lower())
        self.assertIn("claude code", bridge_markdown().lower())
        self.assertIn("mcp", bridge_markdown().lower())
        self.assertIn("cli", bridge_markdown().lower())

    def test_claude_code_cli_two_step_prompt(self) -> None:
        prompt = setup_prompt("Claude Code", "CLI")
        panel = agent_panel_html("Claude Code", "CLI").lower()
        self.assertIn(PACKAGE_NAME, prompt)
        self.assertIn(INVOKE, prompt)
        self.assertIn("film_lab.cli", prompt)
        self.assertIn("127.0.0.1:43123", prompt)
        self.assertIn("do not install a hosted", prompt.lower())
        self.assertIn("no credits", prompt.lower())
        self.assertIn("copy this prompt", panel)
        self.assertIn("film lab cli and skills", panel)
        self.assertIn("connect and start creating", panel)
        mcp = setup_prompt("Claude Code", "MCP")
        self.assertIn("film_lab.mcp_stub", mcp)
        self.assertIn("127.0.0.1", mcp)
        self.assertNotIn("https://", mcp.lower())

    def test_mcp_stub_and_cli(self) -> None:
        stub = mcp_stub()
        self.assertEqual(stub["name"], "film-lab")
        self.assertEqual(stub["bind"], "127.0.0.1")
        self.assertEqual(stub["cli_package"], PACKAGE_NAME)
        names = {t["name"] for t in stub["tools"]}
        self.assertTrue({"list_projects", "write_draft", "list_connectors"} <= names)
        self.assertIn("OpenClaw", stub["clients"])
        self.assertIn("Claude Code", stub["clients"])
        self.assertIn("Grok Bot", stub["clients"])
        proc = subprocess.run(
            [sys.executable, "-m", "film_lab.mcp_stub"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        printed = json.loads(proc.stdout)
        self.assertEqual(printed["name"], "film-lab")
        self.assertIn("coming soon", proc.stderr.lower())
        cli = subprocess.run(
            [sys.executable, "-m", "film_lab.cli", "init"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(cli.returncode, 0)
        self.assertIn(PACKAGE_NAME, cli.stdout)
        self.assertIn("127.0.0.1:43123", cli.stdout)
        self.assertIn("no film lab credits", cli.stdout.lower())
        self.assertIn(PACKAGE_NAME, init_text())
        self.assertIn("skills", skills_text().lower())

    def test_tools_and_claude_provider_constant(self) -> None:
        names = {t["name"] for t in TOOL_MANIFEST}
        self.assertIn("generate_shot", names)
        self.assertIn("enhance_prompt", names)
        self.assertEqual(PROVIDER_CLAUDE, "Claude (Anthropic)")


if __name__ == "__main__":
    unittest.main()
