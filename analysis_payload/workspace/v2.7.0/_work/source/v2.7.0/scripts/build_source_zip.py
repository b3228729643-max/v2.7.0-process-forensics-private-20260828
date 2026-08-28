#!/usr/bin/env python3
"""Build the deterministic source release archive.

The archive contains the complete rebuildable source and project metadata, but
not generated PDFs, build outputs, render caches, execution state, or Git
metadata. It is generated only after the final build passes.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path, PurePosixPath
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION_PATH = ROOT / "manifests" / "release_version.tex"
RELEASE_DEFINITION_PATTERN = re.compile(
    r"\\newcommand\s*\{\\SLReleaseVersion\}\s*"
    r"\{(?P<version>v\d+\.\d+\.\d+)\}"
)
RELEASE_COMMAND_PATTERN = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand)\s*\{\\SLReleaseVersion\}"
)


def read_release_version() -> str:
    r"""Return the single active ``\SLReleaseVersion`` manifest value."""
    source = RELEASE_VERSION_PATH.read_text(encoding="utf-8")
    active_source = "\n".join(line.split("%", 1)[0] for line in source.splitlines())
    definitions = RELEASE_COMMAND_PATTERN.findall(active_source)
    matches = RELEASE_DEFINITION_PATTERN.findall(active_source)
    release_tokens = re.findall(r"\\SLReleaseVersion\b", active_source)
    if len(definitions) != 1 or len(matches) != 1 or len(release_tokens) != 1:
        raise RuntimeError(
            "release_version.tex must contain exactly one active "
            r"\newcommand{\SLReleaseVersion}{vX.Y.Z} definition"
        )
    return matches[0]


RELEASE_VERSION = read_release_version()
ARCHIVE_NAME = f"统计学习方法讲义_{RELEASE_VERSION}_LaTeX源码.zip"
README_NAME = f"README_{RELEASE_VERSION}.md"
BUILD_SCRIPT_NAME = f"build_{RELEASE_VERSION}.ps1"
RELEASE_PDF_NAME = f"统计学习方法初学者讲义_合并总册{RELEASE_VERSION}_完整解析版.pdf"
ARCHIVE = ROOT.parent.parent.parent / ARCHIVE_NAME
PREFIX = PurePosixPath(RELEASE_VERSION)

TOP_LEVEL_FILES = (
    "AGENTS.md",
    README_NAME,
    BUILD_SCRIPT_NAME,
)
RELEASE_FILES = (
    "figures/figure_manifest.csv",
    "manifests/release_version.tex",
    "manifests/v2.3.1_figure_implementation_status.csv",
    "manifests/v2.3.1_figure_source_map.csv",
    "scripts/audit_pdf_navigation.py",
    "scripts/build_source_zip.py",
    "scripts/verify_source_zip.py",
    "styles/README.md",
    "styles/figure-style-v2.3.1.tex",
)
SOURCE_TREES = (
    "src/讲义源码",
    "src/绘图源码",
)
EXCLUDED_PARTS = {
    ".git",
    ".worktrees",
    "__pycache__",
    "build",
    "build-output",
    "legacy",
    "node_modules",
    "previews",
    "rendered",
    "tmp",
    "work_state",
}
EXCLUDED_SUFFIXES = (
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".idx",
    ".ilg",
    ".ind",
    ".log",
    ".out",
    ".pdf",
    ".run.xml",
    ".synctex.gz",
    ".toc",
)

MERGED_SOURCE_DIRECTORY = PurePosixPath("src/讲义源码/合并总册")
MERGED_RELEASE_ENTRIES = {"main.tex", "main_full.tex", "main_student.tex"}
LEGACY_COMMON_ENTRIES = {"figure-style-v2.3.0.tex", "template_demo.tex"}


def include_file(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    rel_posix = PurePosixPath(rel.as_posix())
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return False
    if any(part.startswith(".slbuild-") for part in rel.parts):
        return False
    if path.name in {ARCHIVE.name, RELEASE_PDF_NAME, "SHA256SUMS.txt"}:
        return False
    if path.name.startswith(("figure_batch_v250_", "example_batch_v250_", "knowledge_batch_v250_")):
        return False
    if path.name == "figure_integration_harness.tex":
        return False
    if rel_posix.parent == MERGED_SOURCE_DIRECTORY and path.name not in MERGED_RELEASE_ENTRIES:
        return False
    if rel_posix.parent == PurePosixPath("src/讲义源码/common") and path.name in LEGACY_COMMON_ENTRIES:
        return False
    lower = path.name.lower()
    return not any(lower.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def collect_files() -> list[Path]:
    files: set[Path] = set()
    for name in TOP_LEVEL_FILES:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(f"required release file missing: {path}")
        files.add(path)
    for name in RELEASE_FILES:
        path = ROOT / PurePosixPath(name)
        if not path.is_file():
            raise FileNotFoundError(f"required release file missing: {path}")
        files.add(path)
    for tree_name in SOURCE_TREES:
        tree = ROOT / tree_name
        if not tree.is_dir():
            raise FileNotFoundError(f"required release tree missing: {tree}")
        files.update(path for path in tree.rglob("*") if path.is_file() and include_file(path))
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def write_archive(files: list[Path]) -> None:
    temp = ARCHIVE.with_suffix(ARCHIVE.suffix + ".tmp")
    if temp.exists():
        temp.unlink()
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            relative = PurePosixPath(path.relative_to(ROOT).as_posix())
            archive_name = str(PREFIX / relative)
            info = zipfile.ZipInfo(archive_name, date_time=(2026, 8, 13, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            with path.open("rb") as handle:
                zf.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    os.replace(temp, ARCHIVE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate and list the release set without creating the archive",
    )
    args = parser.parse_args()
    files = collect_files()
    if args.check:
        print(f"SOURCE_FILES={len(files)}")
        print("RELEASE_SET=PASS")
        return 0
    write_archive(files)
    with zipfile.ZipFile(ARCHIVE) as zf:
        bad = zf.testzip()
        entries = len(zf.infolist())
    if bad is not None:
        raise RuntimeError(f"ZIP CRC verification failed at {bad}")
    print(f"SOURCE_ZIP={ARCHIVE}")
    print(f"SOURCE_FILES={len(files)}")
    print(f"ZIP_ENTRIES={entries}")
    print(f"ZIP_BYTES={ARCHIVE.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
