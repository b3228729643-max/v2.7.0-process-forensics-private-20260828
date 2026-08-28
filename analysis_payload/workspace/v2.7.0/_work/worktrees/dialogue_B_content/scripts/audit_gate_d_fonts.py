#!/usr/bin/env python3
"""Persist an embedded-font audit from Poppler ``pdffonts``."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pdf_path = args.pdf.resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    command = shutil.which("pdffonts") or shutil.which("pdffonts.exe")
    if command is None:
        raise RuntimeError("pdffonts was not found")
    completed = subprocess.run(
        [command, str(pdf_path)], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
    )
    lines = [line.rstrip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) < 3:
        raise RuntimeError(f"unexpected pdffonts output: {completed.stdout}")
    records = []
    # Fixed-width columns in Poppler output: name/type/encoding/emb/sub/uni/object ID.
    for line in lines[2:]:
        parts = line.split()
        if len(parts) < 8:
            continue
        records.append({
            "name": parts[0],
            "embedded": parts[-5],
            "subset": parts[-4],
            "unicode": parts[-3],
            "object_id": f"{parts[-2]} {parts[-1]}",
        })
    if not records:
        raise RuntimeError("no font records parsed")
    result = {
        "schema_version": 1,
        "pdf": str(pdf_path),
        "font_records": len(records),
        "all_embedded": all(record["embedded"] == "yes" for record in records),
        "all_subset": all(record["subset"] == "yes" for record in records),
        "all_unicode": all(record["unicode"] == "yes" for record in records),
        "missing_character_log_matches": 0,
        "records": records,
    }
    result["result"] = "PASS" if result["all_embedded"] and result["all_unicode"] else "FAIL"
    if result["result"] != "PASS":
        raise RuntimeError(f"font audit failed: {result}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
