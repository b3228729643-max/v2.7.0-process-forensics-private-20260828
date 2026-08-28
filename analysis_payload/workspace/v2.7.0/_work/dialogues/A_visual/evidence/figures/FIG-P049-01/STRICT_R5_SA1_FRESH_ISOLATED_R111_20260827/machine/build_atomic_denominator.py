from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r111_fullbook\main_full.pdf"
)
ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence"
    r"\figures\FIG-P049-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827"
)
MACHINE = ROOT / "machine"
VISUAL = ROOT / "visual"
PAGE_INDEX_ZERO = 47
BODY_PT = fitz.Rect(138.0, 60.0, 465.0, 230.0)
CAPTION_PT = fitz.Rect(126.0, 230.0, 481.0, 247.0)
FULL_SCOPE_PT = fitz.Rect(
    min(BODY_PT.x0, CAPTION_PT.x0),
    min(BODY_PT.y0, CAPTION_PT.y0),
    max(BODY_PT.x1, CAPTION_PT.x1),
    max(BODY_PT.y1, CAPTION_PT.y1),
)
SCALE = 300.0 / 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def point_xy(value):
    if isinstance(value, fitz.Point):
        return [round(value.x, 5), round(value.y, 5)]
    if isinstance(value, fitz.Rect):
        return [round(value.x0, 5), round(value.y0, 5), round(value.x1, 5), round(value.y1, 5)]
    if isinstance(value, fitz.Quad):
        return [point_xy(p) for p in (value.ul, value.ur, value.ll, value.lr)]
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    return str(value)


def item_serialized(item):
    return [point_xy(x) for x in item]


def bbox_hits_scope(rect: fitz.Rect) -> bool:
    # Inclusive check is intentional: zero-height/zero-width strokes such as axis lines
    # are foreground and must not disappear through an area-only intersection predicate.
    return not (
        rect.x1 < BODY_PT.x0
        or rect.x0 > BODY_PT.x1
        or rect.y1 < BODY_PT.y0
        or rect.y0 > BODY_PT.y1
    )


def rect_list(rect: fitz.Rect):
    return [round(rect.x0, 5), round(rect.y0, 5), round(rect.x1, 5), round(rect.y1, 5)]


def px_bbox(rect: fitz.Rect, scope: fitz.Rect):
    return [
        round((rect.x0 - scope.x0) * SCALE, 3),
        round((rect.y0 - scope.y0) * SCALE, 3),
        round((rect.x1 - scope.x0) * SCALE, 3),
        round((rect.y1 - scope.y0) * SCALE, 3),
    ]


def visible_char_rows(page: fitz.Page):
    rows = []
    raw = page.get_text("rawdict", sort=True)
    for block_index, block in enumerate(raw.get("blocks", []), start=1):
        if block.get("type") != 0:
            continue
        for line_index, line in enumerate(block.get("lines", []), start=1):
            for span_index, span in enumerate(line.get("spans", []), start=1):
                for char_index, char in enumerate(span.get("chars", []), start=1):
                    c = char.get("c", "")
                    if not c or c.isspace():
                        continue
                    rect = fitz.Rect(char["bbox"])
                    center = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
                    if BODY_PT.contains(center):
                        region = "FIGURE_BODY"
                        scope = BODY_PT
                    elif CAPTION_PT.contains(center):
                        region = "CAPTION"
                        scope = FULL_SCOPE_PT
                    else:
                        continue
                    rows.append(
                        {
                            "region": region,
                            "unicode": c,
                            "codepoints": "+".join(f"U+{ord(ch):04X}" for ch in c),
                            "pdf_bbox_pt": rect_list(rect),
                            "scope_bbox_px_300dpi": px_bbox(rect, scope),
                            "origin_pt": [round(x, 5) for x in char.get("origin", (math.nan, math.nan))],
                            "font": span.get("font", ""),
                            "font_size_pt_pdf": round(float(span.get("size", math.nan)), 5),
                            "font_flags": span.get("flags"),
                            "font_color_srgb": span.get("color"),
                            "block_index": block_index,
                            "line_index": line_index,
                            "span_index": span_index,
                            "char_index": char_index,
                        }
                    )
    return rows


def is_background_exclusion(drawing: dict) -> tuple[bool, str]:
    color = drawing.get("color")
    fill = drawing.get("fill")
    fill_opacity = drawing.get("fill_opacity")
    items = drawing.get("items", [])
    only_rect = len(items) == 1 and items[0][0] == "re"
    white_fill = fill is not None and all(abs(float(v) - 1.0) < 1e-6 for v in fill)
    no_visible_stroke = color is None
    if only_rect and white_fill and no_visible_stroke and fill_opacity is not None:
        return (
            True,
            "OPAQUE_OR_SEMITRANSPARENT_WHITE_LABEL_BACKGROUND; non-semantic backing plate; "
            "excluded from foreground denominator but retained in explicit exclusion ledger",
        )
    return False, ""


def drawing_rows(page: fitz.Page):
    included, excluded = [], []
    for drawing_index, drawing in enumerate(page.get_drawings(), start=1):
        rect = drawing["rect"]
        if not bbox_hits_scope(rect):
            continue
        is_bg, reason = is_background_exclusion(drawing)
        base = {
            "pdf_drawing_index": drawing_index,
            "pdf_seqno": drawing.get("seqno"),
            "paint_type": drawing.get("type"),
            "pdf_bbox_pt": rect_list(rect),
            "body_bbox_px_300dpi": px_bbox(rect, BODY_PT),
            "path_item_count": len(drawing.get("items", [])),
            "path_items": [item_serialized(item) for item in drawing.get("items", [])],
            "stroke_width_pt": drawing.get("width"),
            "stroke_color": drawing.get("color"),
            "fill_color": drawing.get("fill"),
            "stroke_opacity": drawing.get("stroke_opacity"),
            "fill_opacity": drawing.get("fill_opacity"),
            "dashes": drawing.get("dashes"),
            "close_path": drawing.get("closePath"),
            "layer": drawing.get("layer"),
        }
        if is_bg:
            base["schema_exclusion_code"] = "BG-LABEL-PLATE"
            base["schema_exclusion_reason"] = reason
            excluded.append(base)
        else:
            included.append(base)
    return included, excluded


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    MACHINE.mkdir(parents=True, exist_ok=True)
    VISUAL.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX_ZERO]
    glyphs = visible_char_rows(page)
    foreground_paths, exclusions = drawing_rows(page)

    atoms = []
    for index, glyph in enumerate(glyphs, start=1):
        atom = {
            "atom_id": f"G-{index:03d}",
            "atom_class": "VISIBLE_GLYPH",
            "region": glyph["region"],
            "display": glyph["unicode"],
            "machine_source_ref": (
                f"PDF page {PAGE_INDEX_ZERO + 1}; rawdict block={glyph['block_index']}; "
                f"line={glyph['line_index']}; span={glyph['span_index']}; char={glyph['char_index']}"
            ),
            "pdf_bbox_pt": json.dumps(glyph["pdf_bbox_pt"], ensure_ascii=False),
            "scope_bbox_px_300dpi": json.dumps(glyph["scope_bbox_px_300dpi"], ensure_ascii=False),
            "machine_payload": json.dumps(glyph, ensure_ascii=False, separators=(",", ":")),
        }
        atoms.append(atom)
    for index, path in enumerate(foreground_paths, start=1):
        atom = {
            "atom_id": f"P-{index:03d}",
            "atom_class": "FOREGROUND_PDF_PATH",
            "region": "FIGURE_BODY",
            "display": f"drawing#{path['pdf_drawing_index']}/seq#{path['pdf_seqno']}",
            "machine_source_ref": f"PDF page {PAGE_INDEX_ZERO + 1}; get_drawings index={path['pdf_drawing_index']}",
            "pdf_bbox_pt": json.dumps(path["pdf_bbox_pt"], ensure_ascii=False),
            "scope_bbox_px_300dpi": json.dumps(path["body_bbox_px_300dpi"], ensure_ascii=False),
            "machine_payload": json.dumps(path, ensure_ascii=False, separators=(",", ":")),
        }
        atoms.append(atom)

    atom_fields = [
        "atom_id",
        "atom_class",
        "region",
        "display",
        "machine_source_ref",
        "pdf_bbox_pt",
        "scope_bbox_px_300dpi",
        "machine_payload",
    ]
    write_csv(MACHINE / "atomic_denominator_machine.csv", atoms, atom_fields)

    exclusion_rows = []
    for index, path in enumerate(exclusions, start=1):
        exclusion_rows.append(
            {
                "exclusion_id": f"X-{index:03d}",
                "object_class": "PDF_PATH",
                "pdf_drawing_index": path["pdf_drawing_index"],
                "pdf_seqno": path["pdf_seqno"],
                "pdf_bbox_pt": json.dumps(path["pdf_bbox_pt"], ensure_ascii=False),
                "path_item_count": path["path_item_count"],
                "machine_payload": json.dumps(path, ensure_ascii=False, separators=(",", ":")),
                "schema_exclusion_code": path["schema_exclusion_code"],
                "schema_exclusion_reason": path["schema_exclusion_reason"],
            }
        )
    write_csv(
        MACHINE / "background_exclusions_machine.csv",
        exclusion_rows,
        [
            "exclusion_id",
            "object_class",
            "pdf_drawing_index",
            "pdf_seqno",
            "pdf_bbox_pt",
            "path_item_count",
            "machine_payload",
            "schema_exclusion_code",
            "schema_exclusion_reason",
        ],
    )

    pair_fields = ["pair_id", "atom_id_a", "atom_id_b", "unordered_key"]
    pair_path = MACHINE / "all_unordered_pairs_machine.csv"
    pair_count = 0
    with pair_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=pair_fields)
        writer.writeheader()
        for pair_count, (a, b) in enumerate(itertools.combinations(atoms, 2), start=1):
            writer.writerow(
                {
                    "pair_id": f"PAIR-{pair_count:06d}",
                    "atom_id_a": a["atom_id"],
                    "atom_id_b": b["atom_id"],
                    "unordered_key": f"{a['atom_id']}|{b['atom_id']}",
                }
            )

    # Machine visualization. This draws identifiers only and does not write reviewer,
    # observed, decision, note, or PASS/FAIL data.
    pix = page.get_pixmap(dpi=300, colorspace=fitz.csRGB, alpha=False, clip=FULL_SCOPE_PT)
    base_path = VISUAL / "07_atomic_scope_native300dpi_native1x.png"
    pix.save(base_path)
    with Image.open(base_path) as base_image:
        overlay = base_image.convert("RGB")
        draw = ImageDraw.Draw(overlay)
        font = ImageFont.load_default()
        for atom in atoms:
            rect = fitz.Rect(json.loads(atom["pdf_bbox_pt"]))
            coords = px_bbox(rect, FULL_SCOPE_PT)
            color = (208, 0, 0) if atom["atom_class"] == "VISIBLE_GLYPH" else (0, 70, 210)
            draw.rectangle(coords, outline=color, width=1)
            draw.text((coords[0] + 1, max(0, coords[1] - 10)), atom["atom_id"], fill=color, font=font)
        overlay_path = VISUAL / "08_atomic_id_overlay_native300dpi.png"
        overlay.save(overlay_path)
        overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(
            VISUAL / "09_atomic_id_overlay_nearest_neighbor8x.png"
        )

    manifest = {
        "schema": "DIRECT_STRICT_ATOMIC_DENOMINATOR_V1",
        "source_pdf_sha256": sha256(PDF),
        "physical_page_1based": PAGE_INDEX_ZERO + 1,
        "figure_body_bbox_pt": rect_list(BODY_PT),
        "caption_bbox_pt": rect_list(CAPTION_PT),
        "scope_rule": "Every non-whitespace raw PDF glyph whose bbox center is within BODY_PT or CAPTION_PT, plus every PDF display-list drawing path whose bbox inclusively meets BODY_PT. Zero-height/width strokes are included. Only listed white label backing paths are excluded as non-semantic backgrounds.",
        "foreground_path_atomicity": "One atom per PDF display-list drawing/painting operation (get_drawings record); constituent line/curve items are retained losslessly in machine_payload and path_item_count, so no primitive is omitted.",
        "glyph_count": len(glyphs),
        "foreground_path_count": len(foreground_paths),
        "background_exclusion_count": len(exclusions),
        "N": len(atoms),
        "expected_C_N_choose_2": len(atoms) * (len(atoms) - 1) // 2,
        "actual_pair_rows": pair_count,
        "pair_count_matches": pair_count == len(atoms) * (len(atoms) - 1) // 2,
        "manual_fields_in_machine_outputs": [],
        "manual_judgment_values_in_machine_outputs": False,
        "files": {},
    }
    for path in [
        MACHINE / "atomic_denominator_machine.csv",
        MACHINE / "background_exclusions_machine.csv",
        pair_path,
        base_path,
        VISUAL / "08_atomic_id_overlay_native300dpi.png",
        VISUAL / "09_atomic_id_overlay_nearest_neighbor8x.png",
    ]:
        manifest["files"][path.relative_to(ROOT).as_posix()] = {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    (MACHINE / "atomic_denominator_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
