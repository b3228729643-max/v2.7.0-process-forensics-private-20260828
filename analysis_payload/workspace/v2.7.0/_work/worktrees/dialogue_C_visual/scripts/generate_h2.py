#!/usr/bin/env python3
"""Generate the one-shot H2 final-delivery SHA-256 manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "SHA256SUMS.txt"
RELATIVE_PATHS = (
    "统计学习方法初学者讲义_合并总册v2.0.0_完整解析版.pdf",
    "统计学习方法讲义_v2.0.0_LaTeX源码.zip",
    "README_构建说明.md",
    "build_v2.0.0.ps1",
    "AGENTS.md",
    ".codex/hooks.json",
    "styles/README.md",
    "src/讲义源码/common/statlearnbook.sty",
    "src/绘图源码/figure_numeric_manifest_v16.json",
    "figures/figure_manifest.csv",
    "manifests/MASTER_PROMPT_v2.0.0.md",
    "manifests/H0_input_sha256.txt",
    "manifests/H1_content_sha256.txt",
    "qa/统计学习方法讲义_v2.0.0_问题关闭台账.xlsx",
    "qa/前置概念依赖矩阵.xlsx",
    "qa/前置概念依赖矩阵.csv",
    "qa/概念首次出现审计.xlsx",
    "qa/例题解答分级矩阵.xlsx",
    "qa/绘图重制矩阵.xlsx",
    "qa/逐页视觉审计.xlsx",
    "qa/未定义术语报告.md",
    "qa/全书符号规范.md",
    "qa/符号冲突报告.csv",
    "qa/baseline_reproduction.md",
    "qa/gate_a_structure_dependency.md",
    "qa/gate_b_math_teaching.md",
    "qa/gate_c_figures_layout.md",
    "qa/编译与链接QA.md",
    "qa/数学修复回归.md",
    "qa/最终验收报告.md",
    "qa/source_cache/gate_d_source_link_audit.json",
    "qa/source_cache/gate_d_pdf_link_audit.json",
    "qa/source_cache/gate_d_render_audit.json",
    "qa/source_cache/gate_d_full_pixel_diff.json",
    "qa/source_cache/gate_d_final_figure_audit.json",
    "qa/source_cache/gate_d_artifact_verification.json",
    "qa/source_cache/gate_d_source_zip_verification.json",
    "qa/source_cache/gate_d_figure_action_verification.json",
    "qa/source_cache/gate_d_font_audit.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()
    if len(RELATIVE_PATHS) != len(set(RELATIVE_PATHS)):
        raise RuntimeError("H2 input list contains duplicate paths")
    missing = [name for name in RELATIVE_PATHS if not (ROOT / name).is_file()]
    if missing:
        raise FileNotFoundError(f"H2 input files are missing: {missing}")
    if args.list_only:
        print("\n".join(RELATIVE_PATHS))
        print(f"H2_INPUTS={len(RELATIVE_PATHS)}")
        print("H2_HASH_EXECUTED=false")
        return 0
    if OUTPUT.exists():
        raise FileExistsError(f"H2 is one-shot and already exists: {OUTPUT}")
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "# H2 final-delivery SHA-256 manifest",
        "# algorithm=SHA-256",
        "# execution=1",
        f"# generated_utc={generated}",
        "# scope=final PDF, source ZIP, build/recovery interfaces, final workbooks, required QA, and key figure/style sources",
        "# SHA256SUMS.txt is excluded from self-hashing.",
    ]
    lines.extend(f"{sha256(ROOT / name)}  {name}" for name in RELATIVE_PATHS)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"H2_ENTRIES={len(RELATIVE_PATHS)}")
    print(f"H2_OUTPUT={OUTPUT}")
    print("H2_HASH_EXECUTED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
