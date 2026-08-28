from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd


WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE.parent
BASELINE = WORKSPACE / "baseline"
BASELINE_SOURCE = WORKSPACE / "baseline_source"
SOURCE = WORKSPACE / "source"
META = WORKSPACE / "meta"
HASHES = WORKSPACE / "hashes"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_text(command: list[str], cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def owner_for(issue_id: str) -> str:
    if issue_id.startswith("G"):
        return "main"
    if not issue_id.startswith("M"):
        return "main"
    number = int(issue_id[1:])
    if number <= 20:
        return "A"
    if number <= 51:
        return "B"
    if number <= 85:
        return "C"
    return "D"


def relative(path: Path) -> str:
    return path.relative_to(WORKSPACE).as_posix()


def validate_and_create_ledger() -> tuple[pd.DataFrame, dict[str, int]]:
    csv_candidates = list(BASELINE.glob("*问题追踪表.csv"))
    if len(csv_candidates) != 1:
        raise RuntimeError(f"Expected one baseline issue CSV, found {csv_candidates!r}")
    frame = pd.read_csv(csv_candidates[0], encoding="utf-8-sig")
    expected = {"P0": 30, "P1": 54, "P2": 37, "P3": 5}
    actual = frame["优先级"].value_counts().to_dict()
    if len(frame) != 126 or actual != expected:
        raise RuntimeError(f"Issue baseline mismatch: rows={len(frame)}, counts={actual}")
    if frame["ID"].isna().any() or not frame["ID"].is_unique:
        raise RuntimeError("Issue IDs must be non-null and unique")

    frame["owner"] = frame["ID"].map(owner_for)
    for column in (
        "physical_source_file",
        "source_line_before",
        "source_line_after",
        "fix_summary",
        "verification_command",
        "verification_evidence",
        "commit_or_patch",
    ):
        frame[column] = ""
    frame["status"] = "todo"
    frame["notes"] = ""
    ledger_path = META / "issue_ledger_v1.7.0.csv"
    frame.to_csv(ledger_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
    return frame, actual


def create_ownership_table(frame: pd.DataFrame) -> None:
    counts = Counter(frame["owner"])
    rows = [
        ("A", "第1-14章", "M001-M020", "第01册全部章节；第02册 V2-C01 至 V2-C03；同章绘图源", "只写所属章节/绘图源；不得写公共宏、入口、台账"),
        ("B", "第15-23章", "M021-M051", "第02册 V2-C04 至 V2-C05；第03册全部章节；同章绘图源", "只写所属章节/绘图源；不得写公共宏、入口、台账"),
        ("C", "第24-34章", "M052-M085", "第04册全部章节；第05册 V5-C01 至 V5-C05；同章绘图源", "只写所属章节/绘图源；不得写公共宏、入口、台账"),
        ("D", "第35-37章", "M086-M106", "第05册 V5-C06 至 V5-C08；同章绘图源", "只写所属章节/绘图源；不得写公共宏、入口、台账"),
        ("main", "全书共享", "G001-G020", "common、各 main.tex、构建脚本、索引、台账、测试与交付", "单写者：仅主线程修改"),
    ]
    lines = [
        "# v1.7.0 物理文件所有权表",
        "",
        "同一物理文件只能有一个写者。第五册按独立章节文件切分：C 仅拥有 V5-C01 至 V5-C05，D 仅拥有 V5-C06 至 V5-C08，因此不存在同文件并发写入。",
        "",
        "| Owner | 章节范围 | 问题范围 | 物理文件范围 | 写入约束 | 台账条数 |",
        "|---|---|---|---|---|---:|",
    ]
    for owner, chapters, issues, files, constraint in rows:
        lines.append(f"| {owner} | {chapters} | {issues} | {files} | {constraint} | {counts[owner]} |")
    lines.extend(
        [
            "",
            "## 共享单写者文件",
            "",
            "- `source/讲义源码/common/`",
            "- `source/讲义源码/*/main.tex`",
            "- `source/验证工具/` 中的全书级脚本",
            "- `meta/issue_ledger_v1.7.0.csv`、`meta/RUN_STATE.json`、`meta/SESSION_JOURNAL.md`",
            "- `hashes/` 与最终交付目录",
            "",
        ]
    )
    (META / "physical_file_ownership.md").write_text("\n".join(lines), encoding="utf-8")


def create_h1() -> list[dict[str, str]]:
    pdf = next(BASELINE.glob("*.pdf"))
    report = next(BASELINE.glob("*优化报告.md"))
    issues = next(BASELINE.glob("*问题追踪表.csv"))
    source_archive = BASELINE / "v1.6.0_source_head.zip"
    main_entry = BASELINE_SOURCE / "讲义源码" / "合并总册" / "main.tex"
    targets = [pdf, report, issues, main_entry, source_archive]
    missing = [str(path) for path in targets if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"H1 inputs missing: {missing}")
    records = [{"sha256": sha256(path), "path": relative(path)} for path in targets]
    lines = [f"{record['sha256']}  {record['path']}" for record in records]
    (HASHES / "H1_baseline.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return records


def tool_record(name: str, args: list[str]) -> dict[str, object]:
    executable = shutil.which(name)
    if executable is None:
        return {"name": name, "available": False, "path": None, "version": None}
    output = run_text([executable, *args])
    return {
        "name": name,
        "available": True,
        "path": executable,
        "version": "\n".join(output.splitlines()[:4]),
    }


def create_inventory(frame: pd.DataFrame, counts: dict[str, int], h1: list[dict[str, str]]) -> None:
    source_files = [path for path in SOURCE.rglob("*") if path.is_file()]
    baseline_files = [path for path in BASELINE.rglob("*") if path.is_file()]
    tools = [
        tool_record("python", ["--version"]),
        tool_record("latexmk", ["-v"]),
        tool_record("xelatex", ["--version"]),
        tool_record("qpdf", ["--version"]),
        tool_record("pdfinfo", ["-v"]),
        tool_record("pdftoppm", ["-v"]),
        tool_record("pdffonts", ["-v"]),
        tool_record("mutool", ["-v"]),
        tool_record("chktex", ["--version"]),
        tool_record("lacheck", ["--version"]),
    ]
    git_head = run_text(["git", "rev-parse", "HEAD"])
    branch = run_text(["git", "branch", "--show-current"])
    inventory = {
        "generated_at": now_iso(),
        "workspace": str(WORKSPACE),
        "delivery": str(WORKSPACE.parent / "v1.7.0_交付"),
        "git_branch": branch,
        "git_head": git_head,
        "selected_baseline_main": relative(BASELINE_SOURCE / "讲义源码" / "合并总册" / "main.tex"),
        "selected_candidate_main": relative(SOURCE / "讲义源码" / "合并总册" / "main.tex"),
        "baseline_file_count": len(baseline_files),
        "candidate_source_file_count": len(source_files),
        "issue_rows": len(frame),
        "severity_counts": counts,
        "h1": h1,
        "tools": tools,
    }
    (META / "inventory.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    tool_lines = []
    for record in tools:
        state = "可用" if record["available"] else "不可用"
        version = str(record["version"] or "").splitlines()[0] if record["version"] else ""
        tool_lines.append(f"| {record['name']} | {state} | {record['path'] or ''} | {version} |")
    lines = [
        "# v1.7.0 阶段 0 文件与环境清单",
        "",
        f"生成时间：{inventory['generated_at']}",
        "",
        "## 权威输入",
        "",
        f"- v1.6.0 PDF：`{relative(next(BASELINE.glob('*.pdf')))}`",
        f"- 审校报告：`{relative(next(BASELINE.glob('*优化报告.md')))}`",
        f"- 126 项 CSV：`{relative(next(BASELINE.glob('*问题追踪表.csv')))}`",
        f"- 基线源码归档：`{relative(BASELINE / 'v1.6.0_source_head.zip')}`",
        f"- 基线主入口：`{inventory['selected_baseline_main']}`",
        f"- 当前候选主入口：`{inventory['selected_candidate_main']}`",
        "",
        "## 基线验证",
        "",
        f"- 行数：{len(frame)}",
        f"- P0/P1/P2/P3：{counts['P0']}/{counts['P1']}/{counts['P2']}/{counts['P3']}",
        f"- ID 唯一且非空：是",
        f"- H1：`hashes/H1_baseline.sha256`（{len(h1)} 个对象）",
        "",
        "## Git 与隔离",
        "",
        f"- 分支：`{branch}`",
        f"- HEAD：`{git_head}`",
        f"- 候选源码文件：{len(source_files)}",
        f"- 基线目录文件：{len(baseline_files)}",
        "",
        "## 工具",
        "",
        "| 工具 | 状态 | 路径 | 版本首行 |",
        "|---|---|---|---|",
        *tool_lines,
        "",
        "说明：系统 PATH 中的 `pdfinfo`/`pdftoppm` 包装器若失效，后续应改用 TeX Live 同目录 Poppler 可执行文件并在测试报告中记录替代路径。",
        "",
    ]
    (WORKSPACE / "inventory.md").write_text("\n".join(lines), encoding="utf-8")


def create_recovery_files(frame: pd.DataFrame) -> None:
    git_head = run_text(["git", "rev-parse", "HEAD"])
    state = {
        "phase": "stage_0_baseline_frozen",
        "baseline_commit": git_head,
        "current_commit": git_head,
        "closed_issue_ids": [],
        "open_issue_ids": frame["ID"].tolist(),
        "blocked_issue_ids": [],
        "last_successful_build": None,
        "next_action": "Audit the isolated candidate source against all 126 ledger rows and record physical source locations.",
        "updated_at": now_iso(),
    }
    (META / "RUN_STATE.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    journal = [
        "# v1.7.0 Session Journal",
        "",
        f"## {now_iso()} - 阶段 0 基线冻结",
        "",
        "- 已验证原始问题表：126 行；P0/P1/P2/P3=30/54/37/5；ID 唯一且非空。",
        "- 已创建 `v1.7.0-refine` 分支，保留进入任务时的未提交候选改动。",
        "- 已隔离复制当前候选源码，并从 Git HEAD 导出 v1.6.0 基线源码归档。",
        "- 已生成 H1、执行台账、物理文件所有权表和恢复状态。",
        "- 下一步：四个章节域并行审计候选源码；主线程审计 G001-G020 与构建基础设施。",
        "",
    ]
    (META / "SESSION_JOURNAL.md").write_text("\n".join(journal), encoding="utf-8")


def main() -> None:
    META.mkdir(parents=True, exist_ok=True)
    HASHES.mkdir(parents=True, exist_ok=True)
    frame, counts = validate_and_create_ledger()
    create_ownership_table(frame)
    h1 = create_h1()
    create_inventory(frame, counts, h1)
    create_recovery_files(frame)
    print(
        json.dumps(
            {
                "status": "ok",
                "rows": len(frame),
                "counts": counts,
                "h1_records": len(h1),
                "ledger": str(META / "issue_ledger_v1.7.0.csv"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
