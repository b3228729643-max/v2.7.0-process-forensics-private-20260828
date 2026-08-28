from __future__ import annotations

import csv
import itertools
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from mechanical_prepare_evidence import OBJECTS, px_box


ROOT = Path(__file__).resolve().parent
REF = {
    "black": np.array([31, 35, 40], dtype=np.int16),
    "gray": np.array([77, 83, 88], dtype=np.int16),
    "lightgray": np.array([184, 192, 200], dtype=np.int16),
    "green": np.array([47, 125, 109], dtype=np.int16),
    "blue": np.array([31, 78, 121], dtype=np.int16),
    "red": np.array([178, 58, 72], dtype=np.int16),
}
ALLOWED = {
    "O01": ("black",),
    "O02": ("gray",),
    "O03": ("gray",),
    "O04": ("lightgray",),
    "O05": ("green",),
    "O06": ("blue",),
    "O07": ("green",),
    "O08": ("black",),
    "O09": ("blue",),
    "O10": ("black", "blue"),
    "O11": ("blue",),
    "O12": ("black", "blue"),
    "O13": ("blue",),
    "O14": ("green",),
    "O15": ("black",),
    "O16": ("black",),
    "O17": ("gray",),
    "O18": ("green",),
    "O19": ("green",),
    "O20": ("green",),
    "O21": ("blue",),
    "O22": ("black",),
    "O23": ("black",),
    "O24": ("gray",),
    "O25": ("blue",),
    "O26": ("blue",),
    "O27": ("blue",),
    "O28": ("red",),
    "O29": ("gray", "black"),
    "O30": ("black",),
    "O31": ("gray", "black"),
}


def main() -> None:
    image = Image.open(ROOT / "full_page_300dpi.png").convert("RGB")
    rgb = np.asarray(image, dtype=np.int16)
    masks: dict[str, np.ndarray] = {}
    color_names = tuple(REF)
    references = np.stack([REF[name] for name in color_names], axis=0)
    for object_id, _, _, pdf_box in OBJECTS:
        x0, y0, x1, y1 = px_box(pdf_box)
        local = rgb[y0:y1, x0:x1]
        delta = local[:, :, None, :] - references[None, None, :, :]
        distance2 = np.sum(delta * delta, axis=3)
        nearest = np.argmin(distance2, axis=2)
        nearest_distance2 = np.min(distance2, axis=2)
        allowed_indices = [color_names.index(name) for name in ALLOWED[object_id]]
        accepted = np.isin(nearest, allowed_indices) & (nearest_distance2 <= 60 * 60)
        full = np.zeros(rgb.shape[:2], dtype=bool)
        full[y0:y1, x0:x1] = accepted
        masks[object_id] = full

    rows = []
    membership = np.zeros(rgb.shape[:2], dtype=np.uint8)
    for mask in masks.values():
        membership += mask.astype(np.uint8)
    pairwise_total = 0
    nonzero_pairs = 0
    for pair_index, (left, right) in enumerate(itertools.combinations(OBJECTS, 2), start=1):
        left_id, left_class = left[0], left[1]
        right_id, right_class = right[0], right[1]
        count = int(np.count_nonzero(masks[left_id] & masks[right_id]))
        pairwise_total += count
        if count:
            nonzero_pairs += 1
        rows.append(
            {
                "pair_id": f"P{pair_index:03d}",
                "object_a": left_id,
                "object_b": right_id,
                "class_a": left_class,
                "class_b": right_class,
                "mechanical_shared_mask_pixel_count": count,
            }
        )
    with (ROOT / "mechanical_pixel_pair_candidates.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    candidate = membership > 1
    overlay = np.asarray(image).copy()
    overlay[candidate] = (255, 0, 180)
    figure_crop = px_box((62, 55, 533, 451))
    Image.fromarray(overlay).crop(figure_crop).save(ROOT / "candidate_pixel_overlay_300dpi.png")

    font = ImageFont.load_default()
    tile_w, tile_h = 260, 220
    sheet = Image.new("RGB", (8 * tile_w, 4 * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (object_id, _, label, pdf_box) in enumerate(OBJECTS):
        row, col = divmod(index, 8)
        x0, y0, x1, y1 = px_box(pdf_box)
        local = Image.fromarray((~masks[object_id][y0:y1, x0:x1] * 255).astype(np.uint8))
        local.thumbnail((tile_w - 12, tile_h - 32), Image.Resampling.NEAREST)
        left = col * tile_w + (tile_w - local.width) // 2
        top = row * tile_h + 24 + (tile_h - 28 - local.height) // 2
        sheet.paste(local.convert("RGB"), (left, top))
        draw.text((col * tile_w + 4, row * tile_h + 4), f"{object_id} {label}", fill="black", font=font)
    sheet.save(ROOT / "mechanical_object_mask_contact_sheet.png")

    (ROOT / "mechanical_pixel_candidate_summary.txt").write_text(
        f"pair_count={len(rows)}\n"
        f"nonzero_candidate_pair_count={nonzero_pairs}\n"
        f"pairwise_candidate_pixel_total={pairwise_total}\n"
        f"unique_multiassigned_pixel_count={int(np.count_nonzero(candidate))}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
