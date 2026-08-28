from __future__ import annotations

import csv
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIGURE_ID = "FIG-P126-01"
HANDOFF_ID = "A-R116-P126-SA1-FRESH-ISOLATED-20260828"
PDF_PAGE = 137


OBJECTS = [
    ("O001", "graphic", "axis", "x-axis", "14-16", "horizontal coordinate axis x_1"),
    ("O002", "graphic", "axis", "y-axis", "14-16", "vertical coordinate axis x_2"),
    ("O003", "graphic", "contour", "outer contour", "20-21", "level-set contour scale 2.70"),
    ("O004", "graphic", "contour", "middle-outer contour", "22-23", "level-set contour scale 2.15"),
    ("O005", "graphic", "contour", "middle-inner contour", "24-25", "level-set contour scale 1.65"),
    ("O006", "graphic", "contour", "inner contour", "26-27", "level-set contour scale 0.90"),
    ("O007", "graphic", "update-arrow-x2", "step 1 arrow q0->q1", "39", "dashed teal vertical update"),
    ("O008", "graphic", "update-arrow-x1", "step 2 arrow q1->q2", "36", "solid blue horizontal update"),
    ("O009", "graphic", "update-arrow-x2", "step 3 arrow q2->q3", "40", "dashed teal vertical update"),
    ("O010", "graphic", "update-arrow-x1", "step 4 arrow q3->q4", "37", "solid blue horizontal update"),
    ("O011", "graphic", "update-arrow-x2", "step 5 arrow q4->q5", "41", "dashed teal vertical update"),
    ("O012", "graphic", "update-arrow-x1", "step 6 arrow q5->q6", "38", "solid blue horizontal update"),
    ("O013", "graphic", "update-arrow-x2", "step 7 arrow q6->q7", "42", "dashed teal vertical update"),
    ("O014", "graphic", "marker-initial", "initial point q0", "43", "black filled circular marker"),
    ("O015", "text", "point-label", "initial label", "44", "x^(0)"),
    ("O016", "text", "step-label", "step label 1", "45", "1"),
    ("O017", "text", "step-label", "step label 2", "46", "2"),
    ("O018", "text", "step-label", "step label 3", "47", "3"),
    ("O019", "text", "step-label", "step label 4", "48", "4"),
    ("O020", "text", "step-label", "step label 5", "49", "5"),
    ("O021", "text", "step-label", "step label 6", "50-52", "6"),
    ("O022", "text", "step-label", "step label 7", "53-55", "7"),
    ("O023", "graphic", "marker-x2", "square marker q1", "56-57", "teal outlined square"),
    ("O024", "graphic", "marker-x2", "square marker q3", "56-57", "teal outlined square"),
    ("O025", "graphic", "marker-x2", "square marker q5", "56-57", "teal outlined square"),
    ("O026", "graphic", "marker-x2", "square marker q7", "56-57", "teal outlined square"),
    ("O027", "graphic", "marker-x1", "circle marker q2", "58", "blue filled circle"),
    ("O028", "graphic", "marker-x1", "circle marker q4", "59", "blue filled circle"),
    ("O029", "graphic", "marker-x1", "circle marker q6", "60", "blue filled circle"),
    ("O030", "graphic", "marker-optimum", "optimum star", "61-62", "gold five-point star at origin"),
    ("O031", "text", "point-label", "optimum label", "63-64", "x*"),
    ("O032", "text", "axis-label", "x1 axis label", "16", "x_1"),
    ("O033", "text", "axis-label", "x2 axis label", "16", "x_2"),
    ("O034", "graphic", "legend-key", "legend x1 sample", "65", "solid blue line sample"),
    ("O035", "text", "legend-label", "legend x1 text", "66", "更新 x_1"),
    ("O036", "graphic", "legend-key", "legend x2 sample", "67-72", "disconnected teal line sample"),
    ("O037", "text", "legend-label", "legend x2 text", "73", "更新 x_2"),
    ("O038", "text", "caption", "numbered figure caption", "76", "坐标下降的每个子步只改变一个坐标，因此轨迹沿轴向折线逼近最优点。"),
]


GLYPHS = {
    "O015": "x⁽⁰⁾",
    "O016": "1",
    "O017": "2",
    "O018": "3",
    "O019": "4",
    "O020": "5",
    "O021": "6",
    "O022": "7",
    "O031": "x*",
    "O032": "x₁",
    "O033": "x₂",
    "O035": "更新 x₁",
    "O037": "更新 x₂",
    "O038": "坐标下降的每个子步只改变一个坐标，因此轨迹沿轴向折线逼近最优点。",
}


MATH_CHECKS = [
    ("M001", "O032", "$x_1$", "horizontal axis denotes coordinate 1"),
    ("M002", "O033", "$x_2$", "vertical axis denotes coordinate 2"),
    ("M003", "O015", "$x^{(0)}$", "initial iterate label has superscript zero"),
    ("M004", "O031", "$x^*$", "optimum label carries a star superscript"),
    ("M005", "O035", "更新 $x_1$", "solid-blue legend role"),
    ("M006", "O037", "更新 $x_2$", "dashed-teal legend role"),
    ("M007", "O003-O006", "x=r(cos(t)-sin(t)), y=r sin(t)", "nested rotated elliptical level sets centered at origin"),
]


GEOMETRY_CHECKS = [
    ("G001", "coordinate frame", "O001,O002", "axes cross at the optimum origin"),
    ("G002", "contour nesting", "O003-O006", "four centered, similarly oriented nested contours"),
    ("G003", "step 1", "O007,O014,O023", "q0=(-3.20,2.20) to q1=(-3.20,1.60): x1 fixed"),
    ("G004", "step 2", "O008,O023,O027", "q1 to q2=(-1.60,1.60): x2 fixed"),
    ("G005", "step 3", "O009,O027,O024", "q2 to q3=(-1.60,0.80): x1 fixed"),
    ("G006", "step 4", "O010,O024,O028", "q3 to q4=(-0.80,0.80): x2 fixed"),
    ("G007", "step 5", "O011,O028,O025", "q4 to q5=(-0.80,0.40): x1 fixed"),
    ("G008", "step 6", "O012,O025,O029", "q5 to q6=(-0.40,0.40): x2 fixed"),
    ("G009", "step 7", "O013,O029,O026", "q6 to q7=(-0.40,0.20): x1 fixed"),
    ("G010", "trajectory convergence", "O007-O013,O030", "alternating axis-aligned path approaches the origin"),
    ("G011", "label attachment", "O015-O022,O031", "labels identify their intended point/step without ambiguity"),
    ("G012", "legend mapping", "O034-O037", "legend samples match the two update encodings"),
    ("G013", "figure bounds", "O001-O037", "no target object is clipped by figure/page bounds"),
    ("G014", "caption placement", "O038", "caption remains attached to target figure and does not collide"),
]


SEMANTIC_CHECKS = [
    ("S001", "coordinate descent", "each substep changes exactly one coordinate"),
    ("S002", "update order", "steps 1,3,5,7 change x2; steps 2,4,6 change x1"),
    ("S003", "encoding", "solid blue means update x1; dashed teal means update x2"),
    ("S004", "iteration", "x^(0) is the initial iterate and labels 1-7 give path order"),
    ("S005", "optimum", "x* at the contour center is the intended optimum"),
    ("S006", "convergence", "the axis-aligned path moves toward x*"),
    ("S007", "contours", "nested rotated ellipses represent a coordinate-misaligned objective"),
    ("S008", "caption consistency", "caption matches the visible trajectory"),
    ("S009", "body consistency", "the visible zigzag supports the adjacent diagnosis of coordinate mismatch"),
    ("S010", "reading order", "initial point, numbered arrows, optimum, and legend form an unambiguous path"),
]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def codepoints(text: str) -> str:
    return " ".join(f"U+{ord(ch):04X}" for ch in text)


def main() -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat()
    object_rows = [
        {
            "object_id": oid,
            "kind": kind,
            "role": role,
            "source_name": name,
            "source_lines": lines,
            "expected_visible_semantics": expected,
            "scope": "target figure including generated caption",
        }
        for oid, kind, role, name, lines, expected in OBJECTS
    ]
    write_csv(
        ROOT / "machine_object_denominator.csv",
        list(object_rows[0]),
        object_rows,
    )

    pair_rows = []
    for index, (a, b) in enumerate(itertools.combinations([row[0] for row in OBJECTS], 2), 1):
        pair_rows.append(
            {
                "pair_id": f"PAIR-{index:04d}",
                "object_a": a,
                "object_b": b,
                "acceptance_question": "illegal visible-ink overlap, severe ambiguity, or true clipping?",
            }
        )
    write_csv(ROOT / "machine_unordered_pairs.csv", list(pair_rows[0]), pair_rows)

    object_manual_rows = []
    for row in object_rows:
        object_manual_rows.append(
            {
                "object_id": row["object_id"],
                "full_page_opened": "",
                "native_opened": "",
                "gray_opened": "",
                "overlay_opened": "",
                "native1x_opened": "",
                "nearest8x_opened": "",
                "present": "",
                "correct_glyph_or_shape": "",
                "readable_balanced": "",
                "not_clipped": "",
                "no_illegal_visible_ink_overlap": "",
                "math_geometry_semantics_correct": "",
                "manual_result": "",
                "manual_notes": "",
            }
        )
    write_csv(ROOT / "manual_object_ledger.csv", list(object_manual_rows[0]), object_manual_rows)

    pair_manual_rows = []
    for pair in pair_rows:
        pair_manual_rows.append(
            {
                "pair_id": pair["pair_id"],
                "object_a": pair["object_a"],
                "object_b": pair["object_b"],
                "critical_roi_id": "",
                "native1x_opened": "",
                "nearest8x_opened": "",
                "spatial_relation": "",
                "visible_ink_overlap_class": "",
                "clipping_or_ambiguity": "",
                "manual_result": "",
                "manual_notes": "",
            }
        )
    write_csv(ROOT / "manual_pair_ledger.csv", list(pair_manual_rows[0]), pair_manual_rows)

    glyph_rows = []
    for oid, text in GLYPHS.items():
        glyph_rows.append(
            {
                "glyph_check_id": f"GL-{len(glyph_rows)+1:03d}",
                "object_id": oid,
                "expected_unicode": text,
                "expected_codepoints": codepoints(text),
                "native1x_opened": "",
                "nearest8x_opened": "",
                "observed_glyphs": "",
                "missing_tofu_wrong_codepoint": "",
                "manual_result": "",
                "manual_notes": "",
            }
        )
    write_csv(ROOT / "manual_glyph_codepoint_ledger.csv", list(glyph_rows[0]), glyph_rows)

    math_rows = [
        {
            "math_check_id": mid,
            "object_ids": objects,
            "expected_math": expected,
            "semantic_role": role,
            "native1x_opened": "",
            "nearest8x_opened": "",
            "observed_math": "",
            "manual_result": "",
            "manual_notes": "",
        }
        for mid, objects, expected, role in MATH_CHECKS
    ]
    write_csv(ROOT / "manual_math_ledger.csv", list(math_rows[0]), math_rows)

    geometry_rows = [
        {
            "geometry_check_id": gid,
            "scope": scope,
            "object_ids": objects,
            "expected_geometry": expected,
            "native1x_opened": "",
            "nearest8x_opened": "",
            "observed_geometry": "",
            "manual_result": "",
            "manual_notes": "",
        }
        for gid, scope, objects, expected in GEOMETRY_CHECKS
    ]
    write_csv(ROOT / "manual_geometry_ledger.csv", list(geometry_rows[0]), geometry_rows)

    semantic_rows = [
        {
            "semantic_check_id": sid,
            "scope": scope,
            "expected_semantics": expected,
            "full_page_opened": "",
            "native_opened": "",
            "observed_semantics": "",
            "manual_result": "",
            "manual_notes": "",
        }
        for sid, scope, expected in SEMANTIC_CHECKS
    ]
    write_csv(ROOT / "manual_semantic_ledger.csv", list(semantic_rows[0]), semantic_rows)

    page_rows = [
        {
            "page_check_id": "PAGE-001",
            "physical_page": str(PDF_PAGE),
            "full_page_200dpi_opened": "",
            "full_page_native_opened": "",
            "grayscale_opened": "",
            "overlay_opened": "",
            "caption_matches": "",
            "page_integration": "",
            "clipping": "",
            "unreadability_or_severe_imbalance": "",
            "manual_result": "",
            "manual_notes": "",
        }
    ]
    write_csv(ROOT / "manual_page_ledger.csv", list(page_rows[0]), page_rows)

    manifest = {
        "generated_at": now,
        "generator_scope": "judgment-free skeletons only",
        "figure_id": FIGURE_ID,
        "handoff_id": HANDOFF_ID,
        "pdf_physical_page": PDF_PAGE,
        "object_count": len(OBJECTS),
        "unordered_pair_count": len(pair_rows),
        "glyph_check_count": len(glyph_rows),
        "math_check_count": len(math_rows),
        "geometry_check_count": len(geometry_rows),
        "semantic_check_count": len(semantic_rows),
        "manual_verdict_fields_populated": 0,
        "scope_note": "Denominator covers every semantic reader-visible object emitted by the target figure source, including the generated numbered caption and excluding surrounding page body/header/footer.",
    }
    (ROOT / "machine_skeleton_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
