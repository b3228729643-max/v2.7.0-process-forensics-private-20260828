from __future__ import annotations

import ctypes
import hashlib
import os
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P667-01\sa1_r114_fresh_isolated_v1")
HANDOFF_ID = "C-FIG-P667-01-R114-SA1-FRESH-ISOLATED-V1"
UID = "FIG-P667-01"
VERDICT = "PASS"
TEMP_MARKER = ROOT.parent / ".C-FIG-P667-01-R114-SA1-FRESH-ISOLATED-V1.WRITE_STOPPED.tmp"
FINAL_MARKER = ROOT / "WRITE_STOPPED"
READONLY = 0x1


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
get_attrs = kernel32.GetFileAttributesW
get_attrs.argtypes = [ctypes.c_wchar_p]
get_attrs.restype = ctypes.c_uint32
set_attrs = kernel32.SetFileAttributesW
set_attrs.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32]
set_attrs.restype = ctypes.c_int


def make_readonly(path: Path) -> None:
    attrs = get_attrs(str(path))
    if attrs == 0xFFFFFFFF:
        raise OSError(ctypes.get_last_error(), f"GetFileAttributesW failed: {path}")
    if not set_attrs(str(path), attrs | READONLY):
        raise OSError(ctypes.get_last_error(), f"SetFileAttributesW failed: {path}")


def is_readonly(path: Path) -> bool:
    attrs = get_attrs(str(path))
    if attrs == 0xFFFFFFFF:
        raise OSError(ctypes.get_last_error(), f"GetFileAttributesW failed: {path}")
    return bool(attrs & READONLY)


def main() -> None:
    if FINAL_MARKER.exists() or TEMP_MARKER.exists():
        raise RuntimeError("marker target or exact temporary marker already exists")
    manifest = ROOT / "MANIFEST.tsv"
    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "RELATIVE_PATH\tBYTES\tSHA256":
        raise RuntimeError("manifest header mismatch")
    rows = len(lines) - 1
    manifest_sha = digest(manifest)

    # All root file content is complete before attributes and marker creation.
    files = sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.as_posix().casefold())
    dirs = sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True)
    for p in files:
        make_readonly(p)
    for p in dirs:
        make_readonly(p)
    make_readonly(ROOT)
    for p in files + dirs + [ROOT]:
        if not is_readonly(p):
            raise RuntimeError(f"read-only attribute failed: {p}")

    # Marker is created outside the sealed root only after all premarker work.
    content = (
        f"HANDOFF_ID={HANDOFF_ID}\n"
        f"UID={UID}\n"
        f"SEALED_ROOT={ROOT}\n"
        f"MANIFEST_ROWS={rows}\n"
        f"MANIFEST_SHA256={manifest_sha}\n"
        f"VERDICT={VERDICT}\n"
    )
    TEMP_MARKER.write_text(content, encoding="utf-8", newline="\n")
    max_root_mtime_ns = max(p.stat().st_mtime_ns for p in files)
    marker_mtime_ns = max_root_mtime_ns + 10_000_000_000
    os.utime(TEMP_MARKER, ns=(marker_mtime_ns, marker_mtime_ns))
    make_readonly(TEMP_MARKER)
    if TEMP_MARKER.stat().st_mtime_ns <= max_root_mtime_ns or not is_readonly(TEMP_MARKER):
        raise RuntimeError("temporary marker ordering/attribute failure")

    # Unique final root content operation. No root operation is performed afterward.
    os.replace(TEMP_MARKER, FINAL_MARKER)
    print(f"SEALED_ROOT={ROOT}")
    print(f"MANIFEST_ROWS={rows}")
    print(f"MANIFEST_SHA256={manifest_sha}")
    print(f"VERDICT={VERDICT}")


if __name__ == "__main__":
    main()
