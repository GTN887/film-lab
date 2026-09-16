# Mark & Direct

Region edit on a **still** or a **frozen take frame**. Draw **circle / square / lasso**, write a note (clothing, body, face emotion, …), **Apply**. One region at a time; they stack. Then **Animate / Regenerate** so the clip follows the marked frame.

On **Take Board**, this is **Direct** mode only. Default is **Playback** — play / pause / scrub. Pause freezes; it does not edit. Enter Direct with **Mark & Direct** · **Fix this frame**. Banner: **Directing — changes will make a new take**. Exit Direct returns to Playback. The old take stays. See [PLAYBACK.md](PLAYBACK.md).

Local overlay + **MARK NOTE** always work. Optional Comfy inpaint (`workflows/mark/inpaint_region.json`) is a stub — Film Lab **will not fake** an inpaint rewrite.

Works with **Pose** and **Director Note**. Mark the **head** on a sleeping take to **Enter dream** (linked child scenes) or, with **Thought bubble** style, overlay dream content on the sleeping shot. See [DREAM.md](DREAM.md). **Regular | 18+ Explicit** still applies: sexual / nude / undress region notes stay locked unless mode is 18+ Explicit and every cast member is 18+.

Zero credits.

## Flow

1. Play a take on Take Board (or drop a still on Motion / Mark Desk).
2. Press **Mark & Direct** · Fix this frame. Pause never opens this.
3. Pick circle / square (place with X / Y / size), lasso (brush), or **pointer** (Actor A → locked room / bathroom → go-to take on Take Board).
4. Choose the region and write the note — or **speak** it (mic on the note box). Actor / prop / object. Same note as typed. Pick a **prop action** (pick up book, set glass down) to fill an empty note and target **prop action**. Then Apply / Regenerate. See [VOICE_NOTES.md](VOICE_NOTES.md) and [PERFORMANCE.md](PERFORMANCE.md).
5. Apply. Stack another if you need it.
6. **Regenerate** — a new take is forked. The old one stays on the board.

Sidecars: `stills/mark_<id>.png` + `*.mark.json`. Stack persists as `mark_direct.json` on the project (not committed). Frozen Direct frame: `direct_frame.png` (not committed).
