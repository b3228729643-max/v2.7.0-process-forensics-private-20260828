"""Object-level native replay for the two independent data curves.

This keeps the candidate page's own copied resources and PDF content prefix,
then replaces the page content stream with (background only), (background +
blue curve), and (background + teal curve).  Thus no same-colour threshold,
paint-order contamination, page-white halo, or neighbouring object can enter a
pre-occlusion curve mask.  Each replay is rendered straight from the copied
candidate PDF at native 300 dpi.
"""
from __future__ import annotations

import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
CANDIDATE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
PAGE_INDEX = 169
DPI = 300
SCALE = DPI / 72.0
OUT = ROOT / "object_replay"


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


def render(path: Path) -> np.ndarray:
    doc = fitz.open(path)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    doc.close()
    return image[:, :, :3].copy()


def save_mask(mask: np.ndarray, path: Path) -> tuple[int, tuple[int, int, int, int]]:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").save(path)
    ys, xs = np.where(mask)
    if not len(xs):
        return 0, (0, 0, 0, 0)
    return int(mask.sum()), (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


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
        "O-G001_training_curve_pre": prefix + blue_group,
        "O-G002_validation_curve_pre": prefix + teal_group,
        "both_curves_in_source_draw_order": prefix + blue_group + teal_group,
    }
    renders: dict[str, np.ndarray] = {}
    for name, stream in variants.items():
        pdf = OUT / f"{name}.pdf"
        make_variant(source, stream, pdf)
        image = render(pdf)
        Image.fromarray(image, "RGB").save(OUT / f"{name}_native_300dpi.png")
        renders[name] = image
    source.close()

    baseline = renders["background_only"].astype(np.int16)
    rows = []
    pre_masks: dict[str, np.ndarray] = {}
    for obj, key in (("O-G001", "O-G001_training_curve_pre"), ("O-G002", "O-G002_validation_curve_pre")):
        delta = np.max(np.abs(renders[key].astype(np.int16) - baseline), axis=2)
        # Exact revision-111 foreground condition: at least 20 / 255 contrast
        # from the same independently rendered local background.
        mask = delta >= 20
        pre_masks[obj] = mask
        count, bbox = save_mask(mask, OUT / f"{obj}_independent_pre_raw_mask.png")
        mask8 = Image.open(OUT / f"{obj}_independent_pre_raw_mask.png")
        mask8.resize((mask8.width * 8, mask8.height * 8), Image.Resampling.NEAREST).save(OUT / f"{obj}_independent_pre_raw_mask_8x_nearest.png")
        rows.append({"OBJECT_ID": obj, "REPLAY_PDF": f"object_replay/{key}.pdf", "NATIVE_RENDER": f"object_replay/{key}_native_300dpi.png", "BASELINE_RENDER": "object_replay/background_only_native_300dpi.png", "MASK": f"object_replay/{obj}_independent_pre_raw_mask.png", "THRESHOLD": "max per-channel local-background delta >=20/255", "INK_PX": count, "BBOX": bbox})
    a, b = pre_masks["O-G001"], pre_masks["O-G002"]
    inter = a & b
    count, bbox = save_mask(inter, OUT / "O-G001_O-G002_independent_pre_intersection.png")
    inter8 = Image.open(OUT / "O-G001_O-G002_independent_pre_intersection.png")
    inter8.resize((inter8.width * 8, inter8.height * 8), Image.Resampling.NEAREST).save(OUT / "O-G001_O-G002_independent_pre_intersection_8x_nearest.png")
    # Final-visible masks are recomputed by removal comparison in the exact
    # copied-PDF drawing order.  This preserves antialiased contributions: a
    # pixel belongs to a curve only when removing that curve changes the final
    # composite by >=20/255 relative to the same local background/composite.
    both = renders["both_curves_in_source_draw_order"].astype(np.int16)
    blue_final = np.max(np.abs(both - renders["O-G002_validation_curve_pre"].astype(np.int16)), axis=2) >= 20
    teal_final = np.max(np.abs(both - renders["O-G001_training_curve_pre"].astype(np.int16)), axis=2) >= 20
    final_rows = []
    for obj, mask, comparator in (("O-G001", blue_final, "O-G002_validation_curve_pre_native_300dpi.png"), ("O-G002", teal_final, "O-G001_training_curve_pre_native_300dpi.png")):
        final_count, final_bbox = save_mask(mask, OUT / f"{obj}_final_visible_contribution_mask.png")
        image = Image.open(OUT / f"{obj}_final_visible_contribution_mask.png")
        image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(OUT / f"{obj}_final_visible_contribution_mask_8x_nearest.png")
        final_rows.append({"OBJECT_ID": obj, "FINAL_VISIBLE_MASK": f"object_replay/{obj}_final_visible_contribution_mask.png", "REMOVAL_COMPARATOR": f"object_replay/{comparator}", "INK_PX": final_count, "BBOX": final_bbox})
    final_inter = blue_final & teal_final
    final_count, final_bbox = save_mask(final_inter, OUT / "O-G001_O-G002_final_visible_intersection.png")
    final_inter8 = Image.open(OUT / "O-G001_O-G002_final_visible_intersection.png")
    final_inter8.resize((final_inter8.width * 8, final_inter8.height * 8), Image.Resampling.NEAREST).save(OUT / "O-G001_O-G002_final_visible_intersection_8x_nearest.png")
    (OUT / "curve_replay_manifest.json").write_text(json.dumps({"candidate": str(CANDIDATE), "physical_page": 170, "dpi": DPI, "native_grid": [2481, 3508], "method": "copied candidate page/resources with curve-specific PDF content stream replay", "objects": rows, "final_visible_objects": final_rows, "independent_pre_overlap_px": count, "independent_pre_intersection_bbox": bbox, "final_visible_overlap_px": final_count, "final_visible_intersection_bbox": final_bbox, "draw_order": "O-G001 blue curve is emitted before O-G002 teal curve"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pre_overlap_px": count, "pre_bbox": bbox, "final_visible_overlap_px": final_count, "final_bbox": final_bbox, "rows": rows, "final_rows": final_rows}, ensure_ascii=False))


if __name__ == "__main__":
    main()
