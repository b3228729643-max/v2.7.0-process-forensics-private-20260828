from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED = PROJECT_ROOT / "qa" / "source_cache" / "issue_ledger_seed.json"
OUTPUT_DIR = PROJECT_ROOT / "qa" / "context" / "task_packets"


CONFIG = {
    "a": {
        "title": "基础、前置结构与第1—11章",
        "branch": "codex/phase2-agent-a",
        "worktree": ".worktrees/agent_a",
        "chapters": set(range(1, 12)),
        "global_ids": {"ISS-001", "ISS-002", "ISS-003", "ISS-004", "ISS-005"},
        "allowed": [
            "src/讲义源码/合并总册/*.tex",
            "src/讲义源码/common/foundation_routes.tex",
            "src/讲义源码/common/references-body.tex",
            "src/讲义源码/第01册_数学基础与统计学习基本理论/main.tex",
            "src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/*.tex",
            "logs/subagent_a_handoff.md",
        ],
        "focus": "删除前置诊断/参考资料入口、移动符号索引、把C1—C12移出首次阅读路径，并按依赖顺序补足第1—11章概念桥和台账问题。",
        "test": "运行精确关键词残留检查；对第01册做一次目标分册编译（若外部超时，保留日志并停止重试）。",
    },
    "b": {
        "title": "第12—23章监督学习与序列模型",
        "branch": "codex/phase2-agent-b",
        "worktree": ".worktrees/agent_b",
        "chapters": set(range(12, 24)),
        "global_ids": set(),
        "allowed": [
            "src/讲义源码/第02册_基础监督学习方法/main.tex",
            "src/讲义源码/第02册_基础监督学习方法/chapters/*.tex",
            "src/讲义源码/第03册_优化模型与序列模型/main.tex",
            "src/讲义源码/第03册_优化模型与序列模型/chapters/*.tex",
            "logs/subagent_b_handoff.md",
        ],
        "focus": "直接修复第12—23章数学问题，补模型认识卡与必要概念桥，重写核心/高风险例题，并把算法正文压缩为数学层、工程契约改为短条带。",
        "test": "运行本范围标签/引用/问题关键词定向检查；分别对第02、03册做目标分册编译（外部超时只记录一次）。",
    },
    "c": {
        "title": "第24—37章无监督、采样、主题模型与图排序",
        "branch": "codex/phase2-agent-c",
        "worktree": ".worktrees/agent_c",
        "chapters": set(range(24, 38)),
        "global_ids": set(),
        "allowed": [
            "src/讲义源码/第04册_无监督学习与矩阵分解/main.tex",
            "src/讲义源码/第04册_无监督学习与矩阵分解/chapters/*.tex",
            "src/讲义源码/第05册_采样方法主题模型与图排序/main.tex",
            "src/讲义源码/第05册_采样方法主题模型与图排序/chapters/*.tex",
            "logs/subagent_c_handoff.md",
        ],
        "focus": "直接修复第24—37章数学与方向约定，补概念桥和核心例题，分离算法数学层/工程层，重点完成SVD零秩、MH坐标核、LDA多启动与第37章评估协议。",
        "test": "运行本范围标签/引用/问题关键词定向检查；分别对第04、05册做目标分册编译（外部超时只记录一次）。",
    },
}


def issue_chapter(row: dict) -> int | None:
    raw = str(row.get("章", "")).strip()
    return int(raw) if raw.isdigit() else None


def selected_rows(rows: list[dict], config: dict) -> list[dict]:
    return [
        row
        for row in rows
        if issue_chapter(row) in config["chapters"] or row["ID"] in config["global_ids"]
    ]


def render_packet(agent: str, config: dict, rows: list[dict]) -> str:
    allowed = "\n".join(f"- `{path}`" for path in config["allowed"])
    issue_ids = ", ".join(row["ID"] for row in rows)
    issue_blocks = []
    for row in rows:
        issue_blocks.append(
            "\n".join(
                [
                    f"### {row['ID']} · {row['严重度']} · 第{row.get('章') or '全书'}章/范围",
                    f"- 对象：{row['章节/对象']}",
                    f"- 问题：{row['问题']}",
                    f"- 修改动作：{row['修改方案']}",
                    f"- 验收：{row['验收标准']}",
                ]
            )
        )
    return f"""# Subagent {agent.upper()} 任务包

## 任务身份

- 范围：{config['title']}
- 分支：`{config['branch']}`
- worktree：`{config['worktree']}`
- 问题数：{len(rows)}
- 问题 ID：{issue_ids}

## 必须实际完成

{config['focus']}

这不是第二轮全书审计。只读取下列台账行和自己拥有的源码，定位后立即修改；不得创建新的问题编号或新的问题工作簿。

## 允许编辑

{allowed}

## 禁止编辑

- `qa/context/**`、`qa/*.xlsx`、`qa/source_cache/**`、`manifests/**`、`.codex/**`
- `src/讲义源码/common/statlearnbook.sty`、`src/build.ps1`、所有绘图源码
- 其他 Agent 的分册/章节文件

若必须修改禁止文件，只在 handoff 中写出最小补丁建议，由主线程决定，不得直接编辑。

## 权威输入与最小读取范围

- `manifests/MASTER_PROMPT_v2.0.0.md`：只读与本范围相关的第8—13、16、18节。
- `qa/source_cache/issue_ledger_seed.json`：只读取本包列出的 ID。
- `qa/source_cache/report_v1.9.0.json`：仅在台账行需要补充定位时读取相关节。
- `qa/context/PROJECT_CHARTER.md`、本任务包、根 `AGENTS.md`。

## 局部验证

{config['test']}

禁止完整合并总册构建、H0/H1/H2、全书渲染、原工作簿重读和全仓库重复发现型扫描。

## 交付

1. 在自己的分支提交实际源码修改；提交信息含阶段、章节范围、代表问题 ID。
2. 写 `logs/subagent_{agent}_handoff.md`，列出修改文件、解决 ID、概念桥、重写例题、算法分层、测试、失败证据和主线程待决事项。
3. handoff 必须明确“已修改/已测试/未测试”，不得把定位或建议当作完成。

## 本包问题行

{chr(10).join(issue_blocks)}
"""


def main() -> None:
    payload = json.loads(SEED.read_text(encoding="utf-8"))
    rows = payload["rows"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    claimed: set[str] = set()
    summary: dict[str, dict] = {}
    for agent, config in CONFIG.items():
        scoped = selected_rows(rows, config)
        overlap = claimed.intersection(row["ID"] for row in scoped)
        if overlap:
            raise RuntimeError(f"overlapping issue assignment: {sorted(overlap)}")
        claimed.update(row["ID"] for row in scoped)
        (OUTPUT_DIR / f"subagent_{agent}.md").write_text(
            render_packet(agent, config, scoped), encoding="utf-8", newline="\n"
        )
        summary[agent] = {
            "branch": config["branch"],
            "worktree": config["worktree"],
            "issue_count": len(scoped),
            "issue_ids": [row["ID"] for row in scoped],
        }
    (OUTPUT_DIR / "assignment_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
