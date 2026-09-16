# Asymmetric J-Cut / L-Cut Assembly Gate

## Status

- Production persistence and Creator controls: **PASS / REAL**
- Explicit J-cut lead and L-cut tail planning: **PASS / REAL**
- FFmpeg asymmetric audio placement in Cinema export: **PASS / REAL**
- Selected-Take preservation and Director authority: **PASS / REAL**
- Automated regression: **PASS — 452 passed, 0 failed**
- Python compilation: **PASS**
- Full Gradio UI construction: **PASS**
- Local FFmpeg smoke render: **PASS** — video + audio streams, 7.400-second output from two 4-second clips with a 0.600-second picture overlap
- Windows/AMD/Creator-footage audible acceptance: **NOT TESTED**

Superseding recovery verification: `SOURCE_HANDLE_SPLIT_EDITS_GATE.md` separates picture in/out from audio timing and proves same-source handles at the 467-test checkpoint. This earlier gate remains preserved as checkpoint history.

## Implemented operation

The Take Board now lets the Director save the audio cut into an incoming persistent Take as `HARD_CUT`, `J_CUT`, `L_CUT`, or `J_L_CUT`, with explicit lead/tail timing from 0–2 seconds. Cinema reads the ordered Selected Takes, proves every audio stream, builds one transition plan per boundary, and executes asymmetric FFmpeg audio placement. A J-cut advances incoming audio before incoming picture; an L-cut retains outgoing audio under incoming picture. Timing is clamped to available source handles and the two-second safety bound.

The Creator-facing **Send Selected Takes to Cinema** path now uses the same audio-preserving authoritative exporter instead of the older visual-only stitcher. Original Takes and their media remain untouched. Cut direction is metadata; export creates a new output and never changes the Selected Take.

## Truth boundary

Film Lab acts only on explicit Director intent. It does not infer dialogue meaning, speaker identity, room acoustics, microphone perspective, or artistic mix quality. If every Selected Take does not have a proven audio stream, Cinema uses the established visual-only fallback and does not claim audio preservation. Audible transition quality on the Creator's Windows/AMD machine and real production footage remains **NOT TESTED**.
