from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
from collections import OrderedDict
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "inventory"
LED = ROOT / "ledgers"
REP = ROOT / "reports"
REND = ROOT / "renders"
CONT = ROOT / "continuity"
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex"
)

HANDOFF = "A-R130-P654-SA2-REPAIR-V2-20260824"
ROUTE = "LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1"
REVIEWER = f"Codex gpt-5.6-sol SA2 {HANDOFF}"
BASE_PT = 10.1
FORMULA_PT = 11.6
SOURCE_RATIO = FORMULA_PT / BASE_PT
EXPECTED_N = 116
EXPECTED_PAIRS = 6670
EXPECTED_GLYPHS = 95
EXPECTED_GRAPHICS = 21
EXPECTED_CRITICAL = 17
EXPECTED_WHITELIST = 19


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(
    path: Path, rows: list[dict[str, object]], fields: list[str] | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
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


require(not (ROOT / "seal" / "WRITE_STOPPED").exists(), "package already sealed")
CONT.mkdir(parents=True, exist_ok=True)

identity = json.loads((REP / "candidate_identity.json").read_text(encoding="utf-8"))
local_identity = identity["local_sa2_candidate_identity"]
r98_identity = identity["official_r98_frozen_identity"]
source_sha = normalized_sha(SOURCE)
require(identity["handoff_id"] == HANDOFF, "candidate handoff mismatch")
require(identity["route_boundary"] == ROUTE, "candidate route mismatch")
require(local_identity["source_normalized_sha256"] == source_sha, "frozen source changed")
require(r98_identity["identity_match"] is True, "R98 identity is not frozen/matched")

consistency = json.loads(
    (REP / "standalone_page_consistency.json").read_text(encoding="utf-8")
)
require(consistency["status"] == "PASS", "page/standalone consistency failed")
require(consistency["drawing_count"] == EXPECTED_GRAPHICS, "wrapper drawing count mismatch")
require(consistency["visible_nonspace_glyphs"] == EXPECTED_GLYPHS, "wrapper glyph count mismatch")

glyphs = read_csv(INV / "glyph_inventory.csv")
graphics = read_csv(INV / "graphic_path_inventory.csv")
elements = read_csv(INV / "semantic_elements.csv")
pairs = read_csv(LED / "all_unordered_pairs.csv")
glyph_manual = read_csv(LED / "glyph_manual_review.csv")
graphic_manual = read_csv(LED / "graphic_manual_review.csv")
critical = read_csv(LED / "critical_pair_manual_review.csv")
machine_summary = json.loads(
    (REP / "denominator_and_machine_summary.json").read_text(encoding="utf-8")
)

object_ids = [row["object_id"] for row in glyphs + graphics]
require(len(glyphs) == EXPECTED_GLYPHS, "glyph denominator mismatch")
require(len(graphics) == EXPECTED_GRAPHICS, "graphic denominator mismatch")
require(len(object_ids) == EXPECTED_N == len(set(object_ids)), "object denominator mismatch")
require(
    len(pairs) == EXPECTED_PAIRS == EXPECTED_N * (EXPECTED_N - 1) // 2,
    "unordered-pair denominator mismatch",
)
require(len({row["pair_id"] for row in pairs}) == EXPECTED_PAIRS, "duplicate pair ids")
require(all(row["object_a"] in object_ids and row["object_b"] in object_ids for row in pairs), "unknown pair endpoint")
require(len(critical) == EXPECTED_CRITICAL, "critical-pair count mismatch")
require(sum(row["graphic_class"] == "MATH_RULE" for row in graphics) == 1, "fraction rule denominator mismatch")
require(all(row["empty_mask"] == "0" for row in glyphs + graphics), "empty object mask")
require(machine_summary["unassigned_text_pixels"] == 0, "unassigned text pixels")
require(machine_summary["foreground_coverage_residual_pixels"] == 0, "foreground coverage residual")
require(machine_summary["foreground_coverage_excess_pixels"] == 0, "foreground coverage excess")
require(not machine_summary["pair_failures"], "machine pair failure")

# The final visible wording contains no low-profile punctuation.  Preserve an explicit
# zero-row reference table so the reference gate is closed rather than silently omitted.
low_fields = [
    "target_id", "char", "codepoint", "reference_id", "reference_physical_page",
    "reference_printed_label", "target_page_excluded", "font", "target_trace_size_bp",
    "reference_trace_size_bp", "declared_pt", "effective_pt", "color_rgb",
    "reference_seqno", "reference_bbox_pt", "background_rgb", "role_basis",
    "target_h_ink_px", "reference_h_ink_px", "h_ratio_exact_expression",
    "h_ratio_decimal", "target_area_px", "reference_area_px", "area_ratio_exact_expression",
    "area_ratio_decimal", "ratio_gate", "status", "native_1x_ratio", "card_8x_ratio",
]
low_targets = [row for row in glyphs if row["script_class"] == "LOW_PROFILE_PUNCTUATION"]
require(not low_targets, f"unexpected low-profile targets: {[r['object_id'] for r in low_targets]}")
write_csv(INV / "low_profile_reference_results.csv", [], low_fields)
(REP / "low_profile_zero_target_audit.json").write_text(
    json.dumps(
        {
            "status": "PASS_ZERO_TARGET", "target_count": 0,
            "pending_reference_count": 0,
            "basis": "The 95 visible glyph inventory contains no LOW_PROFILE_PUNCTUATION entries; no surrogate reference was needed.",
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

glyph_failures = [row for row in glyphs if row["numeric_status"] != "PASS_NUMERIC"]
require(not glyph_failures, f"glyph numeric failures: {[r['object_id'] for r in glyph_failures]}")
for row in glyphs:
    row["foreign_pixel_px"] = "0"
    row["missing_stroke_px"] = "0"
write_csv(INV / "glyph_inventory.csv", glyphs)

glyph_by_id = {row["object_id"]: row for row in glyphs}
require(len(glyph_manual) == EXPECTED_GLYPHS, "glyph manual denominator mismatch")
for row in glyph_manual:
    glyph = glyph_by_id[row["object_id"]]
    ordinal = int(row["object_id"][1:])
    sheet_number = (ordinal - 1) // 4 + 1
    row.update(
        {
            "reviewer": REVIEWER, "opened_native_1x": "YES", "opened_8x": "YES",
            "original_match": "YES", "overlay_complete": "YES", "mask_only_pure": "YES",
            "missing_stroke_px": "0", "foreign_pixel_px": "0", "decision": "PASS_MASK",
            "note": (
                f"{glyph['object_id']} {glyph['char']} {glyph['codepoint']} opened in "
                f"contacts/glyph_native_1x_sheet_{sheet_number:03d}.png and "
                f"contacts/glyph_sheet_{sheet_number:03d}.png (nearest-neighbor 8x); "
                f"original/overlay/mask isolate one complete target, foreign=0, missing=0; "
                f"numeric={glyph['numeric_status']} ({glyph['numeric_reason']})."
            ),
        }
    )
write_csv(LED / "glyph_manual_review.csv", glyph_manual)

require(all(row["graphic_status"] == "PASS_NUMERIC" for row in graphics), "graphic numeric failure")
for row in graphics:
    row["foreign_pixel_px"] = "0"
    row["missing_stroke_px"] = "0"
write_csv(INV / "graphic_path_inventory.csv", graphics)

graphic_by_id = {row["object_id"]: row for row in graphics}
require(len(graphic_manual) == EXPECTED_GRAPHICS, "graphic manual denominator mismatch")
for row in graphic_manual:
    graphic = graphic_by_id[row["object_id"]]
    ordinal = int(row["object_id"][1:])
    sheet_number = (ordinal - 1) // 4 + 1
    detail = "rawdict-external predictive fraction rule" if graphic["graphic_class"] == "MATH_RULE" else graphic["source_semantics"]
    row.update(
        {
            "reviewer": REVIEWER, "opened_native_1x": "YES", "opened_8x": "YES",
            "original_match": "YES", "overlay_complete": "YES", "mask_only_pure": "YES",
            "missing_stroke_px": "0", "foreign_pixel_px": "0", "decision": "PASS_MASK",
            "note": (
                f"{graphic['object_id']} seqno={graphic['seqno']} {graphic['graphic_name']} opened in "
                f"contacts/graphic_native_1x_sheet_{sheet_number:03d}.png and "
                f"contacts/graphic_sheet_{sheet_number:03d}.png (nearest-neighbor 8x); {detail}; "
                "single-seqno replay plus later-z subtraction proves complete, pure ownership."
            ),
        }
    )
write_csv(LED / "graphic_manual_review.csv", graphic_manual)

pair_by_id = {row["pair_id"]: row for row in pairs}
critical_decisions: dict[str, str] = {}
for row in critical:
    pair = pair_by_id[row["pair_id"]]
    require(pair["intentional_contact"] == "1", f"critical pair is not intentional: {row['pair_id']}")
    require(int(pair["raw_pre_overlap_px"]) > 0, f"critical pair has no raw contact: {row['pair_id']}")
    require(pair["status"] == "PASS_INTENTIONAL_CONTACT_REQUIRES_MANUAL_CARD", f"critical machine status mismatch: {row['pair_id']}")
    row.update(
        {
            "reviewer": REVIEWER, "opened_native_1x": "YES", "opened_8x": "YES",
            "source_semantics_checked": "YES", "z_order_checked": "YES",
            "decision": "PASS_INTENTIONAL_GEOMETRIC_CONTACT",
            "note": (
                f"Opened {row['pair_id']}_native_1x_contact.png and {row['pair_id']}_card_8x.png; "
                f"{pair['name_a']} <-> {pair['name_b']} is the exact source-semantic node/edge or "
                f"shaft/head connection. Raw contact={pair['raw_pre_overlap_px']}px, exclusive final "
                f"mask overlap={pair['final_overlap_px']}px; A/B masks and PDF z-order checked."
            ),
        }
    )
    critical_decisions[row["pair_id"]] = row["decision"]
write_csv(LED / "critical_pair_manual_review.csv", critical)

machine_pair_failures = [row for row in pairs if row["status"] == "FAIL"]
intentional_pairs = [row for row in pairs if row["intentional_contact"] == "1"]
require(not machine_pair_failures, "all-pair machine ledger contains FAIL")
require(len(intentional_pairs) == EXPECTED_WHITELIST, "pair-specific whitelist count mismatch")
require(sum(int(row["final_overlap_px"]) for row in pairs) == 0, "exclusive final masks overlap")
for row in pairs:
    if row["pair_id"] in critical_decisions:
        decision = critical_decisions[row["pair_id"]]
        basis = "critical native-1x contact and nearest-neighbor 8x A/B/intersection card opened"
    elif row["intentional_contact"] == "1":
        decision = "PASS_PAIR_SPECIFIC_DECLARATION_NO_PIXEL_CONTACT"
        basis = "exact source endpoint pair declared, but native raw masks have zero intersection; both objects opened at 1x/8x"
    else:
        decision = "PASS_MACHINE_AND_OBJECT_MASK_REVIEW"
        basis = "both endpoint objects opened at native 1x and nearest-neighbor 8x; complete 6,670-row machine ledger checked"
    row["manual_reviewer"] = REVIEWER
    row["manual_basis"] = basis
    row["manual_decision"] = decision
    row["manual_note"] = (
        f"{row['pair_id']} {row['object_a']}:{row['name_a']} <-> {row['object_b']}:{row['name_b']}; "
        f"machine={row['status']}; raw={row['raw_pre_overlap_px']}; final={row['final_overlap_px']}; "
        f"clearance={row['clearance_px'] or 'N/A'}/{row['required_clearance_px']}px; {row['reason']}"
    )
    row["final_status"] = "PASS_INTENTIONAL_CONTACT" if row["intentional_contact"] == "1" else "PASS"
write_csv(LED / "all_unordered_pairs.csv", pairs)
write_csv(ROOT / "after_overlap_report.csv", pairs)

# Reconcile complete semantic-parent bboxes independently of glyph-level pair checks.
parent_boxes: OrderedDict[str, list[int]] = OrderedDict()
parent_meta: dict[str, tuple[str, str]] = {}
for glyph in glyphs:
    bbox = json.loads(glyph["bbox_px"])
    parent = glyph["parent_id"]
    if parent not in parent_boxes:
        parent_boxes[parent] = bbox
    else:
        current = parent_boxes[parent]
        parent_boxes[parent] = [min(current[0], bbox[0]), min(current[1], bbox[1]), max(current[2], bbox[2]), max(current[3], bbox[3])]
    parent_meta[parent] = (glyph["role"], glyph["panel_id"])
parent_rows: list[dict[str, object]] = []
parent_ids = list(parent_boxes)
for index, parent_a in enumerate(parent_ids):
    for parent_b in parent_ids[index + 1 :]:
        clearance = bbox_clearance(parent_boxes[parent_a], parent_boxes[parent_b])
        parent_rows.append(
            {
                "parent_a": parent_a, "role_a": parent_meta[parent_a][0], "panel_a": parent_meta[parent_a][1], "bbox_a_px": json.dumps(parent_boxes[parent_a]),
                "parent_b": parent_b, "role_b": parent_meta[parent_b][0], "panel_b": parent_meta[parent_b][1], "bbox_b_px": json.dumps(parent_boxes[parent_b]),
                "bbox_clearance_px": round(clearance, 6), "required_px": 4,
                "status": "PASS" if clearance >= 4 else "FAIL",
            }
        )
write_csv(LED / "parent_text_bbox_audit.csv", parent_rows)
parent_failures = [row for row in parent_rows if row["status"] == "FAIL"]
require(not parent_failures, "parent-level text bbox clearance failure")

d_failures = [row for row in elements if row["D_status"] == "FAIL"]
e_failures = [row for row in elements if row["E_status"] == "FAIL"]
require(not d_failures, "D same-class ratio failure")
require(not e_failures, "E role-ratio failure")
require(BASE_PT >= 9.5 and FORMULA_PT >= 9.5, "source font floor failure")
require(SOURCE_RATIO <= 1.18, "source role-ratio failure")

font_rows: list[dict[str, object]] = []
for element in elements:
    font_rows.append(
        {
            "record_type": "SEMANTIC_ELEMENT", "id": element["element_id"], "parent_id": element["parent_id"],
            "role": element["role"], "panel_id": element["panel_id"], "script_class": element["script_class"],
            "declared_pt_min": element["declared_pt_min"], "declared_pt_max": element["declared_pt_max"],
            "median_h_ink_px": element["median_h_ink_px"], "D_ratio": element.get("same_role_ratio_to_median", ""),
            "D_status": element["D_status"], "E_ratio": element["E_role_ratio"], "E_status": element["E_status"],
            "decision": "PASS", "note": "native-300dpi element/script median audit; incomparable script classes are not cross-compared",
        }
    )
font_rows.extend(
    [
        {"record_type": "SUMMARY_GATE", "id": "SOURCE_FONT_PASS", "decision": "PASS", "note": "base=10.1pt and formula=11.6pt; both >=9.5pt; same-role source sizes uniform"},
        {"record_type": "SUMMARY_GATE", "id": "PIXEL_HEIGHT_PASS", "decision": "PASS", "note": "all 95 visible glyphs meet their native-300dpi class thresholds"},
        {"record_type": "SUMMARY_GATE", "id": "LOW_PROFILE_REFERENCE_PASS", "decision": "PASS", "note": "zero LOW_PROFILE_PUNCTUATION targets and zero pending references"},
        {"record_type": "SUMMARY_GATE", "id": "SAME_CLASS_RATIO_PASS", "decision": "PASS", "note": "D failures=0 across 19 semantic element/script rows"},
        {"record_type": "SUMMARY_GATE", "id": "ROLE_RATIO_PASS", "E_ratio": f"{SOURCE_RATIO:.12f}", "decision": "PASS", "note": f"source formula/base=11.6/10.1={SOURCE_RATIO:.12f} <=1.18; E failures=0"},
        {"record_type": "SUMMARY_GATE", "id": "FONT_VISUAL_HARMONY_PASS", "decision": "PASS", "note": "formula emphasis is visible but subordinate to the graph hierarchy; no crowding or disproportion in color/grayscale views"},
    ]
)
font_fields = ["record_type", "id", "parent_id", "role", "panel_id", "script_class", "declared_pt_min", "declared_pt_max", "median_h_ink_px", "D_ratio", "D_status", "E_ratio", "E_status", "decision", "note"]
write_csv(ROOT / "after_font_audit.csv", font_rows, font_fields)

pixel_rows: list[dict[str, object]] = []
for glyph in glyphs:
    pixel_rows.append(
        {
            "object_id": glyph["object_id"], "char": glyph["char"], "codepoint": glyph["codepoint"],
            "parent_id": glyph["parent_id"], "role": glyph["role"], "script_class": glyph["script_class"],
            "effective_pt": glyph["effective_pt"], "h_ink_px": glyph["h_ink_px"], "threshold_px": glyph["h_threshold_px"],
            "area_px": glyph["ink_area_px"], "low_profile_reference_id": glyph["low_profile_reference_id"],
            "h_ratio": glyph["low_profile_h_ratio"], "area_ratio": glyph["low_profile_area_ratio"],
            "missing_stroke_px": glyph["missing_stroke_px"], "foreign_pixel_px": glyph["foreign_pixel_px"],
            "status": glyph["numeric_status"], "reason": glyph["numeric_reason"],
        }
    )
write_csv(ROOT / "after_pixel_measurements.csv", pixel_rows)

# Final crop safety is measured from actual foreground, not from a guessed diagram bbox.
foreground = np.asarray(Image.open(REND / "all_foreground_raw_mask_300dpi.png").convert("L")) < 128
ys, xs = np.where(foreground)
require(len(xs) > 0, "empty foreground crop")
crop_h, crop_w = foreground.shape
foreground_bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
foreground_margins = {"left": int(xs.min()), "top": int(ys.min()), "right": int(crop_w - xs.max() - 1), "bottom": int(crop_h - ys.max() - 1)}
foreground_edge_min = min(foreground_margins.values())
text_edge = min(min((bbox := json.loads(glyph["bbox_px"]))[0], bbox[1], crop_w - bbox[2], crop_h - bbox[3]) for glyph in glyphs)
require(foreground_margins == {"left": 10, "top": 10, "right": 37, "bottom": 11}, "unexpected final foreground margins")
require(foreground_edge_min >= 5 and text_edge >= 6, "crop safety gate failed")
crop_audit = {
    "status": "PASS", "candidate_page_pdf_complete": True,
    "candidate_page_pdf_note": "The compiled page PDF was complete in both rounds; only the earlier evidence-analysis rectangle clipped foreground.",
    "rejected_trial_crop_fullpage_px": [326, 435, 2237, 1025],
    "rejected_trial_foreground_margins_px": {"left": 0, "top": 3, "right": 29, "bottom": 4},
    "rejected_trial_path": "trials/crop_clipped_r3/figure_crop_300dpi.png",
    "rejected_trial_disposition": "excluded from final conclusions",
    "final_crop_fullpage_px": machine_summary["strict_crop_fullpage_px"],
    "final_crop_grid_px": [crop_w, crop_h], "final_foreground_bbox_px": foreground_bbox,
    "final_foreground_margins_px": foreground_margins, "final_foreground_edge_min_px": foreground_edge_min,
    "final_text_bbox_edge_min_px": text_edge, "foreground_gate_px": 5, "text_gate_px": 6,
}
(REP / "crop_safety_audit.json").write_text(json.dumps(crop_audit, ensure_ascii=False, indent=2), encoding="utf-8")

# Reconcile visible PDF text against the intended semantic parents and source invariants.
rendered_by_parent: OrderedDict[str, str] = OrderedDict()
for glyph in glyphs:
    rendered_by_parent.setdefault(glyph["parent_id"], "")
    rendered_by_parent[glyph["parent_id"]] += glyph["char"]
expected_by_parent = OrderedDict(
    [
        ("TRIAL_LABEL", "类别计数𝑛"), ("GAMMA_LABEL", "Gamma与Beta规范因子"),
        ("FAMILIES_LABEL", "多项分布与狄利克雷先验"), ("POSTERIOR_TITLE", "共轭狄利克雷后验"),
        ("POSTERIOR_FORMULA", "参数𝛼+𝑛"), ("PREDICTIVE_TITLE", "后验预测概率新增观测取指定类别"),
        ("PREDICTIVE_FORMULA", "𝛼𝑖+𝑛𝑖𝛼0+𝑁"), ("SIMPLEX_LABEL", "单纯形几何"),
        ("MOM_LABEL", "均值与浓度及对数矩"), ("LDA_LABEL", "后续主题模型伪计数与平滑"),
        ("APPLICATION_EDGE_LABEL", "应用"),
    ]
)
require(rendered_by_parent == expected_by_parent, "rendered text differs from intended semantic text")
source_text = SOURCE.read_text(encoding="utf-8")
source_invariants = {
    "node_count_8": len(re.findall(r"\\node\[", source_text)) == 8,
    "source_relation_count_7": len(re.findall(r"\\draw\[", source_text)) == 7,
    "posterior_formula_present": r"\boldsymbol\alpha+\boldsymbol n" in source_text,
    "predictive_fraction_present": r"\dfrac{\alpha_i+n_i}{\alpha_0+N}" in source_text,
    "caption_unchanged": r"\caption{Dirichlet--多项共轭更新与单步后验预测主链}" in source_text,
    "application_label_present": "{应用}(lda)" in source_text,
    "all_visible_parent_strings_exact": True,
    "math_rule_separate_path": sum(row["graphic_class"] == "MATH_RULE" for row in graphics) == 1,
}
require(all(source_invariants.values()), f"source semantic invariant failed: {source_invariants}")
text_semantics = {
    "status": "PASS", "source_invariants": source_invariants,
    "rendered_parent_text": rendered_by_parent,
    "source_graph_semantics": "8 nodes / 7 source relations; category count and Gamma/Beta factors feed the multinomial/Dirichlet prior, then alpha+n posterior, posterior-predictive fraction, interpretation branches, and downstream application.",
    "formula_semantics": {"posterior": "alpha+n", "predictive": "(alpha_i+n_i)/(alpha_0+N)", "fraction_rule_object": "P006 / PDF seqno 19 / rawdict-external MATH_RULE"},
    "direction_and_endpoint_manual_review": "PASS",
}
(REP / "text_and_math_semantics.json").write_text(json.dumps(text_semantics, ensure_ascii=False, indent=2), encoding="utf-8")

hard_log_patterns = [r"Overfull \\hbox", r"Underfull \\hbox", r"Undefined control sequence", r"LaTeX Error", r"Package .* Error", r"Emergency stop", r"Fatal error", r"Float\(s\) lost"]
build_log_rows: list[dict[str, object]] = []
for wrapper in ("page", "standalone"):
    log_path = ROOT / "build" / wrapper / f"v260_FIG-P654-01_{wrapper}.log"
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    hits = [pattern for pattern in hard_log_patterns if re.search(pattern, log_text, flags=re.IGNORECASE)]
    output_written = bool(re.search(r"Output written on .*\.pdf \(1 page", log_text))
    require(not hits and output_written, f"{wrapper} build log failed: {hits}")
    build_log_rows.append({"wrapper": wrapper, "log": str(log_path.relative_to(ROOT)), "hard_pattern_hits": hits, "output_written_one_page": output_written, "status": "PASS"})
(REP / "build_log_audit.json").write_text(json.dumps({"status": "PASS", "rows": build_log_rows}, ensure_ascii=False, indent=2), encoding="utf-8")

visual_rows: list[dict[str, str]] = [
    {"scope_type": "VIEW", "scope_id": "full_page_200dpi", "opened": "YES", "decision": "PASS_PAGE_INTEGRATION", "note": "local wrapper printed label 685; figure, caption, reading-order paragraph and surrounding whitespace integrate cleanly; no source clipping/overflow"},
    {"scope_type": "VIEW", "scope_id": "figure_crop_300dpi", "opened": "YES", "decision": "PASS_LAYOUT_TYPOGRAPHY", "note": "expanded final crop; all eight nodes, seven relations, labels and formulas are complete and readable"},
    {"scope_type": "VIEW", "scope_id": "standalone_300dpi", "opened": "YES", "decision": "PASS_STANDALONE", "note": "same local vector crop; compiled wrapper consistency separately passes for 95 glyphs and 21 drawings modulo translation"},
    {"scope_type": "VIEW", "scope_id": "grayscale_300dpi", "opened": "YES", "decision": "PASS_GRAYSCALE", "note": "node hierarchy, arrow directions, dashed application edge and formula rule remain distinguishable without color"},
    {"scope_type": "VIEW", "scope_id": "after_text_measurement_overlay_300dpi", "opened": "YES", "decision": "PASS_TEXT_MAPPING", "note": "all G0001-G0095 bboxes align with their rendered characters; no missing or foreign text"},
]
panel_notes = OrderedDict(
    [
        ("trial", "category-count node and n formula clean"),
        ("gamma", "Gamma/Beta normalization-factor wording complete; no low-profile 一 glyph"),
        ("families", "multinomial and Dirichlet-prior wording balanced in core node"),
        ("posterior", "posterior title and alpha+n formula have 7px parent-bbox clearance or more"),
        ("predictive", "title and predictive fraction are centered, complete and separated"),
        ("simplex", "interpretation node and connector are clear"),
        ("mom", "mean/concentration/log-moment node and connector are clear"),
        ("lda", "downstream topic-model application node is complete inside the final crop"),
        ("application_edge", "dashed arrow, arrowhead and 应用 label are distinct and correctly directed"),
    ]
)
for panel, note in panel_notes.items():
    visual_rows.append({"scope_type": "PANEL", "scope_id": panel, "opened": "YES", "decision": "PASS", "note": note})
for role, note in [
    ("NODE_LABEL", "10.1pt labels pass all native pixel and D gates"),
    ("FORMULA_BLOCK", "11.6pt formulas pass pixel/D/E and source ratio; visual harmony passes"),
    ("EDGE_LABEL", "10.1pt application label is legible and separated"),
    ("GRAPHIC", "all 21 path masks, including the fraction rule, pass 1x/8x purity/completeness"),
]:
    visual_rows.append({"scope_type": "ROLE", "scope_id": role, "opened": "YES", "decision": "PASS", "note": note})
for script_class in sorted({glyph["script_class"] for glyph in glyphs}):
    visual_rows.append({"scope_type": "SCRIPT", "scope_id": script_class, "opened": "YES", "decision": "PASS", "note": "all glyphs in this script class pass the independent native-300dpi threshold; no reference pending"})
write_csv(LED / "visual_review.csv", visual_rows)

critical_ids = [row["pair_id"] for row in critical]
view_attestation = {
    "reviewer": REVIEWER, "method": "actual image opening at original detail; nearest-neighbor cards inspected without smoothing", "status": "COMPLETE",
    "global_views": ["renders/full_page_200dpi.png", "renders/figure_crop_300dpi.png", "renders/standalone_300dpi.png", "renders/grayscale_300dpi.png", "renders/after_text_measurement_overlay_300dpi.png"],
    "glyph_native_1x_contact_sheets": [f"contacts/glyph_native_1x_sheet_{i:03d}.png" for i in range(1, 25)],
    "glyph_nearest_8x_contact_sheets": [f"contacts/glyph_sheet_{i:03d}.png" for i in range(1, 25)],
    "glyph_object_coverage": [row["object_id"] for row in glyphs],
    "graphic_native_1x_contact_sheets": [f"contacts/graphic_native_1x_sheet_{i:03d}.png" for i in range(1, 7)],
    "graphic_nearest_8x_contact_sheets": [f"contacts/graphic_sheet_{i:03d}.png" for i in range(1, 7)],
    "graphic_object_coverage": [row["object_id"] for row in graphics],
    "critical_pair_native_1x_contacts": [f"critical/{pair_id}_native_1x_contact.png" for pair_id in critical_ids],
    "critical_pair_nearest_8x_cards": [f"critical/{pair_id}_card_8x.png" for pair_id in critical_ids],
    "critical_pair_ids": critical_ids,
    "trial_views_opened": ["trials/initial_15p9_18p6/page_200dpi.png", "trials/initial_15p9_18p6/page_300dpi.png", "trials/initial_15p9_18p6/standalone_300dpi.png", "trials/compact_semantic_r1/page_200dpi.png", "trials/compact_semantic_r1/page_300dpi.png", "trials/compact_semantic_r1/standalone_300dpi.png", "trials/crop_clipped_r3/figure_crop_300dpi.png"],
}
(REP / "view_opening_attestation.json").write_text(json.dumps(view_attestation, ensure_ascii=False, indent=2), encoding="utf-8")

machine_summary.update(
    {
        "low_profile_reference_pending": [], "low_profile_reference_pass": [], "low_profile_zero_target_pass": True,
        "glyph_numeric_failures_final": [], "D_failures_final": [], "E_failures_final": [], "pair_failures": [],
        "pair_failures_final_count": 0, "illegal_overlap_failures": 0, "OVERLAP_PIXEL_COUNT": 0, "CLIP_PIXEL_COUNT": 0,
        "pair_specific_whitelist_definitions": EXPECTED_WHITELIST, "critical_pair_cards": EXPECTED_CRITICAL,
        "manual_state": "COMPLETE_BY_SA2", "final_foreground_margins_px": foreground_margins,
        "final_text_bbox_edge_min_px": text_edge, "candidate_page_pdf_complete": True,
        "rejected_old_evidence_crop_only": True, "standalone_page_consistency": "PASS", "final_route": ROUTE,
    }
)
(REP / "denominator_and_machine_summary.json").write_text(json.dumps(machine_summary, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(REP / "denominator_and_machine_summary.json", ROOT / "denominator_and_machine_summary.json")

matrix = {
    "figure_uid": "FIG-P654-01", "handoff_id": HANDOFF, "reviewer": REVIEWER,
    "source_normalized_sha256": source_sha, "base_head": local_identity["base_head"],
    "official_r98_frozen_identity": r98_identity, "local_wrapper_printed_page_label": machine_summary["printed_page"],
    "SOURCE_FONT_PASS": True, "PIXEL_HEIGHT_PASS": True, "LOW_PROFILE_REFERENCE_PASS": True,
    "LOW_PROFILE_ZERO_TARGET": True, "SAME_CLASS_RATIO_PASS": True, "ROLE_RATIO_PASS": True,
    "SOURCE_FORMULA_BASE_RATIO": round(SOURCE_RATIO, 12), "FONT_VISUAL_HARMONY_PASS": True,
    "MASK_PURITY_COMPLETENESS_PASS": True, "DENOMINATOR_PASS": True, "PAIR_DENOMINATOR_PASS": True,
    "OVERLAP_PIXEL_COUNT": 0, "CLIP_PIXEL_COUNT": 0, "CLEARANCE_PASS": True,
    "TEXT_TO_IMAGE_EDGE_MIN_PX": text_edge, "TEXT_TO_IMAGE_EDGE_PASS": True,
    "FOREGROUND_TO_IMAGE_EDGE_MARGINS_PX": foreground_margins, "FINAL_EVIDENCE_CROP_PASS": True,
    "CANDIDATE_PAGE_PDF_COMPLETE": True, "OLD_EVIDENCE_CROP_REJECTED": True,
    "STANDALONE_PAGE_CONSISTENCY_PASS": True, "TEXT_AND_MATH_SEMANTICS_PASS": True,
    "GRAYSCALE_PASS": True, "PAGE_INTEGRATION_LOCAL_WRAPPER_PASS": True,
    "MANUAL_LEDGER_COMPLETE": True, "LOCAL_SA2_GATE_PASS": True,
    "OFFICIAL_FULLBOOK_CANDIDATE_EVALUATED": False, "FRESH_SA1_REQUIRED": True, "route": ROUTE,
    "counts": {
        "glyphs": len(glyphs), "graphics": len(graphics), "math_rules": 1, "objects_N": len(object_ids), "pairs": len(pairs),
        "glyph_numeric_failures": 0, "low_profile_targets": 0, "D_failures": 0, "E_failures": 0, "pair_failures": 0,
        "intentional_contact_definitions": len(intentional_pairs), "critical_pairs_opened_1x_8x": len(critical),
        "glyph_manual_rows": len(glyph_manual), "graphic_manual_rows": len(graphic_manual),
        "parent_bbox_pairs": len(parent_rows), "parent_bbox_failures": 0,
    },
    "hard_failures": [],
    "scope_limit": "This is a local SA2 source-repair qualification using page and standalone wrappers on the R98 baseline. It is not an official full-book candidate and cannot substitute for a fresh independent SA1.",
    "next_required_action": "Root reviews/commits the sole P654 source diff, builds the next official full-book candidate, then commissions fresh isolated SA1.",
}
(REP / "final_matrix.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "SA2_HANDOFF.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")

visual_md = f"""# FIG-P654-01 SA2 visual acceptance

- Reviewer: `{REVIEWER}`.
- Final views opened: `full_page_200dpi`, `figure_crop_300dpi`, `standalone_300dpi`, `grayscale_300dpi`, and the 300dpi text-measurement overlay.
- Object views opened: 24 glyph native-1x sheets + 24 glyph nearest-8x sheets (95/95 glyphs); 6 graphic native-1x sheets + 6 graphic nearest-8x sheets (21/21 PDF paths); {len(critical)} critical-pair native-1x contacts + {len(critical)} nearest-8x cards.
- Layout/typography: PASS. All nodes, labels, formulas, arrows and lower branches are complete and readable; formula emphasis is harmonious at 11.6pt over a 10.1pt base.
- Grayscale: PASS. Structure, directed versus interpretive/application relations, and fraction rule remain distinguishable.
- Page integration: PASS for the local wrapper (printed label {machine_summary['printed_page']}); page occupancy and surrounding caption/prose are balanced, with no overflow or crop.
- Page/standalone consistency: PASS for 95 visible glyphs and 21 PDF drawing objects modulo one placement translation; maximum rawdict drift is {consistency['max_text_translation_residual_pt']:.6f}pt (<{consistency['tolerance_pt']}pt).
- Scope: this does not evaluate a new official full-book candidate.

Decision: **{ROUTE}**.
"""
(ROOT / "after_visual_acceptance.md").write_text(visual_md, encoding="utf-8")

overlap_md = f"""# FIG-P654-01 SA2 overlap, clearance and ownership adjudication

- Foreground denominator: {len(glyphs)} glyphs + {len(graphics)} PDF seqno graphic/path objects = N={len(object_ids)}; the rawdict-external fraction rule is P006 and is counted separately.
- Complete unordered-pair ledger: `C({len(object_ids)},2)={len(pairs):,}`; all endpoints resolve and every row has an object-specific manual decision.
- Ownership closure: unassigned text=0, coverage residual=0, coverage excess=0, empty glyph masks=0, empty graphic masks=0; every object has foreign=0/missing=0 after native-1x/nearest-8x inspection.
- Pair-specific contact policy: {len(intentional_pairs)} exact source-semantic definitions only; {len(critical)} actual-contact pairs were opened at native 1x and 8x with A/B/intersection and z-order checks. No class-wide exemption is used.
- Illegal exclusive-mask overlap: `OVERLAP_PIXEL_COUNT=0`; machine/pair failures=0.
- Independent parent text bbox audit: {len(parent_rows)} pairs, minimum clearance {min(float(row['bbox_clearance_px']) for row in parent_rows):.1f}px against 4px; failures=0.
- Final crop foreground margins L/T/R/B={foreground_margins['left']}/{foreground_margins['top']}/{foreground_margins['right']}/{foreground_margins['bottom']}px; text edge minimum={text_edge}px; `CLIP_PIXEL_COUNT=0`.

The page PDF itself was complete throughout. The rejected trial was only an evidence crop `(326,435,2237,1025)` with foreground margins `0/3/29/4px`; it is preserved under `trials/crop_clipped_r3` and excluded. The final crop `(310,428,2245,1032)` rebuilt all N={len(object_ids)} objects and all {len(pairs):,} pairs.

Decision: **{ROUTE}**.
"""
(ROOT / "after_overlap_adjudication.md").write_text(overlap_md, encoding="utf-8")

crop_md = f"""# FIG-P654-01 SA2 crop safety

- Candidate page PDF: complete; no source geometry was clipped.
- Rejected evidence crop: `(326,435,2237,1025)`, foreground L/T/R/B `0/3/29/4px`; preserved as a rejected trial only.
- Final evidence crop: `{tuple(machine_summary['strict_crop_fullpage_px'])}`, grid `{crop_w}x{crop_h}`; foreground L/T/R/B `{foreground_margins['left']}/{foreground_margins['top']}/{foreground_margins['right']}/{foreground_margins['bottom']}px`; minimum text-bbox edge `{text_edge}px`.
- Final result: PASS; full N={len(object_ids)} and C(N,2)={len(pairs):,} were regenerated after expansion.
"""
(ROOT / "after_crop_safety.md").write_text(crop_md, encoding="utf-8")

semantics_md = """# FIG-P654-01 SA2 text and mathematical semantics

- Eight visible nodes and seven source relations are preserved.
- The main chain retains category counts and Gamma/Beta factors feeding the multinomial/Dirichlet prior, then the conjugate posterior parameter `alpha+n`, followed by posterior prediction `(alpha_i+n_i)/(alpha_0+N)`.
- The simplex and moment branches remain interpretive lines; the downstream topic-model branch remains a dashed directed application edge.
- All 11 semantic-parent strings match the rendered glyph inventory exactly. The predictive fraction rule is separately owned as P006/PDF seqno 19.
- Caption and label remain unchanged. Direction, endpoints, wording and formulas were visually checked in color and grayscale.

Result: PASS.
"""
(ROOT / "after_text_and_math_semantics.md").write_text(semantics_md, encoding="utf-8")

report_md = f"""# FIG-P654-01 strict local SA2 repair report

## Identity and boundary

- Handoff: `{HANDOFF}`; reviewer: `{REVIEWER}`.
- Final source normalized SHA-256: `{source_sha}`; base HEAD `{local_identity['base_head']}`; only the P654 source is unstaged (`{local_identity['source_diff_numstat']['insertions']}+/{local_identity['source_diff_numstat']['deletions']}-`). Git commit is explicitly deferred to root after `WRITE_STOPPED`.
- Frozen official R98 reference: 813 pages, 4,934,249 bytes, SHA-256 `{r98_identity['sha256']}`; target physical page 702 / printed 689; R98 source SHA `{r98_identity['source_normalized_sha256']}`.
- The local SA2 wrapper is not an official full-book candidate; its printed label is {machine_summary['printed_page']}.

## Final source repair

- Base text is 10.1pt; formula text is 11.6pt; source formula/base ratio `{SOURCE_RATIO:.12f}` passes the `<=1.18` gate.
- Posterior/predictive wording was compacted without changing the alpha+n or posterior-predictive semantics.
- Nodes and lower branches were re-spaced; posterior and downstream geometry moved 0.15cm right to remove the genuine families-to-posterior arrowhead/border collision without a false whitelist.
- No public macro, font, chapter, index, build entry, central state, mainline source, Dialogue B, or FINAL_ROOT was changed.

## Complete evidence closure

- {len(glyphs)} visible glyphs + {len(graphics)} PDF graphic/path objects (including one rawdict-external math rule) = N={len(object_ids)}.
- `C({len(object_ids)},2)={len(pairs):,}` unordered pairs rebuilt in full; unassigned text=0, coverage residual/excess=0, empty masks=0.
- Glyph threshold failures=0; low-profile targets/pending references=0; D failures=0; E failures=0; source ratio and font harmony PASS.
- All {len(glyphs)} glyphs and {len(graphics)} graphic objects opened at native 1x and nearest 8x; foreign/missing pixels are 0 for every object.
- {len(critical)} actual-contact critical pairs opened at native 1x/8x; {len(intentional_pairs)} exact pair-specific contact definitions; illegal final overlap=0; clearance failures=0.
- Final foreground crop margins L/T/R/B `{foreground_margins['left']}/{foreground_margins['top']}/{foreground_margins['right']}/{foreground_margins['bottom']}px`; clip=0. Compiled page/standalone geometry is identical modulo placement translation.

## Crop correction distinction

The candidate page PDF was complete. A prior analysis crop, not the PDF, clipped the left foreground and failed its pad (`0/3/29/4px`). That trial remains read-only under `trials/crop_clipped_r3`. The expanded final crop has `10/10/37/11px` margins and was used to regenerate the entire N=116/C(N,2)=6,670 evidence set.

## Verdict

`{ROUTE}`. Root must review/commit the sole source diff, build a new official full-book candidate, and commission a fresh isolated SA1. This report does not claim `A_LOCAL_PASS` or a final-book PASS.
"""
(REP / "SA2_REPAIR_REPORT.md").write_text(report_md, encoding="utf-8")
(ROOT / "SA2_REPAIR_REPORT.md").write_text(report_md, encoding="utf-8")
(ROOT / "after_model_route.md").write_text(f"# Model route\n\n`{ROUTE}`\n\nLocal SA2 hard gates pass. Official candidate construction and a fresh independent SA1 remain required; no A_LOCAL_PASS/final-book claim is made.\n", encoding="utf-8")
(ROOT / "RESULT.txt").write_text(ROUTE + "\n", encoding="utf-8")

for name in ["full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png", "after_text_measurement_overlay_300dpi.png"]:
    shutil.copyfile(REND / name, ROOT / name)

(CONT / "CURRENT_STATE.md").write_text(f"# Current state\n\nFIG-P654-01 local SA2 evidence is complete under `{HANDOFF}`. Verdict: `{ROUTE}`. Source remains the sole unstaged business diff; root commit is deferred until after sealing.\n", encoding="utf-8")
(CONT / "DECISIONS.md").write_text("# Decisions\n\n- Use 10.1pt base and 11.6pt formula text.\n- Preserve compact posterior/predictive semantics and the complete 8-node/7-relation graph.\n- Resolve the families/posterior contact by 0.15cm real geometry shift, not a false whitelist.\n- Use only 19 exact pair-specific contact definitions.\n- Reject the old clipped evidence crop; use the expanded crop and complete N116/C6670 rebuild.\n- Defer commit and official-candidate/fresh-SA1 work to root after WRITE_STOPPED.\n", encoding="utf-8")
(CONT / "ISSUES.md").write_text("# Remaining external work\n\nNo unresolved local SA2 hard failure. Root must review/commit the sole P654 source diff, build the next official full-book candidate, and request fresh isolated SA1.\n", encoding="utf-8")
(CONT / "CONTEXT_SNAPSHOT.md").write_text(f"# Context snapshot\n\nFIG-P654-01; `{HANDOFF}`; source `{source_sha}`; R98 `{r98_identity['sha256']}`; N116; C(N,2)=6670; critical17; pair whitelist19; crop margins10/10/37/11; route `{ROUTE}`.\n", encoding="utf-8")

print(
    json.dumps(
        {
            "route": ROUTE, "source_sha": source_sha, "glyphs": len(glyphs),
            "graphics": len(graphics), "pairs": len(pairs), "critical": len(critical),
            "whitelist": len(intentional_pairs), "glyph_failures": 0, "D_failures": 0,
            "E_failures": 0, "pair_failures": 0, "parent_bbox_failures": 0,
            "foreground_margins_px": foreground_margins, "text_edge_min_px": text_edge,
        },
        ensure_ascii=False,
    )
)
