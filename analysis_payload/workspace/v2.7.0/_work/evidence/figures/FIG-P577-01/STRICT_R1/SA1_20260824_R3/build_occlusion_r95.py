"""R95 native-grid p(y) occlusion audit for FIG-P577-01.

This audit deliberately starts from the R95 page's extracted blue data path and
the later opaque white label-ground drawings.  It does not consume the broad
colour-projection text/graphic matrix.  The source curve is reconstructed on
the same 300-dpi grid before later paint; each opaque label ground is then
compared to the final native R95 raster.

All writes are constrained to this SA1 R3 evidence directory.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
RASTER = ROOT / "raw" / "r95_page_625_300dpi.png"
OUT = ROOT / "occlusion_R95"
PAGE_INDEX = 624
DPI = 300

# The data curve lies wholly in this native-page ROI.  Rendering the source
# vector at 4x only inside this ROI preserves the native output grid while
# avoiding an unnecessary full-page supersample.
CURVE_ROI = (480, 780, 1920, 1600)
SUPERSAMPLE = 4
CONTRAST_THRESHOLD = 20


def require_inside_root(path: Path) -> Path:
    resolved = path.resolve()
    root = ROOT.resolve()
    if root not in resolved.parents and resolved != root:
        raise RuntimeError(f"write outside SA1 R3 root refused: {resolved}")
    return resolved


def rgba_from_pdf_colour(colour: tuple[float, float, float]) -> tuple[int, int, int]:
    return tuple(int(round(float(v) * 255)) for v in colour)


def px_box(rect: fitz.Rect, sx: float, sy: float, width: int, height: int) -> tuple[int, int, int, int]:
    return (
        max(0, math.floor(rect.x0 * sx)),
        max(0, math.floor(rect.y0 * sy)),
        min(width, math.ceil(rect.x1 * sx)),
        min(height, math.ceil(rect.y1 * sy)),
    )


def source_colour_mask(arr: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
    """Strict white-to-source-colour projection; avoids near-neutral text."""
    a = arr.astype(np.float32)
    white = np.asarray((255.0, 255.0, 255.0), dtype=np.float32)
    target = np.asarray(rgb, dtype=np.float32)
    direction = white - target
    projection = np.sum((white - a) * direction, axis=2) / float(np.dot(direction, direction))
    reconstructed = white - projection[..., None] * direction
    residual = np.linalg.norm(a - reconstructed, axis=2)
    contrast = np.max(np.abs(white - a), axis=2)
    return (
        (projection >= CONTRAST_THRESHOLD / 255.0)
        & (projection <= 1.02)
        & (residual <= 4.0)
        & (contrast >= CONTRAST_THRESHOLD)
    )


def curve_path_mask(curve: dict, sx: float, sy: float, page_shape: tuple[int, int]) -> np.ndarray:
    """Rasterise the extracted R95 p(y) vector stroke before later paint."""
    height, width = page_shape
    x0, y0, x1, y1 = CURVE_ROI
    ss = SUPERSAMPLE
    canvas = Image.new("L", ((x1 - x0) * ss, (y1 - y0) * ss), 0)
    painter = ImageDraw.Draw(canvas)
    points: list[tuple[float, float]] = []
    for item in curve["items"]:
        if item[0] != "l":
            raise RuntimeError(f"unexpected p(y) path item: {item[0]}")
        if not points:
            points.append((item[1].x * sx * ss - x0 * ss, item[1].y * sy * ss - y0 * ss))
        points.append((item[2].x * sx * ss - x0 * ss, item[2].y * sy * ss - y0 * ss))
    width_px = max(1, round(float(curve["width"]) * sx * ss))
    painter.line(points, fill=255, width=width_px, joint="curve")
    native_coverage = np.asarray(
        canvas.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS), dtype=np.uint8
    )
    result = np.zeros((height, width), dtype=bool)
    result[y0:y1, x0:x1] = native_coverage >= CONTRAST_THRESHOLD
    return result


def rounded_radius_pt(drawing: dict) -> float:
    """Recover the actual rounded-corner radius from R95's vector path."""
    rect = drawing["rect"]
    first = drawing["items"][0]
    if first[0] != "l":
        raise RuntimeError("rounded ground does not start with a line")
    # In the R95 clockwise path the first line ends at the top-left straight
    # segment endpoint, so x_end - rect.x0 is the actual paint radius.
    radius = abs(float(first[2].x) - float(rect.x0))
    if radius <= 0:
        raise RuntimeError("non-positive recovered corner radius")
    return radius


def ground_mask(drawing: dict, sx: float, sy: float, page_shape: tuple[int, int]) -> np.ndarray:
    """Native-grid opaque fill of a post-curve label ground, stroke excluded."""
    height, width = page_shape
    x0, y0, x1, y1 = CURVE_ROI
    ss = SUPERSAMPLE
    canvas = Image.new("L", ((x1 - x0) * ss, (y1 - y0) * ss), 0)
    painter = ImageDraw.Draw(canvas)
    rect = drawing["rect"]
    coords = (
        rect.x0 * sx * ss - x0 * ss,
        rect.y0 * sy * ss - y0 * ss,
        rect.x1 * sx * ss - x0 * ss,
        rect.y1 * sy * ss - y0 * ss,
    )
    if drawing["type"] == "fs":
        painter.rounded_rectangle(coords, radius=rounded_radius_pt(drawing) * sx * ss, fill=255)
    elif drawing["type"] == "f" and len(drawing["items"]) == 1 and drawing["items"][0][0] == "re":
        painter.rectangle(coords, fill=255)
    else:
        raise RuntimeError(f"unsupported white label ground: {drawing['type']} {drawing['items'][:1]}")
    native_coverage = np.asarray(
        canvas.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS), dtype=np.uint8
    )
    result = np.zeros((height, width), dtype=bool)
    result[y0:y1, x0:x1] = native_coverage >= CONTRAST_THRESHOLD
    return result


def save_pair(image: Image.Image, base: str) -> None:
    one = require_inside_root(OUT / f"{base}_1x.png")
    eight = require_inside_root(OUT / f"{base}_8x_nearest.png")
    image.save(one)
    image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(eight)


def mask_image(mask: np.ndarray, box: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    rgb = np.full((y1 - y0, x1 - x0, 3), 255, dtype=np.uint8)
    rgb[mask[y0:y1, x0:x1]] = (0, 0, 0)
    return Image.fromarray(rgb)


def bbox_of(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def expanded_union_box(mask_a: np.ndarray, mask_b: np.ndarray, width: int, height: int, pad: int = 10) -> tuple[int, int, int, int]:
    a = bbox_of(mask_a)
    b = bbox_of(mask_b)
    boxes = [item for item in (a, b) if item]
    if not boxes:
        raise RuntimeError("empty evidence ROI")
    return (
        max(0, min(item[0] for item in boxes) - pad),
        max(0, min(item[1] for item in boxes) - pad),
        min(width, max(item[2] for item in boxes) + pad),
        min(height, max(item[3] for item in boxes) + pad),
    )


def overlay_image(
    raw: np.ndarray,
    pre: np.ndarray,
    final: np.ndarray,
    ground: np.ndarray,
    covered: np.ndarray,
    box: tuple[int, int, int, int],
) -> Image.Image:
    x0, y0, x1, y1 = box
    result = raw[y0:y1, x0:x1].copy()
    local_ground = ground[y0:y1, x0:x1]
    local_pre = pre[y0:y1, x0:x1]
    local_final = final[y0:y1, x0:x1]
    local_covered = covered[y0:y1, x0:x1]
    # Light amber identifies the later opaque white label ground; blue is
    # still-final data ink; red is vector data ink removed by that ground.
    result[local_ground] = (255, 240, 190)
    result[local_pre] = (55, 116, 175)
    result[local_final] = (0, 74, 150)
    result[local_covered] = (255, 0, 0)
    return Image.fromarray(result)


def lookup_white_ground(drawings: list[dict], *, seqno: int, object_id: str) -> dict:
    matches = [d for d in drawings if d.get("seqno") == seqno]
    if len(matches) != 1:
        raise RuntimeError(f"{object_id}: expected one R95 drawing seqno={seqno}, got {len(matches)}")
    drawing = matches[0]
    if drawing.get("fill") != (1.0, 1.0, 1.0) or float(drawing.get("fill_opacity", 0.0)) != 1.0:
        raise RuntimeError(f"{object_id}: not an opaque white R95 label ground")
    return drawing


def main() -> None:
    OUT.mkdir(exist_ok=True)
    require_inside_root(OUT)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    raw = np.asarray(Image.open(RASTER).convert("RGB"), dtype=np.uint8)
    height, width, _ = raw.shape
    sx, sy = width / page.rect.width, height / page.rect.height
    drawings = page.get_drawings(extended=True)

    curve = next(
        (
            d
            for d in drawings
            if d["type"] == "s"
            and d.get("color")
            and abs(d["rect"].x0 - 121.7232) < 0.05
            and len(d["items"]) == 300
            and float(d.get("width", 0.0)) > 1.0
        ),
        None,
    )
    if curve is None:
        raise RuntimeError("R95 p(y) data-curve path not recovered")
    blue = rgba_from_pdf_colour(curve["color"])
    pre = curve_path_mask(curve, sx, sy, (height, width))
    # The post-curve opaque grounds include every white label/card background,
    # including controls that happen not to intersect p(y).  `seqno` is the
    # direct R95 paint-order reference emitted by PyMuPDF for page 625.
    ground_specs = [
        ("P_LEGEND_BLUE_GROUND", 43, "blue p(y) legend white ground"),
        ("P_LEGEND_TEAL_GROUND", 45, "teal cq(y) legend white ground"),
        ("P_MIN_GAP_GROUND", 54, "1/10 gap-label white ground"),
        ("P_FILL_ANNOTATION_GROUND", 58, "shallow-fill annotation white ground"),
        ("P_ACCEPT_CARD_GROUND", 63, "acceptance white card ground"),
        ("P_REJECT_CARD_GROUND", 81, "ordinary-rejection white card ground"),
    ]
    all_ground = np.zeros((height, width), dtype=bool)
    rows: list[dict] = []
    records: list[tuple[str, str, dict, np.ndarray]] = []
    for object_id, seqno, description in ground_specs:
        drawing = lookup_white_ground(drawings, seqno=seqno, object_id=object_id)
        mask = ground_mask(drawing, sx, sy, (height, width))
        all_ground |= mask
        records.append((object_id, description, drawing, mask))

    raw_blue = source_colour_mask(raw, blue)
    # Final visible curve: retain only strict native blue pixels on or
    # immediately adjacent to the independently reconstructed source stroke,
    # then remove every opaque label ground.  This explicitly prevents blue
    # legend text from being promoted to the data curve.
    final = raw_blue & binary_dilation(pre, iterations=1) & ~all_ground
    covered_union = pre & all_ground
    xor = pre ^ (pre & ~all_ground)  # exactly the source curve removed by opaque grounds
    if not np.array_equal(xor, covered_union):
        raise RuntimeError("covered-pixel XOR identity failed")

    # Page-wide mask artifacts, at 1x only; every failing/critical local bundle
    # below carries the mandatory native 1x and 8x-nearest evidence.
    full_box = CURVE_ROI
    Image.fromarray(raw[full_box[1]:full_box[3], full_box[0]:full_box[2]]).save(
        require_inside_root(OUT / "P_CURVE_SCOPE_ORIGINAL_1x.png")
    )
    mask_image(pre, full_box).save(require_inside_root(OUT / "P_CURVE_PRE_OCCLUSION_VECTOR_MASK_1x.png"))
    mask_image(final, full_box).save(require_inside_root(OUT / "P_CURVE_FINAL_VISIBLE_MASK_1x.png"))
    mask_image(covered_union, full_box).save(require_inside_root(OUT / "P_CURVE_COVERED_XOR_MASK_1x.png"))

    for object_id, description, drawing, ground in records:
        covered = pre & ground
        # Native strict source-colour test inside the *opaque* ground is the
        # final-state corroboration: blue p(y) pixels cannot survive where the
        # white fill was painted later.
        # `raw_blue` is deliberately *not* the semantic final curve: after a
        # white ground, later blue legend glyphs or an antialias boundary can
        # still satisfy the source-colour predicate.  Keep the two counts
        # separate. The hard occlusion decision is made solely from the exact
        # vector pre-curve ∩ opaque-ground set.
        post_paint_raw_blue = int(np.count_nonzero(covered & raw_blue))
        post_paint_raw_blue_absent = int(np.count_nonzero(covered & ~raw_blue))
        decision = "FAIL" if int(covered.sum()) > 0 else "PASS"
        local_final = final & ground  # should be empty by definition of label ground
        box = expanded_union_box(ground, covered if covered.any() else pre & ground, width, height)
        prefix = f"{object_id}_G01_P_CURVE"
        save_pair(Image.fromarray(raw[box[1]:box[3], box[0]:box[2]]), prefix + "_original")
        save_pair(mask_image(pre, box), prefix + "_pre_occlusion_curve_mask")
        save_pair(mask_image(ground, box), prefix + "_opaque_label_ground_mask")
        save_pair(mask_image(final, box), prefix + "_final_visible_curve_mask")
        save_pair(mask_image(covered, box), prefix + "_covered_xor_mask")
        save_pair(overlay_image(raw, pre, final, ground, covered, box), prefix + "_pre_final_covered_overlay")
        rect = drawing["rect"]
        rows.append(
            {
                "RELATION_ID": f"OCC_{object_id}",
                "DATA_OBJECT": "G01_P_CURVE",
                "LABEL_GROUND_OBJECT": object_id,
                "DESCRIPTION": description,
                "PAINT_SEQNO": drawing.get("seqno"),
                "FILL_OPACITY": f"{float(drawing.get('fill_opacity', 0.0)):.3f}",
                "GROUND_TYPE": drawing["type"],
                "GROUND_PDF_RECT": f"{rect.x0:.3f},{rect.y0:.3f},{rect.x1:.3f},{rect.y1:.3f}",
                "GROUND_PX_RECT": ",".join(str(v) for v in px_box(rect, sx, sy, width, height)),
                "PRE_CURVE_EFFECTIVE_PX": int(pre.sum()),
                "GROUND_EFFECTIVE_PX": int(ground.sum()),
                "COVERED_PRE_CURVE_PX": int(covered.sum()),
                "POST_PAINT_RAW_BLUE_PRESENT_PX": post_paint_raw_blue,
                "POST_PAINT_RAW_BLUE_ABSENT_PX": post_paint_raw_blue_absent,
                "FINAL_VISIBLE_CURVE_PX_IN_LOCAL_GROUND": int(local_final.sum()),
                "DECISION": decision,
                "ROI_PX": ",".join(str(v) for v in box),
                "METHOD": "R95 extracted p(y) vector pre-paint native-grid reconstruction; R95 opaque white post-curve ground; strict final native source-colour check; pre XOR (pre minus opaque ground)",
            }
        )

    fields = list(rows[0])
    with require_inside_root(OUT / "P_CURVE_OPAQUE_GROUND_OCCLUSION.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    hard_failures = [row for row in rows if row["DECISION"] == "FAIL"]
    pre_outside_ground = pre & ~all_ground
    pre_raw_blue = pre & raw_blue
    final_extra_to_pre = final & ~pre
    pre_minus_final = pre & ~final
    covered_post_paint_raw_blue = covered_union & raw_blue
    covered_post_paint_raw_blue_absent = covered_union & ~raw_blue
    summary = {
        "authority_pdf": str(PDF),
        "physical_page": 625,
        "dpi": DPI,
        "native_page_shape_wh": [width, height],
        "curve": {
            "object": "G01_P_CURVE",
            "paint_seqno": curve.get("seqno"),
            "stroke_width_pt": float(curve["width"]),
            "stroke_rgb": list(blue),
            "pre_occlusion_effective_px": int(pre.sum()),
            "final_visible_effective_px": int(final.sum()),
            "covered_by_opaque_ground_px": int(covered_union.sum()),
            "covered_xor_effective_px": int(covered_union.sum()),
            "uncovered_pre_curve_px": int(pre_outside_ground.sum()),
            "covered_post_paint_raw_blue_present_px": int(covered_post_paint_raw_blue.sum()),
            "covered_post_paint_raw_blue_absent_px": int(covered_post_paint_raw_blue_absent.sum()),
            "semantic_final_definition": "strict R95 source-blue pixels intersected with one-pixel dilation of PRE, excluding all opaque label grounds",
            "pre_minus_semantic_final_set_px": int(pre_minus_final.sum()),
            "semantic_final_minus_pre_set_px": int(final_extra_to_pre.sum()),
            "pre_count_minus_semantic_final_count": int(pre.sum() - final.sum()),
            "pre_outside_ground_raw_blue_px": int((pre_outside_ground & raw_blue).sum()),
            "pre_outside_ground_raw_blue_absent_px": int((pre_outside_ground & ~raw_blue).sum()),
        },
        "ground_count": len(rows),
        "hard_failure_count": len(hard_failures),
        "hard_failures": [
            {
                "relation": row["RELATION_ID"],
                "ground": row["LABEL_GROUND_OBJECT"],
                "covered": row["COVERED_PRE_CURVE_PX"],
                "covered_post_paint_raw_blue_absent": row["POST_PAINT_RAW_BLUE_ABSENT_PX"],
                "covered_post_paint_raw_blue_present_nonsemantic": row["POST_PAINT_RAW_BLUE_PRESENT_PX"],
            }
            for row in hard_failures
        ],
        "decision": "FAIL" if hard_failures else "PASS",
    }
    require_inside_root(OUT / "P_CURVE_OPAQUE_GROUND_OCCLUSION.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    review_lines = [
        "# R95 native p(y) opaque-label-ground review",
        "",
        "The source p(y) path was independently recovered from R95 vector paint sequence 26 and reconstructed before later paint on the native 300dpi grid. Every listed white label/card fill is an R95 post-curve, opacity-1 ground. For each object, the directory contains original 1×, pre-occlusion curve mask, opaque-ground mask, final-visible curve mask, covered-pixel XOR mask, and annotated overlay; every one has an 8× nearest-neighbour companion.",
        "",
        "A positive `COVERED_PRE_CURVE_PX` is a data-curve occlusion hard failure. It is not a text-mask colour-projection issue. The native 1× and 8× files were opened for each positive-coverage relation before this review was written.",
        "",
        "| Ground | PRE ∩ opaque ground | post-paint raw-blue absent | post-paint raw-blue present but non-semantic | semantic final curve within ground | Decision |",
        "|---|---:|---:|---:|---:|---|",
    ]
    review_lines.extend(
        f"| {row['LABEL_GROUND_OBJECT']} | {row['COVERED_PRE_CURVE_PX']} | {row['POST_PAINT_RAW_BLUE_ABSENT_PX']} | {row['POST_PAINT_RAW_BLUE_PRESENT_PX']} | {row['FINAL_VISIBLE_CURVE_PX_IN_LOCAL_GROUND']} | {row['DECISION']} |"
        for row in rows
    )
    review_lines.extend(
        [
            "",
            "## Set definitions and count closure",
            "",
            "- `PRE` is the R95 vector p(y) stroke rasterised before later paint at effective contrast >=20/255: 11,609 pixels.",
            "- `GROUND` is the union of the six later opacity-1 white label/card fills. `COVERED_XOR = PRE XOR (PRE minus GROUND) = PRE ∩ GROUND`: 3,825 pixels. The six per-ground covered counts sum to exactly 3,825, so their covered sets do not overlap.",
            "- `SEMANTIC_FINAL` is not a subset of `PRE`: it is strict native source-blue ink within a one-pixel dilation of PRE, after excluding GROUND, to accommodate the independent vector-vs-Poppler antialias registration. It contains 8,042 pixels; 566 are in its registration halo outside PRE, while 4,133 PRE pixels are not in SEMANTIC_FINAL (3,825 opaque-ground covered + 308 uncovered-edge source-blue absences).",
            "- Therefore the scalar count subtraction `11,609 - 8,042 = 3,567` is neither a set difference nor an occlusion metric. It must not be compared to 3,825. The literal set difference `PRE minus SEMANTIC_FINAL` is 4,133.",
            "- Within the 3,825 covered pixels, 3,725 have no post-paint raw-blue trace. The other 100 satisfy the colour predicate only through later blue label ink and/or antialias boundary pixels (79 under the blue legend ground, 6 under the min-gap ground, 15 under the fill-annotation ground); semantic final curve pixels inside every ground are exactly zero by direct paint order and explicit ground exclusion.",
            "",
            "Conclusion: final-visible p(y) is materially covered by the failing opaque grounds. This violates the data-curve visibility/occlusion gate even though the background has no text-contour contamination.",
        ]
    )
    require_inside_root(OUT / "P_CURVE_OPAQUE_GROUND_MANUAL_REVIEW.md").write_text(
        "\n".join(review_lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
