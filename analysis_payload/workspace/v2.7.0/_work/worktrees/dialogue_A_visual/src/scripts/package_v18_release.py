"""Assemble the v1.8.0 deliverables without creating the H2 checkpoint."""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release" / "v1.8.0"
SOURCE_ZIP = RELEASE / "统计学习方法讲义_v1.8.0_完整源码.zip"

PDF_SOURCES = {
    ROOT / "candidate-build" / "merged_full" / "main_full.pdf": RELEASE
    / "统计学习方法初学者讲义_合并总册v1.8.0_完整解析版.pdf",
    ROOT / "candidate-build" / "volume1" / "main.pdf": RELEASE
    / "统计学习方法初学者讲义_第01册_数学基础与统计学习基本理论_v1.8.0_完整解析版.pdf",
    ROOT / "candidate-build" / "volume2" / "main.pdf": RELEASE
    / "统计学习方法初学者讲义_第02册_基础监督学习方法_v1.8.0_完整解析版.pdf",
    ROOT / "candidate-build" / "volume3" / "main.pdf": RELEASE
    / "统计学习方法初学者讲义_第03册_优化模型与序列模型_v1.8.0_完整解析版.pdf",
    ROOT / "candidate-build" / "volume4" / "main.pdf": RELEASE
    / "统计学习方法初学者讲义_第04册_无监督学习与矩阵分解_v1.8.0_完整解析版.pdf",
    ROOT / "candidate-build" / "volume5" / "main.pdf": RELEASE
    / "统计学习方法初学者讲义_第05册_采样方法主题模型与图排序_v1.8.0_完整解析版.pdf",
}

DENIED_SUFFIXES = {
    ".aux",
    ".fdb_latexmk",
    ".fls",
    ".idx",
    ".ilg",
    ".ind",
    ".log",
    ".out",
    ".pdf",
    ".synctex.gz",
    ".toc",
    ".xdv",
}
TEXT_SUFFIXES = {
    ".bib",
    ".cfg",
    ".cls",
    ".csv",
    ".def",
    ".ini",
    ".json",
    ".lua",
    ".md",
    ".ps1",
    ".py",
    ".sty",
    ".tex",
    ".txt",
}
ABSOLUTE_LOCAL_PATH = re.compile(
    r"(?i)(?:C|D):[\\/](?:Users|Windows|texlive|Program Files)(?:[\\/]|$)"
)


def copy_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if source.stat().st_size != destination.stat().st_size:
        raise RuntimeError(f"copy size mismatch: {source} -> {destination}")


def is_source_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts):
        return False
    if any(part.startswith(".slbuild-") for part in path.parts):
        return False
    # Historical drawing README files contain host-specific test commands and
    # are not build inputs. Keep the frozen H1 source untouched and omit them.
    if "绘图源码" in path.parts and path.suffix.lower() == ".md":
        return False
    return path.suffix.lower() not in DENIED_SUFFIXES


def selected_source_files() -> list[tuple[Path, Path]]:
    selected: list[tuple[Path, Path]] = []
    for directory in ["讲义源码", "绘图源码"]:
        source_root = ROOT / directory
        for path in source_root.rglob("*"):
            if is_source_file(path):
                selected.append((path, path.relative_to(ROOT)))

    for directory in ["tests", "qa", "scripts"]:
        source_root = ROOT / directory
        for path in source_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".tex"}:
                selected.append((path, path.relative_to(ROOT)))

    for name in ["build.ps1", "validate.ps1", "README_v1.8.0.md"]:
        path = ROOT / name
        selected.append((path, Path(name)))

    unique: dict[str, tuple[Path, Path]] = {}
    for source, archive_path in selected:
        key = archive_path.as_posix()
        unique[key] = (source, archive_path)
    return [unique[key] for key in sorted(unique)]


def validate_portability(files: list[tuple[Path, Path]]) -> None:
    findings: list[str] = []
    for source, archive_path in files:
        if source.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        if ABSOLUTE_LOCAL_PATH.search(text):
            findings.append(archive_path.as_posix())
    if findings:
        raise RuntimeError("absolute local paths found in source package: " + ", ".join(findings))


def write_deterministic_source_zip(files: list[tuple[Path, Path]]) -> None:
    SOURCE_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SOURCE_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, archive_path in files:
            info = zipfile.ZipInfo(archive_path.as_posix(), date_time=(2026, 8, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def copy_qa_tree() -> None:
    for gate in ["G1", "G2", "G3"]:
        source_root = ROOT / "qa" / "gates" / gate
        destination_root = RELEASE / "qa" / "gates" / gate
        for source in source_root.rglob("*"):
            if not source.is_file() or source.name == "manual-test.png":
                continue
            copy_file(source, destination_root / source.relative_to(source_root))

    copy_file(
        ROOT / "qa" / "hash" / "H0_v1.7.0_baseline.sha256",
        RELEASE / "qa" / "hash" / "H0_v1.7.0_baseline.sha256",
    )
    copy_file(
        ROOT / "qa" / "hash" / "H1_v1.8.0_candidate.sha256",
        RELEASE / "qa" / "hash" / "H1_v1.8.0_candidate.sha256",
    )


def copy_tests() -> None:
    grouped_code = RELEASE / "tests" / "测试代码与日志" / "代码"
    for source in (ROOT / "tests").rglob("*"):
        if source.is_file() and source.suffix.lower() in {".py", ".tex"}:
            relative = source.relative_to(ROOT / "tests")
            copy_file(source, RELEASE / "tests" / relative)
            copy_file(source, grouped_code / relative)
    copy_file(
        ROOT / "qa" / "gates" / "G1" / "full_unittest.log",
        RELEASE / "tests" / "logs" / "G1_full_unittest_228.log",
    )
    copy_file(
        ROOT / "qa" / "gates" / "G3" / "G3_independent_numeric_tests.log",
        RELEASE / "tests" / "logs" / "G3_independent_numeric_tests_24.log",
    )
    copy_file(
        ROOT / "qa" / "gates" / "G1" / "full_unittest.log",
        RELEASE / "tests" / "测试代码与日志" / "日志" / "G1_full_unittest_228.log",
    )
    copy_file(
        ROOT / "qa" / "gates" / "G3" / "G3_independent_numeric_tests.log",
        RELEASE / "tests" / "测试代码与日志" / "日志" / "G3_independent_numeric_tests_24.log",
    )


def copy_explicit_delivery_views() -> None:
    automatic = RELEASE / "qa" / "自动检查结果"
    for gate in ["G1", "G2", "G3"]:
        copy_file(
            ROOT / "qa" / "gates" / gate / f"{gate}_gate_report.json",
            automatic / f"{gate}_gate_report.json",
        )
    for source in [
        ROOT / "qa" / "gates" / "G1" / "full_unittest.log",
        ROOT / "qa" / "gates" / "G2" / "candidate_layout_audit.json",
        ROOT / "qa" / "gates" / "G3" / "G3_independent_numeric_tests.log",
        ROOT / "qa" / "gates" / "G3" / "G3_manual_visual_review.json",
        ROOT / "qa" / "hash" / "H0_v1.7.0_baseline.verify.json",
        ROOT / "qa" / "post_h1" / "authority_preview_compliance.json",
    ]:
        copy_file(source, automatic / source.name)

    visual = RELEASE / "qa" / "视觉回归结果"
    visual_source = ROOT / "qa" / "gates" / "G3" / "visual"
    for source in visual_source.rglob("*"):
        if source.is_file() and source.name != "manual-test.png":
            copy_file(source, visual / source.relative_to(visual_source))
    copy_file(
        ROOT / "qa" / "gates" / "G3" / "G3_manual_visual_review.json",
        visual / "G3_manual_visual_review.json",
    )


def main() -> int:
    RELEASE.mkdir(parents=True, exist_ok=True)
    for source, destination in PDF_SOURCES.items():
        copy_file(source, destination)

    final_closure = ROOT / "outputs" / "g3-closure-final"
    for suffix in [".csv", ".xlsx"]:
        source = final_closure / f"统计学习方法讲义_v1.8.0_问题闭环表{suffix}"
        copy_file(source, RELEASE / source.name)
    copy_file(
        ROOT / "audit" / "v1.8.0_完成性审计_20260810.md",
        RELEASE / "统计学习方法讲义_v1.8.0_完成性审计.md",
    )
    copy_file(
        ROOT / "qa" / "post_h1" / "authority_preview_compliance.md",
        RELEASE / "统计学习方法讲义_v1.8.0_第三权威PDF对照审计.md",
    )

    copy_qa_tree()
    copy_tests()
    copy_explicit_delivery_views()

    source_files = selected_source_files()
    validate_portability(source_files)
    write_deterministic_source_zip(source_files)

    inventory = []
    for path in sorted(RELEASE.rglob("*"), key=lambda item: item.relative_to(RELEASE).as_posix()):
        if path.is_file() and path.name != "release_inventory.json":
            inventory.append(
                {
                    "path": path.relative_to(RELEASE).as_posix(),
                    "bytes": path.stat().st_size,
                }
            )
    report = {
        "schema_version": 1,
        "release": "v1.8.0",
        "status": "final_content_frozen",
        "source_zip_files": len(source_files),
        "source_zip_portability_scan": "passed",
        "h0": "present_and_verified",
        "h1": "present",
        "h2": "manifest_excluded_from_inventory_and_generated_after_content_freeze",
        "files": inventory,
    }
    (RELEASE / "release_inventory.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"release": str(RELEASE), "files": len(inventory) + 1, "source_zip_files": len(source_files)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
