from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--visual-dir", required=True, type=Path)
    args = parser.parse_args()

    before = Image.open(args.before).convert("RGB")
    after = Image.open(args.after).convert("RGB")
    if before.size != after.size:
        raise SystemExit(f"size mismatch: {before.size} != {after.size}")

    difference = ImageChops.difference(before, after)
    bbox = difference.getbbox()
    changed = sum(1 for pixel in difference.getdata() if pixel != (0, 0, 0))

    args.visual_dir.mkdir(parents=True, exist_ok=True)
    if bbox:
        left, top, right, bottom = bbox
        expanded = (
            max(0, left - 80),
            max(0, top - 80),
            min(after.width, right + 80),
            min(after.height, bottom + 80),
        )
        target = after.crop(expanded)
        target.save(args.visual_dir / "P109_R115_domain_label_diff_bbox_native300.png")
        target.resize(
            (target.width * 8, target.height * 8),
            resample=Image.Resampling.NEAREST,
        ).save(args.visual_dir / "P109_R115_domain_label_diff_bbox_nearest8x.png")

        mask = difference.convert("L").point(lambda value: 255 if value else 0)
        overlay = after.copy()
        red = Image.new("RGB", after.size, (255, 0, 0))
        overlay.paste(red, mask=mask)
        overlay.crop(expanded).save(
            args.visual_dir / "P109_R114_to_R115_changed_pixels_overlay.png"
        )
    else:
        expanded = None

    result = {
        "before": str(args.before),
        "after": str(args.after),
        "image_size_px": list(after.size),
        "changed_pixels": changed,
        "changed_bbox_xyxy": list(bbox) if bbox else None,
        "expanded_review_bbox_xyxy": list(expanded) if expanded else None,
        "outside_changed_bbox_pixels": 0,
        "result": "PASS" if bbox and changed > 0 else "FAIL",
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
