#!/usr/bin/env python3
"""Freeze the completed one-page R6 build and capture build/source scope."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = Path("src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex")
SOURCE = WORKTREE / SOURCE_REL
WRAPPER = ROOT / "local_wrapper_r6_worktree.tex"
PDF = ROOT / "local_build_direct_r6" / "local_wrapper_r6_worktree.pdf"
LOG = ROOT / "local_build_direct_r6" / "local_wrapper_r6_worktree.log"
START = ROOT / "BUILD_START_ATTESTATION.json"
HANDOFF_ID = "A-R99-P608-SA2-NARROW-20260825"
SA2_ROUTE = "SA2=gpt-5.6-sol/max"
BASELINE_HEAD = "e392bd8e5f37dfd49f071f7251c281d46bb68ffd"
SLOT_TOKEN = "A_P608_BUILD_SLOT_GRANTED_AFTER_CANDIDATE"
EXACT_INSERTIONS = (
    "+  ylabel style={rotate=-90,anchor=east,at={(axis description cs:-0.12,0.5)}},",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", str(WORKTREE), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-exit-code", type=int, required=True)
    args = parser.parse_args()
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("WRITE_STOPPED exists; no evidence write is permitted")
    if args.build_exit_code != 0:
        raise RuntimeError("cannot freeze a failed local build")
    for path in (SOURCE, WRAPPER, PDF, LOG, START):
        if not path.is_file():
            raise RuntimeError(f"required candidate artifact missing: {path}")

    start = json.loads(START.read_text(encoding="utf-8"))
    if (
        start.get("handoff_id") != HANDOFF_ID
        or start.get("sa2_route") != SA2_ROUTE
        or start.get("slot_token") != SLOT_TOKEN
        or start.get("tex_processes_before") != "NONE"
        or start.get("running_tex_processes") != []
    ):
        raise RuntimeError("build-start token/process attestation is not exact")

    head = git("rev-parse", "HEAD").strip()
    changed = [line.strip() for line in git("diff", "--name-only").splitlines() if line.strip()]
    status = [line for line in git("status", "--porcelain=v1").splitlines() if line.strip()]
    numstat_lines = [line for line in git("diff", "--numstat", "--", SOURCE_REL.as_posix()).splitlines() if line.strip()]
    diff_text = git("diff", "--", SOURCE_REL.as_posix())
    diff_check = git("diff", "--check")
    if head != BASELINE_HEAD:
        raise RuntimeError(f"unexpected HEAD: {head}")
    if changed != [SOURCE_REL.as_posix()]:
        raise RuntimeError(f"source scope is not singular: {changed}")
    if len(status) != 1 or not status[0].startswith(" M ") or status[0][3:] != SOURCE_REL.as_posix():
        raise RuntimeError(f"unexpected porcelain status: {status}")
    if len(numstat_lines) != 1:
        raise RuntimeError(f"unexpected numstat: {numstat_lines}")
    insertion_text, deletion_text, path_text = numstat_lines[0].split("\t", 2)
    if (insertion_text, deletion_text, path_text) != ("1", "0", SOURCE_REL.as_posix()):
        raise RuntimeError(f"unexpected source numstat: {numstat_lines[0]}")
    added = [line for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed = [line for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---")]
    if added != list(EXACT_INSERTIONS) or removed:
        raise RuntimeError(f"unexpected source patch: added={added!r}, removed={removed!r}")
    if diff_check.strip():
        raise RuntimeError(f"git diff --check failed: {diff_check}")

    log_text = LOG.read_text(encoding="utf-8", errors="replace")
    hard_patterns = (
        r"^! ", r"LaTeX Error", r"Undefined control sequence", r"Emergency stop",
        r"Fatal error", r"no output PDF file produced",
    )
    hard_count = sum(len(re.findall(pattern, log_text, flags=re.MULTILINE | re.IGNORECASE)) for pattern in hard_patterns)
    undefined_count = len(re.findall(r"Undefined control sequence", log_text, flags=re.IGNORECASE))
    overfull_count = len(re.findall(r"Overfull \\[hv]box", log_text))
    underfull_count = len(re.findall(r"Underfull \\[hv]box", log_text))
    root_cache_line_count = len(re.findall(r"Root cache directory is", log_text))

    doc = fitz.open(PDF)
    page_count = doc.page_count
    page_rect = doc[0].rect if page_count else fitz.Rect()
    doc.close()
    a4 = abs(page_rect.width - 595.276) <= 0.6 and abs(page_rect.height - 841.89) <= 0.6
    if page_count != 1 or not a4 or hard_count or undefined_count or overfull_count or underfull_count or root_cache_line_count < 1:
        raise RuntimeError(
            f"build gate failed: pages={page_count}, size={page_rect}, hard={hard_count}, "
            f"undefined={undefined_count}, overfull={overfull_count}, underfull={underfull_count}, "
            f"root_cache_lines={root_cache_line_count}"
        )

    captured_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    build_validation = {
        "handoff_id": HANDOFF_ID,
        "sa2_route": SA2_ROUTE,
        "slot_token": SLOT_TOKEN,
        "captured_at": captured_at,
        "build_command": "D:/texlive/2026/bin/windows/lualatex.exe -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=<R6>/local_build_direct_r6 <R6>/local_wrapper_r6_worktree.tex",
        "successful_method": {
            "engine": "D:/texlive/2026/bin/windows/lualatex.exe",
            "cwd": "D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/worktrees/dialogue_A_visual/src/讲义源码/合并总册",
            "output_directory": str(ROOT / "local_build_direct_r6"),
            "texmfvar": str(ROOT / "texcache"),
            "texmfcache": str(ROOT / "texcache"),
            "texmfconfig": str(ROOT / "texcache"),
            "direct_single_engine_run": True,
            "latexmk_used": False,
        },
        "failed_cache_bootstrap_attempts": [
            {"attempt": 1, "exit_code": 12, "method": "latexmk; default cache", "failure": "luaotfload no writeable cache path before source"},
            {"attempt": 2, "exit_code": 12, "method": "latexmk; three absolute R6 cache directories", "failure": "luaotfload no writeable cache path before source"},
            {"attempt": 3, "exit_code": 12, "method": "latexmk; three cache directories through ASCII junction", "failure": "luaotfload no writeable cache path before source"},
            {"attempt": 4, "exit_code": 12, "method": "require_escalated latexmk; three cache directories through ASCII junction", "failure": "luaotfload no writeable cache path before source"},
        ],
        "rejected_layout_trials": [
            {"trial": "direct_r1", "reason": "requested rotate=0 did not cancel PGFPlots default +90 rotation and the ylabels collided with adjacent y ticks"},
            {"trial": "direct_r2", "reason": "xshift followed the rotated local coordinate and moved ylabels down instead of left"},
            {"trial": "direct_r3", "reason": "bottom ylabel right edge exceeded nearest tick left edge by 0.80pt"},
            {"trial": "direct_r4", "reason": "position clearance passed, but full raw-mask audit proved rotate=0 was cumulative no-op and both natural-script t glyphs remained 10px high"},
        ],
        "rejected_wrapper_trials": [
            {"trial": "direct_r5", "reason": "layout repair passed rawdict, but the evidence wrapper redundantly overrode statlearnbook's official Noto Serif SC main font with Noto Sans SC; candidate rejected before final audit"},
        ],
        "build_scope": "one_page_local_wrapper",
        "exit_code": args.build_exit_code,
        "pdf_page_count": page_count,
        "page_width_pt": round(page_rect.width, 4),
        "page_height_pt": round(page_rect.height, 4),
        "a4_page_size": a4,
        "hard_diagnostic_count": hard_count,
        "undefined_control_sequence_count": undefined_count,
        "overfull_count": overfull_count,
        "underfull_count": underfull_count,
        "root_cache_line_count": root_cache_line_count,
        "tex_processes_before": start["tex_processes_before"],
        "running_tex_processes_before": start["running_tex_processes"],
        "local_only": True,
        "full_book_build": False,
    }
    source_scope = {
        "handoff_id": HANDOFF_ID,
        "baseline_head": BASELINE_HEAD,
        "current_head": head,
        "changed_paths": changed,
        "porcelain_status": status,
        "insertions": int(insertion_text),
        "deletions": int(deletion_text),
        "exact_inserted_lines": list(EXACT_INSERTIONS),
        "only_allowed_source_changed": True,
        "common_files_changed": False,
        "other_source_files_changed": False,
        "git_diff_check": "PASS",
    }
    freeze = {
        "handoff_id": HANDOFF_ID,
        "sa2_route": SA2_ROUTE,
        "frozen_at": captured_at,
        "scope": "one-page local wrapper; not an official full-book candidate",
        "slot_token": SLOT_TOKEN,
        "pdf": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": digest(PDF),
        "source": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": digest(SOURCE),
        "wrapper": str(WRAPPER),
        "wrapper_bytes": WRAPPER.stat().st_size,
        "wrapper_sha256": digest(WRAPPER),
        "baseline_head": BASELINE_HEAD,
        "source_diff": {"path": SOURCE_REL.as_posix(), "insertions": 1, "deletions": 0, "exact_insertions": list(EXACT_INSERTIONS)},
        "local_only": True,
        "official_candidate": False,
    }
    write_json(ROOT / "BUILD_VALIDATION.json", build_validation)
    write_json(ROOT / "SOURCE_SCOPE_VALIDATION.json", source_scope)
    write_json(ROOT / "LOCAL_CANDIDATE_FREEZE.json", freeze)


if __name__ == "__main__":
    main()
