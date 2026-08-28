from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R4_SA2_R3_COORDINATE_DIRECT_BUILD_R110_20260827")
PDF = ROOT / "build" / "v260_FIG-P033-01_standalone.pdf"
PNG = ROOT / "render_r4_300dpi.png"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C02\fig_v1_c02_projection.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P033-01_standalone.tex")
MACHINE = ROOT / "machine"
SHEETS = ROOT / "sheets"
ROIS = ROOT / "rois"
SCALE = 300.0 / 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rect_list(rect) -> list[float]:
    return [float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])]


def px_rect(rect: list[float]) -> list[int]:
    return [
        math.floor(rect[0] * SCALE),
        math.floor(rect[1] * SCALE),
        math.ceil(rect[2] * SCALE),
        math.ceil(rect[3] * SCALE),
    ]


def rect_metrics(a: list[int], b: list[int]) -> tuple[int, int, float, int]:
    ox = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    oy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    clearance = math.hypot(dx, dy)
    return ox, oy, clearance, ox * oy


def crop_with_box(image: Image.Image, box: list[int], padding: int = 14) -> Image.Image:
    x0 = max(0, box[0] - padding)
    y0 = max(0, box[1] - padding)
    x1 = min(image.width, box[2] + padding)
    y1 = min(image.height, box[3] + padding)
    return image.crop((x0, y0, x1, y1))


def contact_sheet(image: Image.Image, objects: list[dict], output: Path, columns: int, cell_w: int, cell_h: int) -> None:
    rows = math.ceil(len(objects) / columns)
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for idx, obj in enumerate(objects):
        col, row = idx % columns, idx // columns
        x, y = col * cell_w, row * cell_h
        crop = crop_with_box(image, obj["bbox_px"], padding=18)
        max_w, max_h = cell_w - 12, cell_h - 34
        ratio = min(max_w / max(crop.width, 1), max_h / max(crop.height, 1), 5.0)
        resized = crop.resize((max(1, int(crop.width * ratio)), max(1, int(crop.height * ratio))), Image.Resampling.NEAREST)
        sheet.paste(resized, (x + (cell_w - resized.width) // 2, y + 24))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline="#a0a0a0", width=1)
        draw.text((x + 4, y + 4), obj["sheet_label"], fill="black", font=font)
    sheet.save(output)


def critical_sheet(image: Image.Image, pair_rows: list[dict], object_map: dict[str, dict], output: Path) -> None:
    columns, cell_w, cell_h = 4, 500, 300
    rows = math.ceil(len(pair_rows) / columns) if pair_rows else 1
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
    font = ImageFont.load_default()
    for idx, pair in enumerate(pair_rows):
        col, row = idx % columns, idx // columns
        x0, y0 = col * cell_w, row * cell_h
        a, b = object_map[pair["object_a"]], object_map[pair["object_b"]]
        union = [
            min(a["bbox_px"][0], b["bbox_px"][0]),
            min(a["bbox_px"][1], b["bbox_px"][1]),
            max(a["bbox_px"][2], b["bbox_px"][2]),
            max(a["bbox_px"][3], b["bbox_px"][3]),
        ]
        pad = 24
        crop_box = [max(0, union[0] - pad), max(0, union[1] - pad), min(image.width, union[2] + pad), min(image.height, union[3] + pad)]
        crop = image.crop(tuple(crop_box)).convert("RGB")
        cdraw = ImageDraw.Draw(crop)
        for obj, color in ((a, "red"), (b, "blue")):
            bx = obj["bbox_px"]
            cdraw.rectangle((bx[0] - crop_box[0], bx[1] - crop_box[1], bx[2] - crop_box[0], bx[3] - crop_box[1]), outline=color, width=2)
        max_w, max_h = cell_w - 12, cell_h - 46
        ratio = min(max_w / max(crop.width, 1), max_h / max(crop.height, 1), 4.0)
        resized = crop.resize((max(1, int(crop.width * ratio)), max(1, int(crop.height * ratio))), Image.Resampling.NEAREST)
        sheet.paste(resized, (x0 + (cell_w - resized.width) // 2, y0 + 40))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((x0, y0, x0 + cell_w - 1, y0 + cell_h - 1), outline="#a0a0a0", width=1)
        label = f"{pair['pair_id']} {pair['object_a']}:{pair['object_b']} gap={pair['bbox_clearance_px']}"
        draw.text((x0 + 4, y0 + 4), label, fill="black", font=font)
    sheet.save(output)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    for directory in (MACHINE, SHEETS, ROIS):
        directory.mkdir(exist_ok=True)

    image = Image.open(PNG).convert("RGB")
    doc = fitz.open(PDF)
    page = doc[0]
    objects: list[dict] = []
    glyph_rows: list[dict] = []
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    value = char.get("c", "")
                    if not value.strip():
                        continue
                    ident = f"G{len(glyph_rows) + 1:04d}"
                    bbox_pt = rect_list(char["bbox"])
                    bbox_px = px_rect(bbox_pt)
                    row = {
                        "object_id": ident,
                        "kind": "glyph",
                        "value": value,
                        "codepoint": "+".join(f"U+{ord(c):04X}" for c in value),
                        "font": span.get("font", ""),
                        "font_size_pt": round(float(span.get("size", 0.0)), 6),
                        "bbox_pt": json.dumps([round(v, 6) for v in bbox_pt], separators=(",", ":")),
                        "bbox_px": json.dumps(bbox_px, separators=(",", ":")),
                        "clip_fail": int(bbox_pt[0] < 0 or bbox_pt[1] < 0 or bbox_pt[2] > page.rect.width or bbox_pt[3] > page.rect.height),
                        "empty_bbox_fail": int(bbox_px[2] <= bbox_px[0] or bbox_px[3] <= bbox_px[1]),
                    }
                    glyph_rows.append(row)
                    objects.append({
                        "id": ident,
                        "kind": "glyph",
                        "bbox_pt": bbox_pt,
                        "bbox_px": bbox_px,
                        "sheet_label": f"{ident} {row['codepoint']}",
                    })

    drawing_rows: list[dict] = []
    for drawing in page.get_drawings():
        ident = f"D{len(drawing_rows) + 1:04d}"
        bbox_pt = rect_list(drawing["rect"])
        bbox_px = px_rect(bbox_pt)
        row = {
            "object_id": ident,
            "kind": "drawing",
            "drawing_type": drawing.get("type", ""),
            "item_count": len(drawing.get("items", [])),
            "stroke_width_pt": "" if drawing.get("width") is None else round(float(drawing["width"]), 6),
            "stroke_color": json.dumps(drawing.get("color"), separators=(",", ":")),
            "fill_color": json.dumps(drawing.get("fill"), separators=(",", ":")),
            "bbox_pt": json.dumps([round(v, 6) for v in bbox_pt], separators=(",", ":")),
            "bbox_px": json.dumps(bbox_px, separators=(",", ":")),
            "clip_fail": int(bbox_pt[0] < 0 or bbox_pt[1] < 0 or bbox_pt[2] > page.rect.width or bbox_pt[3] > page.rect.height),
            "empty_bbox_fail": int(bbox_px[2] <= bbox_px[0] or bbox_px[3] <= bbox_px[1]),
        }
        drawing_rows.append(row)
        objects.append({
            "id": ident,
            "kind": "drawing",
            "bbox_pt": bbox_pt,
            "bbox_px": bbox_px,
            "sheet_label": f"{ident} type={row['drawing_type']} items={row['item_count']}",
        })

    pair_rows: list[dict] = []
    for ordinal, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        ox, oy, clearance, overlap_area = rect_metrics(a["bbox_px"], b["bbox_px"])
        critical = int(overlap_area > 0 or clearance < 3.0 or {a["id"], b["id"]} == {"G0001", "D0003"})
        pair_rows.append({
            "pair_id": f"P{ordinal:05d}",
            "object_a": a["id"],
            "object_b": b["id"],
            "kind_a": a["kind"],
            "kind_b": b["kind"],
            "bbox_overlap_width_px": ox,
            "bbox_overlap_height_px": oy,
            "bbox_overlap_area_px2": overlap_area,
            "bbox_clearance_px": round(clearance, 6),
            "critical_candidate": critical,
        })
    critical_rows = [row for row in pair_rows if row["critical_candidate"]]

    object_map = {obj["id"]: obj for obj in objects}
    target = dict(next(row for row in pair_rows if {row["object_a"], row["object_b"]} == {"G0001", "D0003"}))
    target["semantic_relation"] = "subspace-label-first-glyph versus lower plane boundary"
    target["native_bbox_disjoint_pass"] = int(target["bbox_clearance_px"] > 0)

    content_box = [
        min(obj["bbox_px"][0] for obj in objects),
        min(obj["bbox_px"][1] for obj in objects),
        max(obj["bbox_px"][2] for obj in objects),
        max(obj["bbox_px"][3] for obj in objects),
    ]
    figure_crop = crop_with_box(image, content_box, padding=80)
    figure_crop.save(ROIS / "figure_crop_native300dpi.png")
    figure_crop.convert("L").save(ROIS / "figure_crop_grayscale_native300dpi.png")

    glyph_obj = object_map["G0001"]
    lower_edge_obj = object_map["D0003"]
    gx = glyph_obj["bbox_px"]
    target_box = [
        max(0, gx[0] - 80),
        max(0, min(gx[1], lower_edge_obj["bbox_px"][3]) - 90),
        min(image.width, gx[2] + 120),
        min(image.height, gx[3] + 90),
    ]
    target_crop = image.crop(tuple(target_box)).convert("RGB")
    tdraw = ImageDraw.Draw(target_crop)
    for obj, color in ((glyph_obj, "red"), (lower_edge_obj, "blue")):
        bx = obj["bbox_px"]
        tdraw.rectangle((bx[0] - target_box[0], bx[1] - target_box[1], bx[2] - target_box[0], bx[3] - target_box[1]), outline=color, width=2)
    target_crop.save(ROIS / "target_G0001_D0003_native1x.png")
    target_crop.resize((target_crop.width * 8, target_crop.height * 8), Image.Resampling.NEAREST).save(ROIS / "target_G0001_D0003_overlay8x.png")

    contact_sheet(image, [object_map[row["object_id"]] for row in glyph_rows], SHEETS / "glyph_contact_sheet.png", 5, 260, 170)
    contact_sheet(image, [object_map[row["object_id"]] for row in drawing_rows], SHEETS / "drawing_contact_sheet.png", 3, 440, 280)
    critical_sheet(image, critical_rows, object_map, SHEETS / "critical_pair_contact_sheet.png")

    write_csv(MACHINE / "glyph_objects.csv", glyph_rows, list(glyph_rows[0].keys()))
    write_csv(MACHINE / "drawing_objects.csv", drawing_rows, list(drawing_rows[0].keys()))
    write_csv(MACHINE / "all_unordered_pairs.csv", pair_rows, list(pair_rows[0].keys()))
    write_csv(MACHINE / "critical_candidates.csv", critical_rows, list(pair_rows[0].keys()))
    (MACHINE / "target_pair_G0001_D0003.json").write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "uid": "FIG-P033-01",
        "round": "STRICT_R4_SA2_R3_COORDINATE_DIRECT_BUILD_R110_20260827",
        "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
        "source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
        "wrapper": {"path": str(WRAPPER), "bytes": WRAPPER.stat().st_size, "sha256": sha256(WRAPPER)},
        "page_count": doc.page_count,
        "page_width_pt": page.rect.width,
        "page_height_pt": page.rect.height,
        "render_width_px": image.width,
        "render_height_px": image.height,
        "glyph_count": len(glyph_rows),
        "drawing_count": len(drawing_rows),
        "object_count": len(objects),
        "pair_count": len(pair_rows),
        "expected_pair_count": len(objects) * (len(objects) - 1) // 2,
        "critical_candidate_count": len(critical_rows),
        "clip_failures": sum(row["clip_fail"] for row in glyph_rows + drawing_rows),
        "empty_bbox_failures": sum(row["empty_bbox_fail"] for row in glyph_rows + drawing_rows),
        "replacement_character_count": sum(1 for row in glyph_rows if row["codepoint"] == "U+FFFD"),
        "target_pair": target,
        "manual_fields_generated_by_script": 0,
    }
    (MACHINE / "MACHINE_RESULT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == "__main__":
    main()
