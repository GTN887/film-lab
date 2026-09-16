# Film Lab

Private **film-school** studio for Liam's personal study: writing studio, script, character bible, stills, flexible shot cards, **local AMD img2vid** (ComfyUI sidecar) as the motion product, voice, score, grade, reel. Ken Burns is Advanced-only timing. Not a commercial SaaS.

**Works offline for local generation.** PRE-FINISH zip: unzip, read **CLICK_ME_FIRST.txt**, double-click **Install Film Lab** (purple FL icon). Daily: **START_FILM_LAB.bat** → **http://127.0.0.1:43123**. Uninstall: **UNINSTALL_FILM_LAB.bat**. Grok Bot can patch in place. No PowerShell for daily use. [PREFINISH.md](PREFINISH.md) · [docs/DESKTOP.md](docs/DESKTOP.md) · [docs/PACKAGING.md](docs/PACKAGING.md) · [docs/UNINSTALL.md](docs/UNINSTALL.md)

**Personal private use.** Two filming modes: **Regular** (everyday / family story, including Teen / Child / Infant — **non-sexual only**) and **18+ Explicit** (adult intimacy / nude / sex). That split is a **mode toggle only** — Film Lab stays one purple + soft cyan studio. There is no red Darkroom Suite skin and no second app for explicit work. Adult explicit / pornographic sex is **allowed** only in 18+ Explicit when every cast member is 18+ with an adult role. The app is local-only. There is no cloud upload, no hosted NSFW filter, **no Film Lab credit meter, quota, or paywall**, and no commercial video API sold by this lab. Optional Grok / Gemini / ChatGPT / Claude calls use **keys you own**. Under-18 roles never unlock explicit tools. **Not affiliated with the MPAA** or any ratings board — intensity labels are creative guides, not certificates and not a refusal gate.

Film Lab is **original software**. It is **not affiliated with, endorsed by, or a copy of Higgsfield** (or any other hosted AI video product). **[higgsfield.ai](https://higgsfield.ai/) is a UX / feature-job reference only** — card grid, shelves, project strip. We do **not** copy their branding, logos, model names, or APIs. Home-hub jobs use Film Lab names only (AI Production Pipeline, Still Desk, Take Board, Director Bridge, Cinema Desk, Director Brain, UGC Ads Desk, Character Consistency, Pose Desk, 3D Set Desk). The code, UI, and generators are our own Gradio + ffmpeg + open/local tools. **Zero Film Lab credits.**

**Generate** on **AI Production Pipeline** (home card) is **Upload once → Enhance | Pose | Animate** on the **same shot** (no re-upload). Full Motion Desk still has Quality, duration, Director Note, and Mark. **Upload → Pose adjust → Enhance → Animate**. Still-first OpenPose-style guide on the still (face lock stays; not video puppeting), then Add Prompt → short command → visible Prompt Enhancement → local ComfyUI SVD-XT (`svd_xt.safetensors` at `127.0.0.1:8188`, `--cuda-device 1` on the RX 5600 XT). Duration lock: **5s / 10s / 15s / 20s / 30s** one pass; **1 min / 2 min** last-frame chain + Cinema stitch. **Regenerate** is always on (new seed, same still + prompt + Quality). Ken Burns is **Advanced only**. Crash / OOM / off-prompt: [docs/CRASH_RECOVERY.md](docs/CRASH_RECOVERY.md) and [docs/QUALITY.md](docs/QUALITY.md). No Film Lab NSFW filter. Adults 18+ only. Missing extras **fail soft**.

**Quality program (RX 5600 XT, not NVIDIA).** One **Resolution** dropdown **480p / 720p / 1080p / 1440p / 4K** on Pipeline Enhance, Still, Motion, and Cinema export. Prefer native **480 / 720**; allow **1080** when VRAM allows; **1440p / 4K = generate lower then upscale on export**. Shot card stores Quality so Regenerate keeps it. DEBUG CHECKLIST on fail / OOM / crash: drop one step (1080→720→480); shorter duration / fewer frames; retry Regenerate; restart Comfy via the launcher if still dead; **never force native 4K** on this GPU. The same tip sits next to the Quality picker.

```
LOCAL ONLY — film-school study on this machine. Not a commercial SaaS.
Regular / story or 18+ Explicit. Adult explicit sex: 18+ Explicit + adults only.
No subscriptions, Film Lab credits, quotas, or paywalls.
```

## Module map

| Tab | What it does |
| --- | --- |
| **Home** | Studio hub: job cards + Lighting / Score / Voice / Effects / Pose / Set craft desks, looks shelf, local lot. [HOME.md](HOME.md) |
| **Save Library** | Browse stills / takes / sets / writing on this PC. Optional OneDrive / Google Drive folder backup when online. [docs/LIBRARY.md](docs/LIBRARY.md) |
| **AI Production Pipeline** | One desk. **Enhance | Pose | Animate** on the **same shot** — no re-upload. Back to Home. [docs/PIPELINE.md](docs/PIPELINE.md) |
| **Motion Desk** | Full desk: Quality, duration, Director Note, Mark. **Any still → Animate**. [docs/MOTION.md](docs/MOTION.md) · [docs/QUALITY.md](docs/QUALITY.md) · [docs/ASPECT.md](docs/ASPECT.md) |
| **Still Desk** | Ingest stills at Quality (4K stills ingest at 720p). `data/projects/<name>/stills/` |
| **Take Board** | Play a take. Pause, click the person, **Dream about…** (Actor A/B/C + look-refs). [docs/PLAYBACK.md](docs/PLAYBACK.md) · [docs/DREAM.md](docs/DREAM.md) |
| **Director Bridge** | Agent tabs (ChatGPT, Claude, Grok Bot, Cursor, Claude Code, OpenClaw, Hermes) + MCP / CLI — not a hosted plugin |
| **Cinema Desk** | Gallery, stitch, reel timeline, per-character dialogue mux |
| **Director Brain** | Writing Studio. **Import** PDF / Word / PowerPoint / Excel / text, **Fuse** Grok + Gemini drafts, **Export** Word / PDF / PowerPoint / Excel / plain text, **Plan shots** → Motion. Local templates + optional **Grok / Gemini / ChatGPT / Claude** keys you own |
| **UGC Ads Desk** | Product ref + avatar + prompt → Enhance → Animate. Optional hook→CTA plan. [docs/UGC.md](docs/UGC.md) |
| **Character Consistency** | Bible + multi-ref character sheet + **Word / PDF** bio import/export + **micro-expressions / behavior** + **Family Genetics** (infant / child / teen from two adult refs) + InstantID/FaceID stubs + **Environment / Set lock**. [docs/CHARACTER_CONSISTENCY.md](docs/CHARACTER_CONSISTENCY.md) · [docs/PERFORMANCE.md](docs/PERFORMANCE.md) · [docs/GENETICS.md](docs/GENETICS.md) · [docs/ENV_LOCK.md](docs/ENV_LOCK.md) |
| **Script** | Fountain-ish scenes. Export `.fountain` / `.txt` / `.pdf`. Link → shot cards |
| **Lighting Desk** | Studio / natural + cinematic pack (or skip). Same list on Pipeline Enhance, Effects, Cinema. [docs/LIGHTING.md](docs/LIGHTING.md) |
| **Voice Desk** | Per-character Voice profile, tagged-line routing, Local TTS default + cloud picker. [docs/VOICE.md](docs/VOICE.md) |
| **Score Desk** | Cue list (mood, duration, intensity). Import-first. Local synth. Cinema mux. [docs/SCORE.md](docs/SCORE.md) |
| **Effects Desk** | Character still + optional location / product + descriptive presets. Local Comfy. [docs/EFFECTS.md](docs/EFFECTS.md) |
| **Pose Desk** | Still-first body / hands / face guide. Face lock stays. Then Animate. Not video puppeting. [docs/POSE.md](docs/POSE.md) |
| **3D Set Desk** | **LOCKED Environment from photo** + **Pointer / Go-to** (Actor A walks to a bathroom / locked room; take lands on Take Board). Stored in `data/projects/<name>/sets/`, `stills/`, `takes/`. [docs/SET.md](docs/SET.md) |
| **Mark & Direct** | Circle / square / lasso on a still or clip frame. Per-region note. Stackable. Then Animate / Regenerate. [docs/MARK.md](docs/MARK.md) |
| **Finish** | Original `.cube` LUTs + ffmpeg fade / grain / bloom / letterbox / speed. Looks shelf lands here |
| **Queue** | Sequential shot generate |

```
app.py                      Gradio studio
film_lab/shot_card.py       Shot JSON
film_lab/script.py          Scenes / Fountain
film_lab/writing.py         Writing Studio drafts + optional Grok / Gemini / ChatGPT / Claude / Dual
film_lab/write_fuse.py      Import office files + local Fuse into screenplay / novel / beat sheet
film_lab/office.py          PDF / Word / PowerPoint / Excel import + typed export
docs/WRITING.md             Import → view / Fuse → edit → Export → Plan shots → Motion / Take Board
film_lab/llm.py             User-owned xAI + Gemini + OpenAI + Anthropic clients (no Film Lab credits)
film_lab/genres.py          Genre catalog, presets, age guard
film_lab/senses.py          Emotion, senses, environment presets + prompt brief
film_lab/living.py          Living style / conditions + nest presets
film_lab/intimacy.py        Intimacy / sex modes including explicit adult porn
film_lab/intensity.py       Theatrical content-intensity dial (0–1 + named presets)
film_lab/characters.py      Bible + prompt inject + adult age guard
film_lab/char_sheet.py      Character Bible Word / PDF sheet import + export (not Excel)
film_lab/genetics.py        Family Genetics — two adult refs → Regular/story child cards
docs/GENETICS.md            Actor A + Actress B, infant/child/teen, belongs-to both
film_lab/performance.py     Micro-expressions, full-body behavior, prop actions
docs/PERFORMANCE.md         Bible / Note / Pose / Voice / Writing / Mark / World Note
film_lab/dream.py           Dream / Lucid Layer — parent sleep → child scenes → wake
docs/DREAM.md               Enter dream / Thought bubble; inner vision; text stylize; stitch sleep→dream→wake
film_lab/consistency.py     Actor + env program, InstantID/FaceID/OpenPose stubs (6GB AMD)
film_lab/envlock.py         Environment / Set lock (World Note + 3D Set, regenerate keeps it)
docs/ENV_LOCK.md            Locked set still, ControlNet geometry, AMD OOM notes
data/characters/            Studio library JSON (Alison / Bradley)
film_lab/lighting.py        Lighting presets + prompt chips
film_lab/voice.py           Cinematic VO + local TTS
film_lab/music.py           Score cues + synth / import
film_lab/video_tools.py     Local video-path notes (6GB AMD)
film_lab/motion_path.py     Prompt + still → MP4 with ComfyUI (Ken Burns Advanced only)
docs/MOTION_SMOKE.md        Windows three-click generate test
docs/EXTENDED_REEL.md       60s / 120s = chain short SVD clips + stitch
film_lab/quality.py         Quality lock (480p / 720p / 1080p / 1440p / 4K) + AMD native vs export
docs/ASPECT.md              Aspect picker next to Quality (image + video)
docs/QUALITY.md             RX 5600 XT native sizes, 4K upscale, OOM checklist
film_lab/duration.py        Motion duration lock (5–30s / 1–2 min)
film_lab/extend.py          Beat sheet, last-frame continue, sequence stitch
docs/CRASH_RECOVERY.md      Restart launcher, Comfy 8188, OOM, off-prompt, salvage
film_lab/effects.py         Effects Desk presets + Comfy / stub notes
docs/EFFECTS.md             Preset shelf; finish in DaVinci / After Effects
film_lab/pose.py            Still-first OpenPose-style pose / hand–face guide
docs/POSE.md                Pose Desk — still edit, then SVD Animate
film_lab/filming.py         Regular | 18+ Explicit split + family roles + hard intimacy gate
docs/FILMING.md             Filming modes and age/role safety
film_lab/setdesk.py         3D Set notes (orbit / aerial / outdoor plates)
film_lab/setbuild.py        LOCKED Environment from photo → sets / stills / takes
film_lab/pointer.py         Pointer / Go-to — Actor A walks to a locked room; Take Board
docs/SET.md                 3D Set Desk — photo lock, notes, not a 3D engine
film_lab/mark.py            Mark & Direct — region edit / masked prompt
docs/MARK.md                Circle / square / lasso, then Animate
docs/PLAYBACK.md            Take Board Play vs Fix — pause never edits
film_lab/playback.py        Playback / Direct mode chrome
docs/VOICE_NOTES.md         Type or speak into the same Director / Mark note
film_lab/voice_notes.py     Mic → same note box, then Apply / Regenerate
film_lab/director_notes.py  Director Note (performance) + World Note (mise-en-scène)
docs/DIRECTOR_NOTES.md      Click face → note; Apply folds into Enhance → Pose → Animate
film_lab/luts.py            Stock LUTs
film_lab/finish.py          LUT + VFX
film_lab/reel.py            Board + assemble
film_lab/stitch.py          Crossfade + audio mux
film_lab/hub.py             Home cards, looks shelf, local lot
film_lab/offline.py         Offline-first banner, safe mode, repair copy
film_lab/desktop.py         Windows icon / shortcut / zip payload (no PowerShell daily)
film_lab/winlnk.py          Portable Install Film Lab.lnk for the zip
START_FILM_LAB.bat          Daily desktop start (cmd — no PowerShell)
INSTALL_FILM_LAB.bat        Places files + Desktop / Start Menu shortcuts
UNINSTALL_FILM_LAB.bat      Remove shortcuts and optional install folder
REPAIR.bat                  Offline Repair menu (cmd)
docs/DESKTOP.md             Icon, START, Repair, works offline
docs/PACKAGING.md           Zip (Install Film Lab.lnk) / Inno Setup.exe
docs/UNINSTALL.md           Shortcuts + folder delete; Grok Bot patch in place
film_lab/studio.css         Dark studio landing chrome (not default Gradio)
film_lab/ugc.py             UGC Ads Desk briefs + local script + 9:16 plan
film_lab/product.py         Product still composite + bible/upload avatar + Animate
film_lab/motion_scope.py    Any still → Animate; two-beat product example (open → pour)
docs/UGC.md                 Product flow + spoken plan (adults 18+, zero credits)
docs/MOTION.md              Motion primary img2vid; multi-beat via Mark & Direct / stitch
film_lab/variations.py      Take Board variants
film_lab/bridge.py          Director Bridge agent page (MCP / CLI)
film_lab/cli.py             film-lab-cli stub (`python -m film_lab.cli init`)
film_lab/mcp_stub.py        Print-only Film Lab MCP document (`python -m film_lab.mcp_stub`)
docs/DIRECTOR_BRIDGE.md     Agent tabs + Claude Code two-step
docs/cli/SKILLS.md          Companion skill notes for CLI agents
docs/mcp/film-lab.mcp.json  Example local MCP client config
film_lab/generators/        AMD ComfyUI img2vid (product) + Ken Burns Advanced timing
workflows/                  ComfyUI API graphs (AnimateDiff v3, LTX 2B)
examples/alison_bradley/    Sample shots, scene, characters (JSON)
HOME.md                     Home hub + UGC Ads workflow (not a paid UGC API)
docs/LIGHTING.md            Lighting Desk research → UI
docs/SCORE.md               Score Desk research → UI
docs/VOICE.md               Voice Desk research → UI
docs/PROVIDERS.md           Nested Local / cloud picker menus (keys you own)
docs/DIRECTOR_WORKFLOW.md   Full pipeline
data/luts/                  Drop your own .cube files here
```

## Requirements

- Python 3.11+ (3.12 is fine)
- [ffmpeg](https://ffmpeg.org/) on `PATH`
- A browser on the same machine

Real motion needs the ComfyUI sidecar on the AMD card — [docs/AMD_IMG2VID.md](docs/AMD_IMG2VID.md). Ken Burns is Advanced timing only, not a substitute product.

## Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x scripts/run.sh
./scripts/run.sh
```

Ubuntu/Debian: `sudo apt install ffmpeg`  
Optional speech: `sudo apt install espeak-ng` (or rely on the placeholder WAV / pyttsx3)  
macOS: `brew install ffmpeg`

Then open [http://127.0.0.1:43123](http://127.0.0.1:43123).

**Windows first run:** open [START_HERE.md](START_HERE.md). Double-click **INSTALL_FILM_LAB.bat**, then the **Film Lab** Desktop icon — Comfy on GPU1 + Film Lab + browser. No PowerShell for daily use. Cursor “Open in Web” / Origin shows **source code only**. The desk is local Gradio at http://127.0.0.1:43123. **Works offline for local generation.**

## Windows

1. Install Python 3.11+ and tick **Add python.exe to PATH**.
2. Install ffmpeg once (`winget install Gyan.FFmpeg` in any new terminal).
3. Double-click **Install Film Lab** (`.lnk` in the zip, or `INSTALL_FILM_LAB.bat`). That copies files and pins Desktop / Start Menu shortcuts.
4. Double-click the **Film Lab** icon. Uninstall: **UNINSTALL_FILM_LAB.bat**. Repair: **REPAIR.bat**. Browse to `http://127.0.0.1:43123` if the browser does not open. Grok Bot can patch the install folder in place.

Optional zip / Setup.exe: [docs/PACKAGING.md](docs/PACKAGING.md). PowerShell `scripts\install_windows.ps1` is still there if you want it — not required for daily start.

## First session

1. Default project `alison-bradley-study` is created with example shots, the bedroom scene, and Alison / Bradley bible entries. **Home** is the six-job studio hub.
2. **Still Desk** stills (intimate stills stay on disk).
3. Pin 3–10 refs per character on **Characters**.
4. Open **Script**, load `INT. BEDROOM - NIGHT`, export Fountain if you want.
5. **Writing**: pull that scene, build a prompt pack (works offline), or set an xAI key to generate. Push pages back to Script; send rehearsal takes to Voice.
6. **AI Production Pipeline** (home card): drop a still **once**, then **Enhance | Pose | Animate** on that same shot — no re-upload. **Back to Home** when you are done. Full **Motion Desk** still has Quality, duration, Director Note, and Mark. [docs/PIPELINE.md](docs/PIPELINE.md) · [docs/POSE.md](docs/POSE.md) · [docs/PLAYBACK.md](docs/PLAYBACK.md).
7. Queue a second shot. **Voice Desk** a line. **Score Desk** a lamp bed.
8. **Finish** with `warm_lamp.cube` if you like. **Rebuild reel from scenes**, then **Assemble reel**.

Director notes: [docs/DIRECTOR_WORKFLOW.md](docs/DIRECTOR_WORKFLOW.md).

## Shot controls

Same flexible desk as before: start/end frame, **2–10s** (2–4s first on 6GB AMD), 16:9 / 9:16 / 1:1, camera move, motion strength, body notes, intimacy / sex mode (covered sheets / artistic nude / intimate sex / explicit / pornographic), character tags, lighting, optional negative + seed, plus scene link and bible ids. Camera + body notes feed the ComfyUI prompt.

Projects persist as:

```
data/projects/<name>/
  project.json
  stills/
  shots/*.json
  scenes/*.json
  characters/<id>/profile.json
  characters/<id>/refs/
  audio/dialogue/  audio/music/  audio/beds/
  writing/*.json
  luts/
  outputs/*.mp4
  reel.json
  gallery.json
```

## Writing Studio + Grok / Gemini / ChatGPT / Claude (optional)

The Writing tab always works **offline**: it builds a system/user prompt (with locked Alison/Bradley descriptors), saves drafts under `writing/`, and exports `.fountain` / `.md` / `.txt`. **Import** `.pdf` / `.docx` / `.txt` / `.md` (RTF later). Paste Grok online + Gemini (or any chat) and **Fuse** into one screenplay, novel, or beat sheet — local merge, no API. Edit the body, then **Plan shots → Motion Desk** (cap 8, ~2.5s) or Open Take Board. See [docs/WRITING.md](docs/WRITING.md).

**There is no Film Lab credit system.** This is a private film-school desk. Optional cloud LLMs are **your** API keys. If xAI, Google, OpenAI, or Anthropic bills those calls, that is their account — Film Lab never meters, quotas, or resells generation.

Provider picker: **Local templates only** | **Grok (xAI)** | **Gemini (Google)** | **ChatGPT (OpenAI)** | **Claude (Anthropic)** | **Dual (two providers)**. Dual default: Gemini writes the story spine, Grok expands dialogue and roleplay. ChatGPT can take the spine, a sequential full-draft → rewrite, or a compare page (ChatGPT + Grok). You can also run Grok + Gemini sequential / compare. Film Lab does **not** require a hosted plugin.

Genre is first-class: pick a **primary** from the catalog (romance, thriller, horror, fantasy, SF, YA 18+, theatrical teen film, erotica, experimental, …), optional **secondary** tags, and free-text custom tags. **Apply genre preset** fills tone, pacing, and an editable tropes checklist. Example prompts filter by the selected genres. The pack injects into novel, screenplay, book→screenplay (genre-aware adaptation notes — scare set pieces, emotional set pieces, thriller turns), roleplay, and rewrite. Genre persists on the draft JSON and on the linked Script scene. Young adult / New adult / adult coming-of-age / **Teen film / coming-of-age (theatrical)** are labeled **18+ protagonists only** (college senior, 18–19+, newly adult — never high-school minors). Intimate or nude study plus minor-coded language is blocked.

### Content intensity dial (not a ratings board)

Intimacy mode is *what is available on camera*. Intensity is *how far the writing and frame go*. They compose; the app does **not** refuse adult explicit when the cast is 18+.

| Preset | Slider landmark | Creative feel |
| --- | --- | --- |
| **Implied / soft** | ~0.22 | PG-13-style heat: suggestion, cutaways, tension, closed doors |
| **Frank / theatrical R** | ~0.62 (default) | Clear sex, adult language, visible intimacy without default porn framing |
| **MA-17 / Euphoria-style** | ~0.82 | Euphoria-level heat for **clearly adult** characters — not high-school / teen-appearing sex |
| **Explicit / adult study** | 1.0 | Full pornographic language and framing allowed for this private lab |

The slider is a continuum 0–1. Sit anywhere between the named points — you have more flexibility than theater ratings. These labels are **director shorthand only**. Film Lab is **not affiliated with the MPAA**, the BBFC, or any certificates board. Numeric **Age (years) 18+** on the character bible is required for intimate, frank, or explicit work. Under-18 is always a hard block. There is no in-app refusal for adult explicit.

**Living style & conditions** live on the character bible and as project nest defaults in `project.json`. Writing Studio inherits from selected characters → linked scene → project, or override per draft. Presets: Newlywed warm apartment, Tight budget thin walls, Quiet suburban house, Noisy city loft. Thin walls couple to hearing; a cramped room couples to touch. The same nest line injects into local shot prompts. Story labels only — not real household PII.

Separate from story genre: the **Emotion & senses** and **Environment** accordions. Primary + conflicting emotion, intensity, inner vs outer (subtext), relationship temperature; optional touch / smell / taste / hearing / sight; set, time, weather, light, ambient, blocking, props. Room presets (*Warm bedroom newlywed*, *Cold argument kitchen*, *Rain outside window*). **Sensory pass** requires multi-sense detail grounded in that room. Screenplay keeps dialogue playable and puts sensation in action lines. These fields persist on the writing draft and compose with genre into one local director brief. See [docs/DIRECTOR_WORKFLOW.md](docs/DIRECTOR_WORKFLOW.md).

For live generation, set keys in the environment — never in the repo:

```bash
export FILM_LAB_XAI_API_KEY="xai-..."          # or XAI_API_KEY
export FILM_LAB_XAI_MODEL="grok-4.3"           # optional; confirm on https://docs.x.ai
# export FILM_LAB_XAI_BASE="https://api.x.ai/v1"

export FILM_LAB_GEMINI_API_KEY="AIza..."       # or GEMINI_API_KEY / GOOGLE_API_KEY
export FILM_LAB_GEMINI_MODEL="gemini-3.8-flash"  # optional; current Flash GA id
# export FILM_LAB_GEMINI_BASE="https://generativelanguage.googleapis.com/v1beta"

export FILM_LAB_OPENAI_API_KEY="sk-..."        # or OPENAI_API_KEY
export FILM_LAB_OPENAI_MODEL="gpt-4.1"         # optional; current chat completions id
# export FILM_LAB_OPENAI_BASE="https://api.openai.com/v1"

export FILM_LAB_ANTHROPIC_API_KEY="..."        # or ANTHROPIC_API_KEY
export FILM_LAB_ANTHROPIC_MODEL="claude-sonnet-4-5"  # optional
# export FILM_LAB_ANTHROPIC_BASE="https://api.anthropic.com/v1"
python app.py
```

The Writing panel shows **Grok / Gemini / ChatGPT / Claude Off/Ready** separately. A missing key leaves that provider Off; the rest of the studio still works. Generate with a live provider **leaves this machine** to xAI, Google, OpenAI, and/or Anthropic. Wrong model ids fail soft (HTTP 404) — set `FILM_LAB_XAI_MODEL`, `FILM_LAB_GEMINI_MODEL`, `FILM_LAB_OPENAI_MODEL`, or `FILM_LAB_ANTHROPIC_MODEL` to an id your account lists.

**Director Bridge** is an agent page: ChatGPT, Claude, Grok Bot, Cursor, Claude Code, OpenClaw, Hermes, with an **MCP / CLI** toggle. Claude Code CLI is two steps — copy the Film Lab setup prompt (`film-lab-cli` / `python -m film_lab.cli`), then Connect and start creating. OpenClaw / Hermes stay Coming soon. See [docs/DIRECTOR_BRIDGE.md](docs/DIRECTOR_BRIDGE.md).

Default Gemini id is `gemini-3.8-flash` (documented on [ai.google.dev](https://ai.google.dev/gemini-api/docs/models) as of 2026-09). Default ChatGPT id is `gpt-4.1` (OpenAI Chat Completions). If a vendor retires an id, override the env var. Default Grok id is `grok-4.3`.

There is no NSFW filter in Film Lab. Adult explicit / pornographic sex is allowed; characters stay adults 18+.

This is original Film Lab UI, not a copy of any proprietary Grok, Gemini, or ChatGPT product. Do not wire a hosted “superagent” plugin as a required path.

## Optional local extras (all fail soft)

| Extra | How |
| --- | --- |
| **AMD img2vid (default)** | `scripts/install_comfyui_amd.ps1` then `run_comfyui_amd.ps1`. Models: `v1-5-pruned-emaonly.safetensors` + `v3_sd15_mm.ckpt` (or LTX `ltxv-2b-0.9.8-distilled.safetensors`). See [docs/AMD_IMG2VID.md](docs/AMD_IMG2VID.md) |
| CUDA I2V (NVIDIA only) | Optional. `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124` and `diffusers transformers accelerate`. Model: `stabilityai/stable-video-diffusion-img2vid-xt` or `FILM_LAB_I2V_MODEL` |
| Piper TTS | Install the Piper CLI and a local voice |
| Coqui XTTS | Local `TTS` package + weights |
| MusicGen | `pip install audiocraft` — the desk still renders synth beds without it |
| Face lock | Point ComfyUI IP-Adapter / InstantID at `characters/<id>/refs/`. Film Lab does not call a hosted face API |

ComfyUI is the **wired** local motion path (AnimateDiff v3 on 6GB, LTX 2B if the node exists). Open weights only. Do not jailbreak a commercial API from this app.

Stock LUTs (`warm_lamp`, `soft_print`, `cool_shadow`) are original Film Lab samples. Drop your own licensed `.cube` files in `data/luts/`. Do not pirate commercial LUT packs.

## Environment

| Variable | Default | Meaning |
| --- | --- | --- |
| `FILM_LAB_PORT` | `43123` | Gradio port |
| `FILM_LAB_HOST` | `127.0.0.1` | Bind address (open http://127.0.0.1:43123) |
| `FILM_LAB_COMFY_URL` | `http://127.0.0.1:8188` | ComfyUI sidecar |
| `FILM_LAB_COMFY_WORKFLOW` | bundled `workflows/amd_*_api.json` | Custom API-format graph |
| `FILM_LAB_I2V_WIDTH` / `HEIGHT` | 512 / 288 (16:9) | Internal AMD size |
| `FILM_LAB_I2V_MODEL` | `stabilityai/stable-video-diffusion-img2vid-xt` | Optional NVIDIA diffusers weights |
| `FILM_LAB_XAI_API_KEY` / `XAI_API_KEY` | unset | Optional Grok key you own (never committed) |
| `FILM_LAB_XAI_MODEL` | `grok-4.3` | xAI chat model id |
| `FILM_LAB_XAI_BASE` | `https://api.x.ai/v1` | OpenAI-compatible base URL |
| `FILM_LAB_GEMINI_API_KEY` / `GEMINI_API_KEY` / `GOOGLE_API_KEY` | unset | Optional Gemini key you own |
| `FILM_LAB_GEMINI_MODEL` | `gemini-3.8-flash` | Gemini generateContent model id |
| `FILM_LAB_GEMINI_BASE` | `https://generativelanguage.googleapis.com/v1beta` | Gemini REST base |
| `FILM_LAB_OPENAI_API_KEY` / `OPENAI_API_KEY` | unset | Optional ChatGPT key you own (never committed) |
| `FILM_LAB_OPENAI_MODEL` | `gpt-4.1` | OpenAI Chat Completions model id |
| `FILM_LAB_OPENAI_BASE` | `https://api.openai.com/v1` | OpenAI Chat Completions base URL |

Do not deploy this to Vercel or any public host.

## Tests

```bash
python tests/test_smoke.py
python tests/test_studio.py
```
