# Visual Diffing (Recipe Add-on)

This is an optional add-on for SmokeHarvest to compare screenshots across runs.

## Why

Visual diffs help catch layout or content shifts that are hard to capture with selectors alone.

## Folder Structure

Each run lives in a single timestamped folder with everything together:

```
screenshots/
└── 20260129-181436/
    ├── explore/          <- what the MCP browser saw (live app)
    │   ├── 01-login.png
    │   ├── 02-otp.png
    │   └── ...
    ├── script/           <- what Playwright test scripts saw
    │   ├── 01-login.png
    │   ├── 02-otp.png
    │   └── ...
    ├── diff/             <- pixel difference images (generated)
    │   ├── 01-login.png
    │   ├── 02-otp.png
    │   └── ...
    └── report.md         <- verdict & RMS values (generated)
```

Open the folder, compare `explore/04-game.png` next to `script/04-game.png`, check `diff/04-game.png` for the delta, read `report.md` for the summary — all in one place.

## Minimal Rules (from real usage)

- **Lock the viewport** (example: 1024×768) for both exploratory and scripted runs.
- **Prefer viewport-only screenshots** (not full-page) to avoid height drift.
- **Use predictable filenames** like `NN-description.png` (e.g., `01-login.png`, `03-after-otp.png`). The diff script pairs files by matching filenames across `explore/` and `script/`.

## If you are using Playwright MCP in Docker

Screenshots are written inside the container (commonly `/tmp/playwright-output`). Copy them into the `explore/` subfolder of your run:

```bash
# Create the run folder
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p screenshots/$TIMESTAMP/explore screenshots/$TIMESTAMP/script

# After Docker MCP explore, copy screenshots out
docker cp <container_name>:/tmp/playwright-output/. screenshots/$TIMESTAMP/explore/
```

**Watch for stale files.** The Docker container retains screenshots from earlier runs. If old files leak in, remove them before diffing:

```bash
# Only keep the NN-*.png files you expect
ls screenshots/$TIMESTAMP/explore/
```

## Scripted Test Screenshots

Your Playwright test script should write into the `script/` subfolder. Use an environment variable to set the run path:

```python
import os
from pathlib import Path

SHOT_DIR = Path(os.environ.get("SHOT_RUN", "screenshots/latest")) / "script"

# In your test
page.screenshot(path=str(SHOT_DIR / "01-login.png"))
```

Run with:

```bash
SHOT_RUN=screenshots/20260129-181436 pytest tests/test_visual_script.py -v
```

## Running the Diff Script

This repo includes a diff script at `scripts/diff_screenshots.py`.

### Setup (isolated env)

Option A: `uv` (fast, no global install)

```bash
uv venv
source .venv/bin/activate
uv pip install pillow
```

Option B: `python -m venv` (standard)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pillow
```

### Run

```bash
# Diff a specific run
python3 scripts/diff_screenshots.py screenshots/20260129-181436

# Or let it find the latest run automatically
python3 scripts/diff_screenshots.py
```

The script writes `diff/*.png` images and `report.md` into the same run folder.

## RMS Thresholds

The diff script uses RMS (root mean square) of pixel differences to classify each step:

| RMS | Verdict | Meaning |
|-----|---------|---------|
| < 22 | **MATCH** | Rendering noise (font smoothing, sub-pixel, emoji rendering) |
| 22–30 | **REVIEW** | Possible change — inspect the diff image |
| ≥ 30 | **DIFFERS** | Different content — scripts need updating or app has a bug |

These thresholds were tuned from real runs comparing Docker Chromium (MCP explore) against local Chromium (pytest-playwright). Identical page content produces RMS ~11–21 due to rendering engine differences. Adjust if your environment produces different baselines.

## Report Verdicts

The generated `report.md` ends with one of three verdicts:

- **ALL CLEAR** — Every step matches. Explore and scripts see the same thing.
- **REVIEW NEEDED** — Minor diffs detected (RMS 22–30). Likely cosmetic, but check the diff images.
- **SCRIPTS NEED UPDATE** — Major diffs detected (RMS ≥ 30). The live app has changed in a way the scripts don't account for. The report identifies the first divergence point.

## Notes

- If image sizes differ, the script pads to match and reports a size mismatch.
- For clean diffs, keep viewport + scroll position consistent between runs.
- The `screenshots/` folder should be in `.gitignore` — these are ephemeral artifacts, not committed baselines.
