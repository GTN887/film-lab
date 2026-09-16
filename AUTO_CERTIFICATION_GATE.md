# Automatic Real-Render Certification Gate

Creator motion generation now carries its successful real ComfyUI output directly into Film Lab's evidence-based certification path.

Flow:

`Generate -> Preflight -> ComfyUI render -> persistent Take -> exact output provenance -> Take selection -> Cinema export -> store reload -> certificate`

Truth rules:
- Certification requires the exact generation output to be linked to a persistent Take.
- A real-render PASS requires generator `amd_i2v`, a READY preflight, and a validated generator route.
- Imported/mock/fallback/unvalidated outputs cannot receive a real-render PASS.
- Certification failure does not fabricate a Take or media file.
- Actual AMD hardware certification still requires execution on the Creator's Windows/ComfyUI machine.

Regression status for this recovery build: 273 passed, 12 existing Pillow deprecation warnings.
