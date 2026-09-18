"""Tests for _system/init_vault.py. Run with:
  python3 -m unittest discover -s tests -v
"""
import datetime
import tempfile
import unittest
from pathlib import Path

from vault_helpers import SYSTEM_DIR  # noqa: F401 - adds _system/ to sys.path

import init_vault
import lint


class TestInitVault(unittest.TestCase):
    def test_creates_expected_layout_and_lints_clean(self):
        today = datetime.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "new-vault"
            result = init_vault.init_vault(dest, today)
            self.assertEqual(init_vault.validate(result), [])
            issues, _ = lint.check_vault(result)
            self.assertEqual(issues, [])

    def test_does_not_create_git_repo(self):
        today = datetime.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "new-vault"
            result = init_vault.init_vault(dest, today)
            self.assertFalse((result / ".git").exists())

    def test_does_not_copy_example_notes(self):
        today = datetime.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "new-vault"
            result = init_vault.init_vault(dest, today)
            for area in ("Properties", "Tenants", "Finance"):
                self.assertEqual(list((result / area).glob("*.md")), [])

    def test_refuses_destination_inside_repo(self):
        with self.assertRaises(SystemExit):
            init_vault.init_vault(
                init_vault.REPO_ROOT / "should-not-be-created", "2026-01-01")

    def test_refuses_nonempty_destination(self):
        today = datetime.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "new-vault"
            dest.mkdir()
            (dest / "something.txt").write_text("not empty", encoding="utf-8")
            with self.assertRaises(SystemExit):
                init_vault.init_vault(dest, today)

    def test_creates_sensitive_vault_marker(self):
        today = datetime.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "new-vault"
            result = init_vault.init_vault(dest, today)
            self.assertTrue((result / ".sensitive-vault").exists())


if __name__ == "__main__":
    unittest.main()
