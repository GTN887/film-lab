# Voice notes — typed or spoken

**Director Note** and **Mark & Direct** accept the same note from the keyboard **or** the mic. Speech transcribes into the text box already on the desk. Then **Apply / Regenerate** as usual.

- **Actor** — Director Note acting beats (hold the look, don't rush).
- **Prop / object / clothing** — Mark & Direct region note (jacket, glass, walk).

Pause on Take Board still does not edit. Speak only after you are in the note box (Director popup, or Direct → region note).

## How

1. Type, or press the **Mic** and speak.
2. The transcript lands in the **same note**. Edit if you want.
3. **Apply** or **Regenerate**.

No Film Lab credits.

## Transcriber

Local first:

1. `pip install vosk` and unzip the small English model into `data/models/vosk-model-small-en-us-0.15` (or set `FILM_LAB_VOSK_MODEL`).
2. Or `pip install faster-whisper` (CPU — not NVIDIA).
3. Or a writing-studio key you already own (`FILM_LAB_OPENAI_API_KEY`) for cloud STT.

If nothing is installed, **type the note**. Film Lab will not invent a transcript.

Sidecar audio is not committed. Models stay in `data/models/` (gitignored).
