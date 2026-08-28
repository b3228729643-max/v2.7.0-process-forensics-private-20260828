#!/usr/bin/env python3
"""Reproducible PDF font, sparse-page, and chapter-card audit.

The audit is intentionally read-only.  It uses visible text spans reported by
PyMuPDF, keeps page numbers one-based in every result, and never treats a local
development build as a G2/G3 pass by itself.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import fitz


NONSPACE = re.compile(r"\S")
CHAPTER_CARD_START = "本章地图"
CHAPTER_CARD_END = "完成标准与返回"
SYMBOL_TABLE_START = "本章符号表"


@dataclass(frozen=True)
class PageStat:
    page: int
    width: float
    height: float
    visible_characters: int
    text_span_count: int
    minimum_font_pt: float | None
    characters_below_6pt: int
    characters_below_7_5pt: int
    characters_below_8_5pt: int


@dataclass(frozen=True)
class ChapterCardStat:
    start_page: int
    end_page: int | None
    footprint_pages: float | None
    complete: bool
    reason: str


def _visible_characters(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def _page_text_blocks(page: fitz.Page) -> list[tuple[float, float, float, float, str]]:
    blocks: list[tuple[float, float, float, float, str]] = []
    for raw in page.get_text("blocks"):
        x0, y0, x1, y1, text = raw[:5]
        if NONSPACE.search(text or ""):
            blocks.append((float(x0), float(y0), float(x1), float(y1), str(text)))
    return sorted(blocks, key=lambda block: (block[1], block[0]))


def page_stat(page: fitz.Page, page_number: int) -> PageStat:
    raw = page.get_text("dict")
    minimum: float | None = None
    spans = 0
    below_6 = 0
    below_7_5 = 0
    below_8_5 = 0
    visible = 0
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = str(span.get("text", ""))
                count = _visible_characters(text)
                if count == 0:
                    continue
                size = float(span.get("size", 0.0))
                spans += 1
                visible += count
                minimum = size if minimum is None else min(minimum, size)
                if size < 6.0:
                    below_6 += count
                if size < 7.5:
                    below_7_5 += count
                if size < 8.5:
                    below_8_5 += count
    rect = page.rect
    return PageStat(
        page=page_number,
        width=round(float(rect.width), 3),
        height=round(float(rect.height), 3),
        visible_characters=visible,
        text_span_count=spans,
        minimum_font_pt=None if minimum is None else round(minimum, 3),
        characters_below_6pt=below_6,
        characters_below_7_5pt=below_7_5,
        characters_below_8_5pt=below_8_5,
    )


def _first_block_y(blocks: Sequence[tuple[float, float, float, float, str]], marker: str) -> float | None:
    ys = [block[1] for block in blocks if marker in block[4]]
    return min(ys) if ys else None


def _card_end_y(
    blocks: Sequence[tuple[float, float, float, float, str]],
) -> float | None:
    dependency_y = _first_block_y(blocks, CHAPTER_CARD_END)
    if dependency_y is None:
        return None
    symbol_y = _first_block_y(blocks, SYMBOL_TABLE_START)
    eligible = [block[3] for block in blocks if block[1] >= dependency_y]
    if symbol_y is not None:
        eligible = [block[3] for block in blocks if dependency_y <= block[1] < symbol_y]
    return max(eligible, default=None)


def chapter_card_stats(document: fitz.Document, lookahead: int = 3) -> list[ChapterCardStat]:
    page_blocks = [_page_text_blocks(page) for page in document]
    results: list[ChapterCardStat] = []
    for start_index, blocks in enumerate(page_blocks):
        start_y = _first_block_y(blocks, CHAPTER_CARD_START)
        if start_y is None:
            continue
        end_index: int | None = None
        end_y: float | None = None
        for candidate in range(start_index, min(len(document), start_index + lookahead + 1)):
            found = _card_end_y(page_blocks[candidate])
            if found is not None:
                end_index = candidate
                end_y = found
                break
        if end_index is None or end_y is None:
            results.append(
                ChapterCardStat(
                    start_page=start_index + 1,
                    end_page=None,
                    footprint_pages=None,
                    complete=False,
                    reason=f"missing '{CHAPTER_CARD_END}' within {lookahead} following pages",
                )
            )
            continue
        first_height = float(document[start_index].rect.height)
        if end_index == start_index:
            footprint = max(0.0, end_y - start_y) / first_height
        else:
            footprint = max(0.0, first_height - start_y) / first_height
            footprint += max(0, end_index - start_index - 1)
            footprint += max(0.0, end_y) / float(document[end_index].rect.height)
        results.append(
            ChapterCardStat(
                start_page=start_index + 1,
                end_page=end_index + 1,
                footprint_pages=round(footprint, 3),
                complete=True,
                reason="ok",
            )
        )
    return results


def audit_pdf(
    pdf_path: Path,
    *,
    exempt_pages: Iterable[int] = (),
    sparse_character_limit: int = 100,
    low_content_character_limit: int = 300,
    chapter_card_limit: float = 1.5,
) -> dict:
    exempt = set(exempt_pages)
    with fitz.open(pdf_path) as document:
        pages = [page_stat(page, index + 1) for index, page in enumerate(document)]
        page_texts = [page.get_text() for page in document]
        cards = chapter_card_stats(document)
    automatic_exempt_reasons: dict[int, str] = {}
    for page_number, text in enumerate(page_texts, 1):
        # Every body page has a footer link named “目录”, whereas a contents
        # page also has its page heading.  Requiring two occurrences and a
        # front-matter position keeps ordinary chapter pages auditable.
        if page_number <= 40 and text.count("目录") >= 2:
            automatic_exempt_reasons[page_number] = "table_of_contents"
        elif any(marker in text for marker in ("符号索引", "主题索引")):
            automatic_exempt_reasons[page_number] = "index"
    effective_exempt = exempt | set(automatic_exempt_reasons)
    below_6 = [stat.page for stat in pages if stat.characters_below_6pt]
    below_7_5 = [stat.page for stat in pages if stat.characters_below_7_5pt]
    below_8_5 = [stat.page for stat in pages if stat.characters_below_8_5pt]
    sparse = [
        stat.page
        for stat in pages
        if stat.page not in effective_exempt and stat.visible_characters <= sparse_character_limit
    ]
    low_content = [
        stat.page
        for stat in pages
        if stat.page not in effective_exempt and stat.visible_characters <= low_content_character_limit
    ]
    incomplete_cards = [card.start_page for card in cards if not card.complete]
    oversized_cards = [
        card.start_page
        for card in cards
        if card.footprint_pages is not None and card.footprint_pages > chapter_card_limit
    ]
    return {
        "pdf": str(pdf_path.resolve()),
        "page_count": len(pages),
        "thresholds": {
            "absolute_minimum_font_pt": 6.0,
            "ordinary_body_report_pt": 7.5,
            "algorithm_figure_report_pt": 8.5,
            "sparse_visible_characters": sparse_character_limit,
            "low_content_visible_characters": low_content_character_limit,
            "chapter_card_footprint_pages": chapter_card_limit,
        },
        "exempt_pages": sorted(exempt),
        "automatic_exempt_pages": automatic_exempt_reasons,
        "summary": {
            "pages_with_characters_below_6pt": below_6,
            "pages_with_characters_below_7_5pt": below_7_5,
            "pages_with_characters_below_8_5pt": below_8_5,
            "sparse_pages": sparse,
            "low_content_pages": low_content,
            "incomplete_chapter_cards": incomplete_cards,
            "oversized_chapter_cards": oversized_cards,
        },
        "chapter_cards": [asdict(card) for card in cards],
        "pages": [asdict(stat) for stat in pages],
    }


def _parse_pages(raw: str) -> set[int]:
    pages: set[int] = set()
    if not raw.strip():
        return pages
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "-" in item:
            start_text, end_text = item.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start <= 0 or end < start:
                raise argparse.ArgumentTypeError(f"invalid page range: {item}")
            pages.update(range(start, end + 1))
        else:
            page = int(item)
            if page <= 0:
                raise argparse.ArgumentTypeError(f"invalid page: {item}")
            pages.add(page)
    return pages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", nargs="+", type=Path)
    parser.add_argument("--exempt-pages", default="1-4", help="one-based list/ranges, e.g. 1-4,9")
    parser.add_argument("--sparse-limit", type=int, default=100)
    parser.add_argument("--low-content-limit", type=int, default=300)
    parser.add_argument("--chapter-card-limit", type=float, default=1.5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exempt = _parse_pages(args.exempt_pages)
    reports = [
        audit_pdf(
            pdf,
            exempt_pages=exempt,
            sparse_character_limit=args.sparse_limit,
            low_content_character_limit=args.low_content_limit,
            chapter_card_limit=args.chapter_card_limit,
        )
        for pdf in args.pdf
    ]
    payload = {"reports": reports}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    if not args.strict:
        return 0
    for report in reports:
        summary = report["summary"]
        if (
            summary["pages_with_characters_below_6pt"]
            or summary["sparse_pages"]
            or summary["incomplete_chapter_cards"]
            or summary["oversized_chapter_cards"]
        ):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
