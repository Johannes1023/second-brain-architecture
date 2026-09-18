"""Unit tests for _system/vaultlib.py: the frontmatter parser and root
resolution. Run with: python3 -m unittest discover -s tests -v
"""
import os
import tempfile
import unittest
from pathlib import Path

from vault_helpers import SYSTEM_DIR  # noqa: F401 - adds _system/ to sys.path

import vaultlib


def write(tmp, text):
    p = Path(tmp) / "note.md"
    p.write_text(text, encoding="utf-8")
    return p


class TestParse(unittest.TestCase):
    def test_plain_scalar(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "---\ndescription: A note\nstatus: active\n---\nBody.\n")
            meta, body, has_fm = vaultlib.parse(p)
            self.assertTrue(has_fm)
            self.assertEqual(meta["description"], "A note")
            self.assertEqual(meta["status"], "active")
            self.assertEqual(body.strip(), "Body.")

    def test_quoted_scalar_with_colon(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, '---\ndescription: "Note: with a colon inside"\n---\nBody.\n')
            meta, _, _ = vaultlib.parse(p)
            self.assertEqual(meta["description"], "Note: with a colon inside")

    def test_inline_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "---\ntags: [a, b, c]\n---\nBody.\n")
            meta, _, _ = vaultlib.parse(p)
            self.assertEqual(meta["tags"], ["a", "b", "c"])

    def test_inline_list_with_quoted_comma(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, '---\naliases: ["Hello, World", "Second"]\n---\nBody.\n')
            meta, _, _ = vaultlib.parse(p)
            self.assertEqual(meta["aliases"], ["Hello, World", "Second"])

    def test_full_line_comment_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "---\n# a comment\ndescription: fine\n---\nBody.\n")
            meta, _, _ = vaultlib.parse(p)
            self.assertEqual(meta["description"], "fine")
            self.assertNotIn("# a comment", meta)

    def test_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "Just body text, no frontmatter.\n")
            meta, body, has_fm = vaultlib.parse(p)
            self.assertFalse(has_fm)
            self.assertEqual(meta, {})
            self.assertIn("Just body text", body)

    def test_malformed_file_never_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "---\nnot a valid line at all\n---\nBody.\n")
            meta, body, has_fm = vaultlib.parse(p)  # must not raise
            self.assertTrue(has_fm)


class TestParseIssues(unittest.TestCase):
    def test_duplicate_key_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "---\ndescription: first\ndescription: second\n---\nBody.\n")
            meta, _, _ = vaultlib.parse(p)
            issues = vaultlib.parse_issues(p)
            self.assertEqual(meta["description"], "second")  # last value wins
            self.assertTrue(any("duplicate frontmatter key" in i for i in issues))

    def test_unterminated_quote_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, '---\ndescription: "unterminated\n---\nBody.\n')
            issues = vaultlib.parse_issues(p)
            self.assertTrue(any("unterminated quoted value" in i for i in issues))

    def test_unterminated_list_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "---\ntags: [a, b\n---\nBody.\n")
            issues = vaultlib.parse_issues(p)
            self.assertTrue(any("unterminated list value" in i for i in issues))

    def test_clean_file_has_no_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "---\ndescription: fine\ntags: [a, b]\n---\nBody.\n")
            self.assertEqual(vaultlib.parse_issues(p), [])


class TestResolveRoot(unittest.TestCase):
    def test_explicit_path_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = vaultlib.resolve_root(tmp)
            self.assertEqual(root, Path(tmp).resolve())

    def test_explicit_bad_path_raises(self):
        with self.assertRaises(SystemExit):
            vaultlib.resolve_root("/definitely/does/not/exist/anywhere")

    def test_env_var_used_when_no_cli_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("SECOND_BRAIN_ROOT")
            os.environ["SECOND_BRAIN_ROOT"] = tmp
            try:
                root = vaultlib.resolve_root(None)
                self.assertEqual(root, Path(tmp).resolve())
            finally:
                if old is None:
                    os.environ.pop("SECOND_BRAIN_ROOT", None)
                else:
                    os.environ["SECOND_BRAIN_ROOT"] = old

    def test_bad_env_var_raises_not_silently_falls_back(self):
        old = os.environ.get("SECOND_BRAIN_ROOT")
        os.environ["SECOND_BRAIN_ROOT"] = "/definitely/does/not/exist/anywhere"
        try:
            with self.assertRaises(SystemExit):
                vaultlib.resolve_root(None)
        finally:
            if old is None:
                os.environ.pop("SECOND_BRAIN_ROOT", None)
            else:
                os.environ["SECOND_BRAIN_ROOT"] = old


if __name__ == "__main__":
    unittest.main()
