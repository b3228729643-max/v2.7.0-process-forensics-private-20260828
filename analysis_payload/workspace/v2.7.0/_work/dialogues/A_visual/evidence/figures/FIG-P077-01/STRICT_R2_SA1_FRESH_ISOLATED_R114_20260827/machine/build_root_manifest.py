from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R2_SA1_FRESH_ISOLATED_R114_20260827")
OUTPUT = ROOT / "audit" / "ROOT_CONTENT_MANIFEST.json"
EXCLUDED = {"audit/ROOT_CONTENT_MANIFEST.json", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()


files = []
for path in sorted(ROOT.rglob("*"), key=lambda p: p.relative_to(ROOT).as_posix().lower()):
    if not path.is_file():
        continue
    rel = path.relative_to(ROOT).as_posix()
    if rel in EXCLUDED:
        continue
    files.append({"relative_path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})

directories = [
    p.relative_to(ROOT).as_posix()
    for p in sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: p.relative_to(ROOT).as_posix().lower())
]
manifest = {
    "schema": "FIGURE_FRESH_SA1_ROOT_CONTENT_MANIFEST_V1",
    "figure_id": "FIG-P077-01",
    "handoff_id": "A-R114-P077-SA1-FRESH-ISOLATED-20260827",
    "result": "PASS",
    "listed_file_count": len(files),
    "listed_directory_count": len(directories),
    "listed_total_bytes": sum(x["bytes"] for x in files),
    "excluded_self": "audit/ROOT_CONTENT_MANIFEST.json",
    "expected_final_unlisted_marker": "WRITE_STOPPED",
    "directories": directories,
    "files": files,
}
OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"listed_file_count": len(files), "listed_directory_count": len(directories),
                  "listed_total_bytes": manifest["listed_total_bytes"]}, separators=(",", ":")))
