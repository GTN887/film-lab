"""Project Save Library — browse local shelves; optional Drive folder backup.

Local-first. OneDrive / Google Drive are optional folder paths (desktop sync
clients). Film Lab does not log into those services. Offline: the local library
still works. Zero credits.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from film_lab.project import IMAGE_SUFFIXES, VIDEO_SUFFIXES, Project, default_data_root

SHELVES: tuple[str, ...] = ("Stills", "Takes", "Sets", "Writing", "Exports")
DEFAULT_SHELF = "Stills"

_SHELF_DIR: dict[str, str] = {
    "Stills": "stills",
    "Takes": "takes",
    "Sets": "sets",
    "Writing": "writing",
    "Exports": "outputs",
}

BACKUP_FOLDERS: tuple[str, ...] = ("stills", "takes", "sets", "writing", "outputs")
DRIVE_DEST_NAME = "Film Lab"
SYNC_FILENAME = "drive_sync.json"

WRITING_SUFFIXES = {".txt", ".md", ".fountain", ".docx", ".pdf", ".pptx", ".xlsx"}


@dataclass(frozen=True)
class LibraryItem:
    name: str
    shelf: str
    rel: str
    path: str
    size: int
    updated: str


@dataclass
class SyncConfig:
    onedrive: str = ""
    gdrive: str = ""
    last_backup: str = ""


def sync_config_path(data_root: Path | None = None) -> Path:
    root = (data_root or default_data_root()).parent
    return root / SYNC_FILENAME


def load_sync_config(data_root: Path | None = None) -> SyncConfig:
    path = sync_config_path(data_root)
    if not path.is_file():
        return SyncConfig()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return SyncConfig()
    if not isinstance(raw, dict):
        return SyncConfig()
    return SyncConfig(
        onedrive=str(raw.get("onedrive") or "").strip(),
        gdrive=str(raw.get("gdrive") or "").strip(),
        last_backup=str(raw.get("last_backup") or "").strip(),
    )


def save_sync_config(cfg: SyncConfig, data_root: Path | None = None) -> Path:
    path = sync_config_path(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "onedrive": cfg.onedrive,
                "gdrive": cfg.gdrive,
                "last_backup": cfg.last_backup,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def shelf_dir(project: Project, shelf: str) -> Path:
    key = _SHELF_DIR.get((shelf or DEFAULT_SHELF).strip(), "stills")
    return project.root / key


def list_shelf(project: Project, shelf: str) -> list[LibraryItem]:
    """Browse one local shelf. Empty folder is a valid empty library."""
    name = (shelf or DEFAULT_SHELF).strip()
    if name not in SHELVES:
        name = DEFAULT_SHELF
    folder = shelf_dir(project, name)
    if not folder.exists():
        return []
    items: list[LibraryItem] = []
    for path in folder.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        rel = str(path.relative_to(folder)).replace("\\", "/")
        try:
            stat = path.stat()
        except OSError:
            continue
        stamp = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M"
        )
        items.append(
            LibraryItem(
                name=path.name,
                shelf=name,
                rel=rel,
                path=str(path),
                size=int(stat.st_size),
                updated=stamp,
            )
        )
    items.sort(key=lambda item: item.updated, reverse=True)
    return items


def table_rows(items: list[LibraryItem]) -> list[list[str]]:
    rows: list[list[str]] = []
    for item in items:
        kb = max(1, item.size // 1024) if item.size else 0
        rows.append([item.name, item.shelf, item.rel, f"{kb} KB", item.updated])
    return rows


def preview_paths(items: list[LibraryItem], limit: int = 24) -> list[str]:
    out: list[str] = []
    media = IMAGE_SUFFIXES | VIDEO_SUFFIXES
    for item in items:
        suffix = Path(item.path).suffix.lower()
        if suffix in media:
            out.append(item.path)
        if len(out) >= limit:
            break
    return out


def folder_status(path: str | None) -> str:
    text = (path or "").strip()
    if not text:
        return "off"
    if Path(text).expanduser().is_dir():
        return "ready"
    return "missing"


def suggest_drive_folders() -> tuple[str, str]:
    """Best-effort local OneDrive / Google Drive folders. Empty if none."""
    home = Path.home()
    one_hits = (
        home / "OneDrive",
        home / "OneDrive - Personal",
        Path.home() / "OneDrive" / "Documents",
    )
    g_hits = (
        home / "Google Drive",
        home / "GoogleDrive",
        home / "My Drive",
    )
    one = next((str(p) for p in one_hits if p.is_dir()), "")
    gdrive = next((str(p) for p in g_hits if p.is_dir()), "")
    return one, gdrive


def connect_folder(kind: str, path: str, data_root: Path | None = None) -> tuple[str, str]:
    """Save a Drive folder path. Does not log in. Missing folder → honest miss."""
    cfg = load_sync_config(data_root)
    cleaned = str(path or "").strip()
    key = "gdrive" if (kind or "").lower().startswith("g") else "onedrive"
    if cleaned:
        resolved = str(Path(cleaned).expanduser())
        setattr(cfg, key, resolved)
    else:
        setattr(cfg, key, "")
    save_sync_config(cfg, data_root)
    status = folder_status(getattr(cfg, key))
    label = "Google Drive" if key == "gdrive" else "OneDrive"
    if status == "off":
        return getattr(cfg, key), f"{label} disconnected. Local library stays."
    if status == "missing":
        return (
            getattr(cfg, key),
            f"{label} folder missing — Drive may be offline. Local files stay. "
            "Connect again when the desktop folder is online.",
        )
    return getattr(cfg, key), f"{label} folder ready. Optional backup only. Local-first."


def _copy_tree(src: Path, dest: Path) -> int:
    if not src.exists():
        return 0
    copied = 0
    dest.mkdir(parents=True, exist_ok=True)
    for path in src.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        rel = path.relative_to(src)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    return copied


def backup_project(
    project: Project,
    *,
    onedrive: str = "",
    gdrive: str = "",
    data_root: Path | None = None,
) -> str:
    """Copy stills / takes / sets / writing / exports into connected Drive folders.

    Local files are the source of truth. A missing Drive folder is skipped.
    """
    cfg = load_sync_config(data_root)
    one = (onedrive or cfg.onedrive).strip()
    gdest = (gdrive or cfg.gdrive).strip()
    targets: list[tuple[str, Path]] = []
    notes: list[str] = []
    for label, raw in (("OneDrive", one), ("Google Drive", gdest)):
        status = folder_status(raw)
        if status == "off":
            notes.append(f"{label}: not connected.")
            continue
        if status == "missing":
            notes.append(
                f"{label}: folder missing (offline or unmounted). "
                "Local library stays. Retry when online."
            )
            continue
        targets.append((label, Path(raw).expanduser() / DRIVE_DEST_NAME / project.name))

    if not targets:
        return (
            "No Drive folder ready. Local Save Library is the source of truth. "
            + " ".join(notes)
        )

    copied = 0
    for label, dest_root in targets:
        batch = 0
        for folder in BACKUP_FOLDERS:
            src = project.root / folder
            dest_name = "exports" if folder == "outputs" else folder
            batch += _copy_tree(src, dest_root / dest_name)
        copied += batch
        notes.append(f"{label}: wrote {batch} file(s) under `{dest_root}`.")

    cfg.onedrive = one
    cfg.gdrive = gdest
    cfg.last_backup = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    save_sync_config(cfg, data_root)
    return (
        f"Backup finished. {copied} file(s) copied. Local-first — Drive is optional. "
        + " ".join(notes)
    )


def status_markdown(cfg: SyncConfig | None = None, data_root: Path | None = None) -> str:
    cfg = cfg or load_sync_config(data_root)
    one = folder_status(cfg.onedrive)
    gdrive = folder_status(cfg.gdrive)
    last = cfg.last_backup or "never"
    return (
        f"**Local:** `data/projects/<lot>/` — stills, takes, sets, writing, exports.\n\n"
        f"**OneDrive:** {one}. `{cfg.onedrive or '—'}`\n\n"
        f"**Google Drive:** {gdrive}. `{cfg.gdrive or '—'}`\n\n"
        f"**Last backup:** {last}\n\n"
        "Local-first. Drive is optional when online. No Film Lab login to either service."
    )


def library_help() -> str:
    return (
        "### Project Save Library — this PC first\n"
        "Browse **stills / takes / sets / writing** (plus exports) in the current lot. "
        "Nothing is uploaded.\n\n"
        "**Optional backup.** Paste a OneDrive and/or Google Drive **folder** that the "
        "desktop app already syncs. Film Lab copies movies, images, and exports there "
        "if you ask — useful when a local disk hiccups. If the folder is missing "
        "(Drive offline), the toast says so and the local library stays.\n\n"
        "No credits. No hosted Drive API. Connect only when you want a second copy."
    )
