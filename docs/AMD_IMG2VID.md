# Local AMD image-to-video (RX 5600 XT)

Film Lab’s **primary** generate path is **ComfyUI SVD-XT img2vid** on this PC (`svd_xt.safetensors`). It is not a Grok / xAI / Higgsfield video API. There are **no Film Lab credits** and **no Film Lab NSFW filter**. Adults 18+ only.

Verified target: **AMD Ryzen 9 7900X + Radeon RX 5600 XT (~6GB) + Windows 11**.

## Why ComfyUI + SVD-XT

| Backend | On this card |
| --- | --- |
| **`--cuda-device 1`** | Liam's Comfy-Desktop on the RX 5600 XT. Film Lab talks to `127.0.0.1:8188`. |
| **DirectML** (`--directml`) | Alternate sidecar if you installed `FilmLab-ComfyUI`. Use `--lowvram`. |
| ROCm for Windows | Aimed at newer RDNA. gfx1010 (5600 XT) is a poor fit. |
| CUDA / stock torch | **Do not** install as the default. There is no NVIDIA GPU. |
| ZLUDA | Optional later if you want a CUDA-named torch. Not required. |

## Quality (480p / 720p / 1080p / 4K)

The same picker is on Motion Desk, Still Desk, and Cinema export. Prefer native **480p / 720p** on this card. **1080p** only if VRAM allows. **4K** is never a native SVD pass — generate at 720p, then upscale on Download / stitch / assemble. Quality sticks on the shot card so Regenerate keeps it. See [QUALITY.md](QUALITY.md).

Ken Burns (ffmpeg zoompan) is **Advanced only** — collapsed on Motion Desk, never auto-fallback, not the product.

Motion Desk lists **local video tools**: ComfyUI SVD-XT img2vid (primary), AnimateDiff / LTX if those nodes exist, WAN-class later. Ken Burns is timing/zoom only. No hosted video subscription. Zero Film Lab credits.

Any still is legal input — people, products, cans, posters. Pose / face lock are for people. Product + person ads are UGC Ads Desk. **No marketplace.** See [MOTION.md](MOTION.md).

## Install (Windows PowerShell)

From the unzipped project folder (`app.py` + `scripts\`):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\install_comfyui_amd.ps1
```

`install_comfyui_amd.ps1` clones ComfyUI to `%USERPROFILE%\FilmLab-ComfyUI` so a new Film Lab zip does not wipe weights.

ComfyUI + `torch-directml` want **Python 3.12** (or 3.11). If `py -3` is 3.14, install 3.12 from python.org and re-run the sidecar installer.

Optional (large downloads):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_comfyui_amd.ps1 -DownloadModels
```

## Models (open weights only)

Default **6GB** path — AnimateDiff v3 + SD 1.5 at **512×288**, **8 fps**, **9 / 17 / 25** frames (~2–3s):

| File | Hugging Face |
| --- | --- |
| `v1-5-pruned-emaonly.safetensors` | `stable-diffusion-v1-5/stable-diffusion-v1-5` |
| `v3_sd15_mm.ckpt` | `guoyww/animatediff` (`v3_sd15_mm.ckpt`) |

Custom nodes (cloned by the installer):

- `ComfyUI-AnimateDiff-Evolved` (Kosinkadink)
- `ComfyUI-VideoHelperSuite`
- `ComfyUI-Manager`

Newer stock-ComfyUI path if `LTXVImgToVideo` exists:

| File | Hugging Face |
| --- | --- |
| `ltxv-2b-0.9.8-distilled.safetensors` | `Lightricks/LTX-Video` |

Film Lab picks **LTX** when that node is installed, otherwise **AnimateDiff**. Override with `FILM_LAB_COMFY_BACKEND=animatediff` or `ltx`.

Do **not** expect Wan 14B, SVD-XT, or Hunyuan on 6GB DirectML.

## Start order

Window A — sidecar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_comfyui_amd.ps1
```

Listens on `http://127.0.0.1:8188` with `--directml --lowvram`.

Window B — desk:

```powershell
.\scripts\run.ps1
```

Chrome/Edge: `http://127.0.0.1:43123` → Motion Desk → **Generate video (SVD-XT · AMD)**.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_amd.ps1
```

## First clip

See `docs/MOTION_SMOKE.md` for the three-click Windows pass.

1. Motion prompt is enough. A still is optional (drop one for likeness).
2. Duration **2–4 seconds** (default 3). **Use 9:16 UGC** for vertical.
3. 16:9 internal 512×288 (pad to 1280×720). 9:16 internal 288×512.
4. Camera + body notes inject into the ComfyUI prompt when the sidecar is Ready.
5. **Generate video (SVD-XT · AMD)**. If ComfyUI is Off, this button **stops**. Start the sidecar.
6. First ComfyUI run can take several minutes while DirectML compiles.

If VRAM dies: drop to 2s, or set `FILM_LAB_I2V_WIDTH=448` and `FILM_LAB_I2V_HEIGHT=256`. Advanced Ken Burns is timing only, not a substitute take.

## Workflows in this repo

| File | Use |
| --- | --- |
| `workflows/amd_animatediff_i2v_api.json` | Default API graph (titles `film_lab_*`) |
| `workflows/amd_ltx_i2v_api.json` | LTX 2B distilled API graph |

Film Lab injects image / prompt / seed / size / frames. If ComfyUI rejects a node, open the graph in ComfyUI, install missing nodes via Manager, **File → Export Workflow (API)**, then:

```powershell
$env:FILM_LAB_COMFY_WORKFLOW = "$HOME\Desktop\film_lab_windows\workflows\amd_animatediff_i2v_api.json"
```

Keep node titles: `film_lab_image`, `film_lab_positive`, `film_lab_negative`, `film_lab_seed`.

## Environment

| Variable | Default | Meaning |
| --- | --- | --- |
| `FILM_LAB_COMFY_URL` | `http://127.0.0.1:8188` | Sidecar |
| `FILM_LAB_COMFY_HOME` | `%USERPROFILE%\FilmLab-ComfyUI` | Install / run path |
| `FILM_LAB_COMFY_TIMEOUT` | `1800` | Seconds to wait |
| `FILM_LAB_COMFY_BACKEND` | auto (`svd` first) | `svd` / `animatediff` / `ltx` / `custom` |
| `FILM_LAB_SVD_CKPT` | `svd_xt.safetensors` | Filename inside ComfyUI `models/checkpoints` |
| `FILM_LAB_COMFY_CUDA_DEVICE` | `1` | Passed to `run_comfyui_amd.ps1` |
| `FILM_LAB_COMFY_WORKFLOW` | bundled API json | Your exported graph |
| `FILM_LAB_I2V_WIDTH` / `HEIGHT` | 512×288 (16:9) | Internal size |
| `FILM_LAB_SD15_CKPT` | `v1-5-pruned-emaonly.safetensors` | Checkpoint filename |
| `FILM_LAB_AD_MOTION` | `v3_sd15_mm.ckpt` | AnimateDiff module |
| `FILM_LAB_LTX_CKPT` | `ltxv-2b-0.9.8-distilled.safetensors` | LTX checkpoint |

## Zip update on the Desktop

Unzip a new `film_lab_windows.zip` **over** the project folder (or next to it). Do **not** delete `%USERPROFILE%\FilmLab-ComfyUI` — models live there. Re-run `install_windows.ps1` if `requirements.txt` changed. Re-copy workflows if you want the latest graphs:

```powershell
Copy-Item .\workflows\amd_*.json $HOME\FilmLab-ComfyUI\user\default\workflows\ -Force
```

## Legal / product

Open models only. No cracked Higgsfield weights, no hosted NSFW filter, no credit meter. Adult explicit is allowed locally. Characters must be adults 18+.
