from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"
EPOCH_FILETIME_100NS = 116444736000000000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def exact_utc_from_ns(mtime_ns: int) -> str:
    seconds, nanoseconds = divmod(mtime_ns, 1_000_000_000)
    base = datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{nanoseconds // 100:07d}Z"


def record_class(relative: str) -> str:
    top = relative.split("/", 1)[0]
    if top in {"renders", "machine", "masks", "cards", "pairs", "manual"}:
        return "payload"
    if relative in {"SA3_REPORT.md", "RESULT.json", "HANDOFF.md"}:
        return "seal"
    if relative in {"IDENTITY.md", "EVIDENCE_INDEX.md"} or relative.endswith(".py"):
        return "control"
    raise RuntimeError(f"Unclassified record: {relative}")


files = sorted(
    (path for path in ROOT.rglob("*") if path.is_file() and path not in {MANIFEST, MARKER}),
    key=lambda path: path.relative_to(ROOT).as_posix().casefold(),
)

entries = []
for ordinal, path in enumerate(files, start=1):
    relative = path.relative_to(ROOT).as_posix()
    stat = path.stat()
    entries.append(
        {
            "ordinal": ordinal,
            "relative_path": relative,
            "resolved_path": str(path.resolve()),
            "record_class": record_class(relative),
            "bytes": stat.st_size,
            "sha256": sha256_file(path),
            "mtime_utc_exact_100ns": exact_utc_from_ns(stat.st_mtime_ns),
            "mtime_filetime_100ns": EPOCH_FILETIME_100NS + stat.st_mtime_ns // 100,
        }
    )

canonical_recordset = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
recordset_sha256 = hashlib.sha256(canonical_recordset).hexdigest().upper()

class_counts = {name: sum(entry["record_class"] == name for entry in entries) for name in ("payload", "control", "seal")}
class_bytes = {name: sum(entry["bytes"] for entry in entries if entry["record_class"] == name) for name in ("payload", "control", "seal")}

manifest = {
    "schema": "FIGURE_SA3_FRESH_ISOLATED_MANIFEST_V1",
    "uid": "FIG-P637-01",
    "release": "R103",
    "role": "SA3_FRESH_ISOLATED",
    "handoff_id": "C-FIG-P637-01-R103-SA3-FRESH-ISOLATED-V1",
    "root_resolved_path": str(ROOT.resolve()),
    "scope_definition": {
        "payload": "evidentiary renders, machine inventories, masks, cards, pair artifacts, and manually authored ledgers",
        "control": "fixed identity/index and local machine-only build, supplement, cross-check, and manifest scripts",
        "seal": "self-contained SA3 report, machine-readable result, and concise handoff",
        "self": "MANIFEST.json; intentionally excluded from its own file records and recordset hash",
        "marker": "WRITE_STOPPED; intentionally excluded and written strictly after manifest/content readonly sealing",
    },
    "inclusion_rule": "every regular file recursively under root except MANIFEST.json and WRITE_STOPPED",
    "manifest_self_listed": False,
    "marker_listed": False,
    "recordset_canonicalization": "UTF-8 JSON of entries with ensure_ascii=false, sort_keys=true, separators comma/colon, in relative-path casefold order",
    "entry_count": len(entries),
    "total_bytes": sum(entry["bytes"] for entry in entries),
    "class_counts": class_counts,
    "class_bytes": class_bytes,
    "recordset_sha256": recordset_sha256,
    "entries": entries,
}

MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"entry_count": len(entries), "recordset_sha256": recordset_sha256, "class_counts": class_counts}, ensure_ascii=False))
