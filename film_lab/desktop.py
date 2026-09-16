"""Windows desktop program layout — shortcut, installer, no-PowerShell daily start.

Daily use is START_FILM_LAB.bat (cmd.exe). PowerShell is install / packaging only.
Zero credits. Local Gradio at 127.0.0.1:43123.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from film_lab.winlnk import write_install_shortcut

DAILY_LAUNCHER = "START_FILM_LAB.bat"
INSTALLER = "INSTALL_FILM_LAB.bat"
INSTALLER_ALIAS = "Install Film Lab.bat"
UNINSTALLER = "UNINSTALL_FILM_LAB.bat"
REPAIR_LAUNCHER = "REPAIR.bat"
COMPAT_START = "START.bat"
ICON_ICO = "assets/film_lab.ico"
ICON_PNG = "assets/film_lab.png"
SHORTCUT_VBS = "scripts/make_desktop_shortcut.vbs"
REMOVE_SHORTCUT_VBS = "scripts/remove_desktop_shortcut.vbs"
PACKAGING_DOC = "docs/PACKAGING.md"
UNINSTALL_DOC = "docs/UNINSTALL.md"
INNO_ISS = "packaging/FilmLab.iss"
ZIP_INSTALL_LNK = "Install Film Lab.lnk"
LOCAL_URL = "http://127.0.0.1:43123"
FORBIDDEN_DAILY = ("powershell", "pwsh")

PACKAGE_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".gradio",
        ".cursor",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
    }
)
PACKAGE_EXCLUDE_REL = frozenset(
    {
        "data/logs",
        "data/projects",
        "data/models",
        "data/safe_mode.flag",
    }
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def daily_launcher_uses_powershell(text: str) -> bool:
    """True if the daily bat actually invokes PowerShell (not the words 'no PowerShell')."""
    low = (text or "").lower()
    return "powershell.exe" in low or "pwsh" in low or "powershell -" in low


def iter_package_files(root: Path | None = None) -> list[Path]:
    """Files that belong in the Windows zip / Inno payload."""
    base = (root or repo_root()).resolve()
    out: list[Path] = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        parts = set(rel.parts)
        if parts & PACKAGE_EXCLUDE_DIRS:
            continue
        rel_posix = rel.as_posix()
        skip = False
        for prefix in PACKAGE_EXCLUDE_REL:
            if rel_posix == prefix or rel_posix.startswith(prefix + "/"):
                skip = True
                break
        if skip:
            continue
        if path.suffix.lower() in {".pyc", ".mp4", ".iso"}:
            continue
        if path.name in {".env", ".DS_Store", "Thumbs.db", ZIP_INSTALL_LNK}:
            continue
        out.append(path)
    return sorted(out)


def build_windows_zip(root: Path | None = None, dest: Path | None = None) -> Path:
    """Zip the desk for INSTALL_FILM_LAB.bat on Windows."""
    base = (root or repo_root()).resolve()
    out = Path(dest) if dest else base / "dist" / "film_lab_windows.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    files = iter_package_files(base)
    names = {p.relative_to(base).as_posix() for p in files}
    for required in (
        DAILY_LAUNCHER,
        INSTALLER,
        UNINSTALLER,
        ICON_ICO,
        "app.py",
        "PREFINISH.md",
        "CLICK_ME_FIRST.txt",
    ):
        if required not in names:
            raise FileNotFoundError(f"package missing {required}")
    lnk = write_install_shortcut(out.parent / ZIP_INSTALL_LNK)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, arcname=path.relative_to(base).as_posix())
        zf.write(lnk, arcname=ZIP_INSTALL_LNK)
    return out
