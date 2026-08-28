"""Read-only integrity check for the completed v1.8.0 G3 visual evidence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
G3 = ROOT / "qa" / "gates" / "G3"


def load(name: str) -> dict[str, object]:
    path = G3 / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def require_file(relative: str) -> None:
    path = ROOT / Path(relative)
    if not path.is_file():
        raise FileNotFoundError(path)


def main() -> int:
    preliminary = load("G3_visual_numeric_preliminary.json")
    manual = load("G3_manual_visual_review.json")
    final = load("G3_gate_report.json")

    if preliminary.get("automatic_passed") is not True:
        raise RuntimeError("G3 automatic phase is not passed")
    dual = preliminary.get("dual_renderer")
    if not isinstance(dual, dict) or dual.get("passed") is not True:
        raise RuntimeError("dual-renderer comparison is not passed")
    engines = dual.get("engines")
    if not isinstance(engines, list) or len(engines) != 2:
        raise RuntimeError("expected exactly two rendering engines")
    comparisons = dual.get("comparisons")
    if not isinstance(comparisons, dict) or len(comparisons) != 8:
        raise RuntimeError("expected eight P1/high-risk comparisons")
    for name, item in comparisons.items():
        if not isinstance(item, dict) or item.get("passed") is not True:
            raise RuntimeError(f"comparison not passed: {name}")
        require_file(str(item["mupdf"]))
        require_file(str(item["poppler"]))

    scenarios = preliminary.get("scenario_evidence")
    if not isinstance(scenarios, dict):
        raise RuntimeError("scenario evidence is missing")
    for key in ["one_hundred_percent", "grayscale", "double_page", "baseline_regression"]:
        require_file(str(scenarios[key]))
    mobile = scenarios.get("mobile_landscape")
    if not isinstance(mobile, list) or len(mobile) != 3:
        raise RuntimeError("mobile landscape evidence must contain three crops")
    for relative in mobile:
        require_file(str(relative))

    if manual.get("passed") is not True:
        raise RuntimeError("manual visual review is not passed")
    for relative in manual.get("evidence", []):
        require_file(str(relative))
    if final.get("passed") is not True:
        raise RuntimeError("final G3 report is not passed")

    print(
        json.dumps(
            {
                "visual_regression": "PASS",
                "engines": engines,
                "comparisons": len(comparisons),
                "manual_evidence": len(manual.get("evidence", [])),
                "scenario_groups": 4,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

