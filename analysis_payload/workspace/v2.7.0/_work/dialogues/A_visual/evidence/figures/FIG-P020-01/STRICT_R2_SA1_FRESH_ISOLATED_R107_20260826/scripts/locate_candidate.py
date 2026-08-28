from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R2_SA1_FRESH_ISOLATED_R107_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C01\fig_v1_c01_language_flow.tex")
CAPTION_KEY = "数学语言从对象声明到任务陈述的依赖关系"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    doc = fitz.open(PDF)
    matches: list[dict[str, object]] = []
    for index in range(doc.page_count):
        page = doc[index]
        text = page.get_text("text", sort=True)
        compact = "".join(text.split())
        if CAPTION_KEY in compact:
            matches.append(
                {
                    "physical_page_1based": index + 1,
                    "page_index_0based": index,
                    "page_label": page.get_label(),
                    "page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
                    "rotation": page.rotation,
                    "text": text,
                }
            )

    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one caption match, found {len(matches)}")

    match = matches[0]
    page = doc[int(match["page_index_0based"])]
    raw = page.get_text("rawdict", sort=True)
    for block in raw.get("blocks", []):
        if block.get("type") == 1:
            block.pop("image", None)
    drawings = page.get_drawings(extended=True)

    identity = {
        "handoff_id": "A-R107-P020-SA1-FRESH-ISOLATED-20260826",
        "role": "SA1",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "canonical_uid": "FIG-P020-01",
        "official_round": "R107",
        "official_pdf": str(PDF),
        "official_pdf_bytes": PDF.stat().st_size,
        "official_pdf_sha256": sha256(PDF),
        "source_file": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "pdf_page_count": doc.page_count,
        "caption_search_key": CAPTION_KEY,
        "caption_match_count": len(matches),
        "physical_page_1based": match["physical_page_1based"],
        "page_index_0based": match["page_index_0based"],
        "page_label": match["page_label"],
        "page_rect_pt": match["page_rect_pt"],
        "page_rotation": match["rotation"],
        "isolation_statement": "Located independently from the official R107 PDF caption and current source; no prior P020 evidence or conclusion was read.",
    }

    (ROOT / "00_identity" / "input_identity.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "00_identity" / "located_page_text.txt").write_text(
        str(match["text"]), encoding="utf-8"
    )
    (ROOT / "02_extraction" / "page_rawdict.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "02_extraction" / "page_drawings.json").write_text(
        json.dumps(drawings, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(identity, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
