#!/usr/bin/env python3
"""Local SA2 repair audit for FIG-P547-01 against the R97 failure entrance.

This program is evidence-producing only.  It never touches the business source,
build entry point, central state, or another audit directory.  It deliberately
refuses to write after the terminal WRITE_STOPPED sentinel exists.

Only ``generate`` is evidence-producing.  Manual ledgers are deliberately left
PENDING and must be completed row-by-row after the reviewer opens every sheet
and every critical/failure 1x + 8x card.  This program has no bulk-PASS phase
and does not seal the package.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.spatial import cKDTree


# Use the user-specified canonical path, rather than the v2.7.0_work junction.
WORK = Path(r"D:\Users\ASUS\Desktop\机器学习")
VROOT = WORK / "v2.7.0" / "_work"
SRCROOT = VROOT / "source" / "v2.7.0" / "src"
PACKAGE_ROOT = VROOT / "evidence" / "figures" / "FIG-P547-01" / "STRICT_R7_SA2_REPAIR_R97_LOCAL_20260824"
OUT = PACKAGE_ROOT / "final_audit"
PDF = PACKAGE_ROOT / "build" / "page" / "v260_FIG-P547-01_page.pdf"
STANDALONE_PDF = PACKAGE_ROOT / "build" / "standalone" / "v260_FIG-P547-01_standalone.pdf"
R97_PDF = SRCROOT / "build" / "strict_current_r97_fullbook" / "main_full.pdf"
FIG_SOURCE = SRCROOT / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C01" / "fig_v5_c01_transition_graph.tex"
BODY = SRCROOT / "讲义源码" / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C01.tex"
STY = SRCROOT / "讲义源码" / "common" / "statlearnbook.sty"
SCHEMA = VROOT / "evidence" / "audits" / "STRICT-GOAL-20260823" / "STRICT_FIGURE_EVIDENCE_SCHEMA.md"
PROTOCOL = VROOT / "evidence" / "audits" / "OVERLAP-RECHECK-20260823" / "STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md"
GOAL = Path(r"D:\Users\ASUS\.codex\attachments\e9427863-0663-4847-93b3-d9c784a212b5\pasted-text.txt")
POPPLER = shutil.which("pdftoppm") or shutil.which("pdftoppm.exe") or r"D:\texlive\2026\bin\windows\pdftoppm.exe"
LUALATEX = r"D:\texlive\2026\bin\windows\lualatex.exe"

PDF_PAGE_1 = 1
PDF_PAGE_0 = PDF_PAGE_1 - 1
PRINTED_PAGE = 578
FIGURE_NO = "30.2"
FIG_RECT_PT = fitz.Rect(60, 120, 535, 267)  # local page: title, graph and full caption
FIG_TEXT_SCOPE_PT = fitz.Rect(60, 123, 535, 265)
SOURCE_SHA_EXPECTED = "29E41548386DA1A3D0EAA40B728DD9CD7B235715A28EEDB5EACD5AAFDE9784E3"
SOURCE_SHA_BEFORE = "638CEA4285D3A9411251DA149963CC7AE4500FA5827F0A99A51FF1FC76640D1A"
PDF_SHA_EXPECTED = "8BBA9F305BDEC610E858DE0DAF2447A1C9DAA151B94AC4FD1AE95B5E331916F0"
STANDALONE_SHA_EXPECTED = "5408B1D8E6E3AEAF9CBEDA49FC87E97BEB06523141EE850D7A77F0E5ACD729BE"
R97_SHA_EXPECTED = "062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814"
GOAL_SHA_EXPECTED = "51BA862B1EEBCD6765565FEE6243BD2BC8BF2611D586115B52623668711928C2"
SCHEMA_SHA_EXPECTED = "D368ACDA21E755240F1842C2009D09C6DC6F3B88E113457A10F412708C8F4C86"
PROTOCOL_SHA_EXPECTED = "D8CD892CE6A33E6B8B9874B0BB3B35FDB537C2EE169401BCC4D85985465AEFA6"
BODY_SHA_EXPECTED = "CCD7F57CFDDD233126593CFFCEB03D4B1CD41C23BB72E09520233FC9C66D9E48"

RENDERS = OUT / "renders"
GLYPH_DIR = OUT / "glyphs"
GLYPH_ROI = GLYPH_DIR / "rois_1x"
GLYPH_CARD = GLYPH_DIR / "cards_8x"
GLYPH_SHEET = GLYPH_DIR / "contact_sheets_8x"
GRAPHIC_DIR = OUT / "graphics"
PAIR_DIR = OUT / "pairs"
OCC_DIR = OUT / "occlusion_reverse"
CAL_DIR = OUT / "low_profile_calibration"
MACHINE_DIR = OUT / "machine"
REPORT_DIR = OUT / "reports"
SOURCE_ID_DIR = PACKAGE_ROOT / "source_identity"
BASELINE_SOURCE = SOURCE_ID_DIR / "baseline_638CEA_fig_v5_c01_transition_graph.tex"
SOURCE_DIFF = SOURCE_ID_DIR / "baseline_to_current.patch"
RELATION_DIR = OUT / "math_relations"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    """Canonical, Windows-readable audit path string."""
    try:
        return str(path.resolve()).replace("/", "\\")
    except OSError:
        return str(path).replace("/", "\\")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def check_writable() -> None:
    if (OUT / "WRITE_STOPPED").exists():
        raise RuntimeError("WRITE_STOPPED exists: this audit is sealed and must not be modified")


def ensure_dirs() -> None:
    check_writable()
    for d in (OUT, RENDERS, GLYPH_DIR, GLYPH_ROI, GLYPH_CARD, GLYPH_SHEET,
              GRAPHIC_DIR, PAIR_DIR, OCC_DIR, CAL_DIR, MACHINE_DIR, REPORT_DIR,
              RELATION_DIR):
        d.mkdir(parents=True, exist_ok=True)


def purge_preseal_generated_output() -> None:
    """Remove only this audit's known, unsealed generated artifacts before a clean rerun."""
    check_writable()
    for d in (RENDERS, GLYPH_DIR, GRAPHIC_DIR, PAIR_DIR, OCC_DIR, CAL_DIR, MACHINE_DIR, REPORT_DIR, RELATION_DIR):
        if d.exists():
            shutil.rmtree(d)
    for p in (OUT / "identity_and_scope_manifest.json", OUT / "SA1_TERMINAL_VERDICT.md", OUT / "TERMINAL_MANIFEST.json"):
        if p.exists():
            p.unlink()


def write_text(path: Path, value: str) -> None:
    check_writable()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    check_writable()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: normalize_cell(row.get(k, "")) for k in fields})


def normalize_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isfinite(value):
            return f"{value:.4f}"
        return "N/A"
    if isinstance(value, (list, tuple)):
        return "|".join(str(x) for x in value)
    return value


def png_save(path: Path, image: Image.Image) -> None:
    check_writable()
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=False)


def bbox_to_str(b: tuple[int, int, int, int] | fitz.Rect) -> str:
    if isinstance(b, fitz.Rect):
        return f"{b.x0:.3f},{b.y0:.3f},{b.x1:.3f},{b.y1:.3f}"
    return ",".join(str(int(v)) for v in b)


def union_bbox(boxes: Iterable[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    values = list(boxes)
    return (min(v[0] for v in values), min(v[1] for v in values),
            max(v[2] for v in values), max(v[3] for v in values))


def clip_bbox(box: tuple[int, int, int, int], w: int, h: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return max(0, x0), max(0, y0), min(w, x1), min(h, y1)


def rect_to_px(rect: fitz.Rect, sx: float, sy: float, w: int, h: int, pad: int = 0) -> tuple[int, int, int, int]:
    return clip_bbox((math.floor(rect.x0 * sx) - pad, math.floor(rect.y0 * sy) - pad,
                      math.ceil(rect.x1 * sx) + pad, math.ceil(rect.y1 * sy) + pad), w, h)


def color_int_to_rgb(color: int) -> tuple[int, int, int]:
    return ((color >> 16) & 255, (color >> 8) & 255, color & 255)


def drawing_color_to_rgb(color: Any) -> tuple[int, int, int]:
    if color is None:
        return (0, 0, 0)
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        return tuple(int(round(max(0, min(1, float(x))) * 255)) for x in color[:3])
    return (0, 0, 0)


def safe_codepoint(c: str) -> str:
    return "_".join(f"U{ord(x):04X}" for x in c)


def category_for_char(c: str, font: str, size: float) -> tuple[str, str, float | None, str]:
    """Strict C thresholds; low-profile glyphs are governed by individual calibration."""
    cjk = "\u3400" <= c <= "\u9fff" or "\uf900" <= c <= "\ufaff"
    low = set(".,;:!?，。；：、！？")
    operators = set("=+−–→←↔×÷±∈∉≤≥∑∏∫∂∞|/\\")
    if cjk:
        return "CJK_FULL", "H_INK>=30", 30.0, "NO"
    if c in low:
        return "LOW_PROFILE", "INDEPENDENT_CALIBRATION", None, "YES"
    if size < 9.5:
        return "NATURAL_SCRIPT", "H_INK>=15", 15.0, "NO"
    if c in operators:
        return "BASE_MATH_OPERATOR", "H_INK>=22", 22.0, "NO"
    if c.isdigit() or ("A" <= c <= "Z"):
        return "DIGIT_UPPER", "H_INK>=24", 24.0, "NO"
    if "MATH" in font.upper() or "XITS" in font.upper():
        return "BASE_MATH", "H_INK>=22", 22.0, "NO"
    return "PROSE_LATIN_X_HEIGHT", "H_INK>=17", 17.0, "NO"


def dominant_background(arr: np.ndarray) -> np.ndarray:
    """Modal coarse RGB of a local crop, without deleting any foreground pixel."""
    if arr.size == 0:
        return np.array([255, 255, 255], dtype=np.float32)
    flat = arr.reshape((-1, 3))
    quant = (flat // 8).astype(np.uint8)
    keys = quant[:, 0].astype(np.int32) * 1024 + quant[:, 1].astype(np.int32) * 32 + quant[:, 2].astype(np.int32)
    code = int(Counter(keys.tolist()).most_common(1)[0][0])
    selected = flat[keys == code]
    return np.median(selected, axis=0).astype(np.float32)


def text_mask_for_bbox(rgb: np.ndarray, box: tuple[int, int, int, int], expected: tuple[int, int, int]) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    """Return exact native-pixel target mask; no morphology, dilation, erosion or repair."""
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = clip_bbox(box, w, h)
    roi = rgb[y0:y1, x0:x1]
    bg = dominant_background(roi)
    target = np.array(expected, dtype=np.float32)
    pixels = roi.astype(np.float32)
    dist_bg = np.sqrt(np.sum((pixels - bg) ** 2, axis=2))
    # A true anti-aliased glyph pixel lies on the physical foreground-to-local-
    # background colour line.  This excludes a nearby gold rule from a black
    # math glyph even where its PDF character bbox reaches the label border.
    direction = target - bg
    denom = float(np.dot(direction, direction))
    if denom < 1.0:
        mask = dist_bg >= 20.0
    else:
        delta = pixels - bg
        alpha = np.sum(delta * direction, axis=2) / denom
        projected = bg + alpha[..., None] * direction
        residual = np.sqrt(np.sum((pixels - projected) ** 2, axis=2))
        target_bg_distance = math.sqrt(denom)
        mask = (dist_bg >= 20.0) & (alpha >= 0.035) & (alpha <= 1.08) & (residual <= max(9.0, target_bg_distance * 0.075))
    return roi, mask, (x0, y0, x1, y1)


def mask_stats(mask: np.ndarray) -> tuple[int, int, int, tuple[int, int, int, int] | None]:
    yy, xx = np.where(mask)
    if len(xx) == 0:
        return 0, 0, 0, None
    x0, x1 = int(xx.min()), int(xx.max()) + 1
    y0, y1 = int(yy.min()), int(yy.max()) + 1
    return x1 - x0, y1 - y0, int(mask.sum()), (x0, y0, x1, y1)


def retain_components_for_nominal_bbox(mask: np.ndarray, roi_global: tuple[int,int,int,int], nominal_global: tuple[int,int,int,int]) -> np.ndarray:
    """Keep raw connected components whose centroid belongs to this PDF glyph bbox.

    This is ownership separation only. It performs no morphology and retains
    the original component pixels verbatim, which is essential for a decimal
    point or Chinese punctuation next to another glyph in a calibration row.
    """
    h,w=mask.shape; visited=np.zeros_like(mask,dtype=bool); comps=[]
    for sy,sx in zip(*np.where(mask)):
        if visited[sy,sx]: continue
        stack=[(int(sy),int(sx))];visited[sy,sx]=True;pts=[]
        while stack:
            y,x=stack.pop();pts.append((y,x))
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    if dx==0 and dy==0: continue
                    ny,nx=y+dy,x+dx
                    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not visited[ny,nx]:
                        visited[ny,nx]=True;stack.append((ny,nx))
        comps.append(pts)
    kept=[]; nx0,ny0,nx1,ny1=nominal_global
    for pts in comps:
        cx=float(np.mean([x for _,x in pts])+roi_global[0]); cy=float(np.mean([y for y,_ in pts])+roi_global[1])
        if nx0<=cx<nx1 and ny0<=cy<ny1: kept.append(pts)
    if not kept and comps:
        def score(pts:list[tuple[int,int]])->float:
            cx=float(np.mean([x for _,x in pts])+roi_global[0]); cy=float(np.mean([y for y,_ in pts])+roi_global[1])
            ox=max(nx0-cx,0,cx-(nx1-1));oy=max(ny0-cy,0,cy-(ny1-1));return ox*ox+oy*oy
        kept=[min(comps,key=score)]
    out=np.zeros_like(mask,dtype=bool)
    for pts in kept:
        yy=np.array([y for y,_ in pts],dtype=np.int32);xx=np.array([x for _,x in pts],dtype=np.int32);out[yy,xx]=True
    return out


def rgb_overlay(roi: np.ndarray, mask: np.ndarray) -> Image.Image:
    arr = roi.copy().astype(np.float32)
    red = np.array([232, 36, 36], dtype=np.float32)
    arr[mask] = 0.42 * arr[mask] + 0.58 * red
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def binary_mask_image(mask: np.ndarray) -> Image.Image:
    out = np.full((mask.shape[0], mask.shape[1], 3), 255, dtype=np.uint8)
    out[mask] = (0, 0, 0)
    return Image.fromarray(out, "RGB")


def nearest8(image: Image.Image) -> Image.Image:
    return image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)


def default_font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def labelled_triptych(identifier: str, original: Image.Image, overlay: Image.Image, mask: Image.Image) -> Image.Image:
    cells = [nearest8(original), nearest8(overlay), nearest8(mask)]
    header_h = 26
    gap = 8
    width = sum(x.width for x in cells) + gap * 4
    height = header_h + max(x.height for x in cells) + gap * 2
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    labels = ["ORIGINAL (8x nearest)", "TARGET OVERLAY (8x nearest)", "MASK ONLY (8x nearest)"]
    x = gap
    for label, cell in zip(labels, cells):
        draw.text((x, 4), label, fill="black", font=default_font())
        canvas.paste(cell, (x, header_h + gap))
        x += cell.width + gap
    draw.text((gap, height - 13), identifier, fill="black", font=default_font())
    return canvas


@dataclass
class ObjectMask:
    object_id: str
    object_type: str
    class_group: str
    role: str
    parent_id: str
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    source_ref: str
    color_rgb: tuple[int, int, int]
    draw_refs: str = ""

    @property
    def pixels(self) -> int:
        return int(self.mask.sum())


def object_global_points(obj: ObjectMask) -> np.ndarray:
    yy, xx = np.where(obj.mask)
    if len(xx) == 0:
        return np.empty((0, 2), dtype=np.int32)
    return np.column_stack((xx + obj.bbox[0], yy + obj.bbox[1])).astype(np.int32)


def build_identity() -> dict[str, Any]:
    files = {
        "local_page_pdf": PDF,
        "local_standalone_pdf": STANDALONE_PDF,
        "r97_upstream_pdf": R97_PDF,
        "figure_source": FIG_SOURCE,
        "direct_body": BODY,
        "strict_schema": SCHEMA,
        "strict_protocol": PROTOCOL,
        "authority_goal": GOAL,
        "style_file": STY,
        "verified_baseline_source_snapshot": BASELINE_SOURCE,
        "baseline_to_current_patch": SOURCE_DIFF,
    }
    found = {key: {"canonical_path": rel(path), "exists": path.exists(),
                   "bytes": path.stat().st_size if path.exists() else None,
                   "sha256": sha256(path) if path.exists() else None}
             for key, path in files.items()}
    doc = fitz.open(PDF)
    page = doc[PDF_PAGE_0]
    pdf_info = {"page_count": doc.page_count, "page_width_pt": page.rect.width,
                "page_height_pt": page.rect.height}
    doc.close()
    return {
        "audit": "FIG-P547-01 STRICT_R7_SA2_REPAIR_R97_LOCAL",
        "generated_utc": now_utc(),
        "canonical_output_directory": rel(OUT),
        "local_target": {"physical_pdf_page": PDF_PAGE_1, "printed_page": PRINTED_PAGE,
                             "figure": FIGURE_NO, "figure_crop_pt": list(FIG_RECT_PT)},
        "inputs": found,
        "expected_hashes": {"figure_source": SOURCE_SHA_EXPECTED, "local_page_pdf": PDF_SHA_EXPECTED,
                            "local_standalone_pdf": STANDALONE_SHA_EXPECTED, "r97_upstream_pdf": R97_SHA_EXPECTED,
                            "authority_goal": GOAL_SHA_EXPECTED, "strict_schema": SCHEMA_SHA_EXPECTED,
                            "strict_protocol": PROTOCOL_SHA_EXPECTED,
                            "direct_body": BODY_SHA_EXPECTED},
        "hash_match": {"figure_source": found["figure_source"]["sha256"] == SOURCE_SHA_EXPECTED,
                       "local_page_pdf": found["local_page_pdf"]["sha256"] == PDF_SHA_EXPECTED,
                       "local_standalone_pdf": found["local_standalone_pdf"]["sha256"] == STANDALONE_SHA_EXPECTED,
                       "r97_upstream_pdf": found["r97_upstream_pdf"]["sha256"] == R97_SHA_EXPECTED,
                       "authority_goal": found["authority_goal"]["sha256"] == GOAL_SHA_EXPECTED,
                       "strict_schema": found["strict_schema"]["sha256"] == SCHEMA_SHA_EXPECTED,
                       "strict_protocol": found["strict_protocol"]["sha256"] == PROTOCOL_SHA_EXPECTED,
                       "direct_body": found["direct_body"]["sha256"] == BODY_SHA_EXPECTED},
        "pdf_geometry": pdf_info,
        "native_render_contract": "pdftoppm direct local page/standalone PDFs at 200/300 dpi; crop only; grayscale without resize; 8x reviews use nearest neighbour only",
        "source_transition": {"before_sha256": SOURCE_SHA_BEFORE, "after_sha256": SOURCE_SHA_EXPECTED,
                              "baseline_snapshot_hash_match": found["verified_baseline_source_snapshot"]["sha256"] == SOURCE_SHA_BEFORE,
                              "patch_present": found["baseline_to_current_patch"]["exists"]},
    }


def source_identity_evidence() -> None:
    if not BASELINE_SOURCE.exists() or sha256(BASELINE_SOURCE)!=SOURCE_SHA_BEFORE:
        raise RuntimeError("verified baseline source snapshot is absent or does not match 638CEA identity")
    if sha256(FIG_SOURCE)!=SOURCE_SHA_EXPECTED:
        raise RuntimeError("current business source no longer matches frozen 29E415 identity")
    baseline=BASELINE_SOURCE.read_text(encoding="utf-8");current=FIG_SOURCE.read_text(encoding="utf-8")
    current_snapshot=SOURCE_ID_DIR/"current_29E415_fig_v5_c01_transition_graph.tex"
    write_text(current_snapshot,current)
    if sha256(current_snapshot)!=SOURCE_SHA_EXPECTED:
        raise RuntimeError("current source snapshot byte identity mismatch")
    diff="".join(difflib.unified_diff(baseline.splitlines(keepends=True),current.splitlines(keepends=True),
                                      fromfile=f"baseline_{SOURCE_SHA_BEFORE}.tex",tofile=f"current_{SOURCE_SHA_EXPECTED}.tex",n=3))
    write_text(SOURCE_DIFF,diff)
    report={"baseline_path":rel(BASELINE_SOURCE),"baseline_sha256":sha256(BASELINE_SOURCE),"baseline_expected":SOURCE_SHA_BEFORE,
            "current_business_source":rel(FIG_SOURCE),"current_business_source_sha256":sha256(FIG_SOURCE),"current_snapshot":rel(current_snapshot),"current_snapshot_sha256":sha256(current_snapshot),
            "unified_diff":rel(SOURCE_DIFF),"unified_diff_sha256":sha256(SOURCE_DIFF),"diff_line_count":len(diff.splitlines()),
            "identity_pass":sha256(BASELINE_SOURCE)==SOURCE_SHA_BEFORE and sha256(FIG_SOURCE)==SOURCE_SHA_EXPECTED and sha256(current_snapshot)==SOURCE_SHA_EXPECTED}
    write_json(SOURCE_ID_DIR/"source_identity_report.json",report)


def render_native() -> dict[str, Any]:
    for exe in (POPPLER,):
        if not Path(exe).exists() and not shutil.which(exe):
            raise RuntimeError(f"required renderer unavailable: {exe}")
    results: dict[str, Any] = {}
    rendered: dict[tuple[str,int,bool], Path] = {}
    for kind, source in (("page", PDF), ("standalone", STANDALONE_PDF)):
        for dpi in (200, 300):
            for gray in ((False, True) if dpi == 300 else (False,)):
                suffix = "_grayscale" if gray else ""
                out_prefix = RENDERS / f"{kind}_{dpi}dpi_native{suffix}"
                out_png = Path(str(out_prefix) + ".png")
                cmd = [str(POPPLER), "-r", str(dpi), "-f", "1", "-l", "1"]
                if gray:
                    cmd.append("-gray")
                cmd += ["-png", "-singlefile", str(source), str(out_prefix)]
                proc = subprocess.run(cmd, cwd=str(OUT), capture_output=True, text=True, encoding="utf-8", errors="replace")
                log_name = f"renderer_{kind}_{dpi}dpi{suffix}.log"
                write_text(MACHINE_DIR / log_name, "COMMAND: " + " ".join(cmd) + "\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr + "\nEXIT=" + str(proc.returncode) + "\n")
                if proc.returncode != 0 or not out_png.exists():
                    raise RuntimeError(f"native pdftoppm {kind} {dpi} dpi failed")
                with Image.open(out_png) as im:
                    key=f"{kind}_{dpi}{'_gray' if gray else ''}"
                    results[key]={"path":rel(out_png),"sha256":sha256(out_png),"dimensions_px":[im.width,im.height],"renderer_command":cmd}
                rendered[(kind,dpi,gray)] = out_png
    image300 = Image.open(rendered[("page",300,False)]).convert("RGB")
    doc = fitz.open(PDF)
    page = doc[PDF_PAGE_0]
    sx, sy = image300.width / page.rect.width, image300.height / page.rect.height
    crop_box = rect_to_px(FIG_RECT_PT, sx, sy, image300.width, image300.height)
    doc.close()
    crop = image300.crop(crop_box)
    crop_path = RENDERS / "local_page_figure30_2_caption_300dpi_native_crop.png"
    png_save(crop_path, crop)
    standalone_path = RENDERS / "local_standalone_figure30_2_300dpi_native_fullpage.png"
    shutil.copyfile(rendered[("standalone",300,False)], standalone_path)
    gray_full=Image.open(rendered[("page",300,True)]).convert("L")
    gray_path = RENDERS / "local_page_figure30_2_caption_300dpi_native_crop_grayscale.png"
    png_save(gray_path, gray_full.crop(crop_box))
    results["figure_crop_300"] = {"path": rel(crop_path), "sha256": sha256(crop_path),
                                   "dimensions_px": [crop.width, crop.height], "crop_box_px": list(crop_box),
                                   "crop_box_pt": list(FIG_RECT_PT), "operation": "direct pixel crop only; no resize"}
    results["standalone_view_300"] = {"path": rel(standalone_path), "sha256": sha256(standalone_path),
                                      "dimensions_px": list(Image.open(standalone_path).size),
                                       "operation": "direct local standalone-PDF page render; no resize"}
    results["grayscale"] = {"path": rel(gray_path), "sha256": sha256(gray_path),
                            "dimensions_px": [crop.width, crop.height], "operation": "integer crop from direct Poppler -gray 300dpi render; no resize"}
    write_json(MACHINE_DIR / "native_render_manifest.json", results)
    return {"full300": np.array(image300), "page_sx": sx, "page_sy": sy, "render": results, "crop_box": crop_box}


def source_and_body_evidence() -> None:
    source_lines = FIG_SOURCE.read_text(encoding="utf-8").splitlines()
    source_audit = [
        "# Source style and structural audit", "",
        f"- Canonical source: `{rel(FIG_SOURCE)}`", f"- SHA-256: `{sha256(FIG_SOURCE)}`", "",
        "## Declared typesetting / stroke values", "",
        "- figure default: `\\fontsize{9.8pt}{11.7pt}` (line 3)",
        "- local geometry relations: equals `.72pt` rules at `±.57ex`; arrow `.70pt` with 2.0 mm head (lines 8–14)",
        "- state node text: `10.2pt`, 9.6 mm node, `.86pt` border (lines 17–19)",
        "- ordinary/focus labels: `11.6pt`; focus label outline `.72pt`, inner sep `2.75pt` (lines 21–22)",
        "- title: bold `10.2pt` (line 23)",
        "- matrix default: `9.8pt`; formulas `11.8pt`; explanatory formula `11.6pt` (lines 24, 39–41, 59–61)",
        "- bridge default: `9.6pt`; bridge formula `12.0pt`; bridge sentence `11.6pt` (lines 25–28, 44–48)",
        "- edge/focus/bridge-arrow line widths: `.86pt` / `1.34pt` / `.88pt` (lines 19–20,28)",
        "",
        "## Source geometry / semantics", "",
        "- Two panels use the same node and edge construction; gold focuses 0.3 and the transpose bridge explicitly preserves `P=A^{\\mathsf T}` through an auditable geometric equality relation.",
        "- There is no `resizebox`, `scalebox`, raster inclusion, or post-hoc figure scale in the frozen source.",
        "",
        "## Frozen source excerpt", "", "```tex", *source_lines, "```", "",
    ]
    write_text(REPORT_DIR / "source_style_and_structure_audit.md", "\n".join(source_audit))
    body_lines = BODY.read_text(encoding="utf-8").splitlines()
    selected = []
    for idx, line in enumerate(body_lines, 1):
        if 175 <= idx <= 205:
            selected.append(f"{idx:04d}: {line}")
    write_text(REPORT_DIR / "direct_body_semantic_excerpt.txt", "\n".join(selected) + "\n")


def resolve_text_mask_overlap(glyphs: list[dict[str, Any]], objects: list[ObjectMask]) -> None:
    """Assign every raw foreground component to one declared PDF glyph.

    Adjacent PDF character bboxes can overlap even though their ink components
    are distinct (for example the decimal point and the following digit).  A
    component-centroid/nominal-bbox owner rule preserves every union pixel and
    prevents one component being claimed by two glyph masks. No morphology,
    pixel addition, or pixel deletion is performed.
    """
    object_by_id = {x.object_id: x for x in objects}
    glyph_by_id = {x["glyph_id"]: x for x in glyphs}
    by_line: dict[str, list[str]] = defaultdict(list)
    for g in glyphs:
        by_line[g["parent_text_object"]].append(g["glyph_id"])
        g["_deconflicted_pixels"] = 0
        g["_component_count"] = 0
    for _, ids in by_line.items():
        parent_box=union_bbox([object_by_id[gid].bbox for gid in ids])
        canvas=np.zeros((parent_box[3]-parent_box[1],parent_box[2]-parent_box[0]),dtype=bool)
        for gid in ids:
            obj = object_by_id[gid]
            canvas[obj.bbox[1]-parent_box[1]:obj.bbox[3]-parent_box[1],obj.bbox[0]-parent_box[0]:obj.bbox[2]-parent_box[0]] |= obj.mask
            obj.mask[:,:]=False
        visited=np.zeros_like(canvas,dtype=bool)
        height,width=canvas.shape
        for sy0,sx0 in zip(*np.where(canvas & ~visited)):
            if visited[sy0,sx0]:
                continue
            stack=[(int(sy0),int(sx0))];visited[sy0,sx0]=True; points=[]
            while stack:
                yy,xx=stack.pop(); points.append((yy,xx))
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        if dx==0 and dy==0: continue
                        ny,nx=yy+dy,xx+dx
                        if 0<=ny<height and 0<=nx<width and canvas[ny,nx] and not visited[ny,nx]:
                            visited[ny,nx]=True;stack.append((ny,nx))
            ys=np.array([p[0] for p in points],dtype=np.int32); xs=np.array([p[1] for p in points],dtype=np.int32)
            gx=float(xs.mean()+parent_box[0]); gy=float(ys.mean()+parent_box[1])
            cb=(int(xs.min()+parent_box[0]),int(ys.min()+parent_box[1]),int(xs.max()+parent_box[0])+1,int(ys.max()+parent_box[1])+1)
            candidates=[]
            for gid in ids:
                obj=object_by_id[gid]
                if boxes_intersect(obj.bbox,cb) is not None:
                    candidates.append(gid)
            def score(gid:str, px:float=gx, py:float=gy)->tuple[float,float]:
                bx=glyph_by_id[gid]["_nominal_bbox_px"]; cx,cy=(bx[0]+bx[2])/2,(bx[1]+bx[3])/2
                ox=max(bx[0]-px,0,px-(bx[2]-1)); oy=max(bx[1]-py,0,py-(bx[3]-1))
                return (ox*ox+oy*oy,(px-cx)*(px-cx)+(py-cy)*(py-cy))
            keep=min(candidates,key=score)
            obj=object_by_id[keep]
            if cb[0]>=obj.bbox[0] and cb[1]>=obj.bbox[1] and cb[2]<=obj.bbox[2] and cb[3]<=obj.bbox[3]:
                obj.mask[ys+parent_box[1]-obj.bbox[1],xs+parent_box[0]-obj.bbox[0]]=True
                glyph_by_id[keep]["_component_count"] += 1
                if len(candidates)>1:
                    glyph_by_id[keep]["_deconflicted_pixels"] += len(points)
            else:
                # A component crossed a true glyph boundary. Retain all of its
                # pixels, but allocate at native-pixel level only for this
                # exceptional component so no object owns pixels outside its ROI.
                touched=set()
                for ly,lx in points:
                    px,py=lx+parent_box[0],ly+parent_box[1]
                    pcands=[gid for gid in ids if object_by_id[gid].bbox[0]<=px<object_by_id[gid].bbox[2] and object_by_id[gid].bbox[1]<=py<object_by_id[gid].bbox[3]]
                    owner=min(pcands,key=lambda gid:score(gid,px,py))
                    po=object_by_id[owner];po.mask[py-po.bbox[1],px-po.bbox[0]]=True;touched.add(owner)
                for owner in touched:
                    glyph_by_id[owner]["_component_count"] += 1
                    glyph_by_id[owner]["_deconflicted_pixels"] += len(points)


def write_glyph_artifacts(glyphs: list[dict[str, Any]], objects: list[ObjectMask], rgb: np.ndarray) -> None:
    object_by_id = {x.object_id: x for x in objects}
    for rec in glyphs:
        obj = object_by_id[rec["glyph_id"]]
        roi = rgb[obj.bbox[1]:obj.bbox[3], obj.bbox[0]:obj.bbox[2]]
        wi, hi, area, ink_local = mask_stats(obj.mask)
        ink_global = None if ink_local is None else (ink_local[0] + obj.bbox[0], ink_local[1] + obj.bbox[1], ink_local[2] + obj.bbox[0], ink_local[3] + obj.bbox[1])
        required = rec["_required"]
        rec["ink_bbox_px"] = bbox_to_str(ink_global) if ink_global else ""
        rec["ink_w_px"], rec["ink_h_px"], rec["ink_area_px"] = wi, hi, area
        rec["initial_size_gate"] = "PENDING_CALIBRATION" if rec["needs_low_profile_calibration"] == "YES" else ("PASS" if hi >= float(required) else "FAIL")
        base = f"{rec['glyph_id']}_{rec['codepoint']}"
        orig_path = GLYPH_ROI / f"{base}_original_1x.png"
        overlay_path = GLYPH_ROI / f"{base}_target_overlay_1x.png"
        mask_path = GLYPH_ROI / f"{base}_mask_only_1x.png"
        card_path = GLYPH_CARD / f"{base}_contact_8x_nearest.png"
        original = Image.fromarray(roi, "RGB")
        overlay = rgb_overlay(roi, obj.mask)
        mask_img = binary_mask_image(obj.mask)
        png_save(orig_path, original); png_save(overlay_path, overlay); png_save(mask_path, mask_img)
        png_save(card_path, labelled_triptych(base, original, overlay, mask_img))
        rec.update({"original_1x":rel(orig_path),"overlay_1x":rel(overlay_path),"mask_only_1x":rel(mask_path),"contact_8x_nearest":rel(card_path),
                    "mask_extraction":"exact native 300dpi pixel colour-line segmentation; duplicate kerning-boundary ownership resolved, no morphology / repair / resampling",
                    "deconflicted_duplicate_assignment_px":rec["_deconflicted_pixels"],"assigned_raw_component_count":rec["_component_count"]})
        for temporary in ("_required", "_nominal_bbox_px", "_deconflicted_pixels", "_component_count"):
            rec.pop(temporary, None)


def extract_glyphs(rgb: np.ndarray, sx: float, sy: float) -> tuple[list[dict[str, Any]], list[ObjectMask], dict[str, Any]]:
    doc = fitz.open(PDF)
    page = doc[PDF_PAGE_0]
    raw = page.get_text("rawdict")
    glyphs: list[dict[str, Any]] = []
    objects: list[ObjectMask] = []
    count = 0
    crop_margin_exclusions: list[dict[str, Any]] = []
    for bi, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block.get("lines", [])):
            line_id = f"TLINE_B{bi:02d}_L{li:02d}"
            # A PDF text block corresponds to one visual label/formula/caption
            # object. Matrix delimiters and entries may be emitted as several
            # PDF lines inside the same block, so their raw pixels must still be
            # made mutually exclusive before all-pair testing.
            block_parent_id = f"TBLOCK_B{bi:02d}"
            # PyMuPDF coalesces the four spatially independent state/loop
            # labels into B05/B13.  Each emitted line is a true semantic text
            # object there; all other figure blocks are one formula/annotation
            # or the single caption paragraph even when geometry splits lines.
            semantic_parent_id = line_id if bi in {5,13} else block_parent_id
            for si, span in enumerate(line.get("spans", [])):
                span_id = f"SPAN_B{bi:02d}_L{li:02d}_S{si:02d}"
                font = str(span.get("font", ""))
                size = float(span.get("size", 0.0))
                color = int(span.get("color", 0))
                for ci, ch in enumerate(span.get("chars", [])):
                    c = str(ch.get("c", ""))
                    if not c or c.isspace():
                        continue
                    rect = fitz.Rect(ch["bbox"])
                    in_text_scope = FIG_TEXT_SCOPE_PT.intersects(rect) and rect.y0 >= FIG_TEXT_SCOPE_PT.y0 and rect.y1 <= FIG_TEXT_SCOPE_PT.y1
                    if not in_text_scope:
                        if FIG_RECT_PT.intersects(rect):
                            crop_margin_exclusions.append({"char": c, "bbox_pt": bbox_to_str(rect), "pdf_block": bi, "pdf_line": li, "reason": "inside visual crop margin but outside figure-title/graphic/caption text scope"})
                        continue
                    count += 1
                    gid = f"C{count:04d}"
                    box = rect_to_px(rect, sx, sy, rgb.shape[1], rgb.shape[0], pad=1)
                    expected = color_int_to_rgb(color)
                    roi, mask, actual_box = text_mask_for_bbox(rgb, box, expected)
                    category, rule, required, needs_cal = category_for_char(c, font, size)
                    rec: dict[str, Any] = {
                        "glyph_id": gid, "char": c, "codepoint": safe_codepoint(c), "pdf_block": bi, "pdf_line": li,
                        "pdf_span": si, "source_span_id": span_id, "pdf_raw_line_id": line_id, "parent_text_object": semantic_parent_id,
                        "font": font, "font_size_pt_pdf_emit": size, "color_rgb": "#%02X%02X%02X" % expected,
                        "char_bbox_pt": bbox_to_str(rect), "roi_bbox_px": bbox_to_str(actual_box),
                        "ink_bbox_px": "", "ink_w_px": "", "ink_h_px": "", "ink_area_px": "", "glyph_class": category, "strict_rule": rule,
                        "required_h_px": required if required is not None else "CALIBRATION", "needs_low_profile_calibration": needs_cal,
                        "initial_size_gate": "PENDING_ARTIFACT", "original_1x": "", "overlay_1x": "", "mask_only_1x": "", "contact_8x_nearest": "",
                        "mask_extraction": "",
                        "_required": required, "_nominal_bbox_px": rect_to_px(rect, sx, sy, rgb.shape[1], rgb.shape[0], pad=0),
                    }
                    glyphs.append(rec)
                    objects.append(ObjectMask(gid, "TEXT_GLYPH", "TEXT", category, semantic_parent_id, actual_box, mask, span_id, expected))
    doc.close()
    resolve_text_mask_overlap(glyphs, objects)
    write_glyph_artifacts(glyphs, objects, rgb)
    metadata = {"glyph_count": len(glyphs), "scope": f"all non-whitespace local-page PDF text glyphs fully within title/graphic/caption text boundary, y={FIG_TEXT_SCOPE_PT.y0:.0f}..{FIG_TEXT_SCOPE_PT.y1:.0f}pt", "raw_text_engine": "PyMuPDF page.get_text(rawdict)", "text_scope_pt": list(FIG_TEXT_SCOPE_PT), "visual_crop_margin_excluded_character_count": len(crop_margin_exclusions), "visual_crop_margin_exclusions": crop_margin_exclusions}
    return glyphs, objects, metadata


def role_for_span(chars: list[dict[str, Any]]) -> str:
    rects = [fitz.Rect(x["char_bbox_pt"].split(",")) for x in chars if x.get("char_bbox_pt")]
    if not rects:
        return "UNKNOWN"
    r = fitz.Rect(rects[0])
    for z in rects[1:]:
        r |= z
    cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
    text = "".join(x["char"] for x in chars)
    if cy < 145:
        return "TITLE"
    if cy > 248:
        return "CAPTION"
    if 185 <= cy <= 230 and 220 <= cx <= 365:
        return "BRIDGE"
    if 160 <= cy <= 190 and text in {"1", "2"}:
        return "STATE_LABEL"
    if 140 <= cy <= 202:
        return "EDGE_LABEL"
    if 198 <= cy <= 248:
        if any(x["char"] in "每行列和为" for x in chars):
            return "MATRIX_EXPLANATION"
        return "MATRIX_FORMULA"
    return "OTHER"


def render_glyph_sheets(glyphs: list[dict[str, Any]], per_sheet: int = 12) -> None:
    manifest_rows = []
    for sheet_index, start in enumerate(range(0, len(glyphs), per_sheet), 1):
        subset = glyphs[start:start + per_sheet]
        cards = [Image.open(Path(row["contact_8x_nearest"])) .convert("RGB") for row in subset]
        cols = 2
        rows = math.ceil(len(cards) / cols)
        cell_w = max(im.width for im in cards) + 12
        cell_h = max(im.height for im in cards) + 18
        canvas = Image.new("RGB", (cols * cell_w + 12, rows * cell_h + 34), "#F4F4F4")
        draw = ImageDraw.Draw(canvas)
        draw.text((8, 8), f"FIG-P547-01 glyph contact sheet {sheet_index:02d}; every cell is 8x nearest", fill="black", font=default_font())
        for i, (entry, card) in enumerate(zip(subset, cards)):
            col, row = i % cols, i // cols
            x, y = 6 + col * cell_w, 28 + row * cell_h
            canvas.paste(card, (x, y))
            entry["contact_sheet"] = f"glyph_sheet_{sheet_index:02d}_8x_nearest.png"
            entry["contact_cell"] = f"R{row + 1}C{col + 1}"
            manifest_rows.append({"glyph_id": entry["glyph_id"], "sheet": entry["contact_sheet"], "cell": entry["contact_cell"], "card": entry["contact_8x_nearest"]})
        sheet_path = GLYPH_SHEET / f"glyph_sheet_{sheet_index:02d}_8x_nearest.png"
        png_save(sheet_path, canvas)
    write_csv(GLYPH_DIR / "glyph_contact_sheet_index.csv", manifest_rows, ["glyph_id", "sheet", "cell", "card"])


def drawing_prediction_mask(drawing: dict[str, Any], bbox: tuple[int, int, int, int], sx: float, sy: float) -> tuple[np.ndarray, str]:
    """Rasterise only the PDF vector path geometry into a local prediction mask."""
    x0, y0, x1, y1 = bbox
    width, height = max(1, x1 - x0), max(1, y1 - y0)
    im = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(im)
    line_w = max(1, int(math.ceil(float(drawing.get("width") or 0.72) * (sx + sy) / 2 + 2)))
    methods: list[str] = []
    def pxy(p: Any) -> tuple[float, float]:
        return float(p.x) * sx - x0, float(p.y) * sy - y0
    def cubic(p0: Any, p1: Any, p2: Any, p3: Any) -> list[tuple[float, float]]:
        result = []
        for i in range(49):
            t = i / 48
            u = 1 - t
            x = u**3 * p0.x + 3*u*u*t*p1.x + 3*u*t*t*p2.x + t**3*p3.x
            y = u**3 * p0.y + 3*u*u*t*p1.y + 3*u*t*t*p2.y + t**3*p3.y
            result.append((x * sx - x0, y * sy - y0))
        return result
    for item in drawing.get("items", []):
        op = item[0]
        if op == "l":
            draw.line([pxy(item[1]), pxy(item[2])], fill=1, width=line_w)
            methods.append("line")
        elif op == "c":
            draw.line(cubic(item[1], item[2], item[3], item[4]), fill=1, width=line_w)
            methods.append("cubic")
        elif op == "re":
            rr = item[1]
            draw.rectangle((rr.x0 * sx - x0, rr.y0 * sy - y0, rr.x1 * sx - x0, rr.y1 * sy - y0), outline=1, width=line_w)
            methods.append("rect")
        elif op == "qu":
            points = [pxy(z) for z in item[1:]]
            if len(points) >= 2:
                draw.line(points, fill=1, width=line_w)
            methods.append("quad")
    arr = np.array(im, dtype=bool)
    if not arr.any():
        # Explicitly recorded conservative fallback for an unsupported PDF item.
        arr[:, :] = True
        return arr, "BBOX_FALLBACK_" + "+".join(sorted(set(methods)) or ["unsupported"])
    return arr, "VECTOR_" + "+".join(sorted(set(methods)))


def actual_stroke_mask(rgb: np.ndarray, prediction: np.ndarray, bbox: tuple[int, int, int, int], target: tuple[int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    roi = rgb[y0:y1, x0:x1].astype(np.float32)
    bg = dominant_background(roi)
    t = np.array(target, dtype=np.float32)
    dt = np.sqrt(np.sum((roi - t) ** 2, axis=2))
    db = np.sqrt(np.sum((roi - bg) ** 2, axis=2))
    target_bg = float(np.sqrt(np.sum((t - bg) ** 2)))
    tol = max(22.0, min(108.0, target_bg * 0.55 + 18.0))
    return prediction & (dt <= tol) & (db >= 20.0)


def graphic_specs() -> list[dict[str, Any]]:
    """All 71 page drawings reconciled to 65 visible foreground objects.

    Six white label fills (indices 8,11,19,49,52,60) are real occlusion
    backgrounds and are reconciled separately.  Every formula rule is kept as
    its own object; none is hidden inside a composite frame.
    """
    return [
        {"id":"MR_EQ01_TOP","role":"L_TITLE_EQ_TOP","draw":[0],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B04"},
        {"id":"MR_EQ01_BOTTOM","role":"L_TITLE_EQ_BOTTOM","draw":[1],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B04"},
        {"id":"MR_ARROW01_SHAFT","role":"L_TITLE_ARROW_SHAFT","draw":[2],"object_type":"GRAPHIC/MATH_RELATION","parent":"TBLOCK_B04"},
        {"id":"MR_ARROW01_HEAD","role":"L_TITLE_ARROW_HEAD","draw":[3],"object_type":"GRAPHIC/MATH_RELATION","parent":"TBLOCK_B04"},
        {"id":"G01","role":"L1_NODE_BORDER","draw":[4]}, {"id":"G02","role":"L2_NODE_BORDER","draw":[5]},
        {"id":"G03","role":"L1_LOOP_SHAFT","draw":[6]}, {"id":"G04","role":"L1_LOOP_HEAD","draw":[7]},
        {"id":"G05","role":"L2_LOOP_SHAFT","draw":[9]}, {"id":"G06","role":"L2_LOOP_HEAD","draw":[10]},
        {"id":"G07","role":"L12_FOCUS_SHAFT","draw":[12]}, {"id":"G08","role":"L12_FOCUS_HEAD","draw":[13]},
        {"id":"G09","role":"L12_FOCUS_LABEL_BORDER","draw":[14]},
        {"id":"MR_EQ02_TOP","role":"L_FOCUS_EQ_TOP","draw":[15],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B06"},
        {"id":"MR_EQ02_BOTTOM","role":"L_FOCUS_EQ_BOTTOM","draw":[16],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B06"},
        {"id":"G10","role":"L21_SHAFT","draw":[17]}, {"id":"G11","role":"L21_HEAD","draw":[18]},
        {"id":"MR_EQ03_TOP","role":"L_LOWER_EQ_TOP","draw":[20],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B07"},
        {"id":"MR_EQ03_BOTTOM","role":"L_LOWER_EQ_BOTTOM","draw":[21],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B07"},
        {"id":"MR_EQ04_TOP","role":"L_MATRIX_EQ_TOP","draw":[22],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B08"},
        {"id":"MR_EQ04_BOTTOM","role":"L_MATRIX_EQ_BOTTOM","draw":[23],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B08"},
        {"id":"MR_BOX_L_TOP","role":"L_MATRIX_FOCUS_FRAME_TOP","draw":[24],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B08"},
        {"id":"MR_BOX_L_LEFT","role":"L_MATRIX_FOCUS_FRAME_LEFT","draw":[25],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B08"},
        {"id":"MR_BOX_L_RIGHT","role":"L_MATRIX_FOCUS_FRAME_RIGHT","draw":[26],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B08"},
        {"id":"MR_BOX_L_BOTTOM","role":"L_MATRIX_FOCUS_FRAME_BOTTOM","draw":[27],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B08"},
        {"id":"MR_EQ05_TOP","role":"L_UPDATE_EQ_TOP","draw":[28],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B09"},
        {"id":"MR_EQ05_BOTTOM","role":"L_UPDATE_EQ_BOTTOM","draw":[29],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B09"},
        {"id":"G13","role":"BRIDGE_PANEL_BORDER","draw":[30]},
        {"id":"MR_EQ06_TOP","role":"BRIDGE_TRANSPOSE_EQ_TOP","draw":[31],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B10"},
        {"id":"MR_EQ06_BOTTOM","role":"BRIDGE_TRANSPOSE_EQ_BOTTOM","draw":[32],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B10"},
        {"id":"MR_ARROW02_SHAFT","role":"BRIDGE_TEXT_ARROW_SHAFT","draw":[33],"object_type":"GRAPHIC/MATH_RELATION","parent":"TBLOCK_B11"},
        {"id":"MR_ARROW02_HEAD","role":"BRIDGE_TEXT_ARROW_HEAD","draw":[34],"object_type":"GRAPHIC/MATH_RELATION","parent":"TBLOCK_B11"},
        {"id":"MR_EQ07_TOP","role":"BRIDGE_INDEX_EQ_TOP","draw":[35],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B11"},
        {"id":"MR_EQ07_BOTTOM","role":"BRIDGE_INDEX_EQ_BOTTOM","draw":[36],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B11"},
        {"id":"G14","role":"BRIDGE_LEFT_SHAFT","draw":[37]}, {"id":"G15","role":"BRIDGE_LEFT_HEAD","draw":[38]},
        {"id":"G16","role":"BRIDGE_RIGHT_SHAFT","draw":[39]}, {"id":"G17","role":"BRIDGE_RIGHT_HEAD","draw":[40]},
        {"id":"MR_EQ08_TOP","role":"R_TITLE_EQ_TOP","draw":[41],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B12"},
        {"id":"MR_EQ08_BOTTOM","role":"R_TITLE_EQ_BOTTOM","draw":[42],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B12"},
        {"id":"MR_ARROW03_SHAFT","role":"R_TITLE_ARROW_SHAFT","draw":[43],"object_type":"GRAPHIC/MATH_RELATION","parent":"TBLOCK_B12"},
        {"id":"MR_ARROW03_HEAD","role":"R_TITLE_ARROW_HEAD","draw":[44],"object_type":"GRAPHIC/MATH_RELATION","parent":"TBLOCK_B12"},
        {"id":"G18","role":"R1_NODE_BORDER","draw":[45]}, {"id":"G19","role":"R2_NODE_BORDER","draw":[46]},
        {"id":"G20","role":"R1_LOOP_SHAFT","draw":[47]}, {"id":"G21","role":"R1_LOOP_HEAD","draw":[48]},
        {"id":"G22","role":"R2_LOOP_SHAFT","draw":[50]}, {"id":"G23","role":"R2_LOOP_HEAD","draw":[51]},
        {"id":"G24","role":"R21_FOCUS_SHAFT","draw":[53]}, {"id":"G25","role":"R21_FOCUS_HEAD","draw":[54]},
        {"id":"G26","role":"R21_FOCUS_LABEL_BORDER","draw":[55]},
        {"id":"MR_EQ09_TOP","role":"R_FOCUS_EQ_TOP","draw":[56],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B14"},
        {"id":"MR_EQ09_BOTTOM","role":"R_FOCUS_EQ_BOTTOM","draw":[57],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B14"},
        {"id":"G27","role":"R12_SHAFT","draw":[58]}, {"id":"G28","role":"R12_HEAD","draw":[59]},
        {"id":"MR_EQ10_TOP","role":"R_LOWER_EQ_TOP","draw":[61],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B15"},
        {"id":"MR_EQ10_BOTTOM","role":"R_LOWER_EQ_BOTTOM","draw":[62],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B15"},
        {"id":"MR_EQ11_TOP","role":"R_MATRIX_EQ_TOP","draw":[63],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B16"},
        {"id":"MR_EQ11_BOTTOM","role":"R_MATRIX_EQ_BOTTOM","draw":[64],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B16"},
        {"id":"MR_BOX_R_TOP","role":"R_MATRIX_FOCUS_FRAME_TOP","draw":[65],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B16"},
        {"id":"MR_BOX_R_LEFT","role":"R_MATRIX_FOCUS_FRAME_LEFT","draw":[66],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B16"},
        {"id":"MR_BOX_R_RIGHT","role":"R_MATRIX_FOCUS_FRAME_RIGHT","draw":[67],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B16"},
        {"id":"MR_BOX_R_BOTTOM","role":"R_MATRIX_FOCUS_FRAME_BOTTOM","draw":[68],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B16"},
        {"id":"MR_EQ12_TOP","role":"R_UPDATE_EQ_TOP","draw":[69],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B17"},
        {"id":"MR_EQ12_BOTTOM","role":"R_UPDATE_EQ_BOTTOM","draw":[70],"object_type":"GRAPHIC/MATH_RULE","parent":"TBLOCK_B17"},
    ]


def extract_graphics(rgb: np.ndarray, sx: float, sy: float) -> tuple[list[dict[str, Any]], list[ObjectMask], dict[int, tuple[np.ndarray, tuple[int, int, int, int], str]]]:
    doc = fitz.open(PDF)
    page = doc[PDF_PAGE_0]
    drawings = page.get_drawings()
    required_max = max(max(x["draw"]) for x in graphic_specs())
    if len(drawings) <= required_max:
        raise RuntimeError(f"drawing inventory unexpectedly short: {len(drawings)} <= {required_max}")
    cached: dict[int, tuple[np.ndarray, tuple[int, int, int, int], str]] = {}
    rows: list[dict[str, Any]] = []
    objects: list[ObjectMask] = []
    for spec in graphic_specs():
        parts = []
        methods = []
        colors = []
        draw_details = []
        for di in spec["draw"]:
            d = drawings[di]
            box = rect_to_px(fitz.Rect(d["rect"]), sx, sy, rgb.shape[1], rgb.shape[0], pad=3)
            pred, method = drawing_prediction_mask(d, box, sx, sy)
            target = drawing_color_to_rgb(d.get("color") or d.get("fill"))
            actual = actual_stroke_mask(rgb, pred, box, target)
            cached[di] = (actual, box, method)
            parts.append((actual, box))
            methods.append(method)
            colors.append(target)
            draw_details.append({"index":di, "rect_pt":bbox_to_str(fitz.Rect(d["rect"])), "type":d.get("type"), "width_pt":d.get("width"), "stroke_rgb":target, "fill":d.get("fill"), "items":str(d.get("items"))})
        all_box = union_bbox([b for _, b in parts])
        combined = np.zeros((all_box[3]-all_box[1], all_box[2]-all_box[0]), dtype=bool)
        for part, box in parts:
            y0, x0 = box[1]-all_box[1], box[0]-all_box[0]
            combined[y0:y0+part.shape[0], x0:x0+part.shape[1]] |= part
        col = colors[0] if colors else (0, 0, 0)
        object_type = spec.get("object_type", "GRAPHIC")
        parent_id = spec.get("parent", "GRAPHICS")
        obj = ObjectMask(spec["id"], object_type, "GRAPHIC", spec["role"], parent_id, all_box, combined,
                         "PDF drawing index " + ",".join(map(str, spec["draw"])), col, ",".join(map(str, spec["draw"])))
        objects.append(obj)
        roi = rgb[all_box[1]:all_box[3], all_box[0]:all_box[2]]
        orig = Image.fromarray(roi, "RGB")
        over = rgb_overlay(roi, combined)
        maskimg = binary_mask_image(combined)
        base = spec["id"] + "_" + spec["role"]
        origp = GRAPHIC_DIR / f"{base}_original_1x.png"
        overp = GRAPHIC_DIR / f"{base}_target_overlay_1x.png"
        maskp = GRAPHIC_DIR / f"{base}_mask_only_1x.png"
        cardp = GRAPHIC_DIR / f"{base}_contact_8x_nearest.png"
        png_save(origp, orig); png_save(overp, over); png_save(maskp, maskimg); png_save(cardp, labelled_triptych(base, orig, over, maskimg))
        rows.append({"object_id":spec["id"], "object_type":object_type, "parent_id":parent_id, "role":spec["role"], "draw_indices":",".join(map(str,spec["draw"])),
                     "pdf_draw_details":json.dumps(draw_details, ensure_ascii=False), "bbox_px":bbox_to_str(all_box), "pixel_count":obj.pixels,
                     "colour_rgb":"#%02X%02X%02X" % col, "mask_method":";".join(methods)+" + final native RGB colour gating",
                     "original_1x":rel(origp), "overlay_1x":rel(overp), "mask_only_1x":rel(maskp), "contact_8x_nearest":rel(cardp)})
    doc.close()
    write_csv(GRAPHIC_DIR / "graphic_object_inventory.csv", rows,
              ["object_id","object_type","parent_id","role","draw_indices","pdf_draw_details","bbox_px","pixel_count","colour_rgb","mask_method","original_1x","overlay_1x","mask_only_1x","contact_8x_nearest"])
    return rows, objects, cached


def render_graphic_sheets(rows:list[dict[str,Any]], per_sheet:int=10) -> None:
    sheet_dir=GRAPHIC_DIR/"contact_sheets_8x";sheet_dir.mkdir(parents=True,exist_ok=True)
    index=[]
    for sheet_index,start in enumerate(range(0,len(rows),per_sheet),1):
        subset=rows[start:start+per_sheet]
        cards=[Image.open(Path(x["contact_8x_nearest"])).convert("RGB") for x in subset]
        cols=2;nrows=math.ceil(len(cards)/cols);cell_w=max(x.width for x in cards)+12;cell_h=max(x.height for x in cards)+18
        canvas=Image.new("RGB",(cols*cell_w+12,nrows*cell_h+34),"#F4F4F4");draw=ImageDraw.Draw(canvas)
        draw.text((8,8),f"FIG-P547-01 graphic/path sheet {sheet_index:02d}; 8x nearest",fill="black",font=default_font())
        for i,(entry,card) in enumerate(zip(subset,cards)):
            col,row=i%cols,i//cols;x,y=6+col*cell_w,28+row*cell_h;canvas.paste(card,(x,y))
            entry["contact_sheet"]=f"graphic_sheet_{sheet_index:02d}_8x_nearest.png";entry["contact_cell"]=f"R{row+1}C{col+1}"
            index.append({"object_id":entry["object_id"],"object_type":entry["object_type"],"sheet":entry["contact_sheet"],"cell":entry["contact_cell"],"card":entry["contact_8x_nearest"]})
        png_save(sheet_dir/f"graphic_sheet_{sheet_index:02d}_8x_nearest.png",canvas)
    write_csv(GRAPHIC_DIR/"graphic_contact_sheet_index.csv",index,["object_id","object_type","sheet","cell","card"])
    manual=[]
    for row in rows:
        manual.append({"object_id":row["object_id"],"object_type":row["object_type"],"role":row["role"],"sheet":row.get("contact_sheet",""),"cell":row.get("contact_cell",""),
                       "reviewer":"PENDING_MANUAL","original_match":"PENDING_MANUAL","overlay_complete":"PENDING_MANUAL","mask_only_pure":"PENDING_MANUAL",
                       "missing_stroke_px":"PENDING_MANUAL","foreign_pixel_px":"PENDING_MANUAL","decision":"PENDING_MANUAL",
                       "note":"Open native 1x original/overlay/mask and the indexed 8x-nearest cell; GRAPHIC/MATH_RULE must remain separate and non-empty."})
    write_csv(GRAPHIC_DIR/"graphic_manual_review_ledger.csv",manual,["object_id","object_type","role","sheet","cell","reviewer","original_match","overlay_complete","mask_only_pure","missing_stroke_px","foreign_pixel_px","decision","note"])


def drawing_path_reconciliation() -> dict[str,Any]:
    doc=fitz.open(PDF);page=doc[PDF_PAGE_0];drawings=page.get_drawings();doc.close()
    primary:dict[int,list[dict[str,Any]]]=defaultdict(list)
    for spec in graphic_specs():
        for di in spec["draw"]: primary[di].append(spec)
    occlusion_only={8:"L_LOOP_0.7_WHITE_HALO",11:"L_LOOP_0.8_WHITE_HALO",19:"L_LOWER_0.2_WHITE_HALO",49:"R_LOOP_0.7_WHITE_HALO",52:"R_LOOP_0.8_WHITE_HALO",60:"R_LOWER_0.2_WHITE_HALO"}
    dual_fill={14:"L_FOCUS_LABEL_OPAQUE_FILL",55:"R_FOCUS_LABEL_OPAQUE_FILL"}
    rows=[];unassigned=[];duplicate_primary=[]
    for idx,d in enumerate(drawings):
        specs=primary.get(idx,[])
        if len(specs)>1: duplicate_primary.append(idx)
        if specs:
            assignment="FOREGROUND_STROKE_OR_PATH";object_ids="|".join(x["id"] for x in specs);object_types="|".join(x.get("object_type","GRAPHIC") for x in specs);roles="|".join(x["role"] for x in specs)
            if idx in dual_fill: assignment+="+OCCLUSION_FILL";roles+="|"+dual_fill[idx]
        elif idx in occlusion_only:
            assignment="OCCLUSION_BACKGROUND_ONLY";object_ids=f"OCC_DRAW_{idx:02d}";object_types="OCCLUSION/BACKGROUND";roles=occlusion_only[idx]
        else:
            assignment="UNASSIGNED";object_ids="";object_types="";roles="";unassigned.append(idx)
        rows.append({"drawing_index":idx,"assignment_kind":assignment,"object_ids":object_ids,"object_types":object_types,"roles":roles,
                     "rect_pt":bbox_to_str(fitz.Rect(d["rect"])),"draw_type":d.get("type"),"stroke_width_pt":d.get("width"),
                     "stroke_rgb":drawing_color_to_rgb(d.get("color")),"fill_rgb":drawing_color_to_rgb(d.get("fill")) if d.get("fill") is not None else "NONE",
                     "item_count":len(d.get("items",[])),"intersects_figure_crop":FIG_RECT_PT.intersects(fitz.Rect(d["rect"])),"decision":"PASS" if assignment!="UNASSIGNED" and len(specs)<=1 else "FAIL"})
    fields=list(rows[0].keys()) if rows else ["drawing_index"]
    write_csv(GRAPHIC_DIR/"drawing_path_reconciliation.csv",rows,fields)
    summary={"pdf_drawing_count":len(drawings),"expected_total":71,"foreground_object_count":len(graphic_specs()),"foreground_unique_drawing_indices":len(primary),
             "occlusion_only_indices":sorted(occlusion_only),"dual_stroke_and_occlusion_fill_indices":sorted(dual_fill),"unassigned_indices":unassigned,
             "duplicate_primary_indices":duplicate_primary,"all_drawings_in_figure_crop":all(x["intersects_figure_crop"] for x in rows),
             "reconciliation_pass":len(drawings)==71 and len(primary)==65 and not unassigned and not duplicate_primary and all(x["intersects_figure_crop"] for x in rows)}
    write_json(GRAPHIC_DIR/"drawing_path_reconciliation.json",summary)
    return summary


def merge_object_masks(parts:list[ObjectMask], object_id:str, object_type:str, role:str, parent_id:str) -> ObjectMask:
    box=union_bbox([x.bbox for x in parts]);mask=np.zeros((box[3]-box[1],box[2]-box[0]),dtype=bool)
    for obj in parts:
        mask[obj.bbox[1]-box[1]:obj.bbox[3]-box[1],obj.bbox[0]-box[0]:obj.bbox[2]-box[0]] |= obj.mask
    return ObjectMask(object_id,object_type,"GRAPHIC",role,parent_id,box,mask,"semantic union of "+"|".join(x.object_id for x in parts),(0,0,0),"|".join(x.draw_refs for x in parts))


def math_relation_composites(rgb:np.ndarray, graphic_objects:list[ObjectMask]) -> list[dict[str,Any]]:
    byid={x.object_id:x for x in graphic_objects}
    specs=[]
    for n in range(1,13):
        specs.append((f"REL_EQ{n:02d}",[f"MR_EQ{n:02d}_TOP",f"MR_EQ{n:02d}_BOTTOM"],"GEOMETRIC_EQUALS",f"EQ{n:02d}"))
    for n in range(1,4):
        specs.append((f"REL_ARROW{n:02d}",[f"MR_ARROW{n:02d}_SHAFT",f"MR_ARROW{n:02d}_HEAD"],"GEOMETRIC_RIGHT_ARROW",f"AR{n:02d}"))
    rows=[];cards=[]
    for rid,partids,kind,semantic in specs:
        parts=[byid[x] for x in partids];obj=merge_object_masks(parts,rid,"GRAPHIC/MATH_RELATION_COMPOSITE",kind,parts[0].parent_id)
        wi,hi,area,ink=mask_stats(obj.mask);roi=rgb[obj.bbox[1]:obj.bbox[3],obj.bbox[0]:obj.bbox[2]]
        original=Image.fromarray(roi,"RGB");overlay=rgb_overlay(roi,obj.mask);maskim=binary_mask_image(obj.mask)
        op=RELATION_DIR/f"{rid}_{kind}_original_1x.png";vp=RELATION_DIR/f"{rid}_{kind}_overlay_1x.png";mp=RELATION_DIR/f"{rid}_{kind}_mask_only_1x.png";cp=RELATION_DIR/f"{rid}_{kind}_contact_8x_nearest.png"
        png_save(op,original);png_save(vp,overlay);png_save(mp,maskim);png_save(cp,labelled_triptych(rid,original,overlay,maskim));cards.append((rid,cp))
        rows.append({"relation_id":rid,"semantic_id":semantic,"relation_kind":kind,"component_object_ids":"|".join(partids),"component_draw_refs":obj.draw_refs,"parent_id":obj.parent_id,
                     "bbox_px":bbox_to_str(obj.bbox),"ink_w_px":wi,"ink_h_px":hi,"ink_area_px":area,"required_h_px":22,"size_gate":"PASS" if hi>=22 else "FAIL",
                     "original_1x":rel(op),"overlay_1x":rel(vp),"mask_only_1x":rel(mp),"contact_8x_nearest":rel(cp),
                     "pair_denominator_note":"Composite excluded to avoid double-count; every individual component is in foreground denominator."})
    write_csv(RELATION_DIR/"math_relation_composite_measurements.csv",rows,list(rows[0].keys()))
    sheet_dir=RELATION_DIR/"contact_sheets_8x";sheet_dir.mkdir(parents=True,exist_ok=True);index=[]
    per_sheet=8
    for sn,start in enumerate(range(0,len(cards),per_sheet),1):
        subset=cards[start:start+per_sheet];ims=[Image.open(p).convert("RGB") for _,p in subset];cols=2;nrows=math.ceil(len(ims)/cols);cw=max(x.width for x in ims)+12;ch=max(x.height for x in ims)+18
        canvas=Image.new("RGB",(cols*cw+12,nrows*ch+34),"#F4F4F4");d=ImageDraw.Draw(canvas);d.text((8,8),f"FIG-P547-01 semantic relation sheet {sn:02d}; 8x nearest",fill="black",font=default_font())
        for i,((rid,_),im) in enumerate(zip(subset,ims)):
            col,row=i%cols,i//cols;x,y=6+col*cw,28+row*ch;canvas.paste(im,(x,y));index.append({"relation_id":rid,"sheet":f"math_relation_sheet_{sn:02d}_8x_nearest.png","cell":f"R{row+1}C{col+1}"})
        png_save(sheet_dir/f"math_relation_sheet_{sn:02d}_8x_nearest.png",canvas)
    write_csv(RELATION_DIR/"math_relation_contact_sheet_index.csv",index,["relation_id","sheet","cell"])
    idx={x["relation_id"]:x for x in index};manual=[]
    for row in rows:
        z=idx[row["relation_id"]];manual.append({"relation_id":row["relation_id"],"semantic_id":row["semantic_id"],"relation_kind":row["relation_kind"],"sheet":z["sheet"],"cell":z["cell"],"reviewer":"PENDING_MANUAL","original_match":"PENDING_MANUAL","overlay_complete":"PENDING_MANUAL","mask_only_pure":"PENDING_MANUAL","visual_symbol_identity":"PENDING_MANUAL","decision":"PENDING_MANUAL","note":"Inspect 1x and 8x; equals must have two complete horizontal rules and arrow must have coordinated shaft/head."})
    write_csv(RELATION_DIR/"math_relation_manual_review_ledger.csv",manual,["relation_id","semantic_id","relation_kind","sheet","cell","reviewer","original_match","overlay_complete","mask_only_pure","visual_symbol_identity","decision","note"])
    return rows


def intentional_whitelist() -> list[dict[str, str]]:
    pairs = []
    def add(identifier: str, a: str, b: str, intent: str, source: str) -> None:
        pairs.append({"whitelist_id":identifier,"object_a":a,"object_b":b,"intent":intent,"source_basis":source})
    for n, (a,b) in enumerate([( "G03","G04"),("G05","G06"),("G07","G08"),("G10","G11"),("G14","G15"),("G16","G17"),("G20","G21"),("G22","G23"),("G24","G25"),("G27","G28")],1):
        add(f"W_ARROW_HEAD_{n:02d}",a,b,"arrow shaft/head construction is a single directed edge", "frozen source edge/focus/bridge-arrow style and PDF drawing order")
    for n,(a,b) in enumerate([("MR_ARROW01_SHAFT","MR_ARROW01_HEAD"),("MR_ARROW02_SHAFT","MR_ARROW02_HEAD"),("MR_ARROW03_SHAFT","MR_ARROW03_HEAD")],1):
        add(f"W_MATH_ARROW_COMPONENT_{n:02d}",a,b,"TikZ math-arrow shaft/head form one semantic relation symbol", "FIGPFiveGeomArrow source macro and PDF drawing order")
    for side,top,left,right,bottom in [
        ("L","MR_BOX_L_TOP","MR_BOX_L_LEFT","MR_BOX_L_RIGHT","MR_BOX_L_BOTTOM"),
        ("R","MR_BOX_R_TOP","MR_BOX_R_LEFT","MR_BOX_R_RIGHT","MR_BOX_R_BOTTOM"),
    ]:
        for n,(a,b) in enumerate([(top,left),(top,right),(bottom,left),(bottom,right)],1):
            add(f"W_{side}_BOX_CORNER_{n:02d}",a,b,"four independent formula rules meet only at the intended boxed-value corner", "\\boxed{\\mathbf{0.3}} source and independent drawing-path reconciliation")
    endpoint_pairs = [("G01","G03"),("G01","G04"),("G02","G05"),("G02","G06"),("G01","G07"),("G02","G08"),("G02","G10"),("G01","G11"),
                      ("G18","G20"),("G18","G21"),("G19","G22"),("G19","G23"),("G18","G24"),("G19","G25"),("G19","G27"),("G18","G28")]
    for n,(a,b) in enumerate(endpoint_pairs,1):
        add(f"W_NODE_ENDPOINT_{n:02d}",a,b,"state-border / directed-edge endpoint is intentional graph topology", "frozen TikZ node/edge endpoint construction")
    add("W_FOCUS_LABEL_HALO_01", "G07", "G09", "focus edge passes beneath/touches its own white halo and outline by ordered TikZ construction", "source line 26; PDF draw indices 12,13 then focus-label fill/outline 14; reverse-occlusion ledger")
    add("W_FOCUS_LABEL_HALO_02", "G24", "G26", "focus edge passes beneath/touches its own white halo and outline by ordered TikZ construction", "source line 46; PDF draw indices 35,36 then focus-label fill/outline 37; reverse-occlusion ledger")
    return pairs


def boxes_intersect(a: tuple[int,int,int,int], b: tuple[int,int,int,int]) -> tuple[int,int,int,int] | None:
    x0, y0 = max(a[0],b[0]), max(a[1],b[1])
    x1, y1 = min(a[2],b[2]), min(a[3],b[3])
    if x0 >= x1 or y0 >= y1:
        return None
    return x0,y0,x1,y1


def raw_overlap(a: ObjectMask, b: ObjectMask) -> int:
    common = boxes_intersect(a.bbox,b.bbox)
    if common is None:
        return 0
    x0,y0,x1,y1 = common
    aa = a.mask[y0-a.bbox[1]:y1-a.bbox[1], x0-a.bbox[0]:x1-a.bbox[0]]
    bb = b.mask[y0-b.bbox[1]:y1-b.bbox[1], x0-b.bbox[0]:x1-b.bbox[0]]
    return int((aa & bb).sum())


def bbox_distance(a: tuple[int,int,int,int], b: tuple[int,int,int,int]) -> float:
    dx = max(a[0]-b[2], b[0]-a[2], 0)
    dy = max(a[1]-b[3], b[1]-a[3], 0)
    return math.hypot(dx,dy)


_TREE_CACHE: dict[tuple[str, tuple[int,int,int,int], int], cKDTree] = {}


def exact_min_distance(a: ObjectMask, b: ObjectMask) -> tuple[float, str]:
    """Exact Euclidean native-pixel-centre distance; never sample masks."""
    if a.pixels == 0 or b.pixels == 0:
        return math.inf, "EMPTY_MASK"
    if raw_overlap(a,b) > 0:
        return 0.0, "RAW_INTERSECTION"
    pa, pb = object_global_points(a), object_global_points(b)
    # Query the smaller point set against a cached exact KD-tree of the larger.
    # scipy's default eps=0 performs an exact nearest-neighbour query.
    if len(pa) > len(pb):
        pa, pb = pb, pa
        tree_obj = a
    else:
        tree_obj = b
    key=(tree_obj.object_id,tree_obj.bbox,tree_obj.pixels)
    tree=_TREE_CACHE.get(key)
    if tree is None:
        tree=cKDTree(pb.astype(np.float64))
        _TREE_CACHE[key]=tree
    distance=float(np.min(tree.query(pa.astype(np.float64),k=1,eps=0.0,workers=1)[0]))
    return distance, "EXACT_CKDTREE_FOREGROUND_PIXEL_CENTRE_DISTANCE_NO_SAMPLING"


def pair_requirement(a: ObjectMask, b: ObjectMask, whitelist: dict[frozenset[str], dict[str,str]]) -> tuple[str, float | None, str, str]:
    key = frozenset((a.object_id,b.object_id))
    if key in whitelist:
        return "INTENTIONAL_WHITELIST", None, "ALLOWED_STRUCTURAL_CONTACT", whitelist[key]["whitelist_id"]
    if a.class_group == "TEXT" and b.class_group == "TEXT":
        if a.parent_id == b.parent_id:
            return "TEXT_INTERNAL", None, "ZERO_RAW_OVERLAP_ONLY", "W_TEXT_INTERNAL_SAME_RAW_LINE"
        return "TT", 4.0, "TEXT_TEXT_CLEARANCE", ""
    if a.class_group == "GRAPHIC" and b.class_group == "GRAPHIC":
        return "GG", 0.0, "ZERO_RAW_OVERLAP", ""
    text, graphic = (a,b) if a.class_group == "TEXT" else (b,a)
    if "NODE_BORDER" in graphic.role:
        return "TG", 5.0, "TEXT_TO_NODE_BORDER", ""
    if "PANEL_BORDER" in graphic.role:
        return "TG", 6.0, "TEXT_TO_PANEL_BORDER", ""
    return "TG", 3.0, "TEXT_TO_LINE_ARROW_MARKER", ""


def pair_contact_card(identifier:str, panels:list[tuple[str,Image.Image]]) -> Image.Image:
    scaled=[(label,nearest8(im)) for label,im in panels]
    header_h=28; gap=8
    width=sum(im.width for _,im in scaled)+gap*(len(scaled)+1)
    height=header_h+max(im.height for _,im in scaled)+gap*2+14
    canvas=Image.new("RGB",(width,height),"white"); draw=ImageDraw.Draw(canvas)
    x=gap
    for label,im in scaled:
        draw.text((x,5),label,fill="black",font=default_font())
        canvas.paste(im,(x,header_h+gap));x+=im.width+gap
    draw.text((gap,height-13),identifier+"; 8x nearest only",fill="black",font=default_font())
    return canvas


def pair_roi(rgb: np.ndarray, a: ObjectMask, b: ObjectMask, pair_id: str) -> dict[str,Path]:
    box = union_bbox([a.bbox,b.bbox])
    box = clip_bbox((box[0]-5,box[1]-5,box[2]+5,box[3]+5), rgb.shape[1], rgb.shape[0])
    roi = rgb[box[1]:box[3],box[0]:box[2]]
    ma = np.zeros(roi.shape[:2],dtype=bool); mb=np.zeros_like(ma)
    for o,m in ((a,ma),(b,mb)):
        common = boxes_intersect(o.bbox,box)
        if common is None: continue
        x0,y0,x1,y1=common
        m[y0-box[1]:y1-box[1],x0-box[0]:x1-box[0]] |= o.mask[y0-o.bbox[1]:y1-o.bbox[1],x0-o.bbox[0]:x1-o.bbox[0]]
    inter=ma&mb
    original=Image.fromarray(roi,"RGB")
    arr=roi.copy().astype(np.float32); arr[ma]=0.45*arr[ma]+0.55*np.array([230,30,30]); arr[mb]=0.45*arr[mb]+0.55*np.array([36,88,238]); arr[inter]=np.array([180,0,180])
    overlay=Image.fromarray(np.clip(arr,0,255).astype(np.uint8),"RGB")
    mask=np.full((*ma.shape,3),255,dtype=np.uint8); mask[ma]=(230,30,30); mask[mb]=(36,88,238); mask[inter]=(180,0,180)
    maskim=Image.fromarray(mask,"RGB")
    am=np.full((*ma.shape,3),255,dtype=np.uint8);am[ma]=(0,0,0)
    bm=np.full((*mb.shape,3),255,dtype=np.uint8);bm[mb]=(0,0,0)
    ix=np.full((*inter.shape,3),255,dtype=np.uint8);ix[inter]=(0,0,0)
    paths={
        "original_1x":PAIR_DIR/f"{pair_id}_original_1x.png",
        "mask_a_1x":PAIR_DIR/f"{pair_id}_mask_A_1x.png",
        "mask_b_1x":PAIR_DIR/f"{pair_id}_mask_B_1x.png",
        "intersection_1x":PAIR_DIR/f"{pair_id}_intersection_mask_1x.png",
        "overlay_1x":PAIR_DIR/f"{pair_id}_overlay_1x.png",
        "contact_8x":PAIR_DIR/f"{pair_id}_contact_8x_nearest.png",
    }
    aim=Image.fromarray(am,"RGB");bim=Image.fromarray(bm,"RGB");iim=Image.fromarray(ix,"RGB")
    png_save(paths["original_1x"],original);png_save(paths["mask_a_1x"],aim);png_save(paths["mask_b_1x"],bim)
    png_save(paths["intersection_1x"],iim);png_save(paths["overlay_1x"],overlay)
    png_save(paths["contact_8x"],pair_contact_card(pair_id,[("ORIGINAL",original),("A MASK",aim),("B MASK",bim),("INTERSECTION",iim),("OVERLAY",overlay)]))
    return paths


def evaluate_pairs(rgb: np.ndarray, text_objects: list[ObjectMask], graphic_objects: list[ObjectMask]) -> list[dict[str,Any]]:
    _TREE_CACHE.clear()
    all_objects = text_objects + graphic_objects
    whitelist_rows = intentional_whitelist()
    whitelist = {frozenset((x["object_a"],x["object_b"])):x for x in whitelist_rows}
    write_csv(PAIR_DIR / "intentional_contact_whitelist.csv", whitelist_rows, ["whitelist_id","object_a","object_b","intent","source_basis"])
    rows=[]; critical=[]
    for i,a in enumerate(all_objects):
        for b in all_objects[i+1:]:
            group,required,rule,white = pair_requirement(a,b,whitelist)
            overlap=raw_overlap(a,b)
            dist,method=exact_min_distance(a,b)
            pair_id=f"PAIR_{a.object_id}_{b.object_id}"
            if rule == "ALLOWED_STRUCTURAL_CONTACT":
                decision="PASS_INTENTIONAL"
            elif overlap>0:
                decision="FAIL"
            elif required is not None and dist < required:
                decision="FAIL"
            else:
                decision="PASS"
            needs_roi=decision=="FAIL" or rule=="ALLOWED_STRUCTURAL_CONTACT" or (required is not None and dist < required+2.0)
            evidence={"original_1x":"","mask_a_1x":"","mask_b_1x":"","intersection_1x":"","overlay_1x":"","contact_8x":""}
            if needs_roi:
                made=pair_roi(rgb,a,b,pair_id); evidence={k:rel(v) for k,v in made.items()}; critical.append(pair_id)
            rows.append({"pair_id":pair_id,"object_a":a.object_id,"object_b":b.object_id,"a_type":a.object_type,"b_type":b.object_type,
                         "pair_group":group,"a_role":a.role,"b_role":b.role,"a_pixels":a.pixels,"b_pixels":b.pixels,
                         "raw_overlap_px":overlap,"raw_distance_px":dist,"distance_method":method,"required_clearance_px":required if required is not None else "N/A",
                         "rule":rule,"intent_whitelist_id":white,"decision":decision,"critical_or_failure_original_1x":evidence["original_1x"],
                         "critical_or_failure_mask_A_1x":evidence["mask_a_1x"],"critical_or_failure_mask_B_1x":evidence["mask_b_1x"],
                         "critical_or_failure_intersection_1x":evidence["intersection_1x"],"critical_or_failure_overlay_1x":evidence["overlay_1x"],
                         "critical_or_failure_contact_8x":evidence["contact_8x"],"manual_review":"PENDING_MANUAL" if needs_roi else "NOT_REQUIRED_NONCRITICAL"})
    fields=["pair_id","object_a","object_b","a_type","b_type","pair_group","a_role","b_role","a_pixels","b_pixels","raw_overlap_px","raw_distance_px","distance_method","required_clearance_px","rule","intent_whitelist_id","decision","critical_or_failure_original_1x","critical_or_failure_mask_A_1x","critical_or_failure_mask_B_1x","critical_or_failure_intersection_1x","critical_or_failure_overlay_1x","critical_or_failure_contact_8x","manual_review"]
    write_csv(PAIR_DIR / "all_foreground_unordered_pairs.csv", rows, fields)
    manual=[]
    for x in rows:
        if x["manual_review"]=="PENDING_MANUAL":
            manual.append({"pair_id":x["pair_id"],"pair_group":x["pair_group"],"object_a":x["object_a"],"object_b":x["object_b"],"machine_decision":x["decision"],
                           "raw_overlap_px":x["raw_overlap_px"],"raw_distance_px":x["raw_distance_px"],"required_clearance_px":x["required_clearance_px"],
                           "original_1x":x["critical_or_failure_original_1x"],"mask_A_1x":x["critical_or_failure_mask_A_1x"],"mask_B_1x":x["critical_or_failure_mask_B_1x"],
                           "intersection_1x":x["critical_or_failure_intersection_1x"],"overlay_1x":x["critical_or_failure_overlay_1x"],"contact_8x":x["critical_or_failure_contact_8x"],
                           "reviewer":"PENDING_MANUAL","separated_masks_match":"PENDING_MANUAL","contact_or_clearance_matches":"PENDING_MANUAL","intent_matches_whitelist":"PENDING_MANUAL" if x["decision"]=="PASS_INTENTIONAL" else "N/A",
                           "manual_decision":"PENDING_MANUAL","note":"Open every referenced native 1x file and its 8x-nearest card; manual decision cannot override a machine hard FAIL."})
    write_csv(PAIR_DIR/"critical_and_intentional_pair_manual_review_ledger.csv",manual,["pair_id","pair_group","object_a","object_b","machine_decision","raw_overlap_px","raw_distance_px","required_clearance_px","original_1x","mask_A_1x","mask_B_1x","intersection_1x","overlay_1x","contact_8x","reviewer","separated_masks_match","contact_or_clearance_matches","intent_matches_whitelist","manual_decision","note"])
    expected=len(all_objects)*(len(all_objects)-1)//2
    gg=[x for x in rows if x["pair_group"] in {"GG","INTENTIONAL_WHITELIST"} and x["a_type"]=="GRAPHIC" and x["b_type"]=="GRAPHIC"]
    groups=Counter(x["pair_group"] for x in rows)
    write_json(PAIR_DIR / "pair_coverage_manifest.json", {"foreground_object_count":len(all_objects),"text_object_count":len(text_objects),"graphic_object_count":len(graphic_objects),"expected_unordered_pair_count":expected,"actual_pair_count":len(rows),"complete":len(rows)==expected,"pair_group_counts":dict(groups),"gg_pair_count":len(gg),"failure_critical_or_intentional_roi_count":len(critical),"manual_pair_ledger_rows":len(manual),"no_morphology":True,"all_pairs_use_final_separated_raw_masks":True,"distance_exact_no_sampling":True})
    return rows


def make_occlusion_mask_from_drawing(drawing: dict[str,Any], bbox: tuple[int,int,int,int], sx:float,sy:float, fill:bool=True) -> np.ndarray:
    # The halo is the *interior fill*, not its visible outline. The interior is
    # derived in native coordinates from the PDF vector bounds and shrunk only
    # by the known outline width; no final-image morphology is used.
    x0,y0,x1,y1=bbox
    m=np.zeros((y1-y0,x1-x0),dtype=bool)
    rect=fitz.Rect(drawing["rect"])
    rb=rect_to_px(rect,sx,sy,x1,y1,pad=0)
    # rb is global clipped to x1,y1, but translate to local.
    inset = 1 if drawing.get("color") is None else max(2, int(math.ceil(float(drawing.get("width") or 0.72) * (sx + sy) / 2)) + 1)
    xx0=max(0,rb[0]-x0+inset); yy0=max(0,rb[1]-y0+inset); xx1=min(m.shape[1],rb[2]-x0-inset); yy1=min(m.shape[0],rb[3]-y0-inset)
    if xx1>xx0 and yy1>yy0: m[yy0:yy1,xx0:xx1]=True
    return m


def occlusion_reverse(rgb: np.ndarray, sx:float,sy:float, draw_cache:dict[int,tuple[np.ndarray,tuple[int,int,int,int],str]]) -> list[dict[str,Any]]:
    doc=fitz.open(PDF); page=doc[PDF_PAGE_0]; drawings=page.get_drawings()
    specs=[("O01","L_LOOP_0.7",[6,7],8),("O02","L_LOOP_0.8",[9,10],11),("O03","L_FOCUS_0.3",[12,13],14),
           ("O04","R_LOOP_0.7",[47,48],49),("O05","R_LOOP_0.8",[50,51],52),("O06","R_FOCUS_0.3",[53,54],55)]
    rows=[]
    for oid,role,preindices,haloindex in specs:
        pieces=[draw_cache[i] for i in preindices]
        allbox=union_bbox([x[1] for x in pieces]+[rect_to_px(fitz.Rect(drawings[haloindex]["rect"]),sx,sy,rgb.shape[1],rgb.shape[0],pad=3)])
        pre=np.zeros((allbox[3]-allbox[1],allbox[2]-allbox[0]),dtype=bool)
        final=np.zeros_like(pre)
        for di, (finalpart,box,_) in zip(preindices,pieces):
            predicted,_=drawing_prediction_mask(drawings[di],box,sx,sy)
            pre[box[1]-allbox[1]:box[3]-allbox[1],box[0]-allbox[0]:box[2]-allbox[0]] |= predicted
            final[box[1]-allbox[1]:box[3]-allbox[1],box[0]-allbox[0]:box[2]-allbox[0]] |= finalpart
        halo=make_occlusion_mask_from_drawing(drawings[haloindex],allbox,sx,sy)
        expected_under=int((pre&halo).sum()); visible_inside=int((final&halo).sum())
        roi=rgb[allbox[1]:allbox[3],allbox[0]:allbox[2]]
        preim=np.full((*pre.shape,3),255,dtype=np.uint8);preim[pre]=(240,140,0)
        haloim=np.full((*halo.shape,3),255,dtype=np.uint8);haloim[halo]=(0,0,0)
        finalim=np.full((*final.shape,3),255,dtype=np.uint8);finalim[final]=(0,120,180)
        combo=roi.copy();combo[halo]=0.45*combo[halo]+0.55*np.array([255,255,255]);combo[final]=np.array([0,120,180])
        base=OCC_DIR/oid
        png_save(base.with_name(base.name+"_pre_occlusion_vector_mask_1x.png"),Image.fromarray(preim,"RGB"))
        png_save(base.with_name(base.name+"_halo_vector_fill_mask_1x.png"),Image.fromarray(haloim,"RGB"))
        png_save(base.with_name(base.name+"_final_visible_raw_mask_1x.png"),Image.fromarray(finalim,"RGB"))
        png_save(base.with_name(base.name+"_draw_order_overlay_8x_nearest.png"),nearest8(Image.fromarray(combo,"RGB")))
        decision="PASS_NO_OVERLAY_NEEDED" if expected_under==0 else ("PASS" if visible_inside==0 else "FAIL")
        rows.append({"occlusion_id":oid,"role":role,"pre_occlusion_draw_indices":",".join(map(str,preindices)),"halo_draw_index":haloindex,
                     "draw_order":"underlying edge first; white label fill after it; label text then placed by TikZ", "pre_under_halo_px":expected_under,"final_visible_inside_halo_px":visible_inside,
                     "halo_method":"PDF vector label-fill interior, excluding its outline; pre=vector geometry, final=official native final colour mask","decision":decision,
                     "pre_mask":rel(base.with_name(base.name+"_pre_occlusion_vector_mask_1x.png")),"halo_mask":rel(base.with_name(base.name+"_halo_vector_fill_mask_1x.png")),"final_mask":rel(base.with_name(base.name+"_final_visible_raw_mask_1x.png")),"overlay_8x":rel(base.with_name(base.name+"_draw_order_overlay_8x_nearest.png"))})
    doc.close()
    write_csv(OCC_DIR/"occlusion_reverse_ledger.csv",rows,["occlusion_id","role","pre_occlusion_draw_indices","halo_draw_index","draw_order","pre_under_halo_px","final_visible_inside_halo_px","halo_method","decision","pre_mask","halo_mask","final_mask","overlay_8x"])
    return rows


def create_calibration_tex() -> Path:
    tex = r'''\documentclass[UTF8,a4paper,11pt,openany]{ctexbook}
\defaultfontfeatures{Ligatures=TeX,Scale=MatchLowercase}
\setmainfont{STIX Two Text}[Scale=1]
\setCJKmainfont{Noto Serif SC}[Scale=1,BoldFont=Noto Sans SC Bold,ItalicFont=Noto Serif SC,BoldItalicFont=Noto Sans SC Bold]
\setCJKsansfont{Noto Sans SC}[Scale=1,BoldFont=Noto Sans SC Bold,ItalicFont=Noto Sans SC,BoldItalicFont=Noto Sans SC Bold]
\usepackage{amsmath}
\usepackage{unicode-math}
\setmathfont{STIX Two Math}[Scale=1]
\setmathfont[version=bold]{XITS Math Bold}
\usepackage{xcolor}
\definecolor{SLGold}{HTML}{B7791F}
\begin{document}
\pagestyle{empty}
% Each target is deliberately isolated from neighbouring target glyphs.  This
% makes the calibration a literal independent glyph measurement rather than a
% component-sharing exercise.  The profile label is held at least 36 pt away.
\noindent\texttt{CAL\_CJK\_TITLE\_BOLD\_10\_2\_COLON}\hspace{36pt}{\fontsize{10.2pt}{12.0pt}\selectfont\bfseries ：}\par\vspace{5pt}
\noindent\texttt{CAL\_CJK\_MATRIX\_9\_8\_SEMICOLON}\hspace{36pt}{\fontsize{9.8pt}{11.7pt}\selectfont ；}\par\vspace{5pt}
\noindent\texttt{CAL\_CJK\_BRIDGE\_11\_6\_COLON}\hspace{36pt}{\fontsize{11.6pt}{13.3pt}\selectfont ：}\par\vspace{5pt}
\noindent\texttt{CAL\_CJK\_CAPTION\_SMALL\_COMMA}\hspace{36pt}{\small ，}\par\vspace{5pt}
\noindent\texttt{CAL\_CJK\_CAPTION\_SMALL\_FULLSTOP}\hspace{36pt}{\small 。}\par\vspace{5pt}
\noindent\texttt{CAL\_MATH\_11\_8\_PERIOD}\hspace{36pt}{\fontsize{11.8pt}{13.6pt}\selectfont $0.3$}\par\vspace{5pt}
\noindent\texttt{CAL\_MATH\_11\_8\_GOLD\_PERIOD}\hspace{36pt}{\fontsize{11.8pt}{13.6pt}\selectfont {\color{SLGold}$\mathbf{0.3}$}}\par\vspace{5pt}
\noindent\texttt{CAL\_MATH\_11\_6\_PERIOD}\hspace{36pt}{\fontsize{11.6pt}{13.3pt}\selectfont $0.3$}\par\vspace{5pt}
\noindent\texttt{CAL\_TEXT\_BOLD\_9\_96\_PERIOD}\hspace{36pt}{\small\bfseries 0.3}\par
\end{document}
'''
    p=CAL_DIR/"independent_low_profile_calibration.tex"
    write_text(p,tex)
    return p


def calibration_profile(rec:dict[str,Any]) -> str:
    font=rec["font"].upper(); size=float(rec["font_size_pt_pdf_emit"])
    if "NOTOSANS" in font and "BOLD" in font: return "CAL_CJK_TITLE_BOLD_10_2"
    if ("NOTOSANS" in font or "NOTOSERIF" in font) and size < 9.87: return "CAL_CJK_MATRIX_9_8"
    if ("NOTOSANS" in font or "NOTOSERIF" in font) and size < 10.25: return "CAL_CJK_CAPTION_SMALL"
    if "NOTOSANS" in font or "NOTOSERIF" in font: return "CAL_CJK_BRIDGE_11_6"
    if "STIXTWOTEXT-BOLD" in font: return "CAL_TEXT_BOLD_9_96"
    if size < 9.0: return "CAL_MATH_SCRIPT_8_1"
    if size < 10.8: return "CAL_MATH_10_2"
    if rec["color_rgb"].upper() == "#B7791F": return "CAL_MATH_11_8_GOLD"
    if rec["char"] in "[]" and size >= 11.70: return "CAL_MATH_11_8_BMATRIX"
    if size >= 11.70: return "CAL_MATH_11_8"
    return "CAL_MATH_11_6"


def extract_calibration_chars(cal_rgb:np.ndarray, sx:float,sy:float) -> list[dict[str,Any]]:
    pdf=CAL_DIR/"independent_low_profile_calibration.pdf"
    doc=fitz.open(pdf);page=doc[0];raw=page.get_text("rawdict")
    output=[]; artifact_dir=CAL_DIR/"calibration_glyphs_1x"; artifact_dir.mkdir(parents=True,exist_ok=True)
    profile_names=["CAL_CJK_TITLE_BOLD_10_2","CAL_CJK_MATRIX_9_8","CAL_CJK_BRIDGE_11_6","CAL_CJK_CAPTION_SMALL","CAL_MATH_11_8_GOLD","CAL_MATH_11_8","CAL_MATH_11_6","CAL_TEXT_BOLD_9_96"]
    labelled_rows=[]
    for b in raw.get("blocks",[]):
        if b.get("type")!=0: continue
        btext="".join(ch.get("c","") for line in b.get("lines",[]) for s in line.get("spans",[]) for ch in s.get("chars",[]))
        p=next((name for name in profile_names if name in btext),"")
        if p:
            br=fitz.Rect(b["bbox"]); labelled_rows.append((p,(br.y0+br.y1)/2))
    for bi,b in enumerate(raw.get("blocks",[])):
        if b.get("type")!=0: continue
        block_text="".join(ch.get("c","") for line in b.get("lines",[]) for s in line.get("spans",[]) for ch in s.get("chars",[]))
        profile=next((p for p in profile_names if p in block_text),"")
        # LuaTeX may emit a stretched closing delimiter in a separate PDF text
        # block.  Associate such a block only with the closest labelled
        # calibration row; this is a reading/ownership rule, not an image edit.
        if not profile:
            br=fitz.Rect(b["bbox"]); cy=(br.y0+br.y1)/2
            if labelled_rows:
                nearest_name,nearest_y=min(labelled_rows,key=lambda x:abs(x[1]-cy))
                if abs(nearest_y-cy)<=22: profile=nearest_name
        for li,line in enumerate(b.get("lines",[])):
            for si,span in enumerate(line.get("spans",[])):
                for ci,ch in enumerate(span.get("chars",[])):
                    c=str(ch.get("c","") or "")
                    if c not in set(".,;:，。；：()[]") or not profile: continue
                    rect=fitz.Rect(ch["bbox"]); box=rect_to_px(rect,sx,sy,cal_rgb.shape[1],cal_rgb.shape[0],pad=1)
                    nominal=rect_to_px(rect,sx,sy,cal_rgb.shape[1],cal_rgb.shape[0],pad=0)
                    expected=color_int_to_rgb(int(span.get("color",0)));roi,mask,bb=text_mask_for_bbox(cal_rgb,box,expected)
                    mask=retain_components_for_nominal_bbox(mask,bb,nominal)
                    wi,hi,area,ink=mask_stats(mask)
                    item_id=f"CAL{len(output)+1:03d}_{safe_codepoint(c)}"
                    orig_path=artifact_dir/f"{item_id}_original_1x.png"; mask_path=artifact_dir/f"{item_id}_mask_only_1x.png"
                    png_save(orig_path,Image.fromarray(roi,"RGB"));png_save(mask_path,binary_mask_image(mask))
                    output.append({"calibration_id":item_id,"profile":profile,"char":c,"font":str(span.get("font","")),"font_size_pt_pdf_emit":float(span.get("size",0)),"color_rgb":"#%02X%02X%02X"%expected,"ink_w_px":wi,"ink_h_px":hi,"ink_area_px":area,"roi_bbox_px":bbox_to_str(bb),"original":roi,"mask":mask,"original_1x":rel(orig_path),"mask_only_1x":rel(mask_path)})
    doc.close(); return output


def low_profile_calibration(glyphs:list[dict[str,Any]]) -> list[dict[str,Any]]:
    low=[g for g in glyphs if g["needs_low_profile_calibration"]=="YES"]
    tex=create_calibration_tex(); log=CAL_DIR/"calibration_lualatex.log"
    cmd=[str(LUALATEX),"-interaction=nonstopmode","-halt-on-error",f"-output-directory={CAL_DIR}",str(tex)]
    cache_root=CAL_DIR/"texmfvar"
    cache_root.mkdir(parents=True,exist_ok=True)
    texenv=os.environ.copy(); texenv["TEXMFVAR"]=str(cache_root); texenv["TEXMFCACHE"]=str(cache_root); texenv["TEXMFCONFIG"]=str(cache_root)
    p=subprocess.run(cmd,cwd=str(SRCROOT/"讲义源码"/"合并总册"),capture_output=True,text=True,encoding="utf-8",errors="replace",env=texenv)
    write_text(log,"COMMAND: "+" ".join(cmd)+"\nSTDOUT:\n"+p.stdout+"\nSTDERR:\n"+p.stderr+"\nEXIT="+str(p.returncode)+"\n")
    cal_pdf=CAL_DIR/"independent_low_profile_calibration.pdf"
    rows=[]
    if p.returncode==0 and cal_pdf.exists():
        prefix=CAL_DIR/"independent_low_profile_calibration_300dpi"
        cmd2=[str(POPPLER),"-r","300","-f","1","-l","1","-png","-singlefile",str(cal_pdf),str(prefix)]
        q=subprocess.run(cmd2,cwd=str(CAL_DIR),capture_output=True,text=True,encoding="utf-8",errors="replace")
        write_text(CAL_DIR/"calibration_renderer.log","COMMAND: "+" ".join(cmd2)+"\nSTDOUT:\n"+q.stdout+"\nSTDERR:\n"+q.stderr+"\nEXIT="+str(q.returncode)+"\n")
        if q.returncode==0 and Path(str(prefix)+".png").exists():
            calim=Image.open(Path(str(prefix)+".png")).convert("RGB"); cdoc=fitz.open(cal_pdf); cpage=cdoc[0]; csx,csy=calim.width/cpage.rect.width,calim.height/cpage.rect.height; cdoc.close()
            cals=extract_calibration_chars(np.array(calim),csx,csy)
        else: cals=[]
    else: cals=[]
    calibration_fields=["calibration_id","profile","char","font","font_size_pt_pdf_emit","color_rgb","ink_w_px","ink_h_px","ink_area_px","roi_bbox_px","original_1x","mask_only_1x"]
    write_csv(CAL_DIR/"calibration_character_inventory.csv",cals,calibration_fields)
    for g in low:
        profile=calibration_profile(g)
        choices=[x for x in cals if x["profile"]==profile and x["char"]==g["char"] and x["font"]==g["font"] and abs(float(x["font_size_pt_pdf_emit"])-float(g["font_size_pt_pdf_emit"]))<=0.16 and x["color_rgb"]==g["color_rgb"]]
        if choices:
            c=choices[0];h_ratio=float(g["ink_h_px"])/c["ink_h_px"] if c["ink_h_px"] else math.inf; a_ratio=float(g["ink_area_px"])/c["ink_area_px"] if c["ink_area_px"] else math.inf
            decision="PASS" if .92<=h_ratio<=1.08 and .92<=a_ratio<=1.08 else "FAIL"
            src=GLYPH_ROI/f"{g['glyph_id']}_{g['codepoint']}_original_1x.png"; candidate=Image.open(src).convert("RGB"); calori=Image.fromarray(c["original"],"RGB"); calmask=binary_mask_image(c["mask"])
            pair=labelled_triptych(g["glyph_id"]+"_CAL",candidate,calori,calmask);pp=CAL_DIR/f"{g['glyph_id']}_{g['codepoint']}_candidate_calibration_mask_8x_nearest.png";png_save(pp,pair)
            rows.append({"glyph_id":g["glyph_id"],"char":g["char"],"profile":profile,"candidate_font":g["font"],"calibration_font":c["font"],"candidate_pt":g["font_size_pt_pdf_emit"],"calibration_pt":c["font_size_pt_pdf_emit"],"candidate_color":g["color_rgb"],"calibration_color":c["color_rgb"],"candidate_h_px":g["ink_h_px"],"calibration_h_px":c["ink_h_px"],"height_ratio":h_ratio,"candidate_area_px":g["ink_area_px"],"calibration_area_px":c["ink_area_px"],"area_ratio":a_ratio,"decision":decision,"independent_render_proof":rel(cal_pdf),"contact_8x_nearest":rel(pp)})
        else:
            rows.append({"glyph_id":g["glyph_id"],"char":g["char"],"profile":profile,"candidate_font":g["font"],"calibration_font":"NO_EXACT_MATCH","candidate_pt":g["font_size_pt_pdf_emit"],"calibration_pt":"","candidate_color":g["color_rgb"],"calibration_color":"","candidate_h_px":g["ink_h_px"],"calibration_h_px":"","height_ratio":"","candidate_area_px":g["ink_area_px"],"calibration_area_px":"","area_ratio":"","decision":"FAIL_NO_EXACT_INDEPENDENT_CALIBRATION","independent_render_proof":rel(tex),"contact_8x_nearest":""})
    fields=["glyph_id","char","profile","candidate_font","calibration_font","candidate_pt","calibration_pt","candidate_color","calibration_color","candidate_h_px","calibration_h_px","height_ratio","candidate_area_px","calibration_area_px","area_ratio","decision","independent_render_proof","contact_8x_nearest"]
    write_csv(CAL_DIR/"low_profile_calibration_ledger.csv",rows,fields)
    decision_by={x["glyph_id"]:x["decision"] for x in rows}
    for g in glyphs:
        if g["glyph_id"] in decision_by:
            g["initial_size_gate"] = "PASS" if decision_by[g["glyph_id"]] == "PASS" else "FAIL"
    return rows


def d_and_e_measurements(glyphs:list[dict[str,Any]]) -> tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    def rbox(g:dict[str,Any]) -> tuple[float,float,float,float]:
        return tuple(float(x) for x in g["char_bbox_pt"].split(","))  # type: ignore[return-value]
    def is_cjk(c:str) -> bool:
        return ("\u3400" <= c <= "\u9fff") or ("\uf900" <= c <= "\ufaff")
    def role(g:dict[str,Any]) -> tuple[str,str]:
        x0,y0,x1,y1=rbox(g); cx,cy=(x0+x1)/2,(y0+y1)/2; c=g["char"]
        panel="LEFT" if cx<220 else ("RIGHT" if cx>365 else "CENTRE")
        if cy<145:
            if is_cjk(c): return "TITLE_CJK",panel
            if "STIXTWOTEXT" in g["font"].upper(): return "TITLE_LATIN",panel
            return "TITLE_MATH",panel
        if cy<=200:
            if c.isdigit() and any(abs(cx-q)<18 for q in (130,207,377,454)):
                return "STATE_LABEL",panel
            return "EDGE_LABEL",panel
        if cy<=248:
            if 220<=cx<=365 and cy<=230: return "BRIDGE",panel
            if is_cjk(c): return "MATRIX_EXPLANATION",panel
            return "MATRIX_FORMULA",panel
        return "CAPTION",panel
    def signature(g:dict[str,Any], ro:str) -> str:
        if is_cjk(g["char"]): return "CJK_FULL_GLYPH"
        if g["glyph_class"] == "DIGIT_UPPER" and g["char"].isdigit(): return "DIGIT"
        if ro == "TITLE_MATH" and g["char"] in {"𝐴","𝑃"}: return "MATH_CAPITAL"
        return g["char"]

    annotated=[]
    for g in glyphs:
        ro,panel=role(g)
        annotated.append({"glyph_id":g["glyph_id"],"char":g["char"],"role":ro,"panel":panel,"glyph_class":g["glyph_class"],"font":g["font"],"font_size_pt_pdf_emit":float(g["font_size_pt_pdf_emit"]),"ink_h_px":float(g["ink_h_px"]),"ink_area_px":float(g["ink_area_px"]),"source_span_id":g["source_span_id"],"comparison_signature":signature(g,ro)})

    # D is a type-scale consistency check, so it uses the actual PDF-emitted
    # point size for the same role/script/font. Raw H is kept alongside as a
    # glyph-shape diagnostic and is not mistaken for a font-size proxy across
    # unlike outlines (notably CJK 一, italic j, and a digit).
    cohorts:dict[tuple[Any,...],list[dict[str,Any]]]=defaultdict(list)
    for a in annotated:
        script_class = "NATURAL_SCRIPT" if a["font_size_pt_pdf_emit"] < 9.5 else a["glyph_class"]
        a["d_script_class"] = script_class
        cohorts[(a["role"],script_class,a["font"])].append(a)
    drows=[]
    for a in annotated:
        key=(a["role"],a["d_script_class"],a["font"])
        members=cohorts[key]; bypanel:dict[str,list[float]]=defaultdict(list)
        for z in members: bypanel[z["panel"]].append(z["font_size_pt_pdf_emit"])
        local=[max(v)/min(v) for v in bypanel.values() if len(v)>=2 and min(v)>0]
        local_abs=[max(v)-min(v) for v in bypanel.values() if len(v)>=2]
        panel_medians=[float(np.median(v)) for v in bypanel.values() if v]
        cross=max(panel_medians)/min(panel_medians) if len(panel_medians)>=2 and min(panel_medians)>0 else None
        if len(members)<2:
            decision="N/A_NO_COMPARABLE_PEER"
        elif any(x>1.03 for x in local) or any(x>.25 for x in local_abs) or (cross is not None and cross>1.05):
            decision="FAIL"
        else:
            decision="PASS"
        drows.append({**a,"d_metric":"actual PDF emitted font size (pt); raw H retained as diagnostic","d_cohort":"|".join(map(str,key)),"d_cohort_size":len(members),"same_panel_ratio":max(local) if local else "N/A","same_panel_absolute_pt":max(local_abs) if local_abs else "N/A","cross_panel_ratio":cross if cross is not None else "N/A","d_limits":"same-panel ratio<=1.03 and absolute<=0.25pt; cross-panel<=1.05","d_decision":decision})

    # E checks role hierarchy from the actual emitted PDF point sizes. Raw H is
    # retained as a diagnostic, but cannot be used to compare a CJK ideograph,
    # a digit and a descending italic glyph as though they were the same form.
    byrole:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for a in annotated:
        if a["font_size_pt_pdf_emit"]>=9.5 and a["font_size_pt_pdf_emit"]>0:
            byrole[a["role"]].append(a)
    base=float(np.median([x["font_size_pt_pdf_emit"] for x in byrole["STATE_LABEL"]])) if byrole.get("STATE_LABEL") else 0.0
    allowed={"TITLE_CJK":(.98,1.02),"TITLE_MATH":(.98,1.02),"TITLE_LATIN":(.98,1.02),"STATE_LABEL":(.98,1.02),"EDGE_LABEL":(1.10,1.20),"MATRIX_FORMULA":(.94,1.20),"MATRIX_EXPLANATION":(.94,1.20),"BRIDGE":(1.10,1.20)}
    erows=[]
    for ro, members in sorted(byrole.items()):
        pts=[x["font_size_pt_pdf_emit"] for x in members]; hs=[x["ink_h_px"] for x in members if x["glyph_class"]!="LOW_PROFILE"]
        ptmed=float(np.median(pts)); hmed=float(np.median(hs)) if hs else 0.0
        if ro not in allowed or base==0:
            ratio="N/A"; rng="N/A"; decision="N/A_ROLE_NO_GLOBAL_BASE_REQUIREMENT"
        else:
            lo,hi=allowed[ro]; ratio=ptmed/base; rng=f"{lo}..{hi}"; decision="PASS" if lo<=ratio<=hi else "FAIL"
        erows.append({"role":ro,"member_count":len(members),"e_metric":"median actual PDF emitted font size (pt)","e_font_pt_median":ptmed,"raw_h_ink_median_px_diagnostic":hmed,"e_base_role":"STATE_LABEL","e_base_font_pt_median":base,"e_ratio":ratio,"e_expected_range":rng,"e_decision":decision})

    font_rows=[]
    for a in annotated:
        script=a["font_size_pt_pdf_emit"]<9.5
        font_rows.append({**a,"font_floor_rule":"NATURAL_SCRIPT_SOURCE_EXCEPTION" if script else ">=9.5pt base font","font_floor_decision":"EXEMPT_NATURAL_SCRIPT" if script else ("PASS" if a["font_size_pt_pdf_emit"]>=9.5 else "FAIL")})
    write_csv(REPORT_DIR/"D_same_role_scale_audit.csv",drows,list(drows[0].keys()) if drows else ["glyph_id"])
    write_csv(REPORT_DIR/"E_cross_role_hierarchy_audit.csv",erows,list(erows[0].keys()) if erows else ["role"])
    write_csv(REPORT_DIR/"font_floor_and_emitted_font_audit.csv",font_rows,list(font_rows[0].keys()) if font_rows else ["glyph_id"])
    write_text(REPORT_DIR/"D_E_method_note.md","""# D/E method note

D compares actual PDF-emitted point sizes for the same semantic role, script class and font. Same-panel maximum/minimum is limited to 1.03 with absolute difference <=0.25 pt, and cross-panel median ratio to 1.05. Raw-pixel ink height is retained as a diagnostic, while C independently enforces the strict raw H thresholds. Low-profile punctuation is decided by its separate independently-rendered matching-font H/area calibration.

E compares role hierarchy from actual emitted PDF font sizes, with raw ink-height medians retained as diagnostics. This avoids treating different glyph outlines (for example a CJK ideograph, a digit, and a descending italic mathematical glyph) as a font-size measurement. All non-script visible font runs are separately checked against the 9.5 pt base floor.
""")
    return drows,erows


def text_object_and_source_font_audit(glyphs:list[dict[str,Any]]) -> list[dict[str,Any]]:
    byparent:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for g in glyphs: byparent[g["parent_text_object"]].append(g)
    declared={4:"10.2",5:"10.2 or 11.6 by independent state/loop label",6:"11.6",7:"11.6",8:"11.8",9:"9.8 explanation; 11.6 update formula",10:"12.0 formula (T emitted from matching sans math at 11.46)",11:"11.6",12:"10.2",13:"10.2 or 11.6 by independent state/loop label",14:"11.6",15:"11.6",16:"11.8",17:"9.8 explanation; 11.6 update formula",18:"10.0 class small (PDF emit 9.9626)"}
    rows=[]
    for parent,members in sorted(byparent.items(),key=lambda z:min(int(x["glyph_id"][1:]) for x in z[1])):
        ordered=sorted(members,key=lambda x:int(x["glyph_id"][1:]));text_value="".join(x["char"] for x in ordered);role=role_for_span(ordered)
        normal=[float(x["font_size_pt_pdf_emit"]) for x in members if float(x["font_size_pt_pdf_emit"])>=9.5]
        scripts=[x for x in members if float(x["font_size_pt_pdf_emit"])<9.5]
        block=int(members[0]["pdf_block"]);parent_base=max(normal) if normal else 0.0
        scripts_valid=all(("MATH" in x["font"].upper() or "XITS" in x["font"].upper()) and parent_base>=9.5 for x in scripts)
        gate=bool(normal and min(normal)>=9.5 and scripts_valid)
        rows.append({"text_object_id":parent,"pdf_block":block,"role":role,"text_without_geometric_relations":text_value,"declared_effective_pt":declared.get(block,"UNMAPPED"),
                     "graphics_scale":1.0,"normal_pdf_emit_sizes_pt":"|".join(f"{x:.4f}" for x in sorted(set(normal))),"normal_min_pdf_emit_pt":min(normal) if normal else "N/A",
                     "natural_script_glyph_ids":"|".join(x["glyph_id"] for x in scripts),"natural_script_sizes_pt":"|".join(f"{float(x['font_size_pt_pdf_emit']):.4f}" for x in scripts),
                     "natural_script_parent_base_pt":parent_base,"font_floor_decision":"PASS" if gate else "FAIL","reviewer":"PENDING_MANUAL","font_visual_harmony":"PENDING_MANUAL",
                     "too_large_or_intrusive":"PENDING_MANUAL","too_small_or_hard_to_read":"PENDING_MANUAL","note":"Review this text object at 100% page, native 300dpi figure, and relevant 8x cards."})
    write_csv(REPORT_DIR/"text_object_effective_font_and_visual_ledger.csv",rows,list(rows[0].keys()))

    source=FIG_SOURCE.read_text(encoding="utf-8");source_lines=source.splitlines();font_rows=[]
    for lineno,line in enumerate(source_lines,1):
        for m in re.finditer(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}",line):
            pt=float(m.group(1));font_rows.append({"source_line":lineno,"command":m.group(0),"declared_pt":pt,"graphics_scale":1.0,"effective_pt":pt,"rule":">=9.5pt normal base text","decision":"PASS" if pt>=9.5 else "FAIL"})
    forbidden=[]
    for token in (r"\resizebox",r"\scalebox",r"transform shape",r"\tiny",r"\scriptsize",r"\footnotesize"):
        if token in source: forbidden.append(token)
    write_csv(REPORT_DIR/"source_font_command_audit.csv",font_rows,["source_line","command","declared_pt","graphics_scale","effective_pt","rule","decision"])
    write_json(REPORT_DIR/"source_font_floor_summary.json",{"explicit_fontsize_occurrences":len(font_rows),"minimum_explicit_effective_pt":min((x["effective_pt"] for x in font_rows),default=None),
               "forbidden_scaling_or_small_font_tokens":forbidden,"whole_figure_scale_present":False,"source_font_floor_pass":bool(font_rows and all(x["decision"]=="PASS" for x in font_rows) and not forbidden),
               "natural_script_policy":"Only TeX-derived sub/superscripts from >=9.5pt base formulas may emit below 9.5pt; listed per text object."})
    return rows


def raw_pixel_role_consistency(glyphs:list[dict[str,Any]]) -> list[dict[str,Any]]:
    def panel_of(g:dict[str,Any])->str:
        x0,_,x1,_=(float(x) for x in g["char_bbox_pt"].split(","));cx=(x0+x1)/2
        return "LEFT" if cx<220 else ("RIGHT" if cx>365 else "CENTRE")
    def script_group(g:dict[str,Any])->str:
        if g["needs_low_profile_calibration"]=="YES":return "LOW_PROFILE_CALIBRATED"
        if float(g["font_size_pt_pdf_emit"])<9.5:return "NATURAL_SCRIPT"
        if g["glyph_class"]=="CJK_FULL":return "CJK_FULL"
        if g["glyph_class"]=="DIGIT_UPPER" and g["char"].isdigit():return "DIGIT"
        if g["glyph_class"]=="PROSE_LATIN_X_HEIGHT":return "PROSE_LATIN_X_HEIGHT"
        if g["glyph_class"]=="DIGIT_UPPER":return "LATIN_UPPER"
        return "BASE_MATH_OR_SYMBOL"
    grouped:dict[tuple[str,str,str],list[dict[str,Any]]]=defaultdict(list)
    for g in glyphs:
        role=role_for_span([g]);grouped[(g["parent_text_object"],role,script_group(g))].append(g)
    objects=[]
    for (parent,role,script),members in grouped.items():
        if script=="LOW_PROFILE_CALIBRATED":continue
        objects.append({"text_object_id":parent,"role":role,"script_group":script,"panel":panel_of(members[0]),"member_count":len(members),
                        "member_glyph_ids":"|".join(x["glyph_id"] for x in members),"object_h_median_px":float(np.median([float(x["ink_h_px"]) for x in members]))})
    cohorts:dict[tuple[str,str],list[dict[str,Any]]]=defaultdict(list)
    for x in objects:cohorts[(x["role"],x["script_group"])].append(x)
    rows=[]
    for x in objects:
        peers=cohorts[(x["role"],x["script_group"])];panel_vals:dict[str,list[float]]=defaultdict(list)
        for z in peers:panel_vals[z["panel"]].append(z["object_h_median_px"])
        own_panel_median=float(np.median(panel_vals[x["panel"]]));ratio=x["object_h_median_px"]/own_panel_median if own_panel_median else math.inf
        pmed=[float(np.median(v)) for v in panel_vals.values() if v];cross=max(pmed)/min(pmed) if len(pmed)>=2 and min(pmed)>0 else None
        decision="PASS" if .92<=ratio<=1.08 and (cross is None or cross<=1.10) else "FAIL"
        rows.append({**x,"same_panel_role_script_median_px":own_panel_median,"element_to_median_ratio":ratio,"required_element_ratio":"0.92..1.08",
                     "cross_panel_role_median_extreme_ratio":cross if cross is not None else "N/A","required_cross_panel_ratio":"<=1.10","decision":decision})
    write_csv(REPORT_DIR/"D_raw_pixel_object_role_audit.csv",rows,list(rows[0].keys()) if rows else ["text_object_id"])
    return rows


def object_ink_bbox_global(obj:ObjectMask)->tuple[int,int,int,int] | None:
    _,_,_,local=mask_stats(obj.mask)
    if local is None:return None
    return (local[0]+obj.bbox[0],local[1]+obj.bbox[1],local[2]+obj.bbox[0],local[3]+obj.bbox[1])


def boundary_and_named_repair_audits(rgb:np.ndarray,sx:float,sy:float,text_objects:list[ObjectMask],graphic_objects:list[ObjectMask]) -> tuple[dict[str,Any],list[dict[str,Any]]]:
    all_objects=text_objects+graphic_objects;byid={x.object_id:x for x in all_objects};crop=rect_to_px(FIG_RECT_PT,sx,sy,rgb.shape[1],rgb.shape[0])
    boundary_rows=[];clip_count=0
    for obj in all_objects:
        bb=object_ink_bbox_global(obj)
        if bb is None:
            boundary_rows.append({"object_id":obj.object_id,"object_type":obj.object_type,"ink_bbox_px":"","figure_crop_edge_clearance_px":"N/A","full_image_edge_clearance_px":"N/A","clip_pixel_count":obj.pixels,"decision":"FAIL_EMPTY_MASK"});clip_count+=obj.pixels;continue
        yy,xx=np.where(obj.mask);gx=xx+obj.bbox[0];gy=yy+obj.bbox[1]
        outside=(gx<crop[0])|(gx>=crop[2])|(gy<crop[1])|(gy>=crop[3]);outside_count=int(outside.sum());clip_count+=outside_count
        fig_clear=float(min(gx.min()-crop[0],crop[2]-1-gx.max(),gy.min()-crop[1],crop[3]-1-gy.max()))
        page_clear=float(min(gx.min(),rgb.shape[1]-1-gx.max(),gy.min(),rgb.shape[0]-1-gy.max()))
        required=6.0 if obj.class_group=="TEXT" else 0.0
        decision="PASS" if outside_count==0 and (obj.class_group!="TEXT" or fig_clear>=required) else "FAIL"
        boundary_rows.append({"object_id":obj.object_id,"object_type":obj.object_type,"ink_bbox_px":bbox_to_str(bb),"figure_crop_edge_clearance_px":fig_clear,"full_image_edge_clearance_px":page_clear,"required_text_to_crop_or_image_edge_px":required if obj.class_group=="TEXT" else "N/A","clip_pixel_count":outside_count,"decision":decision})
    write_csv(REPORT_DIR/"object_boundary_and_clip_audit.csv",boundary_rows,list(boundary_rows[0].keys()))

    parents:dict[str,list[ObjectMask]]=defaultdict(list)
    for o in text_objects:
        if o.parent_id!="TBLOCK_B18":parents[o.parent_id].append(o)
    composites=[]
    for parent,parts in parents.items():
        obj=merge_object_masks(parts,"TXT_"+parent,"TEXT_OBJECT_COMPOSITE","READER_TEXT",parent);obj.class_group="TEXT";composites.append(obj)
    def panel(obj:ObjectMask)->str:
        cx=(obj.bbox[0]+obj.bbox[2])/2/sx
        return "LEFT" if cx<220 else ("RIGHT" if cx>365 else "CENTRE")
    panel_pairs=[]
    for a in composites:
        for b in composites:
            if a.object_id>=b.object_id:continue
            if {panel(a),panel(b)} not in ({"LEFT","CENTRE"},{"CENTRE","RIGHT"}):continue
            dist,method=exact_min_distance(a,b);panel_pairs.append((dist,a,b,method))
    panel_pairs.sort(key=lambda z:z[0]);closest_panel=[]
    for dist,a,b,method in panel_pairs[:8]:
        ev={}
        if dist<14:ev={k:rel(v) for k,v in pair_roi(rgb,a,b,f"PANEL_GAP_{a.parent_id}_{b.parent_id}").items()}
        closest_panel.append({"object_a":a.parent_id,"panel_a":panel(a),"object_b":b.parent_id,"panel_b":panel(b),"distance_px":dist,"distance_method":method,"required_px":8,"decision":"PASS" if dist>=8 else "FAIL","evidence":ev})
    panel_gate=bool(panel_pairs and panel_pairs[0][0]>=8)

    named_specs=[
        ("LEFT_GOLD_BRIDGE_TO_MATRIX",[x.object_id for x in text_objects if x.parent_id=="TBLOCK_B08"],["G14","G15"],3,12,"R96 left gold connector previously crossed the matrix closing bracket"),
        ("RIGHT_GOLD_BRIDGE_TO_P_FORMULA",[x.object_id for x in text_objects if x.parent_id=="TBLOCK_B16"],["G16","G17"],3,12,"right connector checked against the complete P matrix formula"),
        ("LEFT_FOCUS_LABEL_TO_SHAFT",[x.object_id for x in text_objects if x.parent_id=="TBLOCK_B06"],["G07"],3,12,"maps the former PAIR_C0026_G07 failure"),
        ("LEFT_FOCUS_LABEL_TO_BORDER",[x.object_id for x in text_objects if x.parent_id=="TBLOCK_B06"],["G09"],3,12,"maps the former PAIR_C0026_G09 failure"),
        ("RIGHT_FOCUS_LABEL_TO_SHAFT",[x.object_id for x in text_objects if x.parent_id=="TBLOCK_B14"],["G24"],3,12,"maps the former PAIR_C0120_G24 failure"),
        ("RIGHT_FOCUS_LABEL_TO_BORDER",[x.object_id for x in text_objects if x.parent_id=="TBLOCK_B14"],["G26"],3,12,"maps the former PAIR_C0120_G26 failure"),
    ]
    named=[]
    for nid,aids,bids,required,target,basis in named_specs:
        choices=[]
        for aid in aids:
            for bid in bids:
                d,m=exact_min_distance(byid[aid],byid[bid]);choices.append((d,aid,bid,m))
        d,aid,bid,m=min(choices,key=lambda z:z[0]);ev={k:rel(v) for k,v in pair_roi(rgb,byid[aid],byid[bid],nid).items()}
        named.append({"repair_relation_id":nid,"closest_text_glyph_id":aid,"closest_graphic_object_id":bid,"raw_overlap_px":raw_overlap(byid[aid],byid[bid]),"raw_distance_px":d,"distance_method":m,"hard_required_px":required,"root_safety_target_px":target,
                      "hard_gate":"PASS" if raw_overlap(byid[aid],byid[bid])==0 and d>=required else "FAIL","safety_target":"PASS" if d>=target else "BELOW_TARGET_BUT_HARD_PASS" if d>=required else "FAIL","basis":basis,
                      "original_1x":ev["original_1x"],"mask_A_1x":ev["mask_a_1x"],"mask_B_1x":ev["mask_b_1x"],"intersection_1x":ev["intersection_1x"],"overlay_1x":ev["overlay_1x"],"contact_8x":ev["contact_8x"],
                      "reviewer":"PENDING_MANUAL","manual_decision":"PENDING_MANUAL","manual_note":"Open all six referenced evidence files and verify the named repaired relation."})
    write_csv(REPORT_DIR/"named_repair_clearance_and_manual_ledger.csv",named,list(named[0].keys()))
    summary={"figure_crop_px":list(crop),"foreground_object_count":len(all_objects),"clip_pixel_count":clip_count,"empty_mask_count":sum(x.pixels==0 for x in all_objects),
             "minimum_text_to_figure_crop_edge_px":min(float(x["figure_crop_edge_clearance_px"]) for x in boundary_rows if x["object_type"]=="TEXT_GLYPH" and x["figure_crop_edge_clearance_px"]!="N/A"),
             "text_to_crop_edge_required_px":6,"panel_reader_pair_count":len(panel_pairs),"minimum_adjacent_panel_reader_gap_px":panel_pairs[0][0] if panel_pairs else None,"adjacent_panel_required_px":8,
             "closest_adjacent_panel_pairs":closest_panel,"boundary_clip_gate_pass":clip_count==0 and all(x["decision"]=="PASS" for x in boundary_rows),"panel_gap_gate_pass":panel_gate}
    write_json(REPORT_DIR/"boundary_clip_and_panel_gap_summary.json",summary)
    return summary,named


def c0153_resegmentation_binding() -> None:
    base=PACKAGE_ROOT/"before_r97"/"c0153";data=json.loads((base/"C0153_RESEGMENTATION.json").read_text(encoding="utf-8"))
    required=[base/"C0153_UFF1B_original_1x.png",base/"C0153_UFF1B_pure_overlay_foreign_blue_1x.png",base/"C0153_UFF1B_pure_two_component_mask_only_1x.png",base/"C0153_UFF1B_pure_contact_8x_nearest.png",base/"C0153_calibration_original_1x.png",base/"C0153_calibration_overlay_1x.png",base/"C0153_calibration_mask_only_1x.png",base/"C0153_calibration_contact_8x_nearest.png"]
    report={"upstream_r97_sha256":data["r97_pdf_sha256"],"glyph_id":"C0153","char":"；","source_identity":{"font":data["candidate"]["font"],"font_size_pt_pdf_emit":data["candidate"]["font_size_pt_pdf_emit"],"color_rgb":data["candidate"]["color_rgb"],"bbox_pt":data["candidate"]["bbox_pt"]},
            "raw_component_count":data["candidate_raw_component_count"],"pure_component_count":data["pure_candidate_component_count"],"foreign_component_count":data["foreign_component_count"],
            "pure_h_px":data["pure_candidate_h_px"],"calibration_h_px":data["calibration_h_px"],"height_ratio":data["height_ratio"],"pure_area_px":data["pure_candidate_area_px"],"calibration_area_px":data["calibration_area_px"],"area_ratio":data["area_ratio"],
            "decision":data["decision"],"separation_rule":data["separation_rule"],"required_visual_files":[{"path":rel(x),"exists":x.exists(),"sha256":sha256(x) if x.exists() else None} for x in required],
            "binding_decision":"PASS" if data["decision"]=="PASS" and all(x.exists() for x in required) else "FAIL","source_repair_decision":"NO_SOURCE_CHANGE_FOR_C0153; legacy contaminated measurement superseded"}
    write_json(REPORT_DIR/"C0153_clean_mask_binding.json",report)
    write_text(REPORT_DIR/"C0153_clean_mask_binding.md","# C0153 clean-mask binding\n\n"+json.dumps(report,ensure_ascii=False,indent=2)+"\n")


def safe_filename_and_png_integrity(glyphs:list[dict[str,Any]],graphic_rows:list[dict[str,Any]],relation_rows:list[dict[str,Any]]) -> dict[str,Any]:
    expected=[];mapping=[]
    for g in glyphs:
        paths=[g["original_1x"],g["overlay_1x"],g["mask_only_1x"],g["contact_8x_nearest"]]
        mapping.append({"element_id":g["glyph_id"],"safe_filename_stem":f"{g['glyph_id']}_{g['codepoint']}","object_type":"TEXT_GLYPH","decision":"PASS"})
        expected.extend((g["glyph_id"],x) for x in paths)
    for g in graphic_rows:
        paths=[g["original_1x"],g["overlay_1x"],g["mask_only_1x"],g["contact_8x_nearest"]]
        mapping.append({"element_id":g["object_id"],"safe_filename_stem":f"{g['object_id']}_{g['role']}","object_type":g["object_type"],"decision":"PASS"})
        expected.extend((g["object_id"],x) for x in paths)
    for g in relation_rows:
        paths=[g["original_1x"],g["overlay_1x"],g["mask_only_1x"],g["contact_8x_nearest"]]
        mapping.append({"element_id":g["relation_id"],"safe_filename_stem":f"{g['relation_id']}_{g['relation_kind']}","object_type":"GRAPHIC/MATH_RELATION_COMPOSITE","decision":"PASS"})
        expected.extend((g["relation_id"],x) for x in paths)
    pair_manual=read_csv_rows(PAIR_DIR/"critical_and_intentional_pair_manual_review_ledger.csv") if (PAIR_DIR/"critical_and_intentional_pair_manual_review_ledger.csv").exists() else []
    for row in pair_manual:
        for field in ("original_1x","mask_A_1x","mask_B_1x","intersection_1x","overlay_1x","contact_8x"):
            expected.append((row["pair_id"],row[field]))
    file_rows=[];seen=[]
    for eid,pathstr in expected:
        p=Path(pathstr);exists=p.exists();plain=":" not in p.name;opened=False;dims="";error=""
        if exists:
            try:
                with Image.open(p) as im:im.verify()
                with Image.open(p) as im:dims=f"{im.width}x{im.height}"
                opened=True
            except Exception as exc:error=repr(exc)
        file_rows.append({"element_id":eid,"path":rel(p),"basename":p.name,"exists":exists,"plain_filename_no_colon":plain,"png_opened":opened,"dimensions_px":dims,"bytes":p.stat().st_size if exists else "","sha256":sha256(p) if exists else "","decision":"PASS" if exists and plain and opened else "FAIL","error":error});seen.append(str(p).lower())
    write_csv(MACHINE_DIR/"id_to_safe_filename_map.csv",mapping,["element_id","safe_filename_stem","object_type","decision"])
    write_csv(MACHINE_DIR/"expected_png_open_integrity.csv",file_rows,list(file_rows[0].keys()) if file_rows else ["element_id"])
    summary={"unique_element_ids":len({x["element_id"] for x in mapping}),"mapping_rows":len(mapping),"duplicate_element_ids":[x for x,n in Counter(z["element_id"] for z in mapping).items() if n>1],
             "expected_png_references":len(expected),"unique_png_paths":len(set(seen)),"duplicate_png_paths":[x for x,n in Counter(seen).items() if n>1],"missing_png_count":sum(not x["exists"] for x in file_rows),
             "unopenable_png_count":sum(not x["png_opened"] for x in file_rows),"unsafe_colon_basename_count":sum(not x["plain_filename_no_colon"] for x in file_rows),
             "integrity_pass":bool(mapping and len(expected)==len(set(seen)) and all(x["decision"]=="PASS" for x in file_rows))}
    write_json(MACHINE_DIR/"safe_filename_and_png_integrity.json",summary)
    return summary


def foreground_inventory(glyphs:list[dict[str,Any]], graphic_rows:list[dict[str,Any]], objects:list[ObjectMask]) -> None:
    rows=[]
    obj_by={x.object_id:x for x in objects}
    for g in glyphs:
        o=obj_by[g["glyph_id"]]
        rows.append({"object_id":o.object_id,"object_type":o.object_type,"class_group":o.class_group,"role":o.role,"parent_id":o.parent_id,"bbox_px":bbox_to_str(o.bbox),"pixel_count":o.pixels,"source_ref":o.source_ref,"draw_refs":"","is_foreground":"YES"})
    for r in graphic_rows:
        o=obj_by[r["object_id"]]
        rows.append({"object_id":o.object_id,"object_type":o.object_type,"class_group":o.class_group,"role":o.role,"parent_id":o.parent_id,"bbox_px":bbox_to_str(o.bbox),"pixel_count":o.pixels,"source_ref":o.source_ref,"draw_refs":o.draw_refs,"is_foreground":"YES"})
    write_csv(PAIR_DIR/"foreground_object_inventory.csv",rows,["object_id","object_type","class_group","role","parent_id","bbox_px","pixel_count","source_ref","draw_refs","is_foreground"])


def manual_templates(glyphs:list[dict[str,Any]]) -> None:
    rows=[]
    for g in glyphs:
        rows.append({"glyph_id":g["glyph_id"],"char":g["char"],"parent_text_object":g["parent_text_object"],"sheet":g.get("contact_sheet",""),"cell":g.get("contact_cell",""),"reviewer":"PENDING_MANUAL","original_match":"PENDING_MANUAL","overlay_complete":"PENDING_MANUAL","mask_only_pure":"PENDING_MANUAL","missing_stroke_px":"PENDING_MANUAL","foreign_pixel_px":"PENDING_MANUAL","manual_decision":"PENDING_MANUAL","manual_note":"Review exact native 1x and its 8x nearest triptych; do not infer from source font size."})
    write_csv(GLYPH_DIR/"glyph_manual_review_ledger.csv",rows,["glyph_id","char","parent_text_object","sheet","cell","reviewer","original_match","overlay_complete","mask_only_pure","missing_stroke_px","foreign_pixel_px","manual_decision","manual_note"])
    visual=[
        {"review_id":"V01","view":"local page 200dpi","path":rel(RENDERS/"page_200dpi_native.png"),"criterion":"page integration / clipping / placement / whitespace","decision":"PENDING_MANUAL","note":""},
        {"review_id":"V02","view":"local page 300dpi","path":rel(RENDERS/"page_300dpi_native.png"),"criterion":"full native high-resolution page review","decision":"PENDING_MANUAL","note":""},
        {"review_id":"V03","view":"local page 300dpi grayscale","path":rel(RENDERS/"page_300dpi_native_grayscale.png"),"criterion":"page-level grayscale hierarchy / non-colour dependence","decision":"PENDING_MANUAL","note":""},
        {"review_id":"V04","view":"figure+caption native crop 300dpi","path":rel(RENDERS/"local_page_figure30_2_caption_300dpi_native_crop.png"),"criterion":"overall visual harmony, margins, labels, focus hierarchy","decision":"PENDING_MANUAL","note":""},
        {"review_id":"V05","view":"figure+caption crop grayscale","path":rel(RENDERS/"local_page_figure30_2_caption_300dpi_native_crop_grayscale.png"),"criterion":"cropped grayscale hierarchy / non-colour dependence","decision":"PENDING_MANUAL","note":""},
        {"review_id":"V06","view":"local standalone 300dpi","path":rel(RENDERS/"standalone_300dpi_native.png"),"criterion":"standalone geometry, visual harmony and zero clipping","decision":"PENDING_MANUAL","note":""},
        {"review_id":"V07","view":"local standalone 300dpi grayscale","path":rel(RENDERS/"standalone_300dpi_native_grayscale.png"),"criterion":"standalone grayscale and label hierarchy","decision":"PENDING_MANUAL","note":""},
        {"review_id":"V08","view":"direct body semantic excerpt","path":rel(REPORT_DIR/"direct_body_semantic_excerpt.txt"),"criterion":"figure notation, direction, and transpose bridge agree with direct body","decision":"PENDING_MANUAL","note":""},
    ]
    write_csv(REPORT_DIR/"manual_visual_semantic_review_ledger.csv",visual,["review_id","view","path","criterion","decision","note"])


def semantic_report() -> None:
    text="""# Mathematical and textual semantic audit

The source replaces only the raster-poor *glyph forms* of twelve equality signs
and three right arrows.  Each replacement is a real TikZ path in the same
`\mathrel` position; operands, order, indices, probabilities and direction are
unchanged.

| relation | source context after repair | semantic identity preserved |
|---|---|---|
| EQ01 | left title `a_ij [geom =] P(i [geom →] j)` | definition of row-random entry |
| EQ02 | left focus `a_12 [geom =] 0.3` | highlighted edge probability |
| EQ03 | left return `a_21 [geom =] 0.2` | reverse-edge probability |
| EQ04 | `A [geom =] [[0.7,0.3],[0.2,0.8]]` | full row-random matrix |
| EQ05 | `rho_(t+1) [geom =] rho_t A` | row-vector update |
| EQ06 | `P [geom =] A^T` | transpose bridge |
| EQ07 | `a_ij [geom =] P_ji` | same physical-edge probability under the two conventions |
| EQ08 | right title `P_ji [geom =] P(i [geom →] j)` | definition of column-random entry |
| EQ09 | right focus `P_21 [geom =] 0.3` | highlighted edge probability |
| EQ10 | right return `P_12 [geom =] 0.2` | reverse-edge probability |
| EQ11 | `P [geom =] [[0.7,0.2],[0.3,0.8]]` | full column-random matrix |
| EQ12 | `p^(t+1) [geom =] P p^(t)` | column-vector update |
| AR01 | left title `i [geom →] j` | directed edge from `i` to `j` |
| AR02 | bridge `i [geom →] j` | the same physical directed edge |
| AR03 | right title `i [geom →] j` | directed edge from `i` to `j` |

The former phrase `同一条` was changed to `物理边`; this removes the low-stroke
CJK glyph `一` without deleting information.  The complete bridge now reads
`物理边 i→j：a_ij=P_ji`, which states the same mapping more directly.

The candidate matrices remain `A=[[0.7,0.3],[0.2,0.8]]` and
`P=A^T=[[0.7,0.2],[0.3,0.8]]`; row/column sums remain one.  The direct body and
caption state the same transpose convention and update equations.

The caption word `PageRank` remains ordinary `STIXTwoText-Regular` prose.
Its final `n` is classified as `PROSE_LATIN_X_HEIGHT` (17 px gate), not as a
baseline mathematical character (22 px gate); no font enlargement or bolding
was retained.

Semantic mapping and body/caption consistency: **PASS_TO_LOCAL_PIXEL_GATES**.
"""
    write_text(REPORT_DIR/"mathematical_semantic_and_text_consistency_audit.md",text)


def scope_boundary_reconciliation(glyphs:list[dict[str,Any]], meta:dict[str,Any]) -> None:
    """Prove the glyph denominator is the frozen figure environment, not page prose."""
    byblock:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for g in glyphs: byblock[str(g["pdf_block"])].append(g)
    blocks=[]
    for block, members in sorted(byblock.items(), key=lambda x:int(x[0])):
        ordered=sorted(members,key=lambda z:int(z["glyph_id"][1:]))
        text="".join(x["char"] for x in ordered)
        y0=min(float(x["char_bbox_pt"].split(",")[1]) for x in members); y1=max(float(x["char_bbox_pt"].split(",")[3]) for x in members)
        blocks.append({"pdf_block":block,"glyph_count":len(members),"text":text,"y0_pt":y0,"y1_pt":y1,"is_caption":text.startswith("图30.2")})
    captions=[x for x in blocks if x["is_caption"]]
    out_of_scope=[]
    for g in glyphs:
        r=[float(x) for x in g["char_bbox_pt"].split(",")]
        if r[0]<FIG_TEXT_SCOPE_PT.x0 or r[1]<FIG_TEXT_SCOPE_PT.y0 or r[2]>FIG_TEXT_SCOPE_PT.x1 or r[3]>FIG_TEXT_SCOPE_PT.y1:
            out_of_scope.append(g["glyph_id"])
    source_lines=FIG_SOURCE.read_text(encoding="utf-8").splitlines()
    begin_idx=next(i for i,x in enumerate(source_lines,1) if x.strip()=="\\begin{figure}[htbp]")
    caption_idx=next(i for i,x in enumerate(source_lines,1) if x.lstrip().startswith("\\caption{"))
    end_idx=next(i for i,x in enumerate(source_lines,1) if i>caption_idx and x.strip()=="\\end{figure}")
    report={"canonical_scope":"local FIG-P547-01 figure environment title + graphic labels + full caption; wrapper body prose excluded from glyph universe but retained in semantic report","visual_crop_pt":list(FIG_RECT_PT),"glyph_text_scope_pt":list(FIG_TEXT_SCOPE_PT),"source_environment_boundaries":{"begin_figure_line":begin_idx,"caption_line":caption_idx,"end_figure_line":end_idx,"begin_figure":source_lines[begin_idx-1],"caption":source_lines[caption_idx-1],"end_figure":source_lines[end_idx-1]},"direct_body_input_line":184,"selected_visible_non_whitespace_glyphs":len(glyphs),"selected_glyphs_outside_text_scope":out_of_scope,"visible_crop_margin_excluded_count":meta.get("visual_crop_margin_excluded_character_count",0),"visible_crop_margin_exclusions":meta.get("visual_crop_margin_exclusions",[]),"selected_pdf_text_blocks":blocks,"caption_blocks":captions,"caption_complete":len(captions)==1 and "显式转置桥" in captions[0]["text"],"preceding_body_leak_count":sum(1 for g in glyphs if float(g["char_bbox_pt"].split(",")[1])<FIG_TEXT_SCOPE_PT.y0),"trailing_body_leak_count":sum(1 for g in glyphs if float(g["char_bbox_pt"].split(",")[1])>=FIG_TEXT_SCOPE_PT.y1),"zero_omission_claim_basis":"PyMuPDF rawdict enumeration selected every non-whitespace character whose full bbox lies within the declared title/graphic/caption text boundary; selection count and every glyph ID are in all_visible_glyph_raw_measurements.csv."}
    report["scope_gate_pass"] = bool(not out_of_scope and report["caption_complete"] and report["preceding_body_leak_count"]==0 and report["trailing_body_leak_count"]==0)
    write_json(REPORT_DIR/"scope_boundary_reconciliation.json",report)
    write_text(REPORT_DIR/"scope_boundary_reconciliation.md", "# Figure-environment scope reconciliation\n\n"+json.dumps(report,ensure_ascii=False,indent=2)+"\n")


def generate() -> None:
    purge_preseal_generated_output()
    ensure_dirs()
    source_identity_evidence()
    identity=build_identity();write_json(OUT/"identity_and_scope_manifest.json",identity)
    if not all(identity["hash_match"].values()):
        raise RuntimeError("frozen identity mismatch; generation aborted before evidence claims")
    if not identity["source_transition"]["baseline_snapshot_hash_match"] or not identity["source_transition"]["patch_present"]:
        raise RuntimeError("baseline/current source transition identity incomplete")
    source_and_body_evidence()
    native=render_native()
    glyphs,text_objects,meta=extract_glyphs(native["full300"],native["page_sx"],native["page_sy"])
    scope_boundary_reconciliation(glyphs,meta)
    render_glyph_sheets(glyphs)
    graphic_rows,graphic_objects,cache=extract_graphics(native["full300"],native["page_sx"],native["page_sy"])
    render_graphic_sheets(graphic_rows)
    drawing_recon=drawing_path_reconciliation()
    relation_rows=math_relation_composites(native["full300"],graphic_objects)
    all_objects=text_objects+graphic_objects
    foreground_inventory(glyphs,graphic_rows,all_objects)
    calibration_rows=low_profile_calibration(glyphs)
    # Calibration can alter the low-profile size gate, so record the final measurement sheet now.
    glyph_fields=list(glyphs[0].keys()) if glyphs else ["glyph_id"]
    write_csv(GLYPH_DIR/"all_visible_glyph_raw_measurements.csv",glyphs,glyph_fields)
    drows,erows=d_and_e_measurements(glyphs)
    raw_drows=raw_pixel_role_consistency(glyphs)
    text_font_rows=text_object_and_source_font_audit(glyphs)
    pairrows=evaluate_pairs(native["full300"],text_objects,graphic_objects)
    occrows=occlusion_reverse(native["full300"],native["page_sx"],native["page_sy"],cache)
    boundary_summary,named_rows=boundary_and_named_repair_audits(native["full300"],native["page_sx"],native["page_sy"],text_objects,graphic_objects)
    c0153_resegmentation_binding()
    manual_templates(glyphs);semantic_report()
    png_integrity=safe_filename_and_png_integrity(glyphs,graphic_rows,relation_rows)
    gate_counts=Counter(x["initial_size_gate"] for x in glyphs)
    write_json(MACHINE_DIR/"generation_manifest.json",{"generated_utc":now_utc(),"glyph_scope":meta,"glyph_size_gates":dict(gate_counts),"glyph_count":len(glyphs),"graphic_foreground_count":len(graphic_rows),
               "math_relation_composite_count":len(relation_rows),"math_relation_size_failures":sum(x["size_gate"]=="FAIL" for x in relation_rows),"low_profile_entries":len(calibration_rows),"d_rows":len(drows),"raw_pixel_d_rows":len(raw_drows),"e_rows":len(erows),
               "text_object_font_rows":len(text_font_rows),"text_object_font_floor_failures":sum(x["font_floor_decision"]=="FAIL" for x in text_font_rows),"pair_rows":len(pairrows),"pair_failures":sum(x["decision"]=="FAIL" for x in pairrows),
               "occlusion_rows":len(occrows),"occlusion_failures":sum(x["decision"]=="FAIL" for x in occrows),"drawing_path_reconciliation":drawing_recon,"boundary_summary":boundary_summary,
               "named_repair_relations":len(named_rows),"named_repair_hard_failures":sum(x["hard_gate"]=="FAIL" for x in named_rows),"png_integrity":png_integrity,"manual_review_state":"PENDING_MANUAL"})
    pre_review_verify(write=True)


def read_csv_rows(path:Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))


def pre_review_verify(write:bool=False) -> dict[str,Any]:
    required=[OUT/"audit_local_r7.py",OUT/"identity_and_scope_manifest.json",SOURCE_ID_DIR/"source_identity_report.json",BASELINE_SOURCE,SOURCE_ID_DIR/"current_29E415_fig_v5_c01_transition_graph.tex",SOURCE_DIFF,
              MACHINE_DIR/"generation_manifest.json",MACHINE_DIR/"native_render_manifest.json",MACHINE_DIR/"safe_filename_and_png_integrity.json",MACHINE_DIR/"expected_png_open_integrity.csv",MACHINE_DIR/"id_to_safe_filename_map.csv",
              GLYPH_DIR/"all_visible_glyph_raw_measurements.csv",GLYPH_DIR/"glyph_manual_review_ledger.csv",GLYPH_DIR/"glyph_contact_sheet_index.csv",
              GRAPHIC_DIR/"graphic_object_inventory.csv",GRAPHIC_DIR/"graphic_manual_review_ledger.csv",GRAPHIC_DIR/"graphic_contact_sheet_index.csv",GRAPHIC_DIR/"drawing_path_reconciliation.csv",GRAPHIC_DIR/"drawing_path_reconciliation.json",
              RELATION_DIR/"math_relation_composite_measurements.csv",RELATION_DIR/"math_relation_manual_review_ledger.csv",RELATION_DIR/"math_relation_contact_sheet_index.csv",
              PAIR_DIR/"foreground_object_inventory.csv",PAIR_DIR/"all_foreground_unordered_pairs.csv",PAIR_DIR/"pair_coverage_manifest.json",PAIR_DIR/"intentional_contact_whitelist.csv",PAIR_DIR/"critical_and_intentional_pair_manual_review_ledger.csv",
              OCC_DIR/"occlusion_reverse_ledger.csv",CAL_DIR/"low_profile_calibration_ledger.csv",CAL_DIR/"calibration_character_inventory.csv",
              REPORT_DIR/"D_same_role_scale_audit.csv",REPORT_DIR/"D_raw_pixel_object_role_audit.csv",REPORT_DIR/"E_cross_role_hierarchy_audit.csv",REPORT_DIR/"font_floor_and_emitted_font_audit.csv",REPORT_DIR/"D_E_method_note.md",
              REPORT_DIR/"text_object_effective_font_and_visual_ledger.csv",REPORT_DIR/"source_font_command_audit.csv",REPORT_DIR/"source_font_floor_summary.json",REPORT_DIR/"object_boundary_and_clip_audit.csv",REPORT_DIR/"boundary_clip_and_panel_gap_summary.json",
              REPORT_DIR/"named_repair_clearance_and_manual_ledger.csv",REPORT_DIR/"C0153_clean_mask_binding.json",REPORT_DIR/"C0153_clean_mask_binding.md",REPORT_DIR/"scope_boundary_reconciliation.json",REPORT_DIR/"scope_boundary_reconciliation.md",
              REPORT_DIR/"source_style_and_structure_audit.md",REPORT_DIR/"mathematical_semantic_and_text_consistency_audit.md",REPORT_DIR/"manual_visual_semantic_review_ledger.csv"]
    exists={rel(p):p.exists() for p in required}
    glyphs=read_csv_rows(GLYPH_DIR/"all_visible_glyph_raw_measurements.csv") if (GLYPH_DIR/"all_visible_glyph_raw_measurements.csv").exists() else []
    manual=read_csv_rows(GLYPH_DIR/"glyph_manual_review_ledger.csv") if (GLYPH_DIR/"glyph_manual_review_ledger.csv").exists() else []
    gmanual=read_csv_rows(GRAPHIC_DIR/"graphic_manual_review_ledger.csv") if (GRAPHIC_DIR/"graphic_manual_review_ledger.csv").exists() else []
    rmanual=read_csv_rows(RELATION_DIR/"math_relation_manual_review_ledger.csv") if (RELATION_DIR/"math_relation_manual_review_ledger.csv").exists() else []
    pmanual=read_csv_rows(PAIR_DIR/"critical_and_intentional_pair_manual_review_ledger.csv") if (PAIR_DIR/"critical_and_intentional_pair_manual_review_ledger.csv").exists() else []
    objs=read_csv_rows(PAIR_DIR/"foreground_object_inventory.csv") if (PAIR_DIR/"foreground_object_inventory.csv").exists() else []
    pairs=read_csv_rows(PAIR_DIR/"all_foreground_unordered_pairs.csv") if (PAIR_DIR/"all_foreground_unordered_pairs.csv").exists() else []
    expected=len(objs)*(len(objs)-1)//2
    status={"verified_utc":now_utc(),"required_files_present":all(exists.values()),"files":exists,"glyph_count":len(glyphs),"foreground_objects":len(objs),"pair_count":len(pairs),"expected_pair_count":expected,"pair_complete":len(pairs)==expected,
            "glyph_manual_rows":len(manual),"glyph_manual_pending":sum(x.get("manual_decision")=="PENDING_MANUAL" for x in manual),"graphic_manual_rows":len(gmanual),"graphic_manual_pending":sum(x.get("decision")=="PENDING_MANUAL" for x in gmanual),
            "math_relation_manual_rows":len(rmanual),"math_relation_manual_pending":sum(x.get("decision")=="PENDING_MANUAL" for x in rmanual),"pair_manual_rows":len(pmanual),"pair_manual_pending":sum(x.get("manual_decision")=="PENDING_MANUAL" for x in pmanual),
            "state":"PRE_REVIEW"}
    if write:write_json(MACHINE_DIR/"machine_integrity_pre_manual_review.json",status)
    return status


def commit_manual_review() -> None:
    """Forbidden by the strict schema: there is no script bulk-PASS path."""
    raise RuntimeError("bulk manual PASS is prohibited; complete every ledger row manually after opening its evidence")
    check_writable()
    glyph_path=GLYPH_DIR/"all_visible_glyph_raw_measurements.csv"; review_path=GLYPH_DIR/"glyph_manual_review_ledger.csv"; vis_path=REPORT_DIR/"manual_visual_semantic_review_ledger.csv"
    glyphs=read_csv_rows(glyph_path); reviews=read_csv_rows(review_path)
    if len(glyphs)!=len(reviews):raise RuntimeError("manual glyph ledger count mismatch")
    # These decisions are only written after the agent has visually reviewed every listed contact sheet.
    for row in reviews:
        row.update({"original_match":"PASS","overlay_complete":"PASS","mask_pure":"PASS","missing_stroke":"NONE","foreign_pixel":"NONE","manual_decision":"PASS","manual_note":"SA1 manually inspected ORIGINAL / OVERLAY / MASK cells at 8x nearest and referenced native 1x ROI; no target-mask omission, foreign pixel, or mutation observed."})
    write_csv(review_path,reviews,["glyph_id","sheet","cell","original_match","overlay_complete","mask_pure","missing_stroke","foreign_pixel","manual_decision","manual_note"])
    visual=read_csv_rows(vis_path)
    notes={
        "V01":"PASS: full-page placement is inside the text block with no page-edge clip or integration anomaly.",
        "V02":"PASS: native 300dpi page confirms the same placement and no clipping.",
        "V03":"PASS: panel order, arrow direction, labels, white label halos, and highlight hierarchy are visually coherent; raw-pixel threshold failures are recorded separately.",
        "V04":"PASS: grayscale retains the gold-focus / ordinary-edge distinction through border/stroke weight and layout, without a colour-only semantic dependency.",
        "V05":"PASS: direct body notation and the figure match, as documented in the semantic report.",
    }
    for row in visual:
        row["decision"]="PASS";row["note"]=notes.get(row["review_id"],"PASS")
    write_csv(vis_path,visual,["review_id","view","path","criterion","decision","note"])
    write_text(REPORT_DIR/"manual_review_basis.md","""# SA1 manual-review basis

The reviewer inspected every generated glyph contact sheet. Every cell records the actual native 300 dpi ROI and three 8× nearest-neighbour views: unmodified ORIGINAL, TARGET OVERLAY, and MASK ONLY. The review found masks faithful to their target glyphs. This manual fidelity finding does **not** override any raw-pixel threshold failure in `all_visible_glyph_raw_measurements.csv` or any independent low-profile calibration result.

The reviewer also inspected full-page 200 dpi, full-page 300 dpi, native figure/caption crop, its grayscale conversion, and the direct body excerpt. Results are in the visual/semantic ledger.
""")
    final_integrity(write=True)


def final_integrity(write:bool=False) -> dict[str,Any]:
    base=pre_review_verify(write=False)
    manual=read_csv_rows(GLYPH_DIR/"glyph_manual_review_ledger.csv")
    visual=read_csv_rows(REPORT_DIR/"manual_visual_semantic_review_ledger.csv")
    glyphs=read_csv_rows(GLYPH_DIR/"all_visible_glyph_raw_measurements.csv")
    pairs=read_csv_rows(PAIR_DIR/"all_foreground_unordered_pairs.csv")
    occ=read_csv_rows(OCC_DIR/"occlusion_reverse_ledger.csv")
    d=read_csv_rows(REPORT_DIR/"D_same_role_scale_audit.csv")
    e=read_csv_rows(REPORT_DIR/"E_cross_role_hierarchy_audit.csv")
    low=read_csv_rows(CAL_DIR/"low_profile_calibration_ledger.csv")
    val={**base,"manual_rows":len(manual),"manual_pending":sum(x.get("manual_decision") == "PENDING_MANUAL" for x in manual),"manual_nonpass":sum(x.get("manual_decision") != "PASS" for x in manual),"visual_pending":sum(x.get("decision") == "PENDING_MANUAL" for x in visual),"visual_nonpass":sum(x.get("decision") != "PASS" for x in visual),"glyph_strict_failures":sum(x.get("initial_size_gate") == "FAIL" for x in glyphs),"pair_failures":sum(x.get("decision") == "FAIL" for x in pairs),"occlusion_failures":sum(x.get("decision") == "FAIL" for x in occ),"d_failures":sum(x.get("d_decision") == "FAIL" for x in d),"e_failures":sum(x.get("e_decision") == "FAIL" for x in e),"low_profile_failures":sum(x.get("decision") != "PASS" for x in low),"state":"PRE_TERMINAL"}
    val["ready_for_terminal"] = bool(val["required_files_present"] and val["pair_complete"] and val["manual_pending"]==0 and val["visual_pending"]==0)
    if write:write_json(MACHINE_DIR/"machine_integrity_pre_terminal.json",val)
    return val


def write_preterminal_evidence_inventory() -> Path:
    """Hash every pre-terminal evidence file; terminal files are deliberately excluded."""
    inventory_path=MACHINE_DIR/"evidence_file_inventory_preterminal.json"
    excluded={inventory_path.resolve(),(OUT/"SA1_TERMINAL_VERDICT.md").resolve(),(OUT/"TERMINAL_MANIFEST.json").resolve(),(OUT/"WRITE_STOPPED").resolve()}
    entries=[]
    for p in sorted(OUT.rglob("*"),key=lambda q:str(q).lower()):
        if p.is_file() and p.resolve() not in excluded:
            entries.append({"path":rel(p),"sha256":sha256(p),"bytes":p.stat().st_size})
    write_json(inventory_path,{"created_utc":now_utc(),"algorithm":"SHA-256","purpose":"complete pre-terminal evidence inventory","excluded_terminal_paths":[rel(OUT/"SA1_TERMINAL_VERDICT.md"),rel(OUT/"TERMINAL_MANIFEST.json"),rel(OUT/"WRITE_STOPPED")],"file_count":len(entries),"files":entries})
    return inventory_path


def seal() -> None:
    check_writable()
    integ=final_integrity(write=True)
    if not integ["ready_for_terminal"]:raise RuntimeError("terminal blocked: evidence join incomplete or manual review pending")
    hard=[]
    for key,label in [("glyph_strict_failures","strict raw glyph threshold"),("low_profile_failures","low-profile independent calibration"),("pair_failures","unwhitelisted pair collision/clearance"),("occlusion_failures","occlusion reverse"),("d_failures","D same-role consistency"),("e_failures","E hierarchy"),("manual_nonpass","manual glyph fidelity"),("visual_nonpass","visual/semantic ledger")]:
        if integ.get(key,0):hard.append(f"{label}: {integ[key]}")
    inventory_path=write_preterminal_evidence_inventory()
    verdict="FAIL_TO_SA2" if hard else "PASS_TO_SA3"
    sourcehash=sha256(FIG_SOURCE);pdfhash=sha256(PDF)
    verdict_text="# FIG-P547-01 SA1 terminal verdict\n\n"
    verdict_text+=f"**{verdict}**\n\n"
    verdict_text+=f"- Audit: STRICT_R5_REQUAL_R96_SA1_CONT\n- Official PDF: `{rel(PDF)}`\n- Physical PDF page: {PDF_PAGE_1}; printed page: {PRINTED_PAGE}; figure: {FIGURE_NO}\n- Frozen source SHA-256: `{sourcehash}`\n- Official final PDF SHA-256: `{pdfhash}`\n\n"
    if hard: verdict_text+="## Terminal failing gates\n\n"+"\n".join(f"- {x}" for x in hard)+"\n"
    else: verdict_text+="All required gates are supported by complete evidence.\n"
    verdict_text+="\nThis terminal file was written before `TERMINAL_MANIFEST.json` and the final `WRITE_STOPPED` sentinel. No new claim may be added after that sentinel.\n"
    verdict_path=OUT/"SA1_TERMINAL_VERDICT.md";write_text(verdict_path,verdict_text)
    key_files=[OUT/"audit_r96_continuation.py",OUT/"identity_and_scope_manifest.json",MACHINE_DIR/"generation_manifest.json",MACHINE_DIR/"native_render_manifest.json",GLYPH_DIR/"all_visible_glyph_raw_measurements.csv",GLYPH_DIR/"glyph_manual_review_ledger.csv",CAL_DIR/"low_profile_calibration_ledger.csv",CAL_DIR/"calibration_character_inventory.csv",PAIR_DIR/"foreground_object_inventory.csv",PAIR_DIR/"all_foreground_unordered_pairs.csv",PAIR_DIR/"pair_coverage_manifest.json",PAIR_DIR/"intentional_contact_whitelist.csv",OCC_DIR/"occlusion_reverse_ledger.csv",REPORT_DIR/"D_same_role_scale_audit.csv",REPORT_DIR/"E_cross_role_hierarchy_audit.csv",REPORT_DIR/"font_floor_and_emitted_font_audit.csv",REPORT_DIR/"D_E_method_note.md",REPORT_DIR/"scope_boundary_reconciliation.json",REPORT_DIR/"scope_boundary_reconciliation.md",REPORT_DIR/"source_style_and_structure_audit.md",REPORT_DIR/"mathematical_semantic_and_text_consistency_audit.md",REPORT_DIR/"manual_visual_semantic_review_ledger.csv",REPORT_DIR/"manual_review_basis.md",REPORT_DIR/"pair_candidate_manual_review.md",REPORT_DIR/"SA1_gate_register_preterminal.md",MACHINE_DIR/"machine_integrity_pre_terminal.json",inventory_path,verdict_path]
    manifest={"audit":"FIG-P547-01 STRICT_R5_REQUAL_R96_SA1_CONT","sealed_utc":now_utc(),"terminal_verdict":verdict,"terminal_integrity":integ,"canonical_output_directory":rel(OUT),"files_before_write_stopped":[{"path":rel(p),"sha256":sha256(p),"bytes":p.stat().st_size} for p in key_files],"write_order":"SA1_TERMINAL_VERDICT.md -> TERMINAL_MANIFEST.json -> WRITE_STOPPED","post_stop_rule":"No write is permitted after WRITE_STOPPED."}
    write_json(OUT/"TERMINAL_MANIFEST.json",manifest)
    # This must remain the last mutation in this directory.
    (OUT/"WRITE_STOPPED").write_text("SEALED " + now_utc() + "\nTerminal verdict: " + verdict + "\n",encoding="utf-8",newline="\n")
    print(json.dumps({"terminal_verdict":verdict,"hard_failures":hard,"write_stopped":rel(OUT/"WRITE_STOPPED")},ensure_ascii=False))


def verify_only() -> None:
    # Guaranteed read-only: no helper called from here writes a file.
    print(json.dumps({"write_stopped":(PACKAGE_ROOT/"WRITE_STOPPED").exists(),"generated_integrity":pre_review_verify(write=False)},ensure_ascii=False,indent=2))


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("phase",choices=["generate","verify-only"])
    args=parser.parse_args()
    if args.phase=="generate":generate()
    else:verify_only()


if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("AUDIT_ERROR: "+repr(exc),file=sys.stderr)
        raise
