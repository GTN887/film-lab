# Gradio 6 + Director Timeline Gate

## Implemented
- Migrated removed Gradio 6 component arguments used by Film Lab: Audio/Video download/share buttons, Chatbot message mode, and Textbox copy button.
- Full `app.build_ui()` now completes under installed Gradio 6.5.1.
- Added a creator-facing Director Timeline drag surface for Dialogue, Voice, Performance, Reaction, and Camera lanes.
- Drag metadata carries the exact persistent store index and stable Character ID.
- Drop commits through the same persistent move functions used by the precision Move & Save editor.
- The precision editor remains available as an accessible fallback.

## Truth status
- Gradio 6 build blocker: PASS / REAL / TESTED in this environment.
- Director Timeline persistence backend: PASS / REAL / TESTED.
- Drag surface + browser save bridge: PARTIAL. Source integration and persistence boundary are tested; an actual mouse drag in the Creator's Windows/native Film Lab window is NOT TESTED here.
- Windows native pywebview launch: NOT TESTED.
- AMD/ComfyUI render from timeline direction: NOT TESTED.

No fake timeline events are inserted.
