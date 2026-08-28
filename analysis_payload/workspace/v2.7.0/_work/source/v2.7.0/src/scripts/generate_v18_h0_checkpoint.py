"""Generate the one-time v1.8.0 H0 manifest from preserved v1.7.0 inputs."""

from __future__ import annotations

import hashlib
import platform
from datetime import datetime, timezone
from pathlib import Path


V18 = Path(__file__).resolve().parents[1]
WORKSPACE = V18.parents[1]
OUTPUT = V18 / "qa" / "hash" / "H0_v1.7.0_baseline.sha256"

EXCLUDED_COMPONENTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "hashes",
    "哈希",
}
EXCLUDED_SUFFIXES = {
    ".aux",
    ".xdv",
    ".fls",
    ".fdb_latexmk",
    ".toc",
    ".out",
    ".idx",
    ".ind",
    ".ilg",
    ".synctex.gz",
    ".pdf",
}


def excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_COMPONENTS or part.startswith(".slbuild-") for part in relative.parts):
        return True
    lower = relative.name.lower()
    return any(lower.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def add_tree(files: set[Path], root: Path) -> None:
    if not root.is_dir():
        raise FileNotFoundError(root)
    for path in root.rglob("*"):
        if path.is_file() and not excluded(path.relative_to(root)):
            files.add(path.absolute())


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def find_one(directory: Path, pattern: str) -> Path:
    matches = [path for path in directory.glob(pattern) if path.is_file()]
    if len(matches) != 1:
        raise RuntimeError(f"expected one file for {pattern!r} under {directory}, found {len(matches)}")
    return matches[0]


def main() -> int:
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to recompute one-time checkpoint: {OUTPUT}")

    delivery = WORKSPACE / "v1.7.0_交付"
    source_matches = [
        path
        for path in delivery.iterdir()
        if path.is_dir() and path.name.endswith("_v1.7.0_LaTeX源码")
    ]
    if len(source_matches) != 1:
        raise RuntimeError(f"expected one preserved v1.7.0 source tree, found {len(source_matches)}")
    source_root = source_matches[0]

    authority_inputs = [
        WORKSPACE / "统计学习方法讲义_v1.7.0_全书审校报告.md",
        WORKSPACE / "统计学习方法讲义_v1.7.0_问题清单.csv",
        WORKSPACE / "统计学习方法讲义_LaTeX改进方案_编译预览.pdf",
    ]
    for path in authority_inputs:
        if not path.is_file():
            raise FileNotFoundError(path)

    baseline_pdf = V18 / "baseline-build" / "merged_full" / "main_full.pdf"
    if not baseline_pdf.is_file():
        raise FileNotFoundError(baseline_pdf)

    files: set[Path] = set()
    add_tree(files, source_root)
    files.update(path.absolute() for path in authority_inputs)
    files.add(baseline_pdf.absolute())
    ordered = sorted(files, key=lambda path: path.relative_to(WORKSPACE).as_posix())

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# checkpoint: H0",
        f"# generated_at: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        f"# algorithm: SHA-256 ({hashlib.__name__})",
        f"# tool: Python {platform.python_version()}",
        "# scope: preserved v1.7.0 source tree; three authority inputs; clean baseline PDF; build entry and scripts",
        "# verification_base: workspace root",
        f"# preserved_source_root: {source_root.relative_to(WORKSPACE).as_posix()}",
        f"# baseline_pdf: {baseline_pdf.relative_to(WORKSPACE).as_posix()}",
        "# ordering: relative POSIX path, ordinal ascending",
        "# exclusions: .git, caches, historical hash manifests, .slbuild-*, LaTeX auxiliary files, PDFs inside source tree, manifest itself",
        f"# file_count: {len(ordered)}",
    ]
    for path in ordered:
        lines.append(f"{digest(path)}  {path.relative_to(WORKSPACE).as_posix()}")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"H0 PASS files={len(ordered)} output={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

