from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pdfplumber


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R4_SA1_FRESH_ISOLATED_R112_20260827")
TARGETS = (
    "离散随机变量的分布函数",
    "跳跃高度等于对应点的概率质量",
    "右连续：实心点取跳后值",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    matches: list[dict[str, object]] = []
    with pdfplumber.open(PDF) as doc:
        for page_index, page in enumerate(doc.pages):
            text = page.extract_text() or ""
            compact = "".join(text.split())
            found = [needle for needle in TARGETS if "".join(needle.split()) in compact]
            if found:
                relevant_words = []
                for word in page.extract_words(x_tolerance=2, y_tolerance=2):
                    if any(key in word["text"] for key in ("分布", "跳跃", "右连续", "概率", "质量")):
                        relevant_words.append(
                            {
                                "bbox_pt": [
                                    round(word["x0"], 3),
                                    round(word["top"], 3),
                                    round(word["x1"], 3),
                                    round(word["bottom"], 3),
                                ],
                                "text": word["text"],
                            }
                        )
                matches.append(
                    {
                        "page_index_0based": page_index,
                        "physical_page_1based": page_index + 1,
                        "page_rect_pt": [0.0, 0.0, round(page.width, 3), round(page.height, 3)],
                        "matched_needles": found,
                        "relevant_words": relevant_words,
                        "extracted_text": text,
                    }
                )
        page_count = len(doc.pages)
    record = {
        "pdf": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "page_count": page_count,
        "search_targets": list(TARGETS),
        "match_count": len(matches),
        "matches": matches,
    }
    (ROOT / "localization_candidates.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
