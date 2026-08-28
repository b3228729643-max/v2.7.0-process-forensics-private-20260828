from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def decision_counts(data: list[dict[str, str]]) -> dict[str, int]:
    return {
        "PASS": sum(item["manual_decision"] == "PASS" for item in data),
        "FAIL": sum(item["manual_decision"] == "FAIL" for item in data),
    }


def main() -> None:
    identity = json.loads((ROOT / "identity/official_candidate_identity.json").read_text(encoding="utf-8"))
    table_specs = {
        "objects": ("ledgers/manual_object_review.csv", "object_id", 32),
        "glyphs": ("ledgers/manual_glyph_review.csv", "glyph_id", 175),
        "pairs": ("ledgers/manual_pair_review.csv", "pair_id", 496),
        "critical": ("ledgers/manual_critical_review.csv", "pair_id", 17),
        "peer": ("ledgers/manual_peer_review.csv", "peer_id", 42),
        "role": ("ledgers/manual_role_review.csv", "role_id", 3),
        "clip": ("ledgers/manual_clip_review.csv", "object_id", 32),
        "views": ("ledgers/manual_view_review.csv", "view_id", 4),
        "hard_gates": ("ledgers/manual_hard_gate_review.csv", "gate_id", 12),
    }
    manual: dict[str, dict[str, object]] = {}
    ok = True
    for name, (rel, key, expected) in table_specs.items():
        data = rows(rel)
        ids = [item[key] for item in data]
        record = {
            "rows": len(data),
            "expected": expected,
            "unique_ids": len(set(ids)),
            "decisions": decision_counts(data),
            "all_rows_well_formed": all(None not in item and all(value is not None for value in item.values()) for item in data),
        }
        record["pass"] = (
            record["rows"] == expected
            and record["unique_ids"] == expected
            and record["all_rows_well_formed"]
            and sum(record["decisions"].values()) == expected
        )
        manual[name] = record
        ok = ok and bool(record["pass"])

    object_manifest = rows("objects/object_manifest.csv")
    glyph_machine = rows("glyphs/glyph_machine_measurements.csv")
    pair_machine = rows("pairs/all_pairs_machine.csv")
    critical_machine = rows("pairs/critical_machine_index.csv")
    peer_machine = rows("ledgers/peer_machine.csv")
    role_machine = rows("ledgers/role_machine.csv")
    clip_machine = rows("ledgers/clip_machine.csv")

    alignment = {
        "objects": {x["object_id"] for x in object_manifest} == {x["object_id"] for x in rows("ledgers/manual_object_review.csv")},
        "glyphs": {x["glyph_id"] for x in glyph_machine} == {x["glyph_id"] for x in rows("ledgers/manual_glyph_review.csv")},
        "pairs": {x["pair_id"] for x in pair_machine} == {x["pair_id"] for x in rows("ledgers/manual_pair_review.csv")},
        "critical": {x["pair_id"] for x in critical_machine} == {x["pair_id"] for x in rows("ledgers/manual_critical_review.csv")},
        "clip": {x["object_id"] for x in clip_machine} == {x["object_id"] for x in rows("ledgers/manual_clip_review.csv")},
    }
    ok = ok and all(alignment.values())

    manual_glyph_map = {x["glyph_id"]: x["manual_decision"] for x in rows("ledgers/manual_glyph_review.csv")}
    glyph_expected = {x["glyph_id"]: ("PASS" if x["machine_threshold_pass"].lower() == "true" else "FAIL") for x in glyph_machine}
    manual_peer = {(x["element_id"], x["peer_class"]): x["manual_decision"] for x in rows("ledgers/manual_peer_review.csv")}
    peer_expected = {(x["element_id"], x["peer_class"]): ("PASS" if x["machine_peer_pass"].lower() == "true" else "FAIL") for x in peer_machine}
    manual_role = {x["role"]: x["manual_decision"] for x in rows("ledgers/manual_role_review.csv")}
    role_expected = {x["role"]: ("PASS" if x["machine_role_pass"].lower() == "true" else "FAIL") for x in role_machine}
    verdict_alignment = {
        "glyph_manual_matches_strict_machine": manual_glyph_map == glyph_expected,
        "peer_manual_matches_strict_machine": manual_peer == peer_expected,
        "role_manual_matches_strict_machine": manual_role == role_expected,
        "all_pair_manual_pass_and_machine_pass": all(x["manual_decision"] == "PASS" for x in rows("ledgers/manual_pair_review.csv")) and all(x["machine_decision"] == "PASS" for x in pair_machine),
        "all_clip_manual_pass_and_machine_pass": all(x["manual_decision"] == "PASS" for x in rows("ledgers/manual_clip_review.csv")) and all(x["machine_clip_pass"].lower() == "true" for x in clip_machine),
    }
    ok = ok and all(verdict_alignment.values())

    paths_exist = {
        "object_masks_cards": all((ROOT / f"objects/masks_1x/{x['safe_filename']}.png").is_file() and (ROOT / f"objects/cards/{x['safe_filename']}.png").is_file() for x in object_manifest),
        "glyph_masks_cards": all((ROOT / x["mask_path"]).is_file() and (ROOT / x["card_path"]).is_file() for x in glyph_machine),
        "pair_cards": all((ROOT / x["pair_card_path"]).is_file() for x in pair_machine),
        "critical_cards": all((ROOT / x["card_path"]).is_file() for x in critical_machine),
    }
    ok = ok and all(paths_exist.values())

    pair_math = {
        "object_count": len(object_manifest),
        "expected_c_n_2": len(object_manifest) * (len(object_manifest) - 1) // 2,
        "actual_pairs": len(pair_machine),
        "unique_pairs": len({tuple(sorted((x["object_a"], x["object_b"]))) for x in pair_machine}),
        "illegal_overlap_sum": sum(int(x["illegal_overlap_pixel_count"]) for x in pair_machine),
    }
    pair_math["pass"] = pair_math == {
        "object_count": 32,
        "expected_c_n_2": 496,
        "actual_pairs": 496,
        "unique_pairs": 496,
        "illegal_overlap_sum": 0,
    }
    ok = ok and bool(pair_math["pass"])

    mandatory_views = {
        "render/full_page_200dpi.png": [1654, 2339],
        "render/figure_crop_300dpi.png": [1835, 1565],
        "render/standalone_300dpi.png": [1835, 1480],
        "render/grayscale_300dpi.png": [1835, 1565],
    }
    view_dimensions: dict[str, list[int]] = {}
    png_errors: list[dict[str, str]] = []
    png_count = 0
    for path in ROOT.rglob("*.png"):
        try:
            with Image.open(path) as image:
                image.verify()
            png_count += 1
        except Exception as exc:  # evidence report, not silent recovery
            png_errors.append({"path": path.relative_to(ROOT).as_posix(), "error": repr(exc)})
    for rel in mandatory_views:
        with Image.open(ROOT / rel) as image:
            view_dimensions[rel] = list(image.size)
    views_pass = view_dimensions == mandatory_views and not png_errors
    ok = ok and views_pass

    source_identity: dict[str, dict[str, object]] = {}
    for label in ("pdf", "figure_source", "chapter_source"):
        path = Path(identity[f"{label}_path"])
        stat = path.stat()
        current = {
            "bytes": stat.st_size,
            "sha256": sha256(path),
            "mtime_ns": stat.st_mtime_ns,
        }
        current["matches_frozen"] = (
            current["bytes"] == identity[f"{label}_bytes"]
            and current["sha256"] == identity[f"{label}_sha256"]
            and current["mtime_ns"] == identity[f"{label}_mtime_ns"]
        )
        source_identity[label] = current
    ok = ok and all(bool(item["matches_frozen"]) for item in source_identity.values())

    cache_entries = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"} or path.name.lower() == "cache"
    )
    ok = ok and not cache_entries

    report = {
        "uid": "FIG-P602-01",
        "phase": "preseal",
        "validation_pass": ok,
        "manual_tables": manual,
        "id_alignment": alignment,
        "verdict_alignment": verdict_alignment,
        "evidence_paths_exist": paths_exist,
        "pair_math": pair_math,
        "png_count_verified": png_count,
        "png_errors": png_errors,
        "mandatory_view_dimensions": view_dimensions,
        "mandatory_views_pass": views_pass,
        "source_identity": source_identity,
        "cache_entries": cache_entries,
    }
    (ROOT / "qa/preseal_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
