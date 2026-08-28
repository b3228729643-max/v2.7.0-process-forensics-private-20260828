from __future__ import annotations

import json
import math
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parent
PDF = ROOT / "official_r90_page_626.pdf"
PNG = ROOT / "full_page_300dpi.png"

TEXT = "31,35,40,35"
BLUE = "31,78,121,35"
RULE_GRAY = "184,192,200,10"
GRAY = "107,114,128,10"
RED = "178,58,72,35"
TEAL = "15,118,110,35"


def main() -> None:
    with fitz.open(PDF) as document:
        page = document[0]
        page_rect = fitz.Rect(page.rect)
        drawings = page.get_drawings()
        raw = page.get_text("rawdict")

    with Image.open(PNG) as image:
        width, height = image.size

    scale_x = width / page_rect.width
    scale_y = height / page_rect.height

    spans: list[dict] = []
    line_span_ids: list[list[int]] = []
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            ids: list[int] = []
            for span in line["spans"]:
                spans.append(span)
                ids.append(len(spans))
            if ids:
                line_span_ids.append(ids)

    def scale_box(box: tuple[float, float, float, float], pad: int = 2) -> list[int]:
        return [
            max(0, math.floor(box[0] * scale_x) - pad),
            max(0, math.floor(box[1] * scale_y) - pad),
            min(width, math.ceil(box[2] * scale_x) + pad),
            min(height, math.ceil(box[3] * scale_y) + pad),
        ]

    def span_box(first: int, last: int | None = None, pad: int = 2) -> list[int]:
        last = first if last is None else last
        boxes = [spans[index - 1]["bbox"] for index in range(first, last + 1)]
        return scale_box(
            (
                min(box[0] for box in boxes),
                min(box[1] for box in boxes),
                max(box[2] for box in boxes),
                max(box[3] for box in boxes),
            ),
            pad,
        )

    def drawing_box(indices: list[int], pad: int = 4) -> list[int]:
        boxes = [drawings[index - 1]["rect"] for index in indices]
        return scale_box(
            (
                min(box.x0 for box in boxes),
                min(box.y0 for box in boxes),
                max(box.x1 for box in boxes),
                max(box.y1 for box in boxes),
            ),
            pad,
        )

    checks: list[dict] = []

    nodes = [
        ("PRECHECK", 9, 31, [2], RULE_GRAY),
        ("VALID", 32, 32, [3], BLUE),
        ("BADINPUT", 33, 53, [4, 5], RED),
        ("INIT", 54, 66, [6], RULE_GRAY),
        ("GOAL", 67, 70, [7], BLUE),
        ("COMPLETED", 71, 78, [8], TEAL),
        ("BUDGETCHECK", 79, 82, [9], BLUE),
        ("BUDGET", 83, 89, [10], GRAY),
        ("PROPOSAL", 90, 92, [11], BLUE),
        ("PROPOSALFAIL", 93, 104, [12, 13], RED),
        ("COUNT", 105, 109, [14], RULE_GRAY),
        ("UNIFORM", 110, 115, [15], BLUE),
        ("UNIFORMFAIL", 116, 127, [16, 17], RED),
        ("EVALUATE", 128, 134, [18], RULE_GRAY),
        ("NUMERICOK", 135, 144, [19], BLUE),
        ("NUMERICFAIL", 145, 156, [20, 21], RED),
        ("ENVELOPEOK", 157, 160, [22], BLUE),
        ("ENVELOPEFAIL", 161, 174, [23, 24], RED),
        ("ACCEPT", 175, 176, [25], BLUE),
        ("COMMIT", 177, 182, [26], RULE_GRAY),
        ("REJECT", 183, 188, [27], GRAY),
    ]
    node_lookup = {name: (first, last, drawing_ids, mask) for name, first, last, drawing_ids, mask in nodes}

    for name, first, last, drawing_ids, border_mask in nodes:
        border = drawing_box(drawing_ids, pad=2)
        x0, y0, x1, y1 = border
        # Keep the mask box on the border stroke itself.  A wider band can
        # mistake grayscale antialias pixels from nearby black text for a
        # gray border even when the two objects are geometrically separate.
        band = 12
        side_boxes = {
            "TOP": [x0, y0, x1, min(y1, y0 + band)],
            "BOTTOM": [x0, max(y0, y1 - band), x1, y1],
            "LEFT": [x0, y0, min(x1, x0 + band), y1],
            "RIGHT": [max(x0, x1 - band), y0, x1, y1],
        }
        for side, side_box in side_boxes.items():
            checks.append(
                {
                    "id": f"N_{name}_TEXT_BORDER_{side}",
                    "view": "PAGE_300DPI",
                    "element_a_id": f"{name}_ALL_TEXT",
                    "element_a_class": "TEXT_FORMULA",
                    "element_b_id": f"{name}_BORDER_{side}",
                    "element_b_class": "NODE_BORDER",
                    "a_box": span_box(first, last),
                    "b_box": side_box,
                    "a_mask": TEXT,
                    "b_mask": border_mask,
                    "required_clearance_px": 5,
                }
            )

        node_lines: list[tuple[int, int]] = []
        for ids in line_span_ids:
            selected = [index for index in ids if first <= index <= last]
            if selected:
                node_lines.append((min(selected), max(selected)))
        node_lines.sort(key=lambda item: spans[item[0] - 1]["bbox"][1])
        for line_number, (upper, lower) in enumerate(zip(node_lines, node_lines[1:]), start=1):
            checks.append(
                {
                    "id": f"T_{name}_LINE_{line_number}_{line_number + 1}",
                    "view": "PAGE_300DPI",
                    "element_a_id": f"{name}_LINE_{line_number}",
                    "element_a_class": "TEXT_FORMULA",
                    "element_b_id": f"{name}_LINE_{line_number + 1}",
                    "element_b_class": "TEXT_FORMULA",
                    "a_box": span_box(*upper, pad=1),
                    "b_box": span_box(*lower, pad=1),
                    "a_mask": TEXT,
                    "b_mask": TEXT,
                    "required_clearance_px": 4,
                }
            )

    path_labels = [
        ("VALID_NO", 189, [30, 31]),
        ("VALID_YES", 190, [33, 34]),
        ("GOAL_YES", 191, [38, 39]),
        ("GOAL_NO", 192, [41, 42]),
        ("BUDGET_YES", 193, [44, 45]),
        ("BUDGET_NO", 194, [47, 48]),
        ("PROPOSAL_FAIL", 195, [50, 51]),
        ("PROPOSAL_SUCCESS", 196, [53, 54]),
        ("UNIFORM_FAIL", 197, [58, 59]),
        ("UNIFORM_SUCCESS", 198, [61, 62]),
        ("NUMERIC_NO", 199, [66, 67]),
        ("NUMERIC_YES", 200, [69, 70]),
        ("ENVELOPE_NO", 201, [72, 73]),
        ("ENVELOPE_YES", 202, [75, 76]),
        ("ACCEPT_BRANCH", 203, [78, 79]),
        ("REJECT_BRANCH", 204, [81, 82]),
    ]
    for name, span_id, drawing_ids in path_labels:
        checks.append(
            {
                "id": f"L_{name}_TEXT_PATH",
                "view": "PAGE_300DPI",
                "element_a_id": f"LABEL_{name}",
                "element_a_class": "EDGE_LABEL",
                "element_b_id": f"PATH_{name}",
                "element_b_class": "LINE_ARROW",
                "a_box": span_box(span_id),
                "b_box": drawing_box(drawing_ids),
                "a_mask": TEXT,
                "b_mask": BLUE,
                "required_clearance_px": 3,
            }
        )

    checks.append(
        {
            "id": "L_LOOP_TEXT_PATH",
            "view": "PAGE_300DPI",
            "element_a_id": "LOOP_LABEL",
            "element_a_class": "EDGE_LABEL",
            "element_b_id": "RETURN_LOOP_PATH",
            "element_b_class": "LINE_ARROW",
            "a_box": span_box(205, 208),
            "b_box": [490, 900, 516, 2836],
            "a_mask": TEXT,
            "b_mask": GRAY,
            "required_clearance_px": 3,
        }
    )

    label_node_pairs = [
        ("VALID_NO", 189, "VALID"), ("VALID_NO_BADINPUT", 189, "BADINPUT"),
        ("VALID_YES", 190, "VALID"), ("VALID_YES_INIT", 190, "INIT"),
        ("GOAL_YES", 191, "GOAL"), ("GOAL_YES_COMPLETED", 191, "COMPLETED"),
        ("GOAL_NO", 192, "GOAL"), ("GOAL_NO_BUDGETCHECK", 192, "BUDGETCHECK"),
        ("BUDGET_YES", 193, "BUDGETCHECK"), ("BUDGET_YES_STOP", 193, "BUDGET"),
        ("BUDGET_NO", 194, "BUDGETCHECK"), ("BUDGET_NO_PROPOSAL", 194, "PROPOSAL"),
        ("PROPOSAL_FAIL", 195, "PROPOSAL"), ("PROPOSAL_FAIL_NODE", 195, "PROPOSALFAIL"),
        ("PROPOSAL_SUCCESS", 196, "PROPOSAL"), ("PROPOSAL_SUCCESS_COUNT", 196, "COUNT"),
        ("UNIFORM_FAIL", 197, "UNIFORM"), ("UNIFORM_FAIL_NODE", 197, "UNIFORMFAIL"),
        ("UNIFORM_SUCCESS", 198, "UNIFORM"), ("UNIFORM_SUCCESS_EVAL", 198, "EVALUATE"),
        ("NUMERIC_NO", 199, "NUMERICOK"), ("NUMERIC_NO_FAIL", 199, "NUMERICFAIL"),
        ("NUMERIC_YES", 200, "NUMERICOK"), ("NUMERIC_YES_ENV", 200, "ENVELOPEOK"),
        ("ENVELOPE_NO", 201, "ENVELOPEOK"), ("ENVELOPE_NO_FAIL", 201, "ENVELOPEFAIL"),
        ("ENVELOPE_YES", 202, "ENVELOPEOK"), ("ENVELOPE_YES_ACCEPT", 202, "ACCEPT"),
        ("ACCEPT_BRANCH", 203, "ACCEPT"), ("ACCEPT_BRANCH_COMMIT", 203, "COMMIT"),
        ("REJECT_BRANCH", 204, "ACCEPT"), ("REJECT_BRANCH_NODE", 204, "REJECT"),
    ]
    for check_name, span_id, node_name in label_node_pairs:
        _, _, drawing_ids, border_mask = node_lookup[node_name]
        checks.append(
            {
                "id": f"B_{check_name}_{node_name}",
                "view": "PAGE_300DPI",
                "element_a_id": f"LABEL_{check_name}",
                "element_a_class": "EDGE_LABEL",
                "element_b_id": f"{node_name}_BORDER",
                "element_b_class": "NODE_BORDER",
                "a_box": span_box(span_id),
                "b_box": drawing_box(drawing_ids),
                "a_mask": TEXT,
                "b_mask": border_mask,
                "required_clearance_px": 5,
            }
        )

    adjacent_nodes = [
        ("PRECHECK", "VALID"), ("VALID", "INIT"), ("INIT", "GOAL"),
        ("GOAL", "BUDGETCHECK"), ("BUDGETCHECK", "PROPOSAL"),
        ("PROPOSAL", "COUNT"), ("COUNT", "UNIFORM"),
        ("UNIFORM", "EVALUATE"), ("EVALUATE", "NUMERICOK"),
        ("NUMERICOK", "ENVELOPEOK"), ("ENVELOPEOK", "ACCEPT"),
        ("ACCEPT", "COMMIT"), ("ACCEPT", "REJECT"),
    ]
    for upper_name, lower_name in adjacent_nodes:
        _, _, upper_drawings, upper_mask = node_lookup[upper_name]
        _, _, lower_drawings, lower_mask = node_lookup[lower_name]
        checks.append(
            {
                "id": f"G_{upper_name}_{lower_name}_BORDERS",
                "view": "PAGE_300DPI",
                "element_a_id": f"{upper_name}_BORDER",
                "element_a_class": "NODE_BORDER",
                "element_b_id": f"{lower_name}_BORDER",
                "element_b_class": "NODE_BORDER",
                "a_box": drawing_box(upper_drawings),
                "b_box": drawing_box(lower_drawings),
                "a_mask": upper_mask,
                "b_mask": lower_mask,
                "required_clearance_px": 1,
            }
        )

    checks.extend(
        [
            {
                "id": "P_DIAGRAM_CAPTION",
                "view": "PAGE_300DPI",
                "element_a_id": "BOTTOM_RETURN_PATHS",
                "element_a_class": "LINE_ARROW",
                "element_b_id": "CAPTION",
                "element_b_class": "CAPTION",
                "a_box": drawing_box([84, 85, 86, 87, 88, 89]),
                "b_box": span_box(209, 213),
                "a_mask": GRAY,
                "b_mask": TEXT,
                "required_clearance_px": 3,
            },
            {
                "id": "P_CAPTION_FOLLOWING_BODY",
                "view": "PAGE_300DPI",
                "element_a_id": "CAPTION",
                "element_a_class": "CAPTION",
                "element_b_id": "FOLLOWING_BODY",
                "element_b_class": "BODY_TEXT",
                "a_box": span_box(209, 213),
                "b_box": span_box(214, 239),
                "a_mask": TEXT,
                "b_mask": TEXT,
                "required_clearance_px": 4,
            },
            {"id":"E_FIGURE_CROP_EDGE","type":"edge","view":"FIGURE_CROP_300DPI","element_a_id":"ALL_FIGURE_FOREGROUND","element_a_class":"TEXT_GRAPHICS","element_b_id":"FIGURE_CROP_EDGE","element_b_class":"IMAGE_EDGE","required_clearance_px":6},
            {"id":"E_STANDALONE_EDGE","type":"edge","view":"STANDALONE_300DPI","element_a_id":"ALL_FIGURE_FOREGROUND","element_a_class":"TEXT_GRAPHICS","element_b_id":"STANDALONE_EDGE","element_b_class":"IMAGE_EDGE","required_clearance_px":6},
            {"id":"E_PAGE_EDGE","type":"edge","view":"PAGE_300DPI","element_a_id":"ALL_PAGE_FOREGROUND","element_a_class":"TEXT_GRAPHICS","element_b_id":"PAGE_EDGE","element_b_class":"IMAGE_EDGE","required_clearance_px":6},
            {"id":"E_GRAYSCALE_EDGE","type":"edge","view":"GRAYSCALE_300DPI","element_a_id":"ALL_PAGE_FOREGROUND","element_a_class":"TEXT_GRAPHICS","element_b_id":"GRAYSCALE_EDGE","element_b_class":"IMAGE_EDGE","required_clearance_px":6},
        ]
    )

    payload = {
        "candidate_id": "FIG-P578-01-R3-OFFICIAL-R90",
        "foreground_delta": 20,
        "background": [255, 255, 255],
        "views": {
            "PAGE_300DPI": "full_page_300dpi.png",
            "FIGURE_CROP_300DPI": "figure_crop_300dpi.png",
            "STANDALONE_300DPI": "standalone_300dpi.png",
            "GRAYSCALE_300DPI": "grayscale_300dpi.png",
        },
        "checks": checks,
    }
    (ROOT / "overlap_evidence_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"checks={len(checks)} image={width}x{height}")


if __name__ == "__main__":
    main()
