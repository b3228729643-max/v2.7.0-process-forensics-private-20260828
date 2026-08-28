from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa2_r111_r168_readonly_adjudication_v1"
)
SEAL_DIR = ROOT / "08_seal"
PAYLOAD_MANIFEST = SEAL_DIR / "MANIFEST_PAYLOAD.csv"
MANIFEST_CLOSURE = SEAL_DIR / "MANIFEST_CLOSURE.txt"
MARKER = SEAL_DIR / "WRITE_STOPPED"
WINDOWS_EPOCH_TICKS = 621355968000000000
FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def ticks_from_ns(value: int) -> int:
    return WINDOWS_EPOCH_TICKS + value // 100


def get_attributes(path: Path) -> int:
    if os.name != "nt":
        return 0
    import ctypes

    value = ctypes.windll.kernel32.GetFileAttributesW(str(path))
    if value == 0xFFFFFFFF:
        raise OSError(f"GetFileAttributesW failed: {path}")
    return int(value)


def set_readonly(path: Path) -> None:
    if os.name != "nt":
        path.chmod(path.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
        return
    import ctypes

    attributes = get_attributes(path) | FILE_ATTRIBUTE_READONLY
    if not ctypes.windll.kernel32.SetFileAttributesW(str(path), attributes):
        raise OSError(f"SetFileAttributesW failed: {path}")


def entry_row(path: Path) -> list[str | int]:
    info = path.stat()
    relative = "." if path == ROOT else path.relative_to(ROOT).as_posix()
    if path.is_dir():
        return [
            relative,
            "directory",
            0,
            "DIRECTORY",
            ticks_from_ns(info.st_ctime_ns),
            ticks_from_ns(info.st_mtime_ns),
            f"0x{get_attributes(path):08X}",
        ]
    return [
        relative,
        "file",
        info.st_size,
        sha256(path),
        ticks_from_ns(info.st_ctime_ns),
        ticks_from_ns(info.st_mtime_ns),
        f"0x{get_attributes(path):08X}",
    ]


def main() -> None:
    if MARKER.exists():
        raise SystemExit("WRITE_STOPPED already exists; refusing a second seal")
    if PAYLOAD_MANIFEST.exists() or MANIFEST_CLOSURE.exists():
        raise SystemExit("seal manifest already exists; refusing restart or duplicate")

    payload_entries = [ROOT, *sorted(ROOT.rglob("*"), key=lambda p: p.as_posix())]
    with PAYLOAD_MANIFEST.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "relative_path",
                "entry_type",
                "bytes",
                "sha256",
                "creation_utc_ticks",
                "lastwrite_utc_ticks",
                "attributes_before_seal",
            ]
        )
        for path in payload_entries:
            writer.writerow(entry_row(path))

    manifest_info = PAYLOAD_MANIFEST.stat()
    manifest_hash = sha256(PAYLOAD_MANIFEST)
    file_count = sum(path.is_file() for path in payload_entries)
    directory_count = sum(path.is_dir() for path in payload_entries)
    MANIFEST_CLOSURE.write_text(
        "\n".join(
            [
                "HANDOFF_ID=C-FIG-P660-01-R111-SA2-R168-READONLY-ADJUDICATION-V1",
                "DISPOSITION=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1",
                f"PAYLOAD_MANIFEST_PATH={PAYLOAD_MANIFEST.relative_to(ROOT).as_posix()}",
                f"PAYLOAD_MANIFEST_BYTES={manifest_info.st_size}",
                f"PAYLOAD_MANIFEST_SHA256={manifest_hash}",
                f"PAYLOAD_MANIFEST_CREATION_UTC_TICKS={ticks_from_ns(manifest_info.st_ctime_ns)}",
                f"PAYLOAD_MANIFEST_LASTWRITE_UTC_TICKS={ticks_from_ns(manifest_info.st_mtime_ns)}",
                f"PAYLOAD_FILE_COUNT={file_count}",
                f"PAYLOAD_DIRECTORY_COUNT_INCLUDING_ROOT={directory_count}",
                "SELF_REFERENCE_POLICY=MANIFEST_PAYLOAD excludes itself, MANIFEST_CLOSURE, and the future final marker; a root-external sealed-root manifest closes every final root entry after WRITE_STOPPED without mutating the sealed root",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    existing = [ROOT, *sorted(ROOT.rglob("*"), key=lambda p: (len(p.parts), p.as_posix()), reverse=True)]
    files = [path for path in existing if path.is_file()]
    directories = [path for path in existing if path.is_dir()]
    for path in files:
        set_readonly(path)
    for path in directories:
        set_readonly(path)

    marker_text = "\n".join(
        [
            "HANDOFF_ID=C-FIG-P660-01-R111-SA2-R168-READONLY-ADJUDICATION-V1",
            "CANONICAL_UID=FIG-P660-01",
            "DISPOSITION=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1",
            f"PAYLOAD_MANIFEST_SHA256={manifest_hash}",
            "ROOT_CONTENT_WRITES_STOPPED=true",
            "POSTMARKER_ROOT_WRITES_ALLOWED=0",
        ]
    ) + "\n"
    descriptor = os.open(MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        data = marker_text.encode("utf-8")
        os.write(descriptor, data)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

    all_after_creation = [ROOT, *ROOT.rglob("*")]
    latest_before_marker_touch = max(path.stat().st_mtime_ns for path in all_after_creation)
    marker_target_ns = latest_before_marker_touch + 10_000_000_000
    os.utime(MARKER, ns=(marker_target_ns, marker_target_ns))
    set_readonly(MARKER)

    final_entries = [ROOT, *ROOT.rglob("*")]
    marker_count = sum(path.name == "WRITE_STOPPED" for path in final_entries)
    marker_mtime_ns = MARKER.stat().st_mtime_ns
    postmarker_count = sum(
        path != MARKER and path.stat().st_mtime_ns >= marker_mtime_ns for path in final_entries
    )
    nonreadonly = [
        path.relative_to(ROOT).as_posix() if path != ROOT else "."
        for path in final_entries
        if not (get_attributes(path) & FILE_ATTRIBUTE_READONLY)
    ]
    reparses = [
        path.relative_to(ROOT).as_posix() if path != ROOT else "."
        for path in final_entries
        if get_attributes(path) & FILE_ATTRIBUTE_REPARSE_POINT
    ]
    caches = [
        path.relative_to(ROOT).as_posix()
        for path in final_entries
        if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"}
    ]
    result = {
        "root": str(ROOT),
        "marker_count": marker_count,
        "marker_bytes": MARKER.stat().st_size,
        "marker_sha256": sha256(MARKER),
        "marker_creation_utc_ticks": ticks_from_ns(MARKER.stat().st_ctime_ns),
        "marker_lastwrite_utc_ticks": ticks_from_ns(MARKER.stat().st_mtime_ns),
        "postmarker_count_ge": postmarker_count,
        "nonreadonly_count": len(nonreadonly),
        "reparse_count": len(reparses),
        "cache_pyc_count": len(caches),
        "final_file_count": sum(path.is_file() for path in final_entries),
        "final_directory_count_including_root": sum(path.is_dir() for path in final_entries),
        "payload_manifest_sha256": manifest_hash,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if marker_count != 1 or postmarker_count != 0 or nonreadonly or reparses or caches:
        raise SystemExit("seal verification failed without making any postmarker root write")


if __name__ == "__main__":
    main()
