# Lip Sync + Facial Performance Bridge Gate

Status: **PASS / REAL / TESTED at the software bridge boundary**.

Film Lab now binds dialogue audio to explicit per-Character ComfyUI workflow slots using stable Character IDs. Lip sync is reported ENFORCED only when a lip-sync-capable graph is present and every speaking Character has a proven Character-bound audio slot with a real audio file. A lip-sync node by itself is not sufficient evidence.

Facial-performance direction can be injected through explicit Character-bound facial-performance slots when a compatible facial-performance path is present, but facial direction alone does not count as lip synchronization.

Multi-speaker scenes require separate proven audio bindings for each Character. Missing or ambiguous bindings remain PARTIAL rather than being mislabeled ENFORCED.

Actual Windows/AMD/ComfyUI lip-sync rendering remains NOT TESTED until machine acceptance.
