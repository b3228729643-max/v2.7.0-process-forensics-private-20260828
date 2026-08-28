from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def flatten_outline(reader: PdfReader, items: list[Any], level: int = 1):
    for item in items:
        if isinstance(item, list):
            yield from flatten_outline(reader, item, level + 1)
            continue
        title = str(getattr(item, "title", ""))
        try:
            page = reader.get_destination_page_number(item) + 1
        except Exception:
            page = None
        yield {"level": level, "title": title, "page": page}


def resolve_object(value: Any) -> Any:
    return value.get_object() if hasattr(value, "get_object") else value


def audit_links(reader: PdfReader) -> dict[str, Any]:
    named = reader.named_destinations
    link_count = 0
    invalid: list[dict[str, Any]] = []
    kinds: Counter[str] = Counter()
    pages_with_links = 0
    for page_number, page in enumerate(reader.pages, start=1):
        page_links = 0
        for annotation_ref in page.get("/Annots", []):
            annotation = resolve_object(annotation_ref)
            if str(annotation.get("/Subtype")) != "/Link":
                continue
            link_count += 1
            page_links += 1
            destination = annotation.get("/Dest")
            if destination is not None:
                destination = resolve_object(destination)
                if isinstance(destination, str):
                    kinds["named"] += 1
                    if destination not in named:
                        invalid.append({"page": page_number, "destination": destination})
                else:
                    kinds["explicit"] += 1
                continue
            action = resolve_object(annotation.get("/A")) if annotation.get("/A") else None
            if action and str(action.get("/S")) == "/GoTo" and action.get("/D") is not None:
                kinds["goto"] += 1
            elif action and str(action.get("/S")) == "/URI":
                kinds["uri"] += 1
            else:
                kinds["unresolved"] += 1
                invalid.append({"page": page_number, "destination": None})
        if page_links:
            pages_with_links += 1
    return {
        "named_destination_count": len(named),
        "link_count": link_count,
        "pages_with_links": pages_with_links,
        "cover_without_links": not bool(reader.pages[0].get("/Annots", [])),
        "link_kind_counts": dict(kinds),
        "invalid_links": invalid,
    }


def audit_fonts(pdffonts: Path, pdf: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [str(pdffonts), str(pdf)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    records = []
    pattern = re.compile(
        r"^(?P<name>\S+)\s+.+?\s+(?P<embedded>yes|no)\s+"
        r"(?P<subset>yes|no)\s+(?P<unicode>yes|no)\s+"
        r"(?P<object>\d+\s+\d+)\s*$"
    )
    for line in completed.stdout.splitlines()[2:]:
        match = pattern.match(line.strip())
        if match:
            records.append(match.groupdict())
    return {
        "font_records": len(records),
        "all_embedded": bool(records) and all(row["embedded"] == "yes" for row in records),
        "all_subset": bool(records) and all(row["subset"] == "yes" for row in records),
        "all_unicode": bool(records) and all(row["unicode"] == "yes" for row in records),
        "records": records,
    }


def audit_log(log: Path) -> dict[str, int]:
    text = log.read_text(encoding="utf-8", errors="replace")
    patterns = {
        "fatal_or_emergency": r"Fatal error occurred|Emergency stop|^! ",
        "latex_or_package_error": r"LaTeX Error:|Package \S+ Error:",
        "undefined_control_reference_citation": r"Undefined control sequence|Reference .* undefined|Citation .* undefined|There were undefined references",
        "rerun": r"Rerun to get cross-references right|Label\(s\) may have changed",
        "over_underfull": r"(?:Over|Under)full \\[hv]box",
        "missing_character": r"Missing character:",
        "duplicate_destination": r"destination with the same identifier|duplicate destination",
        "font_not_found": r"Font .* not found",
    }
    return {
        name: len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))
        for name, pattern in patterns.items()
    }


def parse_index_log(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    scan = re.search(r"\((\d+) entries accepted, (\d+) rejected\)", text)
    generated = re.search(r"\((\d+) lines written, (\d+) warnings\)", text)
    if not scan or not generated:
        raise RuntimeError(f"Unrecognized makeindex log: {path}")
    return {
        "accepted": int(scan.group(1)),
        "rejected": int(scan.group(2)),
        "lines_written": int(generated.group(1)),
        "warnings": int(generated.group(2)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--main-index-log", required=True, type=Path)
    parser.add_argument("--symbols-index-log", required=True, type=Path)
    parser.add_argument("--pdffonts", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    reader = PdfReader(str(args.pdf))
    sizes = Counter(
        (round(float(page.mediabox.width), 3), round(float(page.mediabox.height), 3))
        for page in reader.pages
    )
    rotations = Counter(int(page.get("/Rotate", 0) or 0) for page in reader.pages)
    outline = list(flatten_outline(reader, reader.outline))
    levels = Counter(row["level"] for row in outline)
    chapters = [row for row in outline if re.match(r"第\d+章", row["title"])]
    volumes = [row for row in outline if re.match(r"第\d+册", row["title"])]
    root = resolve_object(reader.trailer["/Root"])
    names = resolve_object(root.get("/Names")) if root.get("/Names") else {}
    has_javascript = bool(names and names.get("/JavaScript"))
    fonts = audit_fonts(args.pdffonts, args.pdf)
    log_gates = audit_log(args.log)
    links = audit_links(reader)

    result = {
        "schema_version": 1,
        "pdf": str(args.pdf.resolve()),
        "pdf_bytes": args.pdf.stat().st_size,
        "pdf_sha256": sha256(args.pdf),
        "pdf_header": reader.pdf_header,
        "encrypted": reader.is_encrypted,
        "page_count": len(reader.pages),
        "page_size_counts": {f"{key[0]}x{key[1]}": value for key, value in sizes.items()},
        "rotation_counts": {str(key): value for key, value in rotations.items()},
        "javascript": has_javascript,
        "bookmark_count": len(outline),
        "bookmark_level_counts": {str(key): value for key, value in sorted(levels.items())},
        "chapter_bookmark_count": len(chapters),
        "chapter_numbers": [int(re.match(r"第(\d+)章", row["title"]).group(1)) for row in chapters],
        "volume_bookmark_count": len(volumes),
        "volume_numbers": [int(re.match(r"第(\d+)册", row["title"]).group(1)) for row in volumes],
        "required_bookmarks": {
            "符号索引": any(row["title"] == "符号索引" for row in outline),
            "主题索引": any(row["title"] == "主题索引" for row in outline),
        },
        "invalid_bookmarks": [row for row in outline if row["page"] is None],
        **links,
        **fonts,
        "log_bytes": args.log.stat().st_size,
        "log_sha256": sha256(args.log),
        "log_gates": log_gates,
        "main_index": parse_index_log(args.main_index_log),
        "symbols_index": parse_index_log(args.symbols_index_log),
    }
    result["result"] = "PASS" if all(
        [
            result["page_count"] == 817,
            result["page_size_counts"] == {"595.276x841.89": 817},
            result["rotation_counts"] == {"0": 817},
            not result["encrypted"],
            not result["javascript"],
            result["bookmark_count"] == 273,
            result["chapter_bookmark_count"] == 37,
            result["chapter_numbers"] == list(range(1, 38)),
            result["volume_bookmark_count"] == 5,
            result["volume_numbers"] == list(range(1, 6)),
            all(result["required_bookmarks"].values()),
            not result["invalid_bookmarks"],
            result["named_destination_count"] == 7421,
            result["link_count"] == 4961,
            not result["invalid_links"],
            result["font_records"] == 17,
            result["all_embedded"],
            result["all_subset"],
            result["all_unicode"],
            all(value == 0 for value in result["log_gates"].values()),
            result["main_index"]["accepted"] == 731,
            result["main_index"]["rejected"] == 0,
            result["main_index"]["warnings"] == 0,
            result["symbols_index"]["accepted"] == 355,
            result["symbols_index"]["rejected"] == 0,
            result["symbols_index"]["warnings"] == 0,
        ]
    ) else "FAIL"

    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
