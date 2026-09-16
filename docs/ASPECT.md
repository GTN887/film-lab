# Aspect lock (image + video)

Picker is **one dropdown**. Each option shows a small **frame icon** next to the label: square (1:1), tall (9:16 / 4:5 / 2:3 / 3:4), landscape (16:9 / 3:2 / 4:3 / 1.85:1), ultrawide (21:9 / 2.39:1 cinema scope). On **Pipeline Enhance** it sits next to Resolution and Lighting. Same framed list on Still / Motion.

- **Image** — Still ingest fits the plate to Quality × Aspect.
- **Video** — Motion Animate / Regenerate uses the same frame.
- The **shot card** stores `aspect_ratio`. **Regenerate** keeps it unless you change the picker.
- Experiment freely per take. Changing the picker is enough; you do not need a new project.

Default **16:9**. **9:16** is the UGC button. Effects Desk still uses its own 9:16 / 16:9 size lock.

Zero credits. AMD RX 5600 XT — short side follows Quality (720p 16:9 = 1280×720; 720p 9:16 = 720×1280; 720p 21:9 = 1680×720). 4K export upscales the native pass.

See [QUALITY.md](QUALITY.md).
