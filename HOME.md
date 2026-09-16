# Film Lab Home

The Gradio **Home** tab is a purple + soft cyan studio landing page: serif wordmark, full-bleed hero, poster-first job cards, looks tiles, local lot. Then a **craft** row (Lighting, Score, Voice, Effects, Pose, Set). Original Film Lab names. **One theme for every desk.** Regular vs 18+ Explicit is a filming-mode toggle — not a red Darkroom Suite vs a purple regular app. **Film school, not SaaS. Zero credits.** The layout energy is a public AI-video homepage *shape* only — no foreign brands, logos, or credit chrome.

A public AI video homepage was a *layout* reference (card grid, shelves, project strip). This desk is not that product.

## The studio jobs

| Card | Desk | What you do |
| --- | --- | --- |
| AI Production Pipeline | Enhance · Pose · Animate | One shot, one desk. No re-upload. Back to Home. [docs/PIPELINE.md](docs/PIPELINE.md) |
| Still Desk | frames | Ingest stills + local notes. |
| Take Board | play vs fix | Click to play. Pause, click the person, **Dream about…**. [docs/DREAM.md](docs/DREAM.md) |
| Director Bridge | local tools | ChatGPT / Claude / Grok Bot / Cursor / Claude Code / OpenClaw / Hermes. MCP or CLI. Not a paid plugin. |
| Cinema Desk | reel | Auto-stitch the extend sequence with crossfades. Grade and assemble. |
| Director Brain | pages | Writing Studio. Import + Fuse drafts, **dream beat sheet**, then Plan shots → Motion. [docs/WRITING.md](docs/WRITING.md) · [docs/DREAM.md](docs/DREAM.md) |
| **UGC Ads Desk** | product ads | Product ref + avatar + prompt → Enhance → Animate. Optional hook→CTA plan. [docs/UGC.md](docs/UGC.md) |
| **Character Consistency** | bible | Alison / Bradley profiles, active cast, refs, face lock. **Micro-expressions** + full-body behavior. **Family Genetics** (Regular / story kids). [docs/CHARACTER_CONSISTENCY.md](docs/CHARACTER_CONSISTENCY.md) · [docs/PERFORMANCE.md](docs/PERFORMANCE.md) · [docs/GENETICS.md](docs/GENETICS.md) |
| **Lighting Desk** | chips | Studio / natural + cinematic pack (or skip). Same list on Pipeline Enhance, Effects, Cinema. [docs/LIGHTING.md](docs/LIGHTING.md) |
| **Score Desk** | music | Import-first cues; local synth; optional MusicGen-small later. Cinema mux. [docs/SCORE.md](docs/SCORE.md) |
| **Voice Desk** | acting | Per-character Voice profile; tagged lines route to Alison / Bradley; local TTS or import. Cinema muxes each cue. [docs/VOICE.md](docs/VOICE.md) |
| **Effects Desk** | preset shelf | Character still, optional location / product, descriptive motion presets, local Comfy. Finish in DaVinci / AE. [docs/EFFECTS.md](docs/EFFECTS.md) |
| **Pose Desk** | still-first pose | Body / hands / face + micro-expression / behavior on the still. Face lock stays. Then Animate. Not video puppeting. [docs/POSE.md](docs/POSE.md) · [docs/PERFORMANCE.md](docs/PERFORMANCE.md) |
| **3D Set Desk** | orbit · aerial | Virtual set notes: family roles, camera orbit/push/aerial, outdoor plates. Not a 3D engine. [docs/SET.md](docs/SET.md) |
| **Mark & Direct** | region edit | Circle / square / lasso on the still or a clip frame. Per-region note + **prop action** (pick up book). Apply stacks. Then Animate / Regenerate. [docs/MARK.md](docs/MARK.md) |

## UGC Ads Desk (workflow, not a paid model)

This desk is a **local product-ad job**, not a hosted UGC marketplace. Film Lab does **not** require those APIs. Motion is the same local AMD img2vid path. See [docs/UGC.md](docs/UGC.md).

Typical pass:

1. Upload a **product** still.
2. Pick an avatar from the **Character Bible** or upload a picture. **Adults 18+.**
3. Write how the product and the person appear.
4. **Generate still** (local composite) and/or **Enhance** → **Animate**.
5. Edit the finished take: Take Board **Playback**, then **Mark & Direct** · Fix this frame → **Regenerate**. Old take stays.

Optional accordion: hook → CTA five-beat script, push to Motion Desk, stitch on Cinema.

On a Radeon RX 5600 XT (~6GB), expect short clips and some softness. That is a hardware limit, not a paywall. Quality program: native **480p / 720p** (1080 if VRAM allows); **4K** via export upscale. DEBUG CHECKLIST on OOM: drop one step, shorten duration, Regenerate, restart Comfy — never force native 4K.

## Banner

LOCAL ONLY — film-school study on this machine. **Works offline for local generation.** **Save Library** (nav) browses the lot on this PC; OneDrive / Google Drive folders are optional backup when online. Online optional: Grok / Gemini / ChatGPT / Claude / ElevenLabs. Adult work is allowed. Characters and creators **18+** only. No subscriptions, Film Lab credits, quotas, or paywalls. Install: **INSTALL_FILM_LAB.bat**. Daily: **START_FILM_LAB.bat** (no PowerShell). Uninstall: **UNINSTALL_FILM_LAB.bat**. Grok Bot can patch in place. Repair: **REPAIR.bat**.
