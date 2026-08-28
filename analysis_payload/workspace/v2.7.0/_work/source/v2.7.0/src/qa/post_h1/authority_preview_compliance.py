"""Compare the late-arriving authority preview with the frozen v1.8.0 candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[2]


def read_json(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def require_all(text: str, fragments: list[str]) -> bool:
    return all(fragment in text for fragment in fragments)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    authority = args.authority.absolute()
    with fitz.open(authority) as document:
        authority_text = "\n".join(page.get_text("text") for page in document)
        authority_pages = document.page_count

    source = ROOT / "讲义源码"
    svd = (source / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C03.tex").read_text(encoding="utf-8")
    gradient = (source / "第01册_数学基础与统计学习基本理论" / "chapters" / "V1-C03.tex").read_text(encoding="utf-8")
    rejection = (source / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C02.tex").read_text(encoding="utf-8")
    dirichlet = (source / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C05.tex").read_text(encoding="utf-8")
    kmeans = (source / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C02.tex").read_text(encoding="utf-8")
    style = (source / "common" / "statlearnbook.sty").read_text(encoding="utf-8")
    entry_text = "\n".join(path.read_text(encoding="utf-8") for path in source.rglob("main*.tex"))

    g1 = read_json("qa/gates/G1/G1_gate_report.json")
    g2 = read_json("qa/gates/G2/G2_gate_report.json")
    g3 = read_json("qa/gates/G3/G3_gate_report.json")
    g1_static = g1["checks"]["static_source"]["summary"]
    figures = g2["checks"]["required_figure_widths"]["figures"]
    manual_checks = g3["manual_visual_review"]["checks"]
    caption_report = (ROOT / "qa/stage6/FIG-076-FIG-081/FIG-076-FIG-081_局部验证报告.md").read_text(encoding="utf-8")

    checks = {
        "authority_pdf_two_pages": authority_pages == 2,
        "authority_text_complete": require_all(
            authority_text,
            [
                "定义26.3",
                "算法3.1 在每个出口重算最终",
                "算法31.3 拆分数学主体与带预算工程版本",
                "算法34.1 补上",
                "图内最小字号",
                "\\resizebox",
                "分页门槛",
                "三个关键质控门",
            ],
        ),
        "svd_boundary_and_equality": require_all(
            svd,
            [
                r"1\leq k\leq r",
                r"A_k=A\iff k=r",
                r"1\leq k<r\Longrightarrow A_k\ne A",
            ],
        ),
        "gradient_final_recompute": require_all(
            gradient,
            [
                "每个出口都在最终返回点重新计算",
                r"f_{\rm final}",
                r"\boldsymbol g_{\rm final}",
                r"\mathtt{budget\_stop}",
                r"\mathtt{numerical\_failure}",
            ],
        ),
        "rejection_math_and_budget_split": require_all(
            rejection,
            [
                "无限等待数学主体",
                "可执行的有限预算版本",
                r"\label{alg:V5-C02-rejection-math}",
                r"\label{alg:V5-C02-rejection-budget}",
            ],
        ),
        "dirichlet_mutually_exclusive_inputs": require_all(
            dirichlet,
            [
                r"\uIf{仅提供类别序列$\boldsymbol y$}",
                r"\uElseIf{仅提供计数向量$\boldsymbol n$}",
                r"\Else{",
                "必须恰好提供一种",
            ],
        ),
        "algorithm_contracts_complete": (
            g1_static["algorithms"] == 73
            and g1_static["contracted_algorithms"] == 73
            and g1_static["findings"] == 0
        ),
        "figure_floor_and_width_targets": all(
            item["passed"]
            and item["textwidth_ratio"] >= 0.6
            and item["minimum_region_font_pt"] >= 8.5
            for item in figures.values()
        ),
        "figure_caption_body_sample_20": "高重合为 0/20" in caption_report,
        "grayscale_and_visual_review": (
            manual_checks["grayscale_readable"] is True
            and manual_checks["no_clipping_overlap_black_blocks_or_missing_glyphs"] is True
        ),
        "breakable_and_needspace_policy": (
            "breakable" in style
            and r"\Needspace" in style
            and r"\raggedbottom" in entry_text
        ),
        "kmeans_25_2_split_without_shrink": (
            require_all(
                kmeans,
                [
                    r"\label{alg:V4-C02-kmeans}",
                    r"\label{alg:V4-C02-kmeans-empty-repair}",
                    r"\label{alg:V4-C02-kmeans-multistart}",
                ],
            )
            and all(token not in kmeans for token in [r"\tiny", r"\scriptsize", r"\resizebox"])
        ),
        "three_quality_gates_passed": all(report.get("passed") is True for report in [g1, g2, g3]),
    }

    passed = all(checks.values())
    report = {
        "schema_version": 1,
        "scope": "late authority preview versus frozen v1.8.0 candidate",
        "authority_file": authority.name,
        "authority_pages": authority_pages,
        "checks": checks,
        "conflicts": [],
        "missing_requirements": [] if passed else [name for name, value in checks.items() if not value],
        "conclusion": "no_conflict_candidate_already_satisfies_preview" if passed else "remediation_required",
        "passed": passed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
