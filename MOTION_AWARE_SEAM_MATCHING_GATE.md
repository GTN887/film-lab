# Motion-Aware Seam Matching Gate

Status: PASS (software QA) / NOT TESTED (real Windows AMD/ComfyUI footage)

Film Lab now estimates coarse source-vs-repair motion at both localized repair boundaries and records velocity/direction evidence. The evidence is used conservatively to choose a safer xfade/acrossfade duration before intelligent seam reassembly.

Truth boundary: this is deterministic coarse translation/motion matching. It does not perform optical-flow retiming, frame interpolation, motion warping, biometric identity certification, or prove a visually perfect seam. Real generated-footage acceptance remains required.
