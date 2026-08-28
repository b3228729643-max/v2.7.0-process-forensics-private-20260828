from pathlib import Path
import csv
import json


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa2_r110_r168_readonly_adjudication_v1")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fobj:
        return list(csv.DictReader(fobj))


def main() -> None:
    errors: list[str] = []
    csv_paths = sorted(ROOT.rglob("*.csv"))
    json_paths = sorted(ROOT.rglob("*.json"))
    parsed = {path.name: read_csv(path) for path in csv_paths}
    for path in json_paths:
        with path.open(encoding="utf-8-sig") as fobj:
            json.load(fobj)

    objects = parsed["visible_object_denominator.csv"]
    pairs = parsed["all_unordered_pairs.csv"]
    glyphs = parsed["glyph_codepoint_denominator.csv"]
    manual_glyphs = parsed["manual_glyph_review.csv"]
    relations = parsed["critical_relation_machine.csv"]
    manual_relations = parsed["manual_critical_relation_review.csv"]
    manual_text = parsed["manual_text_object_review.csv"]
    manual_graphics = parsed["manual_graphic_object_review.csv"]

    if len(objects) != 29:
        errors.append("object_count")
    if len(pairs) != 406:
        errors.append("pair_count")
    if len({row["pair_id"] for row in pairs}) != 406:
        errors.append("pair_unique")
    if len(glyphs) != 162:
        errors.append("glyph_count")
    if len(manual_glyphs) != 162:
        errors.append("manual_glyph_count")
    if {row["glyph_id"] for row in glyphs} != {row["glyph_id"] for row in manual_glyphs}:
        errors.append("glyph_id_set")
    if len(relations) != 37:
        errors.append("relation_count")
    if len(manual_relations) != 37:
        errors.append("manual_relation_count")
    if {row["relation_id"] for row in relations} != {row["relation_id"] for row in manual_relations}:
        errors.append("relation_id_set")
    if {row["object_id"] for row in manual_text} != {f"T{i:02d}" for i in range(1, 15)}:
        errors.append("text_manual_ids")
    if {row["object_id"] for row in manual_graphics} != {f"G{i:02d}" for i in range(1, 16)}:
        errors.append("graphic_manual_ids")

    for row in parsed["contact_sheet_index.csv"]:
        if not (ROOT / row["file"]).is_file():
            errors.append(f"missing:{row['file']}")
    for row in relations:
        stem = f"{row['relation_id']}_{row['object_a']}_{row['object_b']}"
        for suffix in ("_1x.png", "_overlay_1x.png", "_overlay_8x_nearest.png"):
            path = ROOT / "critical_relations" / f"{stem}{suffix}"
            if not path.is_file():
                errors.append(f"missing:{path.relative_to(ROOT).as_posix()}")

    nonzero_pairs = [row for row in pairs if int(row["raw_mask_intersection_px"]) > 0]
    print(f"CSV_PARSE_COUNT={len(csv_paths)}")
    print(f"JSON_PARSE_COUNT={len(json_paths)}")
    print(f"ROOT_FILE_COUNT={sum(path.is_file() for path in ROOT.rglob('*'))}")
    print(f"NONZERO_PAIR_COUNT={len(nonzero_pairs)}")
    print(f"NONZERO_PAIR_PIXELS={sum(int(row['raw_mask_intersection_px']) for row in pairs)}")
    print(f"ERROR_COUNT={len(errors)}")
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
