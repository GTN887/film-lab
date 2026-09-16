# Temporal Segment Repair & Seamless Reassembly Gate

## Implemented
- Localized visual repair windows can be reassembled with FFmpeg.
- Source video before and after the repair window is preserved.
- Repair candidate supplies only the localized visual window.
- Source audio is preserved unchanged; Film Lab does not claim audio segment repair.
- Entry/exit boundary frames are compared and reported as PASS / REVIEW / NOT_TESTED.
- Reassembled output becomes a new persistent Take and never overwrites source or repair candidates.
- Director Timeline exposes **Reassemble Only Localized Segment** and returns the result to A/B review.

## Truth status
- Temporal visual segment replacement: REAL in software when FFmpeg executes successfully.
- Boundary risk measurement: REAL sampled-frame evidence.
- Seamless visual quality on Creator AMD/ComfyUI footage: NOT TESTED.
- Audio-aware localized regeneration/splicing: NOT ENFORCED; source audio is preserved.
- Windows machine acceptance: NOT TESTED.
