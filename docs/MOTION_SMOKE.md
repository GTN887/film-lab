# Motion Desk smoke test (Windows, RX 5600 XT)

This desk must write a **downloadable MP4** via **local img2vid**. Zero Film Lab credits. Open weights only.

Not a hosted I2V shop. Film Lab does **not** ship pirated commercial video weights.

Ken Burns is **not** the smoke test. It is Advanced-only timing/zoom.

## What “working” means

| You give | Engine | Result |
| --- | --- | --- |
| Still + motion prompt | ComfyUI SVD-XT on the RX 5600 XT | MP4 in the player + download |
| Prompt only | Prompt card, then ComfyUI img2vid | MP4 (likeness is weaker without a still) |
| 9:16 UGC | Same, 288×512 internal / 720×1280 desk | Vertical MP4 |
| Sidecar Off | **Blocked** — start `scripts/run_comfyui_amd.ps1` | No zoom-pan stand-in |
| ffmpeg missing | **Blocked** with install steps | No fake spinner |

## Windows, two windows

**A — the motion engine (ComfyUI DirectML)**

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_comfyui_amd.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\install_comfyui_amd.ps1 -DownloadModels
powershell -ExecutionPolicy Bypass -File .\scripts\run_comfyui_amd.ps1
```

Leave `http://127.0.0.1:8188` running. First clip: **2–4s**, 16:9 or 9:16.

**B — desk**

```powershell
.\scripts\run.ps1
```

Chrome: `http://127.0.0.1:43123` → **Motion Desk**. Upload a still, optional **Pose adjust** (face lock stays; not video puppeting), **Add Prompt**, type a short command, **Generate**. The cinematic paragraph must appear in the feed **before** the clip. Overlay shows **Generating… %**. Duration lock: 5s–30s one pass; **1 min / 2 min** last-frame chain + stitch (`docs/EXTENDED_REEL.md`). **Regenerate** is always available. Crash / OOM / off-prompt: `docs/CRASH_RECOVERY.md`. Pose notes: `docs/POSE.md`.

If window A is closed, Primary Generate **stops**. It will not zoom-pan a still and call that a take. Open **Advanced · Ken Burns (timing only)** only if you want a coverage file.

## Three clicks Liam should feel

1. Start ComfyUI (`--cuda-device 1`). Drop a still. Type a prompt. Click **Generate video (SVD-XT · AMD)**. Preview and download.
2. Click **Use 9:16 UGC**. Generate a vertical beat the same way.
3. If the sidecar OOMs, drop to 2s. Do not treat Ken Burns as the product.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_amd.ps1
```

## Honest Off

Motion Desk shows **Local AMD img2vid: Off** plus the PowerShell line. It does **not** pretend a cloud model is generating. Primary Generate stays blocked until the sidecar is Ready.
