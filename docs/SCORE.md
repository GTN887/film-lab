# Score Desk (Film Lab)

Cue list and mux. **This machine only.** Zero Film Lab credits. No hosted music subscription.

A public “AI music” page may sell generations by the credit. Film Lab does the *job* with import, a local synth, and Cinema Desk mux.

## Priority on RX 5600 XT (~6GB)

1. **Import your music (primary)**  
   Drop a WAV / MP3 / FLAC into Score Desk. Files land in `data/projects/<name>/audio/music/`. Pick the file. Cinema Desk **Assemble reel** muxes it under picture.

2. **Local synth bed (always on)**  
   Mood + in/out (duration) + intensity + BPM. Film Lab writes a quiet harmonic bed so you can lock timing without a GPU model.

3. **MusicGen-small (AudioCraft) — optional**  
   Only if you installed audiocraft **and** set `FILM_LAB_MUSICGEN=1`. Tight on 6GB AMD. Expect Off / OOM. Treat as a later or off-box path. Film Lab never requires it.

## Cue fields

| Field | Use |
| --- | --- |
| Mood | intimate lamp, held breath, afterglow, uneasy quiet, neutral, warm pulse, night street |
| In / Out | Duration of the bed |
| Intensity | How loud the bed sits (0–1) |
| BPM | Slow swell locked to two beats |
| Notes | Diegetic-adjacent, under dialogue, etc. |

## Cinema Desk

Stitch picture first. Then **Assemble reel** with the Score Desk pick. Per-character Voice Desk cues mux in the same pass at their start times.

No Film Lab credits. Import stays the daily path on this card.
