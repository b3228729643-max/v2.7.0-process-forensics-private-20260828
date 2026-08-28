"""PDF-level link checks for the bounded stage-2 navigation batch.

The source contract tests prove that the right global chapter macros occur at
the audited anchors.  These checks cover the other half of the contract: the
standalone volume PDFs must turn every in-volume route into a real GoTo link,
while cross-volume routes remain readable without unresolved destinations.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
VOLUME1_PDF = ROOT / "stage2-build" / "volume1" / "main.pdf"
VOLUME5_PDF = ROOT / "stage2-build" / "volume5" / "main.pdf"


def link_destinations(reader: PdfReader, one_based_page: int) -> set[str]:
    page = reader.pages[one_based_page - 1]
    destinations: set[str] = set()
    for annotation_ref in page.get("/Annots") or []:
        annotation = annotation_ref.get_object()
        if annotation.get("/Subtype") != "/Link":
            continue
        action = annotation.get("/A") or {}
        destination = annotation.get("/Dest") or action.get("/D")
        if destination is not None:
            destinations.add(str(destination))
    return destinations


@unittest.skipUnless(
    VOLUME1_PDF.is_file() and VOLUME5_PDF.is_file(),
    "historical v1.8 stage-2 PDF fixtures are not shipped in the v1.9 source copy",
)
class StageTwoPdfNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.volume1 = PdfReader(VOLUME1_PDF)
        cls.volume5 = PdfReader(VOLUME5_PDF)

    def assert_page_routes(
        self,
        reader: PdfReader,
        page: int,
        expected_destinations: set[str],
    ) -> None:
        actual = link_destinations(reader, page)
        self.assertTrue(
            expected_destinations <= actual,
            f"page {page}: missing {expected_destinations - actual}; actual={sorted(actual)}",
        )

    def test_volume_one_audited_routes_are_live_when_targets_are_present(self) -> None:
        cases = {
            48: {"chapter.4", "chapter.7", "chapter.8"},
            61: {"chapter.2", "chapter.3", "chapter.4"},
            87: {"chapter.7"},
            118: {"chapter.9"},
            148: {"chapter.11"},
        }
        for page, expected in cases.items():
            with self.subTest(page=page):
                self.assert_page_routes(self.volume1, page, expected)

    def test_volume_five_audited_routes_are_live(self) -> None:
        cases = {
            28: {"chapter.2", "chapter.3"},
            53: {"chapter.1", "chapter.2"},
            54: {"chapter.1", "chapter.2"},
            82: {"chapter.3"},
            83: {"chapter.3"},
            103: {"chapter.6"},
            126: {"chapter.4", "chapter.5"},
            127: {"chapter.4", "chapter.5"},
            169: {"chapter.1", "chapter.8"},
        }
        for page, expected in cases.items():
            with self.subTest(page=page):
                self.assert_page_routes(self.volume5, page, expected)

    def test_non_self_referential_volume_five_opening_adds_no_chapter_link(self) -> None:
        destinations = link_destinations(self.volume5, 170)
        chapter_destinations = {
            destination
            for destination in destinations
            if destination.startswith("chapter.")
        }
        self.assertEqual(chapter_destinations, set())


if __name__ == "__main__":
    unittest.main()
