#!/usr/bin/env python3
"""Build Gate C priority-review contact sheets from the existing 200 dpi PNGs.

This script never renders the PDF. It only downsamples the one allowed Gate C
full-book render so that the specified priority sets can be reviewed in batches.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


def load_workbook_sheet(cache: dict, name: str) -> list[list[object]]:
    return next(sheet["values"] for sheet in cache["sheets"] if sheet["name"] == name)


def rows_as_dicts(values: list[list[object]]) -> list[dict[str, object]]:
    headers = [str(value) for value in values[0]]
    return [dict(zip(headers, row)) for row in values[1:]]


def map_baseline_page(page: int, chapter: int, old_starts: dict[int, int], new_starts: dict[int, int]) -> int:
    if chapter <= 0 or chapter not in old_starts or chapter not in new_starts:
        return page
    return page + new_starts[chapter] - old_starts[chapter]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", default="qa/source_cache/gate_c_priority_review.json")
    parser.add_argument("--contact-dir", default="qa/previews/gate_c_priority_pages")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    cache = json.loads((root / "qa/source_cache/workbook_v1.9.0.json").read_text(encoding="utf-8"))
    layout = json.loads((root / "qa/source_cache/gate_c_final_layout.json").read_text(encoding="utf-8"))["reports"][0]
    figures = json.loads((root / "qa/source_cache/gate_c_final_figure_audit.json").read_text(encoding="utf-8"))["figures"]
    render_dir = root / "qa/rendered/gate_c_200dpi"
    contact_dir = root / args.contact_dir
    contact_dir.mkdir(parents=True, exist_ok=True)

    visual_rows = rows_as_dicts(load_workbook_sheet(cache, "逐页视觉风险"))
    algorithm_rows = rows_as_dicts(load_workbook_sheet(cache, "算法审计"))
    old_starts: dict[int, int] = {}
    for row in visual_rows:
        chapter = int(row.get("章") or 0)
        page = int(row.get("PDF页") or 0)
        if chapter > 0 and page > 0:
            old_starts[chapter] = min(old_starts.get(chapter, page), page)
    new_starts = {index + 1: int(card["start_page"]) for index, card in enumerate(layout["chapter_cards"])}

    groups: dict[str, set[int]] = defaultdict(set)
    for row in visual_rows:
        if str(row.get("风险等级") or "") == "高":
            page = map_baseline_page(int(row["PDF页"]), int(row.get("章") or 0), old_starts, new_starts)
            groups["workbook_high_risk"].add(page)
    groups["modified_figure_pages"].update(int(figure["page"]) for figure in figures)
    for row in algorithm_rows:
        page = map_baseline_page(int(row["PDF页"]), int(row.get("章") or 0), old_starts, new_starts)
        groups["long_algorithm_pages"].add(page)
    groups["chapter_openers"].update(new_starts.values())
    groups["volume_separators"].update(new_starts[chapter] for chapter in (1, 12, 17, 24, 30))
    groups["toc_symbol_topic_index"].update(range(2, 14))
    groups["toc_symbol_topic_index"].update(range(765, 772))

    doc = fitz.open(root / "build/gate_c/main_full.pdf")
    table_pattern = re.compile(r"表\s*\d+\.\d+")
    example_pattern = re.compile(r"(?:例|例题)\s*\d+\.\d+")
    for chapter, start in new_starts.items():
        end = new_starts.get(chapter + 1, 765) - 1
        first_example = None
        for page_number in range(start, end + 1):
            text = doc[page_number - 1].get_text("text")
            if table_pattern.search(text):
                groups["long_table_pages"].add(page_number)
            if first_example is None and example_pattern.search(text):
                first_example = page_number
        if first_example is not None:
            groups["first_core_example_pages"].add(first_example)

    reasons: dict[int, list[str]] = defaultdict(list)
    for group, pages in groups.items():
        for page in sorted(pages):
            if 1 <= page <= len(doc):
                reasons[page].append(group)
    selected = sorted(reasons)

    font = ImageFont.load_default()
    thumb_width, thumb_height = 390, 552
    cell_width, cell_height = 400, 590
    per_sheet = 16
    contacts = []
    for sheet_index, offset in enumerate(range(0, len(selected), per_sheet), start=1):
        batch = selected[offset : offset + per_sheet]
        canvas = Image.new("RGB", (cell_width * 4, cell_height * 4), "#d9e2f3")
        draw = ImageDraw.Draw(canvas)
        for position, page in enumerate(batch):
            row, col = divmod(position, 4)
            source = render_dir / f"page-{page:03d}.png"
            with Image.open(source) as image:
                preview = image.convert("RGB")
                preview.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                x = col * cell_width + (cell_width - preview.width) // 2
                y = row * cell_height + 30
                canvas.paste(preview, (x, y))
            label = f"p{page}: {','.join(reasons[page])}"
            draw.text((col * cell_width + 6, row * cell_height + 6), label[:66], fill="#000000", font=font)
        output = contact_dir / f"priority-{sheet_index:02d}.png"
        canvas.save(output, optimize=True)
        contacts.append(str(output))

    payload = {
        "schema_version": 1,
        "source_render": str(render_dir),
        "source_render_reused_without_pdf_rerender": True,
        "selected_page_count": len(selected),
        "selected_pages": [{"page": page, "reasons": reasons[page]} for page in selected],
        "group_counts": {group: len(pages) for group, pages in sorted(groups.items())},
        "contact_sheets": contacts,
    }
    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected_page_count": len(selected), "contact_sheet_count": len(contacts), "output": str(output_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
