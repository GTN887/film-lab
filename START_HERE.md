# START HERE — Film Lab (Windows)

**You are looking at source code if you opened this from Cursor “Open in Web” or an Origin / agent URL.** That page is the repo, not the desk.

The program is a **local Gradio app**. It only appears after you run it on your PC and open Chrome or Edge at:

**http://127.0.0.1:43123**

There are **no Film Lab credits**. This is a private film-school studio on your machine.

**Works offline for local generation.** After models are installed, Motion / Still / Take Board / Character / Mark & Direct / UGC do not need the internet. Grok / Gemini / ChatGPT / Claude / ElevenLabs are **online optional**.

Primary motion is **local SVD-XT img2vid** through ComfyUI at `http://127.0.0.1:8188` (`--cuda-device 1`, RX 5600 XT). Ken Burns is Advanced-only timing/zoom — not the product.

**Desktop PRE-FINISH:** unzip, open **CLICK_ME_FIRST.txt**, double-click **Install Film Lab** (purple FL icon), then **START_FILM_LAB.bat**. Browser: **http://127.0.0.1:43123**. Uninstall: **UNINSTALL_FILM_LAB.bat**. Stuck? **REPAIR.bat**. See [PREFINISH.md](PREFINISH.md) · [docs/DESKTOP.md](docs/DESKTOP.md) · [docs/PACKAGING.md](docs/PACKAGING.md) · [docs/UNINSTALL.md](docs/UNINSTALL.md).

---

## 1. Install once

1. Install **Python 3.11 or newer** from https://www.python.org/downloads/  
   Tick **Add python.exe to PATH**. On this desk use `py -3` (bare `python` may be the Store stub).  
   For ComfyUI, also install **Python 3.12** if `py -3` is 3.14.
2. Install **ffmpeg**:
   - Open a **new** PowerShell and run: `winget install Gyan.FFmpeg`
   - Or: https://ffmpeg.org/download.html and add `ffmpeg.exe` to PATH.

## 2. Unzip on the Windows desk

Unzip `film_lab_windows.zip` (or clone the repo) so the folder contains `app.py`, `INSTALL_FILM_LAB.bat`, and `scripts\`.

## 3. Install Film Lab on Desktop

Double-click **Install Film Lab**. Pick **1** to copy to `Desktop\Film Lab`, **2** for AppData, or **3** to use this folder (patch in place). Shortcuts land on the Desktop and Start Menu. No PowerShell.

## 4. Start the desk

Double-click the Desktop **Film Lab** icon (or **START_FILM_LAB.bat**). That is the program.

Leave the Comfy + Film Lab windows open. You should see a line like: `Running on local URL: http://127.0.0.1:43123`

## 5. Open the UI (not the code)

In **Chrome** or **Edge**, go to:

**http://127.0.0.1:43123**

That Gradio page **is** Film Lab. Chrome is **one purple + soft cyan theme** on every desk — Regular vs 18+ Explicit is a filming-mode toggle, not a red Darkroom Suite vs a purple regular app. **Home** is the studio hub (job cards plus **Lighting**, **Score**, and **Voice** craft desks). **Library** in the top nav is the **Save Library** — browse stills / takes / sets / writing on this PC; OneDrive / Google Drive folders are optional backup when online. The featured card **AI Production Pipeline** opens one desk: **Enhance | Pose | Animate** on the **same shot** (no re-upload), then **Back to Home**. Full **Motion Desk** is still **any still → Animate** (people, products, cans, posters). **Director Brain** imports PDF / Word / text, Fuses Grok + Gemini drafts, then Plans shots to Motion. **Family Genetics** on Character Bible blends two adult refs into Regular / story kids. **UGC Ads Desk** is product + avatar ads — no marketplace. Ken Burns is collapsed under Advanced. Read `HOME.md`, `docs/WRITING.md`, `docs/MOTION.md`, `docs/UGC.md`, `docs/CHARACTER_CONSISTENCY.md`, `docs/LIGHTING.md`, `docs/SCORE.md`, and `docs/VOICE.md`.

---

## AMD img2vid (RX 5600 XT) — first real motion clip

This machine has **no NVIDIA**. Do not install CUDA torch as the default.

1. Install the sidecar (once). Prefer Python **3.12** for ComfyUI:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_comfyui_amd.ps1
```

Add `-DownloadModels` to pull SD 1.5 + AnimateDiff v3 (several GB, open weights).

2. Start ComfyUI and **leave the window open**:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_comfyui_amd.ps1
```

It listens on `http://127.0.0.1:8188` with `--directml --lowvram`.

3. Optional check:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_amd.ps1
```

The Film Lab **Machine** panel should show Local AMD img2vid as **ready**.

4. In Film Lab → **AI Production Pipeline** (home card): drop a still **once**, then **Enhance | Pose | Animate** on that same shot. No re-upload. **Back to Home** when you are done. Full **Motion Desk** still has Director Note, World Note, Resolution (480p / 720p / 1080p / 1440p / 4K), Aspect (16:9 through 2.39:1 cinema scope / 1.85:1), and duration. Intimate / explicit: adult 18+ ONLY. Prompt Enhancement expands it in the feed (continuity, lighting on skin, micro-motions) **before** the clip. Duration lock: 5s / 10s / 15s / 20s / 30s one pass; **1 min / 2 min** = chain + stitch. **Regenerate** (always on) rolls a new seed on the same still + prompt + Quality + Aspect. See `docs/EXTENDED_REEL.md` and `docs/POSE.md`. Local templates default; Grok / Gemini / ChatGPT / Claude if you set keys. Video is local ComfyUI SVD-XT. Film Lab will not reject adult 18+ intimate prompts.

**Take Board — Play vs Fix.** Click a take to play. Pause freezes; it does **not** edit. Enter Direct only with **Mark & Direct** · **Fix this frame**. Banner: *Directing — changes will make a new take.* Apply / Regenerate forks a new take. Exit Direct returns to Playback. The old take stays. `docs/PLAYBACK.md`.

**Voice notes.** Director Note (actor) and Mark & Direct (prop / object / clothing) take **typed or spoken** input into the same box. Mic transcribes, then Apply / Regenerate. Type if no local STT is installed. `docs/VOICE_NOTES.md`.

**Character + Environment program** — Character Bible sheet (Alison / Bradley / family) + InstantID/FaceID stubs + Pose Desk OpenPose. Lock a set still on World Note / 3D Set; img2vid seeds from it; Regenerate keeps the World lock. Drift: strengthen adapter, re-apply refs, drop Quality, Regenerate. `docs/CHARACTER_CONSISTENCY.md`, `docs/ENV_LOCK.md`.

**Quality program (RX 5600 XT, not NVIDIA)** — same picker on Still Desk + Cinema export. Prefer native **480 / 720**; **1080** if VRAM allows; **4K = generate lower then upscale on export**. Shot card stores Quality. DEBUG CHECKLIST on fail / OOM / crash: drop one step (1080→720→480); shorter duration / fewer frames; retry Regenerate; restart Comfy via the launcher if still dead (`8188`); **never force native 4K**. Full notes: `docs/QUALITY.md`, `docs/CRASH_RECOVERY.md`.

SVD-XT on this PC:

`%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\models\checkpoints\svd_xt.safetensors`

First clip is 512×288 internally, then padded to the desk aspect. Camera move + body notes go into the workflow prompt.

Ken Burns lives under **Advanced · Ken Burns (timing only)**. It is not auto-fallback and not the product.

**Effects Desk:** character PNG/JPG, optional location and product, pick a descriptive preset, **Generate**. Local SVD-XT when Comfy is Ready. Custom graphs under `workflows/effects/` are stubs until you drop a real API JSON. After export, grade in DaVinci or After Effects. See `docs/EFFECTS.md`.

**Pose Desk:** upload a still, pick body / hands / face, **Apply pose**. Face pixels stay. Or pose on **AI Production Pipeline** — same shot, no re-upload — then Enhance → Animate. Not video puppeting. See `docs/POSE.md` · `docs/PIPELINE.md`.

Concrete open models (see `docs/AMD_IMG2VID.md`):

| Role | File | Where |
| --- | --- | --- |
| SD 1.5 (default 6GB path) | `v1-5-pruned-emaonly.safetensors` | `FilmLab-ComfyUI\models\checkpoints\` |
| AnimateDiff v3 | `v3_sd15_mm.ckpt` | `FilmLab-ComfyUI\models\animatediff_models\` |
| Optional LTX 2B | `ltxv-2b-0.9.8-distilled.safetensors` | `FilmLab-ComfyUI\models\checkpoints\` |

Workflows in this zip: `workflows/amd_animatediff_i2v_api.json`, `workflows/amd_ltx_i2v_api.json`.

---

## If you still see source code

You opened the **Cursor / Origin / agent** page. Close it. The desk is only at `http://127.0.0.1:43123` after **START_FILM_LAB.bat**.

## Optional writing APIs (your keys — no Film Lab credits)

```powershell
$env:FILM_LAB_XAI_API_KEY = "xai-..."
$env:FILM_LAB_GEMINI_API_KEY = "AIza..."
$env:FILM_LAB_OPENAI_API_KEY = "sk-..."
# optional model ids if a vendor retires the default:
# $env:FILM_LAB_OPENAI_MODEL = "gpt-4.1"
.\scripts\run.ps1
```

Adults 18+ only. Adult explicit is allowed. No sexual content involving minors. Film Lab is a personal film-school desk — no subscriptions, credits, or paywalls.
