#!/usr/bin/env python3
"""Apply the v2.1.0 readability tokens to the 28 audited priority figures."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "src" / "绘图源码"

TARGETS = (
    "第01册_数学基础与统计学习基本理论/V1-C02/fig_v1_c02_projection.tex",
    "第01册_数学基础与统计学习基本理论/V1-C03/fig_v1_c03_gradient_contour.tex",
    "第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex",
    "第01册_数学基础与统计学习基本理论/V1-C10/fig_v1_c10_complexity.tex",
    "第03册_优化模型与序列模型/V3-C01/fig_v3_c01_simplex.tex",
    "第03册_优化模型与序列模型/V3-C03/fig_v3_c03_adaboost_loop.tex",
    "第03册_优化模型与序列模型/V3-C05/fig_v3_c05_lattice.tex",
    "第03册_优化模型与序列模型/V3-C06/fig_v3_c06_chain.tex",
    "第03册_优化模型与序列模型/V3-C07/fig_v3_c07_selection_loop.tex",
    "第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_dependency_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_dependency_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_envelope.tex",
    "第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_dependency_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_rejection_sampling_comparison.tex",
    "第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_dependency_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_coordinate_sweep.tex",
    "第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C06/fig_v5_c06_dependency_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C06/fig_v5_c06_plate_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C06/fig_v5_c06_collapsed_gibbs_counts.tex",
    "第05册_采样方法主题模型与图排序/V5-C06/fig_v5_c06_variational_updates.tex",
    "第05册_采样方法主题模型与图排序/V5-C07/dependency_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C07/inbound_contribution.tex",
    "第05册_采样方法主题模型与图排序/V5-C07/damping_teleportation.tex",
    "第05册_采样方法主题模型与图排序/V5-C07/numerical_rank_trajectory.tex",
    "第05册_采样方法主题模型与图排序/V5-C08/dependency_graph.tex",
    "第05册_采样方法主题模型与图排序/V5-C08/matrix_probability_bridge.tex",
    "第05册_采样方法主题模型与图排序/V5-C08/full_course_synthesis_map.tex",
)

TOKENS = (
    ("①", "1."),
    ("②", "2."),
    ("③", "3."),
    ("④", "4."),
    ("⑤", "5."),
    (r"\fontsize{9.5pt}{11.4pt}", r"\fontsize{9.8pt}{11.8pt}"),
    ("Stealth[length=2.3mm,width=1.6mm]", "Stealth[length=2.5mm,width=1.8mm]"),
    ("line width=0.55pt", "line width=0.65pt"),
    ("line width=0.8pt", "line width=0.9pt"),
)

STAMP = "% v2.1.0 priority-figure QA: 9.8pt labels, strengthened strokes, semantic direct labels.\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    changed: list[tuple[str, int]] = []
    missing: list[str] = []
    for relative in TARGETS:
        path = ROOT / relative
        if not path.is_file():
            missing.append(relative)
            continue
        old = path.read_text(encoding="utf-8")
        new = old
        sites = 0
        for before, after in TOKENS:
            sites += new.count(before)
            new = new.replace(before, after)
        if STAMP.strip() not in new:
            new = STAMP + new
        if new != old:
            changed.append((relative, sites))
            if args.apply:
                path.write_text(new, encoding="utf-8", newline="")

    print(f"mode={'apply' if args.apply else 'check'}")
    print(f"targets={len(TARGETS)}")
    print(f"changed_files={len(changed)}")
    print(f"missing_files={len(missing)}")
    for relative, sites in changed:
        print(f"{sites:3d}  {relative}")
    for relative in missing:
        print(f"MISSING  {relative}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
