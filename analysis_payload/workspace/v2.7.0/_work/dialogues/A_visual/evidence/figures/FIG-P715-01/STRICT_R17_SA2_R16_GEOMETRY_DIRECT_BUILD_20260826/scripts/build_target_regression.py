from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


BUILD_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R17_SA2_R16_GEOMETRY_DIRECT_BUILD_20260826")
ROOT = BUILD_ROOT / "evidence_v3"
OLD_INDEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R15_SA1_FRESH_ISOLATED_R106_20260826\machine\failure_roi_index.csv")


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_mask(obj: dict) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    subdir = "glyphs" if obj["kind"] == "TEXT_GLYPH" else "drawings"
    mask = np.array(Image.open(ROOT / "masks" / subdir / obj["safe_filename"]).convert("L")) >= 128
    return mask, tuple(int(value) for value in obj["bbox_px"])


def localize(mask: np.ndarray, box: tuple[int, int, int, int], roi: tuple[int, int, int, int]) -> np.ndarray:
    result = np.zeros((roi[3] - roi[1], roi[2] - roi[0]), dtype=bool)
    x0, y0 = max(box[0], roi[0]), max(box[1], roi[1])
    x1, y1 = min(box[2], roi[2]), min(box[3], roi[3])
    if x1 > x0 and y1 > y0:
        result[y0-roi[1]:y1-roi[1], x0-roi[0]:x1-roi[0]] = mask[y0-box[1]:y1-box[1], x0-box[0]:x1-box[0]]
    return result


def main() -> None:
    objects = {item["element_id"]: item for item in json.loads((ROOT / "machine/object_manifest.json").read_text(encoding="utf-8"))}
    current = {row["pair_id"]: row for row in read_csv(ROOT / "machine/all_unordered_pairs.csv")}
    old = read_csv(OLD_INDEX)
    page = np.array(Image.open(ROOT / "views/full_page_300dpi_native.png").convert("RGB"))
    output_root = ROOT / "target_regression_rois"
    output_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    contact_cells: list[tuple[str, Image.Image]] = []
    for prior in old:
        pair = current[prior["pair_id"]]
        if (pair["object_a"], pair["object_b"]) != (prior["object_a"], prior["object_b"]):
            raise RuntimeError(f"pair identity drift: {prior['pair_id']}")
        object_a, object_b = objects[pair["object_a"]], objects[pair["object_b"]]
        mask_a, box_a = load_mask(object_a)
        mask_b, box_b = load_mask(object_b)
        x0 = max(0, min(box_a[0], box_b[0]) - 35)
        y0 = max(0, min(box_a[1], box_b[1]) - 35)
        x1 = min(page.shape[1], max(box_a[2], box_b[2]) + 35)
        y1 = min(page.shape[0], max(box_a[3], box_b[3]) + 35)
        roi = (x0, y0, x1, y1)
        original = page[y0:y1, x0:x1].copy()
        local_a, local_b = localize(mask_a, box_a, roi), localize(mask_b, box_b, roi)
        intersection = local_a & local_b
        overlay = original.copy()
        overlay[local_a] = (255, 0, 0)
        overlay[local_b] = (0, 80, 255)
        overlay[intersection] = (255, 215, 0)
        folder = output_root / pair["pair_id"]
        folder.mkdir(parents=True, exist_ok=True)
        Image.fromarray(original).save(folder / "original_native1x.png")
        Image.fromarray(overlay).save(folder / "overlay_native1x.png")
        Image.fromarray(overlay).resize((overlay.shape[1] * 8, overlay.shape[0] * 8), Image.Resampling.NEAREST).save(folder / "overlay_8x_nearest.png")
        contact_cells.append((pair["pair_id"], Image.fromarray(overlay)))
        threshold = float(pair["protocol_min_clearance_px"])
        new_gap = float(pair["white_gap_px"])
        rows.append({
            "pair_id": pair["pair_id"],
            "object_a": pair["object_a"],
            "object_b": pair["object_b"],
            "relation_category": pair["relation_category"],
            "old_raw_intersection_px": prior["raw_intersection_px"],
            "old_white_gap_px": prior["white_gap_px"],
            "new_raw_intersection_px": pair["raw_intersection_px"],
            "new_white_gap_px": pair["white_gap_px"],
            "protocol_min_clearance_px": pair["protocol_min_clearance_px"],
            "mechanical_status": "PASS" if int(pair["raw_intersection_px"]) == 0 and new_gap >= threshold else "REVIEW",
            "roi_native1x": str(Path("target_regression_rois") / pair["pair_id"] / "overlay_native1x.png"),
            "roi_8x": str(Path("target_regression_rois") / pair["pair_id"] / "overlay_8x_nearest.png"),
        })
    write_csv(ROOT / "machine/accepted_failure_regression.csv", rows)
    cell_w, cell_h, columns = 520, 300, 3
    contact_sheet = Image.new("RGB", (cell_w * columns, cell_h * 7), "white")
    draw = ImageDraw.Draw(contact_sheet)
    font = ImageFont.load_default()
    for index, (pair_id, roi_image) in enumerate(contact_cells):
        col, row = index % columns, index // columns
        x, y = col * cell_w, row * cell_h
        draw.text((x + 6, y + 5), pair_id, fill="black", font=font)
        shown = roi_image.copy()
        shown.thumbnail((cell_w - 12, cell_h - 28), Image.Resampling.NEAREST)
        contact_sheet.paste(shown, (x + 6, y + 24))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(180, 180, 180), width=1)
    contact_sheet.save(ROOT / "target_regression_contact_sheet.png")
    result = {
        "prior_failure_denominator": len(rows),
        "pair_identity_drift_count": 0,
        "mechanical_pass_count": sum(row["mechanical_status"] == "PASS" for row in rows),
        "mechanical_review_count": sum(row["mechanical_status"] == "REVIEW" for row in rows),
        "review_pair_ids": [row["pair_id"] for row in rows if row["mechanical_status"] == "REVIEW"],
        "native1x_count": len(rows),
        "nearest_8x_count": len(rows),
        "manual_fields_generated": False,
    }
    (ROOT / "machine/accepted_failure_regression_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
