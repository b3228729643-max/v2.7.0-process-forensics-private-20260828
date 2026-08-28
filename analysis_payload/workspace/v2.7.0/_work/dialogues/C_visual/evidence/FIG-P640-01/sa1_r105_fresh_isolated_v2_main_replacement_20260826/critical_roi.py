from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
ROI = (1500, 250, 1800, 380)


def place_tight(mask_path: Path, bbox: list[int], shape: tuple[int, int]) -> np.ndarray:
    mask = np.asarray(Image.open(mask_path).convert("L")) < 128
    full = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = bbox
    full[y0:y1, x0:x1] = mask[: y1 - y0, : x1 - x0]
    return full


def main() -> None:
    ledger = json.loads((ROOT / "machine" / "object_ledger.json").read_text(encoding="utf-8"))
    objects = {o["id"]: o for o in ledger["objects"]}
    glyph = objects["GLYPH-0109"]
    curve = objects["PATH-RIGHT-ESS-CURVE"]
    original = Image.open(ROOT / "renders" / "figure_crop_300dpi.png").convert("RGB")
    shape = (original.height, original.width)
    gm = place_tight(ROOT / glyph["mask_path"], glyph["mask_bbox"], shape)
    cm = place_tight(ROOT / curve["mask_path"], curve["mask_bbox"], shape)
    inter = gm & cm
    x0, y0, x1, y1 = ROI
    panels = []
    panels.append(original.crop(ROI))
    overlay = np.asarray(original).copy()
    overlay[cm] = np.array([0, 110, 255], dtype=np.uint8)
    overlay[gm] = np.array([255, 0, 0], dtype=np.uint8)
    overlay[inter] = np.array([255, 0, 255], dtype=np.uint8)
    panels.append(Image.fromarray(overlay).crop(ROI))
    for mask in (gm, cm, inter):
        panels.append(Image.fromarray(np.where(mask[y0:y1, x0:x1], 0, 255).astype(np.uint8), mode="L").convert("RGB"))
    labels = ["ORIGINAL", "OVERLAY red=glyph candidate blue=curve magenta=intersection", "A GLYPH TARGET CANDIDATE", "B CURVE FINAL-VISIBLE", "INTERSECTION"]
    out1 = ROOT / "roi" / "right_curve_vs_limit_N_native1x.png"
    out8 = ROOT / "roi" / "right_curve_vs_limit_N_8x_nearest.png"
    panels[0].save(out1)
    cell_w = panels[0].width * 8
    canvas = Image.new("RGB", (cell_w * len(panels), panels[0].height * 8 + 28), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (panel, label) in enumerate(zip(panels, labels)):
        draw.text((i * cell_w + 3, 3), label, fill="black")
        canvas.paste(panel.resize((panel.width * 8, panel.height * 8), Image.Resampling.NEAREST), (i * cell_w, 24))
    canvas.save(out8)
    for name, mask in (("glyph_candidate", gm), ("curve_final_visible", cm), ("intersection", inter)):
        Image.fromarray(np.where(mask[y0:y1, x0:x1], 0, 255).astype(np.uint8), mode="L").save(ROOT / "roi" / f"right_curve_vs_limit_N_{name}_mask.png")
    result = {
        "relationship_id": "REL-GLYPH-0109__PATH-RIGHT-ESS-CURVE",
        "roi_figure_crop_px": list(ROI),
        "roi_full_page_px": [x0 + 300, y0 + 240, x1 + 300, y1 + 240],
        "glyph_candidate_mask_id": "GLYPH-0109",
        "curve_mask_id": "PATH-RIGHT-ESS-CURVE",
        "candidate_intersection_px": int(inter.sum()),
        "native1x": out1.relative_to(ROOT).as_posix(),
        "nearest8x": out8.relative_to(ROOT).as_posix(),
        "machine_scope_note": "Same-color visible fusion prevents machine-only proof of a pure glyph mask; manual native review is required. A positive candidate intersection is not auto-promoted to manual PASS/FAIL by this script.",
    }
    (ROOT / "machine" / "critical_overlap_measurement.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
