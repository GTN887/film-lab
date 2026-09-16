# UGC Ads / Product desk

Local product ads. **Zero Film Lab credits.** Adults **18+** only. Not a hosted marketplace.

The desk is two layers on the same **UGC Ads Desk** tab (hub card `07` — no extra card):

1. **Product flow** (primary): product still + avatar + prompt → **Generate still** → **Enhance** → **Animate**.
2. **Spoken ad plan** (closed accordion): optional hook → CTA five-beat script, then push to Motion Desk.

## Product flow (Liam lock)

1. Upload a **product** still (png / jpg / webp).
2. Choose an avatar from the **Character Bible** **or** upload a picture.
3. Write how the product and the person appear (placement, prompt, notes).
4. **Generate still** and/or **Animate**. Edit the finished take with **Mark & Direct** → **Regenerate**.

### Still

**Generate still** is an honest local composite: the avatar is fit to Quality × Aspect, the product is overlaid with a gold ring. Film Lab does **not** claim an inpaint or diffusion merge.

Quality picker: **480p / 720p / 1080p / 4K**. Aspect defaults to **9:16** (same lock as Motion / Still). 4K is never a native SVD pass.

### Animate

**Animate** uses the same local SVD-XT path as Motion Desk (ComfyUI at `127.0.0.1:8188`). If the sidecar is Off, the toast says so — no Ken Burns auto-fallback. The composite still is still saved so you can retry.

### Mark & Direct

**Mark & Direct this take** lands the mp4 on **Take Board Playback**. Pause never edits. Press **Mark & Direct** · **Fix this frame**, note the region (typed or mic), **Regenerate**. The old take stays. See [PLAYBACK.md](PLAYBACK.md) and [MARK.md](MARK.md).

### Adult gate

UGC / product ads are **adult 18+**. Bible roles marked Teen / Child / Infant are blocked. Age (years) is required. Director Notes on any age are performance / placement — they do not unlock this desk for minors.

## Spoken plan (optional)

Closed accordion. Local hook → problem → product → proof → CTA templates always work. Optional Grok / Gemini / ChatGPT / Claude use keys you own. Five 9:16 beats, about 8–15s after Cinema stitch. **Push plan → Motion Desk shots**, then generate each beat.

## Multi-beat product motion

Example: **can opens alone** → then a person **picks up and pours**.

1. **Mark & Direct** — Animate the can-alone still on Motion Desk. Playback, then Fix this frame, note the pour, **Regenerate**.
2. **Multi-shot stitch** — **Push two beats → Motion Desk**. Animate each. Cinema stitch.

Motion Desk stays the primary plain image→video path. This desk does **not** add a marketplace. See [MOTION.md](MOTION.md).

## Hardware

Radeon RX 5600 XT (~6GB): short clips, prefer 480p / 720p. See [QUALITY.md](QUALITY.md) and [AMD_IMG2VID.md](AMD_IMG2VID.md).
