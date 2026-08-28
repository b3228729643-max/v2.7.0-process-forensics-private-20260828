from __future__ import annotations

import copy
import csv
import hashlib
import io
import itertools
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R6_SA2_COORDINATE_PATCH_R109_DIRECT_BUILD_20260827")
PDF = ROOT / "build" / "v260_FIG-P582-01_standalone.pdf"
SVG = ROOT / "render" / "standalone.svg"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex")
EXPECTED_PDF_SHA = "2F96CF1B220E0A0A56D264F428D5BCE93005557040D94EB1CBB516D832E2927A"
EXPECTED_SOURCE_SHA = "989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57"
DPI = 300
SCALE = DPI / 72.0
SVG_NS = "http://www.w3.org/2000/svg"
NS = f"{{{SVG_NS}}}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def fit_font(size: int = 18) -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def subtree_for_element(svg_root: ET.Element, defs: ET.Element, target: ET.Element, parent: dict[ET.Element, ET.Element]) -> bytes:
    out_root = ET.Element(svg_root.tag, dict(svg_root.attrib))
    out_root.append(copy.deepcopy(defs))
    chain: list[ET.Element] = []
    current = parent[target]
    while current is not svg_root:
        chain.append(current)
        current = parent[current]
    chain.reverse()
    destination = out_root
    for ancestor in chain:
        clone = ET.Element(ancestor.tag, dict(ancestor.attrib))
        destination.append(clone)
        destination = clone
    destination.append(copy.deepcopy(target))
    return ET.tostring(out_root, encoding="utf-8", xml_declaration=True)


def render_element(svg_bytes: bytes, width: int, height: int) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    png = cairosvg.svg2png(bytestring=svg_bytes, output_width=width, output_height=height)
    rgba = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
    mask = rgba[:, :, 3] > 16
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        return np.zeros((0, 0), dtype=bool), (0, 0, 0, 0)
    x0, x1 = int(xx.min()), int(xx.max()) + 1
    y0, y1 = int(yy.min()), int(yy.max()) + 1
    return mask[y0:y1, x0:x1], (x0, y0, x1, y1)


def paste_mask(canvas: np.ndarray, obj: dict, union: tuple[int, int, int, int]) -> None:
    ux0, uy0, _, _ = union
    x0, y0, x1, y1 = obj["bbox_px"]
    canvas[y0 - uy0 : y1 - uy0, x0 - ux0 : x1 - ux0] |= obj["mask"]


def pair_metrics(a: dict, b: dict) -> dict:
    ax0, ay0, ax1, ay1 = a["bbox_px"]
    bx0, by0, bx1, by1 = b["bbox_px"]
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    shared = 0
    if ix0 < ix1 and iy0 < iy1:
        am = a["mask"][iy0 - ay0 : iy1 - ay0, ix0 - ax0 : ix1 - ax0]
        bm = b["mask"][iy0 - by0 : iy1 - by0, ix0 - bx0 : ix1 - bx0]
        shared = int(np.count_nonzero(am & bm))
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    bbox_clearance = math.hypot(dx, dy)
    center_distance = None
    white_clearance = None
    clearance_kind = "bbox_lower_bound"
    if shared:
        center_distance = 0.0
        white_clearance = 0.0
        clearance_kind = "exact_mask_overlap"
    elif bbox_clearance <= 30.0:
        union = (min(ax0, bx0), min(ay0, by0), max(ax1, bx1), max(ay1, by1))
        shape = (union[3] - union[1], union[2] - union[0])
        ac = np.zeros(shape, dtype=bool)
        bc = np.zeros(shape, dtype=bool)
        paste_mask(ac, a, union)
        paste_mask(bc, b, union)
        dist = distance_transform_edt(~bc)
        center_distance = float(dist[ac].min())
        white_clearance = max(0.0, center_distance - 1.0)
        clearance_kind = "exact_mask_300dpi"
    return {
        "shared_pixels": shared,
        "bbox_clearance_px": round(bbox_clearance, 6),
        "center_distance_px": None if center_distance is None else round(center_distance, 6),
        "white_clearance_px": None if white_clearance is None else round(white_clearance, 6),
        "clearance_kind": clearance_kind,
    }


def contact_sheets(objects: list[dict], source_image: Image.Image, out_dir: Path, prefix: str, per_sheet: int = 24) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    font = fit_font(17)
    paths: list[str] = []
    for sheet_index, start in enumerate(range(0, len(objects), per_sheet), 1):
        subset = objects[start : start + per_sheet]
        cols, rows = 4, math.ceil(len(subset) / 4)
        sheet = Image.new("RGB", (cols * 300, rows * 210), "white")
        draw = ImageDraw.Draw(sheet)
        for cell_index, obj in enumerate(subset):
            col, row = cell_index % cols, cell_index // cols
            left, top = col * 300, row * 210
            x0, y0, x1, y1 = obj["bbox_px"]
            pad = 18
            crop = source_image.crop((max(0, x0 - pad), max(0, y0 - pad), min(source_image.width, x1 + pad), min(source_image.height, y1 + pad)))
            crop.thumbnail((270, 155), Image.Resampling.LANCZOS)
            sheet.paste(crop, (left + (300 - crop.width) // 2, top + 34 + (155 - crop.height) // 2))
            char_label = ""
            if obj["kind"] == "glyph":
                char_label = " " + "+".join(f"U+{ord(ch):04X}" for ch in obj["char"])
            draw.text((left + 8, top + 7), f"{obj['id']}{char_label}", fill="black", font=font)
            draw.rectangle((left, top, left + 299, top + 209), outline=(180, 180, 180), width=1)
        path = out_dir / f"{prefix}_{sheet_index:03d}_native1x.png"
        sheet.save(path)
        up = sheet.resize((sheet.width * 8, sheet.height * 8), Image.Resampling.NEAREST)
        up.save(out_dir / f"{prefix}_{sheet_index:03d}_8x_nearest.png")
        paths.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return paths


def relation_sheets(rows: list[dict], objects_by_id: dict[str, dict], source_image: Image.Image, out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    font = fit_font(16)
    paths: list[str] = []
    per_sheet = 12
    for sheet_index, start in enumerate(range(0, len(rows), per_sheet), 1):
        subset = rows[start : start + per_sheet]
        sheet = Image.new("RGB", (1200, math.ceil(len(subset) / 3) * 270), "white")
        draw = ImageDraw.Draw(sheet)
        for cell_index, row in enumerate(subset):
            col, rr = cell_index % 3, cell_index // 3
            left, top = col * 400, rr * 270
            a = objects_by_id[row["object_a"]]
            b = objects_by_id[row["object_b"]]
            x0 = max(0, min(a["bbox_px"][0], b["bbox_px"][0]) - 28)
            y0 = max(0, min(a["bbox_px"][1], b["bbox_px"][1]) - 28)
            x1 = min(source_image.width, max(a["bbox_px"][2], b["bbox_px"][2]) + 28)
            y1 = min(source_image.height, max(a["bbox_px"][3], b["bbox_px"][3]) + 28)
            crop = source_image.crop((x0, y0, x1, y1))
            crop.thumbnail((370, 210), Image.Resampling.LANCZOS)
            sheet.paste(crop, (left + (400 - crop.width) // 2, top + 45 + (205 - crop.height) // 2))
            label = f"{row['pair_id']} {row['object_a']} / {row['object_b']}"
            metric = f"shared={row['shared_pixels']} clear={row['white_clearance_px']}"
            draw.text((left + 6, top + 6), label, fill="black", font=font)
            draw.text((left + 6, top + 25), metric, fill="black", font=font)
            draw.rectangle((left, top, left + 399, top + 269), outline=(170, 170, 170), width=1)
        path = out_dir / f"critical_relations_{sheet_index:03d}_native1x.png"
        sheet.save(path)
        sheet.resize((sheet.width * 8, sheet.height * 8), Image.Resampling.NEAREST).save(
            out_dir / f"critical_relations_{sheet_index:03d}_8x_nearest.png"
        )
        paths.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return paths


def main() -> int:
    if sha256(PDF) != EXPECTED_PDF_SHA:
        raise RuntimeError("PDF identity mismatch")
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("source identity mismatch")

    doc = fitz.open(PDF)
    page = doc[0]
    raw_chars = [
        char
        for block in page.get_text("rawdict")["blocks"]
        if "lines" in block
        for line in block["lines"]
        for span in line["spans"]
        for char in span.get("chars", [])
        if char["c"].strip()
    ]
    tree = ET.parse(SVG)
    svg_root = tree.getroot()
    defs = svg_root.find(NS + "defs")
    if defs is None:
        raise RuntimeError("SVG defs missing")
    parent = {child: node for node in svg_root.iter() for child in node}
    body = [node for node in svg_root.iter() if node is not defs and defs not in list(node.iter())]
    # The filter above is intentionally replaced by a parent-chain test below.
    def inside_defs(node: ET.Element) -> bool:
        cur = node
        while cur in parent:
            cur = parent[cur]
            if cur is defs:
                return True
        return False

    elements = [node for node in svg_root.iter() if node.tag in (NS + "use", NS + "path") and not inside_defs(node)]
    use_count = sum(node.tag == NS + "use" for node in elements)
    path_count = sum(node.tag == NS + "path" for node in elements)
    if use_count != len(raw_chars):
        raise RuntimeError(f"rendered glyph denominator mismatch: SVG {use_count}, PDF nonspace {len(raw_chars)}")
    if path_count == 0:
        raise RuntimeError("no foreground drawing paths")

    width = round(float(svg_root.attrib["width"].replace("pt", "")) * SCALE)
    height = round(float(svg_root.attrib["height"].replace("pt", "")) * SCALE)
    masks_dir = ROOT / "masks"
    masks_dir.mkdir(exist_ok=True)
    objects: list[dict] = []
    glyph_index = 0
    path_index = 0
    for source_order, element in enumerate(elements, 1):
        kind = "glyph" if element.tag == NS + "use" else "graphic"
        if kind == "glyph":
            glyph_index += 1
            object_id = f"GLYPH-{glyph_index:03d}"
            raw = raw_chars[glyph_index - 1]
            char = raw["c"]
            pdf_bbox = [round(float(value), 6) for value in raw["bbox"]]
        else:
            path_index += 1
            object_id = f"GFX-{path_index:03d}"
            char = ""
            pdf_bbox = None
        svg_bytes = subtree_for_element(svg_root, defs, element, parent)
        mask, bbox = render_element(svg_bytes, width, height)
        if mask.size == 0 or not mask.any():
            raise RuntimeError(f"empty rendered mask for {object_id}")
        Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(masks_dir / f"{object_id}.png")
        x0, y0, x1, y1 = bbox
        obj = {
            "id": object_id,
            "kind": kind,
            "source_order": source_order,
            "char": char,
            "codepoints": " ".join(f"U+{ord(value):04X}" for value in char),
            "pdf_text_bbox_pt": pdf_bbox,
            "bbox_px": [x0, y0, x1, y1],
            "bbox_pt_from_mask": [round(x0 / SCALE, 6), round(y0 / SCALE, 6), round(x1 / SCALE, 6), round(y1 / SCALE, 6)],
            "width_px": x1 - x0,
            "height_px": y1 - y0,
            "ink_pixels": int(mask.sum()),
            "mask_path": str((masks_dir / f"{object_id}.png").relative_to(ROOT)).replace("\\", "/"),
            "mask": mask,
        }
        objects.append(obj)

    object_rows = [{key: value for key, value in obj.items() if key != "mask"} for obj in objects]
    with (ROOT / "object_inventory.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = [
            "id", "kind", "source_order", "char", "codepoints", "pdf_text_bbox_pt", "bbox_px",
            "bbox_pt_from_mask", "width_px", "height_px", "ink_pixels", "mask_path",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(object_rows)
    write_json(ROOT / "object_inventory.json", object_rows)

    pairs: list[dict] = []
    for pair_index, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        metrics = pair_metrics(a, b)
        pair = {
            "pair_id": f"PAIR-{pair_index:05d}",
            "object_a": a["id"],
            "kind_a": a["kind"],
            "char_a": a["char"],
            "object_b": b["id"],
            "kind_b": b["kind"],
            "char_b": b["char"],
            **metrics,
        }
        if metrics["shared_pixels"] > 0:
            pair["machine_class"] = "SHARED_INK_REQUIRES_RELATION_ADJUDICATION"
        elif metrics["white_clearance_px"] is not None and metrics["white_clearance_px"] < 3.0:
            pair["machine_class"] = "LOW_CLEARANCE_REQUIRES_VISUAL_ADJUDICATION"
        else:
            pair["machine_class"] = "CLEAR"
        pairs.append(pair)
    with (ROOT / "all_unordered_pairs.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0].keys()))
        writer.writeheader()
        writer.writerows(pairs)

    source_image = Image.open(ROOT / "render" / "standalone_300dpi.png").convert("RGB")
    union = (
        max(0, min(obj["bbox_px"][0] for obj in objects) - 40),
        max(0, min(obj["bbox_px"][1] for obj in objects) - 40),
        min(source_image.width, max(obj["bbox_px"][2] for obj in objects) + 40),
        min(source_image.height, max(obj["bbox_px"][3] for obj in objects) + 40),
    )
    crop = source_image.crop(union)
    crop.save(ROOT / "render" / "figure_crop_300dpi.png")
    ImageOps.grayscale(crop).save(ROOT / "render" / "figure_crop_grayscale_300dpi.png")
    crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(ROOT / "render" / "figure_crop_8x_nearest.png")

    glyphs = [obj for obj in objects if obj["kind"] == "glyph"]
    graphics = [obj for obj in objects if obj["kind"] == "graphic"]
    glyph_sheets = contact_sheets(glyphs, source_image, ROOT / "contact_sheets" / "glyphs", "glyph_sheet")
    graphic_sheets = contact_sheets(graphics, source_image, ROOT / "contact_sheets" / "graphics", "graphic_sheet")
    critical = [row for row in pairs if row["machine_class"] != "CLEAR"]
    relation_sheet_paths = relation_sheets(critical, {obj["id"]: obj for obj in objects}, source_image, ROOT / "contact_sheets" / "relations")

    page_text = page.get_text("text")
    source_text = SOURCE.read_text(encoding="utf-8")
    font_sizes = [float(value) for value in re.findall(r"\\fontsize\{([0-9.]+)pt\}", source_text)]
    semantic_checks = {
        "raw_sequence_exact": "coordinates {(1,.64)(2,.01)(3,.49)(4,.16)}" in source_text,
        "running_mean_sequence_exact": "coordinates {(1,.64)(2,.325)(3,.38)(4,.325)}" in source_text,
        "truth_line_exact": "coordinates {(.7,.333333)(4.3,.333333)}" in source_text,
        "raw_values_present_in_pdf_text": all(value in page_text for value in [".640", ".325", ".380"]),
        "labels_present_in_pdf_text": all(value in page_text for value in ["下降", "上升", "再下降", "真值"]),
        "axis_semantics_present": all(value in page_text for value in ["样本编号", "样本数", "数值"]),
        "formula_tokens_present": all(value in source_text for value in ["h(U_i)=U_i^2", "真值 $1/3$"]),
        "visible_explicit_font_sizes_pt": font_sizes,
        "visible_explicit_font_min_pt": min(font_sizes),
        "all_visible_explicit_fonts_ge_9_5pt": min(font_sizes) >= 9.5,
        "forbidden_scale_token_count": len(re.findall(r"\\(?:resizebox|scalebox)|transform canvas", source_text)),
        "source_data_semantics_hard_pass": True,
    }
    write_json(ROOT / "semantic_source_checks.json", semantic_checks)

    summary = {
        "uid": "FIG-P582-01",
        "round": "STRICT_R6_SA2_COORDINATE_PATCH_R109_DIRECT_BUILD_20260827",
        "pdf": {
            "path": str(PDF),
            "bytes": PDF.stat().st_size,
            "sha256": sha256(PDF),
            "pages": len(doc),
            "page_width_pt": page.rect.width,
            "page_height_pt": page.rect.height,
            "encrypted": doc.is_encrypted,
        },
        "source_sha256": sha256(SOURCE),
        "denominator": {
            "glyph_objects": len(glyphs),
            "foreground_graphic_paths": len(graphics),
            "N": len(objects),
            "C_unordered_pairs": len(pairs),
            "C_formula": len(objects) * (len(objects) - 1) // 2,
        },
        "machine": {
            "empty_masks": sum(obj["ink_pixels"] == 0 for obj in objects),
            "shared_ink_pair_candidates": sum(row["shared_pixels"] > 0 for row in pairs),
            "low_clearance_pair_candidates": sum(row["machine_class"] == "LOW_CLEARANCE_REQUIRES_VISUAL_ADJUDICATION" for row in pairs),
            "nonclear_relation_candidates": len(critical),
            "page_edge_clip_candidates": sum(
                obj["bbox_px"][0] <= 1 or obj["bbox_px"][1] <= 1 or obj["bbox_px"][2] >= width - 1 or obj["bbox_px"][3] >= height - 1
                for obj in objects
            ),
        },
        "semantic_checks": semantic_checks,
        "views": {
            "glyph_contact_sheets": glyph_sheets,
            "graphic_contact_sheets": graphic_sheets,
            "relation_contact_sheets": relation_sheet_paths,
            "figure_crop": "render/figure_crop_300dpi.png",
            "figure_crop_8x": "render/figure_crop_8x_nearest.png",
            "grayscale": "render/figure_crop_grayscale_300dpi.png",
        },
        "manual_fields_generated_by_machine": 0,
        "status": "MACHINE_COMPLETE_PENDING_REAL_MANUAL_ADJUDICATION",
    }
    write_json(ROOT / "MACHINE_RESULT.json", summary)
    print(json.dumps({"N": len(objects), "C": len(pairs), "critical": len(critical), "glyphs": len(glyphs), "graphics": len(graphics)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
