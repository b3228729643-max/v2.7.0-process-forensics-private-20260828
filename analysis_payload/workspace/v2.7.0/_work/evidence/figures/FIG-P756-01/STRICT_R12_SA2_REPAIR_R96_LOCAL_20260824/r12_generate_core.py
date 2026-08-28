"""Run the sealed R115 native-mask generator against the repaired local page wrapper.

This adapter changes only candidate/page coordinates, page-local drawing sequence
numbers, and R12 provenance labels.  The sealed mask, glyph, pair, ROI, clipping,
and contact-sheet algorithms are reused verbatim.
"""
from __future__ import annotations

import csv
import importlib.util
import inspect
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "STRICT_R9_REQUAL_R115_SA1_20260824" / "r115_generate_core.py"
CANDIDATE = ROOT / "build" / "page" / "FIG-P756-01_R12_page.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex")


def load_sealed():
    spec = importlib.util.spec_from_file_location("sealed_r115_generate_core", OLD)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load sealed R115 generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def patch_main(module) -> None:
    source = inspect.getsource(module.main)
    source = source.replace("if len(doc) != 813:", "if len(doc) != 1:")
    source = source.replace(
        'figure_spans = [span for span in spans if 170 <= span["bbox"][1] < 520]',
        'figure_spans = [span for span in spans if 118 <= span["bbox"][1] < 467]',
    )
    source = source.replace(
        'seqs if object_id != "O-G024" else [85]',
        'seqs if object_id != "O-G024" else [78]',
    )
    source = source.replace(
        '"true" if intentional or not passed or clearance < required + 3 else "false"',
        '"true" if pair_index == 1408 or intentional or not passed or clearance < required + 3 else "false"',
    )
    exec(source, module.__dict__)


def normalize_provenance() -> None:
    replacements = {
        "official R95 PDF p801 direct native 300dpi grid": "local R12 page-wrapper p1 direct native 300dpi grid",
        "official R95 p801 native300dpi": "local R12 page-wrapper p1 native300dpi",
        "official R95 final PDF p801 native300dpi 1:1": "local R12 page-wrapper final PDF p1 native300dpi 1:1",
        "official R95 p801 direct pdftoppm 300dpi, no resize": "local R12 page-wrapper p1 direct pdftoppm 300dpi, no resize",
        "official candidate/source absent": "local R12 candidate/source absent",
        "R115_CLIP_PASS": "R12_CLIP_PASS",
        "R115_CLIP_NOTE": "R12_CLIP_NOTE",
    }
    for path in ROOT.glob("*.csv"):
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8", newline="")
    for path in (ROOT / "roi_packages").glob("*/package_manifest.json"):
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


def write_text_overlay() -> None:
    native = ROOT / "renders" / "full_page_native_300dpi.png"
    shutil.copyfile(native, ROOT / "full_page_300dpi.png")
    image = Image.open(native).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    with (ROOT / "glyph_file_manifest.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        box = tuple(int(row[key]) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        draw.rectangle(box, outline=(220, 0, 0), width=1)
        draw.text((box[0], max(0, box[1] - 10)), row["GLYPH_ID"], fill=(160, 0, 0), font=font)
    image.save(ROOT / "after_text_measurement_overlay_300dpi.png")


def main() -> None:
    module = load_sealed()
    module.ROOT = ROOT
    module.CANDIDATE = CANDIDATE
    module.SOURCE = SOURCE
    module.PAGE_NUMBER = 1
    module.PRINTED_PAGE = 753
    module.FIGURE_PDF_RECT = (65.0, 118.0, 540.0, 470.0)
    module.STANDALONE_PDF_RECT = (65.0, 118.0, 540.0, 426.0)
    module.GRAPH_SPECS = [
        (oid, kind, name, line, [seq - 7 for seq in seqs], mode)
        for oid, kind, name, line, seqs, mode in module.GRAPH_SPECS
    ]
    oid, kind, name, line, seqs = module.HALO_SPEC
    module.HALO_SPEC = (oid, kind, name, line, [seq - 7 for seq in seqs])
    patch_main(module)
    module.main()
    normalize_provenance()
    write_text_overlay()
    old_summary = ROOT / "R115_CORE_GENERATION_SUMMARY.json"
    summary = json.loads(old_summary.read_text(encoding="utf-8"))
    summary["candidate_scope"] = "local page-wrapper p1; not the root official full-book candidate"
    (ROOT / "R12_CORE_GENERATION_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    old_summary.unlink()


if __name__ == "__main__":
    main()
