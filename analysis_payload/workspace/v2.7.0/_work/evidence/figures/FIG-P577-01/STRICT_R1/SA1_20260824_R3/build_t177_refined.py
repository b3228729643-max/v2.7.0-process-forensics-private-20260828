"""Corrected R95 visible-contour triad for the lower fraction glyph T177_G01.

The original preliminary triad used the PDF advance box and coloured a nearby
teal dashed envelope segment red.  This independent R95 replay retains only
the final visible digit-5 contour, then records the neighbouring dash as a
separate non-target component.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import find_objects, label


ROOT = Path(__file__).resolve().parent
RASTER = ROOT / "raw" / "r95_page_625_300dpi.png"
OUT = ROOT / "glyph_corrections"


def check(path: Path) -> Path:
    path = path.resolve()
    if ROOT.resolve() not in path.parents:
        raise RuntimeError(f"refuse write outside own evidence root: {path}")
    return path


def cmask(arr: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
    white = np.asarray((255.0, 255.0, 255.0), dtype=np.float32)
    target = np.asarray(rgb, dtype=np.float32)
    a = arr.astype(np.float32)
    direction = white - target
    projection = ((white - a) * direction).sum(axis=2) / float(direction @ direction)
    reconstructed = white - projection[..., None] * direction
    return (
        (projection >= 20.0 / 255.0)
        & (projection <= 1.02)
        & (np.linalg.norm(a - reconstructed, axis=2) <= 4.0)
        & (np.max(abs(white - a), axis=2) >= 20.0)
    )


def save_pair(image: Image.Image, stem: str) -> None:
    image.save(check(OUT / f"{stem}_1x.png"))
    image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(
        check(OUT / f"{stem}_8x_nearest.png")
    )


def main() -> None:
    OUT.mkdir(exist_ok=True)
    arr = np.asarray(Image.open(RASTER).convert("RGB"), dtype=np.uint8)
    # The R95 source colour of the teal legend/dashed-envelope object.
    teal = (15, 118, 110)
    # Direct R95 raw text-operator advance box for the denominator 5.  The
    # final digit ink ends at y=799; the distinct opaque dashed-line component
    # begins at y=804.  This bounds the target by actual visible contour, not
    # merely its advance box.
    glyph_box = (1836, 771, 1856, 809)
    rx0, ry0, rx1, ry1 = (1832, 767, 1860, 813)
    target = np.zeros(arr.shape[:2], dtype=bool)
    x0, y0, x1, y1 = glyph_box
    local = cmask(arr[y0:y1, x0:x1], teal)
    target[y0:y1, x0:x1] = local
    target[803:809, x0:x1] = False
    # A second raw-colour component inventory documents why the nearby dash is
    # excluded rather than silently discarded.
    all_teal = cmask(arr[ry0:ry1, rx0:rx1], teal)
    components, count = label(all_teal)
    rows = []
    for number, slc in enumerate(find_objects(components), 1):
        if slc is None:
            continue
        yy, xx = slc
        comp = components[slc] == number
        bx0, by0, bx1, by1 = rx0 + xx.start, ry0 + yy.start, rx0 + xx.stop, ry0 + yy.stop
        role = "TARGET_T177_VISIBLE_DIGIT_5" if np.any(target[by0:by1, bx0:bx1] & comp) else "NEIGHBOUR_DASH_OR_FILL_NON_TARGET"
        rows.append({
            "COMPONENT": number,
            "PX_BBOX": f"{bx0},{by0},{bx1},{by1}",
            "PIXELS": int(comp.sum()),
            "ROLE": role,
        })
    digit_rows = [r for r in rows if r["ROLE"] == "TARGET_T177_VISIBLE_DIGIT_5"]
    if len(digit_rows) != 1 or digit_rows[0]["PX_BBOX"] != "1836,774,1852,800":
        raise RuntimeError(f"unexpected T177 target components: {rows}")
    dash_rows = [r for r in rows if r["ROLE"] != "TARGET_T177_VISIBLE_DIGIT_5"]
    if not dash_rows or not any(r["PX_BBOX"].endswith(",813") for r in dash_rows):
        raise RuntimeError(f"nearby R95 dash component not independently recovered: {rows}")

    raw_crop = arr[ry0:ry1, rx0:rx1]
    overlay = raw_crop.copy()
    overlay[target[ry0:ry1, rx0:rx1]] = (255, 0, 0)
    mask_only = np.full_like(raw_crop, 255)
    mask_only[target[ry0:ry1, rx0:rx1]] = (0, 0, 0)
    save_pair(Image.fromarray(raw_crop), "T177_G01_R95_refined_original")
    save_pair(Image.fromarray(overlay), "T177_G01_R95_refined_target_overlay_unique_red")
    save_pair(Image.fromarray(mask_only), "T177_G01_R95_refined_target_mask_only")
    triptych = Image.new("RGB", (raw_crop.shape[1] * 3 * 8, raw_crop.shape[0] * 8), "white")
    for position, image in enumerate((raw_crop, overlay, mask_only)):
        panel = Image.fromarray(image).resize((raw_crop.shape[1] * 8, raw_crop.shape[0] * 8), Image.Resampling.NEAREST)
        triptych.paste(panel, (position * raw_crop.shape[1] * 8, 0))
    triptych.save(check(OUT / "T177_G01_R95_REFINED_ORIGINAL_OVERLAY_MASK_8x_nearest.png"))
    with check(OUT / "T177_G01_R95_REFINED_COMPONENTS.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "authority": "R95 native 300dpi page 625",
        "glyph_id": "T177_G01",
        "char": "5",
        "advance_bbox_px": list(glyph_box),
        "visible_target_component_bbox_px": [1836, 774, 1852, 800],
        "target_pixels": int(target.sum()),
        "excluded_neighbour_components": dash_rows,
        "decision": "PASS_TARGET_MASK_PURITY",
    }
    check(OUT / "T177_G01_R95_REFINED_COMPONENTS.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    check(OUT / "T177_G01_R95_REFINED_MANUAL_REVIEW.md").write_text(
        "# T177_G01 R95 refined contour review\n\n"
        "Native 1× and 8× nearest views were opened. The target is the visible denominator digit `5` only: component `1836,774,1852,800`. "
        "The separate opaque teal dash begins at row 804 and is retained in ORIGINAL but excluded from the unique-red target overlay and MASK ONLY. "
        "Thus the old advance-bbox colour projection is superseded and cannot contribute a terminal contamination or TG317 failure.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
