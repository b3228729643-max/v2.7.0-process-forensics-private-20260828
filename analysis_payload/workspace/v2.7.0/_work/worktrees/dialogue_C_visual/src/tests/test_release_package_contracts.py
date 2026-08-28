from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import zipfile

from scripts import build_source_zip
from scripts import audit_pdf_navigation
from scripts import verify_source_zip
from scripts import package_final_deliverables


class ReleasePackageContractTests(unittest.TestCase):
    def test_final_delivery_layout_has_thirteen_payloads(self) -> None:
        self.assertEqual(len(package_final_deliverables.DELIVERY_LAYOUT), 13)
        self.assertEqual(len(package_final_deliverables.expected_members()), 13)
        self.assertNotIn(
            package_final_deliverables.DELIVERY_ARCHIVE_NAME,
            package_final_deliverables.DELIVERY_LAYOUT,
        )

    def test_final_delivery_archive_matches_the_required_layout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="statlearn-final-delivery-") as temp_name:
            root = Path(temp_name)
            for name in package_final_deliverables.DELIVERY_LAYOUT:
                (root / name).write_bytes((name + "\n").encode("utf-8"))
            archive = root / package_final_deliverables.DELIVERY_ARCHIVE_NAME
            package_final_deliverables.write_archive(root, archive)
            result = package_final_deliverables.verify_archive(archive)

            self.assertEqual(result["result"], "PASS")
            self.assertEqual(result["payload_files"], 13)
            self.assertFalse(result["self_included"])

    def test_navigation_audit_uses_the_release_version_manifest(self) -> None:
        self.assertEqual(audit_pdf_navigation.read_release_version(), "v2.7.0")

    def test_release_set_excludes_generated_and_legacy_files(self) -> None:
        files = build_source_zip.collect_files()
        relatives = [path.relative_to(build_source_zip.ROOT) for path in files]

        self.assertTrue(files)
        self.assertFalse(any(path.suffix.lower() == ".pdf" for path in relatives))
        self.assertFalse(
            any(path.name.startswith(("v240_", "v260_")) for path in relatives)
        )
        self.assertFalse(
            any(
                path.name
                in {
                    "README_v1.8.0.md",
                    "figure-style-v2.3.0.tex",
                    "template_demo.tex",
                }
                for path in relatives
            )
        )

    def test_temporary_archive_passes_structural_and_dry_run_verification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="statlearn-release-contract-") as temp_name:
            temp = Path(temp_name)
            archive = temp / build_source_zip.ARCHIVE_NAME
            output = temp / "source_zip_verification.json"

            with mock.patch.object(build_source_zip, "ARCHIVE", archive):
                build_source_zip.write_archive(build_source_zip.collect_files())

            with zipfile.ZipFile(archive) as handle:
                names = verify_source_zip.safe_members(handle)
            self.assertTrue(all(verify_source_zip.is_release_member(name) for name in names))

            with (
                mock.patch.object(verify_source_zip, "ARCHIVE", archive),
                mock.patch.object(verify_source_zip, "OUTPUT", output),
                mock.patch.object(sys, "argv", ["verify_source_zip.py"]),
            ):
                self.assertEqual(verify_source_zip.main(), 0)
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
