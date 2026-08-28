from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P630-01\sa3_r109_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.sha256"
MARKER = ROOT / "WRITE_STOPPED"
MANIFEST_ID = "C-FIG-P630-01-R109-SA3-FRESH-ISOLATED-V1-MANIFEST"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    if MANIFEST.exists():
        raise RuntimeError("manifest already exists; refusing overwrite")
    if MARKER.exists():
        raise RuntimeError("WRITE_STOPPED already exists; refusing pre-marker write")
    if any(path.is_dir() for path in ROOT.iterdir()):
        raise RuntimeError("unexpected subdirectory in sealed root")
    if any(path.is_symlink() for path in ROOT.iterdir()):
        raise RuntimeError("unexpected symlink in sealed root")

    files = sorted(
        (path for path in ROOT.iterdir() if path.is_file() and path.name not in {MANIFEST.name, MARKER.name}),
        key=lambda path: path.name.casefold(),
    )
    lines = [
        f"MANIFEST_ID={MANIFEST_ID}",
        "HASH_ALGORITHM=SHA256",
        "CLOSURE_SCOPE=ALL_REGULAR_ROOT_FILES_PRESENT_IMMEDIATELY_BEFORE_MANIFEST_CREATION",
        "SELF_ENTRY=MANIFEST.sha256|SELF_UNHASHED_NONCIRCULAR",
        "EXCLUDED_MARKER=WRITE_STOPPED",
        "MARKER_HASH_PREDICTED=false",
        "MARKER_CREATION_ORDER=STRICTLY_AFTER_ALL_REPORTS_HANDOFF_AND_MANIFEST",
        f"HASHED_ENTRY_COUNT={len(files)}",
        "FILES_BEGIN",
    ]
    for path in files:
        lines.append(f"{sha256(path)}|{path.stat().st_size}|{path.name}")
    lines.append("FILES_END")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"manifest_id={MANIFEST_ID}")
    print(f"hashed_entry_count={len(files)}")
    print("marker_excluded=true")
    print("marker_hash_predicted=false")


if __name__ == "__main__":
    main()
