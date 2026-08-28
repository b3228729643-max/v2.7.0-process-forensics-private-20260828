from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz

from qa.pdf_layout_audit import audit_pdf


class PdfLayoutAuditTests(unittest.TestCase):
    def _make_pdf(self, pages: list[list[tuple[str, float]]]) -> Path:
        temporary = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temporary.close()
        path = Path(temporary.name)
        document = fitz.open()
        for lines in pages:
            page = document.new_page(width=595, height=842)
            y = 72
            for text, size in lines:
                page.insert_text((72, y), text, fontsize=size, fontname="china-s")
                y += max(20, size * 1.8)
        document.save(path)
        document.close()
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_detects_absolute_small_font_and_sparse_page(self) -> None:
        body = [('ordinary text ordinary text', 10.0)] * 8
        pdf = self._make_pdf([[('small', 5.5)], body])
        report = audit_pdf(pdf, exempt_pages=())
        self.assertEqual(report['summary']['pages_with_characters_below_6pt'], [1])
        self.assertEqual(report['summary']['sparse_pages'], [1])

    def test_exempt_page_is_not_reported_as_sparse(self) -> None:
        body = [('ordinary text ordinary text', 10.0)] * 8
        pdf = self._make_pdf([[('cover', 12.0)], body])
        report = audit_pdf(pdf, exempt_pages={1})
        self.assertEqual(report['summary']['sparse_pages'], [])

    def test_contents_heading_is_transparently_auto_exempt(self) -> None:
        pdf = self._make_pdf([[('目录', 12.0), ('目录', 8.5)]])
        report = audit_pdf(pdf, exempt_pages=())
        self.assertEqual(report['summary']['sparse_pages'], [])
        self.assertEqual(report['automatic_exempt_pages'], {1: 'table_of_contents'})

    def test_measures_complete_chapter_card(self) -> None:
        pdf = self._make_pdf(
            [[
                ('本章地图', 10.0),
                ('路线与核心问题', 10.0),
                ('完成标准与返回', 10.0),
                ('依赖路径', 10.0),
                ('本章符号表', 10.0),
            ]]
        )
        report = audit_pdf(pdf, exempt_pages=())
        card = report['chapter_cards'][0]
        self.assertTrue(card['complete'])
        self.assertEqual(card['start_page'], 1)
        self.assertLess(card['footprint_pages'], 1.5)


if __name__ == '__main__':
    unittest.main()
