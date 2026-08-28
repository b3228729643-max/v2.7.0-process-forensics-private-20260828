from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R11A_SA2_P4_COORDINATE_DIRECT_BUILD_R113_20260827")
PDF = ROOT / "build" / "v260_FIG-P067-01_standalone.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
FROZEN_IMPLEMENTATION = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R9_SA3_FRESH_ISOLATED_R113_20260827\scripts\build_machine_evidence.py")
EXPECTED_IMPLEMENTATION_SHA256 = "39551817E1867E024395303BA2976D99DC8C510A9C79BE2B7B42DD54F8419BB1"
EXPECTED_PDF_SHA256 = "586EFE2C968A05C014A9AD8D639A8CFF0EDD0B21306CA31183485A7C75A338A1"
EXPECTED_SOURCE_SHA256 = "11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one replacement for {old!r}, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if sha256(PDF) != EXPECTED_PDF_SHA256:
        raise RuntimeError("R11A PDF identity mismatch")
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("R11A source identity mismatch")
    implementation_sha = sha256(FROZEN_IMPLEMENTATION)
    if implementation_sha != EXPECTED_IMPLEMENTATION_SHA256:
        raise RuntimeError(f"Frozen machine implementation mismatch: {implementation_sha}")

    render_dir = ROOT / "02_render"
    render_dir.mkdir(parents=True, exist_ok=True)
    with fitz.open(PDF) as document:
        if len(document) != 1:
            raise RuntimeError("R11A standalone PDF must contain exactly one page")
        pixmap = document[0].get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False)
        pixmap.save(render_dir / "page_001_300dpi.png")
    Image.open(render_dir / "page_001_300dpi.png").convert("L").save(render_dir / "page_001_gray_300dpi.png")

    old_root = r'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R9_SA3_FRESH_ISOLATED_R113_20260827'
    old_pdf = r'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf'
    old_source = r'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex'

    patched = FROZEN_IMPLEMENTATION.read_text(encoding="utf-8")
    replacements = [
        (f'ROOT = Path(r"{old_root}")', f'ROOT = Path(r"{ROOT}")'),
        (f'PDF = Path(r"{old_pdf}")', f'PDF = Path(r"{PDF}")'),
        (f'SOURCE = Path(r"{old_source}")', f'SOURCE = Path(r"{SOURCE}")'),
        ('PAGE_NUMBER = 69', 'PAGE_NUMBER = 1'),
        ('EXPECTED_PDF_SHA256 = "6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D"', f'EXPECTED_PDF_SHA256 = "{EXPECTED_PDF_SHA256}"'),
        ('EXPECTED_SOURCE_SHA256 = "2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920"', f'EXPECTED_SOURCE_SHA256 = "{EXPECTED_SOURCE_SHA256}"'),
        ('"role": "SA3_FRESH_ISOLATED"', '"role": "SA2_LOCAL_EVIDENCE"'),
        ('"agent_identity": "/root/p067_r113_fresh_sa3"', '"agent_identity": "/root"'),
        ('"handoff_id": "A-R113-P067-SA3-FRESH-ISOLATED-20260827"', '"handoff_id": "A-R113-P067-SA2-DIRECT-BUILD-R11A-20260827"'),
        ('"official_round": "R113"', '"official_round": "R113_R11A_STANDALONE"'),
        ('"printed_page": 56', '"printed_page": 1'),
        ('"page_069_300dpi.png"', '"page_001_300dpi.png"'),
        ('"page_069_gray_300dpi.png"', '"page_001_gray_300dpi.png"'),
    ]
    for old, new in replacements:
        patched = replace_once(patched, old, new)
    if old_root in patched or old_pdf in patched or old_source in patched:
        raise RuntimeError("Patched implementation still contains an old output/input path")

    namespace = {"__name__": "p067_r11a_machine_exec", "__file__": str(FROZEN_IMPLEMENTATION)}
    exec(compile(patched, str(FROZEN_IMPLEMENTATION), "exec"), namespace)

    provenance = {
        "implementation_path": str(FROZEN_IMPLEMENTATION),
        "implementation_bytes": FROZEN_IMPLEMENTATION.stat().st_size,
        "implementation_sha256": implementation_sha,
        "runtime_replacements": len(replacements),
        "manual_fields_generated_or_overwritten": 0,
        "input_pdf": str(PDF),
        "input_pdf_sha256": EXPECTED_PDF_SHA256,
        "input_source": str(SOURCE),
        "input_source_sha256": EXPECTED_SOURCE_SHA256,
        "output_root": str(ROOT),
    }
    (ROOT / "07_validation" / "MACHINE_TOOLING_PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
