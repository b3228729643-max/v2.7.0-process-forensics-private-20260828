from __future__ import annotations

import argparse
from pathlib import Path
import sys

import fitz


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="List PDF text spans with stable indices and vector bboxes."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, default=1, help="One-based page number")
    args = parser.parse_args()

    with fitz.open(args.pdf) as document:
        page = document[args.page - 1]
        payload = page.get_text("dict")
        index = 0
        for block in payload["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    index += 1
                    bbox = ",".join(f"{value:.3f}" for value in span["bbox"])
                    text = span["text"].replace("\t", "\\t").replace("\n", "\\n")
                    print(
                        f"{index:03d}\t{span['size']:.4f}\t{span['font']}\t"
                        f"{bbox}\t{text}"
                    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
