#!/usr/bin/env python3
"""Diff explore vs script screenshots and write diff images + report.

Usage:
  python3 scripts/diff_screenshots.py

Assumes filenames like:
  screenshots/explore-01-home.png
  screenshots/script-01-home.png
"""

import math
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "screenshots"
DIFFS_ROOT = SCREENSHOTS / "diffs"

PAIR_RE = re.compile(r"^(explore|script)-(?P<key>.+)\.png$")


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


def build_pairs():
    pairs = {}
    for path in SCREENSHOTS.glob("*.png"):
        match = PAIR_RE.match(path.name)
        if not match:
            continue
        key = match.group("key")
        pairs.setdefault(key, {})[match.group(1)] = path
    return pairs


def main():
    if not SCREENSHOTS.exists():
        raise SystemExit("screenshots/ folder not found")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    diff_dir = DIFFS_ROOT / timestamp
    diff_dir.mkdir(parents=True, exist_ok=True)

    pairs = build_pairs()
    if not pairs:
        raise SystemExit("No explore/script screenshot pairs found.")

    report_lines = ["# Screenshot Diff Report", ""]

    for key, items in sorted(pairs.items()):
        explore_path = items.get("explore")
        script_path = items.get("script")
        if not explore_path or not script_path:
            continue

        explore_img = load_image(explore_path)
        script_img = load_image(script_path)

        size_note = ""
        if explore_img.size != script_img.size:
            size_note = f"(size mismatch: explore {explore_img.size} vs script {script_img.size})"
            explore_img, script_img = pad_to_same_size(explore_img, script_img)

        diff = ImageChops.difference(explore_img, script_img)
        stat = ImageStat.Stat(diff)
        diff_rms = rms(stat.rms)

        diff_path = diff_dir / f"diff-{key}.png"
        diff.save(diff_path)

        report_lines.append(f"## {key}")
        report_lines.append("")
        report_lines.append(f"- explore: {explore_path.name}")
        report_lines.append(f"- script: {script_path.name}")
        report_lines.append(f"- diff: {diff_path.name}")
        report_lines.append(f"- rms: {diff_rms:.2f} {size_note}".rstrip())
        report_lines.append("")

    report_path = diff_dir / "report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
