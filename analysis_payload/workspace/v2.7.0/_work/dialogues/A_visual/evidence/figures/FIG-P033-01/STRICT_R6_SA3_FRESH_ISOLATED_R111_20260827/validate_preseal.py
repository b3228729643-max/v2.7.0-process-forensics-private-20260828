from __future__ import annotations

import csv
import hashlib
import json
import re
from itertools import combinations
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C02\fig_v1_c02_projection.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C02.tex")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ids_from_markdown(path: Path, pattern: str) -> list[str]:
    return re.findall(pattern, path.read_text(encoding="utf-8"), flags=re.MULTILINE)


def main() -> None:
    checks: dict[str, object] = {}
    checks["root_exact"] = str(ROOT) == r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827"
    checks["pdf_sha256"] = sha(PDF)
    checks["pdf_sha_match"] = checks["pdf_sha256"] == "DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6"
    checks["source_sha256"] = sha(SOURCE)
    checks["source_sha_match"] = checks["source_sha256"] == "D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05"
    checks["chapter_sha256"] = sha(CHAPTER)
    doc = fitz.open(PDF)
    checks["pdf_pages"] = len(doc)
    checks["pdf_817_pages"] = len(doc) == 817
    checks["pdf_a4"] = abs(doc[0].rect.width - 595.276) < 0.01 and abs(doc[0].rect.height - 841.89) < 0.01

    strict = json.loads((ROOT / "machine_strict_atomic_candidates.json").read_text(encoding="utf-8"))
    atom_ids = [a["atom_id"] for a in strict["atoms"]]
    checks["glyph_count"] = strict["glyph_count"]
    checks["path_count"] = strict["foreground_path_count"]
    checks["atom_count"] = strict["atom_count"]
    checks["atom_ids_unique"] = len(atom_ids) == len(set(atom_ids)) == 96
    checks["strict_counts_match"] = (strict["glyph_count"], strict["foreground_path_count"], strict["atom_count"]) == (85, 11, 96)

    with (ROOT / "machine_all_unordered_pairs.csv").open(encoding="utf-8-sig", newline="") as f:
        pair_rows = list(csv.DictReader(f))
    expected_pairs = {tuple(sorted(pair)) for pair in combinations(atom_ids, 2)}
    actual_pairs = {tuple(sorted((r["ATOM_A"], r["ATOM_B"]))) for r in pair_rows}
    checks["pair_rows"] = len(pair_rows)
    checks["pair_id_unique"] = len({r["PAIR_ID"] for r in pair_rows}) == 4560
    checks["pair_set_complete"] = actual_pairs == expected_pairs and len(pair_rows) == 4560
    checks["machine_manual_fields_blank"] = all(
        not any(r[k] for k in ("REVIEWER", "OBSERVED", "DECISION", "NOTE", "PASS")) for r in pair_rows
    )

    manual_atom_ids = ids_from_markdown(ROOT / "manual_atomic_ledger.md", r"^\| ((?:GLYPH|PATH)-\d{3}) \|")
    checks["manual_atom_rows"] = len(manual_atom_ids)
    checks["manual_atom_ids_exact"] = set(manual_atom_ids) == set(atom_ids) and len(manual_atom_ids) == 96
    checks["manual_atom_pass_rows"] = sum(
        1 for line in (ROOT / "manual_atomic_ledger.md").read_text(encoding="utf-8").splitlines()
        if re.match(r"^\| (?:GLYPH|PATH)-\d{3} \|", line) and line.endswith("| PASS |")
    )

    near_ids = {r["PAIR_ID"] for r in pair_rows if float(r["BBOX_GAP_PX"]) <= 4.0}
    manual_pair_ids = ids_from_markdown(ROOT / "manual_pair_candidate_ledger.md", r"^\| (PAIR-\d{3,4}) \|")
    checks["near_pair_count"] = len(near_ids)
    checks["manual_pair_rows"] = len(manual_pair_ids)
    checks["manual_pair_ids_exact"] = set(manual_pair_ids) == near_ids and len(manual_pair_ids) == 131
    checks["manual_pair_pass_rows"] = sum(
        1 for line in (ROOT / "manual_pair_candidate_ledger.md").read_text(encoding="utf-8").splitlines()
        if re.match(r"^\| PAIR-\d{3,4} \|", line) and line.endswith("| PASS |")
    )
    checks["bbox_separated_pair_count"] = 4560 - len(near_ids)

    with (ROOT / "machine_glyph_metrics.csv").open(encoding="utf-8-sig", newline="") as f:
        glyph_metrics = list(csv.DictReader(f))
    checks["glyph_metric_rows"] = len(glyph_metrics)
    checks["glyph_page_clipped_rows"] = sum(r["PAGE_CLIPPED"] == "true" for r in glyph_metrics)
    checks["glyph_machine_manual_fields_blank"] = all(
        not any(r[k] for k in ("REVIEWER", "OBSERVED", "DECISION", "NOTE", "PASS")) for r in glyph_metrics
    )

    expected_images = {
        "R111_p029_full_native300dpi.png": (2481, 3508),
        "R111_p029_FIG-P033-01_native300dpi.png": (1334, 757),
        "R111_p029_FIG-P033-01_native1x.png": (1334, 757),
        "R111_p029_FIG-P033-01_grayscale_native1x.png": (1334, 757),
        "R111_p029_FIG-P033-01_nearest_neighbor8x.png": (10672, 6056),
        "R111_p029_FIG-P033-01_with_caption_native300dpi.png": (2022, 838),
    }
    image_dims: dict[str, list[int]] = {}
    for name, expected in expected_images.items():
        with Image.open(ROOT / name) as im:
            image_dims[name] = list(im.size)
    checks["image_dimensions"] = image_dims
    checks["image_dimensions_match"] = all(tuple(image_dims[k]) == v for k, v in expected_images.items())

    manual_control_files = [
        "IDENTITY_AND_BOUNDARY.md",
        "input_and_location_proof.md",
        "manual_atomic_ledger.md",
        "manual_pair_candidate_ledger.md",
        "manual_pair_resolution_summary.md",
        "manual_semantics_and_geometry.md",
        "manual_R168_visual_acceptance.md",
    ]
    placeholder_tokens = [chr(123) * 2, "<" + "PLACE" + "HOLDER>", "T" + "BD", "TO" + "DO", "[" + "INSERT"]
    placeholder_hits: list[str] = []
    for name in manual_control_files:
        content = (ROOT / name).read_text(encoding="utf-8")
        if any(token.casefold() in content.casefold() for token in placeholder_tokens):
            placeholder_hits.append(name)
    checks["placeholder_hits"] = placeholder_hits
    checks["placeholder_free_controls"] = not placeholder_hits

    acceptance = (ROOT / "manual_R168_visual_acceptance.md").read_text(encoding="utf-8")
    required_controls = [
        "MISSING_TOFU_WRONG_CODEPOINT_PASS=true",
        "READABILITY_BALANCE_PASS=true",
        "OVERLAP_PIXEL_COUNT=0",
        "CLIP_PIXEL_COUNT=0",
        "PIXEL_ADJUDICATION_STATUS=CLEAR",
        "MATH_SEMANTICS_PASS=true",
        "GEOMETRY_PASS=true",
        "TEXT_CONSISTENCY_PASS=true",
        "GRAYSCALE_PASS=true",
        "PAGE_INTEGRATION_PASS=true",
        "SA3_RESULT=PASS",
    ]
    checks["resolved_controls"] = {c: c in acceptance for c in required_controls}
    checks["resolved_controls_all"] = all(checks["resolved_controls"].values())
    checks["scratch_locate_absent"] = not (ROOT / "scratch_locate.txt").exists()

    boolean_failures = [k for k, v in checks.items() if isinstance(v, bool) and not v]
    numeric_expectations = {
        "manual_atom_pass_rows": 96,
        "manual_pair_pass_rows": 131,
        "glyph_metric_rows": 85,
        "glyph_page_clipped_rows": 0,
        "bbox_separated_pair_count": 4429,
    }
    numeric_failures = {k: checks[k] for k, expected in numeric_expectations.items() if checks[k] != expected}
    result = {
        "validation_scope": "preseal",
        "checks": checks,
        "boolean_failures": boolean_failures,
        "numeric_failures": numeric_failures,
        "pass": not boolean_failures and not numeric_failures,
    }
    (ROOT / "machine_preseal_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
