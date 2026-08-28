from __future__ import annotations

import hashlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P630-01\sa3_r109_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.sha256"
MARKER = ROOT / "WRITE_STOPPED"
MANIFEST_ID = "C-FIG-P630-01-R109-SA3-FRESH-ISOLATED-V1-MANIFEST"
WSTOP_ID = "C-FIG-P630-01-R109-SA3-FRESH-ISOLATED-V1-WRITE-STOPPED"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_manifest_before_marker() -> int:
    if not MANIFEST.is_file():
        raise RuntimeError("manifest missing")
    if MARKER.exists():
        raise RuntimeError("WRITE_STOPPED already exists; seal must occur exactly once")
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        f"MANIFEST_ID={MANIFEST_ID}",
        "SELF_ENTRY=MANIFEST.sha256|SELF_UNHASHED_NONCIRCULAR",
        "EXCLUDED_MARKER=WRITE_STOPPED",
        "MARKER_HASH_PREDICTED=false",
    ]
    if any(item not in text for item in required):
        raise RuntimeError("manifest noncircular contract missing")
    manifest_entries = {}
    in_files = False
    for line in text.splitlines():
        if line == "FILES_BEGIN":
            in_files = True
            continue
        if line == "FILES_END":
            in_files = False
            continue
        if in_files:
            digest, size, name = line.split("|", 2)
            manifest_entries[name] = (digest, int(size))
    actual_files = sorted(
        path for path in ROOT.iterdir() if path.is_file() and path.name not in {MANIFEST.name, MARKER.name}
    )
    if set(manifest_entries) != {path.name for path in actual_files}:
        raise RuntimeError("manifest closure mismatch")
    for path in actual_files:
        expected_hash, expected_size = manifest_entries[path.name]
        if path.stat().st_size != expected_size or sha256(path) != expected_hash:
            raise RuntimeError(f"manifest identity mismatch: {path.name}")
    return len(actual_files)


def set_readonly(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


def main() -> None:
    entry_count = validate_manifest_before_marker()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    marker_text = "\n".join(
        [
            f"WSTOP_ID={WSTOP_ID}",
            "HANDOFF_ID=C-FIG-P630-01-R109-SA3-FRESH-ISOLATED-V1",
            "UID=FIG-P630-01",
            "OFFICIAL_BUILD=R109",
            f"MANIFEST_ID={MANIFEST_ID}",
            f"PREMARKER_HASHED_ENTRY_COUNT={entry_count}",
            f"CREATED_UTC={timestamp}",
            "WRITE_STOPPED=true",
            "RESULT=SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
            "POST_MARKER_WRITES_ALLOWED=READONLY_ATTRIBUTE_APPLICATION_ONLY",
        ]
    ) + "\n"
    with MARKER.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(marker_text)

    for path in ROOT.iterdir():
        if path.is_file():
            set_readonly(path)
    set_readonly(ROOT)
    print(f"wstop_id={WSTOP_ID}")
    print(f"created_utc={timestamp}")
    print(f"premarker_hashed_entry_count={entry_count}")
    print("readonly_attributes_applied=true")


if __name__ == "__main__":
    main()
