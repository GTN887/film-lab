# Film Lab Engineering Standard

## Completion rule

If a control is not clickable, it is not done. If clicking it does not perform the intended real operation, it is not functional.

Every significant feature must be classified as one of:

- **PASS** — intended end-to-end behavior works and is verified.
- **PARTIAL** — meaningful implementation exists but complete production behavior is not verified.
- **FAIL** — implementation was tested and did not meet acceptance criteria.
- **NOT TESTED** — implementation has not yet been verified in the required environment.

Implementation truth must also distinguish **REAL**, **UI-ONLY**, and **STUB** behavior.

## Creator workflow

The Creator is not the debugging pipeline. Engineering follows:

**Inspect → Back up → Implement → Run → Detect errors → Diagnose → Repair → Retest → Regression test → QA**

The Creator performs normal creative actions and final acceptance testing.

## Product architecture

Film Lab converges on:

**Project → Story → Characters → Sets → Scenes → Shots → Takes → Voices → Media → Director Notes → Render Jobs → Final Film**

Creator-facing flow:

**Upload → Direct → Create → Review → Refine → Export**

AI/video engines are replaceable workers behind Film Lab rather than the product architecture itself.
