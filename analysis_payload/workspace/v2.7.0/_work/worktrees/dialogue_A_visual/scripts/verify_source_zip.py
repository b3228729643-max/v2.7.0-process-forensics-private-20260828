#!/usr/bin/env python3
"""Verify the source ZIP structure and extracted offline build plan."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
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


def read_release_version(root: Path) -> str:
    r"""Return the single active ``\SLReleaseVersion`` value below *root*."""
    manifest = root / "manifests" / "release_version.tex"
    source = manifest.read_text(encoding="utf-8")
    active_source = "\n".join(line.split("%", 1)[0] for line in source.splitlines())
    definitions = RELEASE_COMMAND_PATTERN.findall(active_source)
    matches = RELEASE_DEFINITION_PATTERN.findall(active_source)
    release_tokens = re.findall(r"\\SLReleaseVersion\b", active_source)
    if len(definitions) != 1 or len(matches) != 1 or len(release_tokens) != 1:
        raise RuntimeError(
            f"{manifest} must contain exactly one active "
            r"\newcommand{\SLReleaseVersion}{vX.Y.Z} definition"
        )
    return matches[0]


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


RELEASE_VERSION = read_release_version(ROOT)
ARCHIVE_NAME = f"统计学习方法讲义_{RELEASE_VERSION}_LaTeX源码.zip"
README_NAME = f"README_{RELEASE_VERSION}.md"
BUILD_SCRIPT_NAME = f"build_{RELEASE_VERSION}.ps1"
RELEASE_PDF_NAME = f"统计学习方法初学者讲义_合并总册{RELEASE_VERSION}_完整解析版.pdf"
ARCHIVE_PREFIX = PurePosixPath(RELEASE_VERSION)
ARCHIVE = ROOT.parent.parent.parent / ARCHIVE_NAME
OUTPUT = ROOT.parent.parent.parent / "logs" / "source_zip_verification.json"

EXPECTED_NUMBERED_FIGURES = 99
EXPECTED_UNNUMBERED_FIGURES = 2
EXPECTED_FIGURE_RECORDS = EXPECTED_NUMBERED_FIGURES + EXPECTED_UNNUMBERED_FIGURES


def archive_member(*parts: str) -> str:
    return str(ARCHIVE_PREFIX.joinpath(*parts))


def safe_members(zf: zipfile.ZipFile) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for info in zf.infolist():
        name = info.filename
        path = PurePosixPath(name)
        if (
            not name
            or "\\" in name
            or path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != name
            or re.match(r"^[A-Za-z]:", name)
        ):
            raise RuntimeError(f"unsafe ZIP entry: {name}")
        if not path.parts or path.parts[0] != RELEASE_VERSION:
            raise RuntimeError(f"entry outside {RELEASE_VERSION} prefix: {name}")
        if name in seen:
            raise RuntimeError(f"duplicate ZIP entry: {name}")
        seen.add(name)
        names.append(name)
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="also rebuild the extracted archive from a clean ASCII temporary directory",
    )
    parser.add_argument(
        "--expected-pages",
        type=positive_int,
        help=(
            "expected full-rebuild page count; when supplied, the rebuilt PDF "
            "must match it exactly"
        ),
    )
    args = parser.parse_args()
    if args.expected_pages is not None and not args.full_rebuild:
        parser.error("--expected-pages requires --full-rebuild")
    if not ARCHIVE.is_file():
        raise FileNotFoundError(ARCHIVE)
    full_rebuild = None
    with zipfile.ZipFile(ARCHIVE) as zf:
        names = safe_members(zf)
        bad_crc = zf.testzip()
        if bad_crc is not None:
            raise RuntimeError(f"ZIP CRC verification failed at {bad_crc}")

        forbidden = [
            name for name in names
            if any(
                part in {
                    ".git", ".worktrees", "build", "build-output", "node_modules",
                    "previews", "rendered", "tmp",
                }
                or part.startswith(".slbuild-")
                for part in PurePosixPath(name).parts
            )
        ]
        main_files = [name for name in names if name.endswith("/main_full.tex")]
        chapter_files = [
            name for name in names
            if PurePosixPath(name).name.startswith("V")
            and "-C" in PurePosixPath(name).name
            and name.endswith(".tex")
            and "/chapters/" in name
        ]
        style_files = [name for name in names if name.endswith("/common/statlearnbook.sty")]
        shared_style_files = [name for name in names if name.endswith("/styles/figure-style-v2.3.1.tex")]
        required = [
            archive_member(BUILD_SCRIPT_NAME),
            archive_member(README_NAME),
            archive_member("AGENTS.md"),
            archive_member("figures", "figure_manifest.csv"),
            archive_member("manifests", "release_version.tex"),
            archive_member("manifests", "v2.3.1_figure_source_map.csv"),
            archive_member("manifests", "v2.3.1_figure_implementation_status.csv"),
            archive_member("styles", "figure-style-v2.3.1.tex"),
            archive_member("src", "绘图源码", "前置页", "UFIG-P001-01.tex"),
            archive_member(
                "src",
                "绘图源码",
                "第01册_数学基础与统计学习基本理论",
                "V1-C10",
                "UFIG-P158-01.tex",
            ),
        ]
        missing_required = [name for name in required if name not in names]

        if forbidden or len(main_files) != 1 or len(chapter_files) != 37 or len(style_files) != 1 or len(shared_style_files) != 1 or missing_required:
            raise RuntimeError(
                "source ZIP structural verification failed: "
                f"forbidden={len(forbidden)}, main={len(main_files)}, "
                f"chapters={len(chapter_files)}, styles={len(style_files)}, shared_styles={len(shared_style_files)}, missing={missing_required}"
            )

        with tempfile.TemporaryDirectory(prefix="statlearn-v2-zip-") as temp_name:
            temp = Path(temp_name)
            zf.extractall(temp)
            extracted_root = temp / RELEASE_VERSION
            extracted_release_version = read_release_version(extracted_root)
            if extracted_release_version != RELEASE_VERSION:
                raise RuntimeError(
                    "archive release manifest differs from the verifier manifest: "
                    f"archive={extracted_release_version}, verifier={RELEASE_VERSION}"
                )

            # The implementation-status manifest is the authoritative list of
            # 99 numbered FIG records plus 2 unnumbered UFIG records.  A
            # source-level UID comment is useful provenance, but it is not
            # mandatory for every legacy module and therefore must not be used
            # as the release completeness gate.
            status_path = extracted_root / "manifests" / "v2.3.1_figure_implementation_status.csv"
            source_map_path = extracted_root / "manifests" / "v2.3.1_figure_source_map.csv"
            with status_path.open("r", encoding="utf-8-sig", newline="") as handle:
                status_rows = list(csv.DictReader(handle))
            figure_uids = [row["figure_uid"].strip() for row in status_rows]
            numbered_uid_pattern = re.compile(r"^FIG-P\d{3}-\d{2}$")
            unnumbered_uid_pattern = re.compile(r"^UFIG-P\d{3}-\d{2}$")
            numbered_uids = [uid for uid in figure_uids if numbered_uid_pattern.fullmatch(uid)]
            unnumbered_uids = [uid for uid in figure_uids if unnumbered_uid_pattern.fullmatch(uid)]
            invalid_uids = [
                uid
                for uid in figure_uids
                if not numbered_uid_pattern.fullmatch(uid)
                and not unnumbered_uid_pattern.fullmatch(uid)
            ]
            if (
                len(figure_uids) != EXPECTED_FIGURE_RECORDS
                or len(set(figure_uids)) != EXPECTED_FIGURE_RECORDS
                or len(numbered_uids) != EXPECTED_NUMBERED_FIGURES
                or len(set(numbered_uids)) != EXPECTED_NUMBERED_FIGURES
                or len(unnumbered_uids) != EXPECTED_UNNUMBERED_FIGURES
                or len(set(unnumbered_uids)) != EXPECTED_UNNUMBERED_FIGURES
                or invalid_uids
            ):
                raise RuntimeError(
                    "figure record count verification failed: "
                    f"expected FIG={EXPECTED_NUMBERED_FIGURES}, "
                    f"UFIG={EXPECTED_UNNUMBERED_FIGURES}, "
                    f"total={EXPECTED_FIGURE_RECORDS}; "
                    f"found FIG={len(numbered_uids)}, "
                    f"unique_FIG={len(set(numbered_uids))}, "
                    f"UFIG={len(unnumbered_uids)}, "
                    f"unique_UFIG={len(set(unnumbered_uids))}, "
                    f"total={len(figure_uids)}, unique_total={len(set(figure_uids))}, "
                    f"invalid={invalid_uids}"
                )
            missing_sources = []
            for row in status_rows:
                source_rel = row["source_tex_file"].strip().replace("\\", "/")
                if not source_rel or not (extracted_root / PurePosixPath(source_rel)).is_file():
                    missing_sources.append({"figure_uid": row["figure_uid"], "source": source_rel})
            if missing_sources:
                raise RuntimeError(f"figure sources missing from ZIP: {missing_sources}")

            with source_map_path.open("r", encoding="utf-8-sig", newline="") as handle:
                source_map_rows = list(csv.DictReader(handle))
            mapped_figure_uid_rows = [
                row["figure_uid"].strip()
                for row in source_map_rows
                if numbered_uid_pattern.fullmatch(row["figure_uid"].strip())
                or unnumbered_uid_pattern.fullmatch(row["figure_uid"].strip())
            ]
            mapped_figure_uids = set(mapped_figure_uid_rows)
            if (
                len(mapped_figure_uid_rows) != EXPECTED_FIGURE_RECORDS
                or len(mapped_figure_uids) != EXPECTED_FIGURE_RECORDS
                or mapped_figure_uids != set(figure_uids)
            ):
                raise RuntimeError(
                    "figure UID records differ between implementation status and source map: "
                    f"mapped_rows={len(mapped_figure_uid_rows)}, "
                    f"mapped_unique={len(mapped_figure_uids)}, "
                    f"status_only={sorted(set(figure_uids) - mapped_figure_uids)}, "
                    f"source_map_only={sorted(mapped_figure_uids - set(figure_uids))}"
                )

            marker_count = 0
            for tex_path in (extracted_root / "src" / "绘图源码").rglob("*.tex"):
                marker_count += tex_path.read_text(encoding="utf-8").count("v2.3.1 figure UID:")
            powershell = shutil.which("powershell") or shutil.which("powershell.exe")
            if powershell is None:
                raise RuntimeError("powershell executable not found for extracted DryRun")
            completed = subprocess.run(
                [
                    powershell,
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(extracted_root / BUILD_SCRIPT_NAME),
                    "-DryRun",
                ],
                cwd=extracted_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            if completed.returncode != 0:
                raise RuntimeError(f"extracted DryRun failed: {completed.stderr.strip()}")
            plan = json.loads(completed.stdout)
            planned_release_pdf = Path(str(plan.get("release_pdf", ""))).name
            if (
                plan.get("target") != "merged_full"
                or plan.get("release_version") != RELEASE_VERSION
                or planned_release_pdf != RELEASE_PDF_NAME
                or plan.get("network_required") is not False
                or plan.get("automatic_install") is not False
            ):
                raise RuntimeError(f"unexpected extracted build plan: {plan}")

            if args.full_rebuild:
                rebuilt = subprocess.run(
                    [
                        powershell,
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(extracted_root / BUILD_SCRIPT_NAME),
                        "-Engine",
                        "lualatex",
                        "-Clean",
                        "-NoPublish",
                    ],
                    cwd=extracted_root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=1800,
                )
                if rebuilt.returncode != 0:
                    tail = (rebuilt.stdout + "\n" + rebuilt.stderr)[-8000:]
                    raise RuntimeError(f"extracted full rebuild failed with {rebuilt.returncode}:\n{tail}")
                rebuilt_pdf = extracted_root / "build" / "final" / "main_full.pdf"
                rebuilt_log = extracted_root / "build" / "final" / "main_full.log"
                if not rebuilt_pdf.is_file() or not rebuilt_log.is_file():
                    raise RuntimeError("extracted full rebuild did not produce PDF and log")
                log_text = rebuilt_log.read_text(encoding="utf-8", errors="replace")
                page_matches = re.findall(r"Output written on main_full\.pdf \((\d+) pages,", log_text)
                if not page_matches:
                    raise RuntimeError("could not read rebuilt page count from main_full.log")
                rebuilt_pages = int(page_matches[-1])
                bad_log_patterns = {
                    "tex_error": r"(?m)^!|LaTeX Error|Package .* Error",
                    "undefined_control": r"Undefined control sequence",
                    "fatal": r"Emergency stop|Fatal error",
                    "overfull": r"Overfull \\[hv]box",
                    "underfull": r"Underfull \\[hv]box",
                    "undefined_references": r"There were undefined references",
                }
                bad_log_matches = {
                    name: len(re.findall(pattern, log_text, flags=re.IGNORECASE))
                    for name, pattern in bad_log_patterns.items()
                }
                if args.expected_pages is not None and rebuilt_pages != args.expected_pages:
                    raise RuntimeError(
                        "extracted full rebuild page-count comparison failed: "
                        f"expected={args.expected_pages}, actual={rebuilt_pages}"
                    )
                if any(bad_log_matches.values()):
                    raise RuntimeError(
                        f"extracted full rebuild log audit failed: {bad_log_matches}"
                    )
                full_rebuild = {
                    "result": "PASS",
                    "engine": "lualatex",
                    "clean_build": True,
                    "reused_worktree_cache": False,
                    "page_count": rebuilt_pages,
                    "expected_pages": args.expected_pages,
                    "page_count_matches_expected": (
                        rebuilt_pages == args.expected_pages
                        if args.expected_pages is not None
                        else None
                    ),
                    "pdf_bytes": rebuilt_pdf.stat().st_size,
                    "log_bad_matches": bad_log_matches,
                }

    result = {
        "schema_version": 2,
        "release_version": RELEASE_VERSION,
        "archive": ARCHIVE.name,
        "archive_prefix": RELEASE_VERSION,
        "release_pdf_name": RELEASE_PDF_NAME,
        "archive_bytes": ARCHIVE.stat().st_size,
        "zip_entries": len(names),
        "crc_failure": None,
        "safe_paths": True,
        "forbidden_entries": 0,
        "main_full_tex": len(main_files),
        "chapter_files": len(chapter_files),
        "authoritative_style_files": len(style_files),
        "shared_figure_style_files": len(shared_style_files),
        "numbered_figure_records": len(numbered_uids),
        "unique_numbered_figure_uids": len(set(numbered_uids)),
        "unnumbered_figure_records": len(unnumbered_uids),
        "unique_unnumbered_figure_uids": len(set(unnumbered_uids)),
        "figure_records_total": len(figure_uids),
        "unique_figure_uids_total": len(set(figure_uids)),
        "figure_sources_present": len(figure_uids) - len(missing_sources),
        "figure_uid_sets_match": True,
        "source_uid_comment_markers_informational": marker_count,
        "required_files_present": True,
        "extracted_dry_run": "PASS",
        "dry_run_target": plan["target"],
        "dry_run_engine": plan["engine"],
        "network_required": plan["network_required"],
        "automatic_install": plan["automatic_install"],
        "full_rebuild_repeated": bool(args.full_rebuild),
        "expected_pages": args.expected_pages,
        "full_rebuild": full_rebuild,
        "result": "PASS",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
