"""Shared ids and tiny helpers."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(name: str, fallback: str = "item") -> str:
    slug = _SAFE_NAME.sub("-", name.strip().lower()).strip("-")
    return slug or fallback


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
