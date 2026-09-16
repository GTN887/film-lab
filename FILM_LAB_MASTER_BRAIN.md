# Film Lab Master Brain — Authoritative Handoff

## Purpose
This document is the portable engineering memory for Film Lab. A new chat or engineer should read it before changing the project. Do not restart the architecture, remove completed systems, or treat UI-only work as functionality.

## Creator / engineering contract
The user is Creator / Studio Owner. Film Lab is a local-first AI filmmaking application, not a collection of disconnected demos. The Creator should direct films; internal technical work should follow Inspect → Back up → Implement → Run → Detect → Diagnose → Repair → Retest → Regression test → QA. Never pretend to access the Creator's PC. Never modify Windows, Explorer, registry, services, drivers, security, PATH, startup, taskbar, or unrelated applications without explicit Creator approval.

Completion truth uses PASS / PARTIAL / FAIL / NOT TESTED and REAL / UI-ONLY / STUB. A control is not complete merely because it is visible or clickable; it must perform its intended real operation. Do not claim AMD/ComfyUI success until the Creator machine actually proves it.

## Product north star
Project → Story → Characters / Sets → Scene → Shot → Generate → Takes → Direct / Regenerate → Select → Cinema → Export.

Creator UX: Upload → Direct → Create → Review → Refine → Export.

Durable hierarchy: Project → Story → Characters → Sets → Scenes → Shots → Takes → Voices → Media → Director Notes → Render Jobs → Final Film.

Core persistent concepts include Scene World, stable Character IDs and Set IDs, Director Command, Take Board, Mark & Direct, Character Bible, Writing Studio, Voice, Cinema, continuity intelligence, provider/model adapters, and long-form scene/shot/take assembly. Model clip duration must never become project duration.

## Locked UX principles
Film Lab should open as a dedicated desktop application, not visibly as a browser/localhost page. The approved Take Board visual language is dark professional charcoal with blue/purple accents and navigation for Home, Writing, Scene World, Motion, Take Board, Mark & Direct, Cinema, Assets. The project selector uses a persistent Matching Projects list; Selected Project means browsing, Current/Open Project means loaded production.

Home is Director-first: large Director Command, reference/script uploads, Create Scene, production status, result preview, then advanced desks. Prompting is communication with the Director system, not a separate desk.

## Implemented production stack
Persistent production.json Take storage; one Selected Take per Scene+Shot; real-media requirement; Cinema export; Take Board actions/notes/tags; generation queue registration; Mark & Direct non-destructive Take forking; Scene World; Character state; structured conditioning; generator capabilities; ComfyUI discovery/routing; runtime preflight; generation gating; render certification; Creator Certification; production-aware Director Command; continuity preserve/change contracts; advanced conditioning bridge; evidence-based conditioning profiles; multi-character slot assignment; regional actor control; performance timelines; choreography; dialogue/voice synchronization; lip-sync/facial-performance bridge; voice acting; unified audio performance timeline; Director Timeline; Gradio 6 compatibility; playback synchronization; Director preview/regeneration; visual continuity certification; registered Character/object visual targets; automatic target tracking; full-Take continuity scanning; continuity problem localization; temporal video and A/V segment repair; intelligent seam blending; motion-aware seam matching; motion retiming; optical-flow transition alignment; automated Take QC; autonomous bounded multi-pass repair planning; Shot readiness and Director Take ranking; Scene Assembly Intelligence; cross-shot action/screen-direction checks; Camera Geography / 180-degree intent; Shot-to-Shot Lighting & Color Continuity; Dialogue & Audio Cut Continuity; Audio-Preserving Cinema Assembly; explicit asymmetric same-source-handle J-cut / L-cut Cinema assembly with separate picture timing; persistent Scene-Level Room-Tone Beds with Cinema enforcement and provenance.

## Current audio / Cinema truth
Dialogue & Audio Cut Continuity performs deterministic decoded-PCM boundary analysis for RMS/peak and near-silence proxies, carries persisted dialogue timing evidence, and honors explicit Director J/L-cut and intentional level/silence metadata. It does not infer semantic dialogue, speaker identity, acoustics, microphone perspective, or artistic correctness.

Audio-Preserving Cinema Assembly uses FFmpeg and maps both video and audio when every Selected Take has a proven audio stream. Explicit persistent Director metadata separates picture in/out from audio timing. Incoming audio can use proven earlier pre-roll and outgoing audio can use proven later post-roll from the same source Takes. Requested handles are bounded and validated; missing or short handles are rejected, never fabricated. If audio is not proven for all clips, Film Lab retains the established truthful fallback behavior.

## Director authority
Automatic diagnosis, ranking, and repair never silently changes the Director's final Selected Take. Repairs are new Takes. Multi-pass repair has a bounded budget and rejects regressions. Machine QC scores are technical evidence, not proof of acting quality, story quality, anatomy, Character identity, or artistic preference.

## Current software checkpoint
Authoritative package: `FilmLab-Authoritative-480tests-RoomTone.zip`.
Recovery lineage: independently verified recovered 467-test Split Edits checkpoint. Software QA: 480 tests passed, 0 failed; 2,937 repeated warning occurrences from existing Pillow/Gradio categories. Python compile PASS. Full Gradio UI build PASS. Local synthetic Scene room-tone Cinema render PASS. Creator-machine audible acceptance NOT TESTED.

## Real-machine acceptance still required
Windows ComfyUI connection; RX 5600 XT generation; still+instruction → genuine AI MP4; live generated Take selection; Cinema export from generated Takes; restart persistence in installed app; native pywebview behavior; regional/temporal/multi-actor rendering; voice/lip-sync output; physical drag behavior; real footage continuity scanning/tracking/repair; audible A/V seam quality; motion/optical-flow quality; scene assembly, lighting/color, audio-cut analysis, and audio-preserving Cinema export on actual Creator footage are NOT TESTED until machine acceptance.

## Source control / recovery
Private GitHub repository: GTN887/film-lab. Issue #1 is Milestone 1: Real Motion → Persistent Take → Cinema Export and must remain open until real AMD/ComfyUI machine acceptance. Keep the authoritative ZIP, older verified ZIPs, GitHub history, and Creator data. Never delete or overwrite old Creator data merely because a newer build exists.

## Next engineering direction
The exact next unfinished task is Gain Matching / Mix Automation. After that, add final Cinema Audio QC before export. Do not infer room identity or artistic intent from amplitude alone.

## New-chat instruction
When this file is attached to a new chat, say: “This is the Film Lab Master Brain. Read it as the authoritative handoff, preserve all implemented architecture and truth rules, inspect the newest authoritative ZIP/source, and continue from the current checkpoint. Do not restart Film Lab or replace working systems with mock UI.”
