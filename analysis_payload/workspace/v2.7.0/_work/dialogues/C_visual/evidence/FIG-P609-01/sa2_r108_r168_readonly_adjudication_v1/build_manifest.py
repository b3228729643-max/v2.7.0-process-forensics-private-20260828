import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa2_r108_r168_readonly_adjudication_v1")
MANIFEST_NAME = "evidence_manifest.json"
EXCLUSIONS = [MANIFEST_NAME, "SEAL.json", "WRITE_STOPPED"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


entries = []
for path in sorted(ROOT.iterdir(), key=lambda item: item.name.casefold()):
    if path.name in EXCLUSIONS:
        continue
    if not path.is_file():
        raise RuntimeError(f"Non-file payload entry is not allowed: {path}")
    entries.append({
        "path": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    })

manifest = {
    "schema": "FIG-P609-01-evidence-manifest-v1",
    "root": str(ROOT),
    "manifest_self": MANIFEST_NAME,
    "excluded_control_files": EXCLUSIONS,
    "payload_count": len(entries),
    "entries": entries,
}
(ROOT / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

