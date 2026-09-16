"""Film Lab CLI stub — personal use, this machine only.

Original Film Lab package: film-lab-cli (invoke as `python -m film_lab.cli`).
Not a hosted video-product CLI. No account login. Zero Film Lab credits.

    python -m film_lab.cli init
    python -m film_lab.cli skills
"""

from __future__ import annotations

import sys

PACKAGE_NAME = "film-lab-cli"
INVOKE = "python -m film_lab.cli"
SKILLS_CMD = "python -m film_lab.cli skills"
DESK_URL = "http://127.0.0.1:43123"


def init_text() -> str:
    return (
        f"{PACKAGE_NAME} init — local Film Lab desk at {DESK_URL}\n"
        "No hosted sign-in. No Film Lab credits. Optional keys you already own:\n"
        "  FILM_LAB_ANTHROPIC_API_KEY / ANTHROPIC_API_KEY\n"
        "  FILM_LAB_OPENAI_API_KEY / OPENAI_API_KEY\n"
        "  FILM_LAB_XAI_API_KEY / XAI_API_KEY\n"
        f"Next: {SKILLS_CMD}\n"
        "Then generate from Writing Studio or Motion Desk on this PC.\n"
    )


def skills_text() -> str:
    return (
        f"{PACKAGE_NAME} skills — companion notes for Claude Code / OpenClaw / Hermes.\n"
        "Tools (planned local MCP): list_projects, list_shots, generate_shot, "
        "write_draft, list_connectors, enhance_prompt.\n"
        f"Desk: {DESK_URL}. Bind 127.0.0.1 only.\n"
        "See docs/DIRECTOR_BRIDGE.md and docs/cli/SKILLS.md.\n"
        "Zero Film Lab credits. Not a paid cloud.\n"
    )


def help_text() -> str:
    return (
        f"{PACKAGE_NAME} — Film Lab original CLI stub\n"
        f"  {INVOKE} init     write local desk pointer\n"
        f"  {INVOKE} skills   print companion skill notes\n"
        f"  {INVOKE} help     this text\n"
        "Personal use. No hosted auth. Zero credits.\n"
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = (args[0] if args else "help").strip().lower()
    if cmd in {"init", "setup"}:
        print(init_text(), end="")
        return 0
    if cmd in {"skills", "skill"}:
        print(skills_text(), end="")
        return 0
    print(help_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
