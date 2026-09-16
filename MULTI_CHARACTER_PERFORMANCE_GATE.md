# Multi-Character / Performance Gate

Status: software layer REAL / TESTED; physical model enforcement remains CONDITIONAL on the selected ComfyUI graph and local runtime.

Implemented:
- Stable Character-ID-to-conditioning-slot assignment for multiple performers.
- Distinct proven identity/reference graph profiles are reserved per character.
- Insufficient graph slots report PARTIAL/UNSUPPORTED instead of swapping identities.
- Actual image injection is separately verified before a character assignment becomes ENFORCED.
- Character-specific blocking/region intent is resolved by stable Character ID, not list order.
- Spatial control is PROMPT_ONLY unless a real regional/mask workflow bridge is proven.
- Per-character emotion/performance direction is structured and carried in generation metadata.

Not yet claimed complete:
- True regional mask conditioning for multiple performers.
- Actor-isolated regeneration in Mark & Direct.
- Model-level facial/pose/performance controls beyond prompt direction unless a compatible workflow exposes and receives those controls.
- Real Windows/AMD/ComfyUI acceptance.
