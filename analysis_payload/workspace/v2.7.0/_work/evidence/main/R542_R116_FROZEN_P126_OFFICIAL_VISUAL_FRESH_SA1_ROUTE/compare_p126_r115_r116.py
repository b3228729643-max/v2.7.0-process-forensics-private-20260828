from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def save_crop(image: Image.Image, box: tuple[int, int, int, int], path: Path) -> None:
    image.crop(box).save(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    before = Image.open(args.before).convert("RGB")
    after = Image.open(args.after).convert("RGB")
    if before.size != after.size:
        raise SystemExit(f"render size mismatch: {before.size} != {after.size}")

    a = np.asarray(before, dtype=np.int16)
    b = np.asarray(after, dtype=np.int16)
    delta = np.max(np.abs(a - b), axis=2)
    changed = delta > 12
    ys, xs = np.nonzero(changed)
    if len(xs) == 0:
        raise SystemExit("no changed pixels")
    raw_bbox = (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
    pad = 40
    diff_bbox = (
        max(0, raw_bbox[0] - pad),
        max(0, raw_bbox[1] - pad),
        min(before.width, raw_bbox[2] + pad),
        min(before.height, raw_bbox[3] + pad),
    )

    figure_box = (680, 245, 1775, 1085)
    center_box = (845, 300, 1455, 750)
    legend_box = (900, 875, 1525, 1035)

    save_crop(before, figure_box, args.output_dir / "P126_R115_figure_caption_300dpi.png")
    save_crop(after, figure_box, args.output_dir / "P126_R116_figure_caption_300dpi.png")
    save_crop(after.convert("L"), figure_box, args.output_dir / "P126_R116_figure_caption_gray_300dpi.png")
    save_crop(after, center_box, args.output_dir / "P126_R116_labels_path_native_300dpi.png")
    save_crop(after, legend_box, args.output_dir / "P126_R116_legend_native_300dpi.png")

    center = after.crop(center_box)
    center.resize((center.width * 8, center.height * 8), Image.Resampling.NEAREST).save(
        args.output_dir / "P126_R116_labels_path_NN8x.png"
    )
    legend = after.crop(legend_box)
    legend.resize((legend.width * 8, legend.height * 8), Image.Resampling.NEAREST).save(
        args.output_dir / "P126_R116_legend_NN8x.png"
    )

    overlay = after.copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(raw_bbox, outline=(255, 0, 0), width=6)
    overlay.crop(diff_bbox).save(args.output_dir / "P126_R115_R116_changed_region_overlay_300dpi.png")

    heat = np.zeros_like(b, dtype=np.uint8)
    heat[:, :, :] = 255
    heat[changed] = np.array([220, 0, 0], dtype=np.uint8)
    Image.fromarray(heat, "RGB").crop(diff_bbox).save(
        args.output_dir / "P126_R115_R116_pixel_diff_mask.png"
    )

    inside_figure_count = int(
        changed[figure_box[1] : figure_box[3], figure_box[0] : figure_box[2]].sum()
    )
    report = {
        "schema_version": 1,
        "before_path": str(args.before.resolve()),
        "before_sha256": sha256(args.before),
        "after_path": str(args.after.resolve()),
        "after_sha256": sha256(args.after),
        "render_size_px": [before.width, before.height],
        "threshold_max_channel_delta_gt": 12,
        "changed_pixel_count": int(changed.sum()),
        "changed_pixel_fraction": float(changed.mean()),
        "changed_pixel_count_inside_figure_box": inside_figure_count,
        "changed_pixel_count_outside_figure_box": int(changed.sum()) - inside_figure_count,
        "raw_changed_bbox_xyxy": list(raw_bbox),
        "padded_changed_bbox_xyxy": list(diff_bbox),
        "figure_box_xyxy": list(figure_box),
        "center_roi_xyxy": list(center_box),
        "legend_roi_xyxy": list(legend_box),
        "result": "ROI_EXPORT_COMPLETE_MANUAL_ADJUDICATION_REQUIRED",
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
