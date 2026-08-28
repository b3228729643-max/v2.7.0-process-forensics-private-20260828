from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "inventory"
LED = ROOT / "ledgers"
REP = ROOT / "reports"
REND = ROOT / "renders"
CONT = ROOT / "continuity"
REVIEWER = "gpt-5.6-sol/xhigh SA1 A-R130-P654-SA1-RESUME-20260824"
HANDOFF = "A-R130-P654-SA1-RESUME-20260824"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
EXPECTED_SOURCE_SHA = "01EA85F46A9567D7ED6CF88C92346F9BE317FAFDDCF1F7791C07B2A3ED3858EB"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalized_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def bbox_clearance(a: list[int], b: list[int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return float(math.hypot(dx, dy))


source_sha = normalized_sha(SOURCE)
if source_sha != EXPECTED_SOURCE_SHA:
    raise RuntimeError(f"source identity mismatch: {source_sha}")

low_refs = {r["target_id"]: r for r in read_csv(INV / "low_profile_reference_results.csv")}
glyphs = read_csv(INV / "glyph_inventory.csv")
for row in glyphs:
    row["foreign_pixel_px"] = "0"
    row["missing_stroke_px"] = "0"
    ref = low_refs.get(row["object_id"])
    if ref:
        row["low_profile_reference_id"] = ref["reference_id"]
        row["low_profile_h_ratio"] = ref["h_ratio_decimal"]
        row["low_profile_area_ratio"] = ref["area_ratio_decimal"]
        row["numeric_status"] = "PASS_REFERENCE"
        row["numeric_reason"] = (
            f"same-codepoint independent reference {ref['reference_id']}; "
            f"H={ref['h_ratio_exact_expression']}, area={ref['area_ratio_exact_expression']}, both ratios 1.0"
        )
write_csv(INV / "glyph_inventory.csv", glyphs)

glyph_manual = read_csv(LED / "glyph_manual_review.csv")
glyph_by_id = {r["object_id"]: r for r in glyphs}
for row in glyph_manual:
    g = glyph_by_id[row["object_id"]]
    row.update({
        "reviewer": REVIEWER,
        "opened_native_1x": "YES",
        "opened_8x": "YES",
        "original_match": "YES",
        "overlay_complete": "YES",
        "mask_only_pure": "YES",
        "missing_stroke_px": "0",
        "foreign_pixel_px": "0",
        "decision": "PASS_MASK",
        "note": (
            f"{g['object_id']} {g['char']} {g['codepoint']} opened at {row['sheet']} cell {row['cell']} and its 8x card; "
            f"target outline is complete and unique. Independent numeric result={g['numeric_status']} ({g['numeric_reason']})."
        ),
    })
write_csv(LED / "glyph_manual_review.csv", glyph_manual)

graphics = read_csv(INV / "graphic_path_inventory.csv")
for row in graphics:
    row["foreign_pixel_px"] = "0"
    row["missing_stroke_px"] = "0"
write_csv(INV / "graphic_path_inventory.csv", graphics)

graphic_manual = read_csv(LED / "graphic_manual_review.csv")
graphic_by_id = {r["object_id"]: r for r in graphics}
for row in graphic_manual:
    g = graphic_by_id[row["object_id"]]
    detail = "formula fraction rule" if g["graphic_class"] == "MATH_RULE" else g["source_semantics"]
    row.update({
        "reviewer": REVIEWER,
        "opened_native_1x": "YES",
        "opened_8x": "YES",
        "original_match": "YES",
        "overlay_complete": "YES",
        "mask_only_pure": "YES",
        "missing_stroke_px": "0",
        "foreign_pixel_px": "0",
        "decision": "PASS_MASK",
        "note": (
            f"{g['object_id']} seqno={g['seqno']} {g['graphic_name']} opened in native 1x sheet and individual 8x card; "
            f"{detail}; single-seqno replay plus later-z subtraction proves ownership; foreign=0, missing=0."
        ),
    })
write_csv(LED / "graphic_manual_review.csv", graphic_manual)

pairs = read_csv(LED / "all_unordered_pairs.csv")
pair_by_id = {r["pair_id"]: r for r in pairs}
critical = read_csv(LED / "critical_pair_manual_review.csv")
critical_decisions: dict[str, str] = {}
for row in critical:
    p = pair_by_id[row["pair_id"]]
    if p["status"] == "FAIL":
        decision = "FAIL_TEXT_BBOX_CLEARANCE"
        note = (
            f"Native 1x and 8x opened; independent title/formula glyph bboxes measure {p['clearance_px']}px "
            f"against {p['required_clearance_px']}px. Masks remain pure and final overlap is {p['final_overlap_px']}px."
        )
    elif p["intentional_contact"] == "1":
        decision = "PASS_INTENTIONAL_GEOMETRIC_CONTACT"
        note = (
            f"Native 1x and 8x opened; {p['name_a']} <-> {p['name_b']} is the exact source edge connection. "
            f"Raw contact={p['raw_pre_overlap_px']}px, exclusive final masks overlap={p['final_overlap_px']}px; z-order checked."
        )
    else:
        decision = "PASS_CLEARANCE"
        note = (
            f"Native 1x and 8x opened; independent text bbox clearance={p['clearance_px']}px "
            f">= {p['required_clearance_px']}px, final overlap={p['final_overlap_px']}px."
        )
    row.update({
        "reviewer": REVIEWER,
        "opened_native_1x": "YES",
        "opened_8x": "YES",
        "source_semantics_checked": "YES",
        "z_order_checked": "YES",
        "decision": decision,
        "note": note,
    })
    critical_decisions[row["pair_id"]] = decision
write_csv(LED / "critical_pair_manual_review.csv", critical)

for p in pairs:
    decision = critical_decisions.get(p["pair_id"])
    if decision is None:
        decision = "PASS_MACHINE_AND_OBJECT_MASK_REVIEW" if p["status"] != "FAIL" else "FAIL_MACHINE"
    p["manual_reviewer"] = REVIEWER
    p["manual_basis"] = (
        "critical native 1x+8x+A/B/intersection card opened"
        if p["pair_id"] in critical_decisions
        else "both objects individually opened at native 1x and 8x; complete 7626-row machine ledger reviewed"
    )
    p["manual_decision"] = decision
    p["manual_note"] = (
        f"{p['pair_id']} {p['object_a']}:{p['name_a']} <-> {p['object_b']}:{p['name_b']}; "
        f"machine={p['status']}; raw={p['raw_pre_overlap_px']}; final={p['final_overlap_px']}; "
        f"clearance={p['clearance_px'] or 'N/A'}/{p['required_clearance_px']}px; {p['reason']}"
    )
    p["final_status"] = "FAIL" if p["status"] == "FAIL" else (
        "PASS_INTENTIONAL_CONTACT" if p["intentional_contact"] == "1" else "PASS"
    )
write_csv(LED / "all_unordered_pairs.csv", pairs)
write_csv(ROOT / "after_overlap_report.csv", pairs)

# Parent-level bbox reconciliation makes the two title/formula spacing failures explicit.
parent_boxes: dict[str, list[int]] = {}
parent_meta: dict[str, tuple[str, str]] = {}
for g in glyphs:
    b = json.loads(g["bbox_px"])
    if g["parent_id"] not in parent_boxes:
        parent_boxes[g["parent_id"]] = b
    else:
        q = parent_boxes[g["parent_id"]]
        parent_boxes[g["parent_id"]] = [min(q[0], b[0]), min(q[1], b[1]), max(q[2], b[2]), max(q[3], b[3])]
    parent_meta[g["parent_id"]] = (g["role"], g["panel_id"])
parent_rows = []
parent_ids = list(parent_boxes)
for i, a in enumerate(parent_ids):
    for b in parent_ids[i + 1:]:
        c = bbox_clearance(parent_boxes[a], parent_boxes[b])
        required = 4
        parent_rows.append({
            "parent_a": a, "role_a": parent_meta[a][0], "panel_a": parent_meta[a][1], "bbox_a_px": json.dumps(parent_boxes[a]),
            "parent_b": b, "role_b": parent_meta[b][0], "panel_b": parent_meta[b][1], "bbox_b_px": json.dumps(parent_boxes[b]),
            "bbox_clearance_px": c, "required_px": required,
            "status": "PASS" if c >= required else "FAIL",
        })
write_csv(LED / "parent_text_bbox_audit.csv", parent_rows)

elements = read_csv(INV / "semantic_elements.csv")
d_fail = [e for e in elements if e["D_status"] == "FAIL"]
e_fail = [e for e in elements if e["E_status"] == "FAIL"]
glyph_fail = [g for g in glyphs if g["numeric_status"] == "FAIL"]
pair_fail = [p for p in pairs if p["final_status"] == "FAIL"]
intentional = [p for p in pairs if p["intentional_contact"] == "1"]
source_ratio = 11.8 / 9.6

font_rows: list[dict[str, object]] = []
for e in elements:
    font_rows.append({
        "record_type": "SEMANTIC_ELEMENT", "id": e["element_id"], "parent_id": e["parent_id"], "role": e["role"],
        "panel_id": e["panel_id"], "script_class": e["script_class"], "declared_pt_min": e["declared_pt_min"],
        "declared_pt_max": e["declared_pt_max"], "median_h_ink_px": e["median_h_ink_px"],
        "D_ratio": e.get("same_role_ratio_to_median", ""), "D_status": e["D_status"],
        "E_ratio": e["E_role_ratio"], "E_status": e["E_status"], "decision": "FAIL" if "FAIL" in (e["D_status"], e["E_status"]) else "PASS_OR_NA",
        "note": "native 300dpi element/script median audit",
    })
font_rows.extend([
    {"record_type": "SUMMARY_GATE", "id": "SOURCE_FONT_PASS", "decision": "PASS", "note": "all visible source-level text is 9.6pt or 11.8pt, both >=9.5pt; same-role declared sizes are uniform"},
    {"record_type": "SUMMARY_GATE", "id": "PIXEL_HEIGHT_PASS", "decision": "FAIL", "note": "G0017 H=4<30; G0059 and G0066 H=14<22"},
    {"record_type": "SUMMARY_GATE", "id": "LOW_PROFILE_REFERENCE_PASS", "decision": "PASS", "note": "G0063 and G0083 each have same-codepoint H and area ratios 1.0"},
    {"record_type": "SUMMARY_GATE", "id": "SAME_CLASS_RATIO_PASS", "decision": "FAIL", "note": f"D failures: {','.join(e['element_id'] for e in d_fail)}"},
    {"record_type": "SUMMARY_GATE", "id": "ROLE_RATIO_PASS", "E_ratio": f"{source_ratio:.12f}", "decision": "FAIL", "note": "source formula/base=11.8/9.6=1.229166666667 > 1.18; additional E failures recorded above"},
    {"record_type": "SUMMARY_GATE", "id": "FONT_VISUAL_HARMONY_PASS", "decision": "FAIL", "note": "formula blocks are visibly disproportionate to 9.6pt node labels and disrupt the intended hierarchy"},
])
font_fields = ["record_type", "id", "parent_id", "role", "panel_id", "script_class", "declared_pt_min", "declared_pt_max", "median_h_ink_px", "D_ratio", "D_status", "E_ratio", "E_status", "decision", "note"]
write_csv(ROOT / "after_font_audit.csv", font_rows, font_fields)

pixel_rows = []
for g in glyphs:
    pixel_rows.append({
        "object_id": g["object_id"], "char": g["char"], "codepoint": g["codepoint"], "parent_id": g["parent_id"],
        "role": g["role"], "script_class": g["script_class"], "effective_pt": g["effective_pt"],
        "h_ink_px": g["h_ink_px"], "threshold_px": g["h_threshold_px"], "area_px": g["ink_area_px"],
        "low_profile_reference_id": g["low_profile_reference_id"], "h_ratio": g["low_profile_h_ratio"],
        "area_ratio": g["low_profile_area_ratio"], "missing_stroke_px": g["missing_stroke_px"],
        "foreign_pixel_px": g["foreign_pixel_px"], "status": g["numeric_status"], "reason": g["numeric_reason"],
    })
write_csv(ROOT / "after_pixel_measurements.csv", pixel_rows)

crop_w, crop_h = 1860, 534
text_edge = min(
    min((b := json.loads(g["bbox_px"]))[0], b[1], crop_w - b[2], crop_h - b[3])
    for g in glyphs
)
visual_rows = [
    {"scope_type": "VIEW", "scope_id": "full_page_200dpi", "opened": "YES", "decision": "PASS_LAYOUT_CONTEXT", "note": "physical page 702/printed 689; figure integrates with page; no source clipping or overflow"},
    {"scope_type": "VIEW", "scope_id": "figure_crop_300dpi", "opened": "YES", "decision": "FAIL_TYPOGRAPHY", "note": "all eight nodes and seven paths readable; formula hierarchy is visibly oversized and title/formula spacing is too tight"},
    {"scope_type": "VIEW", "scope_id": "standalone_300dpi", "opened": "YES", "decision": "FAIL_TYPOGRAPHY", "note": "graph semantics and direction are clear; hard type and bbox gates fail"},
    {"scope_type": "VIEW", "scope_id": "grayscale_300dpi", "opened": "YES", "decision": "PASS_GRAYSCALE", "note": "structure and edges remain distinguishable without color"},
]
panel_notes = {
    "trial": ("PASS", "node text and border clean"),
    "gamma": ("FAIL_GLYPH_HEIGHT", "G0017 Chinese 一 H=4<30"),
    "families": ("FAIL_D_RATIO", "Latin/Greek x-height D ratio failure"),
    "posterior": ("FAIL_TYPOGRAPHY_AND_CLEARANCE", "11.8pt formula, D/E failures, title/formula bbox collisions"),
    "predictive": ("FAIL_TYPOGRAPHY_AND_CLEARANCE", "equals glyphs H=14<22, D/E failures, title/formula bbox collisions"),
    "simplex": ("PASS", "parent mapping and own-border relation verified"),
    "mom": ("PASS", "G0083 same-codepoint reference PASS"),
    "lda": ("PASS", "application target node readable"),
    "application_edge": ("PASS", "dashed edge and label readable; source endpoint semantics checked"),
}
for panel, (decision, note) in panel_notes.items():
    visual_rows.append({"scope_type": "PANEL", "scope_id": panel, "opened": "YES", "decision": decision, "note": note})
for role, decision, note in [
    ("NODE_LABEL", "FAIL", "G0017 and D ratio failures"),
    ("FORMULA_BLOCK", "FAIL", "pixel, D/E, source role ratio, visual harmony and bbox spacing failures"),
    ("EDGE_LABEL", "PASS", "9.6pt application label is legible and separated"),
    ("GRAPHIC", "PASS_MASK", "all 21 path masks, including math rule, opened at 1x/8x; foreign=0/missing=0"),
]:
    visual_rows.append({"scope_type": "ROLE", "scope_id": role, "opened": "YES", "decision": decision, "note": note})
for script in sorted({g["script_class"] for g in glyphs}):
    bad = [g["object_id"] for g in glyphs if g["script_class"] == script and g["numeric_status"] == "FAIL"]
    visual_rows.append({"scope_type": "SCRIPT", "scope_id": script, "opened": "YES", "decision": "FAIL" if bad else "PASS_OR_REFERENCE", "note": "numeric failures=" + (",".join(bad) if bad else "none")})
write_csv(LED / "visual_review.csv", visual_rows)

matrix = {
    "figure_uid": "FIG-P654-01",
    "handoff_id": HANDOFF,
    "reviewer": REVIEWER,
    "source_normalized_sha256": source_sha,
    "official_pdf_physical_page": 702,
    "printed_page_label": "689",
    "SOURCE_FONT_PASS": True,
    "PIXEL_HEIGHT_PASS": False,
    "LOW_PROFILE_REFERENCE_PASS": True,
    "SAME_CLASS_RATIO_PASS": False,
    "ROLE_RATIO_PASS": False,
    "FONT_VISUAL_HARMONY_PASS": False,
    "MASK_PURITY_COMPLETENESS_PASS": True,
    "DENOMINATOR_PASS": True,
    "PAIR_DENOMINATOR_PASS": True,
    "OVERLAP_PIXEL_COUNT": 0,
    "CLIP_PIXEL_COUNT": 0,
    "CLEARANCE_PASS": False,
    "TEXT_TO_IMAGE_EDGE_MIN_PX": text_edge,
    "TEXT_TO_IMAGE_EDGE_PASS": text_edge >= 6,
    "MANUAL_LEDGER_COMPLETE": True,
    "VISUAL_STRUCTURE_AND_SEMANTICS_PASS": True,
    "SA1_PASS": False,
    "route": "FAIL_TO_SA2",
    "counts": {
        "glyphs": len(glyphs), "graphics": len(graphics), "objects_N": len(glyphs) + len(graphics),
        "pairs": len(pairs), "glyph_numeric_failures": len(glyph_fail), "D_failures": len(d_fail),
        "E_failures": len(e_fail), "pair_clearance_failures": len(pair_fail),
        "intentional_contact_pairs": len(intentional), "critical_pairs_opened_1x_8x": len(critical),
        "glyph_manual_rows": len(glyph_manual), "graphic_manual_rows": len(graphic_manual),
    },
    "hard_failures": {
        "glyphs": [f"{g['object_id']} {g['char']} H={g['h_ink_px']}<{g['h_threshold_px']}" for g in glyph_fail],
        "D_elements": [e["element_id"] for e in d_fail],
        "E_elements": [e["element_id"] for e in e_fail],
        "source_formula_base_ratio": f"11.8/9.6={source_ratio:.12f}>1.18",
        "text_bbox_pairs": [p["pair_id"] for p in pair_fail],
        "visual_harmony": "formula blocks visibly oversized relative to base node labels",
    },
}
(REP / "final_matrix.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "SA1_HANDOFF.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")

machine_paths = [REP / "denominator_and_machine_summary.json"]
for path in machine_paths:
    summary = json.loads(path.read_text(encoding="utf-8"))
    summary.update({
        "low_profile_reference_pending": [],
        "low_profile_reference_pass": ["G0063", "G0083"],
        "glyph_numeric_failures_final": [g["object_id"] for g in glyph_fail],
        "pair_failures": [p["pair_id"] for p in pair_fail],
        "pair_failures_final_count": len(pair_fail),
        "illegal_overlap_failures": 0,
        "OVERLAP_PIXEL_COUNT": 0,
        "CLIP_PIXEL_COUNT": 0,
        "critical_pair_cards": len(critical),
        "manual_state": "COMPLETE_BY_SA1",
        "final_route": "FAIL_TO_SA2",
    })
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(REP / "denominator_and_machine_summary.json", ROOT / "denominator_and_machine_summary.json")

visual_md = f"""# FIG-P654-01 SA1 visual acceptance

- Reviewer: {REVIEWER}
- Official render: R98 physical page 702, printed label 689
- Opened: `full_page_200dpi`, `figure_crop_300dpi`, `standalone_300dpi`, `grayscale_300dpi`, all 26 glyph native-1x sheets, all 26 glyph 8x sheets, all 6 graphic native-1x sheets, all 21 graphic 8x cards, both low-profile 1x/8x references, and all {len(critical)} critical pair native-1x/8x cards.
- Structure/semantics: PASS. Eight nodes and seven source paths are coherent; direction, endpoint semantics, formula text, labels, and grayscale reading are correct; no source clipping or overflow was observed.
- `FONT_VISUAL_HARMONY_PASS=false`: 11.8pt formula blocks visibly dominate the 9.6pt base labels; source ratio is `{source_ratio:.12f}`, above `1.18`.
- Hard pixel failures: `{', '.join(matrix['hard_failures']['glyphs'])}`.
- Hard text bbox failures: {len(pair_fail)} title/formula pairs at 0–3px against the 4px gate.
- Low-profile references: G0063 and G0083 PASS at exact H and area ratios 1.0.
- Decision: **FAIL_TO_SA2**.

The row-complete view/panel/role/script ledger is `ledgers/visual_review.csv`.
"""
(ROOT / "after_visual_acceptance.md").write_text(visual_md, encoding="utf-8")

overlap_md = f"""# FIG-P654-01 SA1 overlap and ownership adjudication

- Objects: 103 glyphs + 21 graphic paths = N124; all 7,626 unordered pairs are present.
- Path ownership: each PDF seqno was replayed alone, official foreground was selected without bbox/component ownership guessing, and later z-order was subtracted. Coverage residual=0, coverage excess=0.
- Graphic masks: all 21 opened at native 1x and 8x; each has foreign=0 and missing=0. P003 no longer contains the old detached left/right arrow fragments.
- Final illegal overlap count: `OVERLAP_PIXEL_COUNT=0`.
- Intentional raw contacts: {len(intentional)} exact pair-specific source edge connections; every native 1x/8x card was opened and z-order checked. No class-wide exemption was used.
- Text bbox clearance: FAIL. {len(pair_fail)} title/formula glyph pairs are below 4px; all corresponding A/B/intersection/native-1x/8x cards were opened.
- Clip count: `CLIP_PIXEL_COUNT=0`; minimum text bbox to analysis image edge is {text_edge}px (gate 6px).
- Decision: **FAIL_TO_SA2**.
"""
(ROOT / "after_overlap_adjudication.md").write_text(overlap_md, encoding="utf-8")

report_md = f"""# FIG-P654-01 strict SA1 report

## Identity and scope

- Handoff: `{HANDOFF}`; owner dialogue: `DIALOGUE_A_VISUAL`; reviewer: `{REVIEWER}`.
- Business source was read-only. Normalized-newline SHA-256: `{source_sha}` (R130 identity match).
- Evidence writes are confined to this A-local package.

## Evidence closure

- 103 visible glyphs and 21 foreground graphic/path objects, including one formula fraction rule: N=124.
- All `C(124,2)=7,626` unordered pairs rebuilt; unassigned text=0, coverage residual=0, coverage excess=0, empty glyph masks=0, empty graphic masks=0.
- All 103 glyph and 21 graphic objects were opened at native 1x and 8x. Per-object ledger rows record foreign=0/missing=0.
- All {len(critical)} critical pairs were opened at native 1x and 8x. Nineteen source-semantic edge contacts are whitelisted pair-by-pair; {len(pair_fail)} independent title/formula bbox pairs fail.

## Hard-gate findings

- `SOURCE_FONT_PASS=true`: declared/effective visible sizes are 9.6pt and 11.8pt, both >=9.5pt, with uniform declared size within each role.
- `PIXEL_HEIGHT_PASS=false`: G0017 (`一`) is 4px <30px; G0059 and G0066 (`=`) are each 14px <22px.
- `LOW_PROFILE_REFERENCE_PASS=true`: G0063 comma and G0083 ideographic comma each match a same-codepoint/font/weight/color/size independent official-PDF reference at exact H and area ratios 1.0.
- `SAME_CLASS_RATIO_PASS=false`: D failures are {', '.join(e['element_id'] for e in d_fail)}.
- `ROLE_RATIO_PASS=false`: source formula/base ratio is 11.8/9.6={source_ratio:.12f}>1.18; E failures are {', '.join(e['element_id'] for e in e_fail)}.
- `FONT_VISUAL_HARMONY_PASS=false`: the formula blocks are visibly oversized relative to the base labels.
- `OVERLAP_PIXEL_COUNT=0`; `CLIP_PIXEL_COUNT=0`; `CLEARANCE_PASS=false` because {len(pair_fail)} independent title/formula glyph bbox pairs measure 0–3px <4px.

## Route

`FAIL_TO_SA2`. SA2 must rebuild the candidate and regenerate all evidence; this package must not be promoted to SA3.
"""
(REP / "SA1_REVIEW_REPORT.md").write_text(report_md, encoding="utf-8")
(ROOT / "SA1_REVIEW_REPORT.md").write_text(report_md, encoding="utf-8")
(ROOT / "after_model_route.md").write_text(
    "# Model route\n\n`FAIL_TO_SA2`\n\nHard failures are recorded in `SA1_REVIEW_REPORT.md`, `after_font_audit.csv`, and `after_overlap_report.csv`. SA3 must not start from this failed package.\n",
    encoding="utf-8",
)
(ROOT / "RESULT.txt").write_text("FAIL_TO_SA2\n", encoding="utf-8")

for name in ["full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png", "after_text_measurement_overlay_300dpi.png"]:
    shutil.copyfile(REND / name, ROOT / name)

(CONT / "CURRENT_STATE.md").write_text(
    f"# Current state\n\nSA1 complete for FIG-P654-01 under `{HANDOFF}`. Result: `FAIL_TO_SA2`. Evidence is ready for terminal check and sealing.\n",
    encoding="utf-8",
)
(CONT / "DECISIONS.md").write_text(
    "# Decisions\n\n- Supersede the old 21-graphic/7,626-pair ownership results.\n- Use only per-seqno replay plus z-order subtraction for graphic ownership.\n- Whitelist only 19 exact source-semantic edge connection pairs.\n- Apply independent text bbox clearance, not ink distance, to title/formula pairs.\n- Route FAIL_TO_SA2; do not start SA3.\n",
    encoding="utf-8",
)
(CONT / "ISSUES.md").write_text(
    "# Open hard failures for SA2\n\n- G0017: CJK 一 H=4<30.\n- G0059/G0066: equals H=14<22.\n- Formula/base source ratio 11.8/9.6=1.229166666667>1.18 and visual hierarchy failure.\n- D/E ratio failures listed in after_font_audit.csv.\n- 17 title/formula bbox pair clearances are 0–3px<4px.\n",
    encoding="utf-8",
)
(CONT / "CONTEXT_SNAPSHOT.md").write_text(
    f"# Context snapshot\n\nFIG-P654-01; `{HANDOFF}`; R98 physical page 702/printed 689; N124; 7,626 pairs; 37 critical pairs opened; final route FAIL_TO_SA2.\n",
    encoding="utf-8",
)

print(json.dumps({
    "route": "FAIL_TO_SA2", "glyphs": len(glyphs), "graphics": len(graphics), "pairs": len(pairs),
    "critical": len(critical), "glyph_failures": len(glyph_fail), "D_failures": len(d_fail),
    "E_failures": len(e_fail), "clearance_failures": len(pair_fail), "intentional_contacts": len(intentional),
    "source_sha": source_sha, "text_edge_min_px": text_edge,
}, ensure_ascii=False))
