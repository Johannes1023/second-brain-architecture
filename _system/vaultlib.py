"""Shared helpers for lint.py and build_export.py. No third-party dependencies.

Frontmatter format supported by parse(): a restricted, hand-parsed subset of
YAML, documented in full in schemas/note-frontmatter.schema.json. Supported:
plain scalars, quoted string scalars ("..."), inline lists ([a, "b, c", d]),
full-line comments (a line whose stripped text starts with '#'), and blank
values. Not supported: multi-line scalars, nested mappings, YAML anchors.
A file using any of those is not rejected outright, it is parsed as far as
this format allows and the rest is treated as body text, which is a silent
misparse worth knowing about. parse_issues() is the function that surfaces
what parse() cannot: duplicate keys, unterminated quotes, unterminated lists.
"""
import os
import re
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".obsidian", "Archive", "_export", ".git"}
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)

# Module-level default, kept for backward compatibility with any script or
# notebook that still does `from vaultlib import ROOT`. New code should not
# rely on this: resolve_root() plus an explicit `root=` argument to notes()
# is the supported path, because a value imported with `from vaultlib import
# ROOT` is a snapshot taken at import time, and later reassigning
# vaultlib.ROOT elsewhere does not change that already-bound name.
ROOT = DEFAULT_ROOT


def resolve_root(cli_value=None):
    """Resolve the vault root a script should operate on.

    Priority: an explicit --vault value, then the SECOND_BRAIN_ROOT
    environment variable, then the folder two levels above this script
    (which is correct both for the shipped example vault and for a real
    vault created by init_vault.py, since that tool copies these scripts
    into the new vault's own _system/ folder).

    An explicit --vault or SECOND_BRAIN_ROOT that does not resolve to a
    real directory is a hard error (SystemExit), never a silent fallback
    to a different, unvalidated location.
    """
    if cli_value:
        root = Path(cli_value).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"--vault path does not exist or is not a directory: {root}")
        return root
    env_value = os.environ.get("SECOND_BRAIN_ROOT")
    if env_value:
        root = Path(env_value).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(
                f"SECOND_BRAIN_ROOT does not exist or is not a directory: {root}")
        return root
    return DEFAULT_ROOT


def notes(root=None, include_system=True, include_templates=False):
    root = root or ROOT
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if not include_system and rel.parts[0] == "_system":
            continue
        if not include_templates and p.name.startswith("Template - "):
            continue
        yield p


def _split_list_items(inner):
    """Split the inside of an inline YAML-ish list, respecting quoted commas.
    "a, \"b, c\", d" -> ["a", "b, c", "d"]. Unterminated quotes leave a stray
    quote character in the item rather than raising; parse_issues() is what
    catches that case and reports it, this function stays lenient."""
    items, buf, in_quotes = [], [], False
    for ch in inner:
        if ch == '"':
            in_quotes = not in_quotes
            buf.append(ch)
        elif ch == "," and not in_quotes:
            items.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        items.append("".join(buf).strip())
    cleaned = []
    for it in items:
        it = it.strip()
        if len(it) >= 2 and it.startswith('"') and it.endswith('"'):
            it = it[1:-1]
        if it:
            cleaned.append(it)
    return cleaned


def _parse_frontmatter_lines(lines):
    """Core line-by-line parser shared by parse() and parse_issues().
    Returns (meta, issues). meta values are str or list[str]. Duplicate keys
    keep the LAST value (matching how a real YAML loader behaves), the
    overwrite itself is reported as an issue, never silently swallowed."""
    meta = {}
    issues = []
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            # Indented continuation lines (nested mappings, multi-line
            # scalars) are outside the supported subset. Skip rather than
            # misinterpret as a new top-level key.
            continue
        if ":" not in line:
            issues.append(f"unrecognized frontmatter line (no ':'): {stripped!r}")
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if k in meta:
            issues.append(f"duplicate frontmatter key '{k}' (last value wins)")
        if v.startswith("["):
            if not v.endswith("]"):
                issues.append(f"'{k}': unterminated list value: {v!r}")
                meta[k] = v
            else:
                meta[k] = _split_list_items(v[1:-1])
        elif v.startswith('"'):
            if not (len(v) >= 2 and v.endswith('"')):
                issues.append(f"'{k}': unterminated quoted value: {v!r}")
                meta[k] = v
            else:
                meta[k] = v[1:-1]
        else:
            meta[k] = v
    return meta, issues


def parse(path):
    """Returns (meta, body, has_frontmatter). Best-effort: never raises on a
    malformed file, so a single broken note cannot crash a full-vault run.
    Call parse_issues() alongside this to learn what, if anything, could not
    be parsed cleanly."""
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return {}, text, False
    meta, _issues = _parse_frontmatter_lines(m.group(1).splitlines())
    body = text[m.end():]
    return meta, body, True


def parse_issues(path):
    """Structural frontmatter problems vaultlib itself can detect, independent
    of any higher-level schema check (missing required fields, invalid enum
    values, etc. are lint.py's job, not this module's): duplicate keys,
    unterminated quotes, unterminated lists, and lines that look like they
    were meant to be a key but have no colon."""
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return []
    _meta, issues = _parse_frontmatter_lines(m.group(1).splitlines())
    return issues
