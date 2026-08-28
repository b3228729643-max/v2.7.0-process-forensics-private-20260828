#!/usr/bin/env python3
"""Audit bookmarks and internal links in the compiled merged PDF."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import re
import sys

import fitz


CHAPTER_RE = re.compile(r"^第\s*(\d+)\s*章")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pdf_path = args.pdf.resolve()

    with fitz.open(pdf_path) as document:
        toc = document.get_toc(simple=True)
        chapter_entries = [
            {"level": level, "title": title, "page": page}
            for level, title, page in toc
            if CHAPTER_RE.match(title.strip())
        ]
        chapter_numbers = [int(CHAPTER_RE.match(item["title"].strip()).group(1)) for item in chapter_entries]
        invalid_toc = [
            {"level": level, "title": title, "page": page}
            for level, title, page in toc
            if page < 1 or page > document.page_count
        ]
        link_kinds: Counter[str] = Counter()
        invalid_links: list[dict[str, object]] = []
        names = document.resolve_names()
        total_links = 0
        pages_with_links = 0
        for page_number, page in enumerate(document, 1):
            links = page.get_links()
            if links:
                pages_with_links += 1
            total_links += len(links)
            for link in links:
                kind = int(link.get("kind", 0))
                kind_name = {
                    fitz.LINK_NONE: "none",
                    fitz.LINK_GOTO: "goto",
                    fitz.LINK_URI: "uri",
                    fitz.LINK_LAUNCH: "launch",
                    fitz.LINK_NAMED: "named",
                    fitz.LINK_GOTOR: "gotor",
                }.get(kind, f"kind_{kind}")
                link_kinds[kind_name] += 1
                if kind == fitz.LINK_GOTO:
                    target = int(link.get("page", -1))
                    if target < 0 or target >= document.page_count:
                        invalid_links.append(
                            {"source_page": page_number, "kind": kind_name, "target_page_zero_based": target}
                        )
                elif kind == fitz.LINK_URI and not str(link.get("uri", "")).strip():
                    invalid_links.append({"source_page": page_number, "kind": kind_name, "reason": "empty URI"})
                elif kind == fitz.LINK_NAMED:
                    destination = str(link.get("nameddest", "")).strip()
                    target = int(link.get("page", -1))
                    if not destination or destination not in names:
                        invalid_links.append(
                            {"source_page": page_number, "kind": kind_name, "destination": destination, "reason": "missing named destination"}
                        )
                    elif target < 0 or target >= document.page_count:
                        invalid_links.append(
                            {"source_page": page_number, "kind": kind_name, "destination": destination, "target_page_zero_based": target}
                        )

        result_ok = (
            len(toc) > 37
            and chapter_numbers == list(range(1, 38))
            and not invalid_toc
            and total_links > 0
            and pages_with_links == document.page_count - 1
            and not invalid_links
        )
        payload = {
            "schema_version": 1,
            "pdf": str(pdf_path),
            "page_count": document.page_count,
            "bookmark_count": len(toc),
            "bookmark_level_counts": dict(Counter(level for level, _, _ in toc)),
            "chapter_bookmark_count": len(chapter_entries),
            "chapter_numbers": chapter_numbers,
            "chapter_entries": chapter_entries,
            "invalid_bookmarks": invalid_toc,
            "link_count": total_links,
            "pages_with_links": pages_with_links,
            "cover_without_links": not document[0].get_links(),
            "named_destination_count": len(names),
            "link_kind_counts": dict(link_kinds),
            "invalid_links": invalid_links,
            "result": "PASS" if result_ok else "FAIL",
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key not in {"chapter_entries", "invalid_links"}}, ensure_ascii=False, indent=2))
    return 0 if result_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
