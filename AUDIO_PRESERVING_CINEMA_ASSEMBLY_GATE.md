# Audio-Preserving Cinema Assembly Gate

Film Lab now preserves proven Selected-Take audio during multi-clip Cinema export. When every clip has a proven audio stream, Cinema uses FFmpeg `xfade` for picture and `acrossfade` for sound and maps both streams into the final MP4. If audio is not proven for every clip, Film Lab retains the legacy visual-only path rather than falsely claiming audio preservation.

Director J/L-cut intent and explicit timing metadata now feed the later verified asymmetric assembly gate documented in `ASYMMETRIC_J_L_CUT_ASSEMBLY_GATE.md`. **Truth boundary:** Film Lab does not infer dialogue semantics, speaker identity, room acoustics, or artistic mix quality. Real Windows/AMD footage and audible transition quality remain NOT TESTED.
