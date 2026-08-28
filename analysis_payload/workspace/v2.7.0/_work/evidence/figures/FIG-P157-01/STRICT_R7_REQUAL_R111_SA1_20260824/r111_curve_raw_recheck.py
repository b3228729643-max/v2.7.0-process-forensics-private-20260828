"""Revision-111 raw final-visible recheck for FIG-P157-01's two data curves.

The masks are reconstructed from the current authoritative PDF page by replaying
each curve's own PDF content group against the identical prefix/background.  A
peer curve is deliberately never removed by an image difference: final-visible
means the raw mask less only a later, truly opaque, *external* object.  This
implements the R111 rule without paint-order contribution artefacts.
"""
from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
CANDIDATE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
PAGE_INDEX = 169  # physical page 170
DPI = 300
THRESHOLD = 20
# The first attempted replay directory is preserved as an interrupted artifact;
# this corrected continuation owns the complete R111 package.
OUT = ROOT / "r111_curve_raw_recheck_v2"


def make_variant(source: fitz.Document, stream: bytes, destination: Path) -> None:
    replay = fitz.open()
    replay.insert_pdf(source, from_page=PAGE_INDEX, to_page=PAGE_INDEX)
    page = replay[0]
    xref = replay.get_new_xref()
    replay.update_object(xref, "<<>>")
    replay.update_stream(xref, stream)
    page.set_contents(xref)
    replay.save(destination, garbage=4, deflate=True)
    replay.close()


def render_pdf(pdf: Path, png_stem: Path, page_number: int | None = None) -> np.ndarray:
    command = ["pdftoppm", "-png", "-singlefile", "-r", str(DPI)]
    if page_number is not None:
        command.extend(["-f", str(page_number), "-l", str(page_number)])
    command.extend([str(pdf), str(png_stem)])
    subprocess.run(command, check=True, capture_output=True)
    return np.asarray(Image.open(png_stem.with_suffix(".png")).convert("RGB"), dtype=np.uint8)


def mask_from_replay(render: np.ndarray, baseline: np.ndarray) -> np.ndarray:
    # Exact native 1x local-background foreground condition; no dilation or resize.
    return np.max(np.abs(render.astype(np.int16) - baseline.astype(np.int16)), axis=2) >= THRESHOLD


def bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if not len(xs):
        return (0, 0, 0, 0)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").save(path)


def save_roi_assets(candidate: np.ndarray, a: np.ndarray, b: np.ndarray, intersection: np.ndarray, roi: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = roi
    raw = Image.fromarray(candidate[y0:y1, x0:x1], "RGB")
    local_a = a[y0:y1, x0:x1]
    local_b = b[y0:y1, x0:x1]
    local_i = intersection[y0:y1, x0:x1]
    mask_a = Image.fromarray(np.where(local_a, 0, 255).astype(np.uint8), "L")
    mask_b = Image.fromarray(np.where(local_b, 0, 255).astype(np.uint8), "L")
    mask_i = Image.fromarray(np.where(local_i, 0, 255).astype(np.uint8), "L")
    overlay = np.full((*local_a.shape, 3), 255, dtype=np.uint8)
    overlay[local_a] = (0, 80, 255)
    overlay[local_b] = (255, 55, 0)
    overlay[local_i] = (220, 0, 220)
    assets = {
        "original_raw_1x.png": raw,
        "mask_A_training_1x.png": mask_a,
        "mask_B_validation_1x.png": mask_b,
        "intersection_1x.png": mask_i,
        "overlay_1x.png": Image.fromarray(overlay, "RGB"),
    }
    for name, image in assets.items():
        image.save(OUT / name)
        image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(
            OUT / name.replace("_1x.png", "_8x_nearest.png")
        )


def distance_to_zero(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    # The explicit intersection test is exact; zero is the required clearance for a collision.
    return 0.0 if bool((mask_a & mask_b).any()) else float("inf")


def source_math() -> dict[str, float | bool]:
    train = lambda x: 0.36 + 3.35 * math.exp(-0.34 * x)
    validation = lambda x: 1.08 + 0.105 * (x - 5.25) ** 2
    gap = lambda x: validation(x) - train(x)
    derivative = lambda x: 0.21 * (x - 5.25) + 1.139 * math.exp(-0.34 * x)
    roots: list[float] = []
    x_prev, d_prev = 0.0, derivative(0.0)
    for index in range(1, 100001):
        x_now = index / 10000
        d_now = derivative(x_now)
        if d_prev == 0 or d_prev * d_now < 0:
            lo, hi = x_prev, x_now
            for _ in range(80):
                mid = (lo + hi) / 2
                if derivative(lo) * derivative(mid) <= 0:
                    hi = mid
                else:
                    lo = mid
            roots.append((lo + hi) / 2)
        x_prev, d_prev = x_now, d_now
    candidates = [0.0, *roots, 10.0]
    minimum_x = min(candidates, key=gap)
    y_pixels = 898.0  # native axis interior: y=283..1181 from the same candidate grid
    gap_px = gap(minimum_x) * y_pixels / 4.35
    combined_radius_px = 0.5 * (1.00 + 1.05) * DPI / 72.0
    return {
        "domain_min": 0.0,
        "domain_max": 10.0,
        "minimum_gap_x": minimum_x,
        "minimum_function_gap_y_units": gap(minimum_x),
        "minimum_function_gap_px": gap_px,
        "combined_stroke_radius_px": combined_radius_px,
        "source_functions_cross": gap(minimum_x) <= 0.0,
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    source = fitz.open(CANDIDATE)
    content = source[PAGE_INDEX].read_contents().decode("latin1")
    blue_start = content.index("q \n0.99628 w \n1 J \n1 j \n0.12158 0.30588 0.47452 RG ")
    teal_start = content.index("q \n0.99628 w \n1 J \n1 j \n0.05882 0.46275 0.43137 RG ", blue_start)
    ref_start = content.index("q \n0.99628 w \n1 J \n1 j \n0.58212 0.60188 0.6414 RG ", teal_start)
    prefix = content[:blue_start].encode("latin1")
    blue_group = content[blue_start:teal_start].encode("latin1")
    teal_group = content[teal_start:ref_start].encode("latin1")
    variants = {
        "background_only": prefix,
        "training_only": prefix + blue_group,
        "validation_only": prefix + teal_group,
        "source_order_both": prefix + blue_group + teal_group,
    }
    replay_renders: dict[str, np.ndarray] = {}
    for name, stream in variants.items():
        replay_pdf = OUT / f"{name}.pdf"
        make_variant(source, stream, replay_pdf)
        replay_renders[name] = render_pdf(replay_pdf, OUT / f"{name}_native_300dpi")
    source.close()
    candidate = render_pdf(CANDIDATE, OUT / "candidate_page_native_300dpi", page_number=170)
    baseline = replay_renders["background_only"]
    training_raw = mask_from_replay(replay_renders["training_only"], baseline)
    validation_raw = mask_from_replay(replay_renders["validation_only"], baseline)
    if candidate.shape != baseline.shape:
        raise RuntimeError(f"candidate/replay grid mismatch: {candidate.shape} vs {baseline.shape}")

    # Later opaque external objects only.  Peer curves are intentionally excluded.
    opaque_ids = ["O-G003", "O-G004", "O-G005", "O-G006", "O-G007", "O-G008", "O-G009", *[f"E{i:03d}" for i in range(1, 12)]]
    with (ROOT / "object_inventory.csv").open("r", encoding="utf-8", newline="") as handle:
        object_rows = {row["OBJECT_ID"]: row for row in csv.DictReader(handle)}
    opaque_union = np.zeros(training_raw.shape, dtype=bool)
    opaque_rows = []
    for object_id in opaque_ids:
        path = ROOT / "object_masks" / f"{object_id}_final_visible_mask.png"
        image = np.asarray(Image.open(path).convert("L"), dtype=np.uint8)
        local_mask = image == 0
        row = object_rows[object_id]
        x0, y0, x1, y1 = (int(row[key]) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        if local_mask.shape != (y1 - y0, x1 - x0):
            raise RuntimeError(f"object local-mask/bbox mismatch for {object_id}: {local_mask.shape} vs {(y1-y0, x1-x0)}")
        mask = np.zeros_like(opaque_union)
        mask[y0:y1, x0:x1] = local_mask
        opaque_union |= mask
        opaque_rows.append({
            "OBJECT_ID": object_id,
            "MASK": str(path.relative_to(ROOT)).replace("\\", "/"),
            "POST_CURVE_TRUE_OPAQUE_EXTERNAL": True,
            "INTERSECTS_TRAINING_RAW_PX": int((mask & training_raw).sum()),
            "INTERSECTS_VALIDATION_RAW_PX": int((mask & validation_raw).sum()),
            "INTERSECTS_PAIR_RAW_INTERSECTION_PX": int((mask & training_raw & validation_raw).sum()),
        })
    # O-H001..O-H003 are not in opaque_union: source lines 7/9 use fill opacity=.90.
    training_final = training_raw & ~opaque_union
    validation_final = validation_raw & ~opaque_union
    intersection_raw = training_raw & validation_raw
    intersection_final = training_final & validation_final
    if not bool(intersection_final.any()):
        raise RuntimeError("unexpected no final-visible collision")
    for name, mask in {
        "O-G001_raw_pre_occlusion_mask_1x.png": training_raw,
        "O-G002_raw_pre_occlusion_mask_1x.png": validation_raw,
        "O-G001_final_visible_rawmask_1x.png": training_final,
        "O-G002_final_visible_rawmask_1x.png": validation_final,
        "O-G001_O-G002_raw_intersection_1x.png": intersection_raw,
        "O-G001_O-G002_final_visible_intersection_1x.png": intersection_final,
        "post_curve_true_opaque_external_union_1x.png": opaque_union,
    }.items():
        save_mask(mask, OUT / name)
    inter_box = bbox(intersection_final)
    x0, y0, x1, y1 = inter_box
    pad = 16
    roi = (max(0, x0 - pad), max(0, y0 - pad), min(candidate.shape[1], x1 + pad), min(candidate.shape[0], y1 + pad))
    save_roi_assets(candidate, training_final, validation_final, intersection_final, roi)
    with (OUT / "post_curve_opaque_external_intersections.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(opaque_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(opaque_rows)
    math_result = source_math()
    summary = {
        "figure_id": "FIG-P157-01",
        "candidate_pdf": str(CANDIDATE),
        "physical_page": 170,
        "printed_page": 157,
        "renderer": "pdftoppm -png -singlefile -r 300; no resize",
        "native_grid_px": [int(candidate.shape[1]), int(candidate.shape[0])],
        "threshold": "max per-channel local-background delta >=20/255 at native 1x",
        "mask_construction": "each curve: current PDF content-group replay against identical prefix/background; no peer-curve removal, dilation, erosion, or resampling",
        "final_visible_rule": "raw curve mask minus union of later true-opaque external objects only; peer data curve excluded; O-H001..O-H003 excluded because source fill opacity=.90",
        "source_draw_order": "O-G001 training curve then O-G002 validation curve",
        "training_raw_ink_px": int(training_raw.sum()),
        "validation_raw_ink_px": int(validation_raw.sum()),
        "training_final_visible_ink_px": int(training_final.sum()),
        "validation_final_visible_ink_px": int(validation_final.sum()),
        "raw_overlap_px": int(intersection_raw.sum()),
        "final_visible_overlap_px": int(intersection_final.sum()),
        "final_visible_intersection_bbox_px": list(inter_box),
        "final_visible_min_clearance_px": distance_to_zero(training_final, validation_final),
        "roi_global_px": list(roi),
        "opaque_external_objects": opaque_rows,
        "all_opaque_external_pair_intersection_px": int((opaque_union & intersection_raw).sum()),
        "math_semantics": math_result,
        "verdict": "FAIL: semantically independent source curves have a nonzero final-visible raw-mask intersection",
    }
    (OUT / "R111_CURVE_RAW_RECHECK.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
