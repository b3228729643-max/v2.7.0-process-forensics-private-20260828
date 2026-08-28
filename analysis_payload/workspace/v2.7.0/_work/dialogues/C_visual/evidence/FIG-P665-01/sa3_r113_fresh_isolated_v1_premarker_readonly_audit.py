import ast
import csv
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa3_r113_fresh_isolated_v1")
MARKER = ROOT / "FINAL_SEAL_MARKER.txt"
counts = {"csv": 0, "json": 0, "python": 0, "text": 0}
errors = []

if MARKER.exists():
    raise RuntimeError("marker exists during premarker audit")

for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
    try:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            if not rows or any(len(row) != len(rows[0]) for row in rows):
                raise RuntimeError("ragged/empty CSV")
            counts["csv"] += 1
        elif suffix == ".json":
            json.loads(path.read_text(encoding="utf-8-sig"))
            counts["json"] += 1
        elif suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            counts["python"] += 1
        elif suffix in {".md", ".txt", ".ps1"}:
            if "\x00" in path.read_text(encoding="utf-8-sig"):
                raise RuntimeError("NUL in text")
            counts["text"] += 1
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")

cache = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} or p.suffix.lower() in {".pyc", ".pyo"}]
if errors or cache:
    raise RuntimeError({"parse_errors": errors, "cache_pyc": cache})

print(json.dumps({"PREMARKER_READONLY_AUDIT_OK": 1, "PARSE_ERRORS": 0, "CACHE_PYC_ITEMS": 0, "PARSED": counts}, sort_keys=True))
