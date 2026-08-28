from __future__ import annotations

import csv
import ctypes
import hashlib
import itertools
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "qa" / "ROOT_VALIDATION.json"
EXPECTED_PDF_SHA = "68188DAAAF9B3C4233D5A032C3D8BE20A73B51D5E6058D0E1C12FDE6471093E7"
EXPECTED_SOURCE_SHA = "6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D"
EXPECTED_START_SHA = "4079A8BA4C6054A6693C6052578BED3056EA9AAD5DA3626477001C7245EDAF57"
EXPECTED_RESULT_SHA = "4746B6DA9D3F1F6DAA03DFBC31A8EBA6BFB6FC1A9A6048CBB8F878BEAB765D17"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def unique_nonblank_notes(data: list[dict[str, str]]) -> bool:
    notes = [r.get("manual_note", "").strip() for r in data]
    return bool(data) and all(notes) and len(notes) == len(set(notes))


def enumerate_alternate_streams(root: Path) -> tuple[list[str], list[str]]:
    class WIN32_FIND_STREAM_DATA(ctypes.Structure):
        _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", ctypes.c_wchar * 296)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    find_first = kernel32.FindFirstStreamW
    find_first.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(WIN32_FIND_STREAM_DATA), ctypes.c_uint32]
    find_first.restype = ctypes.c_void_p
    find_next = kernel32.FindNextStreamW
    find_next.argtypes = [ctypes.c_void_p, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
    find_next.restype = ctypes.c_int
    find_close = kernel32.FindClose
    find_close.argtypes = [ctypes.c_void_p]
    find_close.restype = ctypes.c_int
    invalid_handle = ctypes.c_void_p(-1).value
    alternate: list[str] = []
    errors: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        data = WIN32_FIND_STREAM_DATA()
        handle = find_first(str(path), 0, ctypes.byref(data), 0)
        if handle == invalid_handle:
            error = ctypes.get_last_error()
            if error not in (2, 38):
                errors.append(f"{path.relative_to(root)}:FindFirstStreamW:{error}")
            continue
        try:
            while True:
                if data.cStreamName != "::$DATA":
                    alternate.append(f"{path.relative_to(root)}{data.cStreamName}")
                if not find_next(handle, ctypes.byref(data)):
                    error = ctypes.get_last_error()
                    if error != 38:
                        errors.append(f"{path.relative_to(root)}:FindNextStreamW:{error}")
                    break
        finally:
            find_close(handle)
    return alternate, errors


checks: dict[str, object] = {}
failures: list[str] = []


def gate(name: str, condition: bool, detail: object) -> None:
    checks[name] = {"pass": bool(condition), "detail": detail}
    if not condition:
        failures.append(name)


identity = json.loads((ROOT / "identity" / "candidate_and_source_identity.json").read_text(encoding="utf-8"))
pdf = Path(identity["candidate_pdf_path"])
source = Path(identity["source_path"])
start = Path(identity["build_start_path"])
result = Path(identity["build_result_path"])

gate("candidate_pdf_identity", pdf.is_file() and pdf.stat().st_size == 41653 and sha256(pdf) == EXPECTED_PDF_SHA,
     {"path": str(pdf), "bytes": pdf.stat().st_size if pdf.exists() else None, "sha256": sha256(pdf) if pdf.exists() else None})
gate("source_identity", source.is_file() and source.stat().st_size == 2869 and sha256(source) == EXPECTED_SOURCE_SHA,
     {"path": str(source), "bytes": source.stat().st_size if source.exists() else None, "sha256": sha256(source) if source.exists() else None})
gate("build_control_identity", start.is_file() and result.is_file() and sha256(start) == EXPECTED_START_SHA and sha256(result) == EXPECTED_RESULT_SHA,
     {"start_sha256": sha256(start) if start.exists() else None, "result_sha256": sha256(result) if result.exists() else None})

source_text = source.read_text(encoding="utf-8")
gate("r3_phrase_identity", source_text.count("未规范化目标") == 1 and "未归一化目标" not in source_text and "未经归一化目标" not in source_text and "一" not in source_text,
     {"fresh_phrase_count": source_text.count("未规范化目标"), "old_phrase_count": source_text.count("未归一化目标"), "suggested_phrase_count": source_text.count("未经归一化目标"), "u4e00_count": source_text.count("一")})

objects = rows("objects/object_manifest.csv")
glyphs = rows("glyphs/glyph_machine_measurements.csv")
pairs = rows("pairs/all_pairs_machine.csv")
critical = rows("pairs/critical_machine_index.csv")
peer = rows("ledgers/peer_machine.csv")
roles = rows("ledgers/role_machine.csv")
clips = rows("ledgers/clip_machine.csv")
views = rows("ledgers/view_machine.csv")

object_ids = [r["object_id"] for r in objects]
glyph_ids = [r["glyph_id"] for r in glyphs]
pair_ids = [r["pair_id"] for r in pairs]
expected_pairs = {(a, b) for a, b in itertools.combinations(object_ids, 2)}
actual_pairs = {(r["object_a"], r["object_b"]) for r in pairs}
gate("machine_denominators", (len(objects), len(glyphs), len(pairs), len(critical), len(peer), len(roles), len(clips), len(views)) == (30, 154, 435, 16, 28, 3, 30, 4),
     {"objects": len(objects), "glyphs": len(glyphs), "pairs": len(pairs), "critical": len(critical), "peer": len(peer), "roles": len(roles), "clips": len(clips), "views": len(views)})
gate("machine_id_uniqueness", len(object_ids) == len(set(object_ids)) and len(glyph_ids) == len(set(glyph_ids)) and len(pair_ids) == len(set(pair_ids)),
     {"object_unique": len(set(object_ids)), "glyph_unique": len(set(glyph_ids)), "pair_unique": len(set(pair_ids))})
gate("unordered_pair_closure", expected_pairs == actual_pairs and len(actual_pairs) == 435,
     {"expected": len(expected_pairs), "actual": len(actual_pairs), "missing": sorted(expected_pairs - actual_pairs), "extra": sorted(actual_pairs - expected_pairs)})
gate("machine_decisions", all(r["machine_decision"] == "PASS" for r in pairs) and all(r["machine_threshold_pass"] == "True" and r["empty_mask"] == "False" for r in glyphs) and all(r["machine_clip_pass"] == "True" for r in clips) and all(r["machine_peer_pass"] == "True" for r in peer) and all(r["machine_role_pass"] == "True" for r in roles),
     {"pair_fail": [r["pair_id"] for r in pairs if r["machine_decision"] != "PASS"], "glyph_fail": [r["glyph_id"] for r in glyphs if r["machine_threshold_pass"] != "True" or r["empty_mask"] != "False"], "clip_fail": [r["object_id"] for r in clips if r["machine_clip_pass"] != "True"], "peer_fail": [r["element_id"] + ":" + r["peer_class"] for r in peer if r["machine_peer_pass"] != "True"], "role_fail": [r["role_id"] for r in roles if r["machine_role_pass"] != "True"]})
g032 = next(r for r in glyphs if r["glyph_id"] == "G032")
gate("g032_strict_profile", g032["char"] == "范" and int(g032["ink_width_px"]) == 37 and int(g032["ink_height_px"]) == 34 and g032["machine_threshold_pass"] == "True",
     {k: g032[k] for k in ("glyph_id", "char", "unicode", "ink_width_px", "ink_height_px", "script_class", "threshold_px", "machine_threshold_pass")})

manual_specs = {
    "object": ("ledgers/manual_object_review.csv", 30, "object_id"),
    "glyph": ("ledgers/manual_glyph_review.csv", 154, "glyph_id"),
    "pair": ("ledgers/manual_pair_review.csv", 435, "pair_id"),
    "critical": ("ledgers/manual_critical_pair_review.csv", 16, "pair_id"),
    "peer": ("ledgers/manual_peer_review.csv", 28, "peer_id"),
    "role": ("ledgers/manual_role_review.csv", 3, "role_id"),
    "clip": ("ledgers/manual_clip_review.csv", 30, "object_id"),
    "view": ("ledgers/manual_view_review.csv", 4, "view_id"),
    "hard": ("ledgers/manual_hard_gate_review.csv", 12, "gate_id"),
}
manual: dict[str, list[dict[str, str]]] = {}
for name, (rel, expected, key) in manual_specs.items():
    data = rows(rel)
    manual[name] = data
    decisions_ok = all((r.get("manual_decision") == "PASS") or (r.get("manual_visual_decision") == "PASS" and r.get("hard_gate_decision") == "PASS") for r in data)
    gate(f"manual_{name}_ledger", len(data) == expected and len({r[key] for r in data}) == expected and decisions_ok and unique_nonblank_notes(data),
         {"rows": len(data), "unique_ids": len({r[key] for r in data}), "decisions_ok": decisions_ok, "notes_unique_nonblank": unique_nonblank_notes(data)})

manual_object_ids = [r["object_id"] for r in manual["object"]]
manual_glyph_ids = [r["glyph_id"] for r in manual["glyph"]]
manual_pair_map = [(r["pair_id"], r["object_a"], r["object_b"]) for r in manual["pair"]]
machine_pair_map = [(r["pair_id"], r["object_a"], r["object_b"]) for r in pairs]
gate("manual_machine_id_alignment", manual_object_ids == object_ids and manual_glyph_ids == glyph_ids and manual_pair_map == machine_pair_map,
     {"objects_aligned": manual_object_ids == object_ids, "glyphs_aligned": manual_glyph_ids == glyph_ids, "pairs_aligned": manual_pair_map == machine_pair_map})
critical_machine_map = [(r["pair_id"], r["object_a"], r["object_b"]) for r in critical]
critical_manual_map = [(r["pair_id"], r["object_a"], r["object_b"]) for r in manual["critical"]]
gate("critical_alignment", critical_manual_map == critical_machine_map,
     {"machine": critical_machine_map, "manual": critical_manual_map})
gate("clip_alignment", [r["object_id"] for r in manual["clip"]] == [r["object_id"] for r in clips],
     {"aligned": [r["object_id"] for r in manual["clip"]] == [r["object_id"] for r in clips]})
gate("role_view_alignment", [r["role_id"] for r in manual["role"]] == [r["role_id"] for r in roles] and [r["view_id"] for r in manual["view"]] == [r["view_id"] for r in views],
     {"roles_aligned": [r["role_id"] for r in manual["role"]] == [r["role_id"] for r in roles], "views_aligned": [r["view_id"] for r in manual["view"]] == [r["view_id"] for r in views]})

png_failures: list[str] = []
png_count = 0
for path in ROOT.rglob("*.png"):
    png_count += 1
    try:
        with path.open("rb") as f:
            header = f.read(24)
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            png_failures.append(str(path.relative_to(ROOT)))
            continue
        width, height = struct.unpack(">II", header[16:24])
        if width <= 0 or height <= 0:
            png_failures.append(str(path.relative_to(ROOT)))
    except Exception:
        png_failures.append(str(path.relative_to(ROOT)))
gate("png_parse", png_count == 864 and not png_failures, {"checked": png_count, "expected_complete_set": 864, "failures": png_failures})

csv_failures: list[str] = []
csv_count = 0
for path in ROOT.rglob("*.csv"):
    csv_count += 1
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            list(csv.reader(f))
    except Exception as exc:
        csv_failures.append(f"{path.relative_to(ROOT)}:{exc}")
json_failures: list[str] = []
json_count = 0
for path in ROOT.rglob("*.json"):
    if path == OUTPUT:
        continue
    json_count += 1
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        json_failures.append(f"{path.relative_to(ROOT)}:{exc}")
gate("structured_parse", not csv_failures and not json_failures, {"csv_checked": csv_count, "csv_failures": csv_failures, "json_checked": json_count, "json_failures": json_failures})

hygiene_bad = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and (p.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in p.parts)]
gate("cache_hygiene", not hygiene_bad, {"bad": hygiene_bad})

ads_entries, ads_errors = enumerate_alternate_streams(ROOT)
gate("ads_hygiene", not ads_entries and not ads_errors, {"entries": ads_entries, "probe_errors": ads_errors})

tex_probe = subprocess.run(
    ["D:\\PowerShell7\\pwsh.exe", "-NoProfile", "-Command", "Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue | ForEach-Object { $_.Name + ':' + $_.Id }; exit 0"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
tex_processes = [line.strip() for line in tex_probe.stdout.splitlines() if line.strip()]
gate("terminal_tex_processes", tex_probe.returncode == 0 and not tex_processes, {"probe_exit": tex_probe.returncode, "processes": tex_processes, "stderr": tex_probe.stderr.strip()})

report = {
    "uid": "FIG-P602-01",
    "round": "SA2_R3_V1_NATIVE_R1",
    "validator_is_read_only_over_manual_ledgers": True,
    "outcome": "PASS" if not failures else "FAIL",
    "failures": failures,
    "checks": checks,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=OUTPUT.parent, prefix="ROOT_VALIDATION.", suffix=".tmp") as tmp:
    json.dump(report, tmp, ensure_ascii=False, indent=2)
    tmp.write("\n")
    tmp.flush()
    os.fsync(tmp.fileno())
    tmp_path = Path(tmp.name)
os.replace(tmp_path, OUTPUT)
print(json.dumps({"outcome": report["outcome"], "failure_count": len(failures), "failures": failures, "output": str(OUTPUT)}, ensure_ascii=False))
