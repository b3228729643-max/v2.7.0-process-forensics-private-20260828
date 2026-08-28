from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "rendered" / "page_069_300dpi.png"
MANIFEST = ROOT / "denominator" / "object_manifest.csv"
OUTPUT = ROOT / "mechanical" / "selected_clearances.csv"
PAGE_WIDTH_PT = 595.276
PAGE_HEIGHT_PT = 841.89


def main() -> None:
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = {row["OBJECT_ID"]: row for row in csv.DictReader(stream)}
    page = np.asarray(Image.open(PAGE).convert("RGB"))
    sy = page.shape[0] / PAGE_HEIGHT_PT
    sx = page.shape[1] / PAGE_WIDTH_PT

    def px_box(object_id: str) -> tuple[int, int, int, int]:
        row = rows[object_id]
        return (
            math.floor(float(row["BBOX_X0_PT"]) * sx),
            math.floor(float(row["BBOX_TOP_PT"]) * sy),
            math.ceil(float(row["BBOX_X1_PT"]) * sx),
            math.ceil(float(row["BBOX_BOTTOM_PT"]) * sy),
        )

    def text_to_blue(object_id: str, margin: int = 24) -> int:
        x0, y0, x1, y1 = px_box(object_id)
        lx0 = max(0, x0 - margin)
        ly0 = max(0, y0 - margin)
        lx1 = min(page.shape[1], x1 + margin)
        ly1 = min(page.shape[0], y1 + margin)
        local = page[ly0:ly1, lx0:lx1]
        r = local[:, :, 0].astype(int)
        g = local[:, :, 1].astype(int)
        b = local[:, :, 2].astype(int)
        blue = (b - r >= 25) & (b - g >= 12) & (r < 180)
        neutral_dark = (np.max(local, axis=2) - np.min(local, axis=2) <= 28) & (np.min(local, axis=2) < 205)
        text_box_mask = np.zeros(neutral_dark.shape, dtype=bool)
        text_box_mask[y0 - ly0 : y1 - ly0, x0 - lx0 : x1 - lx0] = True
        text = neutral_dark & text_box_mask
        if not blue.any() or not text.any():
            raise RuntimeError(f"missing mask for {object_id}")
        blue_points = np.argwhere(blue).astype(float)
        text_points = np.argwhere(text).astype(float)
        minimum_squared = float("inf")
        for start in range(0, len(text_points), 128):
            chunk = text_points[start : start + 128]
            delta = chunk[:, None, :] - blue_points[None, :, :]
            minimum_squared = min(
                minimum_squared,
                float(np.min(np.sum(delta * delta, axis=2))),
            )
        return max(0, int(math.floor(math.sqrt(minimum_squared) - 1.0)))

    def text_to_vertical_guide(object_id: str, guide_x_pt: float, half_width_px: int = 5) -> int:
        x0, y0, x1, y1 = px_box(object_id)
        local = page[y0:y1, x0:x1]
        neutral_dark = (
            (np.max(local, axis=2) - np.min(local, axis=2) <= 35)
            & (np.min(local, axis=2) < 215)
        )
        guide_x = guide_x_pt * sx
        xs = np.nonzero(neutral_dark)[1] + x0
        # Exclude the detected guide's own center band before measuring glyph ink.
        xs = xs[np.abs(xs - guide_x) > half_width_px + 1]
        if xs.size == 0:
            raise RuntimeError(f"missing text pixels for {object_id}")
        return max(0, int(math.floor(float(np.min(np.abs(xs - guide_x))) - half_width_px)))

    measurements = [
        ("T06-G21", "annotation ink to t=1 guide", text_to_vertical_guide("T06", 191.870)),
        ("T21-G46", "annotation ink to t=4 guide", text_to_vertical_guide("T21", 434.599)),
        ("T07-blue", "p_1 ink to blue CDF geometry", text_to_blue("T07")),
        ("T08-blue", "p_2 ink to blue CDF geometry", text_to_blue("T08")),
        ("T09-blue", "p_3 ink to blue CDF geometry", text_to_blue("T09")),
        ("T10-blue", "p_4 ink to blue CDF geometry", text_to_blue("T10")),
    ]
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["RELATION_ID", "MEASUREMENT", "CLEARANCE_PX", "SOURCE_DPI", "METHOD"])
        for relation_id, measurement, clearance in measurements:
            writer.writerow(
                [
                    relation_id,
                    measurement,
                    clearance,
                    300,
                    "direct-render color/neutral mask with native-pixel Euclidean or centerline distance",
                ]
            )


if __name__ == "__main__":
    main()
