# Optical-Flow Transition Alignment Gate

Status is evidence-based.

- Film Lab discovers whether the installed FFmpeg exposes `minterpolate`.
- `AVAILABLE` is capability evidence only; it is not an executed render.
- `ENFORCED` is written only after the real FFmpeg motion-compensated interpolation command succeeds and creates a new persistent Take.
- The original Take is preserved.
- Retiming guardrails remain active; unsafe temporal maps are rejected.
- Audio is retimed with the localized repair and crossfaded at the boundaries.
- Boundary certification runs after reconstruction.
- Optical-flow interpolation does **not** prove Character identity, anatomy, semantic continuity, or perceived motion quality. Those require visual acceptance.
- Real Windows/AMD generated-footage acceptance remains NOT TESTED until run on the Creator machine.
