from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook\main_full.pdf")
FIG = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_elbo_geometry.tex")
CHAP = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C06.tex")

INPUTS = [
    ("PDF", PDF, 4_967_161, "93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F"),
    ("FIG", FIG, 3_425, "7BAED58EE4634091A2873D84942A2CA4E2C2475D509B2FA5FDCB5A28E5FADE5F"),
    ("CHAP", CHAP, 120_809, "7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029"),
]

REQUIRED = [
    "full_page_200dpi.png", "full_page_300dpi.png",
    "figure_caption_native_300dpi.png", "figure_caption_grayscale_300dpi.png",
    "foreground_candidate_mask_300dpi.png", "object_overlay_300dpi.png",
    "semantic_overlay_300dpi.png", "text_overlay_300dpi.png",
    "page_739_bbox.xhtml", "object_index.csv", "text_geometry_metrics.csv",
    "scope_and_denominator.md", "input_identity.txt", "manual_object_ledger.csv",
    "manual_pair_ledger.txt", "pair_index_no_verdict.csv", "glyph_codepoint_ledger.csv",
    "manual_overlap_adjudication.md", "source_font_and_readability_adjudication.csv",
    "math_semantic_ledger.md", "page_integration_ledger.md", "manual_visual_acceptance.md",
]
for stem in (
    "roi01_left_bar_formula_note", "roi02_right_title_upper_bound",
    "roi03_right_staircase_local_label", "roi04_right_axis_ticks_label",
    "roi05_formula_codepoints", "roi06_left_lower_note",
    "roi07_caption_all_lines", "roi08_panel_gutter_boundaries",
):
    REQUIRED.extend((f"{stem}_native1x.png", f"{stem}_nearest8x.png"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


lines = []
ok = True
for name, path, expected_size, expected_hash in INPUTS:
    actual_size = path.stat().st_size
    actual_hash = sha256(path)
    passed = actual_size == expected_size and actual_hash == expected_hash
    ok &= passed
    lines.extend((f"{name}_SIZE={actual_size}", f"{name}_SHA256={actual_hash}", f"{name}_IDENTITY_PASS={str(passed).lower()}"))

missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
lines.append(f"REQUIRED_FILE_COUNT={len(REQUIRED)}")
lines.append(f"REQUIRED_MISSING_COUNT={len(missing)}")
ok &= not missing

with (ROOT / "object_index.csv").open(encoding="utf-8") as f:
    object_ids = [row["OBJECT_ID"] for row in csv.DictReader(f)]
with (ROOT / "manual_object_ledger.csv").open(encoding="utf-8") as f:
    object_rows = list(csv.DictReader(f))
object_pass = len(object_ids) == 31 and len(object_rows) == 31 and [r["OBJECT_ID"] for r in object_rows] == object_ids and all(r["POST_OBSERVATION_VERDICT"] == "PASS" for r in object_rows)
lines.extend((f"OBJECT_INDEX_COUNT={len(object_ids)}", f"MANUAL_OBJECT_COUNT={len(object_rows)}", f"MANUAL_OBJECT_PASS={str(object_pass).lower()}"))
ok &= object_pass

with (ROOT / "pair_index_no_verdict.csv").open(encoding="utf-8") as f:
    expected_pairs = {row["PAIR_ID"] for row in csv.DictReader(f)}
seen = {}
for raw in (ROOT / "manual_pair_ledger.txt").read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith(("MANUAL_", "FORMAT=", "ORDER=", "LEGEND_", "EVIDENCE_", "N=", "C=")):
        continue
    parts = line.split("|")
    a = parts[0]
    for token in parts[1:]:
        b, verdict = token.split(":")
        pair_id = f"{a}__{b}"
        if pair_id in seen:
            raise ValueError(f"duplicate pair {pair_id}")
        seen[pair_id] = verdict
counts = Counter(seen.values())
pair_pass = len(seen) == 465 and set(seen) == expected_pairs and counts == Counter({"C": 452, "L": 13})
lines.extend((f"PAIR_INDEX_COUNT={len(expected_pairs)}", f"MANUAL_PAIR_COUNT={len(seen)}", f"MANUAL_PAIR_CLEAR={counts['C']}", f"MANUAL_PAIR_LEGAL={counts['L']}", f"MANUAL_PAIR_PASS={str(pair_pass).lower()}"))
ok &= pair_pass

full200 = Image.open(ROOT / "full_page_200dpi.png")
full300 = Image.open(ROOT / "full_page_300dpi.png")
native = Image.open(ROOT / "figure_caption_native_300dpi.png")
image_pass = full200.size == (1654, 2339) and full300.size == (2481, 3508) and native.size == (1938, 854)
lines.extend((f"FULL200_SIZE={full200.width}x{full200.height}", f"FULL300_SIZE={full300.width}x{full300.height}", f"NATIVE300_SIZE={native.width}x{native.height}", f"IMAGE_GEOMETRY_PASS={str(image_pass).lower()}"))
ok &= image_pass

acceptance = (ROOT / "manual_visual_acceptance.md").read_text(encoding="utf-8")
acceptance_pass = "RESULT=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1" in acceptance and "HARD_DEFECT_COUNT=0" in acceptance and "UNRESOLVED_COUNT=0" in acceptance
lines.append(f"ACCEPTANCE_CONTENT_PASS={str(acceptance_pass).lower()}")
ok &= acceptance_pass

lines.append(f"PRESEAL_VALIDATION_PASS={str(ok).lower()}")
(ROOT / "preseal_validation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
if not ok:
    raise SystemExit(1)
