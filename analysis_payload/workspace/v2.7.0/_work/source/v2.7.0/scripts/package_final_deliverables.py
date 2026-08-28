#!/usr/bin/env python3
"""Validate and package the fourteen v2.7.0 final deliverables."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FINAL_ROOT = PROJECT_ROOT.parent.parent.parent
RELEASE_VERSION_PATH = PROJECT_ROOT / "manifests" / "release_version.tex"


def read_release_version() -> str:
    source = RELEASE_VERSION_PATH.read_text(encoding="utf-8")
    active = "\n".join(line.split("%", 1)[0] for line in source.splitlines())
    matches = re.findall(
        r"\\newcommand\s*\{\\SLReleaseVersion\}\s*\{(v\d+\.\d+\.\d+)\}",
        active,
    )
    if len(matches) != 1:
        raise RuntimeError("release_version.tex must define one SLReleaseVersion")
    return matches[0]


RELEASE_VERSION = read_release_version()
DELIVERY_PREFIX = f"统计学习方法讲义_{RELEASE_VERSION}_全部交付文件"
DELIVERY_ARCHIVE_NAME = f"{DELIVERY_PREFIX}.zip"

DELIVERY_LAYOUT = {
    f"统计学习方法初学者讲义_合并总册{RELEASE_VERSION}_完整解析版.pdf": "00_发布PDF",
    f"统计学习方法讲义_{RELEASE_VERSION}_LaTeX源码.zip": "01_LaTeX源码",
    f"统计学习方法讲义_{RELEASE_VERSION}_最终视觉证据.zip": "02_最终视觉证据",
    f"README_{RELEASE_VERSION}.md": "03_说明与复核记录",
    f"CHANGELOG_{RELEASE_VERSION}.md": "03_说明与复核记录",
    f"{RELEASE_VERSION}_修改与复核总报告.md": "03_说明与复核记录",
    f"{RELEASE_VERSION}_主要问题三角色复核台账.csv": "03_说明与复核记录",
    f"{RELEASE_VERSION}_绘图逐图三角色复核台账.csv": "03_说明与复核记录",
    f"{RELEASE_VERSION}_最终全书视觉扫描记录.md": "03_说明与复核记录",
    f"MANIFEST_{RELEASE_VERSION}.md": "03_说明与复核记录",
    f"GPT_Pro_统计学习方法讲义_{RELEASE_VERSION}_Codex_Goal主提示词.md": "04_执行提示词",
    f"GPT_Pro_统计学习方法讲义_{RELEASE_VERSION}_对话A_逐图视觉重构执行提示词.md": "04_执行提示词",
    f"GPT_Pro_统计学习方法讲义_{RELEASE_VERSION}_对话B_内容数学重构执行提示词.md": "04_执行提示词",
}


def expected_members() -> list[str]:
    return sorted(
        str(PurePosixPath(DELIVERY_PREFIX) / directory / name)
        for name, directory in DELIVERY_LAYOUT.items()
    )


def collect_payload(root: Path) -> list[Path]:
    missing: list[str] = []
    empty: list[str] = []
    payload: list[Path] = []
    for name in DELIVERY_LAYOUT:
        path = root / name
        if not path.is_file():
            missing.append(name)
        elif path.stat().st_size <= 0:
            empty.append(name)
        else:
            payload.append(path)
    if missing or empty:
        raise RuntimeError(
            json.dumps(
                {"missing": missing, "empty": empty},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return payload


def write_archive(root: Path, archive: Path) -> None:
    payload = collect_payload(root)
    temporary = archive.with_suffix(archive.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as handle:
        for path in sorted(
            payload, key=lambda item: (DELIVERY_LAYOUT[item.name], item.name)
        ):
            member = PurePosixPath(DELIVERY_PREFIX) / DELIVERY_LAYOUT[path.name] / path.name
            info = zipfile.ZipInfo(str(member), date_time=(2026, 8, 24, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            handle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    os.replace(temporary, archive)


def verify_archive(archive: Path) -> dict[str, object]:
    with zipfile.ZipFile(archive) as handle:
        names = [info.filename for info in handle.infolist()]
        bad_crc = handle.testzip()
    expected = expected_members()
    unsafe = [
        name
        for name in names
        if "\\" in name
        or PurePosixPath(name).is_absolute()
        or ".." in PurePosixPath(name).parts
        or PurePosixPath(name).as_posix() != name
    ]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    result = {
        "archive": archive.name,
        "payload_files": len(names),
        "expected_payload_files": len(expected),
        "members_match": names == expected,
        "missing_members": sorted(set(expected) - set(names)),
        "extra_members": sorted(set(names) - set(expected)),
        "duplicates": duplicates,
        "unsafe_members": unsafe,
        "crc_failure": bad_crc,
        "self_included": any(
            PurePosixPath(name).name == DELIVERY_ARCHIVE_NAME for name in names
        ),
    }
    result["result"] = "PASS" if all(
        (
            result["members_match"],
            not result["duplicates"],
            not result["unsafe_members"],
            result["crc_failure"] is None,
            not result["self_included"],
        )
    ) else "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=FINAL_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the thirteen payload files without creating the final ZIP",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        payload = collect_payload(root)
    except RuntimeError as error:
        print(json.dumps({"result": "FAIL", "root": str(root), "detail": str(error)}, ensure_ascii=False, indent=2))
        return 1
    if args.check:
        print(json.dumps({"result": "PASS", "root": str(root), "payload_files": len(payload), "final_root_files_after_packaging": len(payload) + 1}, ensure_ascii=False, indent=2))
        return 0

    archive = root / DELIVERY_ARCHIVE_NAME
    write_archive(root, archive)
    result = verify_archive(archive)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
