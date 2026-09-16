"""Film Lab local MCP stub — personal use, localhost only.

This is not a hosted third-party MCP and not a paid subscription.
A later stdio server will expose TOOL_MANIFEST. Today this module prints
the stub so Claude Code, OpenClaw, Hermes, or Cursor can be pointed here.

    python -m film_lab.mcp_stub
"""

from __future__ import annotations

import json
import sys

from film_lab.bridge import mcp_stub


def main(argv: list[str] | None = None) -> int:
    del argv
    print(json.dumps(mcp_stub(), indent=2))
    print(
        "Coming soon: long-running stdio MCP. Film Lab stays on 127.0.0.1. "
        "Zero credits. Not a paid cloud.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
