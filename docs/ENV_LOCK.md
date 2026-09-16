# Environment / Set lock

One locked plate for **World Note** and **3D Set**. Img2vid seeds from that still when the shot has no start frame. **Regenerate** keeps the World lock. Zero credits. Local only.

AMD **RX 5600 XT** (~6GB) — **not NVIDIA**. Start lightweight. OOM → drop Quality (1080p → 720p → 480p). Never native 4K.

## What gets locked

| Field | Job |
| --- | --- |
| Locked set still | The room / street / lamp plate. Primary env lock on 6GB. |
| Style / scene ref | Optional IP-Adapter scene ref when Comfy lists those nodes. |
| Geometry | ControlNet **depth / canny / softedge** (stub until nodes exist). |
| Strength | Stored for a later IP-Adapter graph. Daily path is the locked still. |
| Set note | Text that folds next to World Note + SET NOTE. |

Persist: `env_lock.json` + `env_refs/` on the project (runtime, gitignored).

**LOCKED Environment from photo** (3D Set Desk) also writes:

- `data/projects/<name>/sets/<set-id>/` — source, invented plate, look-around / zoom / aerial stills
- `data/projects/<name>/stills/` — copies
- `data/projects/<name>/takes/` — look-around clip

All on this PC. Offline. **Delete this set** removes them. See [SET.md](SET.md).

## Stack (probed, never faked)

1. **Locked still → img2vid** (wired). Seed Animate from this plate.
2. **IP-Adapter style/scene** (stub). Ready only if the sidecar lists IP-Adapter nodes.
3. **ControlNet depth / canny / softedge** (stub). Room/street geometry when those preprocessors exist.
4. World Note + 3D Set **reuse the same lock**. Apply on either desk.

Film Lab will not rewrite a take with InstantID / FaceID / ControlNet if those nodes are missing. Status on Home Machine: Off / Stub / Ready.

## DEBUG CHECKLIST (identity / env drift)

1. Strengthen adapter / face lock one step (0.55 → 0.65). Do not jump to 1.0.
2. Re-apply Character sheet refs and Environment lock still.
3. Drop Quality one step on OOM. Never native 4K.
4. **Regenerate** (keeps World lock + face lock + Quality).
5. InstantID / FaceID stay stubs until Comfy lists those nodes.

See [CHARACTER_CONSISTENCY.md](CHARACTER_CONSISTENCY.md) and [QUALITY.md](QUALITY.md).
