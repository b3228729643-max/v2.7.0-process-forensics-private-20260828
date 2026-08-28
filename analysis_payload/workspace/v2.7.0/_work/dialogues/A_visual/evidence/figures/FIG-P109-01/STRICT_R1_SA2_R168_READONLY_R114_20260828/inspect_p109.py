from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R1_SA2_R168_READONLY_R114_20260828")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
EXPECTED_BYTES = 4_967_122
EXPECTED_SHA256 = "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6"
NEEDLE = "凸集中任意两点的线段仍位于可行域内"


def identity() -> dict[str, object]:
    data = PDF.read_bytes()
    result = {
        "path": str(PDF),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
    }
    if result["bytes"] != EXPECTED_BYTES or result["sha256"] != EXPECTED_SHA256:
        raise RuntimeError(f"PDF identity mismatch: {result}")
    return result


def render(page_index: int, dpi: int, name: str) -> None:
    document = pdfium.PdfDocument(str(PDF))
    page = document[page_index]
    bitmap = page.render(scale=dpi / 72.0)
    image = bitmap.to_pil()
    image.save(ROOT / name, dpi=(dpi, dpi))
    bitmap.close()
    page.close()
    document.close()


def main() -> None:
    pdf_identity = identity()
    matches: list[dict[str, object]] = []
    with pdfplumber.open(PDF) as doc:
        page_count = len(doc.pages)
        for index, page in enumerate(doc.pages):
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            normalized = "".join(text.split())
            if NEEDLE in normalized:
                words = page.extract_words(
                    x_tolerance=2,
                    y_tolerance=2,
                    keep_blank_chars=False,
                    use_text_flow=True,
                )
                matches.append(
                    {
                        "page_index_zero_based": index,
                        "physical_page_one_based": index + 1,
                        "width_pt": page.width,
                        "height_pt": page.height,
                        "matching_words": [
                            word
                            for word in words
                            if any(fragment in word["text"] for fragment in ("凸集", "任意", "线段", "可行域"))
                        ],
                    }
                )
        if len(matches) != 1:
            raise RuntimeError(f"Expected one current-PDF caption match, found {len(matches)}: {matches}")
        target = matches[0]
        page = doc.pages[int(target["page_index_zero_based"])]
        text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
        chars = []
        for char in page.chars:
            if char.get("text", "").strip():
                chars.append(
                    {
                        "text": char.get("text", ""),
                        "x0": round(float(char["x0"]), 3),
                        "x1": round(float(char["x1"]), 3),
                        "top": round(float(char["top"]), 3),
                        "bottom": round(float(char["bottom"]), 3),
                        "fontname": char.get("fontname"),
                        "size": round(float(char.get("size", 0.0)), 3),
                    }
                )
        geometry = {
            "pdf_identity": pdf_identity,
            "page_count": page_count,
            "needle": NEEDLE,
            "matches": matches,
            "target_page_nonblank_chars": chars,
            "target_page_lines": page.lines,
            "target_page_rects": page.rects,
            "target_page_curves": page.curves,
        }
    (ROOT / "locator.json").write_text(json.dumps(geometry, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "target_page_text.txt").write_text(text, encoding="utf-8")
    page_index = int(matches[0]["page_index_zero_based"])
    render(page_index, 200, "full_page_200dpi.png")
    render(page_index, 300, "full_page_native300dpi.png")
    print(json.dumps({"page_count": page_count, "matches": matches}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
