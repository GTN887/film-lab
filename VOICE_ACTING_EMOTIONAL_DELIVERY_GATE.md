# Voice Acting & Emotional Delivery Gate

Status: REAL / TESTED at the Film Lab software boundary; actual expressive voice rendering remains NOT TESTED on the Creator Windows/AMD runtime.

Film Lab now persists Character-bound voice acting beats with timing, emotion, pace, emphasis, delivery, pauses, and intensity. These beats enter generation conditioning and the production prompt. An explicit `film_lab_voice_performance:<character_id>` workflow slot can receive the Character's structured performance only when an expressive/prosody-capable renderer is present.

Truth rule: prompt direction is `PROMPT_ONLY`. `ENFORCED` requires both a Character-specific slot and evidence of an expressive/prosody voice renderer. A global slot cannot silently bind multiple Characters.
