# Automatic Character/Object Tracking Gate

Film Lab now follows creator-registered visual targets through ordered frame sequences while preserving stable target/Character/Object IDs.

| Capability | Status | Truth |
|---|---|---|
| Stable target ID across track points | PASS / REAL / TESTED | Stored by target ID. |
| Local appearance tracking across moving frames | PASS / REAL / TESTED | Search follows the registered visual region. |
| Lost-target detection | PASS / REAL / TESTED | Low-confidence matches become LOST rather than silently accepted. |
| Persistent project track evidence | PASS / REAL / TESTED | `visual_tracks.json`. |
| Source-vs-candidate position-track comparison | PASS / REAL / TESTED | Measures normalized center drift. |
| Biometric/semantic identity proof | NOT IMPLEMENTED | Tracking is explicitly not identity certification. |
| Full real generated-Take scan on Windows/AMD | NOT TESTED | Requires machine acceptance and real video decoding. |

Next gate: full-Take continuity scanning and sampled-video track orchestration.
