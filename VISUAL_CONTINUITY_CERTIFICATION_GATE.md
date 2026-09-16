# Visual Continuity Certification Gate

## Implemented
- Samples the source and candidate at the Director playhead.
- Uses real decoded frames (or image media) and computes pixel, RMS, edge, histogram, and perceptual-hash similarity.
- Flags large global visual drift before candidate acceptance.
- Persists evidence and sampled frames with the candidate Take.
- Automatically runs after Director Preview regeneration without blocking generation if media cannot be decoded.

## Truth boundary
- **Global frame similarity / composition drift:** REAL / TESTED at software boundary.
- **Video frame decode through ffmpeg:** REAL implementation / machine-specific execution NOT TESTED on Creator Windows PC.
- **Character identity, wardrobe/hair/makeup, named props, and semantic set sameness:** REVIEW_REQUIRED. Global pixel similarity is evidence, not semantic proof.
- **Actual AMD generated candidate visual continuity:** NOT TESTED.

Film Lab must not upgrade semantic identity/wardrobe/prop continuity to PASS solely because two whole frames are visually similar.
