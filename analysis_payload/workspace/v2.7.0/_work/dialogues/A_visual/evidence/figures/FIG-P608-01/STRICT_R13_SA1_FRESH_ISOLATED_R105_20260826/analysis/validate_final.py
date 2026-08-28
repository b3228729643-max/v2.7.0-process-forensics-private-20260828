import csv
import itertools
import json
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R13_SA1_FRESH_ISOLATED_R105_20260826")


def rows(name):
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


objects = rows("object_ledger.csv")
glyphs = rows("glyph_machine_ledger.csv")
rules = [r for r in rows("math_rule_ledger.csv") if r["safe_filename"] != "N/A_AGGREGATE"]
pairs = rows("all_unordered_pairs.csv")
manual = rows("manual_glyph_reviewer_ledger.csv")
manual_rel = rows("manual_relation_reviewer_ledger.csv")
manual_views = rows("manual_view_reviewer_ledger.csv")
semantics = rows("semantic_content_audit.csv")
contact_index = rows("contact_sheet_index.csv")

object_ids = [r["object_id"] for r in objects]
expected_pairs = {tuple(sorted(v)) for v in itertools.combinations(object_ids, 2)}
actual_pairs = {tuple(sorted((r["object_a"], r["object_b"]))) for r in pairs}
expected_review = {r["element_id"] for r in glyphs} | {r["element_id"] for r in rules}
manual_ids = {r["element_id"] for r in manual}

image_refs = {
    "full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png",
    "grayscale_300dpi.png", "page_661_300dpi_native.png",
}
image_refs |= {r["mask_file"] for r in objects}
image_refs |= {f"views/contact_sheets_8x/{r['sheet']}" for r in contact_index}
for r in rows("after_overlap_report.csv"):
    image_refs.add(r["evidence_1x"]); image_refs.add(r["evidence_8x"])
for r in rows("endpoint_clip_counterevidence.csv"):
    image_refs.add(r["view_1x"]); image_refs.add(r["view_8x"])

opened = 0
for rel in sorted(image_refs):
    p = ROOT / rel
    if not p.is_file():
        raise AssertionError(f"missing image: {rel}")
    with Image.open(p) as im:
        im.verify()
    opened += 1

hard_pairs = [r for r in pairs if int(r["required_clearance_px"]) > 0]
hard_overlap = [r for r in hard_pairs if int(r["overlap_pixel_count"]) > 0]
hard_clearance = [r for r in hard_pairs if float(r["clearance_px"]) < float(r["required_clearance_px"])]

checks = {
    "object_count": len(objects),
    "object_ids_unique": len(object_ids) == len(set(object_ids)),
    "nonempty_masks": all(int(r["pixel_count"]) > 0 for r in objects),
    "pair_count": len(pairs),
    "expected_pair_count": len(expected_pairs),
    "pair_set_exact": actual_pairs == expected_pairs and len(actual_pairs) == len(pairs),
    "hard_overlap_count": len(hard_overlap),
    "hard_clearance_failure_count": len(hard_clearance),
    "clip_count": sum(int(r["clip_pixel_count"]) for r in objects),
    "review_expected_count": len(expected_review),
    "review_row_count": len(manual),
    "review_ids_exact": manual_ids == expected_review and len(manual_ids) == len(manual),
    "review_all_pass": all(r["decision"] == "PASS" for r in manual),
    "review_all_true": all(r[k] == "true" for r in manual for k in ("original_match", "overlay_complete", "mask_only_pure")),
    "review_zero_missing_foreign": all(int(r["missing_stroke_px"]) == 0 and int(r["foreign_pixel_px"]) == 0 for r in manual),
    "manual_relation_count": len(manual_rel),
    "manual_relations_all_pass": all(r["decision"] == "PASS" and r["view_1x_opened"] == "true" and r["view_8x_opened"] == "true" for r in manual_rel),
    "manual_views_all_pass": all(r["decision"] == "PASS" and r["opened_native"] == "true" for r in manual_views),
    "semantics_all_pass": all(r["decision"] == "PASS" for r in semantics),
    "contact_index_count": len(contact_index),
    "contact_index_exact": {r["element_id"] for r in contact_index} == expected_review,
    "referenced_images_opened": opened,
    "result_json_pass": json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))["result"] == "PASS",
}
checks["validation_pass"] = all(
    value is True or (key.endswith("_count") and value == 0) or key in {
        "object_count", "pair_count", "expected_pair_count", "review_expected_count", "review_row_count",
        "manual_relation_count", "contact_index_count", "referenced_images_opened",
    }
    for key, value in checks.items()
)
print(json.dumps(checks, ensure_ascii=False, indent=2))
