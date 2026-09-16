# Source-Handle Split Edits Recovery Gate

## Recovery basis

The personal-account 467-test archive was unavailable. This checkpoint was rebuilt forward from the independently verified `FilmLab-Authoritative-452tests.zip` (SHA-256 `a945875b15e1811c0367e37a2bc0dead85805cf9d0be64a2f2b77f8c0a69cf20`). The original archive was not modified.

## Status

- Picture/audio timing separation: **PASS / REAL**
- Persistent Director picture in/out and J-lead/L-tail controls: **PASS / REAL**
- Same-source pre-roll/post-roll handle validation: **PASS / REAL**
- Non-destructive Selected-Take/Cinema behavior: **PASS / REAL**
- Missing/short handle rejection: **PASS / REAL**
- Full regression: **PASS — 467 passed, 0 failed**
- Compilation: **PASS**
- Full Gradio UI construction: **PASS** (`Blocks`)
- Local FFmpeg source-handle smoke render: **PASS** — output contains video and audio streams
- Windows/AMD/Creator-footage acceptance: **NOT TESTED**
- Artistic dialogue/room-tone transition quality: **NOT TESTED**

## Implementation

An incoming Take stores the Director's boundary edit decision in `metadata.audio_cut_intent`: picture in-point, outgoing picture out-point, J-cut lead, L-cut tail, explicit cut type, and Director-explicit provenance. Cinema probes both source durations and audio streams, calculates available incoming pre-roll and outgoing post-roll, and refuses to enforce an edit when a requested handle is absent or too short.

For an enforceable split edit, FFmpeg trims picture independently, concatenates the explicit picture ranges, reads incoming audio from the earlier same-source handle, retains outgoing audio into its later same-source handle, shifts timestamps, mixes the overlap, and maps video plus audio to the new Cinema output. Original Takes and their media are unchanged. A failed plan/render cannot replace a valid source Take or silently alter selection.

## Affected source

- `film_lab/audio_preserving_cinema.py`
- `film_lab/cinema_export.py`
- `film_lab/production.py`
- `film_lab/take_board.py`
- `film_lab/ui_handlers.py`
- `app.py`
- `tests/test_audio_preserving_cinema.py`
- `tests/test_source_handle_split_edits.py`
- `tests/test_take_board.py`

## Truth boundary

The implementation proves explicit timing and signal routing. It does not infer dialogue meaning, speaker identity, room identity, acoustics, microphone perspective, or artistic correctness. Real Creator-machine listening remains **NOT TESTED**.
