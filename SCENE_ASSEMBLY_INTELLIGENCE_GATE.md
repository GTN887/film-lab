# Scene Assembly Intelligence Gate

## Implemented
- Reads the Scene's persisted Shot order and Selected Takes.
- Fails structurally when a Shot has no Selected Take or selected media is missing.
- Samples the outgoing end boundary and incoming start boundary for each consecutive cut when duration/FFmpeg evidence is available.
- Reports measurable whole-frame boundary similarity separately from semantic continuity.
- Carries persisted HIGH/CRITICAL Take continuity events into cut review.
- Explicitly reports audio boundary continuity as NOT_TESTED/REVIEW until a dedicated audible boundary analyzer exists.
- Persists `scene_assembly.json` and exposes **Evaluate Scene Assembly** in Director Timeline.
- Never changes Take selection and never exports Cinema automatically.

## Truth boundary
Boundary-frame similarity does not prove Character identity, wardrobe, props, eyeline, screen direction, action match, lighting intent, camera intent, dialogue flow, or audible smoothness. A hard cut can intentionally have large visual change. `cinema_ready` means structurally assemblable, not creatively approved.

## Machine acceptance still required
Windows/AMD/ComfyUI generated footage, FFmpeg boundary sampling, and real scene-cut quality are NOT TESTED on the Creator machine.
