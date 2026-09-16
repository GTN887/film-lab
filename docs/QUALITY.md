# Quality program (480p / 720p / 1080p / 1440p / 4K)

AMD **RX 5600 XT** (~6GB) — **not NVIDIA**. One **Resolution** dropdown for stills and video on **Pipeline Enhance**, **Motion Desk**, **Still Desk**, and **Cinema Desk** (export). The shot card stores Quality so **Regenerate** keeps the take.

Zero credits. Local only.

## Program

1. UI: Resolution dropdown **480p / 720p / 1080p / 1440p / 4K** on stills + video (and export).
2. Hardware defaults: prefer native **480 / 720**; allow **1080** when VRAM allows; **1440p / 4K = generate lower then upscale on export**.
3. Shot card stores the chosen resolution for Regenerate.
4. On fail / OOM / crash, run the DEBUG CHECKLIST. Never force native 4K on this GPU.

## Picker

| Quality | Native generate (SVD-XT) | Export |
| --- | --- | --- |
| **480p** | Native 480p | Same |
| **720p** (default) | Native 720p | Same |
| **1080p** | Native 1080p if VRAM allows | Same |
| **1440p** | Native **720p** | Upscale on Download / stitch / assemble |
| **4K** | Native **720p** | Upscale on Download / stitch / assemble |

4K is never a native SVD pass on this box.

## RX 5600 XT (~6GB)

Prefer native **480p / 720p**. Try **1080p** only if VRAM allows. For **4K**, generate lower (720p) and upscale on Cinema export. Forcing native 4K SVD will OOM.

Internal SVD sizes stay small (512×288-class on 720p). The desk rewraps to the Quality pixel size after the pass.

## DEBUG CHECKLIST (fail / OOM / crash)

1. Drop one resolution step (**1080p → 720p → 480p**).
2. Shorter duration / fewer frames (30s → 15s → 5s).
3. Retry **Regenerate** (new seed, same still + prompt + Quality).
4. Restart Comfy via the launcher if the sidecar is still dead (`8188`).
5. **Never force native 4K** on this GPU.

## Shot card

`ShotCard.resolution` persists with the take (`720p`, `1080p`, `480p`, or `4K`). New Generate uses the desk picker. Regenerate copies the source take's Quality onto the forked card. Project `quality` in `project.json` is the desk default.

**Aspect** is one dropdown (16:9 through 2.39:1 cinema scope / 1.85:1) next to **Resolution** (480p / 720p / 1080p / 1440p / 4K) on Pipeline Enhance. `ShotCard.aspect_ratio` persists. Regenerate keeps it unless you change the picker. [ASPECT.md](ASPECT.md). **1440p / 4K** generate lower, then upscale on export.

See [CRASH_RECOVERY.md](CRASH_RECOVERY.md) and [AMD_IMG2VID.md](AMD_IMG2VID.md).
