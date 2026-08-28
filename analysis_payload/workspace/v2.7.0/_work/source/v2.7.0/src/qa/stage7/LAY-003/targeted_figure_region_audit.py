from __future__ import annotations

import json
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "build-output" / "volume5" / "main.pdf"
TARGETS = (
    {"page": 177, "y0": 120.0, "y1": 370.0, "figure": "图8.4"},
    {"page": 180, "y0": 220.0, "y1": 470.0, "figure": "图8.5"},
)


def main() -> None:
    document = fitz.open(PDF)
    reports = []
    for target in TARGETS:
        spans = []
        page = document[target["page"] - 1]
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    y = span["bbox"][1]
                    if text and target["y0"] <= y <= target["y1"]:
                        spans.append(span)
        minimum = min(float(span["size"]) for span in spans)
        reports.append(
            {
                **target,
                "visible_spans": len(spans),
                "minimum_font_pt": round(minimum, 3),
                "spans_below_8_5pt": sum(float(span["size"]) < 8.5 for span in spans),
                "passed": minimum >= 8.5,
            }
        )
    print(json.dumps({"pdf": str(PDF), "reports": reports}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
