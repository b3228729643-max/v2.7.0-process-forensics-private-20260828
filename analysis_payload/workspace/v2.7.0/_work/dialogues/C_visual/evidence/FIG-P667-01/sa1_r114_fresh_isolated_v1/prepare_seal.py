from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P667-01\sa1_r114_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_conjugate_update.tex")
HANDOFF_ID = "C-FIG-P667-01-R114-SA1-FRESH-ISOLATED-V1"
UID = "FIG-P667-01"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def all_entries() -> list[Path]:
    return sorted(ROOT.rglob("*"), key=lambda p: p.relative_to(ROOT).as_posix().casefold())


def named_ads(path: Path) -> list[str]:
    # FindFirstStreamW reports the default stream as ::$DATA. Any other stream is ADS.
    if os.name != "nt" or not path.is_file():
        return []
    import ctypes
    from ctypes import wintypes

    class WIN32_FIND_STREAM_DATA(ctypes.Structure):
        _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", wintypes.WCHAR * 296)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    find_first = kernel32.FindFirstStreamW
    find_first.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(WIN32_FIND_STREAM_DATA), wintypes.DWORD]
    find_first.restype = wintypes.HANDLE
    find_next = kernel32.FindNextStreamW
    find_next.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
    find_next.restype = wintypes.BOOL
    find_close = kernel32.FindClose
    find_close.argtypes = [wintypes.HANDLE]
    find_close.restype = wintypes.BOOL

    data = WIN32_FIND_STREAM_DATA()
    handle = find_first(str(path), 0, ctypes.byref(data), 0)
    invalid = wintypes.HANDLE(-1).value
    if handle == invalid:
        err = ctypes.get_last_error()
        if err in (38, 2):
            return []
        raise OSError(err, f"FindFirstStreamW failed for {path}")
    streams = []
    try:
        while True:
            name = data.cStreamName
            if name != "::$DATA":
                streams.append(name)
            if not find_next(handle, ctypes.byref(data)):
                err = ctypes.get_last_error()
                if err == 38:
                    break
                raise OSError(err, f"FindNextStreamW failed for {path}")
    finally:
        find_close(handle)
    return streams


def parse_materials() -> dict:
    json_files = []
    csv_files = []
    utf8_files = []
    for p in all_entries():
        if not p.is_file() or p.name in {"MANIFEST.tsv", "WRITE_STOPPED", "preseal_checks.json"}:
            continue
        suffix = p.suffix.casefold()
        if suffix == ".json":
            json.loads(p.read_text(encoding="utf-8"))
            json_files.append(p.relative_to(ROOT).as_posix())
        elif suffix == ".csv":
            with p.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            if not rows or not rows[0]:
                raise RuntimeError(f"empty CSV: {p}")
            width = len(rows[0])
            if any(len(row) != width for row in rows):
                raise RuntimeError(f"ragged CSV: {p}")
            csv_files.append(p.relative_to(ROOT).as_posix())
        elif suffix in {".md", ".py", ".tsv", ".txt"}:
            p.read_text(encoding="utf-8")
            utf8_files.append(p.relative_to(ROOT).as_posix())
    return {"json_files": json_files, "csv_files": csv_files, "utf8_files": utf8_files}


def main() -> None:
    marker = ROOT / "WRITE_STOPPED"
    if marker.exists():
        raise RuntimeError("WRITE_STOPPED already exists")

    # Material identities are fixed before the manifest is built.
    material = {
        "handoff_id": HANDOFF_ID,
        "uid": UID,
        "verdict": "PASS",
        "pdf": {"bytes": PDF.stat().st_size, "sha256": digest(PDF)},
        "source": {"bytes": SOURCE.stat().st_size, "sha256": digest(SOURCE)},
        "report_sha256": digest(ROOT / "report.md"),
        "handoff_sha256": digest(ROOT / "handoff.md"),
        "object_denominator_rows": sum(1 for _ in (ROOT / "machine" / "object_denominator.csv").open("r", encoding="utf-8-sig")) - 1,
        "unordered_pair_rows": sum(1 for _ in (ROOT / "machine" / "unordered_pair_metrics.csv").open("r", encoding="utf-8-sig")) - 1,
    }
    (ROOT / "material_identity.json").write_text(json.dumps(material, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    parsed = parse_materials()
    entries = all_entries()
    reparse = []
    cache = []
    ads = []
    casefold_paths: dict[str, str] = {}
    duplicate_casefold = []
    for p in entries:
        rel = p.relative_to(ROOT).as_posix()
        key = rel.casefold()
        if key in casefold_paths:
            duplicate_casefold.append([casefold_paths[key], rel])
        casefold_paths[key] = rel
        st = p.lstat()
        if getattr(st, "st_file_attributes", 0) & 0x400:
            reparse.append(rel)
        lname = p.name.casefold()
        if lname == "__pycache__" or lname.endswith(".pyc") or lname.endswith(".pyo") or lname in {".cache", ".pytest_cache"}:
            cache.append(rel)
        if p.is_file():
            for stream in named_ads(p):
                ads.append({"path": rel, "stream": stream})

    checks = {
        "handoff_id": HANDOFF_ID,
        "uid": UID,
        "json_parse_error_count": 0,
        "csv_parse_error_count": 0,
        "utf8_parse_error_count": 0,
        "parsed_json_files": parsed["json_files"],
        "parsed_csv_files": parsed["csv_files"],
        "parsed_utf8_files": parsed["utf8_files"],
        "named_ads_count": len(ads),
        "named_ads": ads,
        "cache_or_pyc_count": len(cache),
        "cache_or_pyc_paths": cache,
        "reparse_point_count": len(reparse),
        "reparse_point_paths": reparse,
        "casefold_duplicate_count": len(duplicate_casefold),
        "casefold_duplicates": duplicate_casefold,
    }
    if ads or cache or reparse or duplicate_casefold:
        raise RuntimeError(f"preseal hygiene failure: {checks}")
    preseal = ROOT / "preseal_checks.json"
    preseal.write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    json.loads(preseal.read_text(encoding="utf-8"))

    # The manifest intentionally excludes only itself and the final marker.
    manifest_rows = []
    for p in all_entries():
        if not p.is_file() or p.name in {"MANIFEST.tsv", "WRITE_STOPPED"}:
            continue
        manifest_rows.append((p.relative_to(ROOT).as_posix(), p.stat().st_size, digest(p)))
    manifest = ROOT / "MANIFEST.tsv"
    with manifest.open("w", encoding="utf-8", newline="\n") as f:
        f.write("RELATIVE_PATH\tBYTES\tSHA256\n")
        for rel, size, sha in manifest_rows:
            f.write(f"{rel}\t{size}\t{sha}\n")

    # Immediate manifest parse and identity check before sealing.
    lines = manifest.read_text(encoding="utf-8").splitlines()
    if lines[0] != "RELATIVE_PATH\tBYTES\tSHA256" or len(lines) - 1 != len(manifest_rows):
        raise RuntimeError("manifest parse/count failure")
    for line, expected in zip(lines[1:], manifest_rows, strict=True):
        rel, size, sha = line.split("\t")
        p = ROOT / Path(rel)
        if (rel, int(size), sha) != expected or p.stat().st_size != int(size) or digest(p) != sha:
            raise RuntimeError(f"manifest identity failure: {rel}")
    print(f"MANIFEST_ROWS={len(manifest_rows)}")
    print(f"MANIFEST_SHA256={digest(manifest)}")
    print("PRESEAL_PARSE_HYGIENE=PASS")


if __name__ == "__main__":
    main()
