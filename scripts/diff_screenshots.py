#!/usr/bin/env python3
"""Diff explore vs script screenshots and write diff images + report.

Usage:
  python3 scripts/diff_screenshots.py [run_folder]

run_folder is a timestamped directory under screenshots/ with this layout:

    screenshots/20260129-180429/
    ├── explore/      <- explore screenshots (NN-name.png)
    ├── script/       <- scripted test screenshots (NN-name.png)
    ├── diff/         <- generated diff images (NN-name.png)
    └── report.md     <- generated report

Defaults to the latest timestamped folder in screenshots/.
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
SHOTS_ROOT = ROOT / "screenshots"

# --- Thresholds ---
# These were tuned from real runs comparing Docker Chromium (MCP explore)
# against local Chromium (pytest-playwright scripts). Font smoothing,
# sub-pixel rendering, and emoji rendering cause RMS ~11-21 even when
# the page content is identical. Real content differences start at ~30+.
MATCH_THRESHOLD = 22.0   # below this = rendering noise
REVIEW_THRESHOLD = 30.0  # below this = minor diff; at or above = major diff


def rms(stat):
    if isinstance(stat, (list, tuple)):
        return math.sqrt(sum(v * v for v in stat) / len(stat))
    return stat


def load_image(path: Path) -> Image.Image:
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def pad_to_same_size(a: Image.Image, b: Image.Image):
    max_w = max(a.width, b.width)
    max_h = max(a.height, b.height)

    def pad(img):
        if img.width == max_w and img.height == max_h:
            return img
        canvas = Image.new("RGB", (max_w, max_h), (0, 0, 0))
        canvas.paste(img, (0, 0))
        return canvas

    return pad(a), pad(b)


def build_pairs(run_dir: Path):
    """Match explore/NN-name.png with script/NN-name.png by filename."""
    explore_dir = run_dir / "explore"
    script_dir = run_dir / "script"
    pairs = {}
    if explore_dir.is_dir():
        for path in sorted(explore_dir.glob("*.png")):
            key = path.stem  # e.g. "01-login"
            pairs.setdefault(key, {})["explore"] = path
    if script_dir.is_dir():
        for path in sorted(script_dir.glob("*.png")):
            key = path.stem
            pairs.setdefault(key, {})["script"] = path
    return pairs


def main():
    if len(sys.argv) > 1:
        run_dir = Path(sys.argv[1])
    else:
        # Use the latest timestamped folder in screenshots/
        candidates = sorted(
            d for d in SHOTS_ROOT.iterdir()
            if d.is_dir() and (d / "explore").is_dir()
        )
        if not candidates:
            raise SystemExit("No run folders found in screenshots/")
        run_dir = candidates[-1]

    print(f"Diffing screenshots in: {run_dir}")

    diff_dir = run_dir / "diff"
    diff_dir.mkdir(parents=True, exist_ok=True)

    pairs = build_pairs(run_dir)
    if not pairs:
        raise SystemExit(f"No explore/script screenshot pairs found in {run_dir}")

    report_lines = ["# Screenshot Diff Report", "", f"Run: `{run_dir.name}`", ""]

    results = []  # (key, rms, size_mismatch)

    for key, items in sorted(pairs.items()):
        explore_path = items.get("explore")
        script_path = items.get("script")
        if not explore_path or not script_path:
            continue

        explore_img = load_image(explore_path)
        script_img = load_image(script_path)

        size_note = ""
        size_mismatch = explore_img.size != script_img.size
        if size_mismatch:
            size_note = f"(size mismatch: explore {explore_img.size} vs script {script_img.size})"
            explore_img, script_img = pad_to_same_size(explore_img, script_img)

        diff = ImageChops.difference(explore_img, script_img)
        stat = ImageStat.Stat(diff)
        diff_rms = rms(stat.rms)

        diff_path = diff_dir / f"{key}.png"
        diff.save(diff_path)

        results.append((key, diff_rms, size_mismatch))

        if diff_rms < MATCH_THRESHOLD:
            verdict = "MATCH (rendering noise)"
        elif diff_rms < REVIEW_THRESHOLD:
            verdict = "REVIEW (possible change)"
        else:
            verdict = "DIFFERS (different content)"
        report_lines.append(f"## {key} — {verdict}")
        report_lines.append("")
        report_lines.append(f"- explore: `explore/{key}.png`")
        report_lines.append(f"- script: `script/{key}.png`")
        report_lines.append(f"- diff: `diff/{key}.png`")
        report_lines.append(f"- rms: **{diff_rms:.2f}** {size_note}".rstrip())
        report_lines.append("")

    # --- Recommendation ---
    matches = [(k, r) for k, r, _ in results if r < MATCH_THRESHOLD]
    minor_diffs = [(k, r) for k, r, _ in results if MATCH_THRESHOLD <= r < REVIEW_THRESHOLD]
    major_diffs = [(k, r) for k, r, _ in results if r >= REVIEW_THRESHOLD]
    total = len(results)

    report_lines.append("---")
    report_lines.append("")
    report_lines.append("# Recommendation")
    report_lines.append("")
    report_lines.append(f"**{len(matches)}/{total}** steps match, "
                        f"**{len(minor_diffs)}** minor diffs, "
                        f"**{len(major_diffs)}** major diffs.")
    report_lines.append("")

    if not major_diffs and not minor_diffs:
        report_lines.append("**Verdict: ALL CLEAR** — Explore and script paths "
                            "are visually identical. No action needed.")
    elif major_diffs:
        report_lines.append("**Verdict: SCRIPTS NEED UPDATE** — The explore path "
                            "(live app) shows a different flow than the scripted tests.")
        report_lines.append("")
        report_lines.append("### Divergence point")
        report_lines.append("")
        first_major = major_diffs[0]
        report_lines.append(f"The first major divergence is at step **{first_major[0]}** "
                            f"(rms: {first_major[1]:.2f}).")
        report_lines.append("")
        report_lines.append("This means the live app has changed in a way the scripts "
                            "don't account for. The explore path succeeded through the "
                            "full flow, so the app itself is working correctly.")
        report_lines.append("")
        report_lines.append("### Steps that diverge")
        report_lines.append("")
        for k, r in major_diffs:
            report_lines.append(f"- **{k}** — rms: {r:.2f}")
        report_lines.append("")
        report_lines.append("### Action items")
        report_lines.append("")
        report_lines.append("1. Review the diff images side-by-side to confirm the "
                            "explore path represents the correct behavior.")
        report_lines.append("2. If explore is correct: **update the Playwright scripts** "
                            "to match the new flow.")
        report_lines.append("3. If explore found a bug: **fix the app**, then re-run "
                            "both paths to confirm scripts pass.")
    elif minor_diffs:
        report_lines.append("**Verdict: REVIEW NEEDED** — Minor visual differences detected. "
                            "These may be timing artifacts, animation states, or subtle "
                            "layout shifts.")
        report_lines.append("")
        for k, r in minor_diffs:
            report_lines.append(f"- **{k}** — rms: {r:.2f}")
        report_lines.append("")
        report_lines.append("Review the diff images to determine if these are "
                            "cosmetic (ignore) or functional (fix scripts/app).")

    report_lines.append("")

    report_path = run_dir / "report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
