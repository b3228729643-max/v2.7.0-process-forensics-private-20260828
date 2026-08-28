from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"
VALIDATION = ROOT / "SEAL_VALIDATION.json"
HANDOFF_ID = "C-FIG-P656-01-R108-SA1-FRESH-ISOLATED-REPLACEMENT-V2"

EXPECTED_CSV_ROWS = {
    "after_font_audit.csv": 25,
    "after_pixel_measurements.csv": 25,
    "critical_glyph_audit.csv": 10,
    "manual_object_adjudication.csv": 48,
    "manual_critical_adjudication.csv": 12,
    "analysis/visible_objects.csv": 48,
    "analysis/all_unordered_pairs.csv": 1128,
}


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_and_validate() -> dict[str, object]:
    counts: dict[str, int] = {}
    for relative_path, expected in EXPECTED_CSV_ROWS.items():
        rows = read_csv(relative_path)
        counts[relative_path] = len(rows)
        if len(rows) != expected:
            raise RuntimeError(f"{relative_path}: {len(rows)} rows, expected {expected}")

    visible_ids = {row["OBJECT_ID"] for row in read_csv("analysis/visible_objects.csv")}
    manual_ids = {row["OBJECT_ID"] for row in read_csv("manual_object_adjudication.csv")}
    if visible_ids != manual_ids or len(visible_ids) != 48:
        raise RuntimeError("manual/visible object ID set mismatch")

    family_rows = read_csv("after_overlap_report.csv")
    non_total = [row for row in family_rows if row["GEOMETRY_FAMILY"] != "TOTAL"]
    total_rows = [row for row in family_rows if row["GEOMETRY_FAMILY"] == "TOTAL"]
    family_sum = sum(int(row["PAIR_COUNT"]) for row in non_total)
    if family_sum != 1128 or len(total_rows) != 1 or int(total_rows[0]["PAIR_COUNT"]) != 1128:
        raise RuntimeError("pair-family closure mismatch")

    json_files = sorted(ROOT.rglob("*.json"))
    for path in json_files:
        with path.open("r", encoding="utf-8-sig") as handle:
            json.load(handle)

    return {
        "csv_row_counts": counts,
        "object_id_count": len(visible_ids),
        "object_id_set_match": "PASS",
        "pair_family_non_total_sum": family_sum,
        "pair_total_row": int(total_rows[0]["PAIR_COUNT"]),
        "json_files_parsed": len(json_files),
    }


def filesystem_hygiene() -> dict[str, int]:
    env = dict(os.environ)
    env["SA1_SEAL_ROOT"] = str(ROOT)
    command = (
        "$r=$env:SA1_SEAL_ROOT; "
        "$f=@(Get-ChildItem -LiteralPath $r -Recurse -File); "
        "$a=@($f | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * | "
        "Where-Object { $_.Stream -ne ':$DATA' } }); "
        "$c=@(Get-ChildItem -LiteralPath $r -Recurse -Directory | "
        "Where-Object { $_.Name -eq '__pycache__' }); "
        "$p=@(Get-ChildItem -LiteralPath $r -Recurse -File | "
        "Where-Object { $_.Extension -eq '.pyc' }); "
        "[pscustomobject]@{nondefault_ads_count=$a.Count;cache_dir_count=$c.Count;"
        "pyc_count=$p.Count} | ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    result = json.loads(completed.stdout)
    normalized = {key: int(value) for key, value in result.items()}
    if any(normalized.values()):
        raise RuntimeError(f"filesystem hygiene failure: {normalized}")
    return normalized


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    if ROOT.name != "sa1_r108_fresh_isolated_replacement_v2":
        raise RuntimeError(f"unexpected evidence root: {ROOT}")
    for forbidden_existing in (MANIFEST, MARKER, VALIDATION):
        if forbidden_existing.exists():
            raise RuntimeError(f"seal is single-use; already exists: {forbidden_existing.name}")

    first_parse = parse_and_validate()
    first_hygiene = filesystem_hygiene()

    validation_payload = {
        "schema": "FIG-P656-01-SA1-seal-validation-v1",
        "handoff_id": HANDOFF_ID,
        "first_parse": first_parse,
        "filesystem_hygiene_before_validation": first_hygiene,
        "validation_scope": "mechanical structure, parseability, counts, and file hygiene",
    }
    write_json(VALIDATION, validation_payload)

    second_parse = parse_and_validate()
    second_hygiene = filesystem_hygiene()
    if second_parse["csv_row_counts"] != first_parse["csv_row_counts"]:
        raise RuntimeError("CSV row counts changed during sealing")

    hashed_entries: list[dict[str, object]] = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p not in (MANIFEST, MARKER)):
        hashed_entries.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "digest_policy": "SHA256_CONTENT",
            }
        )

    manifest_payload = {
        "schema": "FIG-P656-01-SA1-manifest-v1",
        "handoff_id": HANDOFF_ID,
        "evidence_root": str(ROOT),
        "content_entries": hashed_entries,
        "special_entries": [
            {
                "path": "MANIFEST.json",
                "digest_policy": "SELF_EXCLUDED_BY_DEFINITION",
                "reason": "A manifest cannot contain its own stable content digest.",
            },
            {
                "path": "WRITE_STOPPED",
                "digest_policy": "CREATED_LAST_AFTER_MANIFEST",
                "reason": "The immutable stop marker records the completed manifest digest.",
            },
        ],
        "accounted_path_count": len(hashed_entries) + 2,
        "second_parse": second_parse,
        "filesystem_hygiene_before_manifest": second_hygiene,
    }
    write_json(MANIFEST, manifest_payload)

    with MANIFEST.open("r", encoding="utf-8") as handle:
        reparsed_manifest = json.load(handle)
    if reparsed_manifest["accounted_path_count"] != len(hashed_entries) + 2:
        raise RuntimeError("manifest reparse count mismatch")
    actual_before_marker = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != MARKER
    }
    expected_before_marker = {entry["path"] for entry in hashed_entries} | {"MANIFEST.json"}
    if actual_before_marker != expected_before_marker:
        raise RuntimeError("manifest path accounting mismatch before marker")

    manifest_digest = sha256(MANIFEST)
    marker_text = (
        "WRITE_STOPPED\n"
        f"handoff_id={HANDOFF_ID}\n"
        f"manifest_path={MANIFEST}\n"
        f"manifest_sha256={manifest_digest}\n"
        f"accounted_path_count={len(hashed_entries) + 2}\n"
        "postmarker_content_writes_expected=0\n"
    )
    MARKER.write_text(marker_text, encoding="utf-8", newline="\n")

    print(
        json.dumps(
            {
                "manifest_sha256": manifest_digest,
                "manifest_bytes": MANIFEST.stat().st_size,
                "write_stopped_bytes": MARKER.stat().st_size,
                "accounted_path_count": len(hashed_entries) + 2,
                "hashed_content_entry_count": len(hashed_entries),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
