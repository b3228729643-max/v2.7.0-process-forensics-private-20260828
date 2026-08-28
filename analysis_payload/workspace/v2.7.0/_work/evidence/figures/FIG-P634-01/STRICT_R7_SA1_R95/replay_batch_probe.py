"""Non-terminal full-batch validation for official PDF glyph replay support."""
import tempfile
import time
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

import audit_p634_r95 as audit
import pdf_glyph_replay_support as replay


start = time.time()
page = fitz.open(audit.OFFICIAL_PDF)[audit.PAGE_INDEX]
raw = page.get_text("rawdict")
spans = [
    span
    for block in raw["blocks"]
    if block["type"] == 0
    for line in block["lines"]
    for span in line["spans"]
    if "".join(char["c"] for char in span["chars"]).strip()
    and audit.FIG_RECT_PT.contains(fitz.Rect(span["bbox"]))
]
elements = [audit.element_meta(span, index + 1) for index, span in enumerate(spans)]
uses, symbols, symbol_xml = audit.parse_svg_glyph_uses()
glyphs, svg_errors = audit.map_glyphs_to_svg(elements, uses, symbols)
for glyph in glyphs:
    glyph["char_bbox_px"] = audit.rect_to_px(fitz.Rect(glyph["char_bbox_pt"]))
reader, replay_page, stream, records, record_errors = replay.extract_official_text_records(
    audit.OFFICIAL_PDF, audit.PAGE_INDEX
)
bind_errors = replay.bind_glyphs_to_official_replay(
    elements,
    glyphs,
    records,
    float(replay_page.mediabox.height),
    (audit.FIG_RECT_PT.x0, audit.FIG_RECT_PT.y0, audit.FIG_RECT_PT.x1, audit.FIG_RECT_PT.y1),
)
with tempfile.TemporaryDirectory(prefix="fig_p634_batch_") as temp:
    alphas, manifest, render_errors = replay.render_official_glyph_replays(
        glyphs, reader, replay_page, stream, Path(temp) / "replay.pdf", audit.SCALE
    )
    if render_errors:
        print({"render_errors": render_errors, "alpha_keys": len(alphas), "manifest": len(manifest)})
        raise SystemExit(2)
    image = np.asarray(Image.open(audit.FULL_300).convert("RGB"))
    graphics, graphic_errors = audit.build_graphics(page, image)
    rows = []
    nonpath_rows = []
    support_unmodelled_rows = []
    diagnostic_pixels = {}
    residual_sweep = {}
    for residual_limit in (14.0, 18.0, 22.0, 26.0, 30.0, 36.0):
        outside_support = 0
        support_without_ray = 0
        for glyph in glyphs:
            fill, opacity = audit.parse_svg_fill(glyph["svg_parent_style"])
            background, _ = audit.glyph_known_background(glyph)
            candidate = audit.known_background_colour_ray_mask(
                image, fitz.Rect(glyph["char_bbox_pt"]), fill, opacity, background, residual_limit
            )
            support_data = alphas[glyph["glyph_id"]]
            outside_support += int((candidate.data & ~support_data).sum())
            crop = image[candidate.y0 : candidate.y1, candidate.x0 : candidate.x1].astype(np.float32)
            contrast = np.max(np.abs(crop - background), axis=2) >= 20.0
            support_without_ray += int((support_data & contrast & ~candidate.data).sum())
        residual_sweep[residual_limit] = {
            "candidate_nonpath": outside_support,
            "support_visible_not_candidate": support_without_ray,
        }
    for glyph in glyphs:
        fill, opacity = audit.parse_svg_fill(glyph["svg_parent_style"])
        background, _ = audit.glyph_known_background(glyph)
        ray = audit.known_background_colour_ray_mask(
            image, fitz.Rect(glyph["char_bbox_pt"]), fill, opacity, background
        )
        support = audit.Mask(*ray.bbox[:2], alphas[glyph["glyph_id"]])
        missing = ray.pixels - audit.pair_intersection_pixels(support, ray)
        rows.append((glyph["glyph_id"], ray.pixels, support.pixels, missing))
        nonpath = audit.Mask(ray.x0, ray.y0, ray.data & ~support.data)
        hits = [graphic["id"] for graphic in graphics if audit.pair_intersection_pixels(nonpath, graphic["mask"])]
        nonpath_rows.append((glyph["glyph_id"], nonpath.pixels, hits))
        crop = image[ray.y0 : ray.y1, ray.x0 : ray.x1].astype(np.float32)
        contrast = np.max(np.abs(crop - background), axis=2) >= 20.0
        support_unmodelled = support.data & contrast & ~ray.data
        support_unmodelled_rows.append((glyph["glyph_id"], int(support_unmodelled.sum())))
        if glyph["glyph_id"] in {"T012:G01", "T016:G01", "T016:G02"}:
            yy, xx = np.nonzero(nonpath.data)
            values = image[nonpath.y0 + yy, nonpath.x0 + xx]
            diagnostic_pixels[glyph["glyph_id"]] = {
                "coords_rgb": list(zip((nonpath.x0 + xx).tolist(), (nonpath.y0 + yy).tolist(), [tuple(value) for value in values]))[:40],
                "unique_rgb": [
                    (tuple(value), int((values == value).all(axis=1).sum()))
                    for value in np.unique(values, axis=0)
                ],
            }
print(
    {
        "glyphs": len(glyphs),
        "svg_errors": svg_errors,
        "record_errors": record_errors,
        "bind_errors": bind_errors,
        "render_errors": render_errors,
        "alpha_count": len(alphas),
        "missing_pixels_total": sum(row[3] for row in rows),
        "missing_glyph_count": sum(row[3] > 0 for row in rows),
        "worst": max(rows, key=lambda row: row[3]),
        "seconds": round(time.time() - start, 1),
        "bad_rows": [row for row in rows if row[3] > 0][:30],
        "graphic_errors": graphic_errors,
        "nonpath_candidate_total": sum(row[1] for row in nonpath_rows),
        "nonpath_unattributed": [row for row in nonpath_rows if row[1] and not row[2]][:30],
        "nonpath_attributed": [row for row in nonpath_rows if row[1]][:30],
        "support_visible_but_not_fill_ray": [row for row in support_unmodelled_rows if row[1]][:30],
        "diagnostic_pixels": diagnostic_pixels,
        "residual_sweep": residual_sweep,
    }
)
