"""Historical integrity checks for the single-writer v1.8.0 closure table."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
AUTHORITY_CSV = WORKSPACE / "统计学习方法讲义_v1.7.0_问题清单.csv"
CLOSURE_CSV = ROOT / "audit" / "统计学习方法讲义_v1.8.0_问题闭环表.csv"

ORIGINAL_HEADERS = (
    "ID",
    "优先级",
    "置信度",
    "类别",
    "章节",
    "PDF页",
    "印刷页/位置",
    "对象",
    "问题",
    "影响",
    "具体修复",
    "验收方式",
)
CLOSURE_HEADERS = (
    "源码文件",
    "源码锚点/行号",
    "处理状态",
    "修改摘要",
    "验证命令",
    "验证结果",
    "证据文件",
    "提交/补丁标识",
    "复核者",
    "遗留说明",
)
ALLOWED_STATUSES = {
    "unstarted",
    "in_progress",
    "fixed_pending_verification",
    "verified",
    "not_applicable_verified",
    "blocked",
}
EVIDENCED_STATUSES = {
    "fixed_pending_verification",
    "verified",
    "not_applicable_verified",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


@unittest.skipUnless(
    AUTHORITY_CSV.is_file() and CLOSURE_CSV.is_file(),
    "historical v1.8 CSV closure fixtures are not shipped in the v1.9 source copy",
)
class ClosureTableIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority_headers, cls.authority = read_csv(AUTHORITY_CSV)
        cls.closure_headers, cls.closure = read_csv(CLOSURE_CSV)

    def test_shape_headers_and_unique_ids(self) -> None:
        self.assertEqual(len(self.authority), 199)
        self.assertEqual(len(self.closure), 199)
        self.assertEqual(self.authority_headers, list(ORIGINAL_HEADERS))
        self.assertEqual(
            self.closure_headers,
            list(ORIGINAL_HEADERS + CLOSURE_HEADERS),
        )
        ids = [row["ID"] for row in self.closure]
        self.assertEqual(len(ids), len(set(ids)))

    def test_original_twelve_columns_are_byte_for_byte_equal_as_cells(self) -> None:
        for index, (authority, closure) in enumerate(
            zip(self.authority, self.closure, strict=True),
            start=2,
        ):
            for header in ORIGINAL_HEADERS:
                self.assertEqual(
                    closure[header],
                    authority[header],
                    f"row {index}, column {header}",
                )

    def test_statuses_and_evidence_fields_are_valid(self) -> None:
        for row in self.closure:
            issue_id = row["ID"]
            status = row["处理状态"]
            self.assertIn(status, ALLOWED_STATUSES, issue_id)
            if status not in EVIDENCED_STATUSES:
                continue
            for header in CLOSURE_HEADERS:
                self.assertTrue(row[header].strip(), f"{issue_id}: blank {header}")
            for evidence in row["证据文件"].split("；"):
                evidence_path = ROOT / evidence.strip()
                self.assertTrue(
                    evidence_path.is_file(),
                    f"{issue_id}: missing evidence {evidence_path}",
                )


if __name__ == "__main__":
    unittest.main()
