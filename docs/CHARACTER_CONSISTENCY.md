# Character consistency (Film Lab)

Programmed likeness for Liam’s private film-school desk. **This machine only.** Zero Film Lab credits. Adults **18+** only. No hosted face API.

A public AI video site may sell “character lock” as a credit product. Film Lab does the *job* with folders, a bible, and local ComfyUI — not that product, and not their names.

## Program (RX 5600 XT, not NVIDIA)

**Actors (Character Bible)** — Face lock: InstantID (SDXL) and/or IP-Adapter FaceID when Comfy lists those nodes; PuLID only if a Flux path exists later. Body/style: ControlNet OpenPose via Pose Desk now; character LoRA later. Multi-ref character sheet (Alison, Bradley, family roles). ReActor is optional post fallback only.

**Environments (World / Set Bible)** — Lock the set with a reference still + optional IP-Adapter style/scene ref. ControlNet depth / canny / softedge for room/street geometry. World Note + 3D Set reuse the same locked background. Img2vid seeds from the locked still; **Regenerate** keeps the World lock. See [ENV_LOCK.md](ENV_LOCK.md).

**DEBUG CHECKLIST** if identity or env drifts: strengthen adapter one step; re-apply refs; drop Quality on OOM; Regenerate; do not fake InstantID / FaceID when nodes are missing.

## Character Bible

Each adult has a profile:

| Field | What it is |
| --- | --- |
| Name | Alison, Bradley, or a new adult |
| Age band + **Age (years) 18+** | Numeric age required for intimate / frank / explicit |
| Appearance | Hair, build, face notes |
| Wardrobe | What they wear in this nest |
| Rings / props | Wedding bands are a **story prop** |
| Personality | How they take a room |
| Emotion baseline | Default feeling before the scene turns |
| Micro-expression | Bible default face (swallow, glance). Inherits into Director Note. [PERFORMANCE.md](PERFORMANCE.md) |
| Behavior | Full-body default (weight shift, reach then hold) |
| Locked descriptor | One line injected into every local prompt |
| Voice profile | TTS voice id, imported sample, performance notes. Alison `en+f3` / Bradley `en+m3`. Tagged dialogue routes here. [docs/VOICE.md](VOICE.md) |
| Reference stills | 3–10 images in `characters/<id>/refs/` |
| **Family Genetics** | Actor A + Actress B → infant / child / teen stills + a bible card that belongs to both parents. Regular / story only. [GENETICS.md](GENETICS.md) |
| **Word / PDF sheet** | **Import** a `.docx` or `.pdf` bio into the bible fields. **Export** the typed sheet as Word or PDF. Local only. **Not Excel** — spreadsheets / shot lists stay on Writing Studio. |

**Preloaded leads** (bedroom study):

- **Alison** — blonde, late-20s adult woman
- **Bradley** — dark hair, athletic late-20s adult man, wedding bands

Studio copies live in `data/characters/<id>.json`. The working bible for a project is `data/projects/<name>/characters/<id>/profile.json` plus `refs/` and `consistency_hook.json`.

## What gets injected

When you pick the **active cast**, Film Lab appends appearance, wardrobe, rings, personality, and emotion into:

- Motion Desk local prompt (and the AMD img2vid prompt)
- Still Desk notes (cast line on this folder)
- UGC Ads Desk (bible avatar or upload + shot `character_ids`)
- Director Brain / Writing Studio bible block

Nothing is uploaded. Optional Grok / Gemini / ChatGPT / Claude still use **your** keys if you pick them.

## The local stack (RX 5600 XT ~6GB)

Lighter first. Do not start with a Flux identity model on 6GB.

1. **Reference still → img2vid (primary)**  
   Pin refs. Pick the locked still. Generate on Motion Desk (ComfyUI DirectML). The face stays because the video *is* that frame moving. This is the daily path.

2. **IP-Adapter FaceID Plus V2 (stub)**  
   Mature ComfyUI method. When the sidecar lists FaceID nodes, point the graph at `refs/` and use the **face lock** slider (~0.4–0.65). Tight on 6GB — 512×288, short clips.

3. **InstantID (SDXL) (stub)**  
   Better likeness, heavier. Optional later. Expect OOM unless you shrink hard.

4. **PuLID / Flux (advanced doc only)**  
   Not required. Not the 6GB first path.

5. **ControlNet OpenPose (Pose Desk)**  
   Body / hands / face on the still. Face pixels stay. Then Animate.

6. **Character LoRA (advanced)**  
   Train later from 20–40 cropped **adult** stills. Overnight / off-box. Not the daily button.

7. **ReActor (optional post)**  
   Face-fix after a take. Not the primary lock.

Video-native identity models (ConsisID and friends) want more VRAM than this card. They stay optional notes.

## Face lock slider

`0` = prompt + start still only.  
`~0.55` (default) = remember the strength for FaceID when those nodes exist; img2vid still uses the start frame.  
`1` = max identity pressure on a future FaceID graph — easy to plasticize on 6GB.

If ComfyUI is Off, the slider still saves. Start the sidecar for likeness lock — Ken Burns is Advanced timing only.

## ComfyUI stubs on this AMD box

Film Lab talks to a **local** sidecar (`http://127.0.0.1:8188` by default). It never calls a hosted face API.

On boot / status, `film_lab/consistency.py` probes `/object_info` for these node names:

- FaceID: `IPAdapterFaceID`, `IPAdapterApply`, `IPAdapterUnifiedLoader`
- InstantID: `InstantIDFaceAnalysis`, `ApplyInstantID`
- PuLID: `PulidFluxApply`
- ReActor: `ReActorFaceSwap`

Status line on Home:

- **Off** — sidecar down. Start ComfyUI. Primary Generate will not zoom-pan instead.
- **Stub** — sidecar up, no identity nodes. Primary path is start still → img2vid.
- **Ready** — one of those nodes exists. The face-lock slider is meant for that graph.

`characters/<id>/consistency_hook.json` records the stack and the current face-lock plan. Point a later FaceID graph at `characters/<id>/refs/`. Film Lab does not embed faces itself.

**RX 5600 XT (~6GB, DirectML) rules of thumb**

- Daily: 512×288, 2–4s, start still that already looks like Alison / Bradley.
- FaceID Plus V2: try after img2vid is boring-reliable. Drop resolution before you raise strength.
- InstantID / SDXL: optional later. Expect out-of-memory unless tiny.
- PuLID / Flux and ConsisID-class video models: advanced notes only. Do not require them on 6GB.
- Face LoRA: 20–40 cropped **adult** stills, trained off this card or overnight. Load the LoRA in ComfyUI; Film Lab will still inject the bible line.
- ReActor after a take if a frame drifted. Do not treat a swap as the identity program.

## How Liam should work a bedroom take

1. Open **Character Consistency**. Confirm Alison + Bradley, ages 28, bands on. **Import Word / PDF** if you already have a bio; **Export Word / PDF** when the sheet is right. Not Excel.
2. Pin 3–10 bedroom refs each (same lamp, same adults).
3. Set **active cast** and face lock ~0.55.
4. Still Desk: ingest the locked frame.
5. **Pose Desk** (optional): body / hands / face on that still. Face pixels stay. Not video puppeting. [docs/POSE.md](POSE.md).
6. Motion Desk: posed or locked frame as the reference still → Enhance → **Animate** (SVD-XT).
7. Writing / UGC inherit the same bible automatically.

## Hard rules

- No sexual content involving minors or teen-appearing bodies.
- No Film Lab credits, quotas, or paywalls.
- Do not paste a commercial face API key into this repo.
