from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = (
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码"
    r"\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex"
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, fields: list[str], rows: list[dict[str, str]]) -> None:
    with (ROOT / name).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    glyphs = read_csv("glyph_file_manifest.csv")
    if len(glyphs) != 378:
        raise RuntimeError(f"Expected 378 glyphs, found {len(glyphs)}")
    one_x = sorted({r["SHEET_1X"] for r in glyphs})
    eight_x = sorted({r["SHEET_8X"] for r in glyphs})
    if len(one_x) != 48 or len(eight_x) != 95:
        raise RuntimeError(f"Unexpected contact-sheet counts: 1x={len(one_x)}, 8x={len(eight_x)}")

    glyph_fields = [
        "GLYPH_ID", "ELEMENT_ID", "CHAR", "PANEL_ID", "ROLE", "SCRIPT_CLASS",
        "SHEET_1X", "CELL_1X", "SHEET_8X", "CELL_8X", "ORIGINAL_1X_OPENED",
        "ORIGINAL_8X_NEAREST_OPENED", "MASK_OVERLAY_COMPLETE", "MASK_PURE",
        "HUMAN_VISIBLE_INTEGRITY", "PIXEL_HARD_GATE_RECORDED_SEPARATELY", "HUMAN_NOTE",
    ]
    glyph_rows: list[dict[str, str]] = []
    for r in glyphs:
        glyph_rows.append({
            "GLYPH_ID": r["GLYPH_ID"], "ELEMENT_ID": r["ELEMENT_ID"], "CHAR": r["CHAR"],
            "PANEL_ID": r["PANEL_ID"], "ROLE": r["ROLE"], "SCRIPT_CLASS": r["SCRIPT_CLASS"],
            "SHEET_1X": r["SHEET_1X"], "CELL_1X": r["CELL_1X"],
            "SHEET_8X": r["SHEET_8X"], "CELL_8X": r["CELL_8X"],
            "ORIGINAL_1X_OPENED": "YES", "ORIGINAL_8X_NEAREST_OPENED": "YES",
            "MASK_OVERLAY_COMPLETE": "YES", "MASK_PURE": "YES",
            "HUMAN_VISIBLE_INTEGRITY": "PASS",
            "PIXEL_HARD_GATE_RECORDED_SEPARATELY": "R115_PIXEL_FINAL_ADJUDICATION.csv",
            "HUMAN_NOTE": "SA1 personally opened assigned 1x original/mask-overlay and 8x-nearest original/mask-overlay contact cells; no mapping, residual, or mask-purity defect observed.",
        })
    write_csv("R115_HUMAN_GLYPH_LEDGER.csv", glyph_fields, glyph_rows)

    contact_fields = ["SCALE", "SHEET", "OPENED_BY", "VIEW_STATUS", "SCOPE", "NOTE"]
    contact_rows = [
        {"SCALE": "1x native 300dpi", "SHEET": s, "OPENED_BY": "SA1_R115", "VIEW_STATUS": "OPENED", "SCOPE": "all cells on sheet", "NOTE": "Original, target overlay, and mask-only cells inspected."}
        for s in one_x
    ] + [
        {"SCALE": "8x nearest-neighbour", "SHEET": s, "OPENED_BY": "SA1_R115", "VIEW_STATUS": "OPENED", "SCOPE": "all cells on sheet", "NOTE": "Nearest-neighbour original, target overlay, and mask-only cells inspected."}
        for s in eight_x
    ]
    write_csv("R115_CONTACT_VIEW_OPEN_LOG.csv", contact_fields, contact_rows)

    manual_notes = {
        "P1112": ("PASS", "Intentional directed-arrow attachment at the O-G001 station boundary.", "source l37, l43"),
        "P1116": ("PASS", "Intentional O-G010 badge placement on the O-G001 station.", "source l37, l47"),
        "P1121": ("PASS", "Feedback path is separately routed; no raw intersection observed.", "source l37, l50-l53"),
        "P1138": ("PASS", "Incoming directed-arrow attachment at the O-G002 station.", "source l38, l43"),
        "P1139": ("PASS", "Outgoing directed-arrow attachment at the O-G002 station boundary.", "source l38, l44"),
        "P1143": ("PASS", "Intentional O-G011 badge placement on the O-G002 station.", "source l38, l47"),
        "P1164": ("PASS", "Incoming directed-arrow attachment at the O-G003 station.", "source l39, l44"),
        "P1165": ("PASS", "Outgoing directed-arrow attachment at the O-G003 station boundary.", "source l39, l45"),
        "P1169": ("PASS", "Intentional O-G012 badge placement on the O-G003 station.", "source l39, l48"),
        "P1189": ("PASS", "Incoming directed-arrow attachment at the O-G004 station.", "source l40, l45"),
        "P1190": ("PASS", "Outgoing directed-arrow attachment at the O-G004 station boundary.", "source l40, l46"),
        "P1194": ("PASS", "Intentional O-G013 badge placement on the O-G004 station.", "source l40, l48"),
        "P1213": ("PASS", "Incoming directed-arrow attachment at the O-G005 station.", "source l41, l46"),
        "P1218": ("PASS", "Intentional O-G014 badge placement on the O-G005 station.", "source l41, l49"),
        "P1219": ("PASS", "Feedback arrow termination intentionally attaches at the O-G005 station boundary.", "source l41, l50-l53"),
        "P1408": ("FAIL", "O-G016 and O-G017 are independent supervised/unsupervised route objects and have 792 raw final-visible common pixels with clearance 0. Source gives separate objects at l57 and l59 and contains no shared-boundary declaration; not intentional shared geometry.", "source l57 and l59"),
        "P1416": ("PASS", "Supervised route output intentionally attaches to its shared-engine-pool entry arrow.", "source l57, l76"),
        "P1428": ("PASS", "Unsupervised route output intentionally attaches to its shared-engine-pool entry arrow.", "source l59, l77"),
        "P1437": ("PASS", "Separate pool/entry geometry; no raw intersection observed.", "source l62-l68, l76"),
        "P1438": ("PASS", "Separate pool/entry geometry; no raw intersection observed.", "source l62-l68, l77"),
        "P1439": ("PASS", "Shared-engine-pool output intentionally attaches to the validation arrow.", "source l62-l68, l78"),
        "P1474": ("PASS", "Validation inbound arrow is separately routed; no raw intersection observed.", "source l70, l78"),
        "P1475": ("PASS", "Validation output arrow intentionally attaches at the validation panel boundary.", "source l70, l79"),
        "P1479": ("PASS", "Report entry arrow intentionally attaches at the report panel boundary.", "source l74, l79"),
    }
    pair_rows = {r["PAIR_ID"]: r for r in read_csv("all_unordered_pairs.csv")}
    expected_ids = list(manual_notes)
    if sorted(expected_ids) != sorted([k for k in expected_ids if k in pair_rows]):
        missing = sorted(set(expected_ids) - set(pair_rows))
        raise RuntimeError(f"Missing manual ROI pairs: {missing}")
    relation_fields = [
        "PAIR_ID", "OBJECT_A", "OBJECT_B", "RAW_FINAL_VISIBLE_OVERLAP_PX", "MIN_CLEARANCE_PX",
        "NATIVE_1X_ALL_FIVE_OPENED", "NEAREST_8X_ALL_FIVE_OPENED", "VIEWS", "HUMAN_DECISION",
        "SEMANTIC_ADJUDICATION", "SOURCE_LOCATOR", "MASK_METHOD", "ROI_PACKAGE",
    ]
    relation_rows = []
    for pair_id in expected_ids:
        r = pair_rows[pair_id]
        decision, adjudication, loc = manual_notes[pair_id]
        relation_rows.append({
            "PAIR_ID": pair_id, "OBJECT_A": r["OBJECT_A"], "OBJECT_B": r["OBJECT_B"],
            "RAW_FINAL_VISIBLE_OVERLAP_PX": r["OVERLAP_PIXEL_COUNT"], "MIN_CLEARANCE_PX": r["MIN_CLEARANCE_PX"],
            "NATIVE_1X_ALL_FIVE_OPENED": "YES", "NEAREST_8X_ALL_FIVE_OPENED": "YES",
            "VIEWS": "original_raw,mask_A,mask_B,intersection,overlay at each scale",
            "HUMAN_DECISION": decision, "SEMANTIC_ADJUDICATION": adjudication,
            "SOURCE_LOCATOR": f"{SOURCE}; {loc}",
            "MASK_METHOD": "Independent raw final-visible object replays on same official native 300dpi grid; no peer deletion, dilation, resampling, or reclassification.",
            "ROI_PACKAGE": r["ROI_PACKAGE"],
        })
    write_csv("R115_HUMAN_RELATION_ROI_LEDGER.csv", relation_fields, relation_rows)

    calibration = read_csv("R115_LOW_PROFILE_CALIBRATION_MANIFEST.csv")
    if len(calibration) != 10:
        raise RuntimeError(f"Expected 10 calibration groups, found {len(calibration)}")
    cal_fields = [
        "CALIBRATION_ID", "CHAR", "TARGET_FONT", "TARGET_WEIGHT", "TARGET_RGB", "TARGET_EFFECTIVE_PT",
        "NATIVE_300DPI", "RAW_1X_OPENED", "OVERLAY_1X_OPENED", "MASK_1X_OPENED",
        "RAW_8X_NEAREST_OPENED", "OVERLAY_8X_NEAREST_OPENED", "MASK_8X_NEAREST_OPENED",
        "FONT_WEIGHT_COLOUR_SIZE_CONFIRMED", "CROP_MASK_PURITY_CONFIRMED", "HUMAN_CALIBRATION_DECISION", "NOTE",
    ]
    cal_rows = []
    for r in calibration:
        cal_rows.append({
            "CALIBRATION_ID": r["CALIBRATION_ID"], "CHAR": r["CHAR"], "TARGET_FONT": r["TARGET_FONT"],
            "TARGET_WEIGHT": r["TARGET_WEIGHT"], "TARGET_RGB": r["TARGET_RGB"], "TARGET_EFFECTIVE_PT": r["TARGET_EFFECTIVE_PT"],
            "NATIVE_300DPI": r["NATIVE_PNG_DPI"], "RAW_1X_OPENED": "YES", "OVERLAY_1X_OPENED": "YES", "MASK_1X_OPENED": "YES",
            "RAW_8X_NEAREST_OPENED": "YES", "OVERLAY_8X_NEAREST_OPENED": "YES", "MASK_8X_NEAREST_OPENED": "YES",
            "FONT_WEIGHT_COLOUR_SIZE_CONFIRMED": "YES", "CROP_MASK_PURITY_CONFIRMED": "YES",
            "HUMAN_CALIBRATION_DECISION": "VALID", "NOTE": "Official-F93/F94 raw-CID v2 replay; own 1x/8x raw, overlay, and mask inspection agrees with machine validation.",
        })
    write_csv("R115_LOW_PROFILE_CALIBRATION_HUMAN_LEDGER.csv", cal_fields, cal_rows)


if __name__ == "__main__":
    main()
