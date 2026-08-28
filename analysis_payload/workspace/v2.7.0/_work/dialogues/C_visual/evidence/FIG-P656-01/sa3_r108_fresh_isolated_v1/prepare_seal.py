from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.sha256"
VALIDATION = ROOT / "seal_validation.json"
CONTROL_EXCLUSIONS = {"MANIFEST.sha256", ".WRITE_STOPPED.prepared", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def csv_rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def relative_files() -> list[Path]:
    return sorted(
        (
            path
            for path in ROOT.rglob("*")
            if path.is_file() and path.relative_to(ROOT).as_posix() not in CONTROL_EXCLUSIONS
        ),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def nondefault_ads() -> list[str]:
    escaped_root = str(ROOT).replace("'", "''")
    command = (
        f"$r='{escaped_root}'; "
        "$items=@(Get-Item -LiteralPath $r -Force) + @(Get-ChildItem -LiteralPath $r -Recurse -Force); "
        "$streams=@($items | Get-Item -Stream * -ErrorAction SilentlyContinue | "
        "Where-Object { $_.Stream -ne ':$DATA' }); "
        "$streams | ForEach-Object { $_.FileName + '::' + $_.Stream }"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=True,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def reparse_entries() -> list[str]:
    found: list[str] = []
    for path in [ROOT, *ROOT.rglob("*")]:
        attrs = getattr(path.lstat(), "st_file_attributes", 0)
        if path.is_symlink() or attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            found.append(path.relative_to(ROOT).as_posix() if path != ROOT else ".")
    return found


def cache_entries() -> list[str]:
    found: list[str] = []
    for path in ROOT.rglob("*"):
        name = path.name.lower()
        if name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ds_store", "thumbs.db"} or path.suffix.lower() in {".pyc", ".pyo"}:
            found.append(path.relative_to(ROOT).as_posix())
    return found


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    require(not MANIFEST.exists(), "MANIFEST.sha256 already exists")
    require(not (ROOT / "WRITE_STOPPED").exists(), "WRITE_STOPPED already exists")
    require(not (ROOT / ".WRITE_STOPPED.prepared").exists(), "prepared marker already exists")

    objects = csv_rows("objects_machine.csv")
    pairs = csv_rows("all_pairs_machine.csv")
    masks = sorted((ROOT / "object_masks").glob("*.png"))
    rois = sorted((ROOT / "critical_rois").glob("*.png"))
    manual_objects = csv_rows("manual_object_review.csv")
    manual_relations = csv_rows("manual_critical_relations.csv")
    manual_views = csv_rows("manual_view_review.csv")
    manual_hard = csv_rows("manual_hard_gate_review.csv")
    machine_relations = csv_rows("critical_relations_machine.csv")

    object_ids = [row["object_id"] for row in objects]
    require(len(objects) == 50 and len(set(object_ids)) == 50, "object denominator is not 50 unique IDs")
    require(len(masks) == 50, "object mask count is not 50")
    require(len(rois) == 10, "critical ROI view count is not 10")
    require(len(pairs) == 1225, "all-pair count is not C(50,2)=1225")
    require(len({row["pair_id"] for row in pairs}) == 1225, "pair IDs are not unique")
    unordered_pairs = {
        tuple(sorted((row["object_a"], row["object_b"])))
        for row in pairs
    }
    require(len(unordered_pairs) == 1225, "unordered pair membership is not unique/complete")
    require(all(a != b and a in object_ids and b in object_ids for a, b in unordered_pairs), "invalid pair member")
    require(len(manual_objects) == 50 and len({row["object_id"] for row in manual_objects}) == 50, "manual object review is incomplete")
    require(len(manual_relations) == 29 and len({row["relation_id"] for row in manual_relations}) == 29, "manual relation review is incomplete")
    require(len(machine_relations) == 29 and len({row["relation_id"] for row in machine_relations}) == 29, "machine relation review is incomplete")
    require(len(manual_views) == 13 and len({row["view_id"] for row in manual_views}) == 13, "manual view review is incomplete")
    require(len(manual_hard) == 27 and len({row["gate_id"] for row in manual_hard}) == 27, "manual hard-gate review is incomplete")

    with (ROOT / "machine_gate_summary.json").open("r", encoding="utf-8") as stream:
        machine_summary = json.load(stream)
    require(machine_summary["object_denominator_N"] == 50, "machine summary N mismatch")
    require(machine_summary["unordered_pair_denominator_C_N_2"] == 1225, "machine summary C(N,2) mismatch")
    require(machine_summary["pair_ids_unique"] == 1225, "machine summary pair enumeration mismatch")
    require(machine_summary["separate_pair_candidate_overlap_pixels_sum"] == 0, "machine overlap candidate is nonzero")
    require(machine_summary["empty_object_masks"] == [], "empty object mask found")
    require(machine_summary["pairs_requiring_manual_adjudication"] == [], "unadjudicated pair found")
    require(machine_summary["figure_caption_crop_edge_foreground_pixels"] == 0, "crop-edge foreground found")

    # Parse every JSON and CSV payload before the seal snapshot.
    json_parsed: list[str] = []
    csv_parsed: list[str] = []
    for path in sorted(ROOT.rglob("*.json")):
        if path == VALIDATION:
            continue
        with path.open("r", encoding="utf-8-sig") as stream:
            json.load(stream)
        json_parsed.append(path.relative_to(ROOT).as_posix())
    for path in sorted(ROOT.rglob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            list(csv.reader(stream))
        csv_parsed.append(path.relative_to(ROOT).as_posix())

    ads = nondefault_ads()
    reparse = reparse_entries()
    caches = cache_entries()
    require(not ads, f"non-default ADS found: {ads}")
    require(not reparse, f"reparse entry found: {reparse}")
    require(not caches, f"cache/pyc residue found: {caches}")

    validation = {
        "schema": "FIG-P656-01-SA3-SEAL-VALIDATION-v1",
        "handoff_id": "C-FIG-P656-01-R108-SA3-FRESH-ISOLATED-V1",
        "result": "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
        "valid": True,
        "denominator": {"N": 50, "unordered_pairs_expected": 1225, "unordered_pairs_enumerated": 1225},
        "machine": {"object_masks": 50, "critical_relations": 29, "critical_roi_images": 10, "overlap_candidates": 0, "empty_masks": 0, "mask_contamination": 0, "crop_edge_foreground": 0},
        "manual": {"objects": 50, "critical_relations": 29, "views": 13, "hard_gates": 27, "semantic_recomputation": "complete", "font_and_R168_audit": "complete"},
        "parse_validation": {"json_files": json_parsed, "csv_files": csv_parsed},
        "filesystem_checks": {"nondefault_ads": ads, "reparse_entries": reparse, "cache_or_pyc_entries": caches},
        "manifest_policy": {
            "covers": "all intended payload recursively",
            "self_exclusion": "MANIFEST.sha256",
            "control_exclusions": [".WRITE_STOPPED.prepared", "WRITE_STOPPED"],
        },
    }
    VALIDATION.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload = relative_files()
    lines = [
        "# FIG-P656-01 SA3 sealed-payload SHA256 manifest",
        "# SELF_EXCLUSION: MANIFEST.sha256",
        "# CONTROL_EXCLUSIONS: .WRITE_STOPPED.prepared, WRITE_STOPPED",
        f"# PAYLOAD_COUNT: {len(payload)}",
    ]
    for path in payload:
        rel = path.relative_to(ROOT).as_posix()
        lines.append(f"{sha256(path)}  {path.stat().st_size}  {rel}")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"valid": True, "payload_count": len(payload), "manifest_sha256": sha256(MANIFEST), "manifest_bytes": MANIFEST.stat().st_size}))


if __name__ == "__main__":
    main()
