from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


FIELDS = [
    "CHECK_ID", "VIEW", "ELEMENT_A_ID", "ELEMENT_A_CLASS", "ELEMENT_B_ID",
    "ELEMENT_B_CLASS", "A_BBOX_X0", "A_BBOX_Y0", "A_BBOX_X1", "A_BBOX_Y1",
    "B_BBOX_X0", "B_BBOX_Y0", "B_BBOX_X1", "B_BBOX_Y1",
    "OVERLAP_PIXEL_COUNT", "CLIP_PIXEL_COUNT", "MIN_CLEARANCE_PX",
    "REQUIRED_CLEARANCE_PX", "PASS_FAIL", "REASON", "EVIDENCE_ROI",
]


def parse_mask(spec: str, rgb: np.ndarray, background: np.ndarray, delta: int) -> np.ndarray:
    if spec == "foreground":
        return np.max(np.abs(rgb.astype(np.int16) - background), axis=2) >= delta
    parts = [int(value) for value in spec.split(",")]
    if len(parts) != 4:
        raise ValueError("mask must be 'foreground' or R,G,B,TOL")
    target = np.asarray(parts[:3], dtype=np.int16)
    tolerance = parts[3]
    return np.max(np.abs(rgb.astype(np.int16) - target), axis=2) <= tolerance


def target_from_spec(spec: str) -> np.ndarray | None:
    if spec == "foreground":
        return None
    parts = [int(value) for value in spec.split(",")]
    return np.asarray(parts[:3], dtype=np.int16)


def occupied_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def crop_evidence(
    image: Image.Image,
    boxes: list[tuple[int, int, int, int]],
    output: Path,
    pad: int = 24,
) -> None:
    left = max(0, min(box[0] for box in boxes) - pad)
    top = max(0, min(box[1] for box in boxes) - pad)
    right = min(image.width, max(box[2] for box in boxes) + pad)
    bottom = min(image.height, max(box[3] for box in boxes) + pad)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.crop((left, top, right, bottom)).save(output, dpi=(300, 300))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate strict overlap/clearance CSV and native 1:1 evidence ROIs."
    )
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    delta = int(manifest.get("foreground_delta", 20))
    background = np.asarray(manifest.get("background", [255, 255, 255]), dtype=np.int16)
    image_cache: dict[str, tuple[Image.Image, np.ndarray]] = {}
    for view, relative_path in manifest["views"].items():
        path = (args.manifest.parent / relative_path).resolve()
        image = Image.open(path).convert("RGB")
        image_cache[view] = (image, np.asarray(image, dtype=np.uint8))

    rows: list[dict] = []
    for check in manifest["checks"]:
        view = check["view"]
        image, rgb = image_cache[view]
        check_type = check.get("type", "pair")
        required = int(check["required_clearance_px"])

        if check_type == "edge":
            foreground = parse_mask("foreground", rgb, background, delta)
            if not foreground.any():
                raise SystemExit(f"{check['id']}: no foreground")
            x0, y0, x1, y1 = occupied_bbox(foreground)
            clip = int(
                np.count_nonzero(foreground[0, :])
                + np.count_nonzero(foreground[-1, :])
                + np.count_nonzero(foreground[:, 0])
                + np.count_nonzero(foreground[:, -1])
            )
            clearance = min(x0, y0, image.width - 1 - x1, image.height - 1 - y1)
            overlap = 0
            a_bbox = (x0, y0, x1, y1)
            b_bbox = (0, 0, image.width - 1, image.height - 1)
            roi_name = f"roi/{check['id']}_{view}_edge_1to1.png"
            roi_path = args.manifest.parent / roi_name
            image.save(roi_path, dpi=(300, 300))
            reason = f"foreground bbox={a_bbox}; native canvas={image.width}x{image.height}; delta={delta}"
        else:
            boxes = [tuple(check["a_box"]), tuple(check["b_box"])]
            full_masks: list[np.ndarray] = []
            actual_boxes: list[tuple[int, int, int, int]] = []
            for box, spec in zip(boxes, [check["a_mask"], check["b_mask"]]):
                left, top, right, bottom = box
                if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
                    raise SystemExit(f"{check['id']}: invalid box {box} for {image.width}x{image.height}")
                local = parse_mask(spec, rgb[top:bottom, left:right], background, delta)
                if not local.any():
                    raise SystemExit(f"{check['id']}: empty mask {spec} in {box}")
                local_y, local_x = np.nonzero(local)
                actual_boxes.append(
                    (
                        int(local_x.min() + left), int(local_y.min() + top),
                        int(local_x.max() + left), int(local_y.max() + top),
                    )
                )
                full = np.zeros(rgb.shape[:2], dtype=bool)
                full[top:bottom, left:right] = local
                full_masks.append(full)
            a_mask, b_mask = full_masks
            shared = a_mask & b_mask
            target_a = target_from_spec(check["a_mask"])
            target_b = target_from_spec(check["b_mask"])
            if shared.any() and target_a is not None and target_b is not None:
                pixels = rgb.astype(np.int16)
                distance_a = np.max(np.abs(pixels - target_a), axis=2)
                distance_b = np.max(np.abs(pixels - target_b), axis=2)
                assign_a = shared & (distance_a <= distance_b)
                assign_b = shared & (distance_b < distance_a)
                a_mask[shared] = False
                b_mask[shared] = False
                a_mask[assign_a] = True
                b_mask[assign_b] = True
            overlap = int(np.count_nonzero(a_mask & b_mask))
            chessboard = int(
                ndimage.distance_transform_cdt(~b_mask, metric="chessboard")[a_mask].min()
            )
            clearance = max(0, chessboard - 1)
            clip = 0
            a_bbox, b_bbox = actual_boxes
            roi_name = f"roi/{check['id']}_{view}_1to1.png"
            crop_evidence(image, boxes, args.manifest.parent / roi_name)
            reason = (
                f"native 300dpi; delta={delta}; masks={check['a_mask']} vs {check['b_mask']}; "
                f"occupiedA={a_bbox}; occupiedB={b_bbox}"
            )

        passed = overlap == 0 and clip == 0 and clearance >= required
        rows.append(
            {
                "CHECK_ID": check["id"],
                "VIEW": view,
                "ELEMENT_A_ID": check["element_a_id"],
                "ELEMENT_A_CLASS": check["element_a_class"],
                "ELEMENT_B_ID": check["element_b_id"],
                "ELEMENT_B_CLASS": check["element_b_class"],
                "A_BBOX_X0": a_bbox[0], "A_BBOX_Y0": a_bbox[1],
                "A_BBOX_X1": a_bbox[2], "A_BBOX_Y1": a_bbox[3],
                "B_BBOX_X0": b_bbox[0], "B_BBOX_Y0": b_bbox[1],
                "B_BBOX_X1": b_bbox[2], "B_BBOX_Y1": b_bbox[3],
                "OVERLAP_PIXEL_COUNT": overlap,
                "CLIP_PIXEL_COUNT": clip,
                "MIN_CLEARANCE_PX": clearance,
                "REQUIRED_CLEARANCE_PX": required,
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "REASON": reason,
                "EVIDENCE_ROI": roi_name,
            }
        )

    output = args.manifest.parent / "after_overlap_report.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["PASS_FAIL"] != "PASS"]
    minimum = min(int(row["MIN_CLEARANCE_PX"]) for row in rows)
    total_overlap = sum(int(row["OVERLAP_PIXEL_COUNT"]) for row in rows)
    total_clip = sum(int(row["CLIP_PIXEL_COUNT"]) for row in rows)
    print(
        f"candidate={manifest['candidate_id']} checks={len(rows)} failures={len(failures)} "
        f"overlap={total_overlap} clip={total_clip} minimum_clearance={minimum}"
    )
    for row in failures:
        print(
            f"FAIL {row['CHECK_ID']} overlap={row['OVERLAP_PIXEL_COUNT']} "
            f"clip={row['CLIP_PIXEL_COUNT']} clearance={row['MIN_CLEARANCE_PX']} "
            f"required={row['REQUIRED_CLEARANCE_PX']}"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
