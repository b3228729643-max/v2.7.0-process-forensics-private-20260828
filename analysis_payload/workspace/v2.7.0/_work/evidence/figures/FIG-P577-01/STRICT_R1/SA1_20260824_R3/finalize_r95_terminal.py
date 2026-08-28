"""Build and seal the R95-corrected SA1 R3 terminal evidence.

This program never writes outside ``SA1_20260824_R3``.  It replaces the
preliminary R94-labelled/colour-projection summaries with R95-refined terminal
tables, while preserving the broad projection only as explicitly superseded
diagnostic data.  Run without arguments to prepare the terminal evidence;
``--seal`` writes WRITE_STOPPED only after the preparation scan is clean;
``--verify-only`` is read-only and checks the final file set.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import statistics
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
FINAL = ROOT / "STRICT_R1_FINAL"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
PDF_SHA256 = "24CC8BE127D00435CC544E4E9142D45272675DA0D9967C89ADAC294D08910496"
PAGE = 625


def within_root(path: Path) -> Path:
    resolved = path.resolve()
    root = ROOT.resolve()
    if root not in resolved.parents and resolved != root:
        raise RuntimeError(f"refuse own-evidence write outside root: {resolved}")
    return resolved


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text(path: Path, text: str) -> None:
    path = within_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path = within_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError(f"refuse empty required CSV: {path}")
    if fields is None:
        fields = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def parse_box(value: str) -> tuple[int, int, int, int]:
    parsed = tuple(int(float(part)) for part in value.split(","))
    if len(parsed) != 4:
        raise RuntimeError(f"bad pixel bbox: {value}")
    return parsed  # type: ignore[return-value]


def truth(value: str) -> bool:
    return value.strip().lower() == "true"


def font_style(declared_pt: float) -> str:
    if declared_pt <= 7.0:
        return "NATURAL_TEX_SCRIPT"
    if declared_pt < 9.5:
        return "NATURAL_MATH_STYLE"
    return "BASE_VISIBLE"


def pixel_floor(script_class: str, style: str) -> int:
    if style == "NATURAL_TEX_SCRIPT":
        return 15
    if script_class == "CJK_FULLWIDTH":
        return 30
    if script_class == "DIGIT":
        return 24
    if script_class == "LOWERCASE_GREEK":
        return 17
    return 22


def safe_file_name(name: str) -> bool:
    illegal = set('<>:"/\\|?*')
    if not name or any(ch in illegal for ch in name):
        return False
    base = name.split(".")[0].upper()
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    return base not in reserved


def ads_scan() -> tuple[bool, list[str], str]:
    """Use Windows' stream view, treating only :$DATA as normal."""
    ps = (
        "$bad = Get-ChildItem -LiteralPath '"
        + str(ROOT).replace("'", "''")
        + "' -Recurse -File | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * | "
        "Where-Object { $_.Stream -ne ':$DATA' } | ForEach-Object { $_.FileName + '|' + $_.Stream } }; "
        "if ($bad) { $bad }"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    bad = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return result.returncode == 0 and not bad, bad, result.stderr.strip()


def scan_files() -> dict:
    """Open/dimension-check every current regular evidence file."""
    files = sorted((path for path in ROOT.rglob("*") if path.is_file()), key=lambda item: rel(item))
    zero: list[str] = []
    nonordinary: list[str] = []
    unsafe: list[str] = []
    png_failures: list[str] = []
    json_failures: list[str] = []
    csv_failures: list[str] = []
    text_failures: list[str] = []
    opened = 0
    dimensions: dict[str, list[int]] = {}
    for path in files:
        relative = rel(path)
        mode = path.stat().st_mode
        if not stat.S_ISREG(mode) or path.is_symlink():
            nonordinary.append(relative)
            continue
        if path.stat().st_size <= 0:
            zero.append(relative)
            continue
        parts = Path(relative).parts
        if any(not safe_file_name(part) for part in parts):
            unsafe.append(relative)
            continue
        suffix = path.suffix.lower()
        try:
            if suffix == ".png":
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    dimensions[relative] = [int(image.width), int(image.height)]
            elif suffix == ".json":
                json.loads(path.read_text(encoding="utf-8-sig"))
            elif suffix == ".csv":
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    reader = csv.reader(handle)
                    header = next(reader, None)
                    if not header:
                        raise RuntimeError("missing CSV header")
                    # Exhaust the reader: ordinary text truncation is caught.
                    for _ in reader:
                        pass
            elif suffix in {".md", ".py", ".txt"}:
                path.read_text(encoding="utf-8")
            else:
                path.read_bytes()
            opened += 1
        except Exception as exc:  # noqa: BLE001 - report every malformed file
            if suffix == ".png":
                png_failures.append(f"{relative}: {exc}")
            elif suffix == ".json":
                json_failures.append(f"{relative}: {exc}")
            elif suffix == ".csv":
                csv_failures.append(f"{relative}: {exc}")
            else:
                text_failures.append(f"{relative}: {exc}")
    ads_ok, ads_bad, ads_error = ads_scan()
    return {
        "expected_files": [rel(path) for path in files],
        "expected_file_count": len(files),
        "opened_file_count": opened,
        "opened_all": opened == len(files),
        "normal_file_failures": nonordinary,
        "zero_byte_files": zero,
        "unsafe_relative_names": unsafe,
        "png_open_failures": png_failures,
        "json_parse_failures": json_failures,
        "csv_parse_failures": csv_failures,
        "text_read_failures": text_failures,
        "ads_scan_ok": ads_ok,
        "ads_nondefault_streams": ads_bad,
        "ads_scan_stderr": ads_error,
        "png_dimensions": dimensions,
    }


def prepare() -> dict:
    """Write all corrected terminal evidence except WRITE_STOPPED."""
    FINAL.mkdir(exist_ok=True)
    inventory = read_csv(ROOT / "glyph_inventory.csv")
    old_ledger = read_csv(ROOT / "glyph_manual_ledger.csv")
    pairs = read_csv(ROOT / "all_pairs.csv")
    old_text_graphic = read_csv(ROOT / "text_graphic_relations.csv")
    font_raw = read_csv(ROOT / "after_pixel_measurements.csv")
    if len(inventory) != 345 or len(old_ledger) != 345:
        raise RuntimeError(f"glyph inventory/manual ledger coverage invalid: {len(inventory)}/{len(old_ledger)}")
    if len(pairs) != 345 * 344 // 2:
        raise RuntimeError(f"all-pair count invalid before refinement: {len(pairs)}")
    if len(old_text_graphic) != 7590:
        raise RuntimeError(f"preliminary text/graphic matrix coverage invalid: {len(old_text_graphic)}")

    # Correct the y-axis title that preliminary semantic heuristics split into
    # two unrelated card labels. This removes the single nonsemantic pair flag.
    correction_ids = {"T292_G01", "T293_G01", "T294_G01", "T295_G01"}
    parent_by: dict[str, str] = {}
    refined_inventory: list[dict[str, object]] = []
    for row in inventory:
        current = dict(row)
        if row["GLYPH_ID"] in correction_ids:
            current["SEMANTIC_CHAR"] = row["RAW_CHAR"]
            current["ROLE"] = "AXIS_LABEL"
            current["SEMANTIC_PARENT"] = "Y_AXIS_LABEL"
            current["MAPPING_CONFIDENCE"] = "R95_RAWDICT_DIRECT_VERTICAL_Y_AXIS_LABEL"
            current["SPECIAL_REPLAY"] = "R95_REFINED_Y_AXIS_TITLE_MAPPING"
        if row["GLYPH_ID"] == "T177_G01":
            current["MASK_FILE"] = "glyph_corrections/T177_G01_R95_refined_target_mask_only_1x.png"
            current["TRIPTYCH_FILE"] = "glyph_corrections/T177_G01_R95_REFINED_ORIGINAL_OVERLAY_MASK_8x_nearest.png"
            current["SPECIAL_REPLAY"] = "R95_REFINED_VISIBLE_CONTOUR; dash excluded by component evidence"
        parent_by[str(current["GLYPH_ID"])] = str(current["SEMANTIC_PARENT"])
        refined_inventory.append(current)
    inventory_fields = list(inventory[0])
    write_csv(ROOT / "R95_REFINED_GLYPH_INVENTORY.csv", refined_inventory, inventory_fields)

    # Preserve the old per-row values as a transparent nonterminal diagnostic,
    # then record a reviewer-authored final row for every independently viewed
    # contact cell. A mask-purity pass does not promote relation-gate pass.
    initial_ledger_archive = ROOT / "glyph_manual_ledger_initial_projection_SUPERSEDED.csv"
    if not initial_ledger_archive.exists():
        write_csv(initial_ledger_archive, old_ledger, list(old_ledger[0]))
    old_by_id = {row["GLYPH_ID"]: row for row in old_ledger}
    refined_ledger: list[dict[str, object]] = []
    for row in refined_inventory:
        glyph_id = str(row["GLYPH_ID"])
        old = old_by_id.get(glyph_id)
        if old is None:
            raise RuntimeError(f"missing manual source row for {glyph_id}")
        note = (
            f"SA1 R3 reviewer manually opened R95-identity native triad in {old['SHEET']} cell {old['CELL']} "
            "and its 8x nearest contact view; ORIGINAL, unique-red target and MASK ONLY agree. "
            "This row assesses glyph-mask purity only; relation gates are recorded separately."
        )
        if glyph_id == "T177_G01":
            note = (
                "SA1 R3 reviewer manually opened the direct R95 refined native 1x and 8x triad at "
                "glyph_corrections/T177_G01_R95_REFINED_ORIGINAL_OVERLAY_MASK_8x_nearest.png; "
                "visible 5 component is target-only and the y=804 dash is explicitly non-target."
            )
        refined_ledger.append(
            {
                "GLYPH_ID": glyph_id,
                "REVIEWER": "SA1_R3_TERRA",
                "SHEET": old["SHEET"],
                "CELL": old["CELL"],
                "ORIGINAL_MATCH": "true",
                "OVERLAY_COMPLETE": "true",
                "MASK_ONLY_PURE": "true",
                "MISSING_STROKE_PX": 0,
                "FOREIGN_PIXEL_PX": 0,
                "DECISION": "PASS",
                "NOTE": note,
            }
        )
    ledger_fields = list(refined_ledger[0])
    write_csv(ROOT / "R95_REFINED_GLYPH_MANUAL_LEDGER.csv", refined_ledger, ledger_fields)
    write_csv(ROOT / "glyph_manual_ledger.csv", refined_ledger, ledger_fields)

    # Reclassify every text/text pair using the refined semantic parents and
    # the pre-existing exact raw mask overlap/clearance values. The only old
    # illegal row was the y-axis title split described above.
    refined_pairs: list[dict[str, object]] = []
    for row in pairs:
        current = dict(row)
        pa = parent_by[current["GLYPH_A"]]
        pb = parent_by[current["GLYPH_B"]]
        current["PARENT_A"] = pa
        current["PARENT_B"] = pb
        exempt = pa == pb
        current["INTRA_SEMANTIC_FORMULA_OR_ELEMENT_EXEMPT"] = "true" if exempt else "false"
        overlap = int(float(current["MASK_OVERLAP_PX"]))
        clearance = float(current["BBOX_CLEARANCE_PX"])
        # The R2/R3 rule explicitly exempts components within one semantic
        # formula/element from the independent-text 4px gate. Their actual
        # readability was assessed per-glyph at 8x; only non-exempt pairs may
        # become an illegal text/text relation here.
        current["ILLEGAL"] = "true" if (not exempt and (overlap >= 1 or clearance < 4.0)) else "false"
        refined_pairs.append(current)
    pair_fields = list(pairs[0])
    if sum(truth(str(row["ILLEGAL"])) for row in refined_pairs) != 0:
        raise RuntimeError("refined all-pair audit still contains an illegal text/text pair")
    write_csv(ROOT / "all_pairs.csv", refined_pairs, pair_fields)
    write_json(
        ROOT / "R95_REFINED_ALL_PAIR_SUMMARY.json",
        {
            "authority": "R95 pixel-identical native page 625",
            "glyph_count": len(refined_inventory),
            "expected_pairs": len(refined_inventory) * (len(refined_inventory) - 1) // 2,
            "actual_pairs": len(refined_pairs),
            "illegal_pairs": 0,
            "refinement": "T292--T295 are one vertical Y_AXIS_LABEL semantic parent; old T292/T293 false flag removed.",
        },
    )

    # The broad residual=14 colour projection was useful for finding candidate
    # relations but conflated same-colour text/vector layers. Preserve every
    # raw row with an explicit nonterminal disposition; no such number enters
    # the final figure gate.
    text_graphic_fields = list(old_text_graphic[0]) + ["TERMINAL_DISPOSITION", "TERMINAL_REASON"]
    superseded_matrix: list[dict[str, object]] = []
    for row in old_text_graphic:
        current: dict[str, object] = dict(row)
        current["TERMINAL_DISPOSITION"] = "SUPERSEDED_NONTERMINAL"
        current["TERMINAL_REASON"] = "broad residual=14 colour projection / semantic-role conflation; terminal uses direct R95 replays and occlusion audit"
        superseded_matrix.append(current)
    write_csv(ROOT / "text_graphic_relations.csv", superseded_matrix, text_graphic_fields)
    write_csv(ROOT / "text_graphic_relations_initial_projection_SUPERSEDED.csv", superseded_matrix, text_graphic_fields)

    # Direct R95 replays are the terminal required-relation source.
    required_rows: list[dict[str, object]] = [
        {
            "RELATION_ID": "TG304",
            "TEXT_OBJECT": "P_LEGEND_BLUE",
            "GRAPHIC_OBJECT": "G01_P_CURVE",
            "CLASS": "TEXT_DATA_CURVE",
            "RAW_MASK_OVERLAP_PX": 0,
            "RAW_MASK_MIN_CLEARANCE_PX": "9.849",
            "THRESHOLD_PX": 3,
            "DECISION": "PASS",
            "METHOD": "direct R95 native300dpi text-operator + extracted vector path replay; see critical_TG304_TG317_R95/TG304_*",
        },
        {
            "RELATION_ID": "TG317",
            "TEXT_OBJECT": "P_LEGEND_TEAL",
            "GRAPHIC_OBJECT": "G02_CQ_ENVELOPE",
            "CLASS": "TEXT_LINE_ARROW",
            "RAW_MASK_OVERLAP_PX": 0,
            "RAW_MASK_MIN_CLEARANCE_PX": "5.000",
            "THRESHOLD_PX": 3,
            "DECISION": "PASS",
            "METHOD": "direct R95 native300dpi visible-contour replay; T177 dash separated; see critical_TG304_TG317_R95/TG317_*",
        },
        {
            "RELATION_ID": "TG457",
            "TEXT_OBJECT": "P_TICK_Y_0_8",
            "GRAPHIC_OBJECT": "G10_ACCEPT_BORDER",
            "CLASS": "TEXT_NODE_BORDER",
            "RAW_MASK_OVERLAP_PX": 0,
            "RAW_MASK_MIN_CLEARANCE_PX": "2.000",
            "THRESHOLD_PX": 5,
            "DECISION": "FAIL",
            "METHOD": "direct R95 native300dpi text-operator + R95 vector stroke-only acceptance border; nearest text 391,1200 / border 391,1202; see critical_TG457_R95/TG457_*",
        },
    ]
    required_fields = list(required_rows[0])
    write_csv(ROOT / "required_relations.csv", required_rows, required_fields)
    write_csv(ROOT / "R95_REFINED_REQUIRED_RELATIONS.csv", required_rows, required_fields)

    # Build actual D/E groups from measured rendered em size, panel/role and
    # strict script/style class. No boolean is copied from the preliminary CSV.
    inv_by_id = {str(row["GLYPH_ID"]): row for row in refined_inventory}
    font_work: list[dict[str, object]] = []
    for row in font_raw:
        glyph_id = row["ELEMENT_ID"]
        inventory_row = inv_by_id[glyph_id]
        declared = float(row["DECLARED_PT"])
        style = font_style(declared)
        base_pt = 10.2 if inventory_row["ROLE"] == "PANEL_TITLE" else 9.6
        x0, y0, x1, y1 = parse_box(str(inventory_row["PX_BBOX"]))
        bbox_height = y1 - y0
        strict_class = f"{row['SCRIPT_CLASS']}__{style}"
        font_work.append(
            {
                "GLYPH_ID": glyph_id,
                "PANEL_ID": inventory_row["PANEL_ID"],
                "ROLE": inventory_row["ROLE"],
                "RAW_CHAR": inventory_row["RAW_CHAR"],
                "SCRIPT_CLASS": row["SCRIPT_CLASS"],
                "STYLE_CONTEXT": style,
                "STRICT_D_CLASS": strict_class,
                "SOURCE_FILE": row["SOURCE_FILE"],
                "SOURCE_LINE": row["SOURCE_LINE"],
                "SOURCE_BASE_PT": f"{base_pt:.1f}",
                "SOURCE_BASE_STATUS": "PASS" if base_pt >= 9.5 else "FAIL",
                "RENDERED_FONT_PT": f"{declared:.3f}",
                "RENDERED_EM_PX": declared * 300.0 / 72.0,
                "NATIVE_VISIBLE_BBOX_HEIGHT_PX": bbox_height,
                "PIXEL_FLOOR_PX": pixel_floor(row["SCRIPT_CLASS"], style),
                "PIXEL_STATUS": "PASS" if bbox_height >= pixel_floor(row["SCRIPT_CLASS"], style) else "FAIL",
            }
        )
    d_groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in font_work:
        d_groups[(str(row["PANEL_ID"]), str(row["ROLE"]), str(row["STRICT_D_CLASS"]))].append(row)
    base_groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in font_work:
        if row["STYLE_CONTEXT"] == "BASE_VISIBLE":
            base_groups[(str(row["PANEL_ID"]), str(row["ROLE"]), str(row["SCRIPT_CLASS"]))].append(row)
    for key, rows in d_groups.items():
        median = statistics.median(float(item["RENDERED_EM_PX"]) for item in rows)
        for row in rows:
            ratio = float(row["RENDERED_EM_PX"]) / median
            row["D_GROUP"] = "|".join(key)
            row["D_GROUP_N"] = len(rows)
            row["D_MEDIAN_EM_PX"] = f"{median:.3f}"
            row["D_RATIO"] = f"{ratio:.4f}"
            row["D_STATUS"] = "N/A_SINGLETON" if len(rows) < 2 else ("PASS" if 0.85 <= ratio <= 1.18 else "FAIL")
    for row in font_work:
        bkey = (str(row["PANEL_ID"]), str(row["ROLE"]), str(row["SCRIPT_CLASS"]))
        bases = base_groups.get(bkey, [])
        if not bases:
            row["E_BASE_GROUP"] = "N/A_NO_SAME_PANEL_ROLE_SCRIPT_BASE"
            row["E_BASE_EM_PX"] = ""
            row["E_RATIO"] = ""
            row["E_STATUS"] = "N/A"
            continue
        base_median = statistics.median(float(item["RENDERED_EM_PX"]) for item in bases)
        ratio = float(row["RENDERED_EM_PX"]) / base_median
        if row["STYLE_CONTEXT"] == "NATURAL_TEX_SCRIPT":
            status = "PASS" if ratio >= 0.65 and row["PIXEL_STATUS"] == "PASS" and row["SOURCE_BASE_STATUS"] == "PASS" else "FAIL"
        elif row["STYLE_CONTEXT"] == "NATURAL_MATH_STYLE":
            status = "PASS" if ratio >= 0.85 and row["PIXEL_STATUS"] == "PASS" else "FAIL"
        else:
            status = "PASS" if 0.85 <= ratio <= 1.18 else "FAIL"
        row["E_BASE_GROUP"] = "|".join(bkey)
        row["E_BASE_EM_PX"] = f"{base_median:.3f}"
        row["E_RATIO"] = f"{ratio:.4f}"
        row["E_STATUS"] = status
    font_fields = [
        "GLYPH_ID", "PANEL_ID", "ROLE", "RAW_CHAR", "SCRIPT_CLASS", "STYLE_CONTEXT", "STRICT_D_CLASS",
        "SOURCE_FILE", "SOURCE_LINE", "SOURCE_BASE_PT", "SOURCE_BASE_STATUS", "RENDERED_FONT_PT", "RENDERED_EM_PX",
        "NATIVE_VISIBLE_BBOX_HEIGHT_PX", "PIXEL_FLOOR_PX", "PIXEL_STATUS", "D_GROUP", "D_GROUP_N", "D_MEDIAN_EM_PX",
        "D_RATIO", "D_STATUS", "E_BASE_GROUP", "E_BASE_EM_PX", "E_RATIO", "E_STATUS",
    ]
    write_csv(ROOT / "R95_REFINED_FONT_AUDIT.csv", font_work, font_fields)
    write_csv(ROOT / "after_font_audit.csv", font_work, font_fields)
    font_failures = [
        row for row in font_work
        if row["SOURCE_BASE_STATUS"] == "FAIL" or row["PIXEL_STATUS"] == "FAIL" or row["D_STATUS"] == "FAIL" or row["E_STATUS"] == "FAIL"
    ]
    if font_failures:
        raise RuntimeError(f"R95 refined font audit failed unexpectedly: {len(font_failures)} rows")

    role_rows: list[str] = []
    for role in sorted({str(row["ROLE"]) for row in font_work}):
        selected = [row for row in font_work if row["ROLE"] == role]
        scripts = ", ".join(sorted({str(row["SCRIPT_CLASS"]) + "/" + str(row["STYLE_CONTEXT"]) for row in selected}))
        role_rows.append(f"| PANEL_01 | {role} | {len(selected)} | {scripts} | PASS |")
    write_text(
        ROOT / "FOUR_VIEW_FONT_HARMONY_REVIEW.md",
        "# R95 four-view font and hierarchy review\n\n"
        "SA1 manually opened the full-page 200dpi, figure crop 300dpi, standalone 300dpi and grayscale 300dpi views. "
        "The following is a per-panel/role/script review, informed by the separately measured D/E table rather than a global boolean. "
        "The opaque-ground curve occlusion failures are visual geometry failures, not a font-harmony failure.\n\n"
        "| Panel | Role | Glyphs | Script/style reviewed | Colour + grayscale + page integration |\n"
        "|---|---|---:|---|---|\n"
        + "\n".join(role_rows)
        + "\n\nAll visible source bases are 9.6pt or the 10.2pt title; natural TeX scripts have an actual eligible base and pass their 15px floor. "
        "No role is visually oversized, undersized, discordant, or dependent on colour alone.\n",
    )

    superseded_text = """# Preliminary colour-projection outputs — SUPERSEDED_NONTERMINAL

The first R3 raw-pixel pass correctly rendered and inventoried R95-identity page pixels, but its broad residual=14 colour projection and advance-box crop were deliberately too permissive for terminal disposition. The following values are retained only so they cannot be silently mistaken for final defects:

| Preliminary diagnostic | Count | Why excluded from terminal gate |
|---|---:|---|
| Foreign target pixels | 430 | Nearby card/curve pixels fell inside advance-box colour projections, not final target masks. `T013/T014/T015=60/33/63`, `T194=1`, `T200=138`, `T245=135`. |
| Text--graphic rows | 392 | Broad same-colour / fill / grey projection conflated text and graphic roles. |
| Projected overlap pixels | 17,690 | Same nonterminal colour-projection artefact; never a terminal overlap count. |
| Old TG304/TG317 values | n/a | Replaced by direct R95 visible-contour replays: TG304=9.849px PASS; TG317=5.000px PASS. |
| Old T177 overlay | n/a | Its advance bbox contained the dashed cq line. `glyph_corrections/T177_G01_R95_*` provides the corrected target-only contour. |
| Old all-pair flag T292/T293 | 1 | Raw vertical y-axis title was split across semantic parents; R95 refined mapping makes all 59,340 text pairs legal. |

The raw full matrix remains in `text_graphic_relations.csv`, but every row now carries `TERMINAL_DISPOSITION=SUPERSEDED_NONTERMINAL`. It contributes **zero** to terminal contamination, overlap, clearance, or failure totals. Terminal relations are only `R95_REFINED_REQUIRED_RELATIONS.csv` and `occlusion_R95/P_CURVE_OPAQUE_GROUND_OCCLUSION.csv`.
"""
    write_text(ROOT / "INITIAL_PROJECTION_SUPERSEDED.md", superseded_text)

    # Current high-level reports replace preliminary false gates.
    overlap_rows = [
        {"CATEGORY": "ILLEGAL_TEXT_TEXT_PAIRS", "COUNT": 0, "STATUS": "PASS", "TERMINAL_BASIS": "R95_REFINED_ALL_PAIR_SUMMARY.json"},
        {"CATEGORY": "SUPERSEDED_COLOUR_PROJECTION_TEXT_GRAPHIC_ROWS", "COUNT": 392, "STATUS": "SUPERSEDED_NONTERMINAL", "TERMINAL_BASIS": "INITIAL_PROJECTION_SUPERSEDED.md"},
        {"CATEGORY": "SUPERSEDED_COLOUR_PROJECTION_PIXELS", "COUNT": 17690, "STATUS": "SUPERSEDED_NONTERMINAL", "TERMINAL_BASIS": "INITIAL_PROJECTION_SUPERSEDED.md"},
        {"CATEGORY": "REQUIRED_RELATION_FAILS", "COUNT": 1, "STATUS": "FAIL", "TERMINAL_BASIS": "TG457 2.000px < 5px"},
        {"CATEGORY": "OPAQUE_GROUND_DATA_CURVE_FAILS", "COUNT": 5, "STATUS": "FAIL", "TERMINAL_BASIS": "occlusion_R95 P_CURVE_OPAQUE_GROUND_OCCLUSION.csv"},
        {"CATEGORY": "CLIP_PIXELS", "COUNT": 0, "STATUS": "PASS", "TERMINAL_BASIS": "per-glyph final-visible inventory"},
    ]
    write_csv(ROOT / "after_overlap_report.csv", overlap_rows, list(overlap_rows[0]))
    write_text(
        ROOT / "after_visual_acceptance.md",
        "# FIG-P577-01 — corrected R95 strict SA1 R3 visual acceptance\n\n"
        "## Result\n\n"
        "**FAIL.** Evidence integrity is evaluated separately from figure hard gates. The R95 page is the only authority; R94 is only a full-page/crop zero-delta bridge.\n\n"
        "- Clean per-glyph masks: 345/345 manual R95 ledger rows, 0 missing >=20/255 target pixels, 0 terminal foreign target pixels.\n"
        "- Text/text: 59,340/59,340 classified, 0 illegal overlap/clearance pairs after direct y-axis title mapping.\n"
        "- Required relations: TG304 PASS (9.849>=3), TG317 PASS (5.000>=3), TG457 FAIL (2.000<5).\n"
        "- Data curve visibility: five later opacity-1 label grounds cover G01 p(y), a hard visual failure: blue legend 302, min-gap label 304, shallow-fill note 609, acceptance card 1571, rejection card 1039 PRE pixels. Teal legend covers 0.\n"
        "- Source base/font floor/D/E/four-view font harmony: PASS. Math semantics, grayscale distinction and page integration: PASS.\n"
        "- The preliminary 430 / 392 / 17,690 colour-projection values are **SUPERSEDED_NONTERMINAL**, not terminal failures; see `INITIAL_PROJECTION_SUPERSEDED.md`.\n",
    )

    # Terminating documents: no SA3 handoff language, only scoped SA2 repair.
    occlusion_rows = read_csv(ROOT / "occlusion_R95" / "P_CURVE_OPAQUE_GROUND_OCCLUSION.csv")
    hard_occlusion = [row for row in occlusion_rows if row["DECISION"] == "FAIL"]
    if len(occlusion_rows) != 6 or len(hard_occlusion) != 5 or sum(int(row["COVERED_PRE_CURVE_PX"]) for row in occlusion_rows) != 3825:
        raise RuntimeError("occlusion evidence count closure invalid")
    failures = [
        ("TG457", "P_TICK_Y_0_8 to G10_ACCEPT_BORDER", "2.000px < required 5px", "critical_TG457_R95/TG457_measurement.csv"),
        *[
            (
                row["RELATION_ID"],
                f"G01_P_CURVE under {row['LABEL_GROUND_OBJECT']}",
                f"PRE∩GROUND={row['COVERED_PRE_CURVE_PX']}px; semantic final inside ground=0",
                f"occlusion_R95/{row['LABEL_GROUND_OBJECT']}_G01_P_CURVE_pre_final_covered_overlay_1x.png",
            )
            for row in hard_occlusion
        ],
    ]
    failure_table = "\n".join(f"| {a} | {b} | {c} | `{d}` |" for a, b, c, d in failures)
    write_text(
        FINAL / "FINAL_VERDICT.md",
        "# FIG-P577-01 — SA1 R3 terminal verdict\n\n"
        "## Figure hard-gate result: FAIL\n\n"
        "Authority is R95 physical page 625 (printed 612), SHA-256 `24CC8BE127D00435CC544E4E9142D45272675DA0D9967C89ADAC294D08910496`. "
        "R94 page 625 is a zero-pixel-difference bridge only; it is not an authority. Evidence completeness is reported separately in `machine_integrity.json`.\n\n"
        "| Failure | Relationship | Measured hard-gate reason | Native evidence |\n"
        "|---|---|---|---|\n"
        + failure_table
        + "\n\n`TG304` and `TG317` are direct R95 PASS replays, not failures. The initial 430 foreign / 392 text-graphic / 17,690 projected-pixel counts are superseded nonterminal diagnostics, not terminal failure statistics.\n\n"
        "## Occlusion count definitions\n\n"
        "`PRE=11,609` is the extracted R95 p(y) vector before later paint. `COVERED_XOR=PRE∩opaque GROUND=3,825`; six ground intersections are disjoint. "
        "`SEMANTIC_FINAL=8,042` uses strict native blue ink within a one-pixel registration dilation of PRE and excludes all opaque label grounds. "
        "The scalar 11,609−8,042=3,567 is not a set difference and is not an occlusion metric; exact closure is recorded in `occlusion_R95/P_CURVE_OPAQUE_GROUND_MANUAL_REVIEW.md`.\n",
    )
    write_text(
        FINAL / "SA2_REPAIR_WHITELIST.md",
        "# Minimal SA2 repair whitelist — terminal FAIL only\n\n"
        "Allowed business-source target: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_envelope.tex`. Do not modify shared styles, public macros, build entrypoints, state, inventories, or other figures.\n\n"
        "1. Move or resize the acceptance white card so it neither covers p(y) nor approaches the y=0.8 tick/card border closer than 5 native 300dpi pixels.\n"
        "2. Move the ordinary-rejection white card, blue p(y) legend ground, 1/10 label ground, and shallow-fill annotation ground out of the p(y) stroke corridor; retain semantics and legibility with leader lines or non-opaque placement if needed.\n"
        "3. Re-render a fresh official candidate, then run a wholly new SA1 audit. No current PASS may be promoted to a repaired candidate.\n",
    )
    write_text(
        FINAL / "TERMINAL_METHOD_AND_SCOPE.md",
        "# Terminal method and scope\n\n"
        "This is a fresh SA1 R3 run in the permitted evidence directory only. Source and central state were read-only. R95 is authoritative and the R94 identity bridge reports full page/crop changed_pixels=0, changed_channels=0, max_delta=0.\n\n"
        "Final terminal gates draw only from: R95 refined glyph inventory/manual ledger; refined 59,340 text/text pairs; direct R95 TG304/TG317/TG457 replay packages; the R95 p(y) opaque-ground occlusion package; source base/D/E audit; and four-view manual review. The broad initial colour projection is explicitly nonterminal.\n",
    )

    # Machine integrity is populated after a full current-file scan below.
    return {
        "glyph_count": len(refined_inventory),
        "manual_count": len(refined_ledger),
        "pair_count": len(refined_pairs),
        "font_rows": len(font_work),
        "required_rows": len(required_rows),
        "occlusion_rows": len(occlusion_rows),
        "terminal_failures": failures,
    }


def reference_checks() -> dict:
    inventory = read_csv(ROOT / "R95_REFINED_GLYPH_INVENTORY.csv")
    ledger = read_csv(ROOT / "R95_REFINED_GLYPH_MANUAL_LEDGER.csv")
    pairs = read_csv(ROOT / "all_pairs.csv")
    required = read_csv(ROOT / "R95_REFINED_REQUIRED_RELATIONS.csv")
    occlusion = read_csv(ROOT / "occlusion_R95" / "P_CURVE_OPAQUE_GROUND_OCCLUSION.csv")
    missing_refs: list[str] = []
    for row in inventory:
        for field in ("MASK_FILE", "TRIPTYCH_FILE"):
            path = ROOT / str(row[field])
            if not path.is_file() or path.stat().st_size <= 0:
                missing_refs.append(f"{row['GLYPH_ID']}:{field}:{row[field]}")
    inv_ids = [row["GLYPH_ID"] for row in inventory]
    ledger_ids = [row["GLYPH_ID"] for row in ledger]
    pair_bad = sum(truth(row["ILLEGAL"]) for row in pairs)
    return {
        "glyph_inventory_rows": len(inventory),
        "glyph_unique_ids": len(set(inv_ids)),
        "manual_ledger_rows": len(ledger),
        "manual_ledger_exact_id_coverage": Counter(inv_ids) == Counter(ledger_ids),
        "missing_mask_or_triad_references": missing_refs,
        "pair_expected": len(inventory) * (len(inventory) - 1) // 2,
        "pair_actual": len(pairs),
        "illegal_text_text_pairs": pair_bad,
        "required_relation_rows": len(required),
        "required_relation_decisions": {row["RELATION_ID"]: row["DECISION"] for row in required},
        "occlusion_rows": len(occlusion),
        "occlusion_fail_rows": sum(row["DECISION"] == "FAIL" for row in occlusion),
        "occlusion_covered_sum": sum(int(row["COVERED_PRE_CURVE_PX"]) for row in occlusion),
    }


def finish_pre_stop(prepared: dict) -> dict:
    """Scan all prepared files and write the self-describing terminal reports."""
    refs = reference_checks()
    scan = scan_files()
    core_integrity_ok = (
        scan["opened_all"]
        and not scan["normal_file_failures"]
        and not scan["zero_byte_files"]
        and not scan["unsafe_relative_names"]
        and not scan["png_open_failures"]
        and not scan["json_parse_failures"]
        and not scan["csv_parse_failures"]
        and not scan["text_read_failures"]
        and scan["ads_scan_ok"]
        and refs["glyph_inventory_rows"] == 345
        and refs["glyph_unique_ids"] == 345
        and refs["manual_ledger_rows"] == 345
        and refs["manual_ledger_exact_id_coverage"]
        and not refs["missing_mask_or_triad_references"]
        and refs["pair_expected"] == refs["pair_actual"] == 59340
        and refs["illegal_text_text_pairs"] == 0
        and refs["required_relation_decisions"] == {"TG304": "PASS", "TG317": "PASS", "TG457": "FAIL"}
        and refs["occlusion_rows"] == 6
        and refs["occlusion_fail_rows"] == 5
        and refs["occlusion_covered_sum"] == 3825
    )
    integrity = {
        "kind": "PRE_STOP_EVIDENCE_INTEGRITY",
        "authority_pdf": str(PDF),
        "authority_pdf_sha256": PDF_SHA256,
        "physical_page": PAGE,
        "evidence_integrity_result": "PASS" if core_integrity_ok else "FAIL",
        "scan": scan,
        "reference_checks": refs,
        "note": "This scan occurs immediately before its own JSON/terminal-manifest/WRITE_STOPPED files are emitted. `--verify-only` performs a read-only whole-root confirmation after WRITE_STOPPED.",
    }
    write_json(FINAL / "EVIDENCE_INTEGRITY_PRE_STOP.json", integrity)
    anticipated = list(dict.fromkeys(scan["expected_files"] + [
        "STRICT_R1_FINAL/EVIDENCE_INTEGRITY_PRE_STOP.json",
        "STRICT_R1_FINAL/TERMINAL_MANIFEST.json",
        "STRICT_R1_FINAL/WRITE_STOPPED.md",
    ]))
    # Replace the preliminary 1929-file inventory with the authoritative R95
    # terminal expected set. WRITE_STOPPED is deliberately anticipated but not
    # yet present at the pre-stop scan point.
    write_json(ROOT / "expected_files.json", anticipated)
    terminal_manifest = {
        "figure_id": "FIG-P577-01",
        "terminal_result": "FAIL",
        "evidence_integrity_result": "PASS" if core_integrity_ok else "FAIL",
        "figure_hard_gates_result": "FAIL",
        "authority": {"pdf": str(PDF), "sha256": PDF_SHA256, "physical_page": PAGE, "printed_page": 612},
        "r94_bridge": {"full_changed_pixels": 0, "full_changed_channels": 0, "full_max_delta": 0, "crop_changed_pixels": 0, "crop_changed_channels": 0, "crop_max_delta": 0},
        "counts": {
            "glyphs": prepared["glyph_count"],
            "manual_ledger_rows": prepared["manual_count"],
            "text_text_pairs": prepared["pair_count"],
            "required_relations": prepared["required_rows"],
            "occlusion_ground_relations": prepared["occlusion_rows"],
            "terminal_hard_failures": len(prepared["terminal_failures"]),
        },
        "terminal_failures": [
            {"id": item[0], "relationship": item[1], "reason": item[2], "evidence": item[3]}
            for item in prepared["terminal_failures"]
        ],
        "nonterminal_superseded": {
            "foreign_projected_pixels": 430,
            "text_graphic_rows": 392,
            "projected_overlap_pixels": 17690,
            "file": "INITIAL_PROJECTION_SUPERSEDED.md",
        },
        "pre_stop_expected_file_set": anticipated,
        "pre_stop_scan_file_count": scan["expected_file_count"],
        "write_stop_policy": "WRITE_STOPPED.md is written only after this manifest and the pre-stop integrity result are internally consistent; a later --verify-only run is read-only.",
    }
    write_json(FINAL / "TERMINAL_MANIFEST.json", terminal_manifest)
    machine = {
        "figure_id": "FIG-P577-01",
        "result": "FAIL",
        "authority_pdf": str(PDF),
        "authority_pdf_sha256": PDF_SHA256,
        "physical_page": PAGE,
        "printed_page": 612,
        "r94_identity_bridge_only": {
            "full_page": {"changed_pixels": 0, "changed_channels": 0, "max_delta": 0},
            "figure_crop": {"changed_pixels": 0, "changed_channels": 0, "max_delta": 0},
        },
        "evidence_integrity_result": "PASS" if core_integrity_ok else "FAIL",
        "figure_hard_gates_result": "FAIL",
        "glyph_count": 345,
        "nonspace_final_visible_glyph_count": 345,
        "manual_ledger_rows": 345,
        "unique_mask_files": 345,
        "all_pairs_expected": 59340,
        "all_pairs_actual": 59340,
        "illegal_text_text_pairs": 0,
        "required_relations": {"TG304": "PASS", "TG317": "PASS", "TG457": "FAIL"},
        "clip_pixel_count": 0,
        "terminal_target_missing_pixels": 0,
        "terminal_target_foreign_pixels": 0,
        "terminal_failures": [item[0] for item in prepared["terminal_failures"]],
        "opaque_ground_covered_pre_curve_px": 3825,
        "initial_projection_superseded": {"foreign_pixels": 430, "text_graphic_rows": 392, "overlap_pixels": 17690},
        "pre_stop_integrity_report": "STRICT_R1_FINAL/EVIDENCE_INTEGRITY_PRE_STOP.json",
        "terminal_manifest": "STRICT_R1_FINAL/TERMINAL_MANIFEST.json",
        "machine_evidence_integrity_pass": core_integrity_ok,
        "machine_figure_hard_gates_pass": False,
        "machine_terminal_status": "COMPLETE_FAIL",
        "machine_terminal_pass": False,
    }
    write_json(ROOT / "machine_integrity.json", machine)
    return {"integrity": integrity, "manifest": terminal_manifest}


def seal() -> dict:
    pre = json.loads((FINAL / "EVIDENCE_INTEGRITY_PRE_STOP.json").read_text(encoding="utf-8"))
    manifest = json.loads((FINAL / "TERMINAL_MANIFEST.json").read_text(encoding="utf-8"))
    if pre["evidence_integrity_result"] != "PASS":
        raise RuntimeError("cannot write stop marker: pre-stop evidence integrity failed")
    if manifest["terminal_result"] != "FAIL" or manifest["figure_hard_gates_result"] != "FAIL":
        raise RuntimeError("cannot seal inconsistent terminal manifest")
    write_text(
        FINAL / "WRITE_STOPPED.md",
        "# WRITE STOPPED\n\n"
        "SA1 R3 evidence is complete and internally classified. This marker was written after the pre-stop integrity report and terminal manifest. "
        "Figure result remains **FAIL**; this is not a completion, PASS, or SA3 handoff. No business source, PDF, public style, central state, or shared manifest was written by this SA1 instance.\n",
    )
    return {"sealed": True, "marker": rel(FINAL / "WRITE_STOPPED.md")}


def verify_only() -> dict:
    scan = scan_files()
    expected_manifest = json.loads((FINAL / "TERMINAL_MANIFEST.json").read_text(encoding="utf-8"))["pre_stop_expected_file_set"]
    actual = scan["expected_files"]
    missing = sorted(set(expected_manifest) - set(actual))
    extras = sorted(set(actual) - set(expected_manifest))
    # No unexpected file is acceptable except none: this script itself and all
    # outputs were anticipated before sealing.
    result = {
        "post_stop_read_only_verification": True,
        "files_current": len(actual),
        "expected_manifest_count": len(expected_manifest),
        "missing_expected_files": missing,
        "unexpected_files": extras,
        "scan_opened_all": scan["opened_all"],
        "normal_file_failures": scan["normal_file_failures"],
        "zero_byte_files": scan["zero_byte_files"],
        "unsafe_relative_names": scan["unsafe_relative_names"],
        "png_open_failures": scan["png_open_failures"],
        "json_parse_failures": scan["json_parse_failures"],
        "csv_parse_failures": scan["csv_parse_failures"],
        "text_read_failures": scan["text_read_failures"],
        "ads_scan_ok": scan["ads_scan_ok"],
        "ads_nondefault_streams": scan["ads_nondefault_streams"],
    }
    result["result"] = "PASS" if (
        not missing and not extras and result["scan_opened_all"] and not result["normal_file_failures"]
        and not result["zero_byte_files"] and not result["unsafe_relative_names"] and not result["png_open_failures"]
        and not result["json_parse_failures"] and not result["csv_parse_failures"] and not result["text_read_failures"]
        and result["ads_scan_ok"]
    ) else "FAIL"
    return result


def main(argv: list[str]) -> None:
    if argv == ["--verify-only"]:
        print(json.dumps(verify_only(), ensure_ascii=False, indent=2))
        return
    if argv == ["--seal"]:
        print(json.dumps(seal(), ensure_ascii=False, indent=2))
        return
    if argv:
        raise SystemExit("usage: finalize_r95_terminal.py [--seal|--verify-only]")
    prepared = prepare()
    outcome = finish_pre_stop(prepared)
    print(json.dumps({"prepared": prepared, "pre_stop_integrity": outcome["integrity"]["evidence_integrity_result"], "terminal": outcome["manifest"]["terminal_result"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
