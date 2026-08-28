from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P654-01_standalone.tex")
EXCLUDED = {"PRETEX_FAILURE_MANIFEST.json", "PRETEX_FAILURE_SEAL.json", "WRITE_STOPPED"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8-sig"))
assert result["status"] == "BUILD_FAIL_NO_CANDIDATE_PRE_TEX"
assert result["controller_invocation_count"] == 1
assert result["lualatex_invocation_count"] == 0
assert result["pdf_count"] == 0
assert not (ROOT / "DIRECT_INVOCATION_START.json").exists()
assert not (ROOT / "DIRECT_INVOCATION_RESULT.json").exists()
assert not list((ROOT / "build").glob("*.pdf"))
assert sha256(SOURCE) == result["source_sha256"]
assert sha256(WRAPPER) == result["wrapper_sha256"]
assert sha256(ROOT / "run_direct_lualatex_once.ps1") == result["controller_sha256"]

cache_artifacts = [
    path.relative_to(ROOT).as_posix()
    for path in ROOT.rglob("*")
    if path.name == "__pycache__" or path.suffix == ".pyc"
]
assert not cache_artifacts

entries: list[dict[str, object]] = []
for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
    rel = path.relative_to(ROOT).as_posix()
    if rel in EXCLUDED:
        continue
    stat = path.stat()
    entries.append(
        {
            "relative_path": rel,
            "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256(path),
        }
    )

write_json(
    ROOT / "PRETEX_FAILURE_MANIFEST.json",
    {"generated_at_utc": now(), "payload_file_count": len(entries), "entries": entries},
)
seal = {
    "status": "BUILD_FAIL_NO_CANDIDATE_PRE_TEX_SEALED",
    "sealed_at_utc": now(),
    "manifest_sha256": sha256(ROOT / "PRETEX_FAILURE_MANIFEST.json"),
    "source_sha256": sha256(SOURCE),
    "wrapper_sha256": sha256(WRAPPER),
    "controller_sha256": sha256(ROOT / "run_direct_lualatex_once.ps1"),
    "controller_invocation_count": 1,
    "lualatex_invocation_count": 0,
    "pdf_count": 0,
    "build_slot_released": True,
}
write_json(ROOT / "PRETEX_FAILURE_SEAL.json", seal)
write_json(
    ROOT / "WRITE_STOPPED",
    {
        "status": "WRITE_STOPPED",
        "written_at_utc": now(),
        "seal_sha256": sha256(ROOT / "PRETEX_FAILURE_SEAL.json"),
        "instruction": "R9 pre-TeX failure root is immutable. No further writes are permitted.",
    },
)
print(json.dumps(seal))
