#!/usr/bin/env python3
"""Generate the one-time H1 or H2 SHA-256 checkpoint for v1.8.0."""

from __future__ import annotations

import argparse
import hashlib
import platform
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_COMPONENTS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
}
GENERATED_SUFFIXES = {
    ".aux", ".xdv", ".fls", ".fdb_latexmk", ".toc", ".out",
    ".idx", ".ind", ".ilg", ".synctex.gz",
}


def excluded(path: Path) -> bool:
    if any(part in GENERATED_COMPONENTS or part.startswith(".slbuild-") for part in path.parts):
        return True
    lower = path.name.lower()
    return any(lower.endswith(suffix) for suffix in GENERATED_SUFFIXES)


def add_tree(files: set[Path], root: Path) -> None:
    if not root.is_dir():
        raise FileNotFoundError(root)
    for path in root.rglob("*"):
        if path.is_file() and not excluded(path.relative_to(root)):
            files.add(path.resolve())


def h1_files() -> list[Path]:
    files: set[Path] = set()
    add_tree(files, ROOT / "讲义源码")
    add_tree(files, ROOT / "绘图源码")
    add_tree(files, ROOT / "qa" / "gates" / "G1")
    add_tree(files, ROOT / "qa" / "gates" / "G2")
    for path in (ROOT / "audit").iterdir():
        if (
            path.is_file()
            and path.suffix.lower() in {".md", ".csv", ".xlsx"}
            and not path.name.startswith("v1.8.0_完成性审计_")
        ):
            files.add(path.resolve())
    for path in (ROOT / "tests").glob("*.py"):
        files.add(path.resolve())
    for path in (
        ROOT / "build.ps1",
        ROOT / "qa" / "run_g1_gate.py",
        ROOT / "qa" / "run_g2_gate.py",
        ROOT / "qa" / "static_source_audit.py",
        ROOT / "qa" / "link_and_label_audit.py",
        ROOT / "qa" / "pdf_layout_audit.py",
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
        files.add(path.resolve())
    for directory, stem in (
        (ROOT / "candidate-build" / "merged_full", "main_full"),
        (ROOT / "candidate-build" / "volume1", "main"),
        (ROOT / "candidate-build" / "volume2", "main"),
        (ROOT / "candidate-build" / "volume3", "main"),
        (ROOT / "candidate-build" / "volume4", "main"),
        (ROOT / "candidate-build" / "volume5", "main"),
    ):
        for suffix in (".pdf", ".log"):
            path = directory / f"{stem}{suffix}"
            if not path.is_file():
                raise FileNotFoundError(path)
            files.add(path.resolve())
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def release_files(release_root: Path, output: Path) -> list[Path]:
    files = []
    for path in release_root.rglob("*"):
        if not path.is_file() or path.resolve() == output.resolve():
            continue
        if excluded(path.relative_to(release_root)):
            continue
        files.append(path.resolve())
    return sorted(files, key=lambda path: path.relative_to(release_root).as_posix())


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", choices=("H1", "H2"))
    parser.add_argument("--release-root", type=Path)
    args = parser.parse_args()

    if args.checkpoint == "H1":
        base = ROOT
        output = ROOT / "qa" / "hash" / "H1_v1.8.0_candidate.sha256"
        files = h1_files()
        scope = "frozen source; six candidate PDFs; build logs; closure table; G1/G2 automation evidence"
    else:
        if args.release_root is None:
            parser.error("H2 requires --release-root")
        base = args.release_root.resolve()
        output = base / "qa" / "hash" / "H2_v1.8.0_release.sha256"
        files = release_files(base, output)
        scope = "final v1.8.0 release directory"

    if output.exists():
        raise FileExistsError(f"refusing to recompute one-time checkpoint: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# checkpoint: {args.checkpoint}",
        f"# generated_at: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        f"# algorithm: SHA-256 ({hashlib.__name__})",
        f"# tool: Python {platform.python_version()}",
        f"# scope: {scope}",
        "# ordering: relative POSIX path, ordinal ascending",
        "# exclusions: .git, caches, .slbuild-*, LaTeX auxiliary files, manifest itself",
        f"# file_count: {len(files)}",
    ]
    for path in files:
        relative = path.relative_to(base).as_posix()
        lines.append(f"{digest(path)}  {relative}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{args.checkpoint} PASS files={len(files)} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
