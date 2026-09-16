# Provider menus (Film Lab)

UI pickers only. **Local is the default.** Zero Film Lab credits. Cloud families use **keys you own**. Film Lab never hardcodes secrets and never fakes a clip, still, or take.

## Voice Desk

- **Local TTS** (default) — pyttsx3 / Piper / espeak / import / placeholder
- **ElevenLabs** — set API key / coming soon
- **Seed Audio** — set API key / coming soon
- **Seed Speech** — set API key / coming soon

## Video / Motion Desk

Left rail: prompt, Video Model, multi-shot, **Quality** (480p / 720p / 1080p / 4K), **Generate**. Default **Local / ComfyUI · SVD-XT**. RX 5600 XT: native 480/720 (1080 if it fits); 4K via export upscale.

- **Featured** — Film Lab aliases `Multi-Version` and `Reality Mix` (local SVD-XT, not a third-party pack)
- Minimax Hailuo → H3 Max, Hailuo 2.5 Fast, H2, Hailuo 3.0, Hailuo G2
- FLUX.1 Video
- Kling → 3.0 Motion Control, 3.0, V1 Video, V1 Video Edit
- Wan 3.0
- OpenAI Sora 2
- Google Veo → 3.1 Lite, 3.1 Fast, 3.1, Veo 3, Veo 2

Cloud families toast **set API key / coming soon**. Film Lab will not fake or pirate those clips.

## Image / generation (Motion, Still, Effects)

Nested family → model. Default **Local / ComfyUI** (SVD-XT img2vid).

- Nano Banana → Pro, Nano Banana, 2, 2 Lite
- Grok → Imagine, Imagine Edit, Imagine 2.0, Imagine 2.0 Edit
- Ideogram → 2.0, 2.0 Turbo, 1.0
- OpenAI → GPT-4o, GPT-4o mini, GPT-4 Turbo, GPT-3.5 Turbo
- Seedream → 5.0 Pro, 5.0 Lite, 4.5

Unwired families toast **set API key / coming soon**. Animate / Send will not invent a video.

## Prompt Enhance / Writing / UGC

- **Local templates only** (default)
- **Grok** → Grok 2, Grok mini, Grok Beta (your `FILM_LAB_XAI_API_KEY`)
- **Gemini** → Gemini (Google) (your Gemini key)
- **OpenAI** → GPT-4o, GPT-4o mini, GPT-4 Turbo, GPT-3.5 Turbo, o1, o1-mini (your OpenAI key)
- **Claude** → Claude Sonnet, Claude Opus, Claude Haiku (your `FILM_LAB_ANTHROPIC_API_KEY` or `ANTHROPIC_API_KEY`)
- **Dual** — Writing Studio only, same two-key roles as before

Never paste a secret into a field. Environment keys only.
