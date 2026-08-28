from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
PAGE_INDEX = 28
SCALE = 300.0 / 72.0
FIGURE_CLIP_PT = fitz.Rect(130.0, 457.0, 450.0, 638.5)
FIGURE_WITH_CAPTION_CLIP_PT = fitz.Rect(50.0, 457.0, 535.0, 658.0)


def render() -> dict[str, object]:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    mat = fitz.Matrix(SCALE, SCALE)
    full = page.get_pixmap(matrix=mat, alpha=False)
    full_path = ROOT / "R111_p029_full_native300dpi.png"
    full.save(full_path)

    crop = page.get_pixmap(matrix=mat, clip=FIGURE_CLIP_PT, alpha=False)
    crop_path = ROOT / "R111_p029_FIG-P033-01_native300dpi.png"
    crop.save(crop_path)
    image = Image.open(crop_path).convert("RGB")
    image.save(ROOT / "R111_p029_FIG-P033-01_native1x.png", dpi=(300, 300))
    image.convert("L").save(ROOT / "R111_p029_FIG-P033-01_grayscale_native1x.png", dpi=(300, 300))

    # Whole-figure nearest-neighbour enlargement is a pixel-inspection aid only.
    nn = image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)
    nn.save(ROOT / "R111_p029_FIG-P033-01_nearest_neighbor8x.png", dpi=(2400, 2400))

    with_caption = page.get_pixmap(matrix=mat, clip=FIGURE_WITH_CAPTION_CLIP_PT, alpha=False)
    with_caption.save(ROOT / "R111_p029_FIG-P033-01_with_caption_native300dpi.png")

    return {
        "pdf_page_physical": PAGE_INDEX + 1,
        "page_rect_pt": list(page.rect),
        "render_scale_px_per_pt": SCALE,
        "full_png_px": [full.width, full.height],
        "figure_clip_pt": list(FIGURE_CLIP_PT),
        "figure_png_px": [crop.width, crop.height],
        "figure_with_caption_clip_pt": list(FIGURE_WITH_CAPTION_CLIP_PT),
        "figure_with_caption_png_px": [with_caption.width, with_caption.height],
        "render_contract": "Direct PDF rasterization at 300 dpi; native1x is byte-for-byte geometry-equivalent, and NN8x uses nearest-neighbour only.",
    }


def extract_pdf_objects() -> list[dict[str, object]]:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    rows: list[dict[str, object]] = []
    text = page.get_text("dict")
    for block_no, block in enumerate(text["blocks"]):
        if block.get("type") != 0:
            continue
        for line_no, line in enumerate(block.get("lines", [])):
            for span_no, span in enumerate(line.get("spans", [])):
                bbox = fitz.Rect(span["bbox"])
                if bbox.intersects(FIGURE_CLIP_PT):
                    rows.append(
                        {
                            "kind": "TEXT_SPAN",
                            "object_id": f"T-{block_no:02d}-{line_no:02d}-{span_no:02d}",
                            "bbox_pt": [round(v, 3) for v in bbox],
                            "text": span["text"],
                            "font": span["font"],
                            "size_pt": round(span["size"], 3),
                        }
                    )
    for draw_no, drawing in enumerate(page.get_drawings()):
        bbox = fitz.Rect(drawing["rect"])
        if bbox.intersects(FIGURE_CLIP_PT):
            rows.append(
                {
                    "kind": "VECTOR_DRAWING",
                    "object_id": f"V-{draw_no:03d}",
                    "bbox_pt": [round(v, 3) for v in bbox],
                    "fill": drawing.get("fill"),
                    "color": drawing.get("color"),
                    "width_pt": drawing.get("width"),
                    "items": len(drawing.get("items", [])),
                }
            )
    return rows


def strict_atomic_candidates() -> dict[str, object]:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    raw = page.get_text("rawdict")
    atoms: list[dict[str, object]] = []
    glyph_seq = 0
    # These are precisely the six figure-body label blocks plus the caption block,
    # established from the current R111 page raw dictionary. Whitespace is not visible.
    for block_no in range(20, 27):
        block = raw["blocks"][block_no]
        for line_no, line in enumerate(block.get("lines", [])):
            for span_no, span in enumerate(line.get("spans", [])):
                for char_no, char in enumerate(span.get("chars", [])):
                    c = char["c"]
                    if not c or c.isspace():
                        continue
                    glyph_seq += 1
                    atoms.append(
                        {
                            "atom_id": f"GLYPH-{glyph_seq:03d}",
                            "kind": "VISIBLE_GLYPH",
                            "char": c,
                            "bbox_pt": [round(v, 3) for v in char["bbox"]],
                            "source_locator": f"rawdict:block={block_no},line={line_no},span={span_no},char={char_no}",
                            "font": span["font"],
                            "size_pt": round(span["size"], 3),
                        }
                    )

    foreground_drawings = [15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 27]
    drawings = page.get_drawings()
    for path_seq, draw_no in enumerate(foreground_drawings, start=1):
        drawing = drawings[draw_no]
        atoms.append(
            {
                "atom_id": f"PATH-{path_seq:03d}",
                "kind": "FOREGROUND_PAINTED_PATH",
                "pdf_drawing_index": draw_no,
                "bbox_pt": [round(v, 3) for v in drawing["rect"]],
                "stroke": drawing.get("color"),
                "fill": drawing.get("fill"),
                "width_pt": drawing.get("width"),
                "dash": drawing.get("dashes"),
                "pdf_path_item_count": len(drawing.get("items", [])),
                "atomicity_note": "One PDF painted path (one get_drawings entry); internal line/curve commands share a single paint operation and are not merged with another painted path.",
            }
        )

    exclusions = [
        {
            "pdf_drawing_index": 14,
            "reason": "BACKGROUND_EXCLUSION: pale filled subspace field; no foreground stroke in this paint object.",
        },
        {
            "pdf_drawing_index": 23,
            "reason": "BACKGROUND_EXCLUSION: white residual-label knockout mask; no visible foreground stroke.",
        },
        {
            "pdf_drawing_index": 26,
            "reason": "BACKGROUND_EXCLUSION: white distance-label knockout mask; no visible foreground stroke.",
        },
    ]
    return {
        "figure_uid": "FIG-P033-01",
        "pdf_physical_page": PAGE_INDEX + 1,
        "atomicity_rule": "Every non-whitespace rendered glyph is a separate atom. Every foreground PDF paint path is a separate atom. No semantic text/path grouping is used.",
        "background_exclusions": exclusions,
        "glyph_count": glyph_seq,
        "foreground_path_count": len(foreground_drawings),
        "atom_count": len(atoms),
        "unordered_pair_count": len(atoms) * (len(atoms) - 1) // 2,
        "atoms": atoms,
    }


def write_machine_pair_inventory(atoms: list[dict[str, object]]) -> None:
    fields = [
        "PAIR_ID",
        "ATOM_A",
        "ATOM_B",
        "BBOX_INTERSECTS",
        "BBOX_GAP_PX",
        "REVIEWER",
        "OBSERVED",
        "DECISION",
        "NOTE",
        "PASS",
    ]
    with (ROOT / "machine_all_unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for idx, (a, b) in enumerate(itertools.combinations(atoms, 2), start=1):
            ra = fitz.Rect(a["bbox_pt"])
            rb = fitz.Rect(b["bbox_pt"])
            dx = max(rb.x0 - ra.x1, ra.x0 - rb.x1, 0.0)
            dy = max(rb.y0 - ra.y1, ra.y0 - rb.y1, 0.0)
            gap = (dx * dx + dy * dy) ** 0.5 * SCALE
            writer.writerow(
                {
                    "PAIR_ID": f"PAIR-{idx:03d}",
                    "ATOM_A": a["atom_id"],
                    "ATOM_B": b["atom_id"],
                    "BBOX_INTERSECTS": str(ra.intersects(rb)).lower(),
                    "BBOX_GAP_PX": f"{gap:.2f}",
                    # Deliberately blank: manual adjudication is never generated here.
                    "REVIEWER": "",
                    "OBSERVED": "",
                    "DECISION": "",
                    "NOTE": "",
                    "PASS": "",
                }
            )


def write_atomic_overlay(atoms: list[dict[str, object]]) -> None:
    image = Image.open(ROOT / "R111_p029_FIG-P033-01_with_caption_native300dpi.png").convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    xoff, yoff = FIGURE_WITH_CAPTION_CLIP_PT.x0, FIGURE_WITH_CAPTION_CLIP_PT.y0
    for atom in atoms:
        x0, y0, x1, y1 = atom["bbox_pt"]
        box = tuple(int(round((v - off) * SCALE)) for v, off in zip((x0, y0, x1, y1), (xoff, yoff, xoff, yoff)))
        color = (198, 35, 35) if atom["kind"] == "VISIBLE_GLYPH" else (20, 105, 190)
        draw.rectangle(box, outline=color, width=1)
        draw.text((box[0], max(0, box[1] - 10)), atom["atom_id"], fill=color, font=font)
    image.save(ROOT / "machine_strict_atomic_overlay_native1x.png", dpi=(300, 300))

    # Nearest-neighbour enlarged caption/body strips preserve the original raster.
    source = Image.open(ROOT / "R111_p029_FIG-P033-01_with_caption_native300dpi.png").convert("RGB")
    roi_specs = {
        "roi_X_origin_and_labels": (450, 120, 1150, 680),
        "roi_P_residual_right_angle": (900, 120, 1450, 610),
        "roi_norm_note": (1190, 0, 1600, 180),
        "roi_subspace_label": (430, 610, 720, 835),
        "roi_caption": (0, 745, source.width, min(source.height, 840)),
    }
    for stem, raw_box in roi_specs.items():
        x0, y0, x1, y1 = raw_box
        x0 = max(0, min(source.width, x0)); x1 = max(0, min(source.width, x1))
        y0 = max(0, min(source.height, y0)); y1 = max(0, min(source.height, y1))
        roi = source.crop((x0, y0, x1, y1))
        roi.save(ROOT / f"{stem}_native1x.png", dpi=(300, 300))
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
            ROOT / f"{stem}_nearest_neighbor8x.png", dpi=(2400, 2400)
        )


def write_glyph_metrics(strict: dict[str, object]) -> None:
    fields = [
        "ATOM_ID",
        "CHAR",
        "FONT",
        "SIZE_PT",
        "BBOX_WIDTH_PX",
        "BBOX_HEIGHT_PX",
        "PAGE_CLIPPED",
        "REVIEWER",
        "OBSERVED",
        "DECISION",
        "NOTE",
        "PASS",
    ]
    with (ROOT / "machine_glyph_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for atom in strict["atoms"]:
            if atom["kind"] != "VISIBLE_GLYPH":
                continue
            x0, y0, x1, y1 = atom["bbox_pt"]
            clipped = x0 < 0 or y0 < 0 or x1 > 595.2761 or y1 > 841.8901
            writer.writerow(
                {
                    "ATOM_ID": atom["atom_id"],
                    "CHAR": atom["char"],
                    "FONT": atom["font"],
                    "SIZE_PT": atom["size_pt"],
                    "BBOX_WIDTH_PX": f"{(x1 - x0) * SCALE:.2f}",
                    "BBOX_HEIGHT_PX": f"{(y1 - y0) * SCALE:.2f}",
                    "PAGE_CLIPPED": str(clipped).lower(),
                    "REVIEWER": "",
                    "OBSERVED": "",
                    "DECISION": "",
                    "NOTE": "",
                    "PASS": "",
                }
            )


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    render_info = render()
    (ROOT / "machine_render_contract.json").write_text(
        json.dumps(render_info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    objects = extract_pdf_objects()
    (ROOT / "machine_pdf_objects.json").write_text(
        json.dumps(objects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    strict = strict_atomic_candidates()
    (ROOT / "machine_strict_atomic_candidates.json").write_text(
        json.dumps(strict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_machine_pair_inventory(strict["atoms"])
    write_atomic_overlay(strict["atoms"])
    write_glyph_metrics(strict)


if __name__ == "__main__":
    main()
