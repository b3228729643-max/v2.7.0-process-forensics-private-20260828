from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R5_SA3_FRESH_ISOLATED_R112_20260827")
M=ROOT/"machine"


def read_csv(path: Path) -> list[dict]:
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


identity=json.loads((M/"identity_and_denominator.json").read_text(encoding="utf-8"))
elements=json.loads((M/"visible_elements.json").read_text(encoding="utf-8"))
pairs=json.loads((M/"all_unordered_pairs.json").read_text(encoding="utf-8"))
safe_map=json.loads((M/"id_safe_filename_map.json").read_text(encoding="utf-8"))
manual=read_csv(ROOT/"manual_object_ledger.csv")
views=read_csv(ROOT/"manual_view_ledger.csv")
overlaps=read_csv(ROOT/"after_overlap_report.csv")

element_ids=[e["element_id"] for e in elements]
manual_ids=[e["element_id"] for e in manual]
safe_names=[e["safe_filename"] for e in safe_map]
pair_ids=[p["pair_id"] for p in pairs]

png_paths=[]
for e in elements:
    png_paths.extend([ROOT/e["roi_1x"],ROOT/e["roi_8x"],ROOT/e["mask"]])
png_paths.extend(ROOT/p for p in identity["text_contact_sheets"])
png_paths.extend(ROOT/p for p in identity["graphic_contact_sheets"])
png_paths.extend([
    ROOT/"views"/"full_page_200dpi.png",
    ROOT/"views"/"full_page_300dpi.png",
    ROOT/"views"/"figure_crop_300dpi.png",
    ROOT/"views"/"standalone_300dpi.png",
    ROOT/"views"/"grayscale_300dpi.png",
    ROOT/"views"/"after_text_measurement_overlay_300dpi.png",
])

png_errors=[]
for path in png_paths:
    try:
        if not path.is_file():
            raise FileNotFoundError(path)
        with Image.open(path) as img:
            img.verify()
    except Exception as exc:
        png_errors.append({"path":str(path),"error":repr(exc)})

checks={
    "identity_uid":identity["uid"]=="FIG-P067-01",
    "identity_round":identity["official_round"]=="R112",
    "visible_denominator_130":len(elements)==identity["visible_denominator"]==130,
    "visible_text_95":sum(e["kind"]=="TEXT_GLYPH" for e in elements)==95,
    "visible_graphics_35":sum(e["kind"]=="GRAPHIC_PATH" for e in elements)==35,
    "element_ids_unique":len(set(element_ids))==len(element_ids),
    "safe_names_unique":len(set(safe_names))==len(safe_names)==len(elements),
    "all_masks_nonempty":all(not e["mask_empty"] and int(e["ink_area_px"])>0 for e in elements),
    "manual_rows_130":len(manual)==130,
    "manual_ids_exact":set(manual_ids)==set(element_ids) and len(set(manual_ids))==130,
    "manual_fields_complete":all(all(row.get(k,"").strip() for k in ("reviewer","original_match","overlay_complete","mask_only_pure","decision","note")) for row in manual),
    "manual_single_hard_fail":Counter(row["decision"] for row in manual)==Counter({"PASS":129,"FAIL_SEMANTIC":1}),
    "manual_hard_fail_is_gfx007":next(row for row in manual if row["decision"]=="FAIL_SEMANTIC")["element_id"]=="GFX-007",
    "view_rows_6":len(views)==6,
    "all_views_opened":all(row["opened_native_or_original"].lower()=="true" for row in views),
    "all_views_fail_consistent":all(row["decision"]=="FAIL" for row in views),
    "pair_count_formula":len(pairs)==130*129//2==8385,
    "pair_ids_unique":len(set(pair_ids))==8385,
    "pair_elements_valid":all(p["element_a"] in element_ids and p["element_b"] in element_ids for p in pairs),
    "pair_class_counts_sum":sum(int(row["count"]) for row in overlaps if row["row_id"].startswith("PAIR-CLASS-"))==8385,
    "pair_total_row_8385":next(row for row in overlaps if row["row_id"]=="PAIR-TOTAL")["count"]=="8385",
    "text_contact_sheets_8":len(identity["text_contact_sheets"])==8,
    "graphic_contact_sheets_9":len(identity["graphic_contact_sheets"])==9,
    "all_expected_png_openable":not png_errors,
    "result_consistent":(ROOT/"RESULT.txt").read_text(encoding="utf-8").strip()=="SA3_FAIL_RETURN_TO_SA2",
    "acceptance_contains_fail":("SA3_FAIL_RETURN_TO_SA2" in (ROOT/"after_visual_acceptance.md").read_text(encoding="utf-8")),
}

summary={
    "checks":checks,
    "all_checks_pass":all(checks.values()),
    "png_expected_count":len(png_paths),
    "png_errors":png_errors,
    "manual_decisions":dict(Counter(row["decision"] for row in manual)),
    "pair_count":len(pairs),
    "result":"SA3_FAIL_RETURN_TO_SA2",
}
(M/"final_crosscheck.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=True))
if not summary["all_checks_pass"]:
    raise SystemExit(1)
