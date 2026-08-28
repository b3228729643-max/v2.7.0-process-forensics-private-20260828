from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R11A_SA2_P4_COORDINATE_DIRECT_BUILD_R113_20260827")
PAGE = ROOT / "02_render" / "page_001_300dpi.png"
GRAPHIC_MANIFEST = ROOT / "03_objects" / "graphic_manifest.csv"
GLYPH_MANIFEST = ROOT / "03_objects" / "glyph_manifest.csv"
PAIR_LEDGER = ROOT / "06_ledgers" / "after_overlap_report.csv"
GRAPHIC_DETAIL = ROOT / "04_contacts" / "graphic_detail"
TARGET_DIR = ROOT / "05_pairs" / "p4_target_relations"
TARGET_PAIR_IDS = ["P01436", "P01437", "P01449", "P01519", "P01520", "P01532"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parse_bbox(value: str) -> tuple[int, int, int, int]:
    raw = json.loads(value)
    return tuple(int(number) for number in raw)


def load_mask(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L")) < 128


def overlay_for(page: Image.Image, bbox: tuple[int, int, int, int], mask: np.ndarray) -> tuple[Image.Image, Image.Image, Image.Image]:
    original = page.crop(bbox).convert("RGB")
    if mask.shape != (original.height, original.width):
        raise RuntimeError(f"mask/crop mismatch at {bbox}: {mask.shape} vs {(original.height, original.width)}")
    colored = np.asarray(original).copy()
    colored[mask] = [255, 0, 0]
    mask_image = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    return original, Image.fromarray(colored, mode="RGB"), mask_image


def fit(image: Image.Image, width: int, height: int) -> Image.Image:
    ratio = min(width / image.width, height / image.height, 1.0)
    return image.resize((max(1, round(image.width * ratio)), max(1, round(image.height * ratio))), Image.Resampling.LANCZOS)


def contact_sheet(items: list[tuple[str, Image.Image]], path: Path, *, cols: int, cell_w: int, cell_h: int) -> None:
    rows = math.ceil(len(items) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(items):
        col = index % cols
        row = index // cols
        x = col * cell_w
        y = row * cell_h
        draw.text((x + 5, y + 4), label, fill="black")
        fitted = fit(image, cell_w - 10, cell_h - 28)
        sheet.paste(fitted, (x + 5, y + 24))
    sheet.save(path)


def centered_local_bbox(bbox: tuple[int, int, int, int], mask: np.ndarray, image_size: tuple[int, int], radius: int = 28) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise RuntimeError(f"empty mask at {bbox}")
    center_x = int(np.median(xs)) + bbox[0]
    center_y = int(np.median(ys)) + bbox[1]
    x0 = max(0, center_x - radius)
    y0 = max(0, center_y - radius)
    x1 = min(image_size[0], center_x + radius)
    y1 = min(image_size[1], center_y + radius)
    return x0, y0, x1, y1


def make_graphic_evidence(page: Image.Image) -> None:
    GRAPHIC_DETAIL.mkdir(parents=True, exist_ok=False)
    rows = read_csv(GRAPHIC_MANIFEST)
    if len(rows) != 35:
        raise RuntimeError(f"graphic denominator drift: {len(rows)}")
    overview_items: list[tuple[str, Image.Image]] = []
    local_items: list[tuple[str, Image.Image]] = []
    manifest: list[dict[str, object]] = []
    for row in rows:
        element_id = row["element_id"]
        bbox = parse_bbox(row["mask_bbox_px"])
        mask_path = ROOT / row["mask_path"]
        mask = load_mask(mask_path)
        original, overlay, mask_image = overlay_for(page, bbox, mask)
        original_path = GRAPHIC_DETAIL / f"{element_id}_original_1x.png"
        overlay_path = GRAPHIC_DETAIL / f"{element_id}_overlay_1x.png"
        mask_output_path = GRAPHIC_DETAIL / f"{element_id}_mask_1x.png"
        original.save(original_path)
        overlay.save(overlay_path)
        mask_image.save(mask_output_path)
        triptych = Image.new("RGB", (original.width * 3 + 8, original.height), "white")
        triptych.paste(original, (0, 0))
        triptych.paste(overlay, (original.width + 4, 0))
        triptych.paste(mask_image, (2 * original.width + 8, 0))
        overview_items.append((f"{element_id} ORIGINAL / RED TARGET / MASK", triptych))

        local_bbox = centered_local_bbox(bbox, mask, page.size)
        lx0, ly0, lx1, ly1 = local_bbox
        local_original = page.crop(local_bbox).convert("RGB")
        local_mask = np.zeros((ly1 - ly0, lx1 - lx0), dtype=bool)
        ix0, iy0 = max(lx0, bbox[0]), max(ly0, bbox[1])
        ix1, iy1 = min(lx1, bbox[2]), min(ly1, bbox[3])
        local_mask[iy0 - ly0 : iy1 - ly0, ix0 - lx0 : ix1 - lx0] = mask[iy0 - bbox[1] : iy1 - bbox[1], ix0 - bbox[0] : ix1 - bbox[0]]
        local_color = np.asarray(local_original).copy()
        local_color[local_mask] = [255, 0, 0]
        local_overlay = Image.fromarray(local_color, mode="RGB").resize(
            (local_original.width * 8, local_original.height * 8), Image.Resampling.NEAREST
        )
        local_path = GRAPHIC_DETAIL / f"{element_id}_local_8x_nearest.png"
        local_overlay.save(local_path)
        local_items.append((f"{element_id} REPRESENTATIVE LOCAL NN8x", local_overlay))
        manifest.append(
            {
                "element_id": element_id,
                "mask_bbox_px": json.dumps(list(bbox)),
                "local_bbox_px": json.dumps(list(local_bbox)),
                "original_1x": original_path.relative_to(ROOT).as_posix(),
                "overlay_1x": overlay_path.relative_to(ROOT).as_posix(),
                "mask_1x": mask_output_path.relative_to(ROOT).as_posix(),
                "local_8x_nearest": local_path.relative_to(ROOT).as_posix(),
                "manual_fields_generated": 0,
            }
        )
    for start in range(0, len(overview_items), 8):
        number = start // 8 + 1
        contact_sheet(
            overview_items[start : start + 8],
            ROOT / "04_contacts" / f"graphic_contact_sheet_{number:02d}_1x.png",
            cols=2,
            cell_w=720,
            cell_h=260,
        )
        contact_sheet(
            local_items[start : start + 8],
            ROOT / "04_contacts" / f"graphic_contact_sheet_{number:02d}_8x_nearest.png",
            cols=2,
            cell_w=720,
            cell_h=520,
        )
    write_csv(ROOT / "04_contacts" / "graphic_contact_sheet_manifest.csv", manifest)


def object_map() -> dict[str, dict[str, object]]:
    objects: dict[str, dict[str, object]] = {}
    for manifest, mask_dir in ((GLYPH_MANIFEST, "glyph_masks"), (GRAPHIC_MANIFEST, "graphic_masks")):
        for row in read_csv(manifest):
            bbox = parse_bbox(row["mask_bbox_px"])
            mask_path = ROOT / "03_objects" / mask_dir / f"{row['element_id']}.png"
            objects[row["element_id"]] = {"bbox": bbox, "mask": load_mask(mask_path)}
    return objects


def make_target_pair_evidence(page: Image.Image) -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=False)
    pairs = {row["pair_id"]: row for row in read_csv(PAIR_LEDGER)}
    objects = object_map()
    output_rows: list[dict[str, object]] = []
    overview: list[tuple[str, Image.Image]] = []
    for pair_id in TARGET_PAIR_IDS:
        pair = pairs[pair_id]
        a = objects[pair["a_id"]]
        b = objects[pair["b_id"]]
        ax0, ay0, ax1, ay1 = a["bbox"]
        bx0, by0, bx1, by1 = b["bbox"]
        pad = 16
        x0, y0 = max(0, min(ax0, bx0) - pad), max(0, min(ay0, by0) - pad)
        x1, y1 = min(page.width, max(ax1, bx1) + pad), min(page.height, max(ay1, by1) + pad)
        original = page.crop((x0, y0, x1, y1)).convert("RGB")
        mask_a = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        mask_b = np.zeros_like(mask_a)
        mask_a[ay0 - y0 : ay1 - y0, ax0 - x0 : ax1 - x0] = a["mask"]
        mask_b[by0 - y0 : by1 - y0, bx0 - x0 : bx1 - x0] = b["mask"]
        overlap = mask_a & mask_b
        colored = np.asarray(original).copy()
        colored[mask_a] = [255, 0, 0]
        colored[mask_b] = [0, 80, 255]
        colored[overlap] = [255, 0, 255]
        overlay = Image.fromarray(colored, mode="RGB")
        original_path = TARGET_DIR / f"{pair_id}_original_1x.png"
        overlay_path = TARGET_DIR / f"{pair_id}_overlay_1x.png"
        overlay8_path = TARGET_DIR / f"{pair_id}_overlay_8x_nearest.png"
        intersection_path = TARGET_DIR / f"{pair_id}_intersection.png"
        original.save(original_path)
        overlay.save(overlay_path)
        overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(overlay8_path)
        Image.fromarray(np.where(overlap, 0, 255).astype(np.uint8), mode="L").save(intersection_path)
        overview.append((f"{pair_id} {pair['a_id']}--{pair['b_id']} clear={pair['clearance_px']}px", overlay8_path and Image.open(overlay8_path).convert("RGB")))
        output_rows.append(
            {
                "pair_id": pair_id,
                "a_id": pair["a_id"],
                "b_id": pair["b_id"],
                "mask_intersection_px": pair["mask_intersection_px"],
                "clearance_px": pair["clearance_px"],
                "machine_numeric_clearance_met": pair["machine_numeric_clearance_met"],
                "roi_px": json.dumps([x0, y0, x1, y1]),
                "original_1x": original_path.relative_to(ROOT).as_posix(),
                "overlay_1x": overlay_path.relative_to(ROOT).as_posix(),
                "overlay_8x_nearest": overlay8_path.relative_to(ROOT).as_posix(),
                "intersection": intersection_path.relative_to(ROOT).as_posix(),
                "manual_fields_generated": 0,
            }
        )
    contact_sheet(overview, TARGET_DIR / "p4_target_relation_contact_8x_nearest.png", cols=2, cell_w=760, cell_h=540)
    write_csv(TARGET_DIR / "p4_target_pair_manifest.csv", output_rows)


def main() -> None:
    page = Image.open(PAGE).convert("RGB")
    make_graphic_evidence(page)
    make_target_pair_evidence(page)
    print(json.dumps({"graphic_objects": 35, "target_pairs": TARGET_PAIR_IDS, "manual_fields_generated": 0}, ensure_ascii=True))


if __name__ == "__main__":
    main()
