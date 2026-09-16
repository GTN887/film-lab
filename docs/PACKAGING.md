# Packaging Film Lab as a desktop program

Film Lab is a **local Gradio desk**, not a website. After install it should feel like a game on the Desktop: purple **FL** icon, double-click **START_FILM_LAB.bat**, Chrome/Edge opens `http://127.0.0.1:43123`. PRE-FINISH zip: [PREFINISH.md](../PREFINISH.md).

**Daily use does not need PowerShell.** First-time Python / ffmpeg install might.

## Ship to Liam

| Deliverable | Icon | What he double-clicks |
| --- | --- | --- |
| `film_lab_windows.zip` | **Install Film Lab.lnk** (purple FL) at the zip root | That shortcut runs `INSTALL_FILM_LAB.bat` |
| `Install_Film_Lab.exe` (optional Inno) | Setup uses `assets/film_lab.ico` | Windows installer |

Both place **app files** plus **Desktop** and **Start Menu** shortcuts with the Film Lab icon.

## What Liam double-clicks after unzip

| File | When |
| --- | --- |
| **Install Film Lab.lnk** / **INSTALL_FILM_LAB.bat** | Once. Copies files (Desktop or AppData) and pins shortcuts. |
| **START_FILM_LAB.bat** / Desktop **Film Lab** | Every session. |
| **UNINSTALL_FILM_LAB.bat** | Remove shortcuts and optional folder. [UNINSTALL.md](UNINSTALL.md). |
| **REPAIR.bat** | Stuck desk / dead ports / safe mode. |

PowerShell scripts under `scripts\` stay for first-time Comfy sidecar setup. They are **not** the daily path.

## Install on this PC

1. Unzip. Read **CLICK_ME_FIRST.txt**. The folder shows **Install Film Lab.lnk** with the purple FL icon.
2. Python 3.11+ (Add to PATH). Comfy sidecar prefers **3.12**.
3. ffmpeg once (`winget install Gyan.FFmpeg`).
4. Double-click **Install Film Lab**
   - **1** — copy to `Desktop\Film Lab` + shortcuts
   - **2** — copy to `%LOCALAPPDATA%\Film Lab` + Desktop / Start Menu shortcuts
   - **3** — use this folder (Grok Bot / Cursor patch in place)
5. Double-click **Film Lab** on the Desktop.

## Zip for a USB / backup

```
python scripts/package_windows.py
```

Writes `dist/film_lab_windows.zip` including **Install Film Lab.lnk**. Excludes `.venv`, `.git`, `data/projects`, logs, and mp4s.

## Optional Setup.exe (Inno Setup)

`packaging/FilmLab.iss` — per-user `%LOCALAPPDATA%\Film Lab`, Desktop icon, Start Menu, uninstall via Apps.

```
iscc packaging\FilmLab.iss
```

Output: `dist\Install_Film_Lab.exe`.

## Patch in place

The install folder is ordinary files. Point **Grok Bot / Cursor** at it. Edit, then START. No reinstall. See [UNINSTALL.md](UNINSTALL.md).

## Icon

`assets/film_lab.ico`. Shortcut `IconLocation` is that file. Windows may cache icons; sign out if Explorer still shows a cmd glyph.

## Ports

| Process | Bind |
| --- | --- |
| Film Lab Gradio | `127.0.0.1:43123` |
| Comfy sidecar | `127.0.0.1:8188` (`--cuda-device 1`) |

See [DESKTOP.md](DESKTOP.md), [UNINSTALL.md](UNINSTALL.md), [START_HERE.md](../START_HERE.md).
