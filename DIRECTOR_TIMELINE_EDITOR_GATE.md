# Director Timeline Editor Gate

## Software verification

| Capability | Status | Truth |
|---|---|---|
| Unified dialogue / voice / performance / reaction view | PASS | REAL / TESTED |
| Persistent actor performance beat creation | PASS | REAL / TESTED |
| Character-specific performance retiming | PASS | REAL / TESTED |
| Voice beat retiming with duration preservation | PASS | REAL / TESTED |
| Reaction/choreography retiming | PASS | REAL / TESTED |
| Persistent Camera Timeline | PASS | REAL / TESTED |
| Camera beat retiming | PASS | REAL / TESTED |
| Camera timeline enters generation conditioning | PASS | REAL / SOFTWARE TESTED through integration regression |
| Director Timeline Gradio page and Creator controls | PASS | REAL source wiring; full app launch currently blocked by pre-existing Gradio 6 Audio API incompatibility elsewhere in app.py |
| Take Board / Mark & Direct / Motion navigation from timeline | PASS | REAL source wiring |
| Graphical drag handles | PARTIAL | NOT CERTIFIED; reliable Move & Save control is implemented instead |
| Actual camera-keyframe renderer enforcement | NOT TESTED | Requires compatible workflow + machine certification |
| Actual AMD multi-system timeline render | NOT TESTED | Requires Windows/ComfyUI acceptance |

## QA

`346 passed, 0 failed, 12 warnings`

Warnings are the existing Pillow `Image.getdata` deprecations in setbuild/pointer tests.

A direct `app.build_ui()` check is currently blocked before reaching the Director Timeline by an existing Gradio 6 compatibility error: `gr.Audio(... show_download_button=...)`. This batch does not mislabel that full UI launch as certified.
