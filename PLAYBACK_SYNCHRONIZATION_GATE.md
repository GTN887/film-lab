# Shot Playback Synchronization Gate

## Software truth
- Exact Scene + Shot selected Take resolution: **REAL / TESTED**
- Persistent playhead/scrub state: **REAL / TESTED**
- Known-duration clamping and timeline cursor percentage: **REAL / TESTED**
- Director Timeline preview loads selected Take: **REAL / TESTED at callback boundary**
- Scrub → frame extraction for Mark & Direct: **REAL when FFmpeg/runtime succeeds; runtime machine acceptance NOT TESTED**
- Browser/native video currentTime following the Film Lab playhead continuously: **PARTIAL / NOT MACHINE-CERTIFIED**
- AMD regeneration from a paused marked frame: **NOT TESTED**

Film Lab must not describe a saved playhead as frame-accurate synchronized playback unless the installed UI/runtime has been acceptance-tested.
