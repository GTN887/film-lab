# FILM LAB MASTER BRAIN / CONTINUATION HANDOFF
**Version:** 2026-09-15 — preserved history plus independently recovered 467-test Split Edits checkpoint  
**Purpose:** Upload this file into a new ChatGPT conversation so development can continue without restarting Film Lab or losing the engineering decisions from the current chat.

---

## 1. HOW TO USE THIS FILE IN A NEW CHAT

Upload this file together with **FilmLab-Authoritative-448tests.zip**, **Film Lab Take Board Interface.png**, and the newest verified authoritative Film Lab ZIP if a later one exists. Then say:

> **Continue Film Lab development from this Master Brain and the attached authoritative ZIP. Treat the ZIP as source of truth. Do not restart the project, redesign completed systems, or claim machine functionality that has not been tested. Preserve all completed architecture, tests, documents, and truth-status rules.**

If there is any conflict between an older chat recollection and the attached authoritative source, inspect the source and preserve the newest verified implementation.

---

## 2. CURRENT VERIFIED CHECKPOINT

### Superseding Workspace checkpoint
**FilmLab-Authoritative-480tests-RoomTone.zip**

This checkpoint continues from the independently recovered and verified 467-test Split Edits archive. Scene-Level Room-Tone Beds now persist Director-assigned media/provenance, participate in Scene Assembly, and render through Cinema without changing Selected Takes. Verification: **480 tests passed, 0 failed**; Python compilation **PASS**; full Gradio UI build **PASS**; synthetic FFmpeg Scene-bed Cinema render **PASS**. Windows/AMD/Creator-footage and artistic listening acceptance remain **NOT TESTED**.

The exact next unfinished task is **Gain Matching / Mix Automation**, followed by Final Cinema Audio QC.

### Verified authoritative build
**FilmLab-Authoritative-448tests.zip**

This handoff preparation independently re-verified the package from a clean extraction:
- **448 tests passed**
- **0 failed**
- **13 existing warnings**
- Python compilation: **PASS**
- Full Film Lab Gradio UI build: **PASS** (`app.build_ui()` returned `Blocks`)

### Source root inside the ZIP
The current package extracts to a source folder named:
**`fl_cinema_audio/`**

### Latest completed engineering batches
- **444 — Dialogue & Audio Cut Continuity**
- **448 — Audio-Preserving Cinema Assembly**

The 448 package is the newest verified authoritative source for a new chat. Do not restart from 440, 444, or an older ZIP when 448 is attached.

### Historical next task at 448
**True Asymmetric J-Cut / L-Cut Assembly** — completed and superseded by the recovered 467-test source-handle Split Edits checkpoint above.

The goal is to make Film Lab actually move outgoing or incoming audio across the picture cut using explicit Director timing while preserving provenance and source media. Do not silently infer dialogue semantics, speaker identity, or artistic intent.

---

## 3. CREATOR / ENGINEERING ROLES

**Creator / Studio Owner:** user  
**ChatGPT:** Film Lab Architect, source reviewer, code builder, QA, filmmaking mentor  
**Grok/Cursor:** only when true live-Windows-machine access is needed

Cost-saving operating model:
**Creator → ChatGPT architect/code work → one live-machine agent only if genuinely needed → QA at milestones**

Do not recommend stacks of paid AI agents or unnecessary subscriptions.

---

## 4. PRODUCT VISION

Film Lab is a private/local-first AI filmmaking desktop application.

It should feel like:
**double-click Film Lab icon → dedicated Film Lab window opens**

Final Creator UX should not expose:
- Chrome/Edge
- visible localhost URL
- Python terminals
- ComfyUI internals
- developer console noise

Localhost can remain internal/emergency backup.

### Core hierarchy
**Project → Story → Characters → Sets → Scenes → Shots → Takes → Voices → Media → Director Notes → Render Jobs → Final Film**

### Creator workflow
**Upload → Direct → Create → Review → Refine → Export**

### North-star production workflow
**Project → Story → Characters/Sets → Scene → Shot → Generate → Takes → Direct/Regenerate → Select → Cinema → Export**

### Long-form rule
A model's individual clip-length limit must never become Film Lab's project-duration limit.

Long-form assembly:
**Story → Scenes → Shots → Takes → Selected Takes → Sequence → Final Film**

---

## 5. THE CENTRAL ARCHITECTURAL IDEA: SCENE WORLD

Film Lab uses a persistent **Scene World** containing production state such as:
- characters
- sets
- objects/props
- blocking
- lighting
- weather/time
- camera state
- prior-shot references
- continuity anchors
- Director instructions

Characters and sets require stable persistent IDs.

The system must use persistent context instead of treating every generation as an unrelated prompt.

---

## 6. DIRECTOR COMMAND

The Home page is Director-first.

Director Command accepts natural-language filmmaking instructions and orchestrates internal systems.

Home architecture:
1. Film Lab header/status + content mode
2. Large **Director Command** hero
3. Production status pipeline
4. Real result/preview area
5. Advanced desks below

Production status concept:
**Planning → Character → Set → Camera → Motion → Voice → Takes → Cinema**

Director Command should:
- read Scene World
- resolve Character IDs
- read previous Selected Take
- inspect generator capabilities
- generate a production-aware plan
- separate planning from mutation
- apply the plan only when requested
- preserve continuity unless the Director explicitly changes something

Prompting is communication with the Director system, not a separate isolated "prompt desk."

---

## 7. UI / UX SOURCE OF TRUTH

Approved visual reference:
**Film Lab Take Board Interface.png**

The intended style:
- dark professional interface
- charcoal background
- blue/purple accents
- recognizable film-production layout

Top navigation:
- Home
- Writing
- Scene World
- Motion
- Take Board
- Mark & Direct
- Cinema
- Assets

Left project navigation:
- Overview
- Script
- Characters
- Sets & Locations
- Scene World
- Storyboard
- Take Board
- Mark & Direct
- Edit/Cinema
- Audio & Voice
- Assets
- Export

Take Board should include:
- Scene / Shot selectors
- large selected video player
- Take Details
- Director Notes
- Tags
- Generate New Take
- Mark & Direct
- all Takes strip/cards
- status choices such as Reject / Review / Selected
- Compare Takes
- Keep Take
- Reject Take
- Send to Cinema

---

## 8. PROJECT SELECTOR RULE

Previously approved selector behavior must remain stable:

- Find Project text field
- persistent scrollable **Matching Projects** list
- click project → highlights one row
- **Selected Project** means browsing
- **Current Project** means actively loaded production
- **Open Project** changes Current Project

Do not revert to an unstable floating dropdown.

Eventually all desks share current Project / Scene / Shot state.

---

## 9. NON-NEGOTIABLE TRUTH RULES

Status vocabulary:
- **PASS**
- **PARTIAL**
- **FAIL**
- **NOT TESTED**

Implementation truth vocabulary:
- **REAL**
- **UI-ONLY**
- **STUB**

Permanent rules:
- UI presence is not functionality.
- **If it is not clickable, it is not done.**
- If clicking does not perform the intended real operation, it is not functional.
- Do not confuse mocked/software tests with real-machine certification.
- Do not claim "seamless," "identity preserved," "real motion," or similar unless evidence supports it.
- Never create fake demo theater or pretend generated media exists when it does not.

Real completion means:
- Creator opens Film Lab
- clicks the control
- intended real operation occurs
- persistence/integration works
- result remains correct after expected workflow/restart where applicable

---

## 10. INTERNAL DEVELOPMENT PIPELINE

The Creator should not be part of the debugging pipeline.

Internal engineering cycle:
**Inspect → Back up → Implement → Run → Detect errors → Diagnose → Repair → Retest → Regression test → QA**

Creator involvement should be normal creative use and final acceptance testing.

---

## 11. FEATURE PHILOSOPHY

Do not organize Film Lab as "a desk equals a feature."

Functional categories:

### CREATE
- story
- characters
- sets
- shots
- images
- video
- voices

### DIRECT
- camera
- performance
- emotion
- blocking
- motion
- Mark & Direct
- alternatives

### PRODUCE
- Takes
- continuity
- editing
- sound
- Cinema
- export

---

## 12. CORE IMPLEMENTED PRODUCTION SYSTEMS

The following systems were implemented before the current checkpoint and should be preserved:

### Production persistence
Persistent production data and Take records.

Rules:
- exactly one Selected Take per Scene + Shot
- real video requirement where appropriate
- persistent notes/tags/status
- Cinema handoff

### Cinema export
Exports Selected Takes.
Supports one-video copy or multi-shot FFmpeg stitching.

### Take Board
Persistent Take operations:
- notes
- tags
- status
- selected state
- Cinema handoff

### Queue integration
Successful generation auto-registers a persistent Take.
Failed generation must not create a fake Take.

### Mark & Direct
- source Take remains preserved
- target frame can be prepared from actual playhead
- instruction/mark creates new candidate Take
- regeneration is non-destructive

---

## 13. CONDITIONING / COMFYUI ARCHITECTURE

Implemented software-side systems include:
- structured conditioning
- generator capability routing
- ComfyUI discovery
- workflow routing
- runtime preflight
- generation gating
- render certification
- Creator Certification UI

Advanced conditioning supports explicit slots for:
- reference image
- identity image
- camera
- blocking
- objects
- actor regions/masks
- later performance/lip/voice channels

Evidence-based workflow profiling recognizes known connected layouts such as:
- InstantID
- FaceID
- PuLID
- IPAdapter/reference paths

Do not claim identity enforcement unless an identity-capable graph path is actually wired.

---

## 14. CHARACTER / PERFORMANCE SYSTEMS

Implemented engineering foundation includes:
- persistent Character state
- multi-character assignment using stable IDs
- spatial blocking
- actor-bound regions/masks
- Actor Performance Timeline
- model-enforcement bridge
- Performance Choreography
- Dialogue + Voice synchronization
- Lip Sync + Facial Performance bridge
- Voice Acting & Emotional Delivery
- Audio Performance Timeline
- Director Timeline Editor
- Camera Direction Timeline

Truth boundary:
software wiring may be REAL while actual output quality on the Creator's machine remains NOT TESTED.

---

## 15. PLAYBACK / REGENERATION / CONTINUITY

Implemented systems include:
- selected Take playback synchronization
- persistent playhead
- scrub / exact frame prep
- Director Preview & Regeneration Loop
- source preservation
- A/B candidate review
- Continuity-Aware Shot Intelligence

Continuity contracts distinguish:
- requested changes
- preservation requirements

Example:
If the Director says:
"Make Sarah more suspicious when Michael says the last line"

Film Lab should change Sarah's performance while preserving unspecified:
- identity/appearance
- wardrobe/hair/makeup
- set/location
- props
- lighting
- blocking
- camera
- other actors
- dialogue/audio where appropriate

Unknown Character IDs should never be silently targeted.

---

## 16. VISUAL CONTINUITY SYSTEMS

Implemented:
- Visual Continuity Certification
- project-bound Character/Object visual target registration
- automatic target tracking
- Full-Take Continuity Scanning
- problem localization
- persistent repair plans

Visual certification uses deterministic frame evidence such as:
- pixel difference
- RMS
- edge/composition difference
- histogram similarity
- perceptual similarity

Important truth:
pixel/frame similarity does **not** prove:
- Character identity
- wardrobe sameness
- hair sameness
- prop semantics
- anatomy correctness
- story correctness

Those require specialized evidence or Director review.

---

## 17. TEMPORAL REPAIR STACK

Implemented non-destructive repair stack includes:

### Temporal Segment Repair
Replaces only a localized visual region in time:
**source prefix + repaired window + source suffix**

### Localized Audio + Video Segment Repair
Can replace localized video and audio when both are proven.

### Intelligent Seam Blending
Uses FFmpeg:
- `xfade`
- `acrossfade`

### Motion-Aware Seam Matching
Analyzes coarse source/repair motion near repair boundaries and adjusts recommended blend duration.

### Motion Retiming & Transition Alignment
Can detect early/late repaired motion and perform conservative timing alignment.

### Optical-Flow Transition Alignment
Capability-gated path using FFmpeg `minterpolate` when actually available/executed.

Truth:
optical-flow interpolation does not prove semantic or identity correctness.

---

## 18. DIRECTOR QUALITY CONTROL

Implemented:
### Automated Take Quality Control & Repair Decisions
Film Lab can classify problems such as:
- Character/object tracking issues
- motion/position issues
- global visual drift
- camera continuity issues
- performance issues
- dialogue/audio issues
- lip-sync issues
- seam issues

It can recommend a repair strategy.

### Autonomous Repair Planning & Multi-Pass QC
Bounded automatic repair cycle:
**Analyze → Diagnose → Repair → Rescan → Score → Regression Check → Promote/Reject Candidate → Repeat within budget**

Repair budget is bounded.

A repair is promoted only if it improves the targeted evidence without creating unacceptable new high/critical regressions.

Bad repairs remain as evidence but are not silently promoted.

### Final Director authority
Film Lab must NEVER silently change the final Selected Take during autonomous QC.

The Director retains final selection.

---

## 19. TAKE RANKING / SHOT READINESS

Implemented:
**Shot Readiness & Director Take Ranking**

Film Lab can evaluate all Takes for a Shot and rank technical QC evidence.

It can identify:
- missing media
- missing scans
- unresolved HIGH/CRITICAL issues
- technically strongest candidate

Important:
A higher QC score does NOT mean "best acting" or "best creative choice."

Film Lab recommendations must never automatically change the Selected Take.

---

## 20. SCENE ASSEMBLY INTELLIGENCE

Implemented Scene Assembly analysis across consecutive Selected Takes.

Pipeline:
**Selected Takes → Shot Order → Cut Boundaries → Visual Continuity → QC Carry-Forward → Scene Readiness → Director Review → Cinema**

A visually different hard cut is not automatically an error.

Film Lab does not claim pixel similarity proves:
- Character identity
- wardrobe
- props
- eyeline
- screen direction
- action matching
- lighting
- dialogue flow
- audio quality

---

## 21. CROSS-SHOT ACTION & SCREEN-DIRECTION CONTINUITY

Implemented:
- Character/object boundary position
- outgoing vs incoming tracked movement
- screen-direction comparison
- action continuity risk
- explicit eyeline intent support

Intentional movement reversals or jump cuts may be creative choices, so they should produce **REVIEW**, not automatic failure.

Missing evidence should be **NOT TESTED**, never guessed.

---

## 22. CAMERA GEOGRAPHY & 180-DEGREE INTELLIGENCE

Implemented Director/Scene geometry support:
- line of action
- camera position
- side-of-axis comparison across Shots
- warning on unexpected axis crossings

Intentional axis crossing can be explicitly allowed and remains Director-reviewed.

Truth:
current system does not claim automatic 3D camera reconstruction or semantic visual proof of 180-degree-rule compliance.

---

## 23. SHOT-TO-SHOT LIGHTING & COLOR CONTINUITY

This is the newest fully verified subsystem in the **440-test build**.

Film Lab can compare consecutive Selected Takes at edit boundaries for:
- luminance/exposure change
- contrast change
- coarse RGB color-balance change

Intentional changes can be Director-approved and marked REVIEW rather than automatically treated as failure.

Truth:
this is deterministic frame analysis, but does not claim:
- physical color-temperature measurement
- semantic light direction
- skin-tone continuity
- artistic correctness

---

## 24. DIALOGUE & AUDIO CUT CONTINUITY — COMPLETED AT 444

Implemented in **FilmLab-Authoritative-444tests.zip** and retained in 448.

Core behavior:
- analyzes decoded PCM at consecutive Selected-Take boundaries
- compares RMS/peak level and near-silence behavior
- carries persisted dialogue-timing evidence
- honors explicit Director J-cut / L-cut intent metadata
- honors intentional level/silence-change metadata
- integrates into Scene Assembly rather than living as a detached demo

Truth boundary:
- room tone is currently a level/silence proxy, not semantic acoustic matching
- Film Lab does not infer dialogue meaning, speaker identity, microphone perspective, room acoustics, or artistic correctness from PCM amplitude
- J/L-cut labels are explicit Director intent, not guessed from footage

Gate document in current source:
**`DIALOGUE_AUDIO_CUT_CONTINUITY_GATE.md`**

---

## 24A. AUDIO-PRESERVING CINEMA ASSEMBLY — COMPLETED AT 448

Implemented in **FilmLab-Authoritative-448tests.zip**.

Core behavior:
- when every Selected Take has a proven audio stream, Cinema export preserves audio
- FFmpeg picture transition uses `xfade`
- FFmpeg audio transition uses `acrossfade`
- final MP4 maps both video and audio streams
- if audio is not proven for every clip, Film Lab deliberately keeps the established visual-only path rather than falsely claiming preserved audio
- Director J/L-cut intent and explicit audio-overlap metadata are represented in an auditable transition plan

Truth boundary:
- this checkpoint does **not** yet perform true asymmetric J/L editing that shifts dialogue or room tone across the picture cut
- it does not infer semantic dialogue, speaker identity, room acoustics, or artistic mix quality
- real Windows/AMD footage and audible transition quality remain **NOT TESTED**

Key modules in 448:
- `film_lab/audio_cut_continuity.py`
- `film_lab/audio_preserving_cinema.py`
- `film_lab/cinema_export.py`

Key tests:
- `tests/test_audio_cut_continuity.py`
- `tests/test_audio_preserving_cinema.py`

Gate document:
**`AUDIO_PRESERVING_CINEMA_ASSEMBLY_GATE.md`**

---

## 24B. NEXT ENGINEERING TASK — TRUE ASYMMETRIC J-CUT / L-CUT ASSEMBLY

**Historical status:** completed by the recovered 467-test source-handle Split Edits checkpoint. This section is retained as architectural history.

This is the immediate continuation task after 448.

Required behavior:
- allow outgoing dialogue/room tone to continue underneath incoming picture (**L-cut**)
- allow incoming dialogue/room tone to begin before the incoming picture (**J-cut**)
- use explicit Director timing, not guessed semantics
- bound overlap conservatively
- preserve original source Takes and audio non-destructively
- create auditable transition/provenance metadata
- maintain existing fallback behavior when required audio evidence is missing
- keep Director final selection/approval explicit

Suggested implementation direction:
- build on `audio_preserving_cinema.py`, `cinema_export.py`, and persisted Scene Assembly transition metadata
- represent picture-cut time separately from outgoing-audio-end and incoming-audio-start
- use FFmpeg trimming/timestamp shifting/mixing/crossfade only when actual execution proves enforcement
- distinguish **PLANNED / AVAILABLE / ENFORCED / NOT TESTED** where appropriate
- do not claim semantic dialogue understanding

After true J/L assembly, the next audio layer is:
**scene-level room-tone beds → gain matching/mix automation → final Cinema audio QC before export**

---

## 25. QA CHECKPOINT HISTORY

Important later checkpoints:
- 403 — Motion-Aware Seam Matching
- 407 — Motion Retiming & Transition Alignment
- 411 — Optical-Flow Transition Alignment
- 415 — Automated Take Quality Control
- 420 — Autonomous Repair Planning & Multi-Pass QC
- 424 — Shot Readiness & Director Take Ranking
- 428 — Scene Assembly Intelligence
- 432 — Cross-Shot Action & Screen-Direction Continuity
- 436 — Camera Geography & 180-Degree Scene Intelligence
- 440 — Shot-to-Shot Lighting & Color Continuity
- 444 — Dialogue & Audio Cut Continuity
- 448 — Audio-Preserving Cinema Assembly

Each checkpoint was packaged as a versioned authoritative ZIP.

Do not delete old recovery ZIPs merely because a newer ZIP exists.

---

## 26. RUNTIME / MACHINE TRUTH

The software architecture and test suite are substantially ahead of real-machine acceptance.

The following remain NOT TESTED on the Creator's actual Windows/AMD production machine unless a later verified machine run proves otherwise:

- Windows ComfyUI connection
- actual RX 5600 XT generation
- still + Director instruction → genuine AI MP4
- generated Take appears/selects correctly in live installed app
- live Cinema export from generated Take
- installed-app restart persistence
- native pywebview desktop window
- real actor-isolated regional ComfyUI render
- actual temporal performance render
- real multi-actor choreography render
- expressive voice/lip-sync output
- continuous native playback synchronization
- real Director Preview regeneration quality
- real footage visual continuity accuracy
- real target tracking accuracy
- full-take scanning on real generated footage
- audible/visual localized repair seam quality
- motion-aware seam quality
- motion-retiming quality
- optical-flow transition quality
- automated QC accuracy on production footage
- scene assembly accuracy on production footage
- screen-direction analysis on production footage
- camera geography use in real productions
- lighting/color continuity thresholds on production footage
- dialogue/audio-cut continuity analysis on production footage
- audio-preserving Cinema assembly on actual generated Takes
- audible xfade/acrossfade quality on the Creator machine
- true asymmetric J/L-cut assembly (not yet implemented at 448)

Do not close the core real-render milestone until actual machine acceptance succeeds.

---

## 27. HISTORICAL HARDWARE CONTEXT

Previously reported machine:
- Windows 11
- Ryzen 9 7900X
- AMD Radeon RX 5600 XT, roughly 6 GB
- no NVIDIA GPU
- FFmpeg installed via winget
- ComfyUI expected on port 8188

Verify current machine state when real acceptance testing begins.

Do not automatically modify the OS.

---

## 28. WINDOWS SAFETY BOUNDARY

Because there were earlier incidents involving black desktop/taskbar/browser behavior and keyboard repetition, permanent rule:

Work only inside the verified Film Lab workspace unless the Creator explicitly approves otherwise.

Explicit approval required before modifying:
- Explorer shell
- taskbar
- registry
- Windows services
- startup
- system files
- drivers
- security settings
- PATH
- broad permissions
- scheduled tasks
- recovery settings
- unrelated applications

Do not:
- broad-kill processes
- recursively delete uncertain directories
- modify Chrome/Edge/Razer/Windows to "fix" Film Lab
- delete old Film Lab copies before verification

Unexpected system behavior:
**stop → preserve state → report**

---

## 29. GITHUB SOURCE CONTROL

Private repository:
**GTN887/film-lab**

Primary milestone issue:
**Milestone 1: Real Motion → Persistent Take → Cinema Export**

Do not close the real-machine milestone based solely on mocked/software tests.

GitHub remains the preferred source-control platform for now.

Do not migrate to GitLab merely because of a vague claim that GitLab is faster.

---

## 30. FILE / RECOVERY RULES

Permanent:
- do not overwrite the old extracted Film Lab folder
- do not delete old authoritative ZIPs yet
- do not delete `data/` without backup
- extract a new authoritative ZIP into a clearly new folder for testing
- Windows may rename duplicate downloads `(1)`, `(2)`
- preserve project data separately from build source

Long-term target:
**installed Film Lab + GitHub master source + one verified recovery backup**

Until machine acceptance is complete, keeping versioned authoritative ZIPs is appropriate.

---

## 31. USER EXPERIENCE / COMMUNICATION PREFERENCES

The Creator is not a programmer.

Use:
- simple concrete language
- one exact Creator action at a time when an action is unavoidable
- coherent engineering batches
- source-code-first implementation
- direct status reporting

Avoid:
- repeated tiny troubleshooting loops
- making the Creator serve as QA/debugger
- pretending to access the Creator's PC
- expensive tool chains unless necessary
- vague "agent theater"
- describing a next feature without actually implementing it when the Creator says **"go for it"**

When the Creator says:
- **"go for it"** → implement the next coherent engineering batch
- **"next task/page"** → continue forward from the current authoritative checkpoint

---

## 32. STANDARD ENGINEERING COMPLETION CHECKLIST

Every new Film Lab engineering batch should, when feasible:

1. Start from the newest verified authoritative ZIP/source.
2. Back up or work in a new extracted directory.
3. Inspect existing related modules before modifying them.
4. Implement the feature as integrated production logic, not isolated demo UI.
5. Add regression tests.
6. Run full tests with the source path configured correctly.
7. Run:
   `python -m compileall -q film_lab app.py`
8. Build the full UI:
   `import app; app.build_ui()`
9. Write/update a gate document.
10. Package:
   `FilmLab-Authoritative-<EXACT_TEST_COUNT>tests.zip`
11. Report exact status:
   **PASS / PARTIAL / FAIL / NOT TESTED**
12. State the real-machine truth boundary.
13. Never claim actual AMD/ComfyUI success unless it was actually run and verified.

Historical note:
A previous clean extraction initially failed pytest collection with `ModuleNotFoundError: film_lab` because `PYTHONPATH` was not set. Running:
`PYTHONPATH=. pytest -q`
passed. That was an invocation/environment issue, not a source failure.

---

## 33. CURRENT CONTINUATION INSTRUCTION

When continuing from this file:

### Source of truth
Start from:
**FilmLab-Authoritative-480tests-RoomTone.zip**

unless a newer test-certified authoritative ZIP is attached and independently verified.

### Immediate task
Implement:
**Gain Matching / Mix Automation**

Then:
- add focused regression tests
- run the full suite with `PYTHONPATH=. pytest -q`
- run `python -m compileall -q film_lab app.py`
- run a full `app.build_ui()` regression
- write/update the gate document
- package `FilmLab-Authoritative-<EXACT_TEST_COUNT>tests.zip`
- state software truth separately from real-machine truth
- update this Master Brain

### Do not restart completed architecture.
The next chat is a continuation of the same Film Lab project. Inspect the 448 source before editing and preserve working systems.

---

## 33A. HANDOFF VERIFICATION RECORD

During preparation of this new-chat package, **FilmLab-Authoritative-448tests.zip** was extracted cleanly and verified again.

Commands / equivalent checks:
- `PYTHONPATH=. pytest -q` → **448 passed, 13 warnings**
- `python -m compileall -q film_lab app.py` → **PASS**
- `PYTHONPATH=. python -c "import app; app.build_ui()"` → **PASS** (`Blocks`)

Warnings are the existing Gradio 6 constructor migration warning plus Pillow deprecation warnings; they are not test failures.

This does not certify the Creator's Windows/AMD/ComfyUI runtime. It certifies the packaged software checkpoint in the handoff environment only.

---

## 34. CREATOR'S NORTH-STAR PRINCIPLE

Film Lab is not supposed to be a pile of AI buttons.

The Creator should be able to say what they want as a filmmaker, and Film Lab should coordinate the underlying technical systems.

The product should increasingly behave like:
**Director intention → production understanding → automated technical execution → evidence-based review → Creator/Director final decision**

The Creator remains the artistic authority.

---

**END OF FILM LAB MASTER BRAIN / CONTINUATION HANDOFF**
