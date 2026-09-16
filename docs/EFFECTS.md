# Effects Desk

A **preset shelf** on this machine: character still in, short motion clip out. The layout jobs (required character PNG/JPG, optional location and product plates, preset grid, prompt toggle, aspect, resolution, Generate) follow a public effects-page *shape*. Names are Film Lab descriptions — floating fall, high flip, studio slide, melting hold — not a hosted pack.

Zero Film Lab credits. No free-gens counter.

## What Generate does

1. Character still is required. Location and product stills are optional refs (prompt continuity, not a second engine).
2. The selected preset writes a motion prompt (and optional extra line).
3. **Local ComfyUI SVD-XT** (`127.0.0.1:8188`, `--cuda-device 1`, `svd_xt.safetensors`) writes a 2–4s clip when the sidecar is Ready.
4. Film Lab rewraps to the desk aspect and resolution (720 or 1080).
5. If the sidecar is Off, Generate **stops** with the install path. It does not Ken Burns a still.

One SVD pass is still **seconds**. These presets are one beat, not a 60s reel. Chain on Motion Desk if you need length.

## Custom graphs

Drop a ComfyUI **API-format** JSON at `workflows/effects/<preset_id>.json`. Until that file has real `class_type` nodes, the desk treats it as a **stub** and uses the shared SVD-XT graph plus the preset prompt. See `workflows/effects/README.md`.

## After export

Grade and composite in **DaVinci Resolve** or **Adobe After Effects** when you want a finish Film Lab does not pretend to be. LUT / grain on the Finish tab is a light local pass only.

Adults 18+ only. No Film Lab NSFW filter.
