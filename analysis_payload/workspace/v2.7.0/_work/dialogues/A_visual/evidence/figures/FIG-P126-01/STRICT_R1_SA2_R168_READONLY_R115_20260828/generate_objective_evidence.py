from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R1_SA2_R168_READONLY_R115_20260828")
VIEWS = ROOT / "views"
MACHINE = ROOT / "machine"
ROIS = VIEWS / "rois"
CANDIDATES = VIEWS / "candidates"
PAGE_INDEX = 136
PAGE_NUMBER = PAGE_INDEX + 1
TARGET_NEEDLE = "坐标下降的每个子步只改变一个坐标"
FULL_CAPTION = "图8.1 坐标下降的每个子步只改变一个坐标，因此轨迹沿轴向折线逼近最优点。"
SCALE = 300.0 / 72.0
FIGURE_CAPTION_CLIP = fitz.Rect(108, 58, 478, 264)
FIGURE_ONLY_CLIP = fitz.Rect(148, 58, 445, 242)


def mkdirs() -> None:
    for path in (VIEWS, MACHINE, ROIS, CANDIDATES):
        path.mkdir(parents=True, exist_ok=True)


def text_lines(page: fitz.Page) -> list[dict]:
    lines: list[dict] = []
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            chars = [char for span in line["spans"] for char in span.get("chars", [])]
            lines.append(
                {
                    "text": "".join(char["c"] for char in chars),
                    "bbox": list(line["bbox"]),
                    "chars": [{"c": char["c"], "bbox": list(char["bbox"])} for char in chars],
                }
            )
    return lines


def union_bbox(*boxes: list[float]) -> list[float]:
    return [
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    ]


def select_line(lines: list[dict], text: str) -> dict:
    matches = [line for line in lines if line["text"] == text]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one line for {text!r}; found {len(matches)}")
    return matches[0]


def pt_box_to_crop_px(box: list[float], clip: fitz.Rect) -> list[int]:
    return [round((box[0] - clip.x0) * SCALE), round((box[1] - clip.y0) * SCALE), round((box[2] - clip.x0) * SCALE), round((box[3] - clip.y0) * SCALE)]


def render_clip(page: fitz.Page, clip: fitz.Rect, output: Path) -> None:
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip, alpha=False)
    pix.save(output)


def ink_height(image: Image.Image, bbox_px: list[int]) -> tuple[int, list[int] | None]:
    gray = image.convert("L")
    left = max(0, bbox_px[0] - 2)
    top = max(0, bbox_px[1] - 2)
    right = min(gray.width, bbox_px[2] + 2)
    bottom = min(gray.height, bbox_px[3] + 2)
    ink = []
    for y in range(top, bottom):
        for x in range(left, right):
            if gray.getpixel((x, y)) <= 235:
                ink.append((x, y))
    if not ink:
        return 0, None
    xs = [point[0] for point in ink]
    ys = [point[1] for point in ink]
    observed = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
    return observed[3] - observed[1], observed


def font() -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", 18)
    except OSError:
        return ImageFont.load_default()


def main() -> None:
    mkdirs()
    if not PDF.is_file():
        raise FileNotFoundError(PDF)
    with fitz.open(PDF) as document:
        matches = [index + 1 for index, page in enumerate(document) if TARGET_NEEDLE in page.get_text("text")]
        if matches != [PAGE_NUMBER]:
            raise RuntimeError(f"Unexpected target page matches: {matches}")
        page = document[PAGE_INDEX]
        lines = text_lines(page)
        render_clip(page, FIGURE_CAPTION_CLIP, VIEWS / "figure_caption_native_300dpi.png")
        render_clip(page, FIGURE_ONLY_CLIP, VIEWS / "figure_only_native_300dpi.png")

        caption_label = select_line(lines, "图8.1")
        caption_body = select_line(lines, "坐标下降的每个子步只改变一个坐标，因此轨迹沿轴向折线逼近最优点。")
        specs = [
            ("T01", "AXIS_LABEL_X1", "𝑥1", 16, "9.4", "math italic x plus subscript digit 1"),
            ("T02", "AXIS_LABEL_X2", "𝑥2", 16, "9.4", "math italic x plus subscript digit 2"),
            ("T03", "START_LABEL", "𝑥(0)", 44, "9.2", "math italic x with superscript parenthesized 0"),
            ("T04", "STEP_NUMBER", "1", 45, "8.6", "digit 1"),
            ("T05", "STEP_NUMBER", "2", 46, "8.6", "digit 2"),
            ("T06", "STEP_NUMBER", "3", 47, "8.6", "digit 3"),
            ("T07", "STEP_NUMBER", "4", 48, "8.6", "digit 4"),
            ("T08", "STEP_NUMBER", "5", 49, "8.6", "digit 5"),
            ("T09", "STEP_NUMBER", "6", 50, "8.6", "digit 6"),
            ("T10", "STEP_NUMBER", "7", 52, "8.6", "digit 7"),
            ("T11", "OPTIMUM_LABEL", "𝑥∗", 61, "9.2", "math italic x plus mathematical asterisk operator"),
            ("T12", "LEGEND_LABEL", "更新𝑥1", 64, "9.2", "Chinese 更新 plus math italic x and subscript 1"),
            ("T13", "LEGEND_LABEL", "更新𝑥2", 66, "9.2", "Chinese 更新 plus math italic x and subscript 2"),
        ]
        elements: list[dict] = []
        for element_id, role, text, source_line, declared_pt, script_desc in specs:
            line = select_line(lines, text)
            elements.append(
                {
                    "element_id": element_id,
                    "role": role,
                    "visible_text": text,
                    "source_line": source_line,
                    "declared_pt": declared_pt,
                    "script_description": script_desc,
                    "bbox_pt": line["bbox"],
                    "chars": line["chars"],
                }
            )
        elements.append(
            {
                "element_id": "T14",
                "role": "FIGURE_CAPTION",
                "visible_text": FULL_CAPTION,
                "source_line": 69,
                "declared_pt": "INHERITED_CAPTION_STYLE",
                "script_description": "Chinese caption with Arabic figure number 8.1",
                "bbox_pt": union_bbox(caption_label["bbox"], caption_body["bbox"]),
                "chars": caption_label["chars"] + caption_body["chars"],
            }
        )

        native = Image.open(VIEWS / "figure_caption_native_300dpi.png").convert("RGB")
        native.convert("L").save(VIEWS / "figure_caption_grayscale_300dpi.png")
        for element in elements:
            element["bbox_crop_300dpi_px"] = pt_box_to_crop_px(element["bbox_pt"], FIGURE_CAPTION_CLIP)
            height, observed = ink_height(native, element["bbox_crop_300dpi_px"])
            element["machine_h_ink_px"] = height
            element["machine_observed_ink_bbox_px"] = observed
            element["codepoints"] = [f"U+{ord(char['c']):04X}" for char in element["chars"]]

        with (MACHINE / "reader_visible_denominator.csv").open("w", encoding="utf-8", newline="") as handle:
            fields = ["ELEMENT_ID", "ROLE", "VISIBLE_TEXT", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "SCRIPT_DESCRIPTION", "BBOX_PT", "BBOX_CROP_300DPI_PX", "MACHINE_H_INK_PX", "CODEPOINTS"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for element in elements:
                writer.writerow(
                    {
                        "ELEMENT_ID": element["element_id"],
                        "ROLE": element["role"],
                        "VISIBLE_TEXT": element["visible_text"],
                        "SOURCE_FILE": "fig_v1_c08_coordinate.tex",
                        "SOURCE_LINE": element["source_line"],
                        "DECLARED_PT": element["declared_pt"],
                        "SCRIPT_DESCRIPTION": element["script_description"],
                        "BBOX_PT": json.dumps(element["bbox_pt"]),
                        "BBOX_CROP_300DPI_PX": json.dumps(element["bbox_crop_300dpi_px"]),
                        "MACHINE_H_INK_PX": element["machine_h_ink_px"],
                        "CODEPOINTS": " ".join(element["codepoints"]),
                    }
                )

        pairs = list(itertools.combinations(elements, 2))
        with (MACHINE / "all_unordered_text_pairs.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["PAIR_ID", "A_ID", "B_ID"])
            for index, (left, right) in enumerate(pairs, start=1):
                writer.writerow([f"P{index:03d}", left["element_id"], right["element_id"]])

        with (MACHINE / "codepoint_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["ELEMENT_ID", "CHAR_INDEX", "GLYPH", "CODEPOINT", "CHAR_BBOX_PT"])
            for element in elements:
                for index, char in enumerate(element["chars"], start=1):
                    writer.writerow([element["element_id"], index, char["c"], f"U+{ord(char['c']):04X}", json.dumps(char["bbox"])])

        text_overlay = native.copy()
        draw = ImageDraw.Draw(text_overlay)
        label_font = font()
        for element in elements:
            box = element["bbox_crop_300dpi_px"]
            draw.rectangle(box, outline=(0, 145, 70), width=3)
            draw.text((box[0], max(0, box[1] - 20)), element["element_id"], fill=(0, 100, 40), font=label_font)
        text_overlay.save(VIEWS / "text_overlay_300dpi.png")

        drawings = []
        object_overlay = native.copy()
        object_draw = ImageDraw.Draw(object_overlay)
        page_drawings = page.get_drawings()
        for index, drawing in enumerate(page_drawings, start=1):
            rect = fitz.Rect(drawing["rect"])
            expanded = fitz.Rect(rect.x0 - 0.5, rect.y0 - 0.5, rect.x1 + 0.5, rect.y1 + 0.5)
            if not expanded.intersects(FIGURE_CAPTION_CLIP):
                continue
            clipped = expanded & FIGURE_CAPTION_CLIP
            box = pt_box_to_crop_px(list(clipped), FIGURE_CAPTION_CLIP)
            object_id = f"V{len(drawings) + 1:03d}"
            object_draw.rectangle(box, outline=(180, 0, 180), width=2)
            object_draw.text((box[0], box[1]), object_id, fill=(120, 0, 120), font=label_font)
            drawings.append(
                {
                    "object_id": object_id,
                    "source_sequence": index,
                    "rect_pt": list(rect),
                    "type": drawing.get("type"),
                    "fill": drawing.get("fill"),
                    "color": drawing.get("color"),
                    "width": drawing.get("width"),
                    "item_count": len(drawing.get("items", [])),
                }
            )
        object_overlay.save(VIEWS / "object_overlay_300dpi.png")

        candidate_specs = [
            ("T01", 8, "axis x1 label versus third contour"),
            ("T04", 6, "step 1 label versus outer contour"),
            ("T05", 7, "step 2 label versus second contour"),
            ("T07", 9, "step 4 label versus fourth contour"),
            ("T08", 2, "step 5 label versus horizontal axis"),
        ]
        candidate_results = []
        native_gray = native.convert("L")
        for element_id, drawing_sequence, description in candidate_specs:
            element = next(item for item in elements if item["element_id"] == element_id)
            vector = page_drawings[drawing_sequence - 1]
            vector_mask = Image.new("1", native.size, 0)
            vector_draw = ImageDraw.Draw(vector_mask)
            stroke_px = max(2, round(float(vector.get("width") or 0.5) * SCALE))
            for item in vector.get("items", []):
                if item[0] != "l":
                    continue
                p0, p1 = item[1], item[2]
                a = (round((p0.x - FIGURE_CAPTION_CLIP.x0) * SCALE), round((p0.y - FIGURE_CAPTION_CLIP.y0) * SCALE))
                b = (round((p1.x - FIGURE_CAPTION_CLIP.x0) * SCALE), round((p1.y - FIGURE_CAPTION_CLIP.y0) * SCALE))
                vector_draw.line((a, b), fill=1, width=stroke_px)
            bbox = element["bbox_crop_300dpi_px"]
            left, top, right, bottom = bbox
            collision_points = []
            for y in range(max(0, top - 2), min(native.height, bottom + 2)):
                for x in range(max(0, left - 2), min(native.width, right + 2)):
                    if vector_mask.getpixel((x, y)) and native_gray.getpixel((x, y)) <= 110:
                        collision_points.append((x, y))
            overlay = native.copy()
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(bbox, outline=(0, 160, 0), width=3)
            for x, y in collision_points:
                overlay_draw.rectangle((x - 2, y - 2, x + 2, y + 2), fill=(255, 0, 0))
            crop_box = (max(0, left - 70), max(0, top - 70), min(native.width, right + 70), min(native.height, bottom + 70))
            candidate_native = overlay.crop(crop_box)
            candidate_native_path = CANDIDATES / f"{element_id}_vector_text_candidate_native1x.png"
            candidate_8x_path = CANDIDATES / f"{element_id}_vector_text_candidate_nearest8x.png"
            candidate_native.save(candidate_native_path)
            candidate_native.resize((candidate_native.width * 8, candidate_native.height * 8), Image.Resampling.NEAREST).save(candidate_8x_path)
            candidate_results.append(
                {
                    "element_id": element_id,
                    "drawing_sequence": drawing_sequence,
                    "description": description,
                    "vector_stroke_width_px": stroke_px,
                    "dark_final_pixels_under_vector_mask": len(collision_points),
                    "candidate_native": candidate_native_path.name,
                    "candidate_nearest8x": candidate_8x_path.name,
                }
            )
        (MACHINE / "text_contour_candidate_pixels.json").write_text(json.dumps(candidate_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        all_vector_candidates = []
        for drawing_sequence, vector in enumerate(page_drawings, start=1):
            vector_rect = fitz.Rect(vector["rect"])
            expanded = fitz.Rect(vector_rect.x0 - 0.5, vector_rect.y0 - 0.5, vector_rect.x1 + 0.5, vector_rect.y1 + 0.5)
            if not expanded.intersects(FIGURE_CAPTION_CLIP):
                continue
            vector_mask = Image.new("1", native.size, 0)
            vector_draw = ImageDraw.Draw(vector_mask)
            stroke_px = max(2, round(float(vector.get("width") or 0.5) * SCALE))
            for item in vector.get("items", []):
                if item[0] == "l":
                    p0, p1 = item[1], item[2]
                    a = (round((p0.x - FIGURE_CAPTION_CLIP.x0) * SCALE), round((p0.y - FIGURE_CAPTION_CLIP.y0) * SCALE))
                    b = (round((p1.x - FIGURE_CAPTION_CLIP.x0) * SCALE), round((p1.y - FIGURE_CAPTION_CLIP.y0) * SCALE))
                    vector_draw.line((a, b), fill=1, width=stroke_px)
                elif item[0] == "re":
                    rect = item[1]
                    box = pt_box_to_crop_px(list(rect), FIGURE_CAPTION_CLIP)
                    vector_draw.rectangle(box, outline=1, width=stroke_px)
            for element in elements:
                left, top, right, bottom = element["bbox_crop_300dpi_px"]
                count = 0
                for y in range(max(0, top - 2), min(native.height, bottom + 2)):
                    for x in range(max(0, left - 2), min(native.width, right + 2)):
                        if vector_mask.getpixel((x, y)) and native_gray.getpixel((x, y)) <= 110:
                            count += 1
                if count:
                    all_vector_candidates.append(
                        {
                            "ELEMENT_ID": element["element_id"],
                            "DRAWING_SEQUENCE": drawing_sequence,
                            "DRAWING_TYPE": vector.get("type"),
                            "DRAWING_RECT_PT": json.dumps(list(vector_rect)),
                            "DARK_FINAL_PIXELS_UNDER_VECTOR_MASK": count,
                        }
                    )
        with (MACHINE / "all_text_vector_candidate_pixels.csv").open("w", encoding="utf-8", newline="") as handle:
            fields = ["ELEMENT_ID", "DRAWING_SEQUENCE", "DRAWING_TYPE", "DRAWING_RECT_PT", "DARK_FINAL_PIXELS_UNDER_VECTOR_MASK"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(all_vector_candidates)

        semantic_overlay = native.copy()
        semantic_draw = ImageDraw.Draw(semantic_overlay)
        semantic_regions = [
            ("S01_START", fitz.Rect(174, 68, 250, 128), (215, 30, 30)),
            ("S02_MIDDLE", fitz.Rect(220, 100, 295, 151), (255, 135, 0)),
            ("S03_OPTIMUM", fitz.Rect(275, 119, 325, 169), (165, 0, 190)),
            ("S04_AXIS_X1", fitz.Rect(345, 118, 380, 151), (0, 80, 200)),
            ("S05_AXIS_X2", fitz.Rect(284, 57, 319, 92), (0, 80, 200)),
            ("S06_LEGEND", fitz.Rect(215, 215, 330, 241), (0, 130, 110)),
            ("S07_CAPTION", fitz.Rect(110, 239, 475, 262), (70, 70, 70)),
        ]
        for semantic_id, rect, color in semantic_regions:
            box = pt_box_to_crop_px(list(rect), FIGURE_CAPTION_CLIP)
            semantic_draw.rectangle(box, outline=color, width=4)
            semantic_draw.text((box[0] + 2, box[1] + 2), semantic_id, fill=color, font=label_font)
        semantic_overlay.save(VIEWS / "semantic_overlay_300dpi.png")

        roi_specs = [
            ("R01_start", fitz.Rect(174, 68, 250, 128)),
            ("R02_middle", fitz.Rect(220, 100, 295, 151)),
            ("R03_optimum", fitz.Rect(275, 119, 325, 169)),
            ("R04_axis_x1", fitz.Rect(345, 118, 380, 151)),
            ("R05_axis_x2", fitz.Rect(284, 57, 319, 92)),
            ("R06_legend", fitz.Rect(215, 215, 330, 241)),
            ("R07_caption", fitz.Rect(110, 239, 475, 262)),
        ]
        roi_manifest = []
        for roi_id, clip in roi_specs:
            native_path = ROIS / f"{roi_id}_native1x_300dpi.png"
            nearest_path = ROIS / f"{roi_id}_nearest8x.png"
            render_clip(page, clip, native_path)
            with Image.open(native_path) as roi_image:
                enlarged = roi_image.resize((roi_image.width * 8, roi_image.height * 8), Image.Resampling.NEAREST)
                enlarged.save(nearest_path)
                roi_manifest.append(
                    {
                        "roi_id": roi_id,
                        "clip_pt": list(clip),
                        "native_path": native_path.name,
                        "native_size_px": [roi_image.width, roi_image.height],
                        "nearest8x_path": nearest_path.name,
                        "nearest8x_size_px": [enlarged.width, enlarged.height],
                    }
                )

        geometry = {
            "pdf": str(PDF),
            "pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest().upper(),
            "page_count": len(document),
            "target_text_hits_physical_pages": matches,
            "target_physical_page": PAGE_NUMBER,
            "printed_page_number": 124,
            "page_rect_pt": list(page.rect),
            "figure_caption_clip_pt": list(FIGURE_CAPTION_CLIP),
            "figure_only_clip_pt": list(FIGURE_ONLY_CLIP),
            "element_count": len(elements),
            "unordered_pair_count": len(pairs),
            "pair_count_formula": f"C({len(elements)},2)={len(elements) * (len(elements) - 1) // 2}",
            "roi_manifest": roi_manifest,
        }
        (MACHINE / "pdf_location_geometry.json").write_text(json.dumps(geometry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (MACHINE / "page137_text_raw.json").write_text(json.dumps(lines, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (MACHINE / "page137_drawings_summary.json").write_text(json.dumps(drawings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        print(json.dumps({"page": PAGE_NUMBER, "elements": len(elements), "pairs": len(pairs), "drawings": len(drawings), "rois": len(roi_specs)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
