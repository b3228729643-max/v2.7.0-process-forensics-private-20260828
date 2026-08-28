from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


source_root = Path(sys.argv[1])
relative_targets = (
    "合并总册/v260_FIG-P206-01_page.tex",
    "合并总册/v260_FIG-P210-01_page.tex",
    "合并总册/v260_FIG-P547-01_page.tex",
    "合并总册/v260_FIG-P602-01_page.tex",
    "合并总册/v260_FIG-P637-01_page.tex",
    "合并总册/v260_FIG-P638-01_page.tex",
    "合并总册/v260_FIG-P639-01_page.tex",
    "合并总册/v260_FIG-P665-01_page.tex",
    "合并总册/v260_FIG-P667-01_page.tex",
    "合并总册/v260_FIG-P680-01_page.tex",
    "合并总册/v260_FIG-P713-01_page.tex",
    "合并总册/v260_FIG-P715-01_page.tex",
    "合并总册/v260_FIG-P716-01_page.tex",
    "合并总册/v260_FIG-P717-01_page.tex",
    "合并总册/v260_FIG-P719-01_page.tex",
    "合并总册/v260_FIG-P720-01_page.tex",
    "合并总册/v260_FIG-P721-01_page.tex",
    "合并总册/v260_FIG-P722-01_page.tex",
    "第02册_基础监督学习方法/chapters/V2-C02.tex",
    "第04册_无监督学习与矩阵分解/chapters/V4-C02.tex",
    "第05册_采样方法主题模型与图排序/chapters/V5-C03.tex",
    "第05册_采样方法主题模型与图排序/chapters/V5-C05.tex",
    "第05册_采样方法主题模型与图排序/chapters/V5-C06.tex",
    "第05册_采样方法主题模型与图排序/chapters/V5-C07.tex",
    "第05册_采样方法主题模型与图排序/chapters/V5-C08.tex",
)

targets = [source_root / relative for relative in relative_targets]
for target in targets:
    if not target.is_file():
        raise FileNotFoundError(target)
    if any(part in {"绘图源码", "common", "styles", "tests"} for part in target.parts):
        raise RuntimeError(f"forbidden target: {target}")

counts: Counter[str] = Counter()
changed_files: list[str] = []


def replace_counted(pattern: re.Pattern[str], replacement: str, text: str, key: str) -> str:
    updated, count = pattern.subn(replacement, text)
    counts[key] += count
    return updated


for target in targets:
    raw = target.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    body = raw[3:] if has_bom else raw
    text = body.decode("utf-8")
    output_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("%"):
            output_lines.append(line)
            continue

        line = replace_counted(
            re.compile(r"(Gamma|Beta|Dirichlet)[ \u3000]+(?=[\u3400-\u9fff])"),
            r"\1",
            line,
            "distribution_gap",
        )

        if r"\hyphenation{" not in line:
            sort_separator = line.find("@") if (r"\index{" in line or r"\knowledgeanchor{" in line) else -1
            prefix = line[: sort_separator + 1] if sort_separator >= 0 else ""
            visible = line[sort_separator + 1 :] if sort_separator >= 0 else line
            visible = replace_counted(
                re.compile(r"Dirichlet(?:--|—|–|-)多项(?:式)?"),
                r"\\DirichletMultinomial{}",
                visible,
                "DirichletMultinomial",
            )
            visible = replace_counted(
                re.compile(r"Metropolis(?:--|—|–|-)Hastings"),
                r"\\MetropolisHastings{}",
                visible,
                "MetropolisHastings",
            )
            visible = replace_counted(
                re.compile(r"(?<!\\)PageRank"),
                r"\\PageRank{}",
                visible,
                "PageRank",
            )
            visible = replace_counted(
                re.compile(r"(?:\$[kK]\$|(?<![A-Za-z\\])[kK]|𝑘)近邻"),
                r"\\kNN{}",
                visible,
                "kNN",
            )
            visible = replace_counted(
                re.compile(r"(?:\$[kK]\$|(?<![A-Za-z\\])[kK]|𝑘)均值"),
                r"\\kMeans{}",
                visible,
                "kMeans_term",
            )
            visible = replace_counted(
                re.compile(r"(?:\$[kK]\$|(?<![A-Za-z\\])[kK]|𝑘)折"),
                r"\\kFold{}",
                visible,
                "kFold",
            )
            line = prefix + visible

        line = replace_counted(
            re.compile(r"\\kMeans(?!\{\})"),
            r"\\kMeans{}",
            line,
            "terminated_kMeans",
        )
        output_lines.append(line)

    updated_text = "".join(output_lines)
    updated_body = updated_text.encode("utf-8")
    updated_raw = (b"\xef\xbb\xbf" if has_bom else b"") + updated_body
    if updated_raw != raw:
        target.write_bytes(updated_raw)
        changed_files.append(target.relative_to(source_root).as_posix())

print(f"changed_files={len(changed_files)}")
for changed in changed_files:
    print(changed)
for key, count in sorted(counts.items()):
    print(f"{key}={count}")
