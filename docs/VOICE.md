# Voice Desk (Film Lab)

Per-character film acting, not a flat announcement read. **This machine only.** Zero Film Lab credits. Adults **18+**.

Each **Character Bible** entry owns a Voice profile. Dialogue tagged to that character routes to that voice. Cinema Desk muxes every cue at its start time.

## Voice profile (per character)

| Field | What it is |
| --- | --- |
| TTS backend | `auto` → pyttsx3 / Piper / espeak / XTTS / placeholder |
| TTS voice id | Engine voice. Alison ships `en+f3`. Bradley ships `en+m3`. Piper can be a local model path. |
| Imported sample | Recorded VO copied to `characters/<id>/voice/`. XTTS uses it as `speaker_wav` when present. |
| Performance notes | How they act the line (close-mic, unhurried, baritone). |

Save the profile on Character Consistency or Voice Desk. Tagged lines never share a take across adults.

**Alison** — `en+f3`, higher placeholder pitch, tender / unhurried / intimate.

**Bradley** — `en+m3`, lower placeholder pitch, steady / held / intimate.

## Tagged routing

Fountain character cues or roleplay lines:

```
ALISON: Stay like that.
BRADLEY: I'm not going anywhere.
```

**Speak tagged scene lines** (Voice Desk) and **Save takes → Voice** (Director Brain) resolve `ALISON` → `alison` and speak each line in that bible voice. Cues stagger on the timeline (`start_s`).

## Directions (per take)

| Knob | Meaning |
| --- | --- |
| Intention | What the adult wants in the line (tender, sharp, held) |
| Micro-expression | Folds into Breath (`micro-expression swallow`). Same catalog as Director Note. [PERFORMANCE.md](PERFORMANCE.md) |
| Breath | Close-mic inhale, swallowed, after a kiss |
| Pace | held / unhurried / conversational / urgent |
| Register | whisper / intimate / spoken / projected |
| Intensity | How hard the take pushes (0–1) |

## Pause markup

- `[2s]` — held silence (about two seconds)
- `...` — a short hang
- `/` — a breath

Example: `Stay like that. [1s] Don't move.`

## Local engines (lighter first)

1. **Import recorded VO (primary on 6GB)** — drop WAV/MP3. Files go to `audio/dialogue/`. **Import VO as this character's sample** pins it on the bible.
2. **pyttsx3** — offline system voices. Matches Zira/Hazel vs David/George from the character voice id.
3. **Piper / espeak** — if on PATH. espeak uses `-v en+f3` / `en+m3`.
4. **XTTS** — only if you installed local Coqui weights. Uses the imported sample when present.
5. **Placeholder WAV** — timed tones so the timeline still has a file. Alison and Bradley use different pitch.
6. **MOSS-TTS and friends** — optional later. Not required on this card.

No hosted voice shop. No Film Lab credits.

## Cinema Desk mux

Assemble reel (Mux per-character dialogue cues) gathers every Voice cue tagged to that shot or scene, plus any WAV attached on the reel row. Each cue delays by clip start + `start_s`. Alison and Bradley mix as separate takes.
