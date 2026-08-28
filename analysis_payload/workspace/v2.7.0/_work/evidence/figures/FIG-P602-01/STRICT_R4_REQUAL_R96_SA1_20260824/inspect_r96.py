from __future__ import annotations

import json
from pathlib import Path

import fitz


ROOT = Path.cwd()
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r96_fullbook" / "main_full.pdf"
PAGE_INDEX = 650  # Physical page 651, zero based for PyMuPDF.


def main() -> None:
    document = fitz.open(PDF)
    page = document[PAGE_INDEX]
    raw = page.get_text("rawdict")
    lines = []
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            spans = line["spans"]
            text = "".join(char["c"] for span in spans for char in span["chars"])
            x0 = min(span["bbox"][0] for span in spans)
            y0 = min(span["bbox"][1] for span in spans)
            x1 = max(span["bbox"][2] for span in spans)
            y1 = max(span["bbox"][3] for span in spans)
            lines.append(
                {
                    "bbox_pt": [x0, y0, x1, y1],
                    "text": text,
                    "spans": [
                        {
                            "bbox_pt": span["bbox"],
                            "font": span["font"],
                            "size_pt": span["size"],
                            "flags": span["flags"],
                            "text": "".join(char["c"] for char in span["chars"]),
                        }
                        for span in spans
                    ],
                }
            )
    selected = [line for line in lines if 320 <= line["bbox_pt"][1] <= 760]
    print(json.dumps({"page_rect_pt": list(page.rect), "lines": selected}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
