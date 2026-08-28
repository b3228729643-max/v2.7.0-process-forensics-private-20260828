from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evidence_manifest.csv"
MARKER = ROOT / "WRITE_STOPPED.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_100ns(mtime_ns: int) -> str:
    seconds, remainder_ns = divmod(mtime_ns, 1_000_000_000)
    base = datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{remainder_ns // 100:07d}Z"


def main() -> None:
    if MARKER.exists():
        raise SystemExit("WRITE_STOPPED.json already exists")
    if not MANIFEST.is_file():
        raise SystemExit("evidence_manifest.csv is missing")

    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    listed = [row["relative_path"] for row in rows]
    if len(listed) != len(set(listed)):
        raise SystemExit("duplicate manifest paths")

    present_before_marker = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != MARKER
    )
    expected_listed = sorted(path for path in present_before_marker if path != "evidence_manifest.csv")
    if sorted(listed) != expected_listed:
        raise SystemExit("manifest coverage does not exactly match pre-marker ordinary files")

    manifest_stat = MANIFEST.stat()
    payload = {
        "uid": "FIG-P602-01",
        "review": "fresh isolated SA3 official R101",
        "RESULT": "FAIL",
        "FIGURE_STRICT_RESULT": "FAIL",
        "PACKAGE_COMPLETENESS": "PASS",
        "official_inputs": {
            "pdf": {
                "bytes": 4947496,
                "sha256": "0870ff226dc383875c4a1b6eabb06aab942317da294d90d2864b3030d46df1a1",
                "mtime_ns": 1787597833697911500,
                "page_count": 814,
                "target_physical_page": 651,
                "target_printed_page": 638,
            },
            "figure_source": {
                "bytes": 2711,
                "sha256": "18b88f4bc48a21d3fd1a246ac5b6909deeb19900a3d0721c65f9a44369444084",
                "mtime_ns": 1787625127884934000,
            },
            "chapter_source": {
                "bytes": 105168,
                "sha256": "00f3537ae9dd6738f1bab414d587f18870a6b08d64663283c6f9a3f3048e6ba7",
                "mtime_ns": 1787625128206720800,
            },
        },
        "denominators": {
            "objects": {"total": 32, "PASS": 32, "FAIL": 0},
            "glyphs": {"total": 175, "PASS": 158, "FAIL": 17},
            "unordered_pairs": {"total": 496, "PASS": 496, "FAIL": 0, "c_n_2": 496},
            "critical_pairs": {"total": 17, "PASS": 17, "FAIL": 0},
            "peer": {"total": 42, "PASS": 36, "FAIL": 6},
            "role": {"total": 3, "PASS": 2, "FAIL": 1},
            "clip": {"total": 32, "PASS": 32, "FAIL": 0},
            "mandatory_views": {"total": 4, "PASS": 4, "FAIL": 0},
            "hard_gates": {"total": 12, "PASS": 8, "FAIL": 4},
        },
        "manifest": {
            "path": "evidence_manifest.csv",
            "bytes": manifest_stat.st_size,
            "sha256": sha256(MANIFEST),
            "mtime_utc_100ns": utc_100ns(manifest_stat.st_mtime_ns),
            "mtime_unix_100ns": manifest_stat.st_mtime_ns // 100,
            "mtime_ns": manifest_stat.st_mtime_ns,
            "listed_rows": len(rows),
            "coverage": "all ordinary files except evidence_manifest.csv and WRITE_STOPPED.json",
            "unlisted_exact": ["evidence_manifest.csv", "WRITE_STOPPED.json"],
            "final_ordinary_file_count": len(rows) + 2,
        },
        "seal": {
            "policy": "WRITE_STOPPED.json is the strictly last file written; all post-seal checks are read-only and are reported externally",
            "post_marker_writes_authorized": 0,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        },
        "boundaries": {
            "business_sources_read_only": True,
            "tex_or_build_invoked": False,
            "source_or_central_state_written": False,
            "prior_or_sibling_evidence_read": False,
        },
    }

    MARKER.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
