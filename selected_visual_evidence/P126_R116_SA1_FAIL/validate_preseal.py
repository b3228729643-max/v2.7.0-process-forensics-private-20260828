from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUTS = {
    "pdf": (
        Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r116_fullbook\main_full.pdf"),
        4_967_281,
        "19F3D0413AD8C72B4D855B2C23246F10DD7ACECF2FD1E984AEE9F25E1051D3DC",
    ),
    "figure_tex": (
        Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex"),
        4_686,
        "2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405",
    ),
    "chapter_tex": (
        Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C08.tex"),
        59_218,
        "3C60FABCACA8BFC390323033F3CF6539CA5497EBF5A09641B8C4B78E81A0816C",
    ),
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    objects = read_csv("manual_object_ledger.csv")
    pairs = read_csv("manual_pair_ledger.csv")
    machine_pairs = read_csv("machine_unordered_pairs.csv")
    glyphs = read_csv("manual_glyph_codepoint_ledger.csv")
    math_rows = read_csv("manual_math_ledger.csv")
    geometry = read_csv("manual_geometry_ledger.csv")
    semantics = read_csv("manual_semantic_ledger.csv")
    pages = read_csv("manual_page_ledger.csv")
    views = read_csv("manual_view_ledger.csv")
    rois = read_csv("machine_critical_rois.csv")
    defects = read_csv("hard_defects.csv")

    require(len(objects) == 38 and len({r["object_id"] for r in objects}) == 38, "object ledger")
    require({r["object_id"] for r in objects if r["manual_result"] == "FAIL"} == {"O003", "O006", "O015", "O020"}, "object failures")
    require(len(pairs) == 703 and len({r["pair_id"] for r in pairs}) == 703, "pair ledger")
    require([r["pair_id"] for r in pairs] == [r["pair_id"] for r in machine_pairs], "pair ID order/map")
    require({r["pair_id"] for r in pairs if r["manual_result"] == "FAIL"} == {"PAIR-0085", "PAIR-0189"}, "pair failures")
    require(all(r["manual_result"] in {"PASS", "FAIL"} for r in pairs), "pair verdict blanks")
    require(len(glyphs) == 14 and all(r["manual_result"] == "PASS" for r in glyphs), "glyph ledger")
    require(len(math_rows) == 7 and all(r["manual_result"] == "PASS" for r in math_rows), "math ledger")
    require(len(geometry) == 14 and {r["geometry_check_id"] for r in geometry if r["manual_result"] == "FAIL"} == {"G011"}, "geometry ledger")
    require(len(semantics) == 10 and all(r["manual_result"] == "PASS" for r in semantics), "semantic ledger")
    require(len(pages) == 1 and pages[0]["manual_result"] == "FAIL", "page ledger")
    require(len(views) == 33 and all(r["opened"] == "true" for r in views), "view ledger")
    require(len(rois) == 13, "ROI ledger")
    require(len(defects) == 2 and {r["pair_id"] for r in defects} == {"PAIR-0085", "PAIR-0189"}, "hard defects")
    require("Verdict: **FAIL**" in (ROOT / "SA1_MANUAL_VERDICT.md").read_text(encoding="utf-8"), "manual verdict")
    require("A-R116-P126-SA1-FRESH-ISOLATED-20260828" in (ROOT / "SA1_MANUAL_VERDICT.md").read_text(encoding="utf-8"), "handoff identity")

    missing_views = []
    for row in views:
        if not (ROOT / row["file"]).is_file():
            missing_views.append(row["file"])
    require(not missing_views, f"missing opened views: {missing_views}")

    missing_roi_files = []
    for row in rois:
        for key in ("native1x_file", "nearest8x_file"):
            if not (ROOT / row[key]).is_file():
                missing_roi_files.append(row[key])
    require(not missing_roi_files, f"missing ROI files: {missing_roi_files}")
    require(not (ROOT / "WSTOP").exists(), "premature WSTOP")

    identity = {}
    for name, (path, expected_size, expected_hash) in INPUTS.items():
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        require(actual_size == expected_size, f"{name} size")
        require(actual_hash == expected_hash, f"{name} hash")
        identity[name] = {
            "path": str(path),
            "size": actual_size,
            "sha256": actual_hash,
            "size_match": True,
            "hash_match": True,
        }

    report = {
        "checked_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "canonical_instance": "/root/p126_r116_fresh_sa1",
        "handoff_id": "A-R116-P126-SA1-FRESH-ISOLATED-20260828",
        "figure_id": "FIG-P126-01",
        "pdf_physical_page": 137,
        "candidate_identity": identity,
        "manual_counts": {
            "objects": 38,
            "unordered_pairs": 703,
            "glyph_codepoint": 14,
            "math": 7,
            "geometry": 14,
            "semantic": 10,
            "page": 1,
            "views_opened": 33,
            "critical_rois_native1x_plus_nearest8x": 13,
        },
        "hard_defect_count": 2,
        "hard_pair_ids": ["PAIR-0085", "PAIR-0189"],
        "verdict": "FAIL",
        "premature_wstop": False,
        "seal_ready": True,
    }
    (ROOT / "preseal_control_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    rows = []
    for path in sorted(ROOT.iterdir(), key=lambda p: p.name.casefold()):
        if path.name in {"premarker_manifest.csv", "WSTOP"}:
            continue
        require(path.is_file(), f"unexpected directory before seal: {path.name}")
        rows.append({"name": path.name, "size": path.stat().st_size, "kind": "file"})
    with (ROOT / "premarker_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "size", "kind"])
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps(report, ensure_ascii=False))
    print(f"premarker_manifest_entries={len(rows)}")


if __name__ == "__main__":
    main()
