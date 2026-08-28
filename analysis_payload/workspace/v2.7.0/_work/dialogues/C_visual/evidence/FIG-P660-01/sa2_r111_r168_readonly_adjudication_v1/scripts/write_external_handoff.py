from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
import stat


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa2_r111_r168_readonly_adjudication_v1"
)
PARENT = ROOT.parent
STEM = "C-FIG-P660-01-R111-SA2-R168-READONLY-ADJUDICATION-V1"
MANIFEST = PARENT / f"{STEM}_SEALED_ROOT_MANIFEST.csv"
HANDOFF = PARENT / f"{STEM}_HANDOFF.md"
MARKER = ROOT / "08_seal" / "WRITE_STOPPED"
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

    if not ctypes.windll.kernel32.SetFileAttributesW(
        str(path), get_attributes(path) | FILE_ATTRIBUTE_READONLY
    ):
        raise OSError(f"SetFileAttributesW failed: {path}")


def main() -> None:
    if MANIFEST.exists() or HANDOFF.exists():
        raise SystemExit("external handoff already exists; refusing duplicate")
    entries = [ROOT, *sorted(ROOT.rglob("*"), key=lambda p: p.as_posix())]
    marker_mtime_ns = MARKER.stat().st_mtime_ns
    postmarker_count = sum(
        path != MARKER and path.stat().st_mtime_ns >= marker_mtime_ns for path in entries
    )
    nonreadonly = [path for path in entries if not (get_attributes(path) & FILE_ATTRIBUTE_READONLY)]
    reparses = [path for path in entries if get_attributes(path) & FILE_ATTRIBUTE_REPARSE_POINT]
    caches = [
        path
        for path in entries
        if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"}
    ]
    marker_count = sum(path.name == "WRITE_STOPPED" for path in entries)
    if marker_count != 1 or postmarker_count != 0 or nonreadonly or reparses or caches:
        raise SystemExit("sealed-root precondition failed; external files not created")

    with MANIFEST.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "absolute_path",
                "relative_path",
                "entry_type",
                "bytes",
                "sha256",
                "creation_utc_ticks",
                "lastwrite_utc_ticks",
                "windows_attributes_hex",
            ]
        )
        for path in entries:
            info = path.stat()
            relative = "." if path == ROOT else path.relative_to(ROOT).as_posix()
            writer.writerow(
                [
                    str(path),
                    relative,
                    "directory" if path.is_dir() else "file",
                    0 if path.is_dir() else info.st_size,
                    "DIRECTORY" if path.is_dir() else sha256(path),
                    ticks_from_ns(info.st_ctime_ns),
                    ticks_from_ns(info.st_mtime_ns),
                    f"0x{get_attributes(path):08X}",
                ]
            )

    manifest_hash = sha256(MANIFEST)
    HANDOFF.write_text(
        "\n".join(
            [
                "# Sealed SA2 handoff",
                "",
                f"- HANDOFF_ID: `{STEM}`",
                "- canonical UID: `FIG-P660-01`",
                f"- sealed evidence root: `{ROOT}`",
                "- disposition: `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`",
                f"- final root files: {sum(path.is_file() for path in entries)}",
                f"- final root directories including root: {sum(path.is_dir() for path in entries)}",
                f"- sealed-root manifest: `{MANIFEST}`",
                f"- sealed-root manifest bytes: {MANIFEST.stat().st_size}",
                f"- sealed-root manifest SHA-256: `{manifest_hash}`",
                f"- WRITE_STOPPED bytes: {MARKER.stat().st_size}",
                f"- WRITE_STOPPED SHA-256: `{sha256(MARKER)}`",
                f"- WRITE_STOPPED creation UTC ticks: {ticks_from_ns(MARKER.stat().st_ctime_ns)}",
                f"- WRITE_STOPPED last-write UTC ticks: {ticks_from_ns(MARKER.stat().st_mtime_ns)}",
                "- WRITE_STOPPED count: 1",
                "- postmarker root writes: 0",
                "- non-ReadOnly root entries: 0",
                "- reparse points: 0",
                "- cache/pyc/pyo entries: 0",
                "- non-default ADS: 0 (postseal read-only PowerShell audit; the external report does not mutate the sealed root)",
                "",
                "The complete current simplex figure was independently adjudicated. No genuine R168 hard defect was found; no source or build was changed.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    set_readonly(MANIFEST)
    set_readonly(HANDOFF)
    set_readonly(PARENT)
    print(str(MANIFEST))
    print(str(HANDOFF))
    print(manifest_hash)


if __name__ == "__main__":
    main()
