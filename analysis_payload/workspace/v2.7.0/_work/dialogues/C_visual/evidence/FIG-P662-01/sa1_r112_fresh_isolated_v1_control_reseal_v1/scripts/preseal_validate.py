from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa1_r112_fresh_isolated_v1")


def csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def main() -> None:
    files = sorted(p for p in ROOT.rglob("*") if p.is_file())
    dirs = sorted(p for p in ROOT.rglob("*") if p.is_dir())
    parse_errors: list[str] = []
    csv_counts: dict[str, int] = {}
    json_files = 0
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            if path.suffix.lower() == ".csv":
                csv_counts[rel] = csv_rows(path)
            elif path.suffix.lower() == ".json":
                json.loads(path.read_text(encoding="utf-8-sig"))
                json_files += 1
            elif path.suffix.lower() in {".md", ".txt", ".py"}:
                path.read_text(encoding="utf-8-sig")
        except Exception as exc:
            parse_errors.append(f"{rel}: {type(exc).__name__}: {exc}")

    pair_text = (ROOT / "ledgers" / "manual_pair_ledger.md").read_text(encoding="utf-8")
    pair_ids = re.findall(r"(?m)^- (P\d{3}) ", pair_text)
    expected = {f"P{i:03d}" for i in range(1, 301)}
    observed = set(pair_ids)

    cache_names = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache"}
    cache_paths = [p.relative_to(ROOT).as_posix() for p in dirs if p.name in cache_names]
    pyc_paths = [p.relative_to(ROOT).as_posix() for p in files if p.suffix.lower() == ".pyc"]
    reparse_paths = []
    for p in [ROOT, *dirs, *files]:
        try:
            if p.is_symlink() or os.path.isjunction(p):
                reparse_paths.append(p.relative_to(ROOT).as_posix() if p != ROOT else ".")
        except (AttributeError, OSError):
            if p.is_symlink():
                reparse_paths.append(p.relative_to(ROOT).as_posix() if p != ROOT else ".")

    image_files = [p.relative_to(ROOT).as_posix() for p in files if p.suffix.lower() == ".png"]
    report = {
        "scanned_file_count": len(files),
        "scanned_directory_count_excluding_root": len(dirs),
        "csv_row_counts": csv_counts,
        "json_files_parsed": json_files,
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "manual_pair_id_count": len(pair_ids),
        "manual_pair_unique_id_count": len(observed),
        "manual_pair_missing_ids": sorted(expected - observed),
        "manual_pair_extra_ids": sorted(observed - expected),
        "manual_text_element_rows": csv_counts.get("ledgers/manual_text_element_ledger.csv", -1),
        "visible_object_rows": csv_counts.get("ledgers/visible_object_denominator.csv", -1),
        "machine_pair_rows": csv_counts.get("ledgers/machine_all_unordered_pairs.csv", -1),
        "png_file_count": len(image_files),
        "cache_path_count": len(cache_paths),
        "cache_paths": cache_paths,
        "pyc_file_count": len(pyc_paths),
        "pyc_paths": pyc_paths,
        "reparse_path_count": len(reparse_paths),
        "reparse_paths": reparse_paths,
    }
    (ROOT / "controls" / "preseal_parse_hygiene_machine.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
