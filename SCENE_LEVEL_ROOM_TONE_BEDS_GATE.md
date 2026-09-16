# Scene-Level Room-Tone Beds Gate

## Status

- Persistent Scene-bound room-tone state: **PASS / REAL**
- Creator assignment controls: **PASS / REAL**
- Scene Assembly integration: **PASS / REAL**
- Cinema audio integration: **PASS / REAL**
- Source-handle Split Edits regression: **PASS**
- Full regression: **PASS — 480 passed, 0 failed**
- Python compilation: **PASS**
- Full Gradio UI construction: **PASS** (`Blocks`)
- Local FFmpeg Cinema render: **PASS** — two Selected Takes plus looped Scene bed produced video and audio streams with an audit manifest
- Windows/AMD/Creator-footage acceptance: **NOT TESTED**
- Artistic room-tone/audio quality: **NOT TESTED**

## Inspection and architecture

The implementation extends the existing `Project`, `ProductionStore`, Scene Assembly, Score/Audio UI, audio-preserving Cinema exporter, and Split Edits path. It does not create a parallel filmmaking application or modify original Takes.

`RoomToneStore` persists one explicit Director assignment per Scene in `scene_room_tones.json`. Imported media is copied non-destructively under `audio/room_tone/<scene_id>/` and records its original filename, SHA-256 provenance, persistent path, enabled state, gain, fades, assignment time, and Director note. Project initialization now preserves this production-data directory.

The Score Desk provides a real Scene Room Tone control: Scene ID, audio upload, Cinema enable/disable, gain, fades, and Director note. Success is reported only after the media copy and persistent state exist.

Scene Assembly reports `PASS`, `REVIEW`, `FAIL`, or `NOT TESTED` room-tone evidence. An unassigned optional bed is `NOT TESTED`, an explicitly disabled bed is `REVIEW`, an available enabled bed is `PASS`, and missing assigned media is `FAIL` and blocks Cinema readiness.

Cinema groups ordered Selected Takes by Scene, assembles each Scene through the existing audio/Split Edits logic, loops and mixes its assigned bed continuously across the Scene master, then assembles Scene masters into the final film. Existing program audio is preserved and mixed; silent picture receives the bed as its proven audio stream. The output receives an adjacent `.audio_edit.json` audit manifest with Scene, Take, room-tone provenance, enforcement state, and truth boundary.

## Affected files

- `film_lab/room_tone.py` (new)
- `film_lab/project.py`
- `film_lab/cinema_export.py`
- `film_lab/scene_assembly_intelligence.py`
- `film_lab/ui_handlers.py`
- `app.py`
- `tests/test_scene_room_tone.py` (new)

## Verification

Thirteen focused tests cover copying, persistence/reload, Scene isolation, validation, enable state, production directory creation, program-audio mixing, silent-picture mixing, disabled behavior, Scene Assembly evidence, missing-media blocking, and Cinema audit/enforcement. The complete suite passed **480 tests with 0 failures**. The environment emitted 2,937 repeated warning occurrences from the existing Pillow deprecation and Gradio 6 migration categories.

The real local FFmpeg smoke path created two three-second Selected Takes with program audio plus a two-second pink-noise room-tone source. Cinema produced a 5.317-second MP4 containing video and audio streams and a provenance manifest. This proves software execution, not artistic mix quality.

## Truth boundary

Film Lab uses only a Director-assigned recording. It does not infer room identity, acoustic match, microphone perspective, dialogue meaning, noise suitability, or artistic correctness. Audible evaluation on real Creator footage and the Windows/AMD production machine remains **NOT TESTED**. The Director's Selected Takes remain unchanged.
