# Autonomous Repair Planning & Multi-Pass QC Gate

Status: **PASS (software QA)** / **NOT TESTED on Creator AMD/ComfyUI machine**.

Film Lab can run a bounded repair cycle against the current Director A/B candidate. Each pass is diagnosed by Director Quality Control, forks a new candidate, rescans available persisted continuity evidence, and is promoted as the working best candidate only when its QC penalty improves by the configured minimum and introduces no new HIGH/CRITICAL continuity regression.

Safety invariants:
- Maximum automatic pass budget is 5.
- Existing Takes are never overwritten.
- Selected Take status is snapshotted and must remain unchanged.
- A failed/non-improving repair is not promoted.
- Specialized/manual-only strategies stop the loop rather than being silently substituted.
- Creator approval remains required for final Take selection.

The QC score is a deterministic severity penalty for repair planning, not a claim of perceptual film quality. Real render quality remains NOT TESTED until machine acceptance.
