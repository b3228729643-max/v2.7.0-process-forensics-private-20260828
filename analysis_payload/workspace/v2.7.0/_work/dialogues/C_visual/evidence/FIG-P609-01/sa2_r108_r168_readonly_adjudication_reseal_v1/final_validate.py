import csv
import hashlib
import json
import os
from pathlib import Path

import fitz


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa2_r108_r168_readonly_adjudication_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_autocorrelation_ess.tex")
EXPECTED_EXCLUSIONS = ["evidence_manifest.json", "SEAL.json", "WRITE_STOPPED"]
EXPECTED_DECISION = "P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(name: str):
    with (ROOT / name).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def load_csv(name: str):
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


assert ROOT.is_dir() and not ROOT.is_symlink()
assert not (ROOT / "WRITE_STOPPED").exists(), "WRITE_STOPPED must be created only after this validation"
assert PDF.stat().st_size == 4_967_161
assert sha256(PDF) == "C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78"
assert len(fitz.open(PDF)) == 817
assert SOURCE.stat().st_size == 2_602
assert sha256(SOURCE) == "20687D1EE01AABA9B605591A61781CF688328026E0645AD51B6E02E921DC98A2"

objective = load_json("objective_metrics.json")
result = load_json("RESULT.json")
handoff = load_json("HANDOFF.json")
control = load_json("CONTROL.json")
manifest = load_json("evidence_manifest.json")
seal = load_json("SEAL.json")

font_rows = load_csv("manual_source_font_audit.csv")
gate_rows = load_csv("manual_gate_observations.csv")
span_rows = load_csv("page661_figure_text_spans.csv")

assert len(font_rows) == 10
assert len({row["ELEMENT_ID"] for row in font_rows}) == 10
assert len(gate_rows) == 32
assert len({row["GATE_ID"] for row in gate_rows}) == 32
assert len(span_rows) == objective["figure_region_span_count"]
assert all(row["MANUAL_OBSERVATION"].strip() for row in font_rows)
assert all(row["MANUAL_OBSERVATION"].strip() for row in gate_rows)
assert len({row["MANUAL_OBSERVATION"] for row in gate_rows}) == len(gate_rows)

for row in font_rows:
    if row["GENERAL_VISIBLE"].lower() == "true":
        assert float(row["PDF_BASE_SPAN_PT"]) >= 9.5
        if row["EFFECTIVE_PT"] != "normalsize":
            assert float(row["EFFECTIVE_PT"]) >= 9.5

assert result["decision"] == EXPECTED_DECISION
assert result["source_modification_count"] == 0
assert result["tex_call_count"] == 0
assert result["hard_defect_count"] == 0
assert result["unresolved"] == []
assert handoff["decisions"] == [EXPECTED_DECISION]
assert handoff["files_changed"] == []
assert handoff["unresolved"] == []
assert control["manifest_exclusions"] == EXPECTED_EXCLUSIONS
assert manifest["excluded_control_files"] == EXPECTED_EXCLUSIONS
assert manifest["manifest_self"] == "evidence_manifest.json"

entry_names = [entry["path"] for entry in manifest["entries"]]
assert len(entry_names) == len(set(entry_names)) == manifest["payload_count"]
actual_payload = sorted(
    path.name for path in ROOT.iterdir()
    if path.is_file() and path.name not in EXPECTED_EXCLUSIONS
)
assert sorted(entry_names) == actual_payload
for entry in manifest["entries"]:
    path = ROOT / entry["path"]
    assert path.stat().st_size == entry["bytes"]
    assert sha256(path) == entry["sha256"]

assert seal["decision"] == EXPECTED_DECISION
assert seal["manifest_sha256"] == sha256(ROOT / "evidence_manifest.json")
assert seal["result_sha256"] == sha256(ROOT / "RESULT.json")
assert seal["handoff_sha256"] == sha256(ROOT / "HANDOFF.json")
assert seal["payload_count"] == manifest["payload_count"]

for path in ROOT.rglob("*"):
    assert not path.is_symlink(), f"Reparse/symlink entry: {path}"
    lower_name = path.name.lower()
    assert lower_name not in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ds_store", "thumbs.db"}
    assert path.suffix.lower() not in {".pyc", ".pyo"}

seal_mtime = (ROOT / "SEAL.json").stat().st_mtime_ns
assert all(
    path.name == "SEAL.json" or path.stat().st_mtime_ns <= seal_mtime
    for path in ROOT.iterdir() if path.is_file()
)

print(json.dumps({
    "status": "FINAL_VALIDATION_PASS",
    "payload_count": manifest["payload_count"],
    "font_rows": len(font_rows),
    "gate_rows": len(gate_rows),
    "span_rows": len(span_rows),
    "source_hash": sha256(SOURCE),
    "pdf_hash": sha256(PDF),
    "manifest_hash": sha256(ROOT / "evidence_manifest.json"),
    "seal_hash": sha256(ROOT / "SEAL.json"),
}, ensure_ascii=False, indent=2))

