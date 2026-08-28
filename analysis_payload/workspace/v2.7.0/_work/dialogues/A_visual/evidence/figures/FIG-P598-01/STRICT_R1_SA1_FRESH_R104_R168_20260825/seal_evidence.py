from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import stat
import time
from datetime import datetime, timezone


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R1_SA1_FRESH_R104_R168_20260825")
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P598_01_R1_R104_FRESH_SA1_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R104-P598-01-SA1-FRESH-20260825.md")
HASH_MANIFEST = ROOT / "SEALED_MANIFEST.sha256"
JSON_MANIFEST = ROOT / "SEALED_MANIFEST.json"
STOP = ROOT / "WRITE_STOPPED"
EXCLUDED = {HASH_MANIFEST.name, JSON_MANIFEST.name, STOP.name}


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def set_read_only(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode & ~stat.S_IWRITE)


def validate() -> None:
    require(ROOT.is_dir(), "evidence root missing")
    require(REPORT.is_file(), "external report missing")
    require(HANDOFF.is_file(), "external handoff missing")
    require(not HASH_MANIFEST.exists(), "hash manifest already exists; refuse reseal")
    require(not JSON_MANIFEST.exists(), "JSON manifest already exists; refuse reseal")
    require(not STOP.exists(), "WRITE_STOPPED already exists; refuse reseal")

    element = rows("manual_element_adjudication.csv")
    critical = rows("manual_critical_adjudication.csv")
    relationship = rows("manual_relationship_adjudication.csv")
    endpoint = rows("manual_endpoint_adjudication.csv")
    views = rows("manual_view_ledger.csv")
    require(len(element) == 168, "manual element denominator must be 168")
    require(sum(r["element_id"].startswith("G") for r in element) == 142, "glyph denominator must be 142")
    require(sum(r["element_id"].startswith("V") for r in element) == 22, "visible graphic denominator must be 22")
    require(sum(r["element_id"].startswith("OCC") for r in element) == 4, "occlusion auxiliary count must be 4")
    require(len({r["element_id"] for r in element}) == 168, "manual element IDs must be unique")
    require(all(r["reviewer"] == "SA1_FRESH_gpt-5.6-sol_xhigh" for r in element), "manual reviewer identity mismatch")
    require(all(r["decision"] == "PASS" for r in element), "manual element decision not PASS")
    require(all(r["original_match"] == "true" and r["overlay_complete"] == "true" and r["mask_only_pure"] == "true" for r in element), "manual element boolean not true")
    require(all(r["missing_stroke_px"] == "0" and r["foreign_pixel_px"] == "0" for r in element), "manual element pixel defect present")
    require(len(critical) == 17 and all(r["decision"] == "PASS" for r in critical), "critical manual ledger invalid")
    require(len(relationship) == 17 and all(r["decision"] == "PASS" for r in relationship), "relationship manual ledger invalid")
    require(len(endpoint) == 6 and all(r["decision"] == "PASS" for r in endpoint), "endpoint manual ledger invalid")
    require(len(views) == 70 and all(r["result"] == "PASS" for r in views), "manual view ledger invalid")
    require(all((ROOT / r["view_path"]).is_file() for r in views), "manual view path missing")

    require(len(rows("after_overlap_report.csv")) == 13366, "all-pairs ledger count mismatch")
    require(len(rows("raw_overlap_pairs.csv")) == 17, "raw overlap count mismatch")
    require(len(rows("critical_index.csv")) == 17, "critical machine count mismatch")
    require(len(rows("relationship_index.csv")) == 17, "relationship machine count mismatch")
    require(len(rows("connection_continuity_ledger.csv")) == 6, "endpoint machine count mismatch")
    summary = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))
    require(summary["total_visible_object_count"] == 164, "machine visible denominator mismatch")
    require(summary["unordered_pair_count"] == 13366, "machine unordered pair count mismatch")
    require(summary["empty_visible_masks"] == 0, "empty visible mask detected")
    require(summary["replacement_or_tofu_codepoint_flags"] == 0, "replacement/tofu flag detected")
    require(summary["below_numeric_gate_pair_count_machine"] == 0, "below-gate pair detected")
    require((ROOT / "RESULT.txt").read_text(encoding="utf-8").strip() == "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3", "route mismatch")

    for path in ROOT.rglob("*"):
        lower = path.name.lower()
        require(lower != "__pycache__" and not lower.endswith(".pyc") and "cache" not in lower, f"cache/pyc forbidden: {path}")
        require(":" not in path.name, f"colon/ADS-like filename forbidden: {path}")


def main() -> None:
    validate()
    evidence_files = sorted(
        (p for p in ROOT.rglob("*") if p.is_file() and p.name not in EXCLUDED),
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )
    entries: list[dict[str, object]] = []
    for path in evidence_files:
        entries.append(
            {
                "path": f"evidence/{path.relative_to(ROOT).as_posix()}",
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )
    for label, path in (("external_report", REPORT), ("external_handoff", HANDOFF)):
        entries.append({"path": label, "absolute_path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)})

    manifest = {
        "schema": "FIG-P598-01-R104-R168-FRESH-SA1-DUAL-MANIFEST-v1",
        "handoff_id": "A-R104-P598-01-SA1-FRESH-20260825",
        "instance": "/root/p598_01_r104_fresh_sa1",
        "reviewer_uid": "SA1_FRESH_gpt-5.6-sol_xhigh",
        "model_effort": "gpt-5.6-sol/xhigh",
        "verdict": "PASS",
        "route": "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3",
        "entry_count": len(entries),
        "excluded_self_referential_files": [HASH_MANIFEST.name, JSON_MANIFEST.name, STOP.name],
        "entries": entries,
    }
    JSON_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HASH_MANIFEST.write_text(
        "".join(f'{entry["sha256"]}  {entry["path"]}\n' for entry in entries),
        encoding="utf-8",
    )

    hash_manifest_sha = digest(HASH_MANIFEST)
    json_manifest_sha = digest(JSON_MANIFEST)
    time.sleep(1.1)
    stopped_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    STOP.write_text(
        "\n".join(
            [
                "WRITE_STOPPED",
                "HANDOFF_ID=A-R104-P598-01-SA1-FRESH-20260825",
                "INSTANCE=/root/p598_01_r104_fresh_sa1",
                "MODEL_EFFORT=gpt-5.6-sol/xhigh",
                "VERDICT=PASS",
                "ROUTE=SA1_PASS_AWAIT_FRESH_ISOLATED_SA3",
                f"SEALED_ENTRY_COUNT={len(entries)}",
                f"SEALED_MANIFEST_SHA256={hash_manifest_sha}",
                f"SEALED_MANIFEST_JSON_SHA256={json_manifest_sha}",
                f"STOPPED_AT_UTC={stopped_at}",
                "POST_SEAL_WRITES=0",
                "",
            ]
        ),
        encoding="utf-8",
    )

    for path in sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: str(p)):
        set_read_only(path)
    set_read_only(REPORT)
    set_read_only(HANDOFF)

    print(json.dumps({"sealed": True, "entry_count": len(entries), "write_stopped": str(STOP)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
