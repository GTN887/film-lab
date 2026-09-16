# Camera Geography & 180-Degree Scene Intelligence Gate

## Implemented
- Explicit `camera_geography_intent` per Take: line-of-action start/end, camera position, optional intentional axis-cross permission.
- Deterministic side-of-axis calculation and cross-shot camera-side comparison.
- Line-of-action orientation comparison with conservative tolerance.
- Unmotivated axis crossings are HIGH **REVIEW**, not automatic failure; explicitly allowed crossings remain REVIEW.
- Missing geography stays **NOT_TESTED**; Film Lab does not invent camera/actor positions from pixels.
- Integrated into Scene Assembly cut evidence under `metrics.camera_geography`.

## Truth boundary
This is real rule/evidence evaluation over persisted Director/Scene intent. It is not automatic 3D camera reconstruction, semantic actor/gaze recognition, or proof that a crossing is creatively wrong. Real AMD/ComfyUI footage acceptance remains NOT TESTED.
