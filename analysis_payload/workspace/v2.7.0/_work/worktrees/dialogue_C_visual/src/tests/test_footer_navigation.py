"""Static contract for the compact, readable PDF footer navigation."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "讲义源码" / "common" / "statlearnbook.sty"
SMOKE_PDF = ROOT / "qa" / "stage3" / "LAY-004" / "footer_navigation_smoke.pdf"


class FooterNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = STYLE.read_text(encoding="utf-8")
        match = re.search(
            r"\\newcommand\{\\SLPageNavigation\}\{%(.+?)\n\}",
            cls.source,
            re.DOTALL,
        )
        if match is None:
            raise AssertionError("cannot locate SLPageNavigation")
        cls.navigation = match.group(1)

    def test_footer_keeps_exactly_four_core_links(self) -> None:
        labels = re.findall(r"\\SLNavLink\{[^{}]+\}\{([^{}]+)\}", self.navigation)
        self.assertEqual(labels, ["目录", "本章", "练习", "解析"])
        self.assertEqual(self.navigation.count(r"\SLNavLink"), 4)

    def test_removed_repetitive_links_do_not_remain_in_footer(self) -> None:
        for label in ("前置", "例题", "索引"):
            self.assertNotIn(f"{{{label}}}", self.navigation)

    def test_both_footer_styles_use_readable_small_and_one_navigation_macro(self) -> None:
        footer_lines = [
            line.strip()
            for line in self.source.splitlines()
            if r"\fancyfoot[C]" in line
        ]
        self.assertEqual(len(footer_lines), 2)
        for line in footer_lines:
            self.assertIn(r"\small", line)
            self.assertEqual(line.count(r"\SLPageNavigation"), 1)
            self.assertNotIn(r"\scriptsize", line)
            self.assertNotIn(r"\tiny", line)

    @unittest.skipUnless(SMOKE_PDF.is_file(), "historical v1.8 footer smoke PDF is not shipped in the v1.9 source copy")
    def test_smoke_pdf_has_exactly_four_live_footer_destinations(self) -> None:
        reader = PdfReader(SMOKE_PDF)
        expected = [
            "SL:toc",
            "SL:chapter:1",
            "SL:exercises:1",
            "SL:answers:1",
        ]
        for one_based_page in (2, 3):
            destinations: list[str] = []
            for annotation_ref in reader.pages[one_based_page - 1].get("/Annots") or []:
                annotation = annotation_ref.get_object()
                if annotation.get("/Subtype") != "/Link":
                    continue
                action = annotation.get("/A") or {}
                destination = annotation.get("/Dest") or action.get("/D")
                destinations.append(str(destination))
            self.assertEqual(destinations, expected, f"PDF page {one_based_page}")


if __name__ == "__main__":
    unittest.main()
