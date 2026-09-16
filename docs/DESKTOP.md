# Desktop launcher + Repair (offline-first)

**Works offline for local generation.** Once Python, ffmpeg, and local Comfy models are installed, Motion / Still / Take Board / Character / Mark & Direct / UGC do not need the internet.

Grok / Gemini / ChatGPT / Claude / ElevenLabs are **online optional** (keys you own). They are never required.

**Daily use does not need PowerShell.** Double-click the Film Lab icon or `START_FILM_LAB.bat`.

## Install Film Lab on Desktop

The zip ships **Install Film Lab.lnk** with the purple FL icon. Setup.exe uses the same icon. PRE-FINISH click order: [PREFINISH.md](../PREFINISH.md).

1. Unzip (or run `Install_Film_Lab.exe`).
2. First time: Python 3.11+ (Add to PATH) and ffmpeg.
3. Double-click **Install Film Lab**
   - **1** — copy files to `Desktop\Film Lab` + Desktop / Start Menu shortcuts
   - **2** — copy files to `%LOCALAPPDATA%\Film Lab` + shortcuts
   - **3** — keep files here (Grok Bot / Cursor patch in place) + shortcuts
4. Double-click **Film Lab** on the Desktop.

Uninstall: **UNINSTALL_FILM_LAB.bat** (shortcuts, optional folder delete). [UNINSTALL.md](UNINSTALL.md). Packaging: [PACKAGING.md](PACKAGING.md).

`START.bat` still works — it calls `START_FILM_LAB.bat`.

## Double-click START (daily)

`START_FILM_LAB.bat` does three things, offline, in cmd.exe:

1. Starts ComfyUI on **GPU1** (`--cuda-device 1`, port `8188`) if it is not already up.
2. Starts Film Lab on `http://127.0.0.1:43123`.
3. Opens the local UI in your browser.

No folder hunting after the shortcut is installed. Leave the Comfy + Film Lab windows open.

Linux / this box: `scripts/start_desktop.sh`.

PowerShell (`scripts\start_desktop.ps1`, `scripts\install_windows.ps1`) is optional leftover for first-time Comfy sidecar work — not the daily path.

## Repair toolkit (works offline)

Double-click **REPAIR.bat** (cmd menu — no PowerShell):

| Action | What it does |
| --- | --- |
| Restart Film Lab | Kill `43123`, start the desk, open the UI |
| Restart Comfy | Kill `8188`, start sidecar on GPU1 |
| Kill ports | Stop whatever is holding `43123` / `8188` |
| Open logs | `data/logs/` (`launcher.log`, `film_lab.log`) |
| Safe mode | 480p + 5s clip, write `data/safe_mode.flag`, then START |

In-app: Home → **Repair (desktop, works offline)** → **Safe mode (480p / short clip)**.

## Banner

The desk always shows **Offline | Online optional**. Core generation stays local Comfy. Cloud families fail soft if you pick them without a key or without a network.

Force local templates this session (cmd): `set FILM_LAB_OFFLINE=1` then START_FILM_LAB.bat.
