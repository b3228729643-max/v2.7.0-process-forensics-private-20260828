from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


R97 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
R98 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf")
R98_LOG = R98.with_suffix(".log")
R98_FLS = R98.with_suffix(".fls")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_transition_graph.tex")
OUT = Path(__file__).resolve().parent
PHYSICAL_PAGE = 591
PRINTED_PAGE = 578
FIG_RECT_PT = (60.0, 285.0, 535.0, 470.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def run_text(args: list[str]) -> str:
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        raise RuntimeError(f"command failed {proc.returncode}: {args}\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout


def render_poppler(dpi: int, gray: bool = False) -> Path:
    suffix = "_gray" if gray else ""
    prefix = OUT / f"official_R98_physical_{PHYSICAL_PAGE}_full_page_{dpi}dpi{suffix}"
    args = [
        "pdftoppm",
        "-r", str(dpi),
        "-f", str(PHYSICAL_PAGE),
        "-l", str(PHYSICAL_PAGE),
    ]
    if gray:
        args.append("-gray")
    args.extend(["-png", "-singlefile", str(R98), str(prefix)])
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (OUT / f"pdftoppm_{dpi}dpi{suffix}.log").write_text(
        "COMMAND: " + " ".join(args) + f"\nEXIT={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        encoding="utf-8",
    )
    if proc.returncode:
        raise RuntimeError(f"pdftoppm failed: {args}")
    output = prefix.with_suffix(".png")
    if not output.exists():
        raise RuntimeError(f"missing render: {output}")
    return output


def page_raster_hash(page: fitz.Page) -> str:
    pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), colorspace=fitz.csGRAY, alpha=False)
    h = hashlib.sha256()
    h.update(pix.width.to_bytes(4, "little"))
    h.update(pix.height.to_bytes(4, "little"))
    h.update(pix.samples)
    return h.hexdigest().upper()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for required in (R97, R98, R98_LOG, R98_FLS, SOURCE):
        if not required.exists():
            raise FileNotFoundError(required)

    r97 = fitz.open(R97)
    r98 = fitz.open(R98)
    if r97.page_count != 813 or r98.page_count != 813:
        raise AssertionError((r97.page_count, r98.page_count))

    media = set()
    crop = set()
    rotations = set()
    for page in r98:
        media.add(tuple(round(x, 3) for x in (page.mediabox.width, page.mediabox.height)))
        crop.add(tuple(round(x, 3) for x in (page.cropbox.width, page.cropbox.height)))
        rotations.add(page.rotation)

    changed: list[int] = []
    for index in range(813):
        if page_raster_hash(r97[index]) != page_raster_hash(r98[index]):
            changed.append(index + 1)

    changed_page_detail: dict[str, object] = {}
    if changed == [PHYSICAL_PAGE]:
        matrix = fitz.Matrix(300 / 72, 300 / 72)
        old_pix = r97[PHYSICAL_PAGE - 1].get_pixmap(matrix=matrix, colorspace=fitz.csGRAY, alpha=False)
        new_pix = r98[PHYSICAL_PAGE - 1].get_pixmap(matrix=matrix, colorspace=fitz.csGRAY, alpha=False)
        old_arr = np.frombuffer(old_pix.samples, dtype=np.uint8).reshape(old_pix.height, old_pix.width)
        new_arr = np.frombuffer(new_pix.samples, dtype=np.uint8).reshape(new_pix.height, new_pix.width)
        delta = old_arr != new_arr
        ys, xs = np.where(delta)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        mask = np.where(delta, 0, 255).astype(np.uint8)
        Image.fromarray(mask, mode="L").save(OUT / "R97_to_R98_physical_591_diff_mask_300dpi.png")
        changed_page_detail = {
            "size_px": [new_pix.width, new_pix.height],
            "changed_pixels": int(delta.sum()),
            "changed_fraction": float(delta.mean()),
            "diff_bbox_px": bbox,
            "diff_mask_file": "R97_to_R98_physical_591_diff_mask_300dpi.png",
        }

    page_text = r98[PHYSICAL_PAGE - 1].get_text()
    metadata_format = r98.metadata.get("format", "")
    encrypted = bool(r98.is_encrypted)
    r97.close()
    r98.close()

    log_text = R98_LOG.read_text(encoding="utf-8", errors="replace")
    patterns = {
        "bang": r"(?m)^!",
        "latex_error": r"LaTeX Error",
        "package_error": r"Package\s+\S+\s+Error",
        "undefined_control": r"Undefined control sequence",
        "emergency": r"Emergency stop",
        "fatal": r"Fatal error",
        "lost_float": r"Float\(s\) lost",
        "undefined_references": r"There were undefined references",
        "undefined_citations": r"There were undefined citations",
        "multiply_defined": r"multiply defined",
        "duplicate_destination": r"destination with the same identifier|duplicate[^\n]*destination",
        "unreferenced_destination": r"unreferenced destination",
        "overfull": r"Overfull \\[hv]box",
        "underfull": r"Underfull \\[hv]box",
        "missing_character": r"Missing character",
        "rerun": r"Rerun to get cross-references right|Label\(s\) may have changed|Please \(re\)run|rerunfilecheck Warning",
        "no_pages": r"No pages of output",
        "runaway": r"Runaway argument",
        "file_ended_while_scanning": r"File ended while scanning use of",
    }
    hard_scan = {name: len(re.findall(pattern, log_text, flags=re.IGNORECASE)) for name, pattern in patterns.items()}

    pdffonts_text = run_text(["pdffonts", str(R98)])
    (OUT / "R98_pdffonts.txt").write_text(pdffonts_text, encoding="utf-8")
    font_lines = [line for line in pdffonts_text.splitlines()[2:] if line.strip()]
    noncompliant = []
    for line in font_lines:
        fields = line.split()
        if len(fields) < 8 or fields[-5:-2] != ["yes", "yes", "yes"]:
            noncompliant.append(line)

    pdfinfo_text = run_text(["pdfinfo", str(R98)])
    (OUT / "R98_pdfinfo.txt").write_text(pdfinfo_text, encoding="utf-8")

    normalized_source = os.path.normcase(os.path.normpath(str(SOURCE.resolve())))
    fls_hits = 0
    for line in R98_FLS.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("INPUT "):
            continue
        candidate = os.path.normcase(os.path.normpath(line[6:].strip()))
        if candidate == normalized_source:
            fls_hits += 1

    full300 = render_poppler(300)
    full200 = render_poppler(200)
    full300gray = render_poppler(300, gray=True)
    with Image.open(full300) as im:
        sx = im.width / 595.276
        sy = im.height / 841.89
        crop_px = [
            int(round(FIG_RECT_PT[0] * sx)),
            int(round(FIG_RECT_PT[1] * sy)),
            int(round(FIG_RECT_PT[2] * sx)),
            int(round(FIG_RECT_PT[3] * sy)),
        ]
        figure_crop = im.crop(tuple(crop_px))
        figure_crop.save(OUT / "official_R98_physical_591_figure30_2_caption_crop_300dpi.png")
        full300_size = [im.width, im.height]
    with Image.open(full200) as im:
        full200_size = [im.width, im.height]
    with Image.open(full300gray) as im:
        gray_crop = im.crop(tuple(crop_px))
        gray_crop.save(OUT / "official_R98_physical_591_figure30_2_caption_crop_300dpi_gray.png")

    result = {
        "schema": "FIG-P547-01_ROOT_R98_FREEZE_v1",
        "official_pdf": str(R98).replace("\\", "/"),
        "source": {
            "path": str(SOURCE).replace("\\", "/"),
            "bytes": SOURCE.stat().st_size,
            "sha256": sha256(SOURCE),
            "fls_input_hits": fls_hits,
        },
        "build": {
            "command": "powershell -ExecutionPolicy Bypass -File build_v2.7.0.ps1 -OutputDir src\\build\\strict_current_r98_fullbook -NoPublish",
            "result": "PASS",
            "exit_code": 0,
            "bytes": R98.stat().st_size,
            "sha256": sha256(R98),
            "pages": 813,
            "pdf_format": metadata_format,
            "encrypted": encrypted,
            "all_pages_a4": media == {(595.276, 841.89)} and crop == {(595.276, 841.89)},
            "unique_media_box_pt": sorted(media),
            "unique_crop_box_pt": sorted(crop),
            "rotations": sorted(rotations),
            "embedded_subset_unicode_font_rows": len(font_lines) - len(noncompliant),
            "noncompliant_font_rows": len(noncompliant),
            "hard_log_pattern_matches": sum(hard_scan.values()),
        },
        "hard_log_scan": hard_scan,
        "r97_to_r98_raster_identity": {
            "method": "PyMuPDF direct page raster SHA-256",
            "comparison_dpi": 72,
            "colorspace": "grayscale",
            "pages_compared": 813,
            "identical_pages": 813 - len(changed),
            "changed_pages": changed,
            f"page_{PHYSICAL_PAGE}_300dpi": changed_page_detail,
        },
        "figure": {
            "uid": "FIG-P547-01",
            "number": "30.2",
            "physical_page": PHYSICAL_PAGE,
            "printed_page": PRINTED_PAGE,
            "printed_page_text_match": page_text.startswith(f"{PRINTED_PAGE}\n"),
            "figure_text_match": "图30.2" in page_text,
            "rewritten_label_text_match": "物理边" in page_text,
            "full_page_300dpi_px": full300_size,
            "full_page_300dpi_file": full300.name,
            "full_page_200dpi_px": full200_size,
            "full_page_200dpi_file": full200.name,
            "crop_from_full_page_300dpi_px": crop_px,
            "crop_size_px": [figure_crop.width, figure_crop.height],
            "color_crop_file": "official_R98_physical_591_figure30_2_caption_crop_300dpi.png",
            "grayscale_crop_file": "official_R98_physical_591_figure30_2_caption_crop_300dpi_gray.png",
        },
        "root_precheck": {
            "native_300dpi_full_page_viewed": False,
            "native_200dpi_full_page_viewed": False,
            "native_300dpi_color_crop_viewed_1_to_1": False,
            "native_300dpi_grayscale_crop_viewed_1_to_1": False,
            "diff_mask_viewed": False,
            "visible_overlap_or_clipping_found": None,
            "font_hierarchy_visibly_abrupt": None,
            "verdict": "PENDING_ROOT_VIEW",
        },
    }
    (OUT / "R98_BUILD_AND_PAGE_FREEZE.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
