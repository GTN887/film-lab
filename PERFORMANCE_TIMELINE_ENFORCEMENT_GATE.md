# Performance Timeline → Model Enforcement Gate

Film Lab now carries actor performance timelines into ComfyUI through an evidence-based bridge.

Truth rules:
- Prompt timing alone remains PROMPT_ONLY.
- ENFORCED requires an explicit `film_lab_performance_timeline:<character-id>` workflow slot plus a time-aware workflow consumer.
- Pose/expression nodes may be discovered as available evidence, but discovery alone is not enforcement.
- Timeline enforcement is recorded per stable Character ID in generator route metadata.
- Unsupported or unmatched characters remain PROMPT_ONLY.

Actual AMD/ComfyUI temporal performance rendering remains NOT TESTED until certified on the Creator machine.
