from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import itertools
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
HANDOFF_ID = "A-R101-P608-SA1-FRESH-20260825"
PDF_SHA256 = "0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1"
CONTROL_NAMES = {
    "FINAL_PAYLOAD_MANIFEST.json",
    "manifest_parse_check.json",
    "TERMINAL_STOP.json",
    "WRITE_SEAL.json",
}
TEMPLATES = [
    "manual_object_ledger_TEMPLATE.csv",
    "manual_critical_pair_ledger_TEMPLATE.csv",
    "manual_preliminary_ledger_TEMPLATE.csv",
    "manual_role_ledger_TEMPLATE.csv",
    "manual_view_ledger_TEMPLATE.csv",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_json(name: str):
    with (ROOT / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def cleanup_unsealed_scaffolding() -> list[str]:
    assert_true(not (ROOT / "WRITE_SEAL.json").exists(), "refuse cleanup after seal")
    removed: list[str] = []
    for name in TEMPLATES:
        path = (ROOT / name).resolve()
        assert_true(path.parent == ROOT, f"unsafe cleanup target: {path}")
        if path.exists():
            path.unlink()
            removed.append(name)
    cache = (ROOT / "__pycache__").resolve()
    assert_true(cache.parent == ROOT, f"unsafe cache target: {cache}")
    if cache.exists():
        for item in cache.iterdir():
            item_resolved = item.resolve()
            assert_true(item_resolved.parent == cache and item.is_file(), f"unexpected cache member: {item}")
            item.unlink()
        cache.rmdir()
        removed.append("__pycache__/")
    return removed


def bbox_distance(a: list[int], b: list[int]) -> float:
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return (dx * dx + dy * dy) ** 0.5


def list_ads(path: Path) -> tuple[list[str], str | None]:
    if os.name != "nt":
        return [], "ADS scan requires Windows"

    class WIN32_FIND_STREAM_DATA(ctypes.Structure):
        _fields_ = [
            ("StreamSize", ctypes.c_longlong),
            ("cStreamName", ctypes.c_wchar * (260 + 36)),
        ]

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

    data = WIN32_FIND_STREAM_DATA()
    invalid = ctypes.c_void_p(-1).value
    handle = find_first(str(path), 0, ctypes.byref(data), 0)
    if handle == invalid:
        return [], f"FindFirstStreamW error {ctypes.get_last_error()}"
    streams: list[str] = []
    try:
        streams.append(data.cStreamName)
        while find_next(handle, ctypes.byref(data)):
            streams.append(data.cStreamName)
        err = ctypes.get_last_error()
        if err not in (0, 38):
            return streams, f"FindNextStreamW error {err}"
    finally:
        find_close(handle)
    return [s for s in streams if s != "::$DATA"], None


def scan_ads() -> dict:
    entries = []
    errors = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        streams, error = list_ads(path)
        rel = path.relative_to(ROOT).as_posix()
        if streams:
            entries.append({"path": rel, "alternate_streams": streams})
        if error:
            errors.append({"path": rel, "error": error})
    return {
        "scanner": "Win32 FindFirstStreamW/FindNextStreamW",
        "files_scanned": sum(1 for p in ROOT.rglob("*") if p.is_file()),
        "alternate_stream_count": sum(len(e["alternate_streams"]) for e in entries),
        "entries": entries,
        "errors": errors,
        "decision": "PASS" if not entries and not errors else "FAIL",
    }


def validate() -> dict:
    checks: list[dict] = []

    def check(check_id: str, condition: bool, note: str) -> None:
        assert_true(condition, f"{check_id}: {note}")
        checks.append({"check_id": check_id, "decision": "PASS", "note": note})

    identity = read_json("candidate_identity.json")
    check("IDENTITY", identity["identity_pass"] is True and identity["bytes"] == 4_947_496
          and identity["sha256"] == PDF_SHA256 and identity["pages"] == 814
          and identity["physical_page_1based"] == 659, "R101 identity/page mapping exact")
    summary = read_json("denominator_and_pair_summary.json")
    check("ROUTE", summary["handoff_id"] == HANDOFF_ID and summary["sa1_model_route"] == "gpt-5.6-sol/xhigh",
          "handoff and route exact")
    check("OUTCOME", summary["outcome"] == "FAIL_TO_SA2" and summary["hard_failure_count"] == 1,
          "one hard failure and FAIL_TO_SA2")

    conservation = read_json("denominator_conservation.json")
    check("GLYPH_CONSERVATION",
          conservation["page_rawdict_total_chars"] == 837
          and conservation["domain_total_chars"] == 120
          and conservation["domain_final_glyphs"] == 112
          and conservation["domain_whitespace_excluded"] == 8
          and conservation["outside_domain_total_chars"] == 717
          and conservation["page_rawdict_visible_nonspace_chars"] == 778
          and conservation["outside_domain_visible_nonspace"] == 666,
          "837=120+717; 120=112+8; 778=112+666")
    check("DRAWING_CONSERVATION",
          conservation["page_get_drawings_total"] == 89
          and conservation["target_explicit_drawings"] == 58
          and 89 == 6 + 58 + 2 + 2 + 21
          and conservation["visible_pattern_layers_not_emitted_by_get_drawings"] == 2,
          "89 get_drawings partitioned; two mutually exclusive visible patterns")

    objects = read_csv("object_inventory.csv")
    ids = [r["ELEMENT_ID"] for r in objects]
    classes = Counter(r["CLASS"] for r in objects)
    types = Counter(r["OBJECT_TYPE"] for r in objects)
    check("OBJECT_DENOMINATOR", len(objects) == len(set(ids)) == 172 and classes == Counter({"GLYPH": 112, "GRAPHIC": 60}),
          f"N=172 unique; classes={dict(classes)}")
    check("GRAPHIC_PARTITION", types["PATTERN"] == 2 and sum(1 for r in objects if r["CLASS"] == "GRAPHIC" and r["OBJECT_TYPE"] != "PATTERN") == 58,
          "58 explicit graphics + 2 pattern objects")
    caption = [r for r in objects if r["PANEL"] == "CAPTION"]
    check("CAPTION_CLOSURE", len(caption) == 44 and {r["ELEMENT_ID"] for r in caption} == {f"TXT-{i:03d}" for i in range(69, 113)},
          "44 caption glyphs TXT-069..TXT-112")

    safe = read_csv("safe_filename_map.csv")
    check("SAFE_FILENAME_MAP", len(safe) == 172 and len({r["ELEMENT_ID"] for r in safe}) == 172
          and len({r["SAFE_FILENAME"] for r in safe}) == 172 and {r["ELEMENT_ID"] for r in safe} == set(ids),
          "bijective 172-row ID/filename map")

    expected_pairs = {tuple(sorted(pair)) for pair in itertools.combinations(ids, 2)}
    pairs = read_csv("all_unordered_pairs.csv")
    observed_pairs = {tuple(sorted((r["A_ID"], r["B_ID"]))) for r in pairs}
    decisions = Counter(r["DECISION"] for r in pairs)
    check("PAIR_COVERAGE", len(pairs) == len(observed_pairs) == len(expected_pairs) == 14_706 and observed_pairs == expected_pairs,
          "all 14,706 unordered pairs exactly once")
    check("PAIR_DECISIONS", decisions == Counter({"CLEAR": 14176, "INTENDED_DESIGN_OVERLAP": 43, "INTENDED_DESIGN_RELATION": 487}),
          f"pair decisions={dict(decisions)}")
    check("PAIR_FINAL_INTERSECTIONS", all(int(r["FINAL_OVERLAP_PIXEL_COUNT"]) == 0 for r in pairs),
          "all ownership-resolved intersections are zero")

    critical = read_csv("critical_pairs_with_evidence.csv")
    check("CRITICAL_PAIR_COUNT", len(critical) == 102 and len({r["PAIR_ID"] for r in critical}) == 102,
          "102 unique critical relations")
    packet_fields = ["RAW_A", "RAW_B", "INTERSECTION", "ORIGINAL_1X", "OVERLAY_1X", "OVERLAY_8X"]
    missing_packets = []
    for row in critical:
        for field in packet_fields:
            if not (ROOT / row[field]).is_file():
                missing_packets.append(f"{row['PAIR_ID']}:{field}")
    check("CRITICAL_PACKETS", not missing_packets and len(list((ROOT / "critical_pairs").glob("*.png"))) == 102 * 6,
          "102 complete six-image packets")

    mask_dirs = ["pre_native", "pre_8x_nearest", "final_native", "final_8x_nearest"]
    mask_counts = {}
    mask_dim_errors = []
    for dirname in mask_dirs:
        paths = list((ROOT / "masks" / dirname).glob("*.png"))
        mask_counts[dirname] = len(paths)
        for row in objects:
            path = ROOT / "masks" / dirname / f"{row['SAFE_FILENAME']}.png"
            if not path.exists():
                mask_dim_errors.append(f"missing:{dirname}:{row['ELEMENT_ID']}")
                continue
            bbox_key = "RAW_MASK_BBOX_PX" if dirname.startswith("pre_") else "FINAL_MASK_BBOX_PX"
            bbox = ast.literal_eval(row[bbox_key])
            scale = 8 if "8x" in dirname else 1
            expected_size = ((bbox[2] - bbox[0]) * scale, (bbox[3] - bbox[1]) * scale)
            with Image.open(path) as im:
                if im.size != expected_size:
                    mask_dim_errors.append(f"{dirname}:{row['ELEMENT_ID']}:{im.size}!={expected_size}")
    check("MASK_SETS", all(mask_counts[d] == 172 for d in mask_dirs) and not mask_dim_errors,
          f"four 172-object mask sets; dimensions exact: {mask_counts}")
    check("MASK_NONEMPTY", all(int(r["RAW_PIXEL_COUNT"]) > 0 and int(r["FINAL_PIXEL_COUNT"]) > 0 for r in objects),
          "all raw and final masks nonempty")
    check("CLIP_AND_EDGE", summary["clip_pixel_count"] == 0 and summary["minimum_text_crop_edge_clearance_px"] == 32,
          "clip=0, minimum text edge clearance=32px")

    glyph_sheets = {r["SHEET"] for r in objects if r["CLASS"] == "GLYPH"}
    graphic_sheets = {r["SHEET"] for r in objects if r["CLASS"] == "GRAPHIC"}
    check("CONTACT_COVERAGE", len(glyph_sheets) == 10 and len(graphic_sheets) == 3
          and all((ROOT / "contact_sheets" / "glyph" / s).is_file() for s in glyph_sheets)
          and all((ROOT / "contact_sheets" / "graphic" / s).is_file() for s in graphic_sheets),
          "10 glyph sheets + 3 graphic sheets cover inventory")

    ledger_specs = {
        "manual_object_ledger.csv": 172,
        "manual_critical_pair_ledger.csv": 102,
        "manual_preliminary_ledger.csv": 64,
        "manual_low_profile_peer_ledger.csv": 13,
        "manual_role_ledger.csv": 35,
        "manual_view_ledger.csv": 4,
        "manual_hard_failure_ledger.csv": 1,
    }
    ledger_counts = {}
    for name, expected in ledger_specs.items():
        rows = read_csv(name)
        ledger_counts[name] = len(rows)
        check_id = "LEDGER_" + name.removesuffix(".csv").upper()
        check(check_id, len(rows) == expected and len({r["DECISION_ID"] for r in rows}) == expected
              and all(r["NOTE"].strip() and r["DECISION"].strip() for r in rows),
              f"{expected} unique, nonblank decisions")
    check("OBJECT_LEDGER_CLOSURE", {r["ELEMENT_ID"] for r in read_csv("manual_object_ledger.csv")} == set(ids),
          "manual object ledger covers denominator")
    check("PAIR_LEDGER_CLOSURE", {r["PAIR_ID"] for r in read_csv("manual_critical_pair_ledger.csv")} == {r["PAIR_ID"] for r in critical},
          "manual critical ledger covers critical set")

    prelim = read_csv("preliminary_run/preliminary_64_failures.csv")
    prelim_counts = Counter(r["STATUS_AFTER"] for r in prelim)
    replay_identity = read_json("preliminary_run/preliminary_replay_identity.json")
    replay_script = ROOT / "preliminary_algorithm_v1_replay.py"
    check("PRELIMINARY_REPLAY", len(prelim) == 64 and len({r["PRELIM_FAIL_ID"] for r in prelim}) == 64
          and replay_identity["preliminary_failure_count"] == 64
          and replay_identity["replay_script_sha256"] == sha256(replay_script),
          "frozen replay script identity and exact 64-row output")
    check("PRELIMINARY_DISPOSITION", prelim_counts == Counter({"RESOLVED": 63, "REMAINS": 1}),
          f"preliminary disposition={dict(prelim_counts)}")
    check("PRELIMINARY_ASSETS", len(list((ROOT / "preliminary_run" / "before_after").glob("*.png"))) == 488,
          "488 per-item before/after evidence images retained")
    tick15 = read_json("preliminary_run/tick_15_semantic_conservation.json")
    check("TICK15_CONSERVATION", tick15["label"] == "15"
          and tick15["pdf_rawdict_sequences"] == [306, 307]
          and tick15["element_ids"] == ["TXT-034", "TXT-035"],
          "x-tick 15 conserved as two chars/two glyphs")

    candidates = read_csv("fullbook_peer_candidates.csv")
    candidate_counts = Counter(r["TARGET_ID"] for r in candidates)
    selected = [r for r in candidates if r["SELECTED"].lower() == "true"]
    check("FULLBOOK_PEER_CANDIDATES", candidate_counts == Counter({"TXT-072": 99, "TXT-098": 64}) and len(selected) == 2,
          "complete exact-metadata sets: TXT-072=99, TXT-098=64")
    calibration = read_csv("fullbook_peer_calibration.csv")
    cal = {r["ELEMENT_ID"]: r for r in calibration}
    check("FULLBOOK_PEER_SELECTION", cal["TXT-072"]["SELECTED_PAGE"] == "17" and cal["TXT-072"]["SELECTED_RAW_SEQUENCE"] == "251"
          and cal["TXT-098"]["SELECTED_PAGE"] == "187" and cal["TXT-098"]["SELECTED_RAW_SEQUENCE"] == "345",
          "policy-selected peers exact")
    check("FULLBOOK_PEER_RESULTS", cal["TXT-072"]["DECISION"] == "PASS" and cal["TXT-098"]["DECISION"] == "FAIL"
          and abs(float(cal["TXT-098"]["AREA_RATIO"]) - 56 / 72) < 1e-15,
          "TXT-072 passes; TXT-098 area ratio 56/72 fails")

    pixel = read_csv("after_pixel_measurements.csv")
    pixel_fails = [r for r in pixel if r["DECISION"] == "FAIL"]
    hard = read_json("hard_failures.json")
    check("HARD_FAILURE_CLOSURE", len(pixel_fails) == 1 and pixel_fails[0]["ELEMENT_ID"] == "TXT-098"
          and len(hard) == 1 and hard[0]["FAIL_ID"] == "PEER-TXT-098"
          and hard[0]["VALUE"] == [1.0, 0.7777777777777778]
          and hard[0]["THRESHOLD"] == [0.92, 1.08],
          "only PEER-TXT-098 remains hard")
    math = read_csv("math_assembly_measurements.csv")
    check("MATH_ASSEMBLIES", len(math) == 2 and all(r["DECISION"] == "PASS" and int(r["H_INK_PX"]) >= 22 for r in math),
          "two equals assemblies meet 22px hard floor")

    top = [ast.literal_eval(r["FINAL_MASK_BBOX_PX"]) for r in objects if r["CLASS"] == "GLYPH" and r["PANEL"] == "TOP"]
    bottom = [ast.literal_eval(r["FINAL_MASK_BBOX_PX"]) for r in objects if r["CLASS"] == "GLYPH" and r["PANEL"] == "BOTTOM"]
    cross_panel = min(bbox_distance(a, b) for a in top for b in bottom)
    check("CROSS_PANEL_TEXT_CLEARANCE", cross_panel >= 8.0, f"exact minimum={cross_panel:.6f}px >= 8px")

    result_text = (ROOT / "RESULT.txt").read_text(encoding="utf-8")
    review_text = (ROOT / "SA1_REVIEW.md").read_text(encoding="utf-8")
    check("REPORT_CONSISTENCY", result_text.startswith("FAIL_TO_SA2\n") and "PEER-TXT-098" in result_text
          and "FAIL_TO_SA2" in review_text and "A_LOCAL_PASS" in review_text,
          "result and review consistently reject SA1 pass")

    parse_counts = {"json": 0, "csv": 0, "markdown_or_text": 0, "png": 0}
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        if path.name in CONTROL_NAMES:
            continue
        suffix = path.suffix.lower()
        if suffix == ".json":
            with path.open("r", encoding="utf-8") as f:
                json.load(f)
            parse_counts["json"] += 1
        elif suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                list(csv.reader(f))
            parse_counts["csv"] += 1
        elif suffix in {".md", ".txt", ".py"}:
            path.read_text(encoding="utf-8")
            parse_counts["markdown_or_text"] += 1
        elif suffix == ".png":
            with Image.open(path) as im:
                im.verify()
            parse_counts["png"] += 1
    check("PARSE_AND_IMAGE_DECODE", all(v > 0 for v in parse_counts.values()), f"parsed/decoded={parse_counts}")

    return {
        "handoff_id": HANDOFF_ID,
        "decision": "PASS",
        "quality_outcome": "FAIL_TO_SA2",
        "check_count": len(checks),
        "checks": checks,
        "N": 172,
        "C_expected": 14706,
        "C_covered": 14706,
        "classification": {"glyph": 112, "explicit_pdf_drawing": 58, "hatch_pattern": 2},
        "critical_pair_count": 102,
        "manual_ledger_counts": ledger_counts,
        "preliminary": {"exact_replay_rows": 64, "resolved": 63, "remains_hard_fail": 1},
        "cross_panel_text_clearance_px": cross_panel,
        "hard_failure": hard[0],
        "parse_counts": parse_counts,
    }


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def preseal() -> None:
    removed = cleanup_unsealed_scaffolding()
    validation = validate()
    validation["preseal_cleanup"] = removed
    write_json(ROOT / "machine_preseal_check.json", validation)
    ads = scan_ads()
    assert_true(ads["decision"] == "PASS", f"ADS scan failed: {ads}")
    write_json(ROOT / "ads_scan.json", ads)
    print(json.dumps({
        "mode": "preseal",
        "decision": "PASS",
        "quality_outcome": "FAIL_TO_SA2",
        "check_count": validation["check_count"],
        "removed_scaffolding": removed,
        "ads": ads["decision"],
        "cross_panel_text_clearance_px": validation["cross_panel_text_clearance_px"],
    }, ensure_ascii=False))


def payload_files() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name not in CONTROL_NAMES)


def wait_for_strictly_later(reference_mtime_ns: int) -> None:
    while time.time_ns() <= reference_mtime_ns:
        time.sleep(0.001)


def seal() -> None:
    seal_path = ROOT / "WRITE_SEAL.json"
    assert_true(not seal_path.exists(), "evidence root already sealed")
    validation = validate()
    preseal_data = read_json("machine_preseal_check.json")
    ads_pre = read_json("ads_scan.json")
    assert_true(preseal_data["decision"] == "PASS" and ads_pre["decision"] == "PASS", "preseal controls not PASS")

    entries = []
    for path in payload_files():
        stat = path.stat()
        entries.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": stat.st_size,
            "sha256": sha256(path),
            "mtime_ns": stat.st_mtime_ns,
        })
    manifest = {
        "handoff_id": HANDOFF_ID,
        "manifest_scope": "all substantive payload; terminal control files excluded to avoid temporal recursion",
        "excluded_terminal_controls": sorted(CONTROL_NAMES),
        "entry_count": len(entries),
        "entries": entries,
        "quality_outcome": "FAIL_TO_SA2",
    }
    manifest_path = ROOT / "FINAL_PAYLOAD_MANIFEST.json"
    write_json(manifest_path, manifest)
    reopened = read_json("FINAL_PAYLOAD_MANIFEST.json")
    assert_true(reopened == manifest and len(reopened["entries"]) == len(entries), "manifest reopen mismatch")
    for entry in reopened["entries"]:
        path = ROOT / Path(entry["path"])
        assert_true(path.stat().st_size == entry["bytes"] and path.stat().st_mtime_ns == entry["mtime_ns"]
                    and sha256(path) == entry["sha256"], f"manifest payload mismatch: {entry['path']}")

    ads_post_manifest = scan_ads()
    assert_true(ads_post_manifest["decision"] == "PASS", f"post-manifest ADS scan failed: {ads_post_manifest}")
    parse_control = {
        "decision": "PASS",
        "validation_check_count": validation["check_count"],
        "manifest_json_reopened": True,
        "manifest_entry_count": len(entries),
        "manifest_payload_hashes_reverified": len(entries),
        "all_payload_parse_and_image_decode": "PASS",
        "ads_post_manifest": ads_post_manifest,
        "quality_outcome": "FAIL_TO_SA2",
    }
    parse_path = ROOT / "manifest_parse_check.json"
    write_json(parse_path, parse_control)
    read_json("manifest_parse_check.json")

    prior_paths = payload_files() + [manifest_path, parse_path]
    max_prior_mtime = max(p.stat().st_mtime_ns for p in prior_paths)
    stop_path = ROOT / "TERMINAL_STOP.json"
    wait_for_strictly_later(max_prior_mtime)
    stop = {
        "handoff_id": HANDOFF_ID,
        "terminal_stop": True,
        "quality_outcome": "FAIL_TO_SA2",
        "prior_file_count": len(prior_paths),
        "max_prior_mtime_ns": max_prior_mtime,
        "statement": "No substantive payload or evidence-root write is permitted after WRITE_SEAL.json is created.",
    }
    write_json(stop_path, stop)
    assert_true(stop_path.stat().st_mtime_ns > max_prior_mtime, "stop marker not strictly later")

    wait_for_strictly_later(stop_path.stat().st_mtime_ns)
    seal = {
        "handoff_id": HANDOFF_ID,
        "write_sealed": True,
        "quality_outcome": "FAIL_TO_SA2",
        "manifest_sha256": sha256(manifest_path),
        "manifest_parse_check_sha256": sha256(parse_path),
        "terminal_stop_sha256": sha256(stop_path),
        "terminal_stop_mtime_ns": stop_path.stat().st_mtime_ns,
        "statement": "WRITE_SEAL.json is the final evidence-root write; subsequent operations are read-only.",
    }
    write_json(seal_path, seal)
    assert_true(seal_path.stat().st_mtime_ns > stop_path.stat().st_mtime_ns, "seal not strictly later than stop")
    print(json.dumps({
        "mode": "seal",
        "decision": "PASS",
        "quality_outcome": "FAIL_TO_SA2",
        "manifest_entries": len(entries),
        "manifest_sha256": seal["manifest_sha256"],
        "parse": "PASS",
        "ads": "PASS",
        "stop_strictly_later": True,
        "seal_strictly_later": True,
    }, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"preseal", "seal"}:
        raise SystemExit("usage: python terminal_checks_and_seal.py preseal|seal")
    if sys.argv[1] == "preseal":
        preseal()
    else:
        seal()
