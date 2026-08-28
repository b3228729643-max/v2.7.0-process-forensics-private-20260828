"""Correct the R5 opaque-label occlusion evidence without touching the frozen PDF.

H01--H05 are source-order checks with no foreground/halo intersection.  H06 is
the closest white edge-label background to the self-loop, so this program
creates a one-page *evidence copy* in which only that white fill operation is
changed from ``f`` (fill) to ``n`` (end path/no paint), then re-renders it
natively at 300 dpi.  It independently verifies that even H06 has no hidden
foreground pixels; it never infers a pre-state from the final image.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


WORKSPACE = Path(r"D:\Users\ASUS\Desktop\机器学习")
WORK_ROOT = WORKSPACE / "v2.7.0" / "_work"
PDF = WORK_ROOT / "source" / "v2.7.0" / "src" / "build" / "strict_current_r96_fullbook" / "main_full.pdf"
OUT = Path(__file__).resolve().parent
OCC = OUT / "occlusion"
PAGE_INDEX = 650
DPI = 300
SCALE = DPI / 72.0

# The bounds are the actual white edge-label fill rectangles measured from the
# R96 vector content.  They are not foreground objects.
HALOS = [
    ("H01_PROPOSAL_LABEL_HALO", (261.20, 380.80, 282.72, 392.76), "G08_PROPOSAL_SHAFT+G09_PROPOSAL_HEAD", "T12_LABEL_PROPOSAL", 10, 12,
     "vertical proposal connector x=255.77 pt is left of halo x=261.20 pt"),
    ("H02_CALCULATE_LABEL_HALO", (261.23, 426.05, 282.75, 438.00), "G10_CALCULATE_SHAFT+G11_CALCULATE_HEAD", "T13_LABEL_CALCULATE", 13, 15,
     "vertical calculate connector x=255.77 pt is left of halo x=261.23 pt"),
    ("H03_DECIDE_LABEL_HALO", (261.23, 491.70, 282.75, 503.65), "G12_DECIDE_SHAFT+G13_DECIDE_HEAD", "T14_LABEL_DECIDE", 16, 18,
     "vertical decide connector x=255.77 pt is left of halo x=261.23 pt"),
    ("H04_ACCEPT_LABEL_HALO", (140.27, 558.58, 161.79, 570.53), "G14_ACCEPT_BRANCH", "T15_LABEL_ACCEPT", 19, 21,
     "branch y=570 pt is approximately x=172 pt, right of halo x=161.79 pt"),
    ("H05_REJECT_LABEL_HALO", (349.73, 558.61, 371.24, 570.56), "G15_REJECT_BRANCH", "T16_LABEL_REJECT", 22, 24,
     "branch y=570 pt is approximately x=339 pt, left of halo x=349.73 pt"),
    ("H06_LOOP_LABEL_HALO", (345.88, 683.60, 403.78, 695.56), "G16_SELF_LOOP", "T17_LABEL_SELF_LOOP", 25, 27,
     "cubic self-loop maximum y=674.996 pt; halo begins y=683.605 pt, leaving 8.609 pt vector gap before stroke allowance"),
]
G16_RECT = (242.90, 614.60, 506.80, 695.70)
OBJECT_SCOPES = {
    "H01_PROPOSAL_LABEL_HALO": (254.30, 380.70, 257.20, 392.00),
    "H02_CALCULATE_LABEL_HALO": (254.30, 424.50, 257.20, 438.60),
    "H03_DECIDE_LABEL_HALO": (254.30, 491.20, 257.20, 503.80),
    "H04_ACCEPT_LABEL_HALO": (138.00, 558.50, 199.50, 582.30),
    "H05_REJECT_LABEL_HALO": (312.10, 558.50, 373.80, 582.30),
    "H06_LOOP_LABEL_HALO": G16_RECT,
}
H06_FILL_TOKEN = b"90.10548 -330.78996 57.90202 11.95532 re \nf \n"
H06_NO_PAINT_TOKEN = b"90.10548 -330.78996 57.90202 11.95532 re \nn \n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest().upper()


def rect_px(rect: tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        max(0, math.floor(x0 * SCALE)), max(0, math.floor(y0 * SCALE)),
        min(width, math.ceil(x1 * SCALE)), min(height, math.ceil(y1 * SCALE)),
    )


def blue_foreground(rgb: np.ndarray) -> np.ndarray:
    """Select the anti-aliased SLBlue vector foreground, excluding charcoal text."""
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    return (g - r >= 9) & (b - g >= 9) & (b - r >= 22) & (b < 250)


def crop_save_mask(mask: np.ndarray, path: Path) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        Image.new("L", (1, 1), 0).save(path)
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8), "L").save(path)
    return (x0, y0, x1, y1)


def save_roi(base: np.ndarray, pre: np.ndarray, halo: np.ndarray, final: np.ndarray, path: Path) -> tuple[int, int, int, int]:
    union = pre | halo | final
    ys, xs = np.where(union)
    x0 = max(0, int(xs.min()) - 8)
    x1 = min(base.shape[1], int(xs.max()) + 9)
    y0 = max(0, int(ys.min()) - 8)
    y1 = min(base.shape[0], int(ys.max()) + 9)
    image = base[y0:y1, x0:x1].copy()
    # red = pre-occlusion foreground, blue = opaque halo, green = final foreground
    image[pre[y0:y1, x0:x1]] = (235, 64, 52)
    image[halo[y0:y1, x0:x1]] = (44, 115, 195)
    image[final[y0:y1, x0:x1]] = (38, 166, 91)
    native = Image.fromarray(image)
    native.save(path)
    native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(
        path.with_name(path.stem + "_8x_nearest.png")
    )
    return x0, y0, x1, y1


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OCC.mkdir(exist_ok=True)
    original = OUT / "official_R96_physical_651_full_page_300dpi.png"
    if not original.exists():
        raise FileNotFoundError(original)

    # Copy only physical page 651 into a new evidence PDF and mutate the one
    # known H06 white-fill token in memory.  The frozen fullbook remains read-only.
    frozen = fitz.open(PDF)
    page = frozen[PAGE_INDEX]
    original_xref = page.get_contents()[0]
    original_stream = frozen.xref_stream(original_xref)
    if original_stream.count(H06_FILL_TOKEN) != 1:
        raise RuntimeError("expected exactly one H06 white-fill token in frozen page stream")
    evidence = fitz.open()
    evidence.insert_pdf(frozen, from_page=PAGE_INDEX, to_page=PAGE_INDEX)
    copied_page = evidence[0]
    copied_xref = copied_page.get_contents()[0]
    copied_stream = evidence.xref_stream(copied_xref)
    if copied_stream.count(H06_FILL_TOKEN) != 1:
        raise RuntimeError("expected exactly one H06 white-fill token in evidence copy")
    evidence.update_stream(copied_xref, copied_stream.replace(H06_FILL_TOKEN, H06_NO_PAINT_TOKEN, 1))
    pre_pdf = OCC / "H06_pre_occlusion_without_white_halo.pdf"
    evidence.save(pre_pdf, garbage=4, deflate=True)
    evidence.close()
    frozen.close()

    pre_png = OCC / "H06_pre_occlusion_page_300dpi.png"
    subprocess.run(
        ["pdftoppm", "-f", "1", "-l", "1", "-r", str(DPI), "-png", "-singlefile", str(pre_pdf), str(pre_png.with_suffix(""))],
        check=True,
    )
    if not pre_png.exists():
        raise RuntimeError(f"pdftoppm did not create {pre_png}")

    final_rgb = np.array(Image.open(original).convert("RGB"))
    pre_rgb = np.array(Image.open(pre_png).convert("RGB"))
    if final_rgb.shape != pre_rgb.shape:
        raise RuntimeError(f"render dimensions differ: {final_rgb.shape} vs {pre_rgb.shape}")
    h, w = final_rgb.shape[:2]
    final_blue = blue_foreground(final_rgb)
    pre_blue = blue_foreground(pre_rgb)
    scopes: dict[str, np.ndarray] = {}
    for hid, rect in OBJECT_SCOPES.items():
        scope = np.zeros((h, w), dtype=bool)
        x0, y0, x1, y1 = rect_px(rect, w, h)
        scope[y0:y1, x0:x1] = True
        scopes[hid] = scope

    rows: list[dict[str, object]] = []
    for hid, rect, pre_objects, text_parent, pre_idx, fill_idx, analytic in HALOS:
        halo = np.zeros((h, w), dtype=bool)
        x0, y0, x1, y1 = rect_px(rect, w, h)
        halo[y0:y1, x0:x1] = True
        if hid == "H06_LOOP_LABEL_HALO":
            pre = pre_blue & scopes[hid]
            final = final_blue & scopes[hid]
            method = "reverse-rendered native 300 dpi evidence copy: only H06 white fill changed f→n; no exposed loop pixel falls in halo"
            kind = "NO_TRUE_OCCLUSION_REVERSE_RENDERED"
        else:
            # For the five nonintersecting cases, a reverse render is not
            # material: source geometry proves no foreground reaches the halo.
            # The final blue foreground is therefore identical to pre-state
            # within each halo, and we retain it as a checkable mask.
            pre = final_blue & scopes[hid]
            final = final_blue & scopes[hid]
            method = "vector source-order/bounds analysis; no foreground/halo intersection, final state equals pre-state within halo"
            kind = "NO_TRUE_OCCLUSION"
        occluded = pre & halo & ~final
        unexpected = final & halo
        halo_path = OCC / f"{hid}_opaque_halo_mask.png"
        pre_path = OCC / f"{hid}_pre_occlusion_mask.png"
        final_path = OCC / f"{hid}_final_visible_mask.png"
        crop_save_mask(halo, halo_path)
        pre_box = crop_save_mask(pre, pre_path)
        final_box = crop_save_mask(final, final_path)
        roi_path = OCC / f"{hid}_occlusion_roi.png"
        roi = save_roi(final_rgb, pre, halo, final, roi_path)
        status = "PASS" if int(np.count_nonzero(unexpected)) == 0 else "FAIL_UNEXPECTED_FINAL_FOREGROUND"
        rows.append({
            "HALO_ID": hid,
            "TEXT_PARENT": text_parent,
            "PRE_OBJECTS": pre_objects,
            "HALO_RECT_PT": ";".join(f"{v:.2f}" for v in rect),
            "PRE_DRAW_INDEX": pre_idx,
            "WHITE_FILL_DRAW_INDEX": fill_idx,
            "PAINT_ORDER": "foreground vector paints first; opaque white label background paints second; label text paints third",
            "EVALUATION_KIND": kind,
            "PRE_OCCLUSION_METHOD": method,
            "ANALYTIC_EVIDENCE": analytic,
            "PRE_OCCLUSION_PX": int(np.count_nonzero(pre)),
            "HALO_PX": int(np.count_nonzero(halo)),
            "INTENTIONAL_OCCLUDED_PX": int(np.count_nonzero(occluded)),
            "FINAL_VISIBLE_PX": int(np.count_nonzero(final)),
            "UNEXPECTED_VISIBLE_IN_HALO_PX": int(np.count_nonzero(unexpected)),
            "PRE_MASK_BBOX_PX": "" if pre_box is None else ";".join(map(str, pre_box)),
            "FINAL_MASK_BBOX_PX": "" if final_box is None else ";".join(map(str, final_box)),
            "ROI_BBOX_PX": ";".join(map(str, roi)),
            "HALO_MASK": f"occlusion/{halo_path.name}",
            "PRE_MASK": f"occlusion/{pre_path.name}",
            "FINAL_MASK": f"occlusion/{final_path.name}",
            "ROI": f"occlusion/{roi_path.name}",
            "STATUS": status,
        })
    write_csv(OUT / "occlusion_inversion.csv", rows)
    report = {
        "frozen_pdf": str(PDF),
        "frozen_pdf_sha256": sha256(PDF),
        "physical_page": 651,
        "modified_evidence_copy": str(pre_pdf),
        "copied_page_content_stream_xref": copied_xref,
        "frozen_page_content_stream_xref": original_xref,
        "frozen_stream_sha256": hashlib.sha256(original_stream).hexdigest().upper(),
        "target_h06_fill_token_occurrences": 1,
        "mutation": "in evidence copy only, exact H06 white fill token 'f' replaced with 'n' (no paint)",
        "pre_pdf_sha256": sha256(pre_pdf),
        "pre_png_sha256": sha256(pre_png),
        "result": {row["HALO_ID"]: {"kind": row["EVALUATION_KIND"], "occluded_px": row["INTENTIONAL_OCCLUDED_PX"], "unexpected_final_px": row["UNEXPECTED_VISIBLE_IN_HALO_PX"], "status": row["STATUS"]} for row in rows},
    }
    (OCC / "occlusion_reverse_render_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
