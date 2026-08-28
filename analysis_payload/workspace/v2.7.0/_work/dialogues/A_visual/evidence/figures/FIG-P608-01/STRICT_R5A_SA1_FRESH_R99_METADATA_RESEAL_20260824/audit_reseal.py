#!/usr/bin/env python3
"""One-shot R5A metadata reseal for the already-audited FIG-P608-01 package.

This is deliberately a packaging-only operation.  It copies the R5 evidence
bytes, hashes source and destination per file, replaces only the terminal
metadata that needs route/seal correction, then writes WRITE_STOPPED last.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGIN = ROOT.parent / "STRICT_R5_SA1_FRESH_R99_20260824"
NEW_HANDOFF_ID = "A-R99-P608-SA1-FRESH-R5A-METADATA-RESEAL-20260824"
ROUTE = "SA1=gpt-5.6-terra/max"
RESULT = "FAIL_TO_SA2"
REPLACED = {
    "MACHINE_TERMINAL_RECALC.json",
    "manifest.json",
    "after_visual_acceptance.md",
    "RESULT.txt",
    "WRITE_STOPPED",
}
QUARANTINE_FILES = (
    "WRITE_STOPPED",
    "MACHINE_TERMINAL_RECALC.json",
    "manifest.json",
    "after_visual_acceptance.md",
    "RESULT.txt",
)


def utc_stamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    if not ORIGIN.is_dir():
        raise RuntimeError(f"missing R5 origin: {ORIGIN}")
    existing = sorted(item.name for item in ROOT.iterdir() if item.name != Path(__file__).name)
    if existing:
        raise RuntimeError(f"R5A must start empty except audit_reseal.py, found: {existing}")
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("R5A WRITE_STOPPED already exists; no reseal retry is permitted")

    origin_files = sorted(path for path in ORIGIN.rglob("*") if path.is_file())
    if len(origin_files) != 799:
        raise RuntimeError(f"unexpected R5 file count: {len(origin_files)}")
    origin_terminal = json.loads((ORIGIN / "MACHINE_TERMINAL_RECALC.json").read_text(encoding="utf-8"))
    origin_manifest = json.loads((ORIGIN / "manifest.json").read_text(encoding="utf-8"))
    origin_report = (ORIGIN / "after_visual_acceptance.md").read_text(encoding="utf-8")
    origin_result = (ORIGIN / "RESULT.txt").read_text(encoding="utf-8").strip()
    if not (
        origin_terminal["N"] == 170
        and origin_terminal["C_N_2_expected"] == 14365
        and origin_terminal["pair_rows"] == 14365
        and origin_terminal["result"] == RESULT
        and origin_result == RESULT
        and origin_manifest["result"] == RESULT
    ):
        raise RuntimeError("origin decision/counts do not match the sealed R5 baseline")

    r5_times_ns = {name: (ORIGIN / name).stat().st_mtime_ns for name in QUARANTINE_FILES}
    r5_times_utc = {name: utc_stamp(ORIGIN / name) for name in QUARANTINE_FILES}
    r5_tie = len(set(r5_times_ns.values())) == 1
    if not r5_tie:
        raise RuntimeError("R5 quarantine tie was not reproduced from the origin files")
    quarantine = {
        "origin_package": ORIGIN.name,
        "reason": "R5 WRITE_STOPPED LastWriteTimeUtc is exactly tied with MACHINE_TERMINAL_RECALC.json, manifest.json, after_visual_acceptance.md, and RESULT.txt; it is therefore quarantined as non-strict sealing only.",
        "observed_last_write_utc": r5_times_utc,
        "observed_last_write_ns": r5_times_ns,
        "exact_tie_verified": True,
        "bottom_evidence_decision_rejected": False,
    }

    reuse_rows: list[dict[str, object]] = []
    for source in origin_files:
        rel = source.relative_to(ORIGIN)
        if rel.as_posix() in REPLACED:
            continue
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        source_hash = sha256(source)
        dest_hash = sha256(dest)
        status = "REUSED_BYTE_IDENTICAL" if source.stat().st_size == dest.stat().st_size and source_hash == dest_hash else "MISMATCH"
        reuse_rows.append({
            "RELATIVE_PATH": rel.as_posix(),
            "SOURCE_BYTES": source.stat().st_size,
            "DEST_BYTES": dest.stat().st_size,
            "SOURCE_SHA256": source_hash,
            "DEST_SHA256": dest_hash,
            "STATUS": status,
        })
    mismatch_count = sum(row["STATUS"] != "REUSED_BYTE_IDENTICAL" for row in reuse_rows)
    if mismatch_count:
        raise RuntimeError(f"byte reuse mismatch count={mismatch_count}")
    with (ROOT / "reused_evidence_integrity.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(reuse_rows[0].keys()))
        writer.writeheader()
        writer.writerows(reuse_rows)

    reused_bytes = sum(int(row["SOURCE_BYTES"]) for row in reuse_rows)
    reseal = {
        "packaging_only": True,
        "no_pdf_rerender": True,
        "no_latex_or_graphics_source_change": True,
        "no_audit_rerun": True,
        "origin_file_count": len(origin_files),
        "reused_file_count": len(reuse_rows),
        "reused_bytes": reused_bytes,
        "reused_file_mismatch_count": mismatch_count,
        "replaced_terminal_metadata_files": sorted(REPLACED),
        "integrity_ledger": "reused_evidence_integrity.csv",
        "strict_latest": True,
        "strict_latest_scope": "FIG-P608-01 R5/R5A only; R5 is quarantined for timestamp-order defect",
    }
    terminal = dict(origin_terminal)
    terminal.update({
        "handoff_id": NEW_HANDOFF_ID,
        "origin_handoff_id": origin_terminal["handoff_id"],
        "actual_execution_route": ROUTE,
        "model_route": {"SA1": "gpt-5.6-terra/max"},
        "r5_quarantine": quarantine,
        "metadata_reseal": reseal,
        "strict_latest": True,
        "write_stopped_next": True,
    })
    write_json(ROOT / "MACHINE_TERMINAL_RECALC.json", terminal)

    manifest = dict(origin_manifest)
    manifest.update({
        "handoff_id": NEW_HANDOFF_ID,
        "origin_handoff_id": origin_manifest["handoff_id"],
        "actual_execution_route": ROUTE,
        "model_route": {"SA1": "gpt-5.6-terra/max"},
        "r5_quarantine": quarantine,
        "metadata_reseal": reseal,
        "strict_latest": True,
        "scope": "FIG-P608-01 fresh isolated SA1 on official R99 only; R5A metadata reseal",
    })
    write_json(ROOT / "manifest.json", manifest)

    payload_start = origin_report.find("## Candidate and four native views")
    if payload_start < 0:
        raise RuntimeError("origin report payload header missing")
    report = f"""# FIG-P608-01 — fresh isolated SA1 R99 R5A metadata reseal

HANDOFF_ID: `{NEW_HANDOFF_ID}`  
ORIGIN_HANDOFF_ID: `{origin_terminal['handoff_id']}`  
ACTUAL_ROOT_ORCHESTRATION_ROUTE: `{ROUTE}`  
RESULT: `{RESULT}`  
STRICT_LATEST: `true` (relative to R5/R5A only)

This is a packaging-only reseal. It does not rerender the official R99 PDF, rerun
the audit, alter an object/pair count, alter any evidence bytes, or alter the
`FAIL_TO_SA2` decision. It is not a root acceptance and does not assert a
final-book PASS.

## R5 quarantine

R5 is not used as a strict seal because its `WRITE_STOPPED` LastWriteTimeUtc was
exactly tied with its terminal, manifest, report, and result files. The defect is
timestamp ordering only; it does not convert any transient extractor condition
into a design failure. R5A byte-copies and hashes every non-replaced bottom
evidence file, then writes a new sentinel after all other R5A files.

- Reused evidence files: {len(reuse_rows)}; byte mismatches: {mismatch_count}; reused bytes: {reused_bytes}.
- The per-file source/destination checksum ledger is `reused_evidence_integrity.csv`.
- The only retained design failures remain `GLYPH_0025` and `GLYPH_0056`, natural-script `t`, each `H=10px < 15px`.

## Preserved R5 audit payload

""" + origin_report[payload_start:]
    (ROOT / "after_visual_acceptance.md").write_text(report, encoding="utf-8")

    (ROOT / "RESULT.txt").write_text(RESULT + "\n", encoding="utf-8")
    handoff = f"""# FIG-P608-01 R5A handoff

HANDOFF_ID: `{NEW_HANDOFF_ID}`
ORIGIN_HANDOFF_ID: `{origin_terminal['handoff_id']}`
ACTUAL_ROOT_ORCHESTRATION_ROUTE: `{ROUTE}`
RESULT: `{RESULT}`
STRICT_LATEST: `true` (R5/R5A only; R5 is quarantined)

This wrapper reuses {len(reuse_rows)} bottom-evidence files with {mismatch_count}
SHA-256 mismatch(es). It preserves N=170, C(N,2)=14,365, pair rows=14,365,
and the terminal decision. R5 quarantine reason: equal LastWriteTimeUtc for R5
WRITE_STOPPED and its four terminal metadata files. No source or audit rerun was
performed. `WRITE_STOPPED` in this R5A package is intentionally written last.
"""
    (ROOT / "HANDOFF.md").write_text(handoff, encoding="utf-8")

    pre_sentinel_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    expected_before_sentinel = len(reuse_rows) + 7  # script, integrity, 4 replacement metadata, and HANDOFF
    if len(pre_sentinel_files) != expected_before_sentinel:
        raise RuntimeError(f"unexpected pre-sentinel R5A file count: {len(pre_sentinel_files)} != {expected_before_sentinel}")
    latest_other_ns = max(path.stat().st_mtime_ns for path in pre_sentinel_files)
    margin_ns = 1_500_000_000
    remaining = margin_ns - (time.time_ns() - latest_other_ns)
    if remaining > 0:
        time.sleep(remaining / 1_000_000_000 + 0.25)
    sealed_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    sentinel = ROOT / "WRITE_STOPPED"
    sentinel.write_text(
        f"{sealed_at}\n{RESULT}\n{NEW_HANDOFF_ID}\n{ROUTE}\n"
        "R5A metadata-only reseal; sentinel written after every other R5A file.\n",
        encoding="utf-8",
    )
    final_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    latest_other_after_ns = max(path.stat().st_mtime_ns for path in final_files if path != sentinel)
    seal_margin_ns = sentinel.stat().st_mtime_ns - latest_other_after_ns
    if len(final_files) != expected_before_sentinel + 1 or seal_margin_ns < 1_000_000_000:
        raise RuntimeError(f"strict reseal verification failed: files={len(final_files)}, margin_ns={seal_margin_ns}")
    print(json.dumps({
        "reused_file_mismatch_count": mismatch_count,
        "actual_file_count": len(final_files),
        "strict_latest": True,
        "write_stopped_margin_ns": seal_margin_ns,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
