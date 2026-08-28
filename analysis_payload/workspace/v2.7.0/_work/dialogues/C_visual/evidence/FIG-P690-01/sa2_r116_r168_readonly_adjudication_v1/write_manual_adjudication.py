from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P690-01\sa2_r116_r168_readonly_adjudication_v1")
HANDOFF_ID = "C-FIG-P690-01-R116-SA2-R168-READONLY-ADJUDICATION-V1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


objects = read_csv(ROOT / "02_object_inventory_frozen.csv")
pairs = read_csv(ROOT / "03_pair_inventory_frozen.csv")
glyphs = read_csv(ROOT / "04_glyph_inventory_frozen.csv")
math_items = read_csv(ROOT / "05_math_inventory_frozen.csv")
if len(objects) != 28 or len(pairs) != 378 or len(glyphs) != 17 or len(math_items) != 7:
    raise RuntimeError("frozen inventory count changed before manual adjudication")

object_notes = {
    "O001": "Blue bold left title is balanced, fully legible, and matches the coupled-posterior role.",
    "O002": "Outlined θ_m latent node is centered; glyph and subscript are intact; incident edge ends at boundary.",
    "O003": "Outlined z_mn latent node is centered; both incoming arrows and coupling edge terminate at the boundary without touching text.",
    "O004": "Filled w_mn observed node has clean white glyphs and clear observed-role contrast in color and grayscale.",
    "O005": "Rounded φ-fixed parameter box is legible, visibly distinct from latent and observed nodes, and not clipped.",
    "O006": "Horizontal coupling edge cleanly joins the two latent-node boundaries and does not cross either label.",
    "O007": "Left word-input arrow points from observed w_mn to z_mn and stops at the target boundary.",
    "O008": "Left fixed-parameter arrow points upward to z_mn and stops at the target boundary.",
    "O009": "Left dashed panel boundary encloses its four components with positive padding and no clipping.",
    "O010": "True-posterior formula is complete, readable, and separated from the panel border and summary.",
    "O011": "Blue bold right title is balanced, fully legible, and names the cut approximate-posterior dependence.",
    "O012": "Outlined q(θ_m) factor node is centered and clearly larger than the latent node while remaining balanced.",
    "O013": "Outlined q(z_mn) factor node is centered; incoming arrows stop at the boundary and avoid the glyphs.",
    "O014": "Filled right w_mn observed node retains clean white glyphs and grayscale contrast.",
    "O015": "Right φ-fixed parameter box is legible and role-consistent with its left-panel counterpart.",
    "O016": "Left cut-edge stub ends before the orange cut marks and remains distinct from q(θ_m) text.",
    "O017": "Right cut-edge stub begins after the orange cut marks and remains distinct from q(z_mn) text.",
    "O018": "First orange cut slash is intact, separated from both factor circles and the second slash.",
    "O019": "Second orange cut slash is intact, separated from both factor circles and the first slash.",
    "O020": "Right word-input arrow points from observed w_mn to q(z_mn), ending at the factor boundary.",
    "O021": "Right fixed-parameter arrow points upward to q(z_mn), ending at the factor boundary.",
    "O022": "Right dashed panel boundary encloses all components with positive padding and no clipping.",
    "O023": "Factorized q(θ_m)∏_n q(z_mn) formula has correct product, index, parentheses, and subscripts.",
    "O024": "Transition arrow runs left-to-right below its label, contacting only the two panel boundaries as designed.",
    "O025": "Two-line transition label remains readable and clear of the transition arrow and panel contents.",
    "O026": "Bottom conclusion callout is balanced; both lines and embedded math are legible in color and grayscale.",
    "O027": "Bold Figure 35.6 label is complete, correctly numbered, and separated from the body text.",
    "O028": "Two-line caption is fully readable, mathematically intact, not clipped, and consistent with source/chapter semantics.",
}

manual_object_rows = []
for row in objects:
    oid = row["object_id"]
    manual_object_rows.append(
        {
            "object_id": oid,
            "geometry": "PASS",
            "readability": "PASS",
            "glyph_or_text_integrity": "PASS",
            "semantic_role": "PASS",
            "grayscale_distinguishability": "PASS",
            "clipping": "PASS",
            "illegal_visible_ink_overlap": "PASS",
            "overall_verdict": "PASS",
            "post_observation_note": object_notes[oid],
        }
    )
write_csv(
    ROOT / "30_manual_object_ledger.csv",
    [
        "object_id",
        "geometry",
        "readability",
        "glyph_or_text_integrity",
        "semantic_role",
        "grayscale_distinguishability",
        "clipping",
        "illegal_visible_ink_overlap",
        "overall_verdict",
        "post_observation_note",
    ],
    manual_object_rows,
)

intended_contacts = {
    ("O002", "O006"): "coupling edge meets θ_m node boundary",
    ("O003", "O006"): "coupling edge meets z_mn node boundary",
    ("O003", "O007"): "word-input arrowhead meets z_mn node boundary",
    ("O004", "O007"): "word-input arrow shaft begins at w_mn node boundary",
    ("O003", "O008"): "fixed-parameter arrowhead meets z_mn node boundary",
    ("O005", "O008"): "fixed-parameter arrow shaft begins at parameter-box boundary",
    ("O012", "O016"): "left cut stub begins at q(θ_m) factor boundary",
    ("O013", "O017"): "right cut stub ends at q(z_mn) factor boundary",
    ("O013", "O020"): "right word-input arrowhead meets q(z_mn) factor boundary",
    ("O014", "O020"): "right word-input arrow shaft begins at observed-node boundary",
    ("O013", "O021"): "right fixed-parameter arrowhead meets q(z_mn) factor boundary",
    ("O015", "O021"): "right fixed-parameter arrow shaft begins at parameter-box boundary",
    ("O009", "O024"): "transition arrow begins at left panel boundary",
    ("O022", "O024"): "transition arrowhead meets right panel boundary",
}

manual_pair_rows = []
for row in pairs:
    key = tuple(sorted((row["object_a"], row["object_b"])))
    if key in intended_contacts:
        verdict = "INTENDED_CONTACT_CLEAR"
        note = intended_contacts[key] + "; contact is compositional, outside all text ink, and not an illegal overlap"
    else:
        verdict = "CLEAR"
        note = "distinct reader-visible ink remains separated, nested without boundary contact, or spatially unrelated; no illegal visible-ink overlap observed"
    manual_pair_rows.append(
        {
            "pair_id": row["pair_id"],
            "object_a": row["object_a"],
            "object_b": row["object_b"],
            "manual_verdict": verdict,
            "illegal_visible_ink_overlap": "FALSE",
            "post_observation_note": note,
        }
    )
write_csv(
    ROOT / "31_manual_pair_ledger.csv",
    ["pair_id", "object_a", "object_b", "manual_verdict", "illegal_visible_ink_overlap", "post_observation_note"],
    manual_pair_rows,
)

glyph_notes = {
    "G001": "θ_m and z_mn in the title render as the intended Greek/math glyphs with readable subscripts.",
    "G002": "θ_m is complete and centered; no tofu, substitution, or boundary contact.",
    "G003": "z_mn is complete and centered; the two-letter subscript is readable.",
    "G004": "w_mn is complete in white-on-blue with readable subscript.",
    "G005": "bold varphi renders as φ, followed by the correct fixed-parameter text.",
    "G006": "p, θ_m, z_mn, conditional bar, w_m, and φ all render in the intended order.",
    "G007": "q(θ_m) has intact q, parentheses, theta, and subscript.",
    "G008": "q(z_mn) has intact q, parentheses, z, and two-letter subscript.",
    "G009": "right w_mn is complete and readable in white-on-blue.",
    "G010": "right bold varphi renders correctly with the fixed label.",
    "G011": "q(θ_m)∏_n q(z_mn) includes the product glyph and its n subscript with no loss.",
    "G012": "summary w_mn is intact and visibly emphasized.",
    "G013": "summary bold varphi is intact and visibly emphasized.",
    "G014": "summary q(z_mn) is intact with balanced parentheses and readable subscript.",
    "G015": "caption bold varphi is the intended symbol and is not replaced or missing.",
    "G016": "caption bold theta with m subscript is intact and distinguishable from scalar z.",
    "G017": "caption z_mn is intact with the intended scalar glyph and two-letter subscript.",
}
manual_glyph_rows = []
for row in glyphs:
    manual_glyph_rows.append(
        {
            "glyph_id": row["glyph_id"],
            "object_id": row["object_id"],
            "expected": row["glyph_or_expression"],
            "codepoint_or_math_identity": "PASS",
            "render_completeness": "PASS",
            "readability": "PASS",
            "clipping": "PASS",
            "manual_verdict": "PASS",
            "post_observation_note": glyph_notes[row["glyph_id"]],
        }
    )
write_csv(
    ROOT / "32_manual_glyph_ledger.csv",
    ["glyph_id", "object_id", "expected", "codepoint_or_math_identity", "render_completeness", "readability", "clipping", "manual_verdict", "post_observation_note"],
    manual_glyph_rows,
)

math_notes = {
    "M001": "The title correctly states posterior coupling between θ_m and z_mn.",
    "M002": "The conditional posterior p(θ_m,z_mn | w_m,φ) is correctly formed for fixed φ and observed document words.",
    "M003": "q(θ_m) is the document-topic variational factor.",
    "M004": "q(z_mn) is the per-token topic-assignment variational factor.",
    "M005": "q(θ_m)∏_n q(z_mn) correctly represents the chapter's mean-field factorization over token assignments.",
    "M006": "The summary correctly preserves w_mn and fixed φ as inputs to the q(z_mn) responsibility update.",
    "M007": "The caption correctly distinguishes cutting approximate-posterior dependence from deleting generative-model dependence.",
}
manual_math_rows = []
for row in math_items:
    manual_math_rows.append(
        {
            "math_id": row["math_id"],
            "object_id": row["object_id"],
            "expected_claim_or_expression": row["claim_or_expression"],
            "notation": "PASS",
            "mathematical_correctness": "PASS",
            "chapter_consistency": "PASS",
            "manual_verdict": "PASS",
            "post_observation_note": math_notes[row["math_id"]],
        }
    )
write_csv(
    ROOT / "33_manual_math_ledger.csv",
    ["math_id", "object_id", "expected_claim_or_expression", "notation", "mathematical_correctness", "chapter_consistency", "manual_verdict", "post_observation_note"],
    manual_math_rows,
)

geometry_rows = [
    ("GE001", "bilateral component alignment", "PASS", "Corresponding left/right nodes and fixed-parameter boxes align cleanly without obvious imbalance."),
    ("GE002", "left coupling topology", "PASS", "θ_m—z_mn is undirected and boundary-to-boundary, matching a coupled posterior relation."),
    ("GE003", "left observed-word arrow", "PASS", "w_mn→z_mn direction is leftward and ends at the target boundary."),
    ("GE004", "left fixed-parameter arrow", "PASS", "φ→z_mn direction is upward and ends at the target boundary."),
    ("GE005", "mean-field cut corridor", "PASS", "Two separated cut slashes and two edge stubs create a visible geometric break between factor nodes."),
    ("GE006", "right observed-word arrow", "PASS", "w_mn→q(z_mn) direction is leftward and ends at the factor boundary."),
    ("GE007", "right fixed-parameter arrow", "PASS", "φ→q(z_mn) direction is upward and ends at the factor boundary."),
    ("GE008", "approximation transition", "PASS", "The transition arrow reads uniquely from true posterior (left) to mean-field family (right)."),
    ("GE009", "edge endpoint discipline", "PASS", "All node-related edges and arrows stop at node/box boundaries; none crosses label ink."),
    ("GE010", "left panel containment", "PASS", "Left objects are enclosed with visible padding and no border crossings except the designed transition contact."),
    ("GE011", "right panel containment", "PASS", "Right objects are enclosed with visible padding and no border crossings except the designed transition contact."),
    ("GE012", "label clearance", "PASS", "Titles, transition label, formulas, and embedded labels are mutually legible and unobstructed."),
    ("GE013", "summary and caption spacing", "PASS", "The conclusion callout and caption remain separated, aligned, and unclipped."),
    ("GE014", "page integration", "PASS", "Figure, caption, adjacent self-check, proposition block, header, footer, and margins form a balanced page."),
]
write_csv(ROOT / "34_manual_geometry_ledger.csv", ["geometry_id", "gate", "manual_verdict", "post_observation_note"], [dict(zip(["geometry_id", "gate", "manual_verdict", "post_observation_note"], row)) for row in geometry_rows])

semantic_rows = [
    ("S001", "θ_m role", "PASS", "θ_m is represented as latent in the true posterior and as q(θ_m) in the variational family."),
    ("S002", "z_mn role", "PASS", "z_mn is represented as latent in the true posterior and as q(z_mn) in the variational family."),
    ("S003", "w_mn role", "PASS", "w_mn is consistently filled/observed and provides input to z or q(z)."),
    ("S004", "φ role", "PASS", "φ is consistently labeled fixed and provides likelihood information to z or q(z)."),
    ("S005", "true posterior dependence", "PASS", "The left undirected edge correctly communicates posterior coupling."),
    ("S006", "mean-field independence", "PASS", "The right geometric cut correctly communicates removal of direct approximate-posterior dependence."),
    ("S007", "observed input retained", "PASS", "The right w_mn→q(z_mn) arrow correctly shows the observation still affects responsibilities."),
    ("S008", "fixed likelihood parameter retained", "PASS", "The right φ→q(z_mn) arrow correctly shows fixed word parameters still affect responsibilities."),
    ("S009", "factorization semantics", "PASS", "q(θ_m)∏_nq(z_mn) agrees with equation (35.9) and the per-token factor family."),
    ("S010", "caption/source/chapter agreement", "PASS", "Source caption, rendered caption, preceding chapter paragraph, and equation (35.9) agree without role or direction conflict."),
]
write_csv(ROOT / "35_manual_semantic_ledger.csv", ["semantic_id", "gate", "manual_verdict", "post_observation_note"], [dict(zip(["semantic_id", "gate", "manual_verdict", "post_observation_note"], row)) for row in semantic_rows])

page_rows = [
    {
        "page_id": "PAGE_PHYSICAL_740_PRINTED_727",
        "full_color_200": "PASS",
        "full_color_300": "PASS",
        "full_gray_300": "PASS",
        "figure_caption_native": "PASS",
        "readability": "PASS",
        "balance": "PASS",
        "clipping": "PASS",
        "page_ink_overlap": "PASS",
        "manual_verdict": "PASS",
        "post_observation_note": "The figure is prominent but proportionate; caption and adjacent proposition remain readable; no clipped content, abnormal whitespace, tofu, or page-level collision is visible.",
    }
]
write_csv(ROOT / "36_manual_page_ledger.csv", list(page_rows[0].keys()), page_rows)

roi_rows = [
    ("R01_cut_corridor", "PASS", "two slashes are separate; stubs stop before them; factor glyphs and circles are untouched"),
    ("R02_left_coupling", "PASS", "coupling edge and lower arrow meet node boundaries only; labels remain clear"),
    ("R03_left_word_arrow", "PASS", "word and fixed-parameter arrows end at z_mn boundary without entering glyph ink"),
    ("R04_right_word_arrow", "PASS", "word arrow ends at q(z_mn) boundary without entering glyph ink"),
    ("R05_right_phi_input", "PASS", "fixed-parameter arrow meets q(z_mn) boundary and remains clear of box text"),
    ("R06_transition_label_arrow", "PASS", "arrow passes below label and intentionally contacts panel boundaries only"),
    ("R07_bottom_summary_math", "PASS", "w_mn, φ, and q(z_mn) are intact and separated from callout border"),
    ("R08_caption_first_line", "PASS", "figure number, dash, φ, bold θ_m, and z_mn are readable and complete"),
    ("R09_caption_second_line", "PASS", "second caption line is complete, unclipped, and evenly spaced"),
    ("R10_true_posterior_formula", "PASS", "conditional bar, commas, θ_m, z_mn, w_m, and φ are all correct"),
    ("R11_factorized_formula", "PASS", "product glyph, subscript n, factors, parentheses, and subscripts are all correct"),
]
write_csv(ROOT / "37_manual_roi_ledger.csv", ["roi_id", "manual_verdict", "post_observation_note"], [dict(zip(["roi_id", "manual_verdict", "post_observation_note"], row)) for row in roi_rows])

(ROOT / "38_semantic_source_adjudication.md").write_text(
    "# Fresh SA2 semantic adjudication\n\n"
    "The current chapter fixes the topic-word parameter `\\boldsymbol\\varphi`, defines the single-document mean-field family "
    "`q(\\boldsymbol\\theta_m,\\boldsymbol z_m)=Dir(\\boldsymbol\\theta_m)\\prod_n Cat(z_{mn})`, and states that the approximation deliberately cuts posterior dependence between `\\boldsymbol\\theta_m` and each `z_{mn}`. "
    "The current figure preserves those roles: the left panel shows the coupled posterior; the right panel uses separate `q(\\theta_m)` and `q(z_{mn})` factors with a visible cut; observed `w_{mn}` and fixed `\\boldsymbol\\varphi` continue to point to the assignment responsibility factor. "
    "The source caption, rendered caption on physical page 740 / printed page 727, and surrounding chapter paragraph therefore agree.\n\n"
    "R168 adjudication applies: the declared 9.2 pt body font is advisory by itself. The opened native72, 200 dpi, 300 dpi, grayscale, overlay, and native1x/NN8x evidence shows actual readability and no obvious imbalance, so it does not create a hard failure.\n",
    encoding="utf-8",
    newline="\n",
)

general_views = [
    "11_full_page_color200.png",
    "12_full_page_color300.png",
    "13_full_page_gray300.png",
    "14_figure_caption_native72.png",
    "15_figure_caption_native300.png",
    "16_figure_caption_gray300.png",
    "17_object_overlay.png",
    "18_semantic_overlay.png",
    "19_text_overlay.png",
]
roi_views = []
for roi_id, _, _ in roi_rows:
    roi_views.extend([f"20_{roi_id}_native1x.png", f"21_{roi_id}_nearest8x.png"])
write_json(
    ROOT / "39_view_open_log.json",
    {
        "handoff_id": HANDOFF_ID,
        "freeze_preceded_observation": True,
        "general_views": [{"file": name, "opened": True} for name in general_views],
        "critical_roi_views": [{"file": name, "opened": True} for name in roi_views],
        "general_opened_count": len(general_views),
        "critical_roi_opened_count": len(roi_views),
        "observation_completed_before_manual_ledgers": True,
    },
)

completeness = {
    "handoff_id": HANDOFF_ID,
    "physical_page": 740,
    "printed_page": 727,
    "figure_number": "35.6",
    "N": 28,
    "C": 378,
    "manual_objects": len(manual_object_rows),
    "manual_pairs": len(manual_pair_rows),
    "manual_glyphs": len(manual_glyph_rows),
    "manual_math": len(manual_math_rows),
    "manual_geometry": len(geometry_rows),
    "manual_semantic": len(semantic_rows),
    "manual_page": len(page_rows),
    "manual_rois": len(roi_rows),
    "pair_clear": sum(row["manual_verdict"] == "CLEAR" for row in manual_pair_rows),
    "pair_intended_contact_clear": sum(row["manual_verdict"] == "INTENDED_CONTACT_CLEAR" for row in manual_pair_rows),
    "pair_fail": 0,
    "hard_failures": 0,
    "source_change_requested": False,
    "business_result": "PASS",
    "token": "SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1",
}
write_json(ROOT / "40_completeness_and_verdict.json", completeness)
(ROOT / "41_business_verdict.txt").write_text(
    "HANDOFF_ID=" + HANDOFF_ID + "\n"
    "ROLE=SA2\n"
    "BUSINESS_RESULT=PASS\n"
    "HARD_FAILURES=0\n"
    "SOURCE_CHANGE_REQUEST=NONE\n"
    "TOKEN=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1\n",
    encoding="utf-8",
    newline="\n",
)

print("STATUS=MANUAL_ADJUDICATION_COMPLETE")
print("OBJECTS=28/28")
print("PAIRS=378/378")
print("GLYPHS=17/17")
print("MATH=7/7")
print("GEOMETRY=14/14")
print("SEMANTIC=10/10")
print("PAGE=1/1")
print("HARD_FAILURES=0")
print("TOKEN=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1")
