# Visual Diffing (Recipe Add-on)

This is an optional add-on for SmokeHarvest to compare screenshots across runs.

## Why
Visual diffs help catch layout or content shifts that are hard to capture with selectors alone.

## Minimal Rules (from real usage)
- **Lock the viewport** (example: 1024x768) for both exploratory and scripted runs.
- **Prefer viewport-only screenshots** (not full-page) to avoid height drift.
- **Use predictable filenames** so diffs can pair files automatically.
  - Example: `explore-01-home.png` and `script-01-home.png`

## If you are using Playwright MCP in Docker
Screenshots are written inside the container (commonly `/tmp/playwright-output`). Copy them into your repo:

```bash
docker cp <container_name>:/tmp/playwright-output/. /path/to/your/repo/screenshots/
```

## Quickstart: Local diff script (isolated env)

This repo includes a tiny diff script at `scripts/diff_screenshots.py`.

Option A: `uv` (fast, no global install)

```bash
# from repo root
uv venv
source .venv/bin/activate
uv pip install pillow
python3 scripts/diff_screenshots.py
```

Option B: `python -m venv` (standard)

```bash
# from repo root
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pillow
python3 scripts/diff_screenshots.py
```

The script writes:
- `screenshots/diffs/<timestamp>/diff-*.png`
- `screenshots/diffs/<timestamp>/report.md`

## Notes
- If image sizes differ, the script pads to match and reports a size mismatch in the report.
- For clean diffs, keep viewport + scroll position consistent between runs.
