"""Final, one-way sealing routine for FIG-P609-01 R1 SA1 evidence.

Order is intentionally fixed: integrity + report -> terminal -> manifests -> WRITE_STOPPED.
Do not run after WRITE_STOPPED exists.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_autocorrelation_ess.tex")
EXPECTED_PDF = "062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814"
EXPECTED_SOURCE = "20687D1EE01AABA9B605591A61781CF688328026E0645AD51B6E02E921DC98A2"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_csv(name: str):
    with (ROOT / name).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def all_files(exclude=frozenset()):
    return sorted(
        [p for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).as_posix() not in exclude],
        key=lambda p: p.relative_to(ROOT).as_posix().lower(),
    )


def validate_relative_references():
    missing = []
    scanned = 0
    csv_files = list(ROOT.glob("*.csv"))
    for csv_path in csv_files:
        with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                for key, value in row.items():
                    if not value:
                        continue
                    # Evidence-path cells carry explicit raster/file suffixes. Split only the
                    # documented pipe-separated calibration-path encoding.
                    if not (key.lower().endswith("path") or "evidence" in key.lower() or key.lower().endswith("1x") or key.lower().endswith("8")):
                        continue
                    for item in str(value).split("|"):
                        item = item.strip()
                        if not item or ("." not in item):
                            continue
                        candidate = Path(item)
                        if candidate.is_absolute():
                            target = candidate
                        else:
                            target = ROOT / item.replace("/", "\\")
                        scanned += 1
                        if not target.exists():
                            missing.append({"csv": csv_path.name, "field": key, "path": item})
    return scanned, missing


def validate():
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("WRITE_STOPPED already exists; sealing is immutable")
    if sha256(PDF) != EXPECTED_PDF:
        raise RuntimeError("candidate PDF hash changed")
    if sha256(SOURCE) != EXPECTED_SOURCE:
        raise RuntimeError("source hash changed")
    glyphs = read_csv("glyph_ledger.csv")
    pairs = read_csv("after_overlap_report.csv")
    critical = read_csv("critical_pair_manual_ledger.csv")
    rules = read_csv("math_rule_ledger.csv")
    accents = read_csv("math_accent_association_ledger.csv")
    clips = read_csv("clipping_audit.csv")
    objects = read_csv("object_inventory.csv")
    zorder = read_csv("z_order_occlusion_audit.csv")
    candidates = read_csv("manual_candidate_35_review.csv")
    cal = read_csv("manual_low_profile_calibration_audit.csv")
    views = read_csv("manual_global_view_audit.csv")
    harmony = read_csv("font_visual_harmony_audit.csv")
    assert len(glyphs) == 148
    assert len(pairs) == math.comb(59, 2) == 1711
    assert len(critical) == 40
    assert len(rules) == 2
    assert len(accents) == 5
    assert len(objects) == len(zorder) == 59
    assert len(candidates) == 35
    assert len(cal) == 17
    assert len(views) == 4
    assert len(harmony) == 5
    assert all(r["reviewer"] and r["decision"] and r["original_match"] and r["overlay_complete"] and r["mask_only_pure"] for r in glyphs)
    assert all(r["manual_reviewer"] and r["manual_decision"] and r["manual_note"] for r in critical)
    assert all(r["manual_reviewer"] and r["manual_decision"] for r in pairs)
    assert all(r["reviewer"] and r["decision"] for r in rules + accents + clips)
    assert all(r["opened"] == "YES" for r in views)
    assert all(r["decision"] == "FONT_VISUAL_HARMONY_PASS" for r in harmony)
    hard = [r for r in glyphs if r["decision"].startswith("FAIL_")]
    hard_ids = [r["glyph_id"] for r in hard]
    expected_hard = ["GL024", "GL026", "GL034", "GL045", "GL065", "GL072", "GL076", "GL088", "GL109"]
    assert hard_ids == expected_hard
    assert sum(1 for r in pairs if r["result"].startswith("FAIL")) == 0
    assert sum(1 for r in clips if r["pass"] != "True") == 0
    path_rows = read_csv("drawing_path_coverage.csv")
    assert len(path_rows) == 38
    assert sum(r["foreground"] == "True" and r["assignment"] == "MAPPED_FOREGROUND" for r in path_rows) == 36
    assert sum(r["foreground"] == "False" and r["assignment"] == "EXCLUDED_BACKGROUND_FILL" for r in path_rows) == 2
    scanned, missing = validate_relative_references()
    assert not missing, missing[:5]
    files_before_terminal = all_files()
    zero = [p.relative_to(ROOT).as_posix() for p in files_before_terminal if p.stat().st_size == 0]
    assert not zero, zero
    return {
        "candidate_pdf_sha256": EXPECTED_PDF,
        "source_sha256": EXPECTED_SOURCE,
        "physical_page": 659,
        "printed_page": 646,
        "figure_number": "32.9",
        "glyph_records": 148,
        "visible_glyphs": 144,
        "rawdict_combining_controls": 4,
        "hard_glyph_failures": hard_ids,
        "pair_objects": 59,
        "pair_denominator": 1711,
        "critical_pair_manual_rows": 40,
        "unwhitelisted_pair_failures": 0,
        "clip_failures": 0,
        "math_rules": 2,
        "accent_associations": 5,
        "drawing_path_rows": 38,
        "mapped_foreground_paths": 36,
        "excluded_background_paths": 2,
        "unassigned_foreground_paths": 0,
        "zorder_object_rows": 59,
        "font_visual_harmony": "FONT_VISUAL_HARMONY_PASS",
        "reference_paths_scanned": scanned,
        "missing_referenced_paths": missing,
        "zero_byte_files_pre_terminal": zero,
        "pre_terminal_file_count": len(files_before_terminal),
    }


def write_json(name: str, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(summary):
    report = f"""# FIG-P609-01 R97 independent SA1 final report

## Terminal result

`SA1_FAIL_ROUTE_SA2` / `FAIL_TO_SA2`.

No source, macro, build candidate, central state, inventory, or sibling evidence was modified. The conclusion is based only on the frozen R97 candidate, current figure source/direct context, and this isolated R1 evidence package.

## Identity and scope — PASS

- Candidate SHA-256: `{summary['candidate_pdf_sha256']}`; 813 physical pages.
- FIG-P609-01 / Fig. 32.9: physical page 659, printed page 646; aux label and fls input are recorded in `LOCATION_AUX_FLS_SOURCE_AUDIT.md`.
- Current source SHA-256: `{summary['source_sha256']}`.
- P609 scope is the strict native-300dpi rectangle `[291,2187,2125,2925]`; adjacent Fig. 32.8/caption/body are excluded.

## Glyph gate — HARD FAIL (route-determinative)

All 148 rawdict records were individually ledgered; 144 are visible reader glyphs and four are named zero-width combining controls. 13 native 8x glyph sheets and 35 individual candidate native 1x triplets were manually opened.

| Glyph | Observed gate | Result |
| --- | --- | --- |
| GL024 `=` | H_INK 12px vs 22px | hard fail |
| GL026 `⋯` | no eligible exact low-profile comparator for H/area `[0.92,1.08]` | hard evidence fail |
| GL034 `F` | H_INK 23px vs 24px | hard fail |
| GL045 `：` | no eligible exact low-profile comparator for H/area `[0.92,1.08]` | hard evidence fail |
| GL065 `=` | H_INK 12px vs 22px | hard fail |
| GL072 `=` | H_INK 11px vs 22px | hard fail |
| GL076 `−` | H_INK 3px vs 22px | hard fail |
| GL088 `=` | H_INK 12px vs 22px | hard fail |
| GL109 `=` | H_INK 12px vs 22px | hard fail |

Each listed target has a pure native mask and a human note in `glyph_ledger.csv`; purity does not cure an under-threshold glyph or a missing independent calibration. In particular, no source point-size or D/E visual result is substituted for the native hard pixel gate.

## Other required gates — PASS, but non-curative

- Objects/pairs: 59 visible foreground objects, all `59C2=1711` unordered pairs enumerated. 40 critical/contact rows have actual native review. Unwhitelisted-pair failures: 0. Seven tick–stem, seven axis–stem, and seven stem–marker relations are each source-anchored at their individual `k=0…6` coordinates; no category blanket exemption was used.
- Math/path: 2 independent `GRAPHIC/MATH_RULE` objects, 5 accent associations, 36 mapped foreground drawing paths plus 2 explicitly excluded background fills, and zero unassigned foreground paths. Rules/accents are manually reviewed in their separate cards.
- Clip/crop: all object rows pass; the three 20px crop-proximity cards were manually opened. No clip failure.
- Z-order/occlusion: 59 object rows audited; no unintended hiding or line-through-text. Expected construction contacts remain only in the named pair ledger.
- D/E and visual coordination: source effective roles are 9.6pt tick/annotation/formula, 9.8pt axis label, 10.4pt title; same-role/same-panel and cross-panel checks pass. Manual global 200dpi / native crop 300dpi / standalone 300dpi / grayscale 300dpi review records `FONT_VISUAL_HARMONY_PASS` and grayscale readability.

The pair, clipping, z-order, global-view, grayscale, D/E, and font-harmony passes do **not** offset any of the nine glyph hard failures. The only permitted SA1 routing is therefore `FAIL_TO_SA2`.

## Evidence completeness

- Referenced evidence paths checked: {summary['reference_paths_scanned']}; missing: 0.
- Pre-terminal zero-byte files: 0; non-default ADS check: 0 (recorded before sealing).
- Manifest procedure and self-exclusion rationale are recorded in `evidence_manifest.json`; `WRITE_STOPPED` is written last and intentionally is not inside the immutable manifest snapshot.
"""
    (ROOT / "SA1_FINAL_REPORT.md").write_text(report, encoding="utf-8")


def write_terminal(summary):
    content = f"""# SA1 terminal decision — FIG-P609-01

terminal_status: `SA1_FAIL_ROUTE_SA2`
route: `FAIL_TO_SA2`
reason: Nine independently human-confirmed glyph hard failures in `glyph_ledger.csv` ({', '.join(summary['hard_glyph_failures'])}).

This terminal is final for the isolated R1 evidence package. The passing pair/clip/path/z-order/D-E/global/gray gates are documented but non-curative.
"""
    (ROOT / "SA1_TERMINAL_DECISION.md").write_text(content, encoding="utf-8")


def write_manifests():
    # First manifest covers every evidence artifact present before either manifest exists.
    excluded = {"MANIFEST.sha256", "evidence_manifest.json", "WRITE_STOPPED"}
    pre_manifest = all_files(excluded)
    lines = [f"{sha256(path)} *{path.relative_to(ROOT).as_posix()}" for path in pre_manifest]
    (ROOT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # JSON manifest additionally covers MANIFEST.sha256 itself; only its own byte stream is
    # necessarily excluded. WRITE_STOPPED is later by protocol and is likewise excluded.
    json_files = all_files({"evidence_manifest.json", "WRITE_STOPPED"})
    data = {
        "uid": "FIG-P609-01",
        "package_root": str(ROOT),
        "manifest_algorithm": "SHA-256",
        "terminal_status": "SA1_FAIL_ROUTE_SA2",
        "route": "FAIL_TO_SA2",
        "file_entries": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in json_files
        ],
        "file_entry_count": len(json_files),
        "self_excluded": "evidence_manifest.json cannot hash its own final byte stream",
        "post_manifest_excluded": "WRITE_STOPPED is deliberately created last by protocol",
        "manifest_sha256": sha256(ROOT / "MANIFEST.sha256"),
    }
    write_json("evidence_manifest.json", data)
    return len(pre_manifest), len(json_files), sha256(ROOT / "MANIFEST.sha256"), sha256(ROOT / "evidence_manifest.json")


def main():
    summary = validate()
    manual_summary_path = ROOT / "manual_review_summary.json"
    manual_summary = json.loads(manual_summary_path.read_text(encoding="utf-8"))
    manual_summary["manual_final_status"] = "SA1_FAIL_ROUTE_SA2_FINAL__9_GLYPH_HARD_FAILURES"
    manual_summary["terminal_file"] = "SA1_TERMINAL_DECISION.md"
    manual_summary_path.write_text(json.dumps(manual_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # All material evidence/report files exist before the terminal is written.
    write_json("EVIDENCE_INTEGRITY_AUDIT.json", summary)
    write_report(summary)
    # Required order point: final report/integrity first, terminal next.
    write_terminal(summary)
    manifest_pre, manifest_json, manifest_sha, json_sha = write_manifests()
    # Required last write. Do not append to any evidence after this call.
    marker = (
        "WRITE_STOPPED\n"
        "uid=FIG-P609-01\n"
        "terminal_status=SA1_FAIL_ROUTE_SA2\n"
        "route=FAIL_TO_SA2\n"
        f"manifest_entries={manifest_json}\n"
        f"manifest_sha256={manifest_sha}\n"
        f"evidence_manifest_sha256={json_sha}\n"
    )
    (ROOT / "WRITE_STOPPED").write_text(marker, encoding="utf-8")
    print(json.dumps({
        "terminal_status": "SA1_FAIL_ROUTE_SA2",
        "route": "FAIL_TO_SA2",
        "pre_manifest_entries": manifest_pre,
        "evidence_manifest_entries": manifest_json,
        "manifest_sha256": manifest_sha,
        "evidence_manifest_sha256": json_sha,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
