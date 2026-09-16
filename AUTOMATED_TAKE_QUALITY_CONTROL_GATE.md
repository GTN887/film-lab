# Automated Take Quality Control & Repair Decision Gate

Film Lab diagnoses persisted Take continuity evidence and recommends a conservative repair strategy before execution.

- Recommendations never select, overwrite, or reject a Take.
- Localized timed problems can fork a targeted repair candidate.
- Multiple severe failures across domains recommend a fresh candidate rather than stacking patches.
- Untimed evidence is not falsely localized.
- Creator approval remains required in A/B review.
- Actual AMD/ComfyUI visual quality remains NOT TESTED until machine acceptance.
