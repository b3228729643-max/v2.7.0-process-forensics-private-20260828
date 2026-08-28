from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R7_SA2_CDF_STEP_HANDLER_R112_DIRECT_BUILD_20260827")
PDF = ROOT / "build" / "v260_FIG-P067-01_standalone.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P067-01_standalone.tex")
PAGE_PNG = ROOT / "views" / "standalone_300dpi.png"
BASE_SCRIPT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R3_SA2_TICK_LABEL_PATCH_R111_DIRECT_BUILD_20260827\machine\build_r3_machine_evidence.py")


def main() -> None:
    spec = importlib.util.spec_from_file_location("p067_r3_machine_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load frozen machine-evidence implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    module.PDF = PDF
    module.SOURCE = SOURCE
    module.WRAPPER = WRAPPER
    module.PAGE_PNG = PAGE_PNG
    module.main()

    source_text = SOURCE.read_text(encoding="utf-8")
    interval_rows = [
        {"interval": "[.5,1)", "cdf_value": "0", "pmf_cumulative": "0"},
        {"interval": "[1,2)", "cdf_value": ".15", "pmf_cumulative": ".15"},
        {"interval": "[2,3)", "cdf_value": ".45", "pmf_cumulative": ".15+.30"},
        {"interval": "[3,4)", "cdf_value": ".80", "pmf_cumulative": ".15+.30+.35"},
        {"interval": "[4,4.5]", "cdf_value": "1", "pmf_cumulative": ".15+.30+.35+.20"},
    ]
    with (ROOT / "machine" / "cdf_interval_contract.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["interval", "cdf_value", "pmf_cumulative"])
        writer.writeheader()
        writer.writerows(interval_rows)
    contract = {
        "handler_left_count": source_text.count("const plot mark left"),
        "handler_right_count": source_text.count("const plot mark right"),
        "cdf_coordinate_list_count": source_text.count("coordinates {(.5,0) (1,.15) (2,.45) (3,.80) (4,1) (4.5,1)};"),
        "filled_endpoint_plot_count": source_text.count("only marks,mark=*,mark size=2.2pt"),
        "open_endpoint_plot_count": source_text.count("only marks,mark=o,mark size=2.35pt"),
        "pmf_coordinate_list_count": source_text.count("coordinates {(1,.15) (2,.30) (3,.35) (4,.20)};"),
        "expected_right_continuous_intervals": interval_rows,
        "source_semantic_contract_pass": (
            source_text.count("const plot mark left") == 1
            and source_text.count("const plot mark right") == 0
            and source_text.count("coordinates {(.5,0) (1,.15) (2,.45) (3,.80) (4,1) (4.5,1)};") == 1
            and source_text.count("coordinates {(1,.15) (2,.30) (3,.35) (4,.20)};") == 1
        ),
        "manual_fields_generated_or_overwritten": 0,
    }
    (ROOT / "machine" / "cdf_semantic_contract.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
