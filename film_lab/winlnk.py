"""Minimal Windows .lnk writer — no win32com, works on Linux packagers.

Used so the zip ships **Install Film Lab.lnk** with the studio icon.
Target is cmd.exe via an environment block so the shortcut is portable.
"""

from __future__ import annotations

import struct
from pathlib import Path

_CLSID = bytes.fromhex("0114020000000000C000000000000046")
_HAS_NAME = 0x04
_HAS_ARGUMENTS = 0x20
_HAS_ICON = 0x40
_IS_UNICODE = 0x80
_HAS_EXP_STRING = 0x200
_SW_SHOWNORMAL = 1
_ENV_BLOCK_SIZE = 0x314
_ENV_BLOCK_SIG = 0xA0000001


def _u16_string(text: str) -> bytes:
    data = text.encode("utf-16le")
    count = len(text)
    return struct.pack("<H", count) + data


def write_install_shortcut(
    dest: Path,
    *,
    arguments: str = "/c INSTALL_FILM_LAB.bat",
    name: str = "Install Film Lab",
    icon: str = r"assets\film_lab.ico",
    target_env: str = r"%SystemRoot%\System32\cmd.exe",
) -> Path:
    """Write a portable .lnk that runs a bat next to the shortcut."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    flags = _HAS_NAME | _HAS_ARGUMENTS | _HAS_ICON | _IS_UNICODE | _HAS_EXP_STRING
    header = b"".join(
        [
            struct.pack("<I", 0x4C),
            _CLSID,
            struct.pack("<I", flags),
            struct.pack("<I", 0),
            b"\x00" * 24,
            struct.pack("<I", 0),
            struct.pack("<I", 0),
            struct.pack("<I", _SW_SHOWNORMAL),
            struct.pack("<H", 0),
            struct.pack("<H", 0),
            struct.pack("<I", 0),
            struct.pack("<I", 0),
        ]
    )
    strings = _u16_string(name) + _u16_string(arguments) + _u16_string(icon)
    ansi = target_env.encode("ascii", "replace")[:259] + b"\x00"
    ansi = ansi + b"\x00" * (260 - len(ansi))
    uni = (target_env + "\x00").encode("utf-16le")
    uni = uni[:520] + b"\x00" * (520 - min(len(uni), 520))
    env = struct.pack("<II", _ENV_BLOCK_SIZE, _ENV_BLOCK_SIG) + ansi + uni
    terminal = struct.pack("<I", 0)
    dest.write_bytes(header + strings + env + terminal)
    return dest


def looks_like_lnk(path: Path) -> bool:
    data = Path(path).read_bytes()
    return len(data) >= 76 and data[:4] == b"\x4c\x00\x00\x00" and data[4:20] == _CLSID
