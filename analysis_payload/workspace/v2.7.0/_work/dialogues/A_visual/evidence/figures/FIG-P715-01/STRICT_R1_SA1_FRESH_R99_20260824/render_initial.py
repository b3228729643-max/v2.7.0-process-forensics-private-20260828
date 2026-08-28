from pathlib import Path
import hashlib
import json

import fitz


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r99_fullbook\main_full.pdf")
PRINTED_PAGE = 750
CAPTION_FRAGMENT = "列随机约定下的网页有向图"


def main() -> None:
    digest = hashlib.sha256(PDF.read_bytes()).hexdigest().upper()
    doc = fitz.open(PDF)
    matches = []
    for index, candidate_page in enumerate(doc):
        text = candidate_page.get_text("text")
        if CAPTION_FRAGMENT in text:
            matches.append(index + 1)
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one current-R99 caption match, got {matches}")
    page_number = matches[0]
    page = doc[page_number - 1]
    out = {
        "candidate": str(PDF),
        "candidate_sha256": digest,
        "physical_page": page_number,
        "printed_page_from_aux": PRINTED_PAGE,
        "task_card_physical_page_claim": 826,
        "page_count": len(doc),
        "page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
        "rendering": {
            "full_page_200dpi": "full_page_200dpi.png",
            "full_page_300dpi": f"page_{page_number:03d}_300dpi.png",
        },
    }
    page.get_pixmap(dpi=200, alpha=False).save(OUT / "full_page_200dpi.png")
    page.get_pixmap(dpi=300, alpha=False).save(OUT / f"page_{page_number:03d}_300dpi.png")
    (OUT / "candidate_identity.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
