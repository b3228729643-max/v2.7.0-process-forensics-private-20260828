from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.dont_write_bytecode = True
R1_MACHINE_BUILDER = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01"
) / "sa2_geometry_direct_build_r1" / "02_nontex_evidence" / "build_p640_nontex_evidence.py"

spec = importlib.util.spec_from_file_location("p640_r1_machine_builder_logic", R1_MACHINE_BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load frozen machine-builder logic")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Reuse only the frozen machine algorithm and ID schema. All measurements,
# renders, masks, inventories, crops and contact sheets are recomputed from
# the new R2 PDF into this new root. No R1 result or manual ledger is read.
module.ROOT = ROOT
module.OUT = HERE
module.PDF = ROOT / "01_build" / "v260_FIG-P640-01_standalone.pdf"
module.main()

# The inherited R1 machine summary carried a control assertion whose name
# mentioned manual fields. R2 machine artifacts keep only measurements.
summary_path = HERE / "machine_regression_summary.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary.pop("machine_outputs_do_not_contain_manual_reviewer_or_decision_fields", None)
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
