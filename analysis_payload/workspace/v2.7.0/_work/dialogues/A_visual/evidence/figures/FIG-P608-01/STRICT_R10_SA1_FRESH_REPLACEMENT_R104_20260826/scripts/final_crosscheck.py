from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R10_SA1_FRESH_REPLACEMENT_R104_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
TEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def ledger_time_check(path: Path, data: list[dict[str, str]]) -> dict:
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    violations = []
    maxima = []
    for n, row in enumerate(data, 2):
        values = [parse_time(row[k]) for k in ("opened_at", "observed_at", "decided_at") if row.get(k)]
        if not (values[0] <= values[1] <= values[2]):
            violations.append({"line": n, "kind": "order", "values": [x.isoformat() for x in values]})
        if max(values) > mtime:
            violations.append({"line": n, "kind": "manual_time_after_file_mtime"})
        maxima.append(max(values))
    return {
        "file": path.name,
        "rows": len(data),
        "max_manual_time_utc": max(maxima).isoformat().replace("+00:00", "Z"),
        "ledger_last_write_time_utc": mtime.isoformat().replace("+00:00", "Z"),
        "violations": violations,
        "pass": not violations,
    }


def main() -> None:
    summary = json.loads((ROOT / "machine" / "machine_summary.json").read_text(encoding="utf-8"))
    objects = rows(ROOT / "machine" / "object_manifest.csv")
    pairs = rows(ROOT / "machine" / "all_unordered_pairs.csv")
    glyph_machine = rows(ROOT / "machine" / "glyph_machine_ledger.csv")
    graphic_machine = rows(ROOT / "machine" / "graphic_path_ledger.csv")
    critical_machine = rows(ROOT / "machine" / "critical_pair_index.csv")
    manual_paths = [
        ROOT / "manual_view_ledger.csv",
        ROOT / "manual_glyph_ledger.csv",
        ROOT / "manual_graphic_ledger.csv",
        ROOT / "manual_pair_ledger.csv",
    ]
    manual_data = {p.name: rows(p) for p in manual_paths}
    time_checks = [ledger_time_check(p, manual_data[p.name]) for p in manual_paths]

    glyph_ids_machine = {x["element_id"] for x in glyph_machine}
    glyph_ids_manual = {x["element_id"] for x in manual_data["manual_glyph_ledger.csv"]}
    graphic_ids_machine = {x["element_id"] for x in graphic_machine}
    graphic_ids_manual = {x["element_id"] for x in manual_data["manual_graphic_ledger.csv"]}
    critical_ids_machine = {x["pair_id"] for x in critical_machine}
    critical_ids_manual = {x["pair_id"] for x in manual_data["manual_pair_ledger.csv"]}

    view_missing = [x["path"] for x in manual_data["manual_view_ledger.csv"] if not (ROOT / x["path"]).is_file()]
    critical_missing = []
    for row in critical_machine:
        for field in ["raw_1x", "a_mask_1x", "b_mask_1x", "intersection_1x", "overlay_1x", "overlay_8x_nearest"]:
            if not (ROOT / "rois" / row[field]).is_file():
                critical_missing.append({"pair_id": row["pair_id"], "field": field, "path": row[field]})

    expected_pairs = len(objects) * (len(objects) - 1) // 2
    manual_pair_hard_fails = [x["pair_id"] for x in manual_data["manual_pair_ledger.csv"] if x["decision"] == "HARD_FAIL_ILLEGAL_OVERLAP"]
    result_text = (ROOT / "RESULT.txt").read_text(encoding="utf-8")
    checks = {
        "pdf_hash_unchanged": sha(PDF) == summary["candidate_pdf_sha256"],
        "source_hash_unchanged": sha(TEX) == summary["source_tex_sha256"],
        "object_count_is_128": len(objects) == summary["object_count"] == 128,
        "pair_formula_closes": expected_pairs == 8128,
        "all_unordered_pair_rows_close": len(pairs) == expected_pairs,
        "glyph_manual_bijection": glyph_ids_machine == glyph_ids_manual and len(glyph_ids_manual) == 68,
        "graphic_manual_bijection": graphic_ids_machine == graphic_ids_manual and len(graphic_ids_manual) == 60,
        "critical_manual_bijection": critical_ids_machine == critical_ids_manual and len(critical_ids_manual) == 12,
        "manual_view_paths_exist": not view_missing and len(manual_data["manual_view_ledger.csv"]) == 16,
        "critical_evidence_six_views_each_exist": not critical_missing,
        "all_manual_timestamp_ledgers_close": all(x["pass"] for x in time_checks),
        "semantic_check_pass": bool(summary["semantic_pass"]),
        "hard_fail_pairs_recorded": set(manual_pair_hard_fails) == {"PAIR-06596", "PAIR-06650"},
        "result_matches_hard_fail": result_text.startswith("FAIL_TO_SA2"),
        "sa3_not_authorized": "SA3_AUTHORIZED=false" in result_text,
    }
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checks": checks,
        "crosscheck_pass": all(checks.values()),
        "manual_time_checks": time_checks,
        "manual_hard_fail_pairs": manual_pair_hard_fails,
        "manual_graphic_fail_count": sum(1 for x in manual_data["manual_graphic_ledger.csv"] if x["decision"].startswith("FAIL")),
        "manual_glyph_pass_count": sum(1 for x in manual_data["manual_glyph_ledger.csv"] if x["decision"] == "PASS"),
        "missing_view_paths": view_missing,
        "missing_critical_evidence": critical_missing,
    }
    (ROOT / "machine" / "final_crosscheck.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["crosscheck_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
