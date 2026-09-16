# Film Lab — Authoritative Code Audit

Audit basis: the uploaded `z493xr.zip` (216 files), the uploaded Grok/Cursor history text, and the earlier FilmLab Creator Edition reconstruction. This document distinguishes code presence, automated verification, and hardware/runtime proof.

## Decision

`z493xr.zip` is the authoritative functional base. Creator Edition is **not** a competing application anymore. Its useful contribution is the Creator-facing native-window strategy and its stricter Project → Scene → Shot → Take review model. The authoritative build preserves the much larger z493xr feature base and adds a dedicated native desktop launcher while retaining localhost/browser as backup.

## Verification performed

- Full Python test suite: **220 passed** after consolidation.
- Source inventory: **216 files** before consolidation.
- Main UI: `app.py` ~5.3k lines plus `film_lab/ui_handlers.py` ~7k lines and `film_lab/studio.css` ~1.1k lines.
- Automated tests cover AMD I2V adapter logic, UI helpers, desktop packaging, project/offline behavior, character/consistency, craft desks, Mark & Direct helpers, set building, effects, quality, playback, pipeline, providers, UGC, voice profiles, and more.
- This environment does **not** have the Creator's Windows AMD GPU/ComfyUI installation, so a real RX 5600 XT generative render is not certified by this audit.

## Functional truth matrix

| System | Status | What the source supports |
|---|---|---|
| Core Gradio application | REAL / TESTED | Large integrated UI, localhost launch, queueing and handlers; automated suite passes. |
| Local project folders/persistence | REAL / TESTED | `film_lab/project.py` persists project metadata and production folders. |
| Stills ingest | REAL / TESTED | Project ingest and still workflows exist. |
| Shot cards / queue | REAL / TESTED | Structured shot configuration, queue and persistence are implemented. |
| FFmpeg / Ken Burns fallback | REAL | Genuine MP4 fallback/utility path; it is not true generative actor motion and must remain secondary. |
| Stitch / reel assembly | REAL / TESTED | FFmpeg-oriented assembly code and tests exist. |
| Writing Studio | REAL locally; cloud CONDITIONAL | Local templates/drafts are real. Provider generation depends on user-owned API keys/network and is not required for offline use. |
| Character Bible | REAL / TESTED | Character profiles, refs, descriptors and persistence exist. |
| Character consistency | PARTIAL | Start-still consistency is real; InstantID/FaceID/PuLID-class integrations are explicitly stubs/advanced until matching ComfyUI nodes exist. |
| Voice | PARTIAL / graceful fallback | Voice profiles and several local backend probes exist. A placeholder WAV fallback is real but is not cinematic neural voice acting. |
| Music / score | PARTIAL | Cue/import/local-bed utilities exist; advanced generative music depends on optional engines. |
| Lighting | REAL as direction/prompt state | Presets and injection exist; this is not a physical relighting foundation model. |
| Effects / finish | PARTIAL | FFmpeg-style finishing is real; some generative effect workflows explicitly fall back or remain stubs. |
| Motion Desk | PARTIAL / CONDITIONAL | ComfyUI I2V adapter and workflows are real code. Actual generative motion requires a working local ComfyUI/model/hardware stack. No successful RX 5600 XT render is proven here. |
| Mark & Direct | PARTIAL | Selection/direction/state machinery exists. Source explicitly refuses to fake missing inpaint/regeneration workflows. Full targeted generative rewrite is not certified. |
| Scene/Set building | PARTIAL | Set/scene data and image-analysis helpers exist. It is not yet a complete editable 3D world/geometry engine. |
| Take/variation concepts | PARTIAL | Variations and production review concepts exist, but the approved Director review-room experience still needs consolidation/polish around persistent Scene/Shot/Take semantics. |
| Director Bridge / MCP | STUB / COMING SOON | Source explicitly calls this a local stub; do not advertise as working integration. |
| CLI | STUB | Source labels it a stub. |
| Cloud/provider adapters | CONDITIONAL | Some provider code is implemented, but readiness depends on keys/endpoints; missing providers must remain Off/Coming soon. |
| Desktop installation | REAL / TESTED structure | Windows batch/VBS/Inno packaging exists and tests pass. |
| Dedicated Film Lab native window | NEW / TESTED structurally | Added `film_lab/native_desktop.py` + `OPEN_FILM_LAB_APP.bat`; pywebview hosts localhost in a Film Lab window. Browser remains backup. Windows runtime acceptance still required. |

## Obsolete / demoted pieces

- The old tiny `film-lab-starter`, `starter-amd`, `home-hub`, and `dark-studio` packages are historical sources, not authoritative applications.
- Creator Edition's separate 20-file mini application is superseded as a standalone branch. Its native desktop-shell idea is merged here.
- Ken Burns is a fallback/utility, never proof of generative motion.
- Any UI label that implies InstantID/FaceID, MCP, advanced generative effects, or targeted Mark & Direct is functional must be treated as Stub/Conditional until the required local graph/engine is present and runtime-tested.
- Grok/Cursor completion messages are historical evidence only; source + tests + runtime results control status.

## Authoritative architecture going forward

One application. One source tree. Creator-facing workflow remains **Create → Direct → Produce**. Production state should converge on **Project → Story → Characters/Sets → Scene → Shot → Take → Selected Take → Cinema → Export**. Localhost is an implementation detail and browser backup, not the intended daily interface.

## Next runtime gates

1. Windows native-window acceptance: `OPEN_FILM_LAB_APP.bat` opens one Film Lab window without requiring visible browser chrome.
2. Existing-project migration/compatibility on the Creator's current `data/` directory.
3. Real AMD/ComfyUI generation: one still + prompt → genuine motion MP4, with engine/model recorded.
4. Take Board: generated MP4 becomes a persisted Take, survives restart, can be selected/rejected, and selected Take flows to Cinema.
5. Mark & Direct: targeted regeneration must produce a new Take; otherwise remain PARTIAL.
6. Scene World: only graduate from PARTIAL when persistent editable spatial/camera state is demonstrably used by generation.

No additional desk counts as complete merely because a page or button exists.


## Performance choreography
- Multi-actor choreography state/conditioning: REAL / TESTED.
- Renderer enforcement: PROMPT_ONLY/PARTIAL unless proven temporal + actor-specific spatial bridges are both wired.
- Actual AMD choreography render: NOT TESTED.


## Lip Sync + Facial Performance Bridge
- Character-bound dialogue audio bridge: REAL / TESTED.
- Multi-speaker stable-ID audio assignment: REAL / TESTED.
- Facial-performance workflow bridge: REAL / TESTED at software boundary.
- Actual AMD/ComfyUI lip-sync render: NOT TESTED.


## Voice Acting & Emotional Delivery
- Character-bound voice acting state (emotion, pace, emphasis, intensity, delivery, pauses): REAL / TESTED.
- Conditioning/prompt integration: REAL / TESTED.
- Evidence-based expressive voice workflow bridge: REAL / TESTED at software boundary.
- Actual expressive voice render on Creator machine: NOT TESTED.

## Gradio 6 / Director Timeline drag checkpoint
Film Lab's Gradio 6 constructor blocker was repaired and `app.build_ui()` now completes under Gradio 6.5.1. The Director Timeline now includes a visual draggable surface backed by persistent production edits. Browser/native-window drag acceptance remains NOT TESTED until the Creator machine run; the precision Move & Save path remains the certified fallback.

## 358-test checkpoint — Director Timeline playback synchronization
- Added `film_lab/playback_sync.py` for exact Scene/Shot selected-Take resolution and persistent playhead state.
- Director Timeline now loads the selected real Take, exposes a scrub/playhead control, renders a timeline cursor, and can freeze the persisted second for Mark & Direct preparation.
- Scrub state clamps to known Take duration and persists in `director_playback.json`.
- Browser/native continuous video-currentTime coupling is intentionally not certified; installed-machine acceptance remains required.
- Full regression: **358 passed, 0 failed, 13 warnings**.
- Compile check: **PASS**.

## 452-test checkpoint — Asymmetric J/L-cut Cinema assembly

- Persistent Take metadata stores explicit Director J-cut lead and L-cut tail timing without replacing source media or changing selection.
- Cinema executes bounded asymmetric audio placement when every Selected Take has a proven audio stream; mixed/missing evidence keeps the truthful visual-only fallback.
- Creator-facing Take Board Cinema export now uses the authoritative audio-preserving path.
- Full regression: **452 passed, 0 failed**.
- Python compilation and full Gradio UI construction: **PASS**.
- Synthetic local FFmpeg output with video and audio streams: **PASS**.
- Audible Creator-footage quality and Windows/AMD acceptance: **NOT TESTED**.

## 467-test recovered checkpoint — Source-handle Split Edits

- Recovered forward from the verified 452-test package because the claimed personal-account 467 archive could not be retrieved.
- Picture in/out timing is now separate from J-lead/L-tail audio timing.
- Cinema validates real incoming pre-roll and outgoing post-roll from the same source Takes and refuses to fabricate missing handles.
- FFmpeg execution trims picture and audio independently, shifts/mixes audio, preserves provenance, and creates a new output without changing Selected Takes.
- Full regression: **467 passed, 0 failed**.
- Python compilation and full Gradio UI construction: **PASS**.
- Synthetic local same-source-handle FFmpeg output with video and audio streams: **PASS**.
- Audible Creator-footage quality and Windows/AMD acceptance: **NOT TESTED**.

## 480-test checkpoint — Scene-Level Room-Tone Beds

- Persistent Director-assigned Scene beds include copied media, SHA-256 provenance, gain, fades, enable state, note, and reload-safe Scene binding.
- Scene Assembly reports bed availability truthfully and blocks readiness when explicitly assigned media is missing.
- Cinema assembles Selected Takes per Scene, preserves Split Edits/program audio, mixes the Scene bed continuously, and writes an audio-edit audit manifest.
- Full regression: **480 passed, 0 failed**.
- Python compilation and full Gradio UI construction: **PASS**.
- Synthetic local FFmpeg Cinema output with program audio plus room tone: **PASS**.
- Audible Creator-footage quality and Windows/AMD acceptance: **NOT TESTED**.
