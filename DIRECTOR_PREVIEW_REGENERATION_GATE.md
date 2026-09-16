# Director Preview & Regeneration Loop Gate

- Exact Scene/Shot Selected Take + persisted playhead capture: **REAL / TESTED**
- Snapshot of active actor/dialogue/reaction/camera context at playhead: **REAL / TESTED**
- Regeneration forks a new Take and preserves source: **REAL / TESTED** at software boundary
- Candidate provenance stores playhead + preview context: **REAL / TESTED**
- A/B source/candidate review state: **REAL / TESTED**
- Candidate does not replace source until Creator accepts: **REAL / TESTED**
- Accept candidate selects it and preserves playhead: **REAL / TESTED**
- Reject candidate preserves source selection: **REAL / UI wired; regression covered by production status behavior**
- Actual ComfyUI/AMD regeneration: **NOT TESTED**
- Visual identity/performance correctness of regenerated region: **NOT TESTED**

Film Lab must not call a candidate visually correct merely because the renderer returned a video. Runtime/model certification remains separate.
