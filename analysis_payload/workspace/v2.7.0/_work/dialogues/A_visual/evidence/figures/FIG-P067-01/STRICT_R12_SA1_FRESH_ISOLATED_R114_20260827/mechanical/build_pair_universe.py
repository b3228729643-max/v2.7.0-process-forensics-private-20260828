from __future__ import annotations

import csv
import json
import math
from itertools import combinations
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "denominator" / "object_manifest.csv"
PAIR_OUTPUT = ROOT / "denominator" / "all_unordered_pairs.csv"
TEXT_OUTPUT = ROOT / "mechanical" / "text_pixel_measurements.csv"
SUMMARY_OUTPUT = ROOT / "mechanical" / "pair_universe_summary.json"
PAGE_IMAGE = ROOT / "rendered" / "page_069_300dpi.png"
PAGE_WIDTH_PT = 595.276
PAGE_HEIGHT_PT = 841.89


def load_manifest() -> list[dict[str, str]]:
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    ids = [row["OBJECT_ID"] for row in rows]
    if len(rows) != 69 or len(ids) != len(set(ids)):
        raise RuntimeError(f"frozen denominator mismatch: rows={len(rows)} unique={len(set(ids))}")
    return rows


def bbox(row: dict[str, str]) -> tuple[float, float, float, float]:
    return tuple(
        float(row[key])
        for key in ("BBOX_X0_PT", "BBOX_TOP_PT", "BBOX_X1_PT", "BBOX_BOTTOM_PT")
    )


def pair_geometry(a: dict[str, str], b: dict[str, str]) -> dict[str, float | str]:
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    overlap_x = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    overlap_y = max(0.0, min(ay1, by1) - max(ay0, by0))
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    gap = math.hypot(dx, dy)
    return {
        "BBOX_GAP_PT": gap,
        "BBOX_OVERLAP_X_PT": overlap_x,
        "BBOX_OVERLAP_Y_PT": overlap_y,
        "BBOX_INTERSECTION_AREA_PT2": overlap_x * overlap_y,
        "BBOX_RELATION_MECHANICAL": "BBOX_TOUCH_OR_OVERLAP" if gap == 0 else "DISJOINT",
    }


def composite_foreground_in_intersection(
    page: Image.Image,
    a: dict[str, str],
    b: dict[str, str],
) -> int:
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    x0 = max(ax0, bx0)
    y0 = max(ay0, by0)
    x1 = min(ax1, bx1)
    y1 = min(ay1, by1)
    if x0 > x1 or y0 > y1:
        return 0
    # A PDF vector line commonly has a zero-width/zero-height extracted bbox.
    # Expand only that degenerate intersection by 0.5 pt each side so the
    # direct-render raster pixels on the centerline are sampled.
    if x0 == x1:
        x0 -= 0.5
        x1 += 0.5
    if y0 == y1:
        y0 -= 0.5
        y1 += 0.5
    sx = page.width / PAGE_WIDTH_PT
    sy = page.height / PAGE_HEIGHT_PT
    px0 = max(0, math.floor(x0 * sx))
    py0 = max(0, math.floor(y0 * sy))
    px1 = min(page.width, math.ceil(x1 * sx))
    py1 = min(page.height, math.ceil(y1 * sy))
    crop = page.crop((px0, py0, px1, py1))
    return sum(
        1
        for r, g, b in crop.getdata()
        if 255 - min(r, g, b) >= 20
    )


def write_pairs(rows: list[dict[str, str]]) -> tuple[int, int, int]:
    fields = [
        "PAIR_ID",
        "OBJECT_A",
        "OBJECT_B",
        "A_PANEL",
        "B_PANEL",
        "A_CATEGORY",
        "B_CATEGORY",
        "BBOX_GAP_PT",
        "BBOX_OVERLAP_X_PT",
        "BBOX_OVERLAP_Y_PT",
        "BBOX_INTERSECTION_AREA_PT2",
        "BBOX_RELATION_MECHANICAL",
        "COMPOSITE_FOREGROUND_IN_BBOX_INTERSECTION_PX",
    ]
    touch_count = 0
    composite_foreground_total = 0
    with Image.open(PAGE_IMAGE).convert("RGB") as page:
        with PAIR_OUTPUT.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for index, (a, b) in enumerate(combinations(rows, 2), start=1):
                geometry = pair_geometry(a, b)
                foreground_count = 0
                if geometry["BBOX_RELATION_MECHANICAL"] == "BBOX_TOUCH_OR_OVERLAP":
                    touch_count += 1
                    foreground_count = composite_foreground_in_intersection(page, a, b)
                    composite_foreground_total += foreground_count
                writer.writerow(
                    {
                        "PAIR_ID": f"P{index:04d}",
                        "OBJECT_A": a["OBJECT_ID"],
                        "OBJECT_B": b["OBJECT_ID"],
                        "A_PANEL": a["PANEL"],
                        "B_PANEL": b["PANEL"],
                        "A_CATEGORY": a["CATEGORY"],
                        "B_CATEGORY": b["CATEGORY"],
                        "BBOX_GAP_PT": f"{geometry['BBOX_GAP_PT']:.3f}",
                        "BBOX_OVERLAP_X_PT": f"{geometry['BBOX_OVERLAP_X_PT']:.3f}",
                        "BBOX_OVERLAP_Y_PT": f"{geometry['BBOX_OVERLAP_Y_PT']:.3f}",
                        "BBOX_INTERSECTION_AREA_PT2": f"{geometry['BBOX_INTERSECTION_AREA_PT2']:.3f}",
                        "BBOX_RELATION_MECHANICAL": geometry["BBOX_RELATION_MECHANICAL"],
                        "COMPOSITE_FOREGROUND_IN_BBOX_INTERSECTION_PX": foreground_count,
                    }
                )
    return math.comb(len(rows), 2), touch_count, composite_foreground_total


def script_class(object_id: str) -> str:
    if object_id in {"T01", "T07", "T08", "T09", "T10", "T11", "T20"}:
        return "MATH"
    if object_id in {"T02", "T03", "T04", "T05", "T12", "T13", "T14", "T15", "T16", "T17", "T18", "T19"}:
        return "DIGIT"
    if object_id == "T21":
        return "CJK_MATH_MIXED"
    return "CJK"


def write_text_measurements(rows: list[dict[str, str]]) -> int:
    fields = [
        "OBJECT_ID",
        "PANEL",
        "ROLE",
        "SCRIPT_CLASS",
        "BBOX_X0_PX",
        "BBOX_Y0_PX",
        "BBOX_X1_PX",
        "BBOX_Y1_PX",
        "H_INK_PX",
        "W_INK_PX",
        "FOREGROUND_PIXEL_COUNT",
        "THRESHOLD_FROM_WHITE",
    ]
    with Image.open(PAGE_IMAGE).convert("RGB") as page:
        sx = page.width / PAGE_WIDTH_PT
        sy = page.height / PAGE_HEIGHT_PT
        output_rows = []
        for row in rows:
            if row["CATEGORY"] != "TEXT":
                continue
            x0, top, x1, bottom = bbox(row)
            px0 = max(0, math.floor(x0 * sx))
            py0 = max(0, math.floor(top * sy))
            px1 = min(page.width, math.ceil(x1 * sx))
            py1 = min(page.height, math.ceil(bottom * sy))
            crop = page.crop((px0, py0, px1, py1))
            foreground = []
            for y in range(crop.height):
                for x in range(crop.width):
                    r, g, b = crop.getpixel((x, y))
                    if 255 - min(r, g, b) >= 20:
                        foreground.append((x, y))
            if foreground:
                xs = [point[0] for point in foreground]
                ys = [point[1] for point in foreground]
                width = max(xs) - min(xs) + 1
                height = max(ys) - min(ys) + 1
            else:
                width = 0
                height = 0
            output_rows.append(
                {
                    "OBJECT_ID": row["OBJECT_ID"],
                    "PANEL": row["PANEL"],
                    "ROLE": row["ROLE"],
                    "SCRIPT_CLASS": script_class(row["OBJECT_ID"]),
                    "BBOX_X0_PX": px0,
                    "BBOX_Y0_PX": py0,
                    "BBOX_X1_PX": px1,
                    "BBOX_Y1_PX": py1,
                    "H_INK_PX": height,
                    "W_INK_PX": width,
                    "FOREGROUND_PIXEL_COUNT": len(foreground),
                    "THRESHOLD_FROM_WHITE": 20,
                }
            )
    with TEXT_OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)
    return len(output_rows)


def main() -> None:
    rows = load_manifest()
    pair_count, touch_count, composite_foreground_total = write_pairs(rows)
    text_count = write_text_measurements(rows)
    summary = {
        "object_count": len(rows),
        "text_object_count": text_count,
        "graphic_object_count": len(rows) - text_count,
        "unordered_pair_count": pair_count,
        "expected_unordered_pair_count": 2346,
        "mechanical_bbox_touch_or_overlap_count": touch_count,
        "mechanical_disjoint_count": pair_count - touch_count,
        "composite_foreground_in_bbox_intersections_px": composite_foreground_total,
        "manual_fields_emitted": False,
    }
    if pair_count != 2346:
        raise RuntimeError(f"pair universe mismatch: {pair_count}")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
