from __future__ import annotations

import re
import sys
from pathlib import Path


source_root = Path(sys.argv[1])
tex_files = sorted(source_root.rglob("*.tex"))

macros = (
    "DirichletMultinomial",
    "MetropolisHastings",
    "PageRank",
    "kNN",
    "kMeans",
    "kFold",
)
unterminated: list[str] = []
for path in tex_files:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for macro in macros:
            if re.search(rf"\\{macro}(?!\{{\}})", line):
                unterminated.append(f"{path.relative_to(source_root)}:{number}:{macro}:{line.strip()}")

gap_pattern = re.compile(r"(?:Gamma|Beta|Dirichlet)[ \u3000]+[\u3400-\u9fff]")
distribution_gaps: list[str] = []
for path in tex_files:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.lstrip().startswith("%") and gap_pattern.search(line):
            distribution_gaps.append(f"{path.relative_to(source_root)}:{number}:{line.strip()}")

forbidden = {
    "Dirichlet-multinomial dash": re.compile(r"Dirichlet(?:--|—|–|-)多项"),
    "Metropolis-Hastings dash": re.compile(r"Metropolis(?:--|—|–|-)Hastings"),
    "PageRank": re.compile(r"(?<!\\)PageRank"),
    "mathematical k term": re.compile(r"(?:\$[kK]\$|(?<![A-Za-z\\])[kK]|𝑘)(?:近邻|均值|折)"),
}
handwritten: list[str] = []
for path in tex_files:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("%") or r"\hyphenation{" in line:
            continue
        sort_separator = line.find("@") if (r"\index{" in line or r"\knowledgeanchor{" in line) else -1
        for label, pattern in forbidden.items():
            for match in pattern.finditer(line):
                if sort_separator >= 0 and match.start() < sort_separator:
                    continue
                handwritten.append(
                    f"{path.relative_to(source_root)}:{number}:{label}:{match.group(0)}:{line.strip()}"
                )

for name, hits in (
    ("unterminated_macros", unterminated),
    ("distribution_gaps", distribution_gaps),
    ("handwritten_variants", handwritten),
):
    print(f"[{name}] count={len(hits)}")
    print("\n".join(hits))
