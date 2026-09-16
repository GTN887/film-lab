# Creator Acceptance Gate

Film Lab now has a Creator-facing **Certification** tab.

## Purpose

The page is a read-only view of the latest automatic real-render certification for the current project. It never creates evidence and never upgrades a pipeline-only run into a real-render PASS.

## Creator flow

1. Generate normally from Motion Desk.
2. Generation runs the existing automatic runtime preflight.
3. A successful generated output is linked to its persistent Take and automatically certified.
4. Open **Certification** and click **Refresh certification**.
5. Film Lab shows PASS / PARTIAL / FAIL / NOT TESTED plus each certification stage, Take identity, and Cinema output.

## PASS rule

PASS requires `certified_real_render=true` in the saved certification. Imported, mock, fallback, corrupt, or pipeline-only records cannot be shown as a real-render PASS.

## QA

- Full Python regression suite: 277 passed, 0 failed, 12 existing Pillow deprecation warnings.
- Source compile: PASS.
- UI construction smoke test in the build container: BLOCKED by the container's Gradio 6.8.0; this source pins Gradio 4.44.1 and the existing app uses Gradio 4-only component arguments. This is an environment mismatch, not a certification-page test failure.
- Windows + AMD + ComfyUI real-render acceptance: NOT TESTED until run on the Creator machine.
