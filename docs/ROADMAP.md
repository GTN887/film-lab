# Film Lab Roadmap

## Production slice 1 — prove the filmmaking loop

Build and verify this complete chain before expanding more desks:

1. Image/reference + Director instruction.
2. Genuine motion generation through the configured rendering engine.
3. Generated MP4 automatically becomes a persistent Take.
4. Take appears in Take Board with Review / Selected / Rejected state.
5. Exactly one Selected Take per Shot.
6. Notes, tags, status, and media survive application restart.
7. Selected Take flows into Cinema.
8. Cinema produces a real export.
9. Mark & Direct creates a new Take only when targeted regeneration is genuinely available.

## Hardware strategy

Film Lab is hardware-adaptive rather than tied to one GPU. Rendering capability is selected through engine/model adapters and hardware profiles so stronger future hardware can enable larger models, higher resolution, longer or more complex generation, and greater parallelism without redesigning Film Lab.

## Product truth

The goal is a top-tier AI filmmaking system. Comparisons with commercial products are targets, not completion claims. Film Lab only claims a capability after it works end to end and is verified.
