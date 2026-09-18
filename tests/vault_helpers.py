"""Test-only helper for building small, fully synthetic vaults on disk.

Every test in this suite runs against a vault built fresh in a temp directory
by this helper: no fixture files are committed to the repo, and nothing here
ever reads or references the shipped example notes in Properties/, Tenants/,
or Finance/. That keeps the test suite honest about the "fictional data only"
rule this repository holds itself to (see README.md's closing note): a test
vault is generated code, not a data file someone could mistake for real.
"""
import sys
from datetime import date
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = TESTS_DIR.parent / "_system"
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

TODAY = date.today().isoformat()


def build_vault(root: Path, notes: dict, now_md: str = None):
    """Writes `notes` (relative path -> content) under `root`, plus a minimal
    valid NOW.md and _index.md unless the caller already included one. Every
    directory needed for a note's path is created automatically."""
    for rel, content in notes.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    if "NOW.md" not in notes:
        body = (now_md if now_md is not None else
                 "## Active\n\n## Recent developments\n\n## Upcoming\n\n## Open questions\n")
        (root / "NOW.md").write_text(note(
            description="Test NOW.md.", area="System", body=body), encoding="utf-8")

    if "_index.md" not in notes:
        (root / "_index.md").write_text(note(
            description="Test index.", area="System",
            body="# Vault Index\n\nTest vault.\n\n"
                 "<!-- catalog:start -->\n<!-- catalog:end -->\n"), encoding="utf-8")
    return root


def note(description="Test note.", area="Properties", body="Body text.", **overrides):
    """Builds one note's full text: valid frontmatter plus a body. Pass
    overrides like `review="monthly"` or `deadline="2026-01-01"` to vary a
    single field without retyping the whole block."""
    fields = {
        "description": description,
        "created": TODAY,
        "modified": TODAY,
        "last_verified": TODAY,
        "review": "quarterly",
        "status": "active",
        "area": area,
        "aliases": "[]",
        "tags": "[]",
    }
    fields.update(overrides)

    def fmt(v):
        if isinstance(v, list):
            return "[" + ", ".join(v) + "]"
        return str(v)

    lines = ["---"] + [f"{k}: {fmt(v)}" for k, v in fields.items()] + ["---", "", body]
    return "\n".join(lines) + "\n"
