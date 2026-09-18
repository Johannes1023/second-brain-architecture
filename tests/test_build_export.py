"""Tests for _system/build_export.py, against small synthetic vaults built
fresh per test (see vault_helpers.py). Run with:
  python3 -m unittest discover -s tests -v
"""
import tempfile
import unittest
from pathlib import Path

from vault_helpers import build_vault, note  # noqa: F401 - adds _system/ to sys.path

import build_export


class TestCatalog(unittest.TestCase):
    def test_catalog_includes_note_with_its_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_vault(Path(tmp), {
                "Properties/A Property.md": note(description="A test property."),
            })
            cat, dupes = build_export.catalog(root)
            self.assertIn("A Property", cat)
            self.assertIn("A test property.", cat)
            self.assertEqual(dupes, set())

    def test_top_level_files_excluded_from_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_vault(Path(tmp), {
                "Properties/A.md": note(),
            })
            (root / "AGENTS.md").write_text("---\narea: System\n---\ntop level\n",
                                              encoding="utf-8")
            cat, _ = build_export.catalog(root)
            self.assertNotIn("AGENTS", cat)

    def test_duplicate_title_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_vault(Path(tmp), {
                "Properties/Same.md": note(area="Properties"),
                "Tenants/Same.md": note(area="Tenants"),
            })
            _, dupes = build_export.catalog(root)
            self.assertIn("Same", dupes)


class TestMainWritesFiles(unittest.TestCase):
    def test_main_rebuilds_index_and_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_vault(Path(tmp), {
                "Properties/A Property.md": note(description="A test property."),
                "_system/Communication Preferences.md": note(
                    area="System", description="Prefs."),
            })
            rc = build_export.main(["--vault", str(root)])
            self.assertEqual(rc, 0)
            self.assertTrue((root / "_export" / "PORTFOLIO.md").exists())
            self.assertTrue((root / "_export" / "PORTFOLIO-full.md").exists())
            index_text = (root / "_index.md").read_text(encoding="utf-8")
            self.assertIn("A Property", index_text)

    def test_main_refuses_to_write_on_duplicate_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_vault(Path(tmp), {
                "Properties/Same.md": note(area="Properties"),
                "Tenants/Same.md": note(area="Tenants"),
                "_system/Communication Preferences.md": note(
                    area="System", description="Prefs."),
            })
            before = (root / "_index.md").read_text(encoding="utf-8")
            rc = build_export.main(["--vault", str(root)])
            self.assertEqual(rc, 2)
            after = (root / "_index.md").read_text(encoding="utf-8")
            self.assertEqual(before, after)  # refused write leaves the index untouched

    def test_main_rejects_missing_vault_path(self):
        rc = build_export.main(["--vault", "/definitely/does/not/exist"])
        self.assertEqual(rc, 2)

    def test_main_rejects_vault_without_index_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "_index.md").write_text("no markers here\n", encoding="utf-8")
            (root / "NOW.md").write_text("## Active\n", encoding="utf-8")
            rc = build_export.main(["--vault", str(root)])
            self.assertEqual(rc, 2)

    def test_atomic_write_leaves_no_tmp_file_behind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_vault(Path(tmp), {
                "Properties/A.md": note(),
                "_system/Communication Preferences.md": note(
                    area="System", description="Prefs."),
            })
            build_export.main(["--vault", str(root)])
            leftover_tmp_files = list(root.rglob("*.tmp"))
            self.assertEqual(leftover_tmp_files, [])


if __name__ == "__main__":
    unittest.main()
