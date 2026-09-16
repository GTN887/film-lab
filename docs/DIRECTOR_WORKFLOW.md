# Director workflow — full local pipeline

This is a **private, local** studio for personal independent study. Adult characters (18+ / late 20s). Explicit / pornographic sex is allowed. Nothing is uploaded. Intimacy modes and the **content intensity dial** are director knobs, not a cloud filter and not an MPAA certificate. The only hard stop is under-18 characters.

Film Lab is original software, not a Higgsfield clone. Use it as a director's desk: writing / novel / roleplay → script → cast refs → shots → voice → music → grade → reel.

Alison: blonde, late 20s. Bradley: dark hair, athletic, late 20s. Wedding bands are a story prop.

## Pipeline

1. **Writing** — **Import** PDF / Word / text, or paste Grok online + Gemini and **Fuse** into one screenplay, novel, or beat sheet (local, no API). Edit. **Plan shots → Motion Desk** (cap 8). Then work the desk: **emotion → senses → environment → living nest → genre → intensity → page**. Name the primary feeling and the conflicting one; set emotion intensity and the gap between inner state and outer behavior (subtext). Enable only the senses this room needs (sight stays balanced so it does not dominate). Lock the set — location, time, weather, light, ambient sound, blocking, props. Then pick a **story genre** (primary + optional secondary / custom tags) and apply its tone / tropes. **Teen film / coming-of-age (theatrical)** is allowed as a genre style if every protagonist is 18+ (college senior, newly adult). Set **content intensity** (slider 0–1 plus Implied / Frank R / MA-17 / Explicit presets — creative guides, not MPAA). Presets: *Warm bedroom newlywed*, *Cold argument kitchen*, *Rain outside window*, *Aftercare lamp*. **Sensory pass** rewrites with mandatory multi-sense detail grounded in that environment. Screenplay puts sensation in action lines, not dialogue; novel immerses; roleplay reacts through the body. Build the prompt pack (offline). Pick Local / Grok / Gemini / ChatGPT / Dual — Dual default is Gemini spine, Grok dialogue; ChatGPT can take the spine or a compare page. Generate with a cloud provider **leaves this machine** to that API. **No Film Lab credits.** Or paste from chat. Push pages onto the Script desk (genre travels with the scene). Save takes to Voice. [docs/WRITING.md](WRITING.md)
2. **Script** — Write `INT. BEDROOM - NIGHT` (or load the example / accept a Writing push). Heading, action, dialogue, parentheticals, director notes. Export Fountain / txt / pdf if you want it off the screen.
3. **Characters** — Lock Alison and Bradley. Set **Age (years)** to 18+ (required for intimate / frank / explicit). Age band stays adult. Write look, wardrobe, voice, **micro-expression / behavior**, and a **locked descriptor**. Set **living style** (newlywed nest, loft, suburban house, …) and **living conditions** (income pressure, privacy, thin walls, commute — story labels, not real PII). Pin 3–10 reference stills each. **Family Genetics:** Actor A + Actress B → infant / child / teen bible card that belongs to both parents. Regular / story only — never 18+ intimacy. [docs/GENETICS.md](GENETICS.md). [docs/PERFORMANCE.md](PERFORMANCE.md). Descriptor + nest inject into `local_prompt()` and Writing Studio. Save as project nest default to persist on `project.json`.
4. **Ingest** — Covered, nude, or intimate stills. They copy into `stills/`.
5. **Pose Desk** — Optional still-first body / hands / face + micro-expression / behavior guide (OpenPose-style overlay). Face lock stays. Not video puppeting. Then Motion. [docs/POSE.md](POSE.md). [docs/PERFORMANCE.md](PERFORMANCE.md).
6. **Shot desk** — Link the scene. Tick bible ids. Click a cast face for **Director Note** (performance). **World Note** for mise-en-scène. **Dream / Lucid:** sleeping parent take → Mark the head → Enter dream (child scenes, then wake). [docs/DREAM.md](DREAM.md). Intimate / explicit: adult 18+ ONLY — never route minors into porn intensity. Duration **2–4s** on the 6GB AMD path. Upload → Pose adjust → Enhance → Animate (ComfyUI SVD-XT). [docs/DIRECTOR_NOTES.md](DIRECTOR_NOTES.md). Ken Burns is Advanced-only timing, not the product.
7. **Queue** — The rest of the phrase, one after another.
8. **Voice** — Speak selected lines (including takes from Writing). Attach the WAV to a shot. Cue start time is a timeline note (and a delay when you assemble).
9. **Music** — Name a cue, mood, in/out, temp BPM. Render a local synth bed or import a track you own.
10. **Effects Desk** — Character still + optional location / product + a descriptive preset (floating fall, high flip, studio slide, melting). Local Comfy. Finish the export in DaVinci or After Effects when you want a real grade. [docs/EFFECTS.md](EFFECTS.md)
11. **Finish** — Stock LUT (`warm_lamp` for this room) and light VFX (fade, grain, bloom, letterbox, speed).
12. **Reel** — Rebuild from the scene's linked shots. Status: idea / blocked / generated / locked. Assemble: stitch + optional music/dialogue mux.

## Emotion → senses → environment → genre → page

Treat Writing Studio like directing actors who can feel the room, not like filling a genre dropdown.

1. **Emotion** — Primary feeling + a conflicting secondary. Intensity 0–1. Inner state vs outer behavior is the subtext. Relationship temperature (newlywed tenderness, cold argument, grief in the same bed, …).
2. **Senses** — Toggle touch, smell, taste, hearing, sight. Notes are optional; an enabled sense is still prompted. Keep sight in the mix without letting it crowd the others.
3. **Environment** — The set those senses attach to: location, time of day, weather, light quality, ambient sound, spatial blocking, props that trigger the body (sheets, coffee, wet asphalt).
4. **Living nest** — Style (minimalist, newlywed nest, loft, …) plus conditions (tight money, thin walls, cramped, noisy street). Inherit from the character bible / `project.json`, or override per draft. Thin walls couple to hearing; a cramped room couples to touch. Presets: *Newlywed warm apartment*, *Tight budget thin walls*, *Quiet suburban house*, *Noisy city loft*.
5. **Genre** — Story shape (romance, horror, thriller, theatrical teen film, …). Adaptation notes change with genre. Genre does not replace feeling the room. Teen-film style still requires 18+ bodies.
6. **Intensity** — Slider 0–1 plus named presets (Implied / soft, Frank / theatrical R, MA-17 / Euphoria-style, Explicit / adult study). MA-17 is Euphoria-level heat for clearly adult characters — not high-school / teen-appearing sex. Composes with intimacy mode. Not a ratings board. No refusal for adult explicit.
7. **Page** — Build the local prompt pack. Screenplay: playable dialogue, sensory load in action. Novel: full immersion. Roleplay: the character answers through body + senses. Book→screenplay: translate novel sensation into shootable blocking.

A **Sensory pass** checkbox forces multi-sense detail grounded in the chosen environment. Do not invent a different room.

## The phrase

1. Establishing — lamp, both under the sheets.
2. OTS — one face, one shoulder.
3. Insert — hands and bands.
4. Close — kiss or breath.
5. Body — weight shift; intimate sex or explicit / pornographic if that is the knob.
6. Pull-out — aftercare.

Example cards and the bedroom scene live in `examples/alison_bradley/`.

## Shot flexibility

Same knobs as before (start/end, 3–10s, aspect, camera, motion strength, body notes, intimacy label, content intensity, tags, lighting, negative, seed) plus:

| Field | Use |
| --- | --- |
| **Linked scene** | Ties the shot to the Fountain desk and the reel |
| **Character bible ids** | `alison` / `bradley` — drives prompt inject + consistency gallery |
| **Content intensity** | 0–1 continuum + named presets. How far the frame goes; intimacy mode is what the camera may hold |
| **Dialogue cue / start** | Timeline note; Voice tab writes the WAV |
| **Consistency refs** | Character sheet + Environment lock still. ComfyUI IP-Adapter / InstantID read the same folders when those nodes exist |

## Camera ethics

- Faces and consent-in-fiction first.
- Low is motivated, not medical.
- OTS needs a real foreground shoulder.
- Intimate sex: hips, weight, hands, breath, penetration as blocking.
- Explicit / pornographic: the sex is in the frame — bodies, genitals, wet. Adults 18+.
- Aftercare is part of the phrase.

## Consistency (local only)

`characters/<id>/consistency_hook.json` names the **local** 6GB stack. Primary lock is a start still → img2vid. FaceID Plus V2 and InstantID stay stubs until those nodes exist on ComfyUI. ReActor is post-only. Film Lab does not compute cloud embeddings and will not call a hosted face API. See `docs/CHARACTER_CONSISTENCY.md`.

## When Advanced Ken Burns is enough

It will not invent actor motion. It is a timing/coverage zoom, not a take. Use it only from the collapsed Advanced accordion. Primary Generate never falls back to it.

## Privacy

Everything lives under `./data/projects/` and `./data/luts/`. Treat it like a camera card: local disk, your house, your study.
