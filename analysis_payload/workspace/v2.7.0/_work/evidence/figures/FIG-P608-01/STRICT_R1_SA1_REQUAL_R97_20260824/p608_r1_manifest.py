"""Create final self-exclusion-disclosed manifests, then WRITE_STOPPED last."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P608-01\STRICT_R1_SA1_REQUAL_R97_20260824")
MANIFEST = OUT / "MANIFEST.sha256"
EVIDENCE = OUT / "evidence_manifest.json"
STOP = OUT / "WRITE_STOPPED"
SELF_EXCLUSIONS = {"MANIFEST.sha256", "evidence_manifest.json", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest().upper()


def records():
    rows = []
    for p in sorted(q for q in OUT.rglob("*") if q.is_file()):
        rel = p.relative_to(OUT).as_posix()
        if rel in SELF_EXCLUSIONS:
            continue
        rows.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha256(p)})
    return rows


def main():
    if STOP.exists() or MANIFEST.exists() or EVIDENCE.exists():
        raise RuntimeError("terminal manifest artifacts already exist; refusing any post-stop overwrite")
    if not (OUT / "terminal_status.json").is_file() or not (OUT / "terminal_status.md").is_file():
        raise RuntimeError("terminal must exist before manifest")
    rows = records()
    if not rows or any(r["bytes"] == 0 for r in rows):
        raise RuntimeError("manifest scope has no files or contains zero-byte file")
    MANIFEST.write_text("".join(f"{r['sha256']} *{r['path']}\n" for r in rows), encoding="utf-8")
    manifest_sha = sha256(MANIFEST)
    evidence = {
        "schema": "STRICT_FIGURE_EVIDENCE_MANIFEST_V1",
        "audit_directory": str(OUT),
        "scope": "Every regular package file that existed immediately before manifest creation.",
        "entry_count": len(rows),
        "entries": rows,
        "manifest_sha256": manifest_sha,
        "self_referential_exclusions": {
            "MANIFEST.sha256": "cannot hash itself while being its own hash list",
            "evidence_manifest.json": "cannot contain a stable hash of itself",
            "WRITE_STOPPED": "is deliberately written after both manifests as the required final write",
        },
        "terminal_status": "FAIL_TO_SA2",
        "terminal_sha256": sha256(OUT / "terminal_status.json"),
    }
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Verify all content captured by the two manifests before issuing the stop.
    refreshed = {r["path"]: r for r in records()}
    expected = {r["path"]: r for r in rows}
    actual_rel = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()}
    if set(refreshed) != set(expected) or actual_rel != set(expected) | {"MANIFEST.sha256", "evidence_manifest.json"}:
        raise RuntimeError("unexpected package content while manifesting")
    for rel, row in expected.items():
        p = OUT / rel
        if sha256(p) != row["sha256"] or p.stat().st_size != row["bytes"]:
            raise RuntimeError(f"post-manifest content changed: {rel}")
    stop = {
        "status": "WRITE_STOPPED",
        "terminal_status": "FAIL_TO_SA2",
        "written_last": True,
        "manifest_entry_count": len(rows),
        "manifest_sha256": manifest_sha,
        "evidence_manifest_sha256": sha256(EVIDENCE),
        "terminal_status_sha256": sha256(OUT / "terminal_status.json"),
        "self_referential_exclusions": sorted(SELF_EXCLUSIONS),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "instruction": "No further writes are permitted in this evidence directory.",
    }
    STOP.write_text(json.dumps(stop, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifested {len(rows)} files and wrote WRITE_STOPPED last")


if __name__ == "__main__":
    main()
