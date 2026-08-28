from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


OLD_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa1_r101_initial")
NEW_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa1_r101_resealed_v1")
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual")
SOURCE = WORKTREE / r"src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex"
SCRIPT_REL = Path(r"_reseal_tools\reseal_fig_p602_evidence.py")
PROVENANCE_REL = Path(r"00_identity\RESEAL_PROVENANCE.json")
MANIFEST_REL = Path(r"09_manifest\evidence_file_manifest.csv")
SEAL_REL = Path(r"00_identity\WRITE_STOPPED.json")
EXCLUDED_OLD_CONTROLS = {
    SEAL_REL.as_posix(),
    MANIFEST_REL.as_posix(),
}
EXPECTED_OLD_UNMANIFESTED = {
    "_audit_tools/build_p602_r101_measurements.py",
    "_audit_tools/inspect_p602_page.py",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def utc_ns(ns: int) -> str:
    sec, nano = divmod(ns, 1_000_000_000)
    base = datetime.fromtimestamp(sec, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{nano:09d}Z"


def identity(path: Path) -> dict:
    stat = path.stat()
    return {
        "bytes": stat.st_size,
        "sha256": sha256(path),
        "mtime_ns": stat.st_mtime_ns,
        "mtime_utc": utc_ns(stat.st_mtime_ns),
    }


def canonical_recordset_sha(records: list[dict]) -> str:
    selected = [
        {
            "record_type": row["record_type"],
            "path": row["path"],
            "bytes": int(row["bytes"]),
            "sha256": row["sha256"],
            "mtime_ns": int(row["mtime_ns"]),
            "source_path": row["source_path"],
            "source_bytes": row["source_bytes"],
            "source_sha256": row["source_sha256"],
            "source_mtime_ns": row["source_mtime_ns"],
            "copy_content_match": row["copy_content_match"],
            "copy_mtime_match": row["copy_mtime_match"],
        }
        for row in sorted(records, key=lambda item: item["path"])
    ]
    raw = json.dumps(selected, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=WORKTREE,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.rstrip("\r\n")


def section(text: str, start: str, end: str) -> str:
    return text.split(f"## {start}", 1)[1].split(f"## {end}", 1)[0]


def ledger_counts(root: Path) -> dict:
    glyph_text = (root / "SA1_RERUN_GLYPH_LEDGER.md").read_text(encoding="utf-8")
    pair_text = (root / "SA1_RERUN_PAIR_LEDGER.md").read_text(encoding="utf-8")
    review_text = (root / "SA1_RERUN_REVIEW.md").read_text(encoding="utf-8")
    glyph_ids = re.findall(r"^- G(\d{3})\b.* — PASS —", glyph_text, re.MULTILINE)
    pair_ids = re.findall(r"^- P(\d{3})\b.* — PASS —", pair_text, re.MULTILINE)
    object_ids = re.findall(
        r"^- ([TBE]\d{2})\b.* — PASS —",
        section(review_text, "OBJECT_LEDGER", "CRITICAL_LEDGER"),
        re.MULTILINE,
    )
    critical_ids = re.findall(
        r"^- (P\d{3})\b.* — PASS —",
        section(review_text, "CRITICAL_LEDGER", "PEER_LEDGER"),
        re.MULTILINE,
    )
    peer_ids = re.findall(
        r"^- (G\d{3})\b.* — PASS —",
        section(review_text, "PEER_LEDGER", "ROLE_LEDGER"),
        re.MULTILINE,
    )
    role_ids = re.findall(
        r"^- (T\d{2}/[^ ]+)\b.* — PASS —",
        section(review_text, "ROLE_LEDGER", "CLIPPING_LEDGER"),
        re.MULTILINE,
    )
    clipping_ids = re.findall(
        r"^- ([TBE]\d{2})\b.* — PASS —",
        section(review_text, "CLIPPING_LEDGER", "VIEW_AND_HARD_GATES"),
        re.MULTILINE,
    )
    checks = {
        "glyph": (glyph_ids, 175),
        "pair": (pair_ids, 325),
        "object": (object_ids, 26),
        "critical": (critical_ids, 8),
        "peer": (peer_ids, 27),
        "role": (role_ids, 50),
        "clipping": (clipping_ids, 26),
    }
    for name, (ids, expected) in checks.items():
        if len(ids) != expected or len(set(ids)) != expected:
            raise RuntimeError(f"{name} ledger denominator mismatch: rows={len(ids)} unique={len(set(ids))} expected={expected}")
    for required in ("RESULT: PASS", "NEEDS_SOURCE_WRITER: no", "NEEDS_TEX_SLOT: no"):
        if required not in review_text:
            raise RuntimeError(f"manual review terminal field missing: {required}")
    return {
        f"{name}_rows": len(ids)
        for name, (ids, _) in checks.items()
    } | {
        f"{name}_unique": len(set(ids))
        for name, (ids, _) in checks.items()
    } | {
        "glyph_pass": len(glyph_ids),
        "pair_pass": len(pair_ids),
        "review_result": "PASS",
        "needs_source_writer": "no",
        "needs_tex_slot": "no",
    }


def source_manifest_audit(old_files: list[Path]) -> dict:
    old_manifest = OLD_ROOT / MANIFEST_REL
    with old_manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    row_by_path = {row["path"].replace("\\", "/"): row for row in rows}
    old_relpaths = {path.relative_to(OLD_ROOT).as_posix() for path in old_files}
    unmanifested = sorted(old_relpaths - set(row_by_path))
    mismatches = []
    for rel, row in row_by_path.items():
        path = OLD_ROOT / Path(rel)
        if not path.is_file():
            mismatches.append({"path": rel, "kind": "missing"})
            continue
        actual = identity(path)
        if int(row["bytes"]) != actual["bytes"]:
            mismatches.append(
                {
                    "path": rel,
                    "kind": "bytes",
                    "recorded": int(row["bytes"]),
                    "actual": actual["bytes"],
                }
            )
    if set(unmanifested) != EXPECTED_OLD_UNMANIFESTED:
        raise RuntimeError(f"unexpected old unmanifested set: {unmanifested}")
    expected_self_mismatch = [
        item
        for item in mismatches
        if item["path"] == MANIFEST_REL.as_posix()
        and item["kind"] == "bytes"
        and item["recorded"] == 22692
        and item["actual"] == 22780
    ]
    if len(expected_self_mismatch) != 1 or len(mismatches) != 1:
        raise RuntimeError(f"unexpected old manifest mismatch set: {mismatches}")
    return {
        "physical_lines": sum(1 for _ in old_manifest.open("r", encoding="utf-8-sig")),
        "data_rows": len(rows),
        "unmanifested": unmanifested,
        "mismatches": mismatches,
    }


def make_record(
    record_type: str,
    destination: Path,
    source: Path | None,
    notes: str,
) -> dict:
    dest_id = identity(destination)
    if source is None:
        return {
            "record_type": record_type,
            "path": destination.relative_to(NEW_ROOT).as_posix(),
            **dest_id,
            "source_root": "",
            "source_path": "",
            "source_bytes": "",
            "source_sha256": "",
            "source_mtime_utc": "",
            "source_mtime_ns": "",
            "copy_content_match": "",
            "copy_mtime_match": "",
            "notes": notes,
        }
    src_id = identity(source)
    return {
        "record_type": record_type,
        "path": destination.relative_to(NEW_ROOT).as_posix(),
        **dest_id,
        "source_root": str(OLD_ROOT.resolve()),
        "source_path": source.relative_to(OLD_ROOT).as_posix(),
        "source_bytes": src_id["bytes"],
        "source_sha256": src_id["sha256"],
        "source_mtime_utc": src_id["mtime_utc"],
        "source_mtime_ns": src_id["mtime_ns"],
        "copy_content_match": str(dest_id["bytes"] == src_id["bytes"] and dest_id["sha256"] == src_id["sha256"]).lower(),
        "copy_mtime_match": str(dest_id["mtime_ns"] == src_id["mtime_ns"]).lower(),
        "notes": notes,
    }


def main() -> None:
    old_resolved = OLD_ROOT.resolve(strict=True)
    new_resolved = NEW_ROOT.resolve(strict=True)
    if old_resolved == new_resolved:
        raise RuntimeError("old and new roots resolve to the same directory")
    script = NEW_ROOT / SCRIPT_REL
    initial_new_files = sorted(path.relative_to(NEW_ROOT).as_posix() for path in NEW_ROOT.rglob("*") if path.is_file())
    if initial_new_files != [SCRIPT_REL.as_posix()]:
        raise RuntimeError(f"new root is not pristine except for reseal script: {initial_new_files}")

    old_files = sorted(path for path in OLD_ROOT.rglob("*") if path.is_file())
    if len(old_files) != 492:
        raise RuntimeError(f"old ordinary-file denominator changed: {len(old_files)}")
    old_manifest_audit = source_manifest_audit(old_files)
    old_inventory = [
        {
            "path": path.relative_to(OLD_ROOT).as_posix(),
            **identity(path),
        }
        for path in old_files
    ]
    old_inventory_sha = hashlib.sha256(
        json.dumps(old_inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()

    payload_sources = [
        path for path in old_files
        if path.relative_to(OLD_ROOT).as_posix() not in EXCLUDED_OLD_CONTROLS
    ]
    if len(payload_sources) != 490:
        raise RuntimeError(f"payload denominator mismatch: {len(payload_sources)}")

    for source in payload_sources:
        rel = source.relative_to(OLD_ROOT)
        destination = NEW_ROOT / rel
        if destination.exists():
            raise RuntimeError(f"destination collision: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        src_stat = source.stat()
        os.utime(destination, ns=(src_stat.st_atime_ns, src_stat.st_mtime_ns))

    payload_records = [
        make_record(
            "payload",
            NEW_ROOT / source.relative_to(OLD_ROOT),
            source,
            "byte-for-byte copy from rejected old root; old control files excluded",
        )
        for source in payload_sources
    ]
    if not all(row["copy_content_match"] == "true" and row["copy_mtime_match"] == "true" for row in payload_records):
        raise RuntimeError("payload copy identity mismatch")

    ledgers = ledger_counts(NEW_ROOT)
    identity_json = json.loads((NEW_ROOT / "00_identity" / "identity.json").read_text(encoding="utf-8"))
    expected_pdf_sha = "0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1"
    expected_source_sha = "18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084"
    expected_page_png_sha = "8E0DCE21A10BFCAAA5A5BE40627110E262459C0BE586626C9AF4EC8CAEC03C71"
    if identity_json["candidate_sha256"] != expected_pdf_sha:
        raise RuntimeError("R101 PDF identity mismatch")
    if identity_json["source_sha256"] != expected_source_sha:
        raise RuntimeError("source identity mismatch in copied evidence")
    if identity_json["native_page_png_sha256"] != expected_page_png_sha:
        raise RuntimeError("native page identity mismatch")

    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    status = git("status", "--short")
    actual_source_sha = sha256(SOURCE)
    if branch != "v2.7.0/dialogue-c-visual" or head != "eea4060c5229168e2b973bbaea81cf391e7a9dfd" or status:
        raise RuntimeError(f"worktree gate failed: branch={branch} head={head} status={status!r}")
    if actual_source_sha != expected_source_sha:
        raise RuntimeError("current worktree source SHA mismatch")

    provenance = {
        "schema": "FIG-P602-01-evidence-reseal-provenance-v1",
        "source_root_resolved": str(old_resolved),
        "sealed_root_resolved": str(new_resolved),
        "source_root_policy": "permanently read-only; no file was overwritten or deleted",
        "source_ordinary_file_count": len(old_files),
        "source_inventory_sha256": old_inventory_sha,
        "source_manifest_audit": old_manifest_audit,
        "excluded_rejected_controls": sorted(EXCLUDED_OLD_CONTROLS),
        "copied_payload_count": len(payload_records),
        "copy_policy": "byte-identical copy with exact LastWriteTime preservation",
        "copy_content_mismatch_count": sum(row["copy_content_match"] != "true" for row in payload_records),
        "copy_mtime_mismatch_count": sum(row["copy_mtime_match"] != "true" for row in payload_records),
        "manual_content_ledger_counts": ledgers,
        "worktree_gate": {
            "path": str(WORKTREE.resolve()),
            "branch": branch,
            "head": head,
            "status_porcelain": status,
            "source_path": str(SOURCE.resolve()),
            "source_sha256": actual_source_sha,
        },
        "r101_identity": {
            "pdf_sha256": expected_pdf_sha,
            "pdf_page": 651,
            "printed_page": 638,
            "native_page_png_sha256": expected_page_png_sha,
        },
        "forbidden_actions_confirmed": {
            "machine_evidence_rerun": False,
            "manual_conclusion_changed": False,
            "source_write": False,
            "tex_or_build": False,
            "sa3_started": False,
        },
    }
    provenance_path = NEW_ROOT / PROVENANCE_REL
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    control_records = [
        make_record("control", script, None, "reseal implementation; executed with Python -B"),
        make_record("control", provenance_path, None, "resolved source/copy/control provenance"),
    ]
    payload_control_records = payload_records + control_records
    recordset_sha = canonical_recordset_sha(payload_control_records)

    marker_path = NEW_ROOT / SEAL_REL
    manifest_path = NEW_ROOT / MANIFEST_REL
    seal_mtime_ns = (int(time.time()) + 60) * 1_000_000_000
    marker = {
        "schema": "FIG-P602-01-WRITE_STOPPED-reseal-v1",
        "figure_uid": "FIG-P602-01",
        "scope_row": "B52",
        "branch_denominator": 46,
        "sealed_root_resolved": str(new_resolved),
        "source_root_resolved": str(old_resolved),
        "old_root_policy": "permanently read-only",
        "old_control_status": "REJECTED_AND_EXCLUDED",
        "excluded_old_controls": sorted(EXCLUDED_OLD_CONTROLS),
        "payload_count": len(payload_records),
        "control_count": len(control_records),
        "seal_count": 1,
        "manifest_self_count": 1,
        "manifest_entry_count": len(payload_control_records) + 1,
        "expected_total_ordinary_files": len(payload_control_records) + 2,
        "coverage_model": "manifest lists every payload/control file and the predeclared final seal; the manifest alone is excluded as self and is identified by the external immutable root handoff",
        "payload_control_recordset_sha256": recordset_sha,
        "manifest_path": MANIFEST_REL.as_posix(),
        "manual_ledgers": {
            "state": "ADJUDICATED_PASS",
            "result": "PASS",
            "object": "26/26",
            "glyph": "175/175",
            "pair": "325/325",
            "critical": "8/8",
            "peer": "27/27",
            "role": "50/50",
            "clipping": "26/26",
            "needs_source_writer": "no",
            "needs_tex_slot": "no",
        },
        "r101_identity": {
            "pdf_sha256": expected_pdf_sha,
            "pdf_page": 651,
            "printed_page": 638,
            "native_page_png_sha256": expected_page_png_sha,
        },
        "source_sha256": expected_source_sha,
        "worktree": {
            "branch": branch,
            "head": head,
            "clean": True,
        },
        "write_stopped": True,
        "strictly_last_file_write": True,
        "seal_mtime_ns": seal_mtime_ns,
        "seal_mtime_utc": utc_ns(seal_mtime_ns),
        "acceptance_state": "SEALED_PENDING_MAINLINE_ACCEPTANCE",
        "sa3_authorized": False,
        "source_writer": "none",
        "tex_slot": "disabled",
    }
    marker_bytes = (json.dumps(marker, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    marker_sha = hashlib.sha256(marker_bytes).hexdigest().upper()
    seal_record = {
        "record_type": "seal",
        "path": SEAL_REL.as_posix(),
        "bytes": len(marker_bytes),
        "sha256": marker_sha,
        "mtime_ns": seal_mtime_ns,
        "mtime_utc": utc_ns(seal_mtime_ns),
        "source_root": "",
        "source_path": "",
        "source_bytes": "",
        "source_sha256": "",
        "source_mtime_utc": "",
        "source_mtime_ns": "",
        "copy_content_match": "",
        "copy_mtime_match": "",
        "notes": "predeclared final file; written strictly after manifest",
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "record_type", "path", "bytes", "sha256", "mtime_utc", "mtime_ns",
        "source_root", "source_path", "source_bytes", "source_sha256",
        "source_mtime_utc", "source_mtime_ns", "copy_content_match",
        "copy_mtime_match", "notes",
    ]
    manifest_records = sorted(payload_control_records, key=lambda row: (row["record_type"], row["path"])) + [seal_record]
    with manifest_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest_records)
    if manifest_path.stat().st_mtime_ns >= seal_mtime_ns:
        raise RuntimeError("chosen seal mtime does not follow manifest mtime")

    # Final write in the sealed root.  No root file mutation is allowed after this block.
    marker_path.write_bytes(marker_bytes)
    os.utime(marker_path, ns=(seal_mtime_ns, seal_mtime_ns))

    # Read-only post-seal self-check.
    files_after = sorted(path for path in NEW_ROOT.rglob("*") if path.is_file())
    if len(files_after) != marker["expected_total_ordinary_files"]:
        raise RuntimeError(f"post-seal file count mismatch: {len(files_after)}")
    with manifest_path.open("r", encoding="utf-8", newline="") as stream:
        parsed = list(csv.DictReader(stream))
    if len(parsed) != marker["manifest_entry_count"]:
        raise RuntimeError(f"manifest parse count mismatch: {len(parsed)}")
    listed = {row["path"] for row in parsed}
    actual_rel = {path.relative_to(NEW_ROOT).as_posix() for path in files_after}
    if actual_rel - listed != {MANIFEST_REL.as_posix()} or listed - actual_rel:
        raise RuntimeError(f"manifest self model mismatch: unlisted={actual_rel-listed}, missing={listed-actual_rel}")
    for row in parsed:
        actual = identity(NEW_ROOT / Path(row["path"]))
        if (
            actual["bytes"] != int(row["bytes"])
            or actual["sha256"] != row["sha256"]
            or actual["mtime_ns"] != int(row["mtime_ns"])
            or actual["mtime_utc"] != row["mtime_utc"]
        ):
            raise RuntimeError(f"post-seal manifest identity mismatch: {row['path']}")
    if identity(marker_path)["sha256"] != marker_sha:
        raise RuntimeError("final marker hash mismatch")
    if any(path.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in path.parts for path in NEW_ROOT.rglob("*")):
        raise RuntimeError("cache artifact found")
    other_mtimes = [path.stat().st_mtime_ns for path in files_after if path != marker_path]
    if not all(value < marker_path.stat().st_mtime_ns for value in other_mtimes):
        raise RuntimeError("WRITE_STOPPED is not strictly newest")

    print(
        json.dumps(
            {
                "result": "RESEAL_CREATED_PENDING_ROOT_ACCEPTANCE",
                "new_root": str(new_resolved),
                "payload_count": len(payload_records),
                "control_count": len(control_records),
                "seal_count": 1,
                "manifest_self_count": 1,
                "manifest_entries": len(parsed),
                "ordinary_files": len(files_after),
                "payload_control_recordset_sha256": recordset_sha,
                "manifest_identity": identity(manifest_path),
                "marker_identity": identity(marker_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
