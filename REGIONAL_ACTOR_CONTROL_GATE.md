# Regional Actor Control Gate

Status after this checkpoint:

- Stable Character ID can be attached to a Mark & Direct region: REAL / TESTED.
- Saved lasso masks can be resolved to the intended Character ID: REAL / TESTED.
- Generation conditioning carries character-specific regional controls: REAL / TESTED.
- Explicit `film_lab_actor_mask:<character-id>` workflow slots can receive the real saved mask: REAL / TESTED at the graph-injection boundary.
- `mask_regeneration` is only reported wired when an explicit actor-mask slot and an inpaint/mask-capable graph node are both present: REAL / TESTED.
- Character-specific region prompt slots can receive the intended instruction: REAL / TESTED.
- Mark & Direct can request a specific stable Character/region and records whether actor isolation was actually enforced by the render route: REAL / TESTED structurally.
- Actual actor-isolated AMD/ComfyUI render on the Creator's Windows machine: NOT TESTED.
- No claim is made that arbitrary ComfyUI inpaint graphs are automatically compatible. A compatible validated graph/slot is required.
