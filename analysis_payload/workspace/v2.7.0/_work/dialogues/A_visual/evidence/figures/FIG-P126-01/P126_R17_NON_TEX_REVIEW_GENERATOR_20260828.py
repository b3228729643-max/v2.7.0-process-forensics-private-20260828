from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
REVIEW = ROOT / "review"
FULL = REVIEW / "full_page_300.png"


def bbox_of(obj: dict) -> tuple[float, float, float, float]:
    return (float(obj["x0"]), float(obj["top"]), float(obj["x1"]), float(obj["bottom"]))


def union_bbox(items: list[dict]) -> tuple[float, float, float, float]:
    boxes = [bbox_of(x) for x in items]
    return (
        min(x[0] for x in boxes),
        min(x[1] for x in boxes),
        max(x[2] for x in boxes),
        max(x[3] for x in boxes),
    )


def overlap_gap(a: tuple[float, float, float, float], b: tuple[float, float, float, float], sx: float, sy: float) -> tuple[float, float]:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * sx
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1])) * sy
    overlap = ix * iy
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2])) * sx
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3])) * sy
    return overlap, math.hypot(dx, dy)


def px_bbox(box: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    return (
        int(math.floor(box[0] * sx)),
        int(math.floor(box[1] * sy)),
        int(math.ceil(box[2] * sx)),
        int(math.ceil(box[3] * sy)),
    )


def expand(box: tuple[int, int, int, int], pad: int, width: int, height: int) -> tuple[int, int, int, int]:
    return (max(0, box[0] - pad), max(0, box[1] - pad), min(width, box[2] + pad), min(height, box[3] + pad))


def save_nn8(image: Image.Image, path: Path) -> None:
    image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(path)


def color_runs(image: Image.Image, box: tuple[int, int, int, int], kind: str) -> dict:
    rgb = image.convert("RGB")
    x0, y0, x1, y1 = box
    occupied = []
    for x in range(x0, x1):
        hit = False
        for y in range(y0, y1):
            r, g, b = rgb.getpixel((x, y))
            if kind == "blue":
                hit = b - r >= 45 and b - g >= 20 and g - r >= 20 and b <= 185
            else:
                hit = g - r >= 45 and b - r >= 38 and abs(g - b) <= 45 and g <= 185
            if hit:
                hit = True
                break
        occupied.append(hit)
    runs = []
    start = None
    for idx, value in enumerate(occupied + [False]):
        if value and start is None:
            start = idx
        elif not value and start is not None:
            runs.append((x0 + start, x0 + idx - 1, idx - start))
            start = None
    gaps = []
    for left, right in zip(runs, runs[1:]):
        gaps.append((left[1] + 1, right[0] - 1, right[0] - left[1] - 1))
    return {
        "scan_box_px": list(box),
        "occupied_runs": [{"x0": a, "x1": b, "length_px": n} for a, b, n in runs],
        "internal_blank_runs": [{"x0": a, "x1": b, "length_px": n} for a, b, n in gaps],
    }


def main() -> None:
    REVIEW.mkdir(parents=True, exist_ok=True)
    image = Image.open(FULL).convert("RGB")
    with pdfplumber.open(PDF) as document:
        page = document.pages[0]
        objects = page.objects
        sx = image.width / float(page.width)
        sy = image.height / float(page.height)

        lines = objects.get("line", [])
        curves = objects.get("curve", [])
        chars = objects.get("char", [])
        rects = objects.get("rect", [])
        if (len(lines), len(curves), len(chars), len(rects)) != (13, 19, 25, 6):
            raise RuntimeError(f"unexpected PDF primitive denominator: {(len(lines), len(curves), len(chars), len(rects))}")

        catalog = []
        line_names = [
            "x-axis shaft", "y-axis shaft", "q1-q2 x1 update shaft", "q3-q4 x1 update shaft",
            "q5-q6 x1 update shaft", "q0-q1 x2 update shaft", "q2-q3 x2 update shaft",
            "q4-q5 x2 update shaft", "q6-q7 x2 update shaft",
        ]
        for index, name in enumerate(line_names):
            catalog.append({"kind": "line", "source_indices": str(index), "name": name, "bbox": bbox_of(lines[index])})
        catalog.append({"kind": "compound-line", "source_indices": "9;10;11;12", "name": "x2 legend disconnected four-segment swatch", "bbox": union_bbox(lines[9:13])})

        curve_names = [
            "x-axis arrowhead", "y-axis arrowhead", "outer contour", "second contour", "third contour", "inner contour",
            "q1-q2 x1 update arrowhead", "q3-q4 x1 update arrowhead", "q5-q6 x1 update arrowhead",
            "q0-q1 x2 update arrowhead", "q2-q3 x2 update arrowhead", "q4-q5 x2 update arrowhead", "q6-q7 x2 update arrowhead",
            "q0 initial marker", "q2 blue marker", "q4 blue marker", "q6 blue marker", "optimum star", "x1 legend solid swatch",
        ]
        for index, name in enumerate(curve_names):
            catalog.append({"kind": "curve", "source_indices": str(index), "name": name, "bbox": bbox_of(curves[index])})

        for index, char in enumerate(chars):
            text = str(char.get("text", ""))
            catalog.append({"kind": "glyph", "source_indices": str(index), "name": f"glyph {text} U+{ord(text):04X}", "bbox": bbox_of(char), "text": text, "codepoint": f"U+{ord(text):04X}"})

        rect_names = ["digit6 protective background", "digit7 protective background", "q1 square marker", "q3 square marker", "q5 square marker", "q7 square marker"]
        for index, name in enumerate(rect_names):
            catalog.append({"kind": "rect", "source_indices": str(index), "name": name, "bbox": bbox_of(rects[index])})

        if len(catalog) != 60:
            raise RuntimeError(f"reader-visible denominator is {len(catalog)}, expected 60")
        for index, item in enumerate(catalog, start=1):
            item["object_id"] = f"O{index:03d}"
            item["bbox_px"] = px_bbox(item["bbox"], sx, sy)

        with (REVIEW / "OBJECT_CATALOG_MACHINE.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["OBJECT_ID", "KIND", "SOURCE_INDICES", "NAME", "X0_PT", "TOP_PT", "X1_PT", "BOTTOM_PT", "X0_PX", "TOP_PX", "X1_PX", "BOTTOM_PX"])
            for item in catalog:
                b = item["bbox"]
                p = item["bbox_px"]
                writer.writerow([item["object_id"], item["kind"], item["source_indices"], item["name"], *[f"{v:.6f}" for v in b], *p])

        glyphs = [item for item in catalog if item["kind"] == "glyph"]
        with (REVIEW / "GLYPH_CODEPOINT_MACHINE.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["OBJECT_ID", "GLYPH", "CODEPOINT", "EXTRACTED_COUNT"])
            for item in glyphs:
                writer.writerow([item["object_id"], item["text"], item["codepoint"], 1])

        pairs = []
        pair_id = 0
        for left_index in range(len(catalog)):
            for right_index in range(left_index + 1, len(catalog)):
                pair_id += 1
                left = catalog[left_index]
                right = catalog[right_index]
                overlap, gap = overlap_gap(left["bbox"], right["bbox"], sx, sy)
                if overlap > 0:
                    machine_class = "BBOX_INTERSECT_CANDIDATE"
                elif gap <= 2.0:
                    machine_class = "BBOX_NEAR_CANDIDATE"
                else:
                    machine_class = "BBOX_CLEAR"
                pairs.append({
                    "pair_id": f"P{pair_id:05d}",
                    "left": left["object_id"],
                    "right": right["object_id"],
                    "overlap": overlap,
                    "gap": gap,
                    "machine_class": machine_class,
                })
        if pair_id != 1770:
            raise RuntimeError(f"pair denominator is {pair_id}, expected 1770")
        with (REVIEW / "PAIR_SKELETON_MACHINE.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["PAIR_ID", "LEFT_OBJECT_ID", "RIGHT_OBJECT_ID", "BBOX_OVERLAP_AREA_PX2", "BBOX_GAP_PX", "MACHINE_CLASS"])
            for pair in pairs:
                writer.writerow([pair["pair_id"], pair["left"], pair["right"], f"{pair['overlap']:.6f}", f"{pair['gap']:.6f}", pair["machine_class"]])

        candidates = [p for p in pairs if p["machine_class"] != "BBOX_CLEAR"]
        with (REVIEW / "PAIR_CANDIDATES_MACHINE.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["PAIR_ID", "LEFT_OBJECT_ID", "RIGHT_OBJECT_ID", "BBOX_OVERLAP_AREA_PX2", "BBOX_GAP_PX", "MACHINE_CLASS"])
            for pair in candidates:
                writer.writerow([pair["pair_id"], pair["left"], pair["right"], f"{pair['overlap']:.6f}", f"{pair['gap']:.6f}", pair["machine_class"]])

        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        palette = {"line": "#1565c0", "compound-line": "#00897b", "curve": "#8e24aa", "glyph": "#d81b60", "rect": "#ef6c00"}
        for item in catalog:
            box = item["bbox_px"]
            color = palette[item["kind"]]
            draw.rectangle(box, outline=color, width=2)
            draw.text((box[0], max(0, box[1] - 12)), item["object_id"], fill=color)
        overlay.save(REVIEW / "object_overlay_native1x.png")

        figure_box = (790, 240, 1715, 1055)
        figure = image.crop(figure_box)
        figure.save(REVIEW / "figure_native300_color.png")
        ImageOps.grayscale(figure).save(REVIEW / "figure_native300_grayscale.png")
        overlay.crop(figure_box).save(REVIEW / "figure_object_overlay_native1x.png")

        legend_box = (1000, 920, 1510, 1035)
        legend = image.crop(legend_box)
        legend.save(REVIEW / "legend_native1x.png")
        save_nn8(legend, REVIEW / "legend_nearest8x.png")
        ImageOps.grayscale(legend).save(REVIEW / "legend_grayscale_native1x.png")
        save_nn8(ImageOps.grayscale(legend), REVIEW / "legend_grayscale_nearest8x.png")

        label6_box = (1180, 465, 1265, 555)
        label7_box = (1140, 515, 1225, 610)
        label_cluster_box = (1090, 415, 1325, 650)
        for name, box in (("label6", label6_box), ("label7", label7_box), ("label6_7_cluster", label_cluster_box)):
            crop = image.crop(box)
            crop.save(REVIEW / f"{name}_native1x.png")
            save_nn8(crop, REVIEW / f"{name}_nearest8x.png")

        x1_metrics = color_runs(image, (1020, 960, 1120, 975), "blue")
        x2_metrics = color_runs(image, (1245, 960, 1350, 975), "teal")
        legend_metrics = {"x1": x1_metrics, "x2": x2_metrics}
        (REVIEW / "LEGEND_PIXEL_RUNS.json").write_text(json.dumps(legend_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        candidate_sheets = []
        tiles = []
        for pair in candidates:
            left = catalog[int(pair["left"][1:]) - 1]
            right = catalog[int(pair["right"][1:]) - 1]
            union = (
                min(left["bbox_px"][0], right["bbox_px"][0]), min(left["bbox_px"][1], right["bbox_px"][1]),
                max(left["bbox_px"][2], right["bbox_px"][2]), max(left["bbox_px"][3], right["bbox_px"][3]),
            )
            crop_box = expand(union, 18, image.width, image.height)
            crop = image.crop(crop_box).resize(((crop_box[2]-crop_box[0])*4, (crop_box[3]-crop_box[1])*4), Image.Resampling.NEAREST)
            tile = Image.new("RGB", (340, 240), "white")
            crop.thumbnail((330, 210), Image.Resampling.NEAREST)
            tile.paste(crop, ((340-crop.width)//2, 25))
            td = ImageDraw.Draw(tile)
            td.text((5, 5), f"{pair['pair_id']} {pair['left']}-{pair['right']} {pair['machine_class']}", fill="black")
            tiles.append(tile)
        for sheet_index in range(0, len(tiles), 12):
            sheet = Image.new("RGB", (4*340, 3*240), "white")
            for local, tile in enumerate(tiles[sheet_index:sheet_index+12]):
                sheet.paste(tile, ((local % 4)*340, (local // 4)*240))
            path = REVIEW / f"pair_candidates_nearest4x_part{sheet_index//12+1:02d}.png"
            sheet.save(path)
            candidate_sheets.append(path.name)

        object_tiles = []
        for item in catalog:
            box = expand(item["bbox_px"], 14, image.width, image.height)
            crop = image.crop(box)
            crop.thumbnail((200, 120), Image.Resampling.NEAREST)
            tile = Image.new("RGB", (210, 150), "white")
            tile.paste(crop, ((210-crop.width)//2, 24))
            ImageDraw.Draw(tile).text((4, 4), f"{item['object_id']} {item['name'][:24]}", fill="black")
            object_tiles.append(tile)
        for sheet_index in range(0, len(object_tiles), 20):
            sheet = Image.new("RGB", (5*210, 4*150), "white")
            for local, tile in enumerate(object_tiles[sheet_index:sheet_index+20]):
                sheet.paste(tile, ((local % 5)*210, (local // 5)*150))
            sheet.save(REVIEW / f"object_contact_sheet_part{sheet_index//20+1:02d}.png")

        machine = {
            "schema": "P126_R17_NON_TEX_MACHINE_RESULT_V1",
            "pdf": str(PDF),
            "page_count": 1,
            "page_size_points": [float(page.width), float(page.height)],
            "render_size_px": list(image.size),
            "render_scale": [sx, sy],
            "raw_pdf_primitives": {"line": len(lines), "curve": len(curves), "char": len(chars), "rect": len(rects), "total": len(lines)+len(curves)+len(chars)+len(rects)},
            "reader_visible_object_count": len(catalog),
            "compound_object_rule": "four disconnected x2 legend line primitives are one reader-visible swatch object",
            "unordered_pair_count": len(pairs),
            "expected_pair_count": len(catalog)*(len(catalog)-1)//2,
            "bbox_candidate_count": len(candidates),
            "bbox_intersect_count": sum(p["machine_class"] == "BBOX_INTERSECT_CANDIDATE" for p in candidates),
            "bbox_near_count": sum(p["machine_class"] == "BBOX_NEAR_CANDIDATE" for p in candidates),
            "legend_pixel_runs": legend_metrics,
            "candidate_sheets": candidate_sheets,
            "manual_fields_generated_by_script": 0,
        }
        (REVIEW / "MACHINE_RESULT.json").write_text(json.dumps(machine, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
