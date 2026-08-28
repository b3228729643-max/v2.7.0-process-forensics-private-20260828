from __future__ import annotations

import csv
import difflib
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = Path(r"src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex")
SOURCE = WORKTREE / SOURCE_REL
COORD_SOURCE = Path(r"D:\texlive\2026\texmf-dist\tex\generic\pgfplots\pgfplotscoordprocessing.code.tex")
PGFPLOTS_SOURCE = Path(r"D:\texlive\2026\texmf-dist\tex\generic\pgfplots\pgfplots.code.tex")
BEFORE_BYTES = 4626
BEFORE_SHA = "6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502"
AFTER_BYTES = 4686
AFTER_SHA = "2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(WORKTREE), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def excerpt(path: Path, ranges: list[tuple[int, int]]) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    result: list[str] = []
    for start, end in ranges:
        for number in range(start, end + 1):
            result.append(f"{number}\t{lines[number - 1]}")
    return "\n".join(result) + "\n"


def main() -> None:
    after = SOURCE.read_bytes()
    if len(after) != AFTER_BYTES or sha256_bytes(after) != AFTER_SHA:
        raise RuntimeError("after source identity mismatch")
    after_text = after.decode("utf-8")
    if after_text.count(",forget plot]") != 5:
        raise RuntimeError("forget plot count is not five")
    before_text = after_text.replace(",forget plot]", "]")
    before = before_text.encode("utf-8")
    if len(before) != BEFORE_BYTES or sha256_bytes(before) != BEFORE_SHA:
        raise RuntimeError("reverse reconstruction mismatch")

    (ROOT / "SOURCE_AFTER.tex").write_bytes(after)
    (ROOT / "SOURCE_BEFORE_RECONSTRUCTED.tex").write_bytes(before)
    diff = "".join(
        difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile="SOURCE_BEFORE_RECONSTRUCTED.tex",
            tofile="SOURCE_AFTER.tex",
            n=0,
        )
    )
    (ROOT / "INCREMENTAL_DIFF.patch").write_text(diff, encoding="utf-8")
    plus_lines = [line for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    minus_lines = [line for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    if len(plus_lines) != 5 or len(minus_lines) != 5:
        raise RuntimeError("incremental diff is not 5+/5-")

    source_lines = after_text.splitlines()
    addplot_lines = [
        {"line_number": index, "line": line, "forget_plot_count": line.count("forget plot")}
        for index, line in enumerate(source_lines, 1)
        if "\\addplot[" in line
    ]
    if len(addplot_lines) != 5 or any(row["forget_plot_count"] != 1 for row in addplot_lines):
        raise RuntimeError("not every ordinary addplot is forgotten exactly once")
    manual_images = [
        {"line_number": index, "line": line}
        for index, line in enumerate(source_lines, 1)
        if "\\addlegendimage" in line
    ]
    legend_entries = [
        {"line_number": index, "line": line}
        for index, line in enumerate(source_lines, 1)
        if "\\addlegendentry" in line
    ]
    if len(manual_images) != 2 or len(legend_entries) != 2:
        raise RuntimeError("manual legend cardinality mismatch")

    proof = {
        "schema": "P126_R15_STATIC_FORGET_PLOT_PROOF_V1",
        "handoff_id": "A-R115-P126-SA2-STATIC-FORGET-PLOT-PATCH-20260828",
        "status": "STATIC_ONLY_NOT_RENDERED_NOT_PASS",
        "source": str(SOURCE),
        "before_bytes": BEFORE_BYTES,
        "before_sha256": BEFORE_SHA,
        "after_bytes": AFTER_BYTES,
        "after_sha256": AFTER_SHA,
        "reverse_reconstruction_exact": True,
        "incremental_diff_additions": len(plus_lines),
        "incremental_diff_deletions": len(minus_lines),
        "ordinary_addplot_count": len(addplot_lines),
        "ordinary_addplots_with_exactly_one_forget_plot": sum(row["forget_plot_count"] == 1 for row in addplot_lines),
        "ordinary_addplots": addplot_lines,
        "manual_addlegendimage_count": len(manual_images),
        "manual_addlegendimages": manual_images,
        "legend_entry_count": len(legend_entries),
        "legend_entries": legend_entries,
        "static_legend_spec_conclusion": "all five ordinary plot specs become irrelevant and are excluded from the remembered legend plot-spec list; the two manual addlegendimage specs are therefore the only remembered legend specs and pair in order with the two legend entries",
        "render_validation_pending": True,
    }
    (ROOT / "FORGET_PLOT_STATIC_PROOF.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    causal = [
        "# Installed pgfplots causality excerpts",
        "",
        f"- `{COORD_SOURCE}` ({COORD_SOURCE.stat().st_size} bytes, SHA-256 `{sha256(COORD_SOURCE)}`)",
        f"- `{PGFPLOTS_SOURCE}` ({PGFPLOTS_SOURCE.stat().st_size} bytes, SHA-256 `{sha256(PGFPLOTS_SOURCE)}`)",
        "",
        "## `forget plot` marks an ordinary plot irrelevant before plot-spec retention",
        "",
        "```tex",
        excerpt(PGFPLOTS_SOURCE, [(4249, 4250)]).rstrip(),
        excerpt(COORD_SOURCE, [(5121, 5132)]).rstrip(),
        excerpt(COORD_SOURCE, [(3716, 3720)]).rstrip(),
        "```",
        "",
        "The five current ordinary `\\addplot` option lists each set `forget plot` exactly once. The key sets `pgfplots@curplot@isirrelevant`; the coordinate-processing branch then avoids `\\pgfplots@rememberplotspec` for those plots.",
        "",
        "## Manual legend images append their specs",
        "",
        "```tex",
        excerpt(PGFPLOTS_SOURCE, [(5794, 5796)]).rstrip(),
        "```",
        "",
        "## Legend construction consumes remembered plot specs in list order",
        "",
        "```tex",
        excerpt(PGFPLOTS_SOURCE, [(5721, 5739), (5760, 5768)]).rstrip(),
        "```",
        "",
        "With zero retained ordinary plot specs, the two unchanged manual legend-image specs are the only entries in the plot-spec list. They therefore pair, in order, with the unchanged two legend entries. This is a static mechanism proof only; the disconnected x2 rendering still requires a new PDF.",
    ]
    (ROOT / "PGFPLOTS_CAUSALITY.md").write_text("\n".join(causal) + "\n", encoding="utf-8")

    status = run_git("status", "--short")
    name_only = run_git("diff", "--name-only")
    numstat = run_git("diff", "--numstat")
    diff_check = subprocess.run(
        ["git", "-C", str(WORKTREE), "diff", "--check"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    scope = {
        "schema": "P126_R15_GIT_SCOPE_V1",
        "status_short_lines": [line for line in status.splitlines() if line],
        "name_only_lines": [line for line in name_only.splitlines() if line],
        "numstat_lines": [line for line in numstat.splitlines() if line],
        "index_empty": run_git("diff", "--cached", "--name-only").strip() == "",
        "diff_check_exit": diff_check.returncode,
        "diff_check_stdout": diff_check.stdout,
        "diff_check_stderr": diff_check.stderr,
        "sole_source_modified": len([line for line in name_only.splitlines() if line]) == 1,
    }
    (ROOT / "GIT_SCOPE.json").write_text(
        json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
