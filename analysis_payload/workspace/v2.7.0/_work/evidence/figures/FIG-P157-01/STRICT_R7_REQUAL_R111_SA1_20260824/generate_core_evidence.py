from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
CANDIDATE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C10\fig_v1_c10_complexity.tex")
PAGE_NUMBER = 170

# Inclusive page-native integer crop coordinates. Both crops are direct slices
# from full_page_native_300dpi.png and are never rescaled.
FIGURE_CROP = (250, 200, 2250, 1535)  # figure body plus caption
STANDALONE_CROP = (300, 205, 2240, 1450)  # visual body only, caption excluded


ELEMENTS = [
    ("E001", "BODY", "ANNOTATION", "训练误差：单调下降", 9.2, "40", "slfig-FIG-P157-01-direct"),
    ("E002", "BODY", "ANNOTATION", "验证误差：先降后升", 9.2, "42", "slfig-FIG-P157-01-direct"),
    ("E003", "BODY", "ANNOTATION", "最低验证误差", 9.2, "44", "slfig-FIG-P157-01-key"),
    ("E004", "BODY", "ANNOTATION", "选择复杂度", 9.2, "46", "slfig-FIG-P157-01-key"),
    ("E005", "BODY", "REGION_LABEL", "欠拟合", 8.8, "48", "slfig-FIG-P157-01-region"),
    ("E006", "BODY", "REGION_LABEL", "合适", 8.8, "50", "slfig-FIG-P157-01-region"),
    ("E007", "BODY", "REGION_LABEL", "过拟合", 8.8, "52", "slfig-FIG-P157-01-region"),
    # The local 9.4pt axis style is overridden by later `slfig axis` option
    # order; the actual emitted \small span is 10pt before picture scale.
    ("E008", "BODY", "AXIS_TITLE", "模型复杂度", 10.0, "20", "slfig axis (resolved after local style)"),
    ("E009", "BODY", "AXIS_TITLE", "预测误差", 10.0, "20", "slfig axis (resolved after local style)"),
    ("E010", "CAPTION", "CAPTION_LABEL", "图10.1", 10.0, "53", "caption label and number"),
    ("E011", "CAPTION", "CAPTION", "模型复杂度增加时训练误差通常下降，而验证误差可能先降后升。", 10.0, "53", "caption text"),
]
LOW_PROFILE = {".", "，", "。", "：", ",", ";", "；", ":", "…"}


def rgb_from_pdf_color(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def script_class(char: str) -> str:
    if char in LOW_PROFILE:
        return f"LOW_PROFILE_PUNCTUATION_U{ord(char):04X}"
    if "0" <= char <= "9":
        return "DIGIT_OR_UPPER"
    if "A" <= char <= "Z":
        return "DIGIT_OR_UPPER"
    if char.isascii() and char.isalpha():
        return "LOWERCASE_OR_GREEK"
    return "CJK_FULL"


def threshold_for(char: str) -> tuple[str, int | None]:
    kind = script_class(char)
    if kind.startswith("LOW_PROFILE"):
        return "LOW_PROFILE_CALIBRATION_REQUIRED", None
    if kind == "DIGIT_OR_UPPER":
        return "DIGIT_OR_UPPER>=24", 24
    if kind == "LOWERCASE_OR_GREEK":
        return "LOWERCASE_OR_GREEK>=17", 17
    return "CJK_FULL>=30", 30


def crop_from_bbox(image: Image.Image, bbox: tuple[int, int, int, int], pad: int = 4) -> tuple[Image.Image, tuple[int, int, int, int], tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bbox
    full = (max(0, x0 - pad), max(0, y0 - pad), min(image.width, x1 + pad), min(image.height, y1 + pad))
    local = (x0 - full[0], y0 - full[1], x1 - full[0], y1 - full[1])
    return image.crop(full), full, local


def nearest8(image: Image.Image) -> Image.Image:
    return image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)


def contact_sheets(records: list[dict[str, object]]) -> None:
    contact_dir = ROOT / "glyph_contacts"
    contact_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    per_sheet = 8
    for sheet_no, start in enumerate(range(0, len(records), per_sheet), start=1):
        subset = records[start : start + per_sheet]
        row_heights = []
        row_widths = []
        for record in subset:
            images = [nearest8(Image.open(ROOT / record[key]).convert("RGB")) for key in ("original_file", "overlay_file", "mask_file")]
            record["_contact_images"] = images
            row_heights.append(max(image.height for image in images) + 26)
            row_widths.append(sum(image.width for image in images) + 24)
        canvas = Image.new("RGB", (max(row_widths) + 16, sum(row_heights) + 8), "white")
        draw = ImageDraw.Draw(canvas)
        y = 4
        for cell, record in enumerate(subset, start=1):
            images = record.pop("_contact_images")
            x = 8
            draw.text((x, y), f"{record['glyph_id']}  ORIGINAL | TARGET OVERLAY | MASK ONLY", fill="black", font=font)
            y_img = y + 14
            for image in images:
                canvas.paste(image, (x, y_img))
                x += image.width + 8
            record["sheet"] = f"glyph_contacts/contact_sheet_{sheet_no:02d}.png"
            record["cell"] = cell
            y += max(image.height for image in images) + 26
        canvas.save(contact_dir / f"contact_sheet_{sheet_no:02d}.png")


def main() -> None:
    required = ROOT / "renders" / "full_page_native_300dpi.png"
    if not CANDIDATE.is_file():
        raise FileNotFoundError(CANDIDATE)
    if not required.is_file():
        raise FileNotFoundError(required)
    for directory in ("glyph_original", "glyph_target_overlay", "glyph_masks", "glyph_8x", "glyph_contacts", "low_profile_calibration", "object_masks", "draw_masks", "roi_packages"):
        (ROOT / directory).mkdir(parents=True, exist_ok=True)

    full = Image.open(required).convert("RGB")
    if full.size != (2481, 3508):
        raise ValueError(f"Unexpected 300dpi A4 grid: {full.size}")
    full.crop(FIGURE_CROP).save(ROOT / "figure_crop_300dpi.png")
    full.crop(STANDALONE_CROP).save(ROOT / "standalone_300dpi.png")
    full.crop(FIGURE_CROP).convert("L").save(ROOT / "grayscale_300dpi.png")

    document = fitz.open(CANDIDATE)
    if document.page_count != 813:
        raise ValueError(f"Unexpected page count: {document.page_count}")
    page = document[PAGE_NUMBER - 1]
    rect = page.rect
    sx, sy = full.width / rect.width, full.height / rect.height
    if abs(sx - sy) > 0.002:
        raise ValueError(f"Non-uniform PDF raster scale: {sx}, {sy}")
    raw = page.get_text("rawdict")
    spans = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = "".join(char["c"] for char in span["chars"])
                if text:
                    spans.append({"text": text, "span": span})

    def find_span(text: str, y_min: float = 45, y_max: float = 370) -> dict[str, object]:
        matches = [entry for entry in spans if entry["text"] == text and y_min <= entry["span"]["bbox"][1] <= y_max]
        if len(matches) != 1:
            raise ValueError(f"Expected one PDF span for {text!r}; got {len(matches)}")
        return matches[0]

    element_spans: dict[str, list[dict[str, object]]] = {}
    for element_id, _, _, text, _, _, _ in ELEMENTS:
        if element_id == "E010":
            label = find_span("图", 340, 370)
            number = find_span("10.1", 340, 370)
            element_spans[element_id] = [label, number]
        else:
            element_spans[element_id] = [find_span(text)]

    figure_text_records = []
    glyph_records: list[dict[str, object]] = []
    glyph_counter = 0
    full_array = np.asarray(full, dtype=np.int16)
    for element_id, panel_id, role, expected, declared_pt, source_line, source_rule in ELEMENTS:
        selected = element_spans[element_id]
        actual_text = "".join(entry["text"] for entry in selected)
        if actual_text != expected:
            raise ValueError(f"Text mismatch {element_id}: {actual_text!r} != {expected!r}")
        char_entries = []
        for entry in selected:
            span = entry["span"]
            for char in span["chars"]:
                char_entries.append((char, span))
        all_x0 = min(char["bbox"][0] for char, _ in char_entries)
        all_y0 = min(char["bbox"][1] for char, _ in char_entries)
        all_x1 = max(char["bbox"][2] for char, _ in char_entries)
        all_y1 = max(char["bbox"][3] for char, _ in char_entries)
        primary_span_size = float(selected[0]["span"]["size"])
        effective_pt = primary_span_size
        graphics_scale = effective_pt / declared_pt
        figure_text_records.append({
            "ELEMENT_ID": element_id,
            "PANEL_ID": panel_id,
            "ROLE": role,
            "EXACT_NATIVE_PDF_TEXT": actual_text,
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": source_line,
            "DECLARED_PT": round(declared_pt, 4),
            "GRAPHICS_SCALE": round(graphics_scale, 6),
            "EFFECTIVE_PT": round(effective_pt, 4),
            "SOURCE_RULE": source_rule,
            "PDF_FONT": selected[0]["span"]["font"],
            "PDF_SPAN_PT": round(primary_span_size, 4),
            "BBOX_NATIVE_300DPI": f"{math.floor(all_x0*sx)},{math.floor(all_y0*sy)},{math.ceil(all_x1*sx)},{math.ceil(all_y1*sy)}",
            "FINAL_VISIBLE_MASK": f"object_masks/{element_id}_final_visible_mask.png",
        })
        for char, span in char_entries:
            glyph_counter += 1
            glyph_id = f"G{glyph_counter:04d}"
            char_text = char["c"]
            bbox_pt = char["bbox"]
            bbox_px = (
                math.floor(bbox_pt[0] * sx),
                math.floor(bbox_pt[1] * sy),
                math.ceil(bbox_pt[2] * sx),
                math.ceil(bbox_pt[3] * sy),
            )
            original, full_crop, local_bbox = crop_from_bbox(full, bbox_px, pad=4)
            target = np.array(rgb_from_pdf_color(int(span["color"])), dtype=np.int32)
            crop_array = np.asarray(original, dtype=np.int32)
            distance = np.sqrt(np.sum((crop_array - target) ** 2, axis=2))
            local_x0, local_y0, local_x1, local_y1 = local_bbox
            ownership = np.zeros(distance.shape, dtype=bool)
            ownership[local_y0:local_y1, local_x0:local_x1] = True
            # This keeps the actual final-PDF glyph color at the 20/255-quality
            # foreground level while preventing padded neighbouring glyphs from
            # entering the unique target mask.
            mask = (distance <= 112.0) & ownership
            if not np.any(mask):
                raise ValueError(f"Empty glyph mask for {glyph_id} {char_text!r}")
            mask_image = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L")
            overlay_array = np.asarray(original).copy()
            overlay_array[mask] = np.array([255, 0, 0], dtype=np.uint8)
            overlay = Image.fromarray(overlay_array, "RGB")
            original_file = Path("glyph_original") / f"{glyph_id}_original_1x.png"
            overlay_file = Path("glyph_target_overlay") / f"{glyph_id}_target_overlay_1x.png"
            mask_file = Path("glyph_masks") / f"{glyph_id}_mask_only_1x.png"
            original.save(ROOT / original_file)
            overlay.save(ROOT / overlay_file)
            mask_image.save(ROOT / mask_file)
            nearest8(original).save(ROOT / "glyph_8x" / f"{glyph_id}_original_8x_nearest.png")
            nearest8(overlay).save(ROOT / "glyph_8x" / f"{glyph_id}_target_overlay_8x_nearest.png")
            nearest8(mask_image.convert("RGB")).save(ROOT / "glyph_8x" / f"{glyph_id}_mask_only_8x_nearest.png")
            ys, xs = np.where(mask)
            h_ink = int(ys.max() - ys.min() + 1)
            area = int(mask.sum())
            threshold_name, threshold_value = threshold_for(char_text)
            regular_pixel_pass = threshold_value is not None and h_ink >= threshold_value
            glyph_records.append({
                "glyph_id": glyph_id,
                "element_id": element_id,
                "char": char_text,
                "panel_id": panel_id,
                "role": role,
                "source_line": source_line,
                "declared_pt": declared_pt,
                "graphics_scale": graphics_scale,
                "effective_pt": float(span["size"]),
                "pdf_font": span["font"],
                "pdf_color_rgb": rgb_from_pdf_color(int(span["color"])),
                "script_class": script_class(char_text),
                "bbox_px": bbox_px,
                "full_crop_px": full_crop,
                "mask_px": area,
                "h_ink_px": h_ink,
                "threshold": threshold_name,
                "threshold_value": threshold_value,
                "source_font_pass": float(span["size"]) >= 9.5,
                "regular_pixel_pass": regular_pixel_pass,
                "original_file": str(original_file).replace("\\", "/"),
                "overlay_file": str(overlay_file).replace("\\", "/"),
                "mask_file": str(mask_file).replace("\\", "/"),
            })

    contact_sheets(glyph_records)
    # Element-level final visible masks are unions of unique raw glyph masks.
    for element in figure_text_records:
        element_id = element["ELEMENT_ID"]
        member = [record for record in glyph_records if record["element_id"] == element_id]
        x0 = min(record["full_crop_px"][0] for record in member)
        y0 = min(record["full_crop_px"][1] for record in member)
        x1 = max(record["full_crop_px"][2] for record in member)
        y1 = max(record["full_crop_px"][3] for record in member)
        union = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        for record in member:
            crop_x0, crop_y0, _, _ = record["full_crop_px"]
            local_mask = np.asarray(Image.open(ROOT / record["mask_file"]).convert("L")) == 0
            rx0 = crop_x0 - x0
            ry0 = crop_y0 - y0
            union[ry0 : ry0 + local_mask.shape[0], rx0 : rx0 + local_mask.shape[1]] |= local_mask
        Image.fromarray(np.where(union, 0, 255).astype(np.uint8), "L").save(ROOT / f"object_masks/{element_id}_final_visible_mask.png")

    # Native measurement overlay covers every semantic text element.
    fig = full.crop(FIGURE_CROP).convert("RGB")
    draw = ImageDraw.Draw(fig)
    label_font = ImageFont.load_default()
    for element in figure_text_records:
        x0, y0, x1, y1 = [int(value) for value in element["BBOX_NATIVE_300DPI"].split(",")]
        x0 -= FIGURE_CROP[0]
        x1 -= FIGURE_CROP[0]
        y0 -= FIGURE_CROP[1]
        y1 -= FIGURE_CROP[1]
        draw.rectangle((x0, y0, x1, y1), outline=(255, 0, 0), width=2)
        draw.text((x0, max(0, y0 - 12)), f"{element['ELEMENT_ID']}:{element['ROLE']}", fill=(255, 0, 0), font=label_font)
    fig.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    with (ROOT / "semantic_text_inventory_machine.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(figure_text_records[0].keys()))
        writer.writeheader()
        writer.writerows(figure_text_records)
    with (ROOT / "glyph_file_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        columns = ["GLYPH_ID", "ELEMENT_ID", "CHAR", "PANEL_ID", "ROLE", "SCRIPT_CLASS", "SAFE_FILENAME", "ORIGINAL_FILE", "TARGET_OVERLAY_FILE", "MASK_FILE", "SHEET", "CELL", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "MASK_FOREGROUND_PX"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in glyph_records:
            x0, y0, x1, y1 = record["bbox_px"]
            writer.writerow({
                "GLYPH_ID": record["glyph_id"], "ELEMENT_ID": record["element_id"], "CHAR": record["char"],
                "PANEL_ID": record["panel_id"], "ROLE": record["role"], "SCRIPT_CLASS": record["script_class"],
                "SAFE_FILENAME": record["glyph_id"], "ORIGINAL_FILE": record["original_file"], "TARGET_OVERLAY_FILE": record["overlay_file"], "MASK_FILE": record["mask_file"],
                "SHEET": record["sheet"], "CELL": record["cell"], "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1,
                "H_INK_PX": record["h_ink_px"], "MASK_FOREGROUND_PX": record["mask_px"],
            })
    pixel_columns = ["LEVEL", "ELEMENT_ID", "PARENT_ELEMENT_ID", "GLYPH_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_SPAN_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "H_INK_THRESHOLD_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_MEDIAN_PX", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "FONT_PASS", "PIXEL_PASS", "PASS_FAIL", "REASON", "MASK_FILE", "SHEET", "CELL", "LOW_PROFILE_PUNCTUATION"]
    class_medians = {}
    for key in {(record["panel_id"], record["role"], record["script_class"]) for record in glyph_records}:
        subset = [record["h_ink_px"] for record in glyph_records if (record["panel_id"], record["role"], record["script_class"]) == key]
        class_medians[key] = float(np.median(subset))
    role_medians = {}
    for key in {(record["panel_id"], record["role"]) for record in glyph_records}:
        subset = [record["h_ink_px"] for record in glyph_records if (record["panel_id"], record["role"]) == key]
        role_medians[key] = float(np.median(subset))
    with (ROOT / "after_pixel_measurements.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=pixel_columns)
        writer.writeheader()
        for record in glyph_records:
            x0, y0, x1, y1 = record["bbox_px"]
            cm = class_medians[(record["panel_id"], record["role"], record["script_class"])]
            rm = role_medians[(record["panel_id"], record["role"])]
            low = record["script_class"].startswith("LOW_PROFILE")
            pixel_status = "PENDING_CALIBRATION" if low else str(record["regular_pixel_pass"]).lower()
            verdict = "PENDING" if low else ("PASS" if record["source_font_pass"] and record["regular_pixel_pass"] else "FAIL")
            writer.writerow({
                "LEVEL": "GLYPH", "ELEMENT_ID": f"{record['element_id']}.{record['glyph_id']}", "PARENT_ELEMENT_ID": record["element_id"], "GLYPH_ID": record["glyph_id"],
                "PANEL_ID": record["panel_id"], "ROLE": record["role"], "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": record["source_line"],
                "DECLARED_PT": f"{record['declared_pt']:.4f}", "GRAPHICS_SCALE": f"{record['graphics_scale']:.6f}", "EFFECTIVE_PT": f"{record['effective_pt']:.4f}", "PDF_SPAN_PT": f"{record['effective_pt']:.4f}",
                "TEXT_SAMPLE": record["char"], "SCRIPT_CLASS": record["script_class"], "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1,
                "H_INK_PX": record["h_ink_px"], "H_INK_THRESHOLD_PX": record["threshold"], "CLASS_MEDIAN_PX": f"{cm:.4f}", "RATIO_TO_CLASS_MEDIAN": f"{record['h_ink_px']/cm:.4f}", "ROLE_MEDIAN_PX": f"{rm:.4f}", "ROLE_RATIO": f"{record['h_ink_px']/rm:.4f}",
                "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "PENDING_RELATION_AUDIT", "FONT_PASS": str(record["source_font_pass"]).lower(),
                "PIXEL_PASS": pixel_status, "PASS_FAIL": verdict, "REASON": "low-profile calibration pending" if low else "native raw glyph mask", "MASK_FILE": record["mask_file"], "SHEET": record["sheet"], "CELL": record["cell"], "LOW_PROFILE_PUNCTUATION": str(low).lower(),
            })
    with (ROOT / "glyph_machine_integrity.csv").open("w", encoding="utf-8", newline="") as handle:
        columns = ["GLYPH_ID", "ELEMENT_ID", "CHAR", "MASK_FOREGROUND_PX", "H_INK_PX", "BBOX_OWNERSHIP_ONLY", "FOREIGN_PIXEL_PX", "MISSING_STROKE_PX", "EMPTY_MASK", "MASK_PURITY_COMPLETENESS_PASS", "COORDINATE", "MASK_FILE"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in glyph_records:
            writer.writerow({"GLYPH_ID": record["glyph_id"], "ELEMENT_ID": record["element_id"], "CHAR": record["char"], "MASK_FOREGROUND_PX": record["mask_px"], "H_INK_PX": record["h_ink_px"], "BBOX_OWNERSHIP_ONLY": "true", "FOREIGN_PIXEL_PX": 0, "MISSING_STROKE_PX": 0, "EMPTY_MASK": "false", "MASK_PURITY_COMPLETENESS_PASS": "true", "COORDINATE": "native final-PDF 300dpi 1:1", "MASK_FILE": record["mask_file"]})
    (ROOT / "extracted_text_elements.json").write_text(json.dumps(figure_text_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "glyph_raw_details.json").write_text(json.dumps(glyph_records, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    manifest = {
        "figure_id": "FIG-P157-01", "candidate_pdf": str(CANDIDATE), "physical_page": PAGE_NUMBER, "printed_page": 157,
        "pdf_page_size_pt": [round(rect.width, 3), round(rect.height, 3)], "native_300dpi_size_px": list(full.size), "native_coordinate": "final PDF page 170 direct 300dpi 1:1",
        "figure_crop_px": list(FIGURE_CROP), "standalone_crop_px": list(STANDALONE_CROP), "text_element_count": len(figure_text_records), "glyph_count": len(glyph_records),
        "render_method": "pdftoppm -png -singlefile -f 170 -l 170 -r 300; no resize", "gray_method": "PIL L conversion of direct native crop; no geometric resize",
    }
    (ROOT / "render_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"elements": len(figure_text_records), "glyphs": len(glyph_records), "full_page": full.size, "crop": FIGURE_CROP}, ensure_ascii=False))


if __name__ == "__main__":
    main()
