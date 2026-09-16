# Shot-to-Shot Lighting & Color Continuity Gate

Status: software implementation PASS when the full suite passes.

Film Lab samples the outgoing and incoming boundary frames of consecutive Selected Takes and compares luminance/exposure, contrast, and coarse RGB color balance. Director metadata may explicitly allow a lighting/color change; that preserves REVIEW rather than silently declaring the discontinuity correct.

Truth boundary: this is deterministic image-statistics evidence. It does not infer physical color temperature, key/fill direction, skin tone identity, semantic lighting motivation, or artistic correctness. Real Windows/AMD/ComfyUI footage quality remains NOT TESTED until Creator-machine acceptance.
