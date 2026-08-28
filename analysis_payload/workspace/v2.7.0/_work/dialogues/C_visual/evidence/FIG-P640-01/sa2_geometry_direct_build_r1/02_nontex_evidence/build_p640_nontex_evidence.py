from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
PDF = ROOT / "01_build" / "v260_FIG-P640-01_standalone.pdf"
DPI = 300
SCALE = DPI / 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def union_rect(rects: list[fitz.Rect]) -> fitz.Rect:
    if not rects:
        raise ValueError("empty rect list")
    r = fitz.Rect(rects[0])
    for item in rects[1:]:
        r.include_rect(item)
    return r


def text_parts(page_dict: dict, selectors: list[tuple[int, int | None]]) -> tuple[str, fitz.Rect]:
    texts: list[str] = []
    rects: list[fitz.Rect] = []
    blocks = page_dict["blocks"]
    for block_index, line_index in selectors:
        block = blocks[block_index]
        lines = block.get("lines", [])
        chosen = lines if line_index is None else [lines[line_index]]
        for line in chosen:
            line_text = "".join(span["text"] for span in line["spans"])
            texts.append(line_text)
            rects.extend(fitz.Rect(span["bbox"]) for span in line["spans"])
    return " / ".join(texts), union_rect(rects)


def rect_row(r: fitz.Rect) -> dict[str, float]:
    return {
        "x0_pt": round(r.x0, 6),
        "y0_pt": round(r.y0, 6),
        "x1_pt": round(r.x1, 6),
        "y1_pt": round(r.y1, 6),
        "width_pt": round(r.width, 6),
        "height_pt": round(r.height, 6),
    }


def bbox_metrics(a: fitz.Rect, b: fitz.Rect) -> dict[str, float | int]:
    ix = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
    iy = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
    if ix > 0.0 and iy > 0.0:
        gap = 0.0
    else:
        dx = max(a.x0 - b.x1, b.x0 - a.x1, 0.0)
        dy = max(a.y0 - b.y1, b.y0 - a.y1, 0.0)
        gap = math.hypot(dx, dy)
    return {
        "bbox_intersection_width_pt": round(ix, 6),
        "bbox_intersection_height_pt": round(iy, 6),
        "bbox_intersection_area_pt2": round(ix * iy, 6),
        "bbox_gap_pt": round(gap, 6),
    }


def px(point: fitz.Point) -> tuple[int, int]:
    return round(point.x * SCALE), round(point.y * SCALE)


def rect_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        round(rect.x0 * SCALE),
        round(rect.y0 * SCALE),
        round(rect.x1 * SCALE),
        round(rect.y1 * SCALE),
    )


def render_drawing_mask(page: fitz.Page, drawing_indexes: list[int], out_path: Path) -> np.ndarray:
    width, height = Image.open(OUT / "standalone_native_300dpi.png").size
    image = Image.new("L", (width, height), 0)
    pen = ImageDraw.Draw(image)
    drawings = page.get_drawings()
    for drawing_index in drawing_indexes:
        d = drawings[drawing_index]
        stroke_width = max(1, round((d.get("width") or 0.55) * SCALE))
        polygon_points: list[tuple[int, int]] = []
        for item in d["items"]:
            op = item[0]
            if op == "l":
                pen.line([px(item[1]), px(item[2])], fill=255, width=stroke_width)
                polygon_points.extend([px(item[1]), px(item[2])])
            elif op == "re":
                r = fitz.Rect(item[1])
                if d.get("fill") is not None:
                    pen.rectangle(rect_px(r), fill=255)
                else:
                    pen.rectangle(rect_px(r), outline=255, width=stroke_width)
            elif op == "c":
                # The only cubic path used by the target object is the marker ring.
                # Its PDF drawing rectangle is the exact enclosing ellipse.
                pass
        if any(item[0] == "c" for item in d["items"]):
            r = fitz.Rect(d["rect"])
            if d.get("fill") is not None:
                pen.ellipse(rect_px(r), fill=255)
            if d.get("color") is not None:
                pen.ellipse(rect_px(r), outline=255, width=stroke_width)
        elif d.get("fill") is not None and polygon_points:
            pen.polygon(polygon_points, fill=255)
    image.save(out_path)
    return np.asarray(image, dtype=np.uint8) > 0


def crop_with_box(image: Image.Image, box: tuple[int, int, int, int], path: Path) -> None:
    image.crop(box).save(path)


def build_contact_sheets(
    base: Image.Image,
    entries: list[dict],
    object_lookup: dict[str, dict],
    prefix: str,
) -> None:
    cols, rows = 4, 4
    tile_w, tile_h = 480, 300
    per_sheet = cols * rows
    for sheet_no, start in enumerate(range(0, len(entries), per_sheet), 1):
        canvas = Image.new("RGB", (cols * tile_w, rows * tile_h), "white")
        for offset, entry in enumerate(entries[start : start + per_sheet]):
            col, row = offset % cols, offset // cols
            object_ids = entry["object_ids"]
            rects = [
                fitz.Rect(
                    object_lookup[oid]["x0_pt"], object_lookup[oid]["y0_pt"],
                    object_lookup[oid]["x1_pt"], object_lookup[oid]["y1_pt"],
                )
                for oid in object_ids
            ]
            u = union_rect(rects)
            pad_pt = max(10.0, min(26.0, max(u.width, u.height) * 0.35))
            crop_rect = fitz.Rect(
                max(0.0, u.x0 - pad_pt), max(0.0, u.y0 - pad_pt),
                min(595.276, u.x1 + pad_pt), min(841.89, u.y1 + pad_pt),
            )
            crop_box = rect_px(crop_rect)
            tile_source = base.crop(crop_box)
            source_draw = ImageDraw.Draw(tile_source)
            colors = [(0, 110, 255), (255, 0, 170)]
            for object_no, (oid, r) in enumerate(zip(object_ids, rects)):
                local = (
                    round(r.x0 * SCALE) - crop_box[0], round(r.y0 * SCALE) - crop_box[1],
                    round(r.x1 * SCALE) - crop_box[0], round(r.y1 * SCALE) - crop_box[1],
                )
                source_draw.rectangle(local, outline=colors[object_no % 2], width=3)
            header_h = 42
            content_h = tile_h - header_h
            ratio = min(tile_w / max(1, tile_source.width), content_h / max(1, tile_source.height))
            resized = tile_source.resize(
                (max(1, round(tile_source.width * ratio)), max(1, round(tile_source.height * ratio))),
                Image.Resampling.LANCZOS,
            )
            tile = Image.new("RGB", (tile_w, tile_h), "white")
            tx = (tile_w - resized.width) // 2
            ty = header_h + (content_h - resized.height) // 2
            tile.paste(resized, (tx, ty))
            d = ImageDraw.Draw(tile)
            d.text((8, 5), entry["header"], fill="black")
            d.text((8, 22), " / ".join(object_ids), fill="black")
            canvas.paste(tile, (col * tile_w, row * tile_h))
        canvas.save(OUT / f"{prefix}_{sheet_no:02d}.png")


def main() -> None:
    doc = fitz.open(PDF)
    if doc.page_count != 1:
        raise RuntimeError(f"expected one page, got {doc.page_count}")
    page = doc[0]
    page_dict = page.get_text("dict")
    raw = page.get_text("rawdict")
    drawings = page.get_drawings()
    if len(drawings) != 19:
        raise RuntimeError(f"drawing denominator drift: {len(drawings)} != 19")

    glyph_rows: list[dict] = []
    glyph_no = 0
    for bi, block in enumerate(raw["blocks"]):
        for li, line in enumerate(block.get("lines", [])):
            for si, span in enumerate(line.get("spans", [])):
                for ci, char in enumerate(span.get("chars", [])):
                    glyph_no += 1
                    r = fitz.Rect(char["bbox"])
                    glyph_rows.append(
                        {
                            "glyph_id": f"GLYPH_{glyph_no:04d}",
                            "block_index": bi,
                            "line_index": li,
                            "span_index": si,
                            "char_index": ci,
                            "character": char["c"],
                            "codepoint": f"U+{ord(char['c']):04X}",
                            "is_space": int(char["c"].isspace()),
                            "font": span["font"],
                            "font_size_pt": round(span["size"], 6),
                            **rect_row(r),
                        }
                    )
    if glyph_no != 160:
        raise RuntimeError(f"glyph denominator drift: {glyph_no} != 160")
    write_csv(
        OUT / "machine_glyph_inventory.csv",
        glyph_rows,
        [
            "glyph_id", "block_index", "line_index", "span_index", "char_index",
            "character", "codepoint", "is_space", "font", "font_size_pt",
            "x0_pt", "y0_pt", "x1_pt", "y1_pt", "width_pt", "height_pt",
        ],
    )

    specs: list[tuple[str, str, list[tuple[int, int | None]]]] = []
    for i in range(7):
        specs.append((f"T{i + 1:03d}", f"left_x_tick_{i}", [(0, i)]))
    specs.extend(
        [
            ("T008", "left_y_tick_0", [(0, 7)]),
            ("T009", "left_y_tick_025", [(1, 0)]),
            ("T010", "left_y_tick_05", [(2, 0)]),
            ("T011", "left_y_tick_075", [(3, 0)]),
            ("T012", "left_y_tick_1", [(4, 0)]),
            ("T013", "left_x_axis_label", [(5, None)]),
            ("T014", "left_y_axis_formula", [(6, None), (7, None)]),
            ("T015", "left_panel_title", [(8, None)]),
            ("T016", "legend_rho_095", [(9, 0)]),
            ("T017", "legend_rho_070", [(9, 1)]),
            ("T018", "legend_rho_020", [(9, 2)]),
            ("T019", "right_x_tick_0", [(10, 0)]),
            ("T020", "right_x_tick_05", [(10, 1)]),
            ("T021", "right_x_tick_099", [(10, 2)]),
            ("T022", "right_y_tick_0", [(10, 3)]),
            ("T023", "right_y_tick_05", [(11, 0)]),
            ("T024", "right_y_tick_1", [(12, 0)]),
            ("T025", "right_point_label", [(13, None)]),
            ("T026", "right_limit_note", [(14, None)]),
            ("T027", "right_x_axis_label", [(15, None)]),
            ("T028", "right_y_axis_label", [(16, None)]),
            ("T029", "right_panel_title", [(17, None)]),
            ("T030", "right_title_formula", [(18, None), (19, None)]),
        ]
    )
    if len(specs) != 30:
        raise RuntimeError("text object spec must contain 30 items")

    objects: list[dict] = []
    for object_id, semantic_name, selectors in specs:
        text, r = text_parts(page_dict, selectors)
        if object_id == "T030":
            r.include_rect(drawings[18]["rect"])
        objects.append(
            {
                "object_id": object_id,
                "object_kind": "TEXT",
                "semantic_name": semantic_name,
                "source_member": ";".join(f"block={b},line={'ALL' if l is None else l}" for b, l in selectors),
                "extracted_text": text,
                **rect_row(r),
            }
        )

    vector_specs = [
        ("G01", "left_axes_and_ticks", [0, 1, 2]),
        ("G02", "left_curve_rho_095", [3]),
        ("G03", "left_curve_rho_070", [4]),
        ("G04", "left_curve_rho_020", [5]),
        ("G05", "legend_sample_rho_095", [6]),
        ("G06", "legend_sample_rho_070", [7]),
        ("G07", "legend_sample_rho_020", [8]),
        ("G08", "right_axes_ticks_and_arrows", [9, 10, 11, 12, 13, 14]),
        ("G09", "right_efficiency_curve", [15]),
        ("G10", "right_true_point_marker", [17]),
    ]
    for object_id, semantic_name, indexes in vector_specs:
        r = union_rect([fitz.Rect(drawings[i]["rect"]) for i in indexes])
        objects.append(
            {
                "object_id": object_id,
                "object_kind": "VECTOR",
                "semantic_name": semantic_name,
                "source_member": ",".join(f"drawing={i}" for i in indexes),
                "extracted_text": "",
                **rect_row(r),
            }
        )
    if len(objects) != 40 or len({o["object_id"] for o in objects}) != 40:
        raise RuntimeError("object denominator must be 40 unique objects")
    object_fields = [
        "object_id", "object_kind", "semantic_name", "source_member", "extracted_text",
        "x0_pt", "y0_pt", "x1_pt", "y1_pt", "width_pt", "height_pt",
    ]
    write_csv(OUT / "machine_object_inventory.csv", objects, object_fields)

    pair_rows: list[dict] = []
    critical_rows: list[dict] = []
    pair_no = 0
    for a, b in itertools.combinations(objects, 2):
        pair_no += 1
        ar = fitz.Rect(a["x0_pt"], a["y0_pt"], a["x1_pt"], a["y1_pt"])
        br = fitz.Rect(b["x0_pt"], b["y0_pt"], b["x1_pt"], b["y1_pt"])
        metrics = bbox_metrics(ar, br)
        row = {
            "pair_id": f"PAIR_{pair_no:04d}",
            "object_a": a["object_id"],
            "object_b": b["object_id"],
            "kind_a": a["object_kind"],
            "kind_b": b["object_kind"],
            **metrics,
        }
        pair_rows.append(row)
        if metrics["bbox_intersection_area_pt2"] > 0 or metrics["bbox_gap_pt"] <= 8.0:
            critical_rows.append(
                {
                    "critical_id": f"CRIT_{len(critical_rows) + 1:03d}",
                    "selection_basis": "BBOX_INTERSECTION" if metrics["bbox_intersection_area_pt2"] > 0 else "BBOX_GAP_LE_8PT",
                    **row,
                }
            )
    if pair_no != 780 or len({r["pair_id"] for r in pair_rows}) != 780:
        raise RuntimeError(f"pair denominator drift: {pair_no} != 780")
    pair_fields = [
        "pair_id", "object_a", "object_b", "kind_a", "kind_b",
        "bbox_intersection_width_pt", "bbox_intersection_height_pt",
        "bbox_intersection_area_pt2", "bbox_gap_pt",
    ]
    write_csv(OUT / "machine_pair_inventory.csv", pair_rows, pair_fields)
    write_csv(
        OUT / "machine_critical_pair_inventory.csv",
        critical_rows,
        ["critical_id", "selection_basis", *pair_fields],
    )

    clip_rows: list[dict] = []
    for o in objects:
        clip_rows.append(
            {
                "object_id": o["object_id"],
                "distance_left_pt": round(float(o["x0_pt"]), 6),
                "distance_top_pt": round(float(o["y0_pt"]), 6),
                "distance_right_pt": round(page.rect.width - float(o["x1_pt"]), 6),
                "distance_bottom_pt": round(page.rect.height - float(o["y1_pt"]), 6),
                "min_page_edge_distance_pt": round(
                    min(
                        float(o["x0_pt"]), float(o["y0_pt"]),
                        page.rect.width - float(o["x1_pt"]),
                        page.rect.height - float(o["y1_pt"]),
                    ),
                    6,
                ),
            }
        )
    write_csv(
        OUT / "machine_clip_inventory.csv",
        clip_rows,
        [
            "object_id", "distance_left_pt", "distance_top_pt", "distance_right_pt",
            "distance_bottom_pt", "min_page_edge_distance_pt",
        ],
    )

    axis_mask = render_drawing_mask(page, [9, 10, 11, 12, 13, 14], OUT / "pair_0779_axis_mask_300dpi.png")
    marker_mask = render_drawing_mask(page, [17], OUT / "pair_0779_marker_mask_300dpi.png")
    overlap = axis_mask & marker_mask
    overlap_image = Image.fromarray((overlap.astype(np.uint8) * 255), mode="L")
    overlap_image.save(OUT / "pair_0779_overlap_mask_300dpi.png")
    yy, xx = np.where(overlap)
    overlap_count = int(overlap.sum())
    if overlap_count:
        overlap_bbox = [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())]
    else:
        overlap_bbox = None

    native_path = OUT / "standalone_native_300dpi.png"
    native = Image.open(native_path).convert("RGB")
    overlay = native.copy()
    overlay_np = np.asarray(overlay).copy()
    overlay_np[axis_mask] = [0, 120, 255]
    overlay_np[marker_mask] = [255, 174, 0]
    overlay_np[overlap] = [255, 0, 255]
    overlay = Image.fromarray(overlay_np)
    overlay.save(OUT / "pair_0779_overlay_300dpi.png")

    marker_rect_px = rect_px(fitz.Rect(drawings[17]["rect"]))
    cx = (marker_rect_px[0] + marker_rect_px[2]) // 2
    cy = (marker_rect_px[1] + marker_rect_px[3]) // 2
    box_1x = (cx - 70, cy - 70, cx + 70, cy + 70)
    crop_with_box(native, box_1x, OUT / "pair_0779_native_1x.png")
    crop_with_box(overlay, box_1x, OUT / "pair_0779_overlay_1x.png")
    crop_with_box(native, box_1x, OUT / "pair_0779_native_8x_source.png")
    Image.open(OUT / "pair_0779_native_8x_source.png").resize((1120, 1120), Image.Resampling.NEAREST).save(
        OUT / "pair_0779_native_8x.png"
    )
    crop_with_box(overlay, box_1x, OUT / "pair_0779_overlay_8x_source.png")
    Image.open(OUT / "pair_0779_overlay_8x_source.png").resize((1120, 1120), Image.Resampling.NEAREST).save(
        OUT / "pair_0779_overlay_8x.png"
    )
    (OUT / "pair_0779_native_8x_source.png").unlink()
    (OUT / "pair_0779_overlay_8x_source.png").unlink()

    figure_rect = fitz.Rect(90, 60, 520, 265)
    right_rect = fitz.Rect(365, 60, 520, 225)
    crop_with_box(native, rect_px(figure_rect), OUT / "figure_crop_native_300dpi.png")
    crop_with_box(native, rect_px(right_rect), OUT / "right_panel_native_300dpi.png")
    crop_with_box(Image.open(OUT / "standalone_grayscale_300dpi.png").convert("RGB"), rect_px(figure_rect), OUT / "figure_crop_grayscale_300dpi.png")

    object_lookup = {o["object_id"]: o for o in objects}
    build_contact_sheets(
        native,
        [
            {"header": f"OBJECT {o['object_id']} {o['semantic_name']}", "object_ids": [o["object_id"]]}
            for o in objects
        ],
        object_lookup,
        "object_contact_sheet",
    )
    build_contact_sheets(
        native,
        [
            {
                "header": f"{r['critical_id']} {r['pair_id']} {r['selection_basis']}",
                "object_ids": [r["object_a"], r["object_b"]],
            }
            for r in critical_rows
        ],
        object_lookup,
        "critical_pair_contact_sheet",
    )

    pair_0779 = pair_rows[778]
    if pair_0779["pair_id"] != "PAIR_0779" or {pair_0779["object_a"], pair_0779["object_b"]} != {"G08", "G10"}:
        raise RuntimeError(f"PAIR_0779 mapping drift: {pair_0779}")
    regression = {
        "evidence_kind": "NON_TEX_GEOMETRY_REGRESSION",
        "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
        "page_count": doc.page_count,
        "page_width_pt": page.rect.width,
        "page_height_pt": page.rect.height,
        "render_dpi": DPI,
        "object_denominator": len(objects),
        "glyph_denominator_total_including_spaces": glyph_no,
        "glyph_denominator_nonspace": sum(1 for r in glyph_rows if not r["is_space"]),
        "unordered_pair_denominator": pair_no,
        "critical_selection": "all bbox intersections plus bbox gap <= 8pt",
        "critical_pair_denominator": len(critical_rows),
        "clip_denominator": len(clip_rows),
        "drawing_denominator": len(drawings),
        "pair_0779": {
            **pair_0779,
            "axis_drawing_indexes": [9, 10, 11, 12, 13, 14],
            "marker_drawing_index": 17,
            "axis_tick_x_pt": drawings[9]["items"][2][1].x,
            "axis_tick_y0_pt": min(drawings[9]["items"][2][1].y, drawings[9]["items"][2][2].y),
            "axis_tick_y1_pt": max(drawings[9]["items"][2][1].y, drawings[9]["items"][2][2].y),
            "horizontal_axis_y_pt": drawings[11]["items"][0][1].y,
            "marker_rect_pt": list(drawings[17]["rect"]),
            "marker_center_pt": [
                (drawings[17]["rect"].x0 + drawings[17]["rect"].x1) / 2,
                (drawings[17]["rect"].y0 + drawings[17]["rect"].y1) / 2,
            ],
            "axis_marker_overlap_pixel_count_300dpi": overlap_count,
            "axis_marker_overlap_bbox_inclusive_px_300dpi": overlap_bbox,
        },
        "machine_outputs_do_not_contain_manual_reviewer_or_decision_fields": True,
    }
    (OUT / "machine_regression_summary.json").write_text(
        json.dumps(regression, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(regression, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
