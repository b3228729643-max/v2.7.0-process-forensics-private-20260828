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
VOLUME_RE = re.compile(r"^第\s*(\d+)\s*册[：:]")
VERSION_RE = re.compile(r"v\d+\.\d+\.\d+")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_release_version() -> str:
    source = (PROJECT_ROOT / "manifests" / "release_version.tex").read_text(
        encoding="utf-8"
    )
    active_source = "\n".join(line.split("%", 1)[0] for line in source.splitlines())
    matches = re.findall(
        r"\\newcommand\s*\{\\SLReleaseVersion\}\s*\{(v\d+\.\d+\.\d+)\}",
        active_source,
    )
    if len(matches) != 1:
        raise RuntimeError("release_version.tex must define one SLReleaseVersion")
    return matches[0]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pdf_path = args.pdf.resolve()
    release_version = read_release_version()

    with fitz.open(pdf_path) as document:
        toc = document.get_toc(simple=True)
        normalized_titles = [" ".join(title.split()) for _, title, _ in toc]
        chapter_entries = [
            {"level": level, "title": title, "page": page}
            for level, title, page in toc
            if CHAPTER_RE.match(title.strip())
        ]
        chapter_numbers = [int(CHAPTER_RE.match(item["title"].strip()).group(1)) for item in chapter_entries]
        volume_entries = [
            {"level": level, "title": title, "page": page}
            for level, title, page in toc
            if VOLUME_RE.match(title.strip())
        ]
        volume_numbers = [
            int(VOLUME_RE.match(item["title"].strip()).group(1))
            for item in volume_entries
        ]
        required_bookmarks = {
            title: title in normalized_titles for title in ("符号索引", "主题索引")
        }
        invalid_toc = [
            {"level": level, "title": title, "page": page}
            for level, title, page in toc
            if page < 1 or page > document.page_count
        ]
        link_kinds: Counter[str] = Counter()
        invalid_links: list[dict[str, object]] = []
        names = document.resolve_names()
        metadata = document.metadata or {}
        metadata_fields = {
            field: str(metadata.get(field, ""))
            for field in ("title", "subject", "keywords")
        }
        metadata_version_fields = {
            field: release_version in value
            for field, value in metadata_fields.items()
        }
        metadata_versions = sorted(
            set(VERSION_RE.findall("\n".join(metadata_fields.values())))
        )
        unexpected_metadata_versions = [
            version for version in metadata_versions if version != release_version
        ]
        visible_version_pages: dict[str, list[int]] = {}
        for page_number, page in enumerate(document, 1):
            for version in sorted(set(VERSION_RE.findall(page.get_text()))):
                visible_version_pages.setdefault(version, []).append(page_number)
        unexpected_visible_versions = [
            version for version in visible_version_pages if version != release_version
        ]
        a4_page_count = sum(
            1
            for page in document
            if abs(page.rect.width - 595.276) <= 0.5
            and abs(page.rect.height - 841.89) <= 0.5
            and page.rotation == 0
        )
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
            and volume_numbers == list(range(1, 6))
            and all(required_bookmarks.values())
            and not invalid_toc
            and all(metadata_version_fields.values())
            and not unexpected_metadata_versions
            and release_version in visible_version_pages
            and not unexpected_visible_versions
            and a4_page_count == document.page_count
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
            "volume_bookmark_count": len(volume_entries),
            "volume_numbers": volume_numbers,
            "volume_entries": volume_entries,
            "required_bookmarks": required_bookmarks,
            "invalid_bookmarks": invalid_toc,
            "release_version": release_version,
            "metadata": metadata_fields,
            "metadata_version_fields": metadata_version_fields,
            "unexpected_metadata_versions": unexpected_metadata_versions,
            "visible_version_pages": visible_version_pages,
            "unexpected_visible_versions": unexpected_visible_versions,
            "a4_unrotated_page_count": a4_page_count,
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
    print(json.dumps({key: value for key, value in payload.items() if key not in {"chapter_entries", "volume_entries", "invalid_links"}}, ensure_ascii=False, indent=2))
    return 0 if result_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
