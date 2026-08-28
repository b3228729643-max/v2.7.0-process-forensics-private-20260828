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


ACCEPT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ACCEPT_ROOT.parent / "02_native_evidence_r1"
OUTPUT = ACCEPT_ROOT / "ROOT_ACCEPTANCE.json"
MANIFEST_REL = "09_manifest/evidence_file_manifest.csv"
MARKER_REL = "identity/WRITE_STOPPED.json"
EXPECTED_PDF_SHA = "68188DAAAF9B3C4233D5A032C3D8BE20A73B51D5E6058D0E1C12FDE6471093E7"
EXPECTED_SOURCE_SHA = "6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def snapshot(root: Path) -> tuple[list[dict[str, object]], str]:
    records: list[dict[str, object]] = []
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        st = path.stat()
        records.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": st.st_size,
            "sha256": sha256(path),
            "mtime_ns_100": st.st_mtime_ns // 100,
        })
    canonical = "".join(f"{r['path']}|{r['bytes']}|{r['sha256']}|{r['mtime_ns_100']}\n" for r in records).encode("utf-8")
    return records, hashlib.sha256(canonical).hexdigest().upper()


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
    invalid = ctypes.c_void_p(-1).value
    streams: list[str] = []
    errors: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        data = WIN32_FIND_STREAM_DATA()
        handle = find_first(str(path), 0, ctypes.byref(data), 0)
        if handle == invalid:
            error = ctypes.get_last_error()
            if error not in (2, 38):
                errors.append(f"{path.relative_to(root)}:first:{error}")
            continue
        try:
            while True:
                if data.cStreamName != "::$DATA":
                    streams.append(f"{path.relative_to(root)}{data.cStreamName}")
                if not find_next(handle, ctypes.byref(data)):
                    error = ctypes.get_last_error()
                    if error != 38:
                        errors.append(f"{path.relative_to(root)}:next:{error}")
                    break
        finally:
            find_close(handle)
    return streams, errors


checks: dict[str, object] = {}
failures: list[str] = []


def gate(name: str, condition: bool, detail: object) -> None:
    checks[name] = {"pass": bool(condition), "detail": detail}
    if not condition:
        failures.append(name)


pre_records, pre_snapshot_sha = snapshot(EVIDENCE_ROOT)
pre_map = {r["path"]: r for r in pre_records}
manifest_path = EVIDENCE_ROOT / MANIFEST_REL
marker_path = EVIDENCE_ROOT / MARKER_REL
manifest_rows = csv_rows(manifest_path)
marker = json.loads(marker_path.read_text(encoding="utf-8"))

ordinary_paths = set(pre_map)
listed_paths = [r["path"] for r in manifest_rows]
listed_set = set(listed_paths)
unique_unlisted = sorted(ordinary_paths - listed_set)
missing = sorted(listed_set - ordinary_paths)
duplicate_paths = sorted({p for p in listed_paths if listed_paths.count(p) > 1})
gate("manifest_model", len(pre_records) == 896 and len(manifest_rows) == 894 and unique_unlisted == sorted([MANIFEST_REL, MARKER_REL]) and not missing and not duplicate_paths,
     {"ordinary": len(pre_records), "rows": len(manifest_rows), "unique_unlisted": unique_unlisted, "missing": missing, "duplicate_paths": duplicate_paths})

manifest_mismatches: list[dict[str, object]] = []
for row in manifest_rows:
    current = pre_map.get(row["path"])
    if current is None:
        continue
    expected = {"bytes": int(row["bytes"]), "sha256": row["sha256"], "mtime_ns_100": int(row["mtime_ns_100"])}
    actual = {"bytes": current["bytes"], "sha256": current["sha256"], "mtime_ns_100": current["mtime_ns_100"]}
    if expected != actual:
        manifest_mismatches.append({"path": row["path"], "expected": expected, "actual": actual})
gate("manifest_file_identities", not manifest_mismatches, {"checked": len(manifest_rows), "mismatches": manifest_mismatches})

canonical_manifest_records = "".join(
    f"{r['path']}|{r['category']}|{r['bytes']}|{r['sha256']}|{r['mtime_ns_100']}\n"
    for r in manifest_rows
).encode("utf-8")
recordset_sha = hashlib.sha256(canonical_manifest_records).hexdigest().upper()
gate("recordset_and_manifest_identity",
     recordset_sha == marker["canonical_payload_control_recordset_sha256"] and sha256(manifest_path) == marker["manifest"]["sha256"] and manifest_path.stat().st_size == marker["manifest"]["bytes"],
     {"recordset_sha256": recordset_sha, "marker_recordset_sha256": marker["canonical_payload_control_recordset_sha256"], "manifest_sha256": sha256(manifest_path), "marker_manifest_sha256": marker["manifest"]["sha256"], "manifest_bytes": manifest_path.stat().st_size})

marker_mtime = marker_path.stat().st_mtime_ns
latest_other = max(p.stat().st_mtime_ns for p in EVIDENCE_ROOT.rglob("*") if p.is_file() and p != marker_path)
gate("write_stopped_strict_last", marker.get("write_stopped") is True and marker_mtime > latest_other and marker.get("post_seal_writes_expected") == 0,
     {"marker_mtime_ns": marker_mtime, "latest_other_mtime_ns": latest_other, "delta_ns": marker_mtime - latest_other, "write_stopped": marker.get("write_stopped")})

readonly_failures: list[str] = []
for path in EVIDENCE_ROOT.rglob("*"):
    if path.is_file() and not (path.stat().st_file_attributes & 0x1):
        readonly_failures.append(path.relative_to(EVIDENCE_ROOT).as_posix())
gate("all_files_readonly", not readonly_failures, {"checked": len(pre_records), "failures": readonly_failures})

csv_failures: list[str] = []
json_failures: list[str] = []
png_failures: list[str] = []
csv_count = json_count = png_count = 0
for path in EVIDENCE_ROOT.rglob("*.csv"):
    csv_count += 1
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            list(csv.reader(f))
    except Exception as exc:
        csv_failures.append(f"{path.relative_to(EVIDENCE_ROOT)}:{exc}")
for path in EVIDENCE_ROOT.rglob("*.json"):
    json_count += 1
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        json_failures.append(f"{path.relative_to(EVIDENCE_ROOT)}:{exc}")
for path in EVIDENCE_ROOT.rglob("*.png"):
    png_count += 1
    try:
        with path.open("rb") as f:
            header = f.read(24)
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            png_failures.append(path.relative_to(EVIDENCE_ROOT).as_posix())
        elif min(struct.unpack(">II", header[16:24])) <= 0:
            png_failures.append(path.relative_to(EVIDENCE_ROOT).as_posix())
    except Exception as exc:
        png_failures.append(f"{path.relative_to(EVIDENCE_ROOT)}:{exc}")
gate("parse_and_open", not csv_failures and not json_failures and not png_failures and png_count == 864,
     {"csv_checked": csv_count, "csv_failures": csv_failures, "json_checked": json_count, "json_failures": json_failures, "png_checked": png_count, "png_failures": png_failures})

ads_entries, ads_errors = enumerate_alternate_streams(EVIDENCE_ROOT)
cache_files = [p.relative_to(EVIDENCE_ROOT).as_posix() for p in EVIDENCE_ROOT.rglob("*") if p.is_file() and (p.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in p.parts)]
gate("hygiene", not ads_entries and not ads_errors and not cache_files, {"ads": ads_entries, "ads_probe_errors": ads_errors, "cache_files": cache_files})

root_validation = json.loads((EVIDENCE_ROOT / "qa" / "ROOT_VALIDATION.json").read_text(encoding="utf-8"))
gate("embedded_root_validation", root_validation.get("outcome") == "PASS" and root_validation.get("failures") == [],
     {"outcome": root_validation.get("outcome"), "failures": root_validation.get("failures"), "sha256": sha256(EVIDENCE_ROOT / "qa" / "ROOT_VALIDATION.json")})

machine_specs = {
    "objects": ("objects/object_manifest.csv", 30),
    "glyphs": ("glyphs/glyph_machine_measurements.csv", 154),
    "pairs": ("pairs/all_pairs_machine.csv", 435),
    "critical": ("pairs/critical_machine_index.csv", 16),
    "peer": ("ledgers/peer_machine.csv", 28),
    "role": ("ledgers/role_machine.csv", 3),
    "clip": ("ledgers/clip_machine.csv", 30),
    "view": ("ledgers/view_machine.csv", 4),
}
machine_counts = {k: len(csv_rows(EVIDENCE_ROOT / rel)) for k, (rel, _) in machine_specs.items()}
gate("machine_denominators", all(machine_counts[k] == expected for k, (_, expected) in machine_specs.items()), machine_counts)
objects = csv_rows(EVIDENCE_ROOT / "objects" / "object_manifest.csv")
pairs = csv_rows(EVIDENCE_ROOT / "pairs" / "all_pairs_machine.csv")
object_ids = [r["object_id"] for r in objects]
expected_pair_set = set(itertools.combinations(object_ids, 2))
actual_pair_set = {(r["object_a"], r["object_b"]) for r in pairs}
gate("pair_closure_and_machine_pass", expected_pair_set == actual_pair_set and all(r["machine_decision"] == "PASS" for r in pairs),
     {"expected": len(expected_pair_set), "actual": len(actual_pair_set), "machine_failures": [r["pair_id"] for r in pairs if r["machine_decision"] != "PASS"]})

manual_specs = {
    "objects": ("ledgers/manual_object_review.csv", 30, "object_id"),
    "glyphs": ("ledgers/manual_glyph_review.csv", 154, "glyph_id"),
    "pairs": ("ledgers/manual_pair_review.csv", 435, "pair_id"),
    "critical": ("ledgers/manual_critical_pair_review.csv", 16, "pair_id"),
    "peer": ("ledgers/manual_peer_review.csv", 28, "peer_id"),
    "role": ("ledgers/manual_role_review.csv", 3, "role_id"),
    "clip": ("ledgers/manual_clip_review.csv", 30, "object_id"),
    "view": ("ledgers/manual_view_review.csv", 4, "view_id"),
    "hard": ("ledgers/manual_hard_gate_review.csv", 12, "gate_id"),
}
manual_detail: dict[str, object] = {}
manual_ok = True
manual_data: dict[str, list[dict[str, str]]] = {}
for name, (rel, expected, key) in manual_specs.items():
    data = csv_rows(EVIDENCE_ROOT / rel)
    manual_data[name] = data
    notes = [r.get("manual_note", "").strip() for r in data]
    decisions = all((r.get("manual_decision") == "PASS") or (r.get("manual_visual_decision") == "PASS" and r.get("hard_gate_decision") == "PASS") for r in data)
    row_ok = len(data) == expected and len({r[key] for r in data}) == expected and len(notes) == len(set(notes)) and all(notes) and decisions
    manual_ok = manual_ok and row_ok
    manual_detail[name] = {"rows": len(data), "unique_ids": len({r[key] for r in data}), "notes_unique_nonblank": len(notes) == len(set(notes)) and all(notes), "decisions_pass": decisions}
gate("manual_ledgers", manual_ok, manual_detail)

manual_pair_map = [(r["pair_id"], r["object_a"], r["object_b"]) for r in manual_data["pairs"]]
machine_pair_map = [(r["pair_id"], r["object_a"], r["object_b"]) for r in pairs]
gate("manual_pair_endpoint_alignment", manual_pair_map == machine_pair_map, {"aligned": manual_pair_map == machine_pair_map, "rows": len(manual_pair_map)})

glyphs = csv_rows(EVIDENCE_ROOT / "glyphs" / "glyph_machine_measurements.csv")
g032_machine = next(r for r in glyphs if r["glyph_id"] == "G032")
g032_manual = next(r for r in manual_data["glyphs"] if r["glyph_id"] == "G032")
gate("g032_strict_closure", g032_machine["char"] == "范" and g032_machine["ink_width_px"] == "37" and g032_machine["ink_height_px"] == "34" and g032_machine["machine_threshold_pass"] == "True" and g032_manual["manual_visual_decision"] == "PASS" and g032_manual["hard_gate_decision"] == "PASS",
     {"machine": g032_machine, "manual": g032_manual})

identity = json.loads((EVIDENCE_ROOT / "identity" / "candidate_and_source_identity.json").read_text(encoding="utf-8"))
pdf_path = Path(identity["candidate_pdf_path"])
source_path = Path(identity["source_path"])
source_text = source_path.read_text(encoding="utf-8")
gate("external_identities", sha256(pdf_path) == EXPECTED_PDF_SHA and pdf_path.stat().st_size == 41653 and sha256(source_path) == EXPECTED_SOURCE_SHA and source_path.stat().st_size == 2869,
     {"pdf_bytes": pdf_path.stat().st_size, "pdf_sha256": sha256(pdf_path), "source_bytes": source_path.stat().st_size, "source_sha256": sha256(source_path)})
gate("source_r3_phrase", source_text.count("未规范化目标") == 1 and "未归一化目标" not in source_text and "未经归一化目标" not in source_text and "一" not in source_text,
     {"fresh_phrase_count": source_text.count("未规范化目标"), "old_phrase_count": source_text.count("未归一化目标"), "suggested_phrase_count": source_text.count("未经归一化目标"), "u4e00_count": source_text.count("一")})

worktree = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual")
git_head = subprocess.run(["git", "-C", str(worktree), "rev-parse", "HEAD"], capture_output=True, text=True, encoding="utf-8", errors="replace")
git_branch = subprocess.run(["git", "-C", str(worktree), "branch", "--show-current"], capture_output=True, text=True, encoding="utf-8", errors="replace")
git_names = subprocess.run(["git", "-C", str(worktree), "-c", "core.quotepath=false", "diff", "--name-only"], capture_output=True, text=True, encoding="utf-8", errors="replace")
changed_names = [line.strip() for line in git_names.stdout.splitlines() if line.strip()]
expected_source_rel = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_mh_accept_reject.tex"
gate("worktree_scope", git_head.returncode == 0 and git_head.stdout.strip() == "eea4060c5229168e2b973bbaea81cf391e7a9dfd" and git_branch.stdout.strip() == "v2.7.0/dialogue-c-visual" and changed_names == [expected_source_rel],
     {"head": git_head.stdout.strip(), "branch": git_branch.stdout.strip(), "changed_names": changed_names})

tex_probe = subprocess.run(["D:\\PowerShell7\\pwsh.exe", "-NoProfile", "-Command", "Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue | ForEach-Object { $_.Name + ':' + $_.Id }; exit 0"], capture_output=True, text=True, encoding="utf-8", errors="replace")
tex_processes = [line.strip() for line in tex_probe.stdout.splitlines() if line.strip()]
gate("terminal_tex_processes", tex_probe.returncode == 0 and not tex_processes, {"exit_code": tex_probe.returncode, "processes": tex_processes})

post_records, post_snapshot_sha = snapshot(EVIDENCE_ROOT)
gate("evidence_zero_write_during_audit", pre_records == post_records and pre_snapshot_sha == post_snapshot_sha,
     {"pre_recordset_sha256": pre_snapshot_sha, "post_recordset_sha256": post_snapshot_sha, "records": len(pre_records)})

report = {
    "audit_id": "C-FIG-P602-01-SA2-R3-V1-ROOT-ACCEPTANCE-R1",
    "evidence_root": str(EVIDENCE_ROOT),
    "audit_root": str(ACCEPT_ROOT),
    "evidence_root_read_only": True,
    "outcome": "PASS" if not failures else "FAIL",
    "failures": failures,
    "checks": checks,
    "accepted_status": "C_LOCAL_PASS_CANDIDATE_PENDING_MAIN_ACCEPTANCE" if not failures else "REJECT",
    "central_inventory_written": False,
    "commit_created": False,
    "global_pass_claimed": False,
}
with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=ACCEPT_ROOT, prefix="ROOT_ACCEPTANCE.", suffix=".tmp") as tmp:
    json.dump(report, tmp, ensure_ascii=False, indent=2)
    tmp.write("\n")
    tmp.flush()
    os.fsync(tmp.fileno())
    temp_path = Path(tmp.name)
os.replace(temp_path, OUTPUT)
print(json.dumps({"outcome": report["outcome"], "failure_count": len(failures), "failures": failures, "output": str(OUTPUT)}, ensure_ascii=False))
