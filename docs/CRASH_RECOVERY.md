# Crash recovery (Motion Desk)

Film Lab is local. A crash or a take that ignores the prompt is **not** a paywall. Zero credits.

## Launcher / Comfy died

1. Double-click **REPAIR.bat** → **Restart Film Lab** (or `scripts/run.ps1` / `./scripts/run.sh`).
2. **Restart Comfy** from Repair (GPU1 / `--cuda-device 1`) or check `http://127.0.0.1:8188`.
3. Confirm `svd_xt.safetensors` is loaded. Generate again. Primary Generate never falls back to Ken Burns.
4. Still stuck: **Kill ports** `43123` / `8188`, **Open logs**, or **Safe mode** (480p / 5s). Works offline. [DESKTOP.md](DESKTOP.md).

## DEBUG CHECKLIST (fail / OOM / crash — RX 5600 XT, not NVIDIA)

1. Drop one resolution step (**1080p → 720p → 480p**).
2. Shorter duration / fewer frames (30s → 15s → 5s).
3. Retry **Regenerate** (new seed, same still + prompt + Quality).
4. Restart Comfy via the launcher if the sidecar is still dead (`8188`).
5. **Never force native 4K** on this GPU. 4K is generate-at-720p then upscale on Cinema export. See [QUALITY.md](QUALITY.md).

One SVD-XT pass is seconds. **1 min / 2 min** are a multi-shot chain — do not expect one 60s graph. Close other GPU apps, then restart Comfy and Film Lab.

## Output ignores the prompt

1. **Regenerate** — always on the Motion rail. New seed, same still + prompt.
2. **Enhance** the short command again (or edit the enhanced line), then Generate / Regenerate.
3. Tighten **negatives** (quality / age only — not an NSFW gate). Add the motion you want in the prompt body.
4. If the take is still usable, salvage it on **Cinema Desk** (stitch / grade) or finish in **DaVinci** / After Effects. Download MP4 from the desk.

## Salvage a partial reel

- Cinema Desk → **Auto-stitch sequence** if some last-frame clips already exist.
- Or drop the MP4s into DaVinci. Nothing is uploaded. Adults 18+.
