from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "seal"
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex"
SOURCE = WORKTREE / Path(SOURCE_REL)
HANDOFF = "A-R130-P654-SA2-REPAIR-V2-20260824"
ROUTE = "LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalized_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


terminal = json.loads((SEAL / "terminal_check.json").read_text(encoding="utf-8"))
manifest_path = SEAL / "MANIFEST.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
identity = json.loads((ROOT / "reports" / "candidate_identity.json").read_text(encoding="utf-8"))
marker = SEAL / "WRITE_STOPPED"
if marker.exists() or (ROOT / "WRITE_STOPPED").exists():
    raise RuntimeError("WRITE_STOPPED already exists")
if terminal.get("terminal_check") != "PASS" or terminal.get("failure_count") != 0:
    raise RuntimeError("terminal is not PASS")
if terminal.get("handoff_id") != HANDOFF or terminal.get("route") != ROUTE:
    raise RuntimeError("terminal identity mismatch")
if manifest.get("terminal_check") != "PASS" or manifest.get("handoff_id") != HANDOFF or manifest.get("route") != ROUTE:
    raise RuntimeError("manifest identity mismatch")

expected = {entry["path"]: entry for entry in manifest["files"]}
actual = {
    path.relative_to(ROOT).as_posix(): path
    for path in ROOT.rglob("*")
    if path.is_file()
    and path.relative_to(ROOT).as_posix() not in {"seal/MANIFEST.json", "seal/WRITE_STOPPED"}
}
if set(actual) != set(expected):
    raise RuntimeError(
        f"post-manifest file-set drift: added={sorted(set(actual)-set(expected))}, missing={sorted(set(expected)-set(actual))}"
    )
for relative, path in actual.items():
    entry = expected[relative]
    if path.stat().st_size != entry["size"] or sha256(path) != entry["sha256"]:
        raise RuntimeError(f"post-manifest byte drift: {relative}")
if len(expected) != manifest["file_count"]:
    raise RuntimeError("manifest file count mismatch")
if sum(entry["size"] for entry in expected.values()) != manifest["total_bytes_before_manifest_and_marker"]:
    raise RuntimeError("manifest total byte count mismatch")

source_sha = normalized_sha(SOURCE)
if source_sha != identity["local_sa2_candidate_identity"]["source_normalized_sha256"]:
    raise RuntimeError("source changed after candidate freeze")
head = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=WORKTREE, check=True, capture_output=True, text=True
).stdout.strip()
unstaged_raw = subprocess.run(
    ["git", "diff", "--name-only", "-z"], cwd=WORKTREE, check=True, capture_output=True
).stdout
staged_raw = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "-z"], cwd=WORKTREE, check=True, capture_output=True
).stdout
unstaged = [part.decode("utf-8") for part in unstaged_raw.split(b"\0") if part]
staged = [part.decode("utf-8") for part in staged_raw.split(b"\0") if part]
if head != identity["local_sa2_candidate_identity"]["base_head"] or unstaged != [SOURCE_REL] or staged:
    raise RuntimeError(f"source boundary drift: head={head}, unstaged={unstaged}, staged={staged}")

report = (ROOT / "reports" / "SA2_REPAIR_REPORT.md").read_text(encoding="utf-8")
if "## Terminal and seal-stage closure" not in report or ROUTE not in report:
    raise RuntimeError("final report was not finalized after terminal")

manifest_sha = sha256(manifest_path)
marker.write_text(
    "\n".join(
        [
            ROUTE,
            HANDOFF,
            f"SOURCE_SHA256={source_sha}",
            f"MANIFEST_SHA256={manifest_sha}",
            f"MANIFEST_FILE_COUNT={manifest['file_count']}",
            f"MANIFEST_TOTAL_BYTES={manifest['total_bytes_before_manifest_and_marker']}",
            "WRITE_STOPPED_ABSOLUTE_LAST",
            "",
        ]
    ),
    encoding="utf-8",
)
print(
    json.dumps(
        {
            "write_stopped": True,
            "route": ROUTE,
            "marker": str(marker),
            "manifest_sha256": manifest_sha,
            "manifest_file_count": manifest["file_count"],
            "manifest_total_bytes": manifest["total_bytes_before_manifest_and_marker"],
        },
        ensure_ascii=False,
    )
)
