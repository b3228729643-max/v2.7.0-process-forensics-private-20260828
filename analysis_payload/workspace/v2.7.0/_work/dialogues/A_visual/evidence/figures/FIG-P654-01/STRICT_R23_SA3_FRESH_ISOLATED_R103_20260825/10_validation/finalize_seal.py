from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R23_SA3_FRESH_ISOLATED_R103_20260825")
MANIFEST_DIR = ROOT / "11_manifests"
JSON_MANIFEST = MANIFEST_DIR / "MANIFEST.json"
SHA_MANIFEST = MANIFEST_DIR / "MANIFEST.sha256"
MARKER = ROOT / "WRITE_STOPPED"
EXCLUDED = {
    "11_manifests/MANIFEST.json",
    "11_manifests/MANIFEST.sha256",
    "WRITE_STOPPED",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


if MARKER.exists():
    raise RuntimeError("WRITE_STOPPED already exists; refusing any post-seal write")

MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
files = []
for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
    rel = path.relative_to(ROOT).as_posix()
    if rel in EXCLUDED:
        continue
    if ":" in path.name:
        raise RuntimeError(f"Non-portable colon filename: {rel}")
    if path.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in path.parts or "cache" in {part.lower() for part in path.parts}:
        raise RuntimeError(f"Cache artifact present: {rel}")
    files.append({"path": rel, "size_bytes": path.stat().st_size, "sha256": sha256(path)})

payload = {
    "manifest_schema": "FIGURE_FRESH_SA3_DOUBLE_MANIFEST_V1",
    "handoff_id": "A-R103-P654-SA3-FRESH-ISOLATED-20260825",
    "uid": "FIG-P654-01",
    "root": str(ROOT),
    "entry_count": len(files),
    "total_bytes": sum(row["size_bytes"] for row in files),
    "exclusions": sorted(EXCLUDED),
    "entries": files,
}
JSON_MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
SHA_MANIFEST.write_text("".join(f"{row['sha256']} *{row['path']}\n" for row in files), encoding="utf-8")

# Cross-read both manifests before the stop marker.
json_check = json.loads(JSON_MANIFEST.read_text(encoding="utf-8"))
sha_lines = [line for line in SHA_MANIFEST.read_text(encoding="utf-8").splitlines() if line]
if json_check["entry_count"] != len(files) or len(sha_lines) != len(files):
    raise RuntimeError("Double-manifest count mismatch")
expected_lines = [f"{row['sha256']} *{row['path']}" for row in files]
if sha_lines != expected_lines:
    raise RuntimeError("Double-manifest content mismatch")

# This is intentionally the final content write inside the evidence root.
MARKER.write_text(
    "HANDOFF_ID=A-R103-P654-SA3-FRESH-ISOLATED-20260825\n"
    "UID=FIG-P654-01\n"
    "SA3_VERDICT=PASS\n"
    "ROUTE=SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE\n"
    f"MANIFEST_ENTRY_COUNT={len(files)}\n"
    "WRITE_STOPPED_STRICTLY_LAST=true\n",
    encoding="ascii",
)
print(json.dumps({"entry_count": len(files), "total_bytes": payload["total_bytes"], "json_manifest": str(JSON_MANIFEST), "sha_manifest": str(SHA_MANIFEST), "marker": str(MARKER)}, indent=2))
