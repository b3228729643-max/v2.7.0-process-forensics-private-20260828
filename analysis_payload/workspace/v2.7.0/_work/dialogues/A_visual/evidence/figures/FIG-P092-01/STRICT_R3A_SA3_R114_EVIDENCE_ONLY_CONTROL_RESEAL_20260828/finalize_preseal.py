from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence"
    r"\figures\FIG-P092-01\STRICT_R3_SA3_FRESH_ISOLATED_R114_20260828"
)
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r114_fullbook\main_full.pdf"
)
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码"
    r"\第01册_数学基础与统计学习基本理论\V1-C06\fig_v1_c06_binary_entropy.tex"
)
HANDOFF_ID = "A-R114-P092-SA3-FRESH-ISOLATED-20260828"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def csv_rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    expected_pdf = (4_967_122, "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6")
    expected_source = (2_094, "EA3FB7B92ED3B7B2755D513B5F3DEECF7D7114E8DC711F3AB2FE50E9C7EE8608")
    assert (PDF.stat().st_size, sha256(PDF)) == expected_pdf
    assert (SOURCE.stat().st_size, sha256(SOURCE)) == expected_source

    objects = csv_rows("manual_element_ledger.csv")
    pairs = csv_rows("manual_pair_ledger.csv")
    views = csv_rows("manual_view_ledger.csv")
    math_rows = csv_rows("manual_math_ledger.csv")
    semantic_rows = csv_rows("manual_semantic_ledger.csv")
    mechanical_pairs = csv_rows("pair_registry_mechanical.csv")

    ids = [f"E{i:02d}" for i in range(1, 14)]
    expected_pairs = list(itertools.combinations(ids, 2))
    assert [row["element_id"] for row in objects] == ids
    assert all(row["manual_reviewer"] == HANDOFF_ID for row in objects)
    assert all(row["manual_verdict"] == "PASS" for row in objects)
    assert len(pairs) == len(expected_pairs) == 78
    assert [(row["element_a"], row["element_b"]) for row in pairs] == expected_pairs
    assert [(row["element_a"], row["element_b"]) for row in mechanical_pairs] == expected_pairs
    assert all(row["manual_reviewer"] == HANDOFF_ID for row in pairs)
    assert all(row["manual_verdict"] == "CLEAR" for row in pairs)
    assert len(views) == 11 and all(row["opened"] == "true" and row["manual_verdict"] == "PASS" for row in views)
    assert len(math_rows) == 6 and all(row["manual_verdict"] == "PASS" for row in math_rows)
    assert len(semantic_rows) == 8 and all(row["manual_verdict"] == "PASS" for row in semantic_rows)
    assert all(row["manual_reviewer"] == HANDOFF_ID for row in views + math_rows + semantic_rows)

    handoff = json.loads((ROOT / "HANDOFF.json").read_text(encoding="utf-8"))
    assert handoff["handoff_id"] == HANDOFF_ID
    assert handoff["canonical_instance"] == "/root/p092_r114_fresh_sa3"
    assert handoff["reader_visible_denominator"] == 13
    assert handoff["unordered_pair_denominator"] == 78
    assert handoff["outcome"] == "SA3_PASS_AWAIT_MAIN_A_LOCAL_PASS_ACCEPTANCE"

    required_views = [
        "full_page_200dpi.png",
        "official_pdf_native_full_page_300dpi.png",
        "official_pdf_figure_crop_300dpi.png",
        "official_pdf_figure_crop_grayscale_300dpi.png",
        "object_overlay_300dpi.png",
        "critical_peak_and_symmetry_native1x.png",
        "critical_peak_and_symmetry_nearest8x.png",
        "critical_left_endpoint_native1x.png",
        "critical_left_endpoint_nearest8x.png",
        "critical_right_endpoint_native1x.png",
        "critical_right_endpoint_nearest8x.png",
    ]
    assert all((ROOT / name).is_file() for name in required_views)
    assert not (ROOT / "WSTOP").exists()

    audit = {
        "handoff_id": HANDOFF_ID,
        "canonical_instance": "/root/p092_r114_fresh_sa3",
        "figure_uid": "FIG-P092-01",
        "pdf_identity_match": True,
        "source_identity_match": True,
        "manual_element_rows": len(objects),
        "manual_pair_rows": len(pairs),
        "mechanical_pair_rows": len(mechanical_pairs),
        "manual_view_rows": len(views),
        "manual_math_rows": len(math_rows),
        "manual_semantic_rows": len(semantic_rows),
        "all_manual_reviewer_ids_exact": True,
        "all_manual_verdicts_pass_or_clear": True,
        "required_views_present": True,
        "wstop_absent_before_seal": True,
        "result": "PASS",
        "outcome": "SA3_PASS_AWAIT_MAIN_A_LOCAL_PASS_ACCEPTANCE",
    }
    (ROOT / "PRESEAL_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest_path = ROOT / "MANIFEST.sha256.csv"
    files = sorted(path for path in ROOT.iterdir() if path.is_file() and path != manifest_path)
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["relative_path", "bytes", "sha256"])
        writer.writeheader()
        for path in files:
            writer.writerow({"relative_path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})


if __name__ == "__main__":
    main()
