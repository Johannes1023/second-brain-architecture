"""Tests for _system/lint.py's check_vault(), against small synthetic vaults
built fresh per test (see vault_helpers.py). Run with:
  python3 -m unittest discover -s tests -v
"""
import tempfile
import unittest
from pathlib import Path

from vault_helpers import build_vault, note  # noqa: F401 - adds _system/ to sys.path

import lint


def issues_for(notes, now_md=None, deadline_days=30):
    with tempfile.TemporaryDirectory() as tmp:
        root = build_vault(Path(tmp), notes, now_md=now_md)
        return lint.check_vault(root, deadline_days=deadline_days)


class TestCleanVault(unittest.TestCase):
    def test_single_valid_note_is_clean(self):
        issues, notices = issues_for({
            "Properties/A Property.md": note(description="A test property."),
        })
        self.assertEqual(issues, [])


class TestFrontmatter(unittest.TestCase):
    def test_missing_required_field_flagged(self):
        text = "---\ndescription: incomplete\n---\nBody.\n"
        issues, _ = issues_for({"Properties/Incomplete.md": text})
        self.assertTrue(any("frontmatter missing" in i for i in issues))

    def test_invalid_status_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(status="not-a-real-status"),
        })
        self.assertTrue(any("invalid status" in i for i in issues))

    def test_invalid_area_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(area="NotARealArea"),
        })
        self.assertTrue(any("invalid area" in i for i in issues))

    def test_invalid_review_cadence_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(review="weekly"),
        })
        self.assertTrue(any("invalid review cadence" in i for i in issues))

    def test_bad_date_format_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(created="01/01/2026"),
        })
        self.assertTrue(any("bad created" in i for i in issues))

    def test_duplicate_frontmatter_key_surfaced_as_issue(self):
        text = ("---\ndescription: a\ndescription: b\ncreated: 2026-01-01\n"
                "modified: 2026-01-01\nlast_verified: 2026-01-01\nreview: quarterly\n"
                "status: active\narea: Properties\n---\nBody.\n")
        issues, _ = issues_for({"Properties/A.md": text})
        self.assertTrue(any("duplicate frontmatter key" in i for i in issues))


class TestLinksAndTitles(unittest.TestCase):
    def test_broken_wikilink_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(body="See [[Nonexistent Note]] for more."),
        })
        self.assertTrue(any("broken link" in i for i in issues))

    def test_valid_wikilink_not_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(body="See [[B]] for more."),
            "Properties/B.md": note(description="B"),
        })
        self.assertFalse(any("broken link" in i for i in issues))

    def test_alias_resolves_wikilink(self):
        issues, _ = issues_for({
            "Properties/A.md": note(body="See [[B Alias]] for more."),
            "Properties/B.md": note(description="B", aliases=["B Alias"]),
        })
        self.assertFalse(any("broken link" in i for i in issues))

    def test_duplicate_title_flagged(self):
        issues, _ = issues_for({
            "Properties/Same Name.md": note(area="Properties"),
            "Tenants/Same Name.md": note(area="Tenants"),
        })
        self.assertTrue(any("duplicate title" in i for i in issues))

    def test_duplicate_alias_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(aliases=["Shared Alias"]),
            "Properties/B.md": note(aliases=["Shared Alias"]),
        })
        self.assertTrue(any("duplicate alias" in i for i in issues))

    def test_alias_colliding_with_title_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(aliases=["B"]),
            "Properties/B.md": note(description="B"),
        })
        self.assertTrue(any("collides with an existing note title" in i for i in issues))


class TestDeadlinesAndReviews(unittest.TestCase):
    def test_upcoming_deadline_flagged(self):
        import datetime
        soon = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        issues, _ = issues_for({"Properties/A.md": note(deadline=soon)})
        self.assertTrue(any("deadline in" in i for i in issues))

    def test_passed_deadline_flagged(self):
        issues, _ = issues_for({"Properties/A.md": note(deadline="2020-01-01")})
        self.assertTrue(any("deadline passed" in i for i in issues))

    def test_bad_deadline_format_flagged(self):
        issues, _ = issues_for({"Properties/A.md": note(deadline="not-a-date")})
        self.assertTrue(any("bad deadline" in i for i in issues))

    def test_future_last_verified_flagged(self):
        issues, _ = issues_for({"Properties/A.md": note(last_verified="2099-01-01")})
        self.assertTrue(any("is in the future" in i for i in issues))

    def test_overdue_review_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(review="monthly", last_verified="2020-01-01"),
        })
        self.assertTrue(any("review overdue" in i for i in issues))


class TestNowMd(unittest.TestCase):
    def test_stale_line_flagged_in_any_section_not_just_recent(self):
        # Regression test: the linter used to only check the "Recent
        # developments" section for entries older than 30 days, missing
        # stale lines under "Active" or "Upcoming".
        now_md = "## Active\n\n- 2020-01-01: [[A]] something long since resolved\n"
        issues, _ = issues_for({"Properties/A.md": note()}, now_md=now_md)
        self.assertTrue(any("older than 30 days" in i for i in issues))

    def test_unparseable_date_reported_not_crashed(self):
        now_md = "## Active\n\n- 2020-99-99: broken date\n"
        issues, _ = issues_for({"Properties/A.md": note()}, now_md=now_md)
        self.assertTrue(any("unparseable date" in i for i in issues))


class TestDocumentReferences(unittest.TestCase):
    def test_missing_document_reference_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(body="See `Documents/Leases/missing.pdf`."),
        })
        self.assertTrue(any("linked document not found" in i for i in issues))

    def test_present_document_reference_not_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(body="See `Documents/Leases/present.pdf`."),
            "Documents/Leases/present.pdf": "not a real pdf, just a test placeholder",
        })
        self.assertFalse(any("linked document not found" in i for i in issues))

    def test_path_escape_flagged(self):
        issues, _ = issues_for({
            "Properties/A.md": note(body="See `Documents/../../../etc/passwd`."),
        })
        self.assertTrue(any("escapes the vault" in i for i in issues))


class TestRepoDocsExemptFromFrontmatter(unittest.TestCase):
    def test_security_md_not_flagged_for_missing_frontmatter(self):
        issues, _ = issues_for({
            "Properties/A.md": note(),
            "SECURITY.md": "# Security\n\nNo frontmatter here, this is a repo doc.\n",
        })
        self.assertFalse(any("SECURITY.md" in i for i in issues))

    def test_docs_folder_file_not_flagged_for_missing_frontmatter(self):
        issues, _ = issues_for({
            "Properties/A.md": note(),
            "docs/THREAT_MODEL.md": "# Threat model\n\nNo frontmatter, repo doc.\n",
        })
        self.assertFalse(any("THREAT_MODEL.md" in i for i in issues))

    def test_vault_note_still_requires_frontmatter(self):
        # Regression guard: the repo-doc exemption must stay scoped to
        # README/CLAUDE/SECURITY and docs/schemas/tests, not swallow real notes.
        issues, _ = issues_for({
            "Properties/A.md": note(),
            "Properties/No Frontmatter.md": "Just body text, no frontmatter.\n",
        })
        self.assertTrue(any("No Frontmatter.md" in i and "frontmatter missing" in i
                             for i in issues))


class TestBrokenNoteDoesNotCrashRun(unittest.TestCase):
    def test_run_continues_past_unreadable_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_vault(Path(tmp), {
                "Properties/Good.md": note(),
            })
            bad = root / "Properties" / "bad_binary.md"
            bad.write_bytes(b"\xff\xfe\x00\x01not valid utf-8 \xff")
            issues, _ = lint.check_vault(root)  # must not raise
            self.assertTrue(any("failed to read/parse" in i for i in issues))
            self.assertFalse(any("Good.md" in i for i in issues))


if __name__ == "__main__":
    unittest.main()
