"""Build the final content manifest, excluding the manifest and seal marker."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"
FILETIME_EPOCH_DELTA_100NS = 116444736000000000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def utc_mtime_and_filetime(path: Path) -> tuple[str, int]:
    stat = path.stat()
    unix_100ns = stat.st_mtime_ns // 100
    seconds, fraction_100ns = divmod(unix_100ns, 10_000_000)
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    utc_text = f"{dt:%Y-%m-%dT%H:%M:%S}.{fraction_100ns:07d}Z"
    return utc_text, unix_100ns + FILETIME_EPOCH_DELTA_100NS


excluded = {MANIFEST.resolve(), MARKER.resolve()}
paths = sorted(
    (path.resolve() for path in ROOT.rglob("*") if path.is_file() and path.resolve() not in excluded),
    key=lambda path: str(path).casefold(),
)
entries = []
for path in paths:
    utc_mtime, filetime = utc_mtime_and_filetime(path)
    entries.append(
        {
            "relative_path": path.relative_to(ROOT.resolve()).as_posix(),
            "resolved_path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "utc_mtime": utc_mtime,
            "filetime_100ns": filetime,
        }
    )

payload = {
    "schema": "FIGURE_FRESH_EVIDENCE_MANIFEST_V1",
    "handoff_id": "C-FIG-P603-01-R104-SA1-FRESH-ISOLATED-V1",
    "uid": "FIG-P603-01",
    "revision": "R104",
    "evidence_root_resolved": str(ROOT.resolve()),
    "entry_count": len(entries),
    "exclusions": [
        {"relative_path": "MANIFEST.json", "reason": "manifest must not self-list"},
        {"relative_path": "WRITE_STOPPED", "reason": "seal marker is created strictly after manifest and must not be listed"},
    ],
    "entries": entries,
}
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"manifest": str(MANIFEST), "entry_count": len(entries)}, ensure_ascii=False))
