from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex"
SOURCE = WORKTREE / Path(SOURCE_REL)
PAGE_PDF = ROOT / "build" / "page" / "v260_FIG-P654-01_page.pdf"
STANDALONE_PDF = ROOT / "build" / "standalone" / "v260_FIG-P654-01_standalone.pdf"
R98_PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf"
)

HANDOFF = "A-R130-P654-SA2-REPAIR-V2-20260824"
ROUTE = "LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1"
EXPECTED_HEAD = "e933f09e757d406954edd09f8ce0a326248c7da9"
EXPECTED_R98_SHA = "52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41"
EXPECTED_R98_BYTES = 4_934_249
EXPECTED_R98_PAGES = 813
R98_TARGET_PHYSICAL_PAGE = 702
R98_TARGET_PRINTED_PAGE = "689"
R98_SOURCE_SHA = "01EA85F46A9567D7ED6CF88C92346F9BE317FAFDDCF1F7791C07B2A3ED3858EB"
R98_SA1_TERMINAL_COMMIT = "7f65bd75ce94aee876aa25735e92214bb5ebe004"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalized_text_sha(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def normalized_file_sha(path: Path) -> str:
    return normalized_text_sha(path.read_text(encoding="utf-8"))


def git_text(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=WORKTREE,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def git_nul(*args: str) -> list[str]:
    data = subprocess.run(
        ["git", *args], cwd=WORKTREE, check=True, capture_output=True
    ).stdout
    return [part.decode("utf-8") for part in data.split(b"\0") if part]


if (ROOT / "seal" / "WRITE_STOPPED").exists() or (ROOT / "WRITE_STOPPED").exists():
    raise RuntimeError("sealed package cannot be refrozen")

head = git_text("rev-parse", "HEAD").strip()
branch = git_text("branch", "--show-current").strip()
unstaged = git_nul("diff", "--name-only", "-z")
staged = git_nul("diff", "--cached", "--name-only", "-z")
untracked = git_nul("ls-files", "--others", "--exclude-standard", "-z")
if head != EXPECTED_HEAD:
    raise RuntimeError(f"unexpected HEAD: {head}")
if unstaged != [SOURCE_REL] or staged or untracked:
    raise RuntimeError(
        f"worktree boundary mismatch: unstaged={unstaged!r}, staged={staged!r}, untracked={untracked!r}"
    )

diff_bytes = subprocess.run(
    ["git", "diff", "--binary", "--", SOURCE_REL], cwd=WORKTREE, check=True, capture_output=True
).stdout
numstat = git_text("diff", "--numstat", "--", SOURCE_REL).strip().split("\t")
if len(numstat) != 3 or numstat[2] != SOURCE_REL:
    raise RuntimeError(f"unexpected numstat: {numstat!r}")

base_source = subprocess.run(
    ["git", "show", f"{head}:{SOURCE_REL}"], cwd=WORKTREE, check=True, capture_output=True
).stdout.decode("utf-8")
base_source_sha = normalized_text_sha(base_source)
if base_source_sha != R98_SOURCE_SHA:
    raise RuntimeError(f"R98 source anchor mismatch: {base_source_sha}")

r98_sha = sha256_file(R98_PDF)
r98_doc = fitz.open(R98_PDF)
r98_page = r98_doc[R98_TARGET_PHYSICAL_PAGE - 1]
r98_size = R98_PDF.stat().st_size
r98_identity_pass = (
    r98_sha == EXPECTED_R98_SHA
    and r98_size == EXPECTED_R98_BYTES
    and r98_doc.page_count == EXPECTED_R98_PAGES
    and r98_page.get_label() == R98_TARGET_PRINTED_PAGE
)
if not r98_identity_pass:
    raise RuntimeError("official R98 frozen identity mismatch")

page_doc = fitz.open(PAGE_PDF)
standalone_doc = fitz.open(STANDALONE_PDF)
page = page_doc[0]
standalone = standalone_doc[0]
source_sha = normalized_file_sha(SOURCE)

identity = {
    "figure_uid": "FIG-P654-01",
    "handoff_id": HANDOFF,
    "route_boundary": ROUTE,
    "frozen_utc": datetime.now(timezone.utc).isoformat(),
    "official_r98_frozen_identity": {
        "path": str(R98_PDF),
        "sha256": r98_sha,
        "expected_sha256": EXPECTED_R98_SHA,
        "identity_match": r98_identity_pass,
        "bytes": r98_size,
        "pages": r98_doc.page_count,
        "pdf_target_physical_page": R98_TARGET_PHYSICAL_PAGE,
        "pdf_target_printed_label": r98_page.get_label(),
        "page_size_pt": [r98_page.rect.width, r98_page.rect.height],
        "source_normalized_sha256": R98_SOURCE_SHA,
        "sealed_sa1_terminal_commit_reference": R98_SA1_TERMINAL_COMMIT,
        "note": "Read-only official R98 baseline identity; it does not contain the SA2 source repair.",
    },
    "local_sa2_candidate_identity": {
        "scope": "local page/standalone wrappers on the frozen R98 source baseline; not an official full-book candidate",
        "worktree": str(WORKTREE),
        "branch": branch,
        "base_head": head,
        "source_relative_path": SOURCE_REL,
        "source_path": str(SOURCE),
        "source_normalized_sha256": source_sha,
        "base_source_normalized_sha256": base_source_sha,
        "source_diff_sha256": hashlib.sha256(diff_bytes).hexdigest().upper(),
        "source_diff_numstat": {
            "insertions": int(numstat[0]),
            "deletions": int(numstat[1]),
            "files": 1,
        },
        "only_unstaged_business_source": unstaged,
        "staged_paths": staged,
        "untracked_paths": untracked,
        "commit_deferred_to_root_after_write_stopped": True,
        "page_wrapper": {
            "path": str(PAGE_PDF),
            "sha256": sha256_file(PAGE_PDF),
            "bytes": PAGE_PDF.stat().st_size,
            "pages": page_doc.page_count,
            "printed_label": page.get_label(),
            "page_size_pt": [page.rect.width, page.rect.height],
            "drawing_objects": len(page.get_drawings()),
        },
        "standalone_wrapper": {
            "path": str(STANDALONE_PDF),
            "sha256": sha256_file(STANDALONE_PDF),
            "bytes": STANDALONE_PDF.stat().st_size,
            "pages": standalone_doc.page_count,
            "page_size_pt": [standalone.rect.width, standalone.rect.height],
            "drawing_objects": len(standalone.get_drawings()),
        },
    },
    "final_source_change_summary": [
        "Base labels raised from 9.6 pt to 10.1 pt; formula text set to 11.6 pt, giving 11.6/10.1=1.148514851485 <= 1.18.",
        "Posterior and predictive nodes were restated with semantically equivalent, compact visible wording while retaining alpha+n and the posterior-predictive fraction.",
        "Node sizes and lower interpretation/application branches were re-spaced to preserve legibility and page occupancy.",
        "Posterior and downstream geometry were shifted 0.15 cm right to remove the real families-to-posterior arrowhead/source-border collision without adding a false whitelist.",
        "No public macro, font, chapter, index, build entry, central state, mainline source, Dialogue B, or FINAL_ROOT file was modified.",
    ],
}

out = ROOT / "reports" / "candidate_identity.json"
out.write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "candidate_identity.json").write_text(
    json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(
    json.dumps(
        {
            "status": "FROZEN_LOCAL_SA2_CANDIDATE",
            "source_sha256": source_sha,
            "r98_sha256": r98_sha,
            "base_head": head,
            "diff_numstat": identity["local_sa2_candidate_identity"]["source_diff_numstat"],
        },
        ensure_ascii=False,
    )
)
