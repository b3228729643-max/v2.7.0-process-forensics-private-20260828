from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
EXPECTED_PDF_SHA = "C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78"
SCALE = 300.0 / 72.0
CLIP = fitz.Rect(100, 260, 506, 462)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def cubic_points(p0, p1, p2, p3, n=48):
    for t in np.linspace(0.0, 1.0, n):
        q = 1.0 - t
        yield (
            q**3 * p0.x + 3 * q*q*t*p1.x + 3*q*t*t*p2.x + t**3*p3.x,
            q**3 * p0.y + 3 * q*q*t*p1.y + 3*q*t*t*p2.y + t**3*p3.y,
        )


def stroke_support(draw, width: int, height: int, ox: int, oy: int) -> np.ndarray:
    im = Image.new("L", (width, height), 0)
    pen = ImageDraw.Draw(im)

    def pp(p):
        return (round(p.x * SCALE - ox), round(p.y * SCALE - oy))

    paths = []
    current = []
    for item in draw["items"]:
        kind = item[0]
        if kind == "l":
            a, b = item[1], item[2]
            if not current or current[-1] != pp(a):
                if current:
                    paths.append(current)
                current = [pp(a)]
            current.append(pp(b))
        elif kind == "c":
            a, b, c, d = item[1], item[2], item[3], item[4]
            pts = [(round(x * SCALE - ox), round(y * SCALE - oy)) for x, y in cubic_points(a, b, c, d)]
            if not current or current[-1] != pts[0]:
                if current:
                    paths.append(current)
                current = [pts[0]]
            current.extend(pts[1:])
        elif kind == "re":
            r = item[1]
            if current:
                paths.append(current)
                current = []
            paths.append([pp(fitz.Point(r.x0, r.y0)), pp(fitz.Point(r.x1, r.y0)), pp(fitz.Point(r.x1, r.y1)), pp(fitz.Point(r.x0, r.y1)), pp(fitz.Point(r.x0, r.y0))])
    if current:
        paths.append(current)
    line_w = max(3, int(math.ceil(float(draw.get("width") or 0.7) * SCALE)) + 2)
    for pts in paths:
        if len(pts) >= 2:
            pen.line(pts, fill=255, width=line_w, joint="curve")
    return np.array(im) > 0


def paste_mask(canvas: np.ndarray, tight: np.ndarray, bbox: list[int]) -> None:
    x0, y0, x1, y1 = bbox
    canvas[y0:y1, x0:x1] |= tight


def main() -> None:
    if sha256(PDF) != EXPECTED_PDF_SHA:
        raise RuntimeError("official PDF identity mismatch")
    out = ROOT / "r168_correction"
    out.mkdir(exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[629]
    pix = page.get_pixmap(dpi=300, alpha=False, clip=CLIP)
    rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].copy()
    draw = page.get_drawings()[26]
    support = stroke_support(draw, pix.width, pix.height, pix.x, pix.y)
    gray_ink = (np.max(255 - rgb, axis=2) >= 20) & (np.max(rgb, axis=2) - np.min(rgb, axis=2) <= 18)
    mask = support & gray_ink
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise RuntimeError("corrected border mask empty")
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    x0, y0, x1, y1 = bbox
    tight = mask[y0:y1, x0:x1]
    Image.fromarray(np.where(tight, 0, 255).astype(np.uint8)).save(out / "G_R_RATIO_CARD_BORDER_corrected_mask.png")

    pad = 12
    rx0, ry0, rx1, ry1 = max(0, x0-pad), max(0, y0-pad), min(pix.width, x1+pad), min(pix.height, y1+pad)
    orig = rgb[ry0:ry1, rx0:rx1]
    overlay = orig.copy()
    local = mask[ry0:ry1, rx0:rx1]
    overlay[local] = (238, 30, 30)
    maskonly = np.repeat(np.where(local[..., None], 0, 255).astype(np.uint8), 3, axis=2)
    strips = [Image.fromarray(orig), Image.fromarray(overlay), Image.fromarray(maskonly)]
    w = sum(im.width for im in strips) + 40
    h = max(im.height for im in strips) + 30
    contact = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(contact)
    xx = 0
    for label, im in zip(("ORIGINAL", "TARGET OVERLAY", "MASK ONLY"), strips):
        d.text((xx, 2), label, fill="black")
        contact.paste(im, (xx, 25))
        xx += im.width + 20
    contact.save(out / "G_R_RATIO_CARD_BORDER_corrected_contact.png")

    objects = list(csv.DictReader((ROOT / "objects/object_manifest.csv").open(encoding="utf-8-sig", newline="")))
    rows = []
    for obj in objects:
        if obj["object_type"] != "TEXT_GLYPH" or obj["panel"] != "R" or obj["parent"] != "R_RATIO_CARD":
            continue
        gb = json.loads(obj["bbox_px"])
        gm = np.array(Image.open(ROOT / obj["mask_path"]).convert("L")) < 128
        gfull = np.zeros(mask.shape, dtype=bool)
        paste_mask(gfull, gm, gb)
        rows.append({
            "object_id": obj["object_id"],
            "corrected_border_intersection_px": int(np.count_nonzero(mask & gfull)),
            "automated_correction_decision": "PASS" if not np.any(mask & gfull) else "FAIL",
        })
    with (out / "card_border_text_recheck.csv").open("w", encoding="utf-8", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wtr.writeheader()
        wtr.writerows(rows)
    summary = {
        "correction_scope": "replace filled-path support with stroke-only support for G_R_RATIO_CARD_BORDER",
        "preserves_raw_evidence": True,
        "corrected_bbox_px": bbox,
        "corrected_area_px": int(mask.sum()),
        "text_objects_rechecked": len(rows),
        "nonzero_text_intersections": sum(r["corrected_border_intersection_px"] > 0 for r in rows),
        "automated_correction_gate": "PASS" if all(r["automated_correction_decision"] == "PASS" for r in rows) else "FAIL",
        "manual_fields_created": False,
    }
    (out / "correction_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
