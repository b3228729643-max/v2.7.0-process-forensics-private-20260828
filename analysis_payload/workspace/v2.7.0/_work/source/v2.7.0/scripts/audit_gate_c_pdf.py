#!/usr/bin/env python3
"""Audit Gate-C figure/font contracts and prepare targeted visual contacts.

The script never performs a full-book render.  It either renders the 99
caption-adjacent figure regions directly for a targeted preflight or crops
those regions from an already completed Gate-C full-page render.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fitz
from PIL import Image, ImageDraw


# LuaLaTeX/PyMuPDF may expose the caption separator as a line break rather
# than a literal colon.  The figure number at the start of its own text block
# is the stable contract; accept either representation.
CAPTION_RE = re.compile(r"^图\s*(\d+\.\d+)$")
FORBIDDEN_FIGURE_SIZING_RE = re.compile(r"\\(?:scriptsize|tiny|resizebox|scalebox)\b")
SOURCE_EXTENSIONS = {".tex"}


@dataclass(frozen=True)
class CaptionRecord:
    number: str
    page: int
    bbox: tuple[float, float, float, float]
    text: str


def global_chapter(chapter_id: str) -> int:
    match = re.fullmatch(r"V([1-5])-C(\d{2})", chapter_id)
    if not match:
        raise ValueError(f"invalid chapter_id: {chapter_id}")
    volume, local = map(int, match.groups())
    offsets = {1: 0, 2: 11, 3: 16, 4: 23, 5: 29}
    return offsets[volume] + local


def load_figure_sources(project_root: Path) -> list[dict]:
    records: list[dict] = []
    manifest_paths = sorted((project_root / "src").rglob("figure_sources.json"))
    if len(manifest_paths) != 37:
        raise RuntimeError(f"expected 37 chapter figure manifests, found {len(manifest_paths)}")
    for manifest_path in manifest_paths:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        chapter_id = str(payload["chapter_id"])
        figures = payload.get("figures", [])
        if int(payload.get("figure_count", -1)) != len(figures):
            raise RuntimeError(f"figure_count mismatch in {manifest_path}")
        chapter = global_chapter(chapter_id)
        for ordinal, raw in enumerate(figures, 1):
            record = dict(raw)
            record["chapter_id"] = chapter_id
            record["chapter"] = chapter
            record["number"] = f"{chapter}.{ordinal}"
            source_path = project_root / "src" / Path(str(record["source_path"]))
            if not source_path.is_file():
                raise RuntimeError(f"missing figure source: {source_path}")
            record["resolved_source"] = str(source_path.resolve())
            records.append(record)
    numbers = [item["number"] for item in records]
    labels = [str(item["label"]) for item in records]
    sources = [str(item["source_path"]) for item in records]
    if len(records) != 99 or len(set(numbers)) != 99 or len(set(labels)) != 99 or len(set(sources)) != 99:
        raise RuntimeError("figure source inventory must contain 99 unique numbers, labels, and paths")
    return records


def load_numeric_contract(project_root: Path) -> dict:
    path = project_root / "src" / "绘图源码" / "figure_numeric_manifest_v16.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    passed = [
        item
        for item in records
        if str(item.get("verification", {}).get("status", "")).startswith("passed")
    ]
    if payload.get("record_count") != 34 or len(records) != 34 or len(passed) != 34:
        raise RuntimeError("the numeric figure contract must contain 34 passed records")
    return {
        "path": str(path.resolve()),
        "record_count": len(records),
        "passed_count": len(passed),
        "identity_unique": len({item.get("figure_id") for item in records}) == len(records),
    }


def caption_records(document: fitz.Document) -> list[CaptionRecord]:
    records: list[CaptionRecord] = []
    for page_number, page in enumerate(document, 1):
        for block in page.get_text("blocks"):
            raw_text = str(block[4])
            first_line = raw_text.splitlines()[0].strip() if raw_text.splitlines() else ""
            text = " ".join(raw_text.split())
            match = CAPTION_RE.fullmatch(first_line)
            if match:
                records.append(
                    CaptionRecord(
                        number=match.group(1),
                        page=page_number,
                        bbox=tuple(round(float(value), 3) for value in block[:4]),
                        text=text,
                    )
                )
    numbers = [item.number for item in records]
    if len(records) != 99 or len(set(numbers)) != 99:
        raise RuntimeError(f"expected 99 unique rendered captions, found {len(records)}/{len(set(numbers))}")
    return records


def visible_count(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def font_audit(document: fitz.Document) -> dict:
    deep_math_scripts: list[dict] = []
    critical_small: list[dict] = []
    base_sizes: list[float] = []
    pages_with_deep_scripts: set[int] = set()
    for page_number, page in enumerate(document, 1):
        payload = page.get_text("dict")
        for block in payload.get("blocks", []):
            for line in block.get("lines", []):
                spans = [span for span in line.get("spans", []) if visible_count(str(span.get("text", "")))]
                if not spans:
                    continue
                for span in spans:
                    size = float(span.get("size", 0.0))
                    text = " ".join(str(span.get("text", "")).split())
                    font = str(span.get("font", ""))
                    bbox = [round(float(value), 3) for value in span.get("bbox", (0, 0, 0, 0))]
                    # TeX emits mathematical subscripts, superscripts, limits,
                    # and their roman words as separate STIX/Heros spans.  The
                    # surrounding display may also be split into another PDF
                    # line, so line-local math detection alone is insufficient.
                    # Actual prose, algorithm text, and CJK figure labels use
                    # Noto/LMMono at their base rung; any sub-8.5pt STIX/Heros
                    # span is therefore a mathematical script, not key text.
                    math_script = size < 8.5 and (
                        font.startswith("STIXTwo") or font.startswith("TeXGyreHeros")
                    )
                    if math_script:
                        pages_with_deep_scripts.add(page_number)
                        deep_math_scripts.append(
                            {"page": page_number, "size": round(size, 3), "font": font, "text": text, "bbox": bbox}
                        )
                    else:
                        base_sizes.append(size)
                        if size < 8.5:
                            critical_small.append(
                                {"page": page_number, "size": round(size, 3), "font": font, "text": text, "bbox": bbox}
                            )
    return {
        "critical_small_span_count": len(critical_small),
        "critical_small_spans": critical_small,
        "deep_math_script_span_count": len(deep_math_scripts),
        "deep_math_script_pages": sorted(pages_with_deep_scripts),
        "deep_math_script_min_pt": round(min((item["size"] for item in deep_math_scripts), default=0.0), 3),
        "base_text_min_pt": round(min(base_sizes), 3) if base_sizes else None,
        "classification_note": (
            "Deep mathematical subscripts/superscripts are reported separately; they are not standalone body, "
            "algorithm, table, or figure labels."
        ),
    }


def source_audit(records: Iterable[dict]) -> dict:
    forbidden: list[dict] = []
    explicit_font_contract = 0
    source_kinds: Counter[str] = Counter()
    dual_encoding_tokens = 0
    includegraphics = 0
    for record in records:
        path = Path(record["resolved_source"])
        text = path.read_text(encoding="utf-8")
        source_kinds[str(record.get("source_kind", "unknown"))] += 1
        if re.search(r"\\fontsize\{9\.5pt\}|\\normalsize", text):
            explicit_font_contract += 1
        for match in FORBIDDEN_FIGURE_SIZING_RE.finditer(text):
            forbidden.append({"source": str(record["source_path"]), "token": match.group(0)})
        dual_encoding_tokens += len(re.findall(r"dashed|dotted|dash pattern|mark\s*=|pattern\s*=", text))
        includegraphics += len(re.findall(r"\\includegraphics\b", text))
    return {
        "figure_source_count": len(list(records)) if not isinstance(records, list) else len(records),
        "source_kind_counts": dict(source_kinds),
        "explicit_9_5pt_or_normalsize_sources": explicit_font_contract,
        "global_fallback": "statlearnbook.sty applies \\small to every TikZ node and PGFPlots label/tick/legend",
        "forbidden_sizing_occurrences": forbidden,
        "includegraphics_occurrences": includegraphics,
        "dual_encoding_token_count": dual_encoding_tokens,
    }


def crop_rect(page: fitz.Page, caption: CaptionRecord) -> fitz.Rect:
    x0 = max(24.0, min(48.0, caption.bbox[0] - 8.0))
    x1 = min(float(page.rect.width) - 24.0, max(float(page.rect.width) - 48.0, caption.bbox[2] + 8.0))
    y0 = max(36.0, caption.bbox[1] - 460.0)
    y1 = min(float(page.rect.height) - 30.0, caption.bbox[3] + 10.0)
    return fitz.Rect(x0, y0, x1, y1)


def existing_page_image(page_image_dir: Path, page_number: int) -> Path:
    candidates = [
        page_image_dir / f"page-{page_number:03d}.png",
        page_image_dir / f"page-{page_number:04d}.png",
        page_image_dir / f"page-{page_number}.png",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    matches = sorted(page_image_dir.glob(f"page-*{page_number}.png"))
    if len(matches) == 1:
        return matches[0]
    raise RuntimeError(f"cannot resolve rendered image for page {page_number} in {page_image_dir}")


def render_or_crop(
    document: fitz.Document,
    caption: CaptionRecord,
    *,
    dpi: int,
    page_image_dir: Path | None,
) -> Image.Image:
    page = document[caption.page - 1]
    clip = crop_rect(page, caption)
    if page_image_dir is None:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), clip=clip, alpha=False)
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    page_image = Image.open(existing_page_image(page_image_dir, caption.page)).convert("RGB")
    scale_x = page_image.width / float(page.rect.width)
    scale_y = page_image.height / float(page.rect.height)
    pixel_box = (
        round(clip.x0 * scale_x),
        round(clip.y0 * scale_y),
        round(clip.x1 * scale_x),
        round(clip.y1 * scale_y),
    )
    return page_image.crop(pixel_box)


def save_contacts(images: list[tuple[str, Image.Image]], output_dir: Path, *, columns: int = 3, rows: int = 4) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cell_width, cell_height, label_height = 1050, 1080, 42
    per_sheet = columns * rows
    outputs: list[str] = []
    for sheet_index in range(0, len(images), per_sheet):
        group = images[sheet_index : sheet_index + per_sheet]
        canvas = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
        draw = ImageDraw.Draw(canvas)
        for local_index, (label, image) in enumerate(group):
            column = local_index % columns
            row = local_index // columns
            x0, y0 = column * cell_width, row * cell_height
            fitted = image.copy()
            fitted.thumbnail((cell_width - 16, cell_height - label_height - 16), Image.Resampling.LANCZOS)
            paste_x = x0 + (cell_width - fitted.width) // 2
            paste_y = y0 + label_height + (cell_height - label_height - fitted.height) // 2
            canvas.paste(fitted, (paste_x, paste_y))
            draw.text((x0 + 12, y0 + 10), label, fill="black")
            draw.rectangle((x0, y0, x0 + cell_width - 1, y0 + cell_height - 1), outline="#777777", width=2)
        output_path = output_dir / f"contact-{sheet_index // per_sheet + 1:02d}.png"
        canvas.save(output_path, optimize=True)
        outputs.append(str(output_path.resolve()))
    return outputs


def visual_contacts(
    document: fitz.Document,
    captions: list[CaptionRecord],
    output_dir: Path,
    *,
    dpi: int,
    page_image_dir: Path | None,
) -> dict:
    color_dir = output_dir / "color"
    gray_dir = output_dir / "gray"
    crop_dir = output_dir / "crops"
    crop_dir.mkdir(parents=True, exist_ok=True)
    color_images: list[tuple[str, Image.Image]] = []
    gray_images: list[tuple[str, Image.Image]] = []
    for index, caption in enumerate(sorted(captions, key=lambda item: tuple(map(int, item.number.split(".")))), 1):
        image = render_or_crop(document, caption, dpi=dpi, page_image_dir=page_image_dir)
        label = f"FIG {caption.number} | PDF p.{caption.page}"
        crop_path = crop_dir / f"fig-{index:03d}-{caption.number}-p{caption.page:03d}.png"
        image.save(crop_path, optimize=True)
        color_images.append((label, image))
        gray_images.append((label, image.convert("L").convert("RGB")))
    return {
        "dpi": dpi,
        "source": "full_page_render" if page_image_dir else "targeted_pdf_regions",
        "crop_count": len(color_images),
        "color_contacts": save_contacts(color_images, color_dir),
        "gray_contacts": save_contacts(gray_images, gray_dir),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--visual-dir", type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--page-image-dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project_root = args.project_root.resolve()
    pdf_path = args.pdf.resolve()
    records = load_figure_sources(project_root)
    numeric = load_numeric_contract(project_root)
    with fitz.open(pdf_path) as document:
        captions = caption_records(document)
        by_number = {item.number: item for item in captions}
        if set(by_number) != {str(item["number"]) for item in records}:
            raise RuntimeError("source and rendered figure-number inventories differ")
        fonts = font_audit(document)
        page_sizes = Counter((round(page.rect.width, 3), round(page.rect.height, 3)) for page in document)
        image_objects = sum(len(page.get_images(full=True)) for page in document)
        visuals = None
        if args.visual_dir:
            visuals = visual_contacts(
                document,
                captions,
                args.visual_dir.resolve(),
                dpi=args.dpi,
                page_image_dir=args.page_image_dir.resolve() if args.page_image_dir else None,
            )
        figure_rows = []
        for record in sorted(records, key=lambda item: tuple(map(int, str(item["number"]).split(".")))):
            caption = by_number[str(record["number"])]
            figure_rows.append(
                {
                    "number": record["number"],
                    "chapter": record["chapter"],
                    "page": caption.page,
                    "figure_id": record["figure_id"],
                    "label": record["label"],
                    "source_path": record["source_path"],
                    "source_kind": record["source_kind"],
                    "semantic_type": record["semantic_type"],
                    "teaching_objective": record["teaching_objective"],
                    "canonical_caption": record["caption"],
                    "rendered_caption": caption.text,
                    "caption_bbox": list(caption.bbox),
                    "numeric_recomputation_required": bool(record.get("numeric_recomputation", {}).get("required")),
                    "alt_text_count": len(record.get("accessibility", {}).get("alt_texts", [])),
                }
            )
        report = {
            "schema_version": 1,
            "pdf": str(pdf_path),
            "page_count": len(document),
            "page_sizes": {f"{width}x{height}": count for (width, height), count in page_sizes.items()},
            "figure_count": len(figure_rows),
            "rendered_image_object_occurrences": image_objects,
            "source_audit": source_audit(records),
            "numeric_contract": numeric,
            "font_audit": fonts,
            "visual_contacts": visuals,
            "figures": figure_rows,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"GATE_C_FIGURES={report['figure_count']}")
    print(f"GATE_C_CRITICAL_SMALL_SPANS={report['font_audit']['critical_small_span_count']}")
    print(f"GATE_C_DEEP_MATH_SCRIPT_SPANS={report['font_audit']['deep_math_script_span_count']}")
    print(f"GATE_C_OUTPUT={args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
