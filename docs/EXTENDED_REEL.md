# Extended reel (1–2 minutes)

Liam wants a **minute or two**, not a two-second take. Film Lab is honest about the engine:

**One local SVD-XT pass is seconds** (about 2–4s on the RX 5600 XT, 14 frames at ~6 fps). There is no single Generate that writes 60s or 120s of actor motion.

**Extended length = chain + stitch.**

1. **Enhance → Animate** as usual (short command → cinematic paragraph in the feed → first clip).
2. Set the **duration lock** on the rail: **1 min** (60s reel) or **2 min** (120s reel). Short locks are 5s / 10s / 15s / 20s / 30s (one pass).
3. **Build shot list** — Film Lab turns the enhanced paragraph into a beat sheet of N clips. N is the count that reaches the target after 0.5s crossfades.
4. **Continue from last frame** — ffmpeg pulls the last frame of the previous MP4; that still is the next SVD start. Faces stay locked.
5. **Generate remaining + stitch** — walk the rest of the list, then crossfade into one MP4.
6. **Cinema Desk → Auto-stitch sequence** if you generated clips one-by-one and want the reel later.

Ken Burns stays **Advanced only**. It is not the extend path and not auto-fallback.

Adults 18+ intimate / explicit is allowed. No Film Lab NSFW filter. Zero credits.

## Math (default 2.5s clips, 0.5s fade)

| Target | Clips | Stitched length |
| --- | --- | --- |
| 60s | 30 | ~60.5s |
| 120s | 60 | ~120.5s |

On 6GB AMD this is a long local session. That is hardware, not a paywall.

Crash, OOM, or off-prompt takes: [CRASH_RECOVERY.md](CRASH_RECOVERY.md) — restart the launcher, check Comfy `8188`, shorten / lower res, **Regenerate**, salvage in Cinema Desk or DaVinci.

## What not to expect

- One SVD graph with `duration=120`. The weights and VRAM do not do that here.
- A cloud I2V minute. This desk does not call one.
- Ken Burns zoom-pan as a substitute minute. Timing only, Advanced accordion.
