"""Tests for the source-level label and internal-link auditor."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "qa" / "link_and_label_audit.py"
SPEC = importlib.util.spec_from_file_location("link_and_label_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class LinkAndLabelAuditTests(unittest.TestCase):
    def make_root(self, *sources: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for index, source in enumerate(sources, 1):
            (root / f"source-{index}.tex").write_text(source, encoding="utf-8")
        return temp, root

    def test_concrete_refs_and_targets_pass(self) -> None:
        temp, root = self.make_root(
            r"\label{chap:one}\hypertarget{SL:toc}{}",
            r"\ref{chap:one}\cref{chap:one}\hyperref[chap:one]{章}\hyperlink{SL:toc}{目录}",
        )
        self.addCleanup(temp.cleanup)
        result = AUDIT.audit_links(root)
        self.assertTrue(result.passed, result.findings)
        self.assertEqual(result.references, 3)
        self.assertEqual(result.hyperlinks, 1)

    def test_unresolved_reference_and_hyperlink_are_reported(self) -> None:
        temp, root = self.make_root(r"\ref{missing}\hyperlink{missing-target}{x}")
        self.addCleanup(temp.cleanup)
        result = AUDIT.audit_links(root)
        codes = {item.code for item in result.findings}
        self.assertIn("unresolved_reference", codes)
        self.assertIn("unresolved_hyperlink", codes)

    def test_duplicate_label_and_target_are_reported(self) -> None:
        temp, root = self.make_root(
            r"\label{same}\hypertarget{same-target}{}",
            r"\label{same}\hypertarget{same-target}{}",
        )
        self.addCleanup(temp.cleanup)
        result = AUDIT.audit_links(root)
        codes = {item.code for item in result.findings}
        self.assertIn("duplicate_label", codes)
        self.assertIn("duplicate_target", codes)

    def test_comments_and_dynamic_macro_arguments_are_ignored(self) -> None:
        temp, root = self.make_root(
            "% \\label{ghost} \\ref{ghost}\n"
            r"\newcommand{\go}[1]{\ref{#1}\hyperlink{SL:chapter:\thechapter}{x}}"
        )
        self.addCleanup(temp.cleanup)
        result = AUDIT.audit_links(root)
        self.assertTrue(result.passed, result.findings)

    def test_shared_section_macro_creates_a_label(self) -> None:
        temp, root = self.make_root(
            r"\SLTeachSection{主题}{sec:topic}\ref{sec:topic}"
        )
        self.addCleanup(temp.cleanup)
        result = AUDIT.audit_links(root)
        self.assertTrue(result.passed, result.findings)


if __name__ == "__main__":
    unittest.main(verbosity=2)
