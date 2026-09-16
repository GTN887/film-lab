# Pose Desk

Still-first **pose / hand–face** adjust on the rehearsal still, then Motion Desk **Animate** (ComfyUI SVD-XT). OpenPose / ControlNet-**style** — a local skeleton guide, not a hosted pose product.

**This is not frame-by-frame video puppeting.** You edit the still. The face stays the Character Bible / FaceID lock. Then img2vid moves that posed frame.

Zero Film Lab credits. Adults 18+ only.

## Motion flow

**Upload → Pose adjust → Enhance → Animate.**

1. Drop or ingest the locked still (Alison / Bradley already look like themselves). On **AI Production Pipeline** this is the same shot as Enhance and Animate — no re-upload. [PIPELINE.md](PIPELINE.md)
2. **Pose Desk**, the Pipeline Pose step, or the Motion accordion: pick **body**, **hands**, **face**, plus **micro-expression** and **behavior**. **Apply pose**. Performance writes into the `.pose.json` sidecar and the Enhance seed. See [PERFORMANCE.md](PERFORMANCE.md).
3. Film Lab writes `stills/pose_<body>_<hands>_<face>_<id>.png` plus a `*.pose.json` sidecar (keypoints, face bbox, `not_video_puppeting: true`).
4. The face oval is punched out of the overlay — original face pixels stay. That is the 6GB face lock.
5. **Enhance** the short command (bible + lighting + emotion).
6. **Animate** / **Generate** — same ComfyUI SVD-XT path as the rest of Motion Desk.
7. **Regenerate** stays on the rail (new seed, same posed still + prompt).

## What Apply pose actually does

- **Always:** Pillow OpenPose-style skeleton on a copy of the still. Hands can move. Face presets are direction ticks *outside* the locked oval.
- **If Comfy lists OpenPose / ControlNet nodes:** status is Ready. Load a live graph in `workflows/pose/openpose_still.json` when you want a real ControlNet rewrite. Until that file has `class_type` nodes, Film Lab **will not fake one**.
- **If the sidecar is Off:** local overlay still works. Animate still needs Comfy for SVD-XT.

## Face lock while pose changes

Primary likeness on the RX 5600 XT (~6GB) is **start still → img2vid**. Pose Desk does not redraw eyes, nose, or mouth. Character Consistency FaceID / InstantID stubs still apply on Animate when those nodes exist. See [CHARACTER_CONSISTENCY.md](CHARACTER_CONSISTENCY.md).

## Hardware

Same box as Motion: Radeon RX 5600 XT, DirectML, Comfy at `http://127.0.0.1:8188`. Pose overlay is CPU / Pillow. It does not need CUDA.

## Honest limits

- One-figure guide. Kiss lean / embrace are blocking notes, not dual-skeleton puppeting.
- Face 3/4 and profile are ticks, not a 3D head turn.
- No claim that every finger is IK-solved. Hands are wrist targets.
- Video motion is SVD-XT from the posed still — not per-frame pose control.
