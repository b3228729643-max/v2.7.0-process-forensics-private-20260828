"""Apply the sealed R115 low-profile and D/E audit to the local R12 candidate."""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "STRICT_R9_REQUAL_R115_SA1_20260824" / "r115_calibrate_and_de.py"
CANDIDATE = ROOT / "build" / "page" / "FIG-P756-01_R12_page.pdf"


def load_sealed():
    spec = importlib.util.spec_from_file_location("sealed_r115_calibrate_and_de", OLD)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load sealed R115 calibration audit")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_provenance() -> None:
    replacements = {
        "official final PDF": "local R12 page-wrapper final PDF",
        "official final-PDF": "local R12 page-wrapper final PDF",
        "official-F93/F94": "local R12 embedded-font",
        "Official-F93/F94": "Local R12 embedded-font",
        "official page": "local R12 page-wrapper page",
    }
    names = [
        "R115_LOW_PROFILE_CALIBRATION_MANIFEST.csv",
        "R115_LOW_PROFILE_CALIBRATION_VALIDATION.csv",
        "R115_PIXEL_FINAL_ADJUDICATION.csv",
        "R115_SOURCE_FONT_ROLE_AUDIT.csv",
        "R115_D_E_FINAL_ADJUDICATION.csv",
        "R115_D_E_ROLE_SUMMARY.csv",
        "R115_D_E_FINAL_SUMMARY.json",
        "R115_CALIBRATION_AND_DE_SUMMARY.json",
    ]
    for name in names:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8", newline="" if path.suffix == ".csv" else None)


def main() -> None:
    module = load_sealed()
    module.ROOT = ROOT
    module.CANDIDATE = CANDIDATE
    module.PAGE_NUMBER = 1
    module.main()
    normalize_provenance()
    aliases = {
        "R115_LOW_PROFILE_CALIBRATION_MANIFEST.csv": "R12_LOW_PROFILE_CALIBRATION_MANIFEST.csv",
        "R115_LOW_PROFILE_CALIBRATION_VALIDATION.csv": "R12_LOW_PROFILE_CALIBRATION_VALIDATION.csv",
        "R115_PIXEL_FINAL_ADJUDICATION.csv": "R12_PIXEL_FINAL_ADJUDICATION.csv",
        "R115_SOURCE_FONT_ROLE_AUDIT.csv": "after_font_audit.csv",
        "R115_D_E_FINAL_ADJUDICATION.csv": "R12_D_E_FINAL_ADJUDICATION.csv",
        "R115_D_E_ROLE_SUMMARY.csv": "R12_D_E_ROLE_SUMMARY.csv",
        "R115_D_E_FINAL_SUMMARY.json": "R12_D_E_FINAL_SUMMARY.json",
        "R115_CALIBRATION_AND_DE_SUMMARY.json": "R12_CALIBRATION_AND_DE_SUMMARY.json",
    }
    for source, target in aliases.items():
        shutil.copyfile(ROOT / source, ROOT / target)
    summary = json.loads((ROOT / "R12_CALIBRATION_AND_DE_SUMMARY.json").read_text(encoding="utf-8"))
    summary["candidate_scope"] = "local page-wrapper p1; root official full-book requalification still required"
    (ROOT / "R12_CALIBRATION_AND_DE_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
