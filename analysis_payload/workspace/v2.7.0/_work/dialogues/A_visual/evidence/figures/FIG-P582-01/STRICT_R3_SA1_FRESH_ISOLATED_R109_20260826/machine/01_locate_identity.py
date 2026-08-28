import hashlib
import json
from pathlib import Path

from pypdf import PdfReader


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf")
OUT = Path(__file__).with_name("01_locate_identity.json")
EXPECTED = {
    "bytes": 4_967_054,
    "pages": 817,
    "sha256": "936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9",
}
NEEDLES = [
    "固定样本序列",
    "运行均值",
    "曲线先降后升再下降",
    "收敛结论不等于逐步单调逼近",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


st = PDF.stat()
reader = PdfReader(str(PDF))
hits = []
for physical_page, page in enumerate(reader.pages, start=1):
    text = (page.extract_text() or "").replace("\x00", "")
    matched = [n for n in NEEDLES if n in text]
    if matched:
        normalized = " ".join(text.split())
        hits.append(
            {
                "physical_page": physical_page,
                "matched_needles": matched,
                "page_text": normalized,
            }
        )

observed = {"bytes": st.st_size, "pages": len(reader.pages), "sha256": sha256(PDF)}
strong = [
    h
    for h in hits
    if all(
        n in h["matched_needles"]
        for n in ("固定样本序列", "运行均值", "曲线先降后升再下降")
    )
]
result = {
    "scope": "fresh isolated independent page location on official R109",
    "pdf": str(PDF),
    "expected": EXPECTED,
    "observed": observed,
    "identity_match": observed == EXPECTED,
    "search_needles": NEEDLES,
    "hits": hits,
    "strong_match_rule": "all of: 固定样本序列, 运行均值, 曲线先降后升再下降",
    "strong_hits": strong,
    "unique_physical_page": strong[0]["physical_page"] if len(strong) == 1 else None,
    "location_pass": len(strong) == 1,
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: result[k] for k in ("observed", "identity_match", "unique_physical_page", "location_pass")}, ensure_ascii=False, indent=2))
