# Film Lab Roadmap

## North star
Project → Story → Characters/Sets → Scene → Shot → Take → Selected Take → Cinema → Export

Creator flow: Upload → Direct → Create → Review → Refine → Export.

## Milestone 1 — Production spine
- [x] Persistent Take records with real media paths.
- [x] Review / Selected / Rejected state.
- [x] Exactly one Selected Take per Shot.
- [x] Persistent Director Notes, tags, generator/model metadata.
- [x] Generated/imported real video can be registered as a Take.
- [x] Cinema manifest consumes Selected Takes only.
- [x] Real single-Take Cinema copy and multi-Take ffmpeg stitch service.
- [x] Local authoritative Take Board controls wired to persistent actions (239-test recovery build).
- [ ] Import the complete authoritative application source tree into GitHub so repository CI can exercise app.py/ui_handlers.py directly.
- [ ] Verify Take Board controls in the running Creator UI on Windows.
- [ ] Verify genuine AMD/ComfyUI generation on Creator hardware.

## Milestone 2 — Director production loop
- [ ] Generated MP4 appears automatically on Take Board with engine/model metadata.
- [ ] Mark & Direct targeted regeneration creates a new Take while preserving the original.
- [ ] Persistent Scene World state is consumed by generation.
- [ ] Character continuity/identity references flow through shots and Takes.
- [ ] Director Command orchestrates Scene World, performance, camera, motion and generation.

## Milestone 3 — Film finishing
- [ ] Selected Takes flow into Cinema timeline/order controls.
- [ ] Voice/audio is attached to production state and export.
- [ ] Effects/finish clearly distinguish real ffmpeg operations from conditional generative workflows.
- [ ] Long-form sequence export and recovery are regression tested.

## Milestone 4 — Creator desktop release
- [ ] Dedicated Film Lab native window verified on Windows without browser chrome in normal use.
- [ ] Existing project migration/compatibility verified.
- [ ] Installer/release packaging verified.
- [ ] End-to-end acceptance: create/open project → generate/import → Take Board → select/direct → Cinema → exported film.

## Truth rules
PASS / PARTIAL / FAIL / NOT TESTED and REAL / UI-ONLY / STUB are mandatory. UI presence never counts as functional completion. Hardware-dependent features remain NOT TESTED until exercised on the target machine.
