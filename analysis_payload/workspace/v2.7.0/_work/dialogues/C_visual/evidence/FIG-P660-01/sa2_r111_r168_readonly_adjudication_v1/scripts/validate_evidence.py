from __future__ import annotations

import ast
import csv
from pathlib import Path

from PIL import Image


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa2_r111_r168_readonly_adjudication_v1"
)


def main() -> None:
    errors: list[str] = []
    counts = {"files": 0, "csv": 0, "png": 0, "python": 0, "text": 0}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        counts["files"] += 1
        if path.stat().st_size == 0:
            errors.append(f"zero-byte file: {path.relative_to(ROOT)}")
        suffix = path.suffix.lower()
        try:
            if suffix == ".csv":
                counts["csv"] += 1
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    reader = csv.reader(handle)
                    rows = list(reader)
                if not rows:
                    errors.append(f"empty CSV: {path.relative_to(ROOT)}")
                elif len({len(row) for row in rows}) != 1:
                    errors.append(f"ragged CSV: {path.relative_to(ROOT)}")
            elif suffix == ".png":
                counts["png"] += 1
                with Image.open(path) as image:
                    image.verify()
            elif suffix == ".py":
                counts["python"] += 1
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            elif suffix in {".md", ".txt"}:
                counts["text"] += 1
                path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"parse error {path.relative_to(ROOT)}: {exc}")

    forbidden = [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"}
    ]
    if forbidden:
        errors.extend(f"forbidden cache/bytecode: {value}" for value in forbidden)

    all_pairs = ROOT / "06_machine_tables" / "all_unordered_pairs_machine.csv"
    with all_pairs.open("r", encoding="utf-8-sig", newline="") as handle:
        pair_rows = list(csv.DictReader(handle))
    if len(pair_rows) != 435 or len({row["pair_id"] for row in pair_rows}) != 435:
        errors.append("unordered pair table is not exactly 435 unique rows")

    denominator = ROOT / "07_manual" / "visible_object_denominator.csv"
    with denominator.open("r", encoding="utf-8-sig", newline="") as handle:
        object_rows = list(csv.DictReader(handle))
    if len(object_rows) != 30 or len({row["object_id"] for row in object_rows}) != 30:
        errors.append("visible-object denominator is not exactly 30 unique rows")

    manual_objects = ROOT / "07_manual" / "manual_object_findings.csv"
    with manual_objects.open("r", encoding="utf-8-sig", newline="") as handle:
        manual_object_rows = list(csv.DictReader(handle))
    if len(manual_object_rows) != 30:
        errors.append("manual object ledger is not exactly 30 rows")

    manual_pairs = ROOT / "07_manual" / "manual_pair_adjudication.csv"
    with manual_pairs.open("r", encoding="utf-8-sig", newline="") as handle:
        manual_pair_rows = list(csv.DictReader(handle))
    if len(manual_pair_rows) != 19:
        errors.append("manual candidate-pair ledger is not exactly 19 rows")

    summary = ROOT / "06_machine_tables" / "validation_machine.txt"
    summary.write_text(
        "\n".join(
            [
                f"FILE_COUNT_BEFORE_MANIFEST_AND_MARKER={counts['files']}",
                f"CSV_PARSED={counts['csv']}",
                f"PNG_VERIFIED={counts['png']}",
                f"PYTHON_AST_PARSED={counts['python']}",
                f"UTF8_TEXT_PARSED={counts['text']}",
                f"VISIBLE_OBJECT_ROWS={len(object_rows)}",
                f"UNORDERED_PAIR_ROWS={len(pair_rows)}",
                f"MANUAL_OBJECT_ROWS={len(manual_object_rows)}",
                f"MANUAL_CANDIDATE_PAIR_ROWS={len(manual_pair_rows)}",
                f"ERROR_COUNT={len(errors)}",
                "MACHINE_FIELDS_ONLY=true",
                *(f"ERROR={error}" for error in errors),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if errors:
        raise SystemExit("; ".join(errors))


if __name__ == "__main__":
    main()
