#!/usr/bin/env python3
import sys; sys.dont_write_bytecode = True
"""Vault health check.
Usage: python3 _system/lint.py [--vault PATH] [--deadline-days N] [--format text|json]

Checks: frontmatter completeness and validity, broken wikilinks (titles and
aliases), duplicate titles/aliases, folder depth, em dashes, overdue reviews,
upcoming or passed deadlines, stale NOW.md lines, open assumptions (#annahme),
frontmatter parse issues (duplicate keys, unterminated quotes/lists), and
missing files referenced from Documents/.

This vault is local-only by design (see AGENTS.md rule 0), so this linter does
NOT scan for "sensitive" data such as IBANs or IDs: storing that data here is
intentional, not a leak. If you ever export or copy content out of this vault,
that is the moment to think about what leaves, not before.

Exit codes: 0 = clean, 1 = issues found, 2 = usage or internal error (bad
--vault path, a crash while reading the vault). A single unreadable or
malformed note is reported as an issue, never a crash: --vault pointing at
something that is not a vault at all is what exits 2.
"""
import argparse
import json as jsonlib
import re
from datetime import date, datetime

import vaultlib

REQUIRED = ["description", "created", "modified", "last_verified", "review", "status", "area"]
REVIEW_DAYS = {"monthly": 31, "quarterly": 92, "yearly": 366}
VALID_STATUS = {"draft", "active", "evergreen", "archived"}
VALID_AREA = {
    "Properties", "Tenants", "Finance", "Taxes", "Maintenance", "Legal",
    "Property Management", "Co-Owners", "System",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WIKILINK = re.compile(r"!?\[\[([^\]|#^]+)")
DOC_REF = re.compile(r"`(Documents/[^`]+)`")


def check_vault(root, deadline_days=30):
    """Runs every check against `root` and returns (issues, notices) as lists
    of strings. Pure function: no printing, no sys.exit. This is what a test
    or another tool should call directly instead of shelling out."""
    today = date.today()
    issues, notices = [], []

    files = list(vaultlib.notes(root=root, include_templates=False))
    parsed = []
    for p in files:
        try:
            meta, body, has_fm = vaultlib.parse(p)
            pissues = vaultlib.parse_issues(p)
        except Exception as e:  # noqa: BLE001 - a broken note must not crash the run
            issues.append(f"{p.relative_to(root)}: failed to read/parse ({e})")
            continue
        parsed.append((p, p.relative_to(root), meta, body, has_fm))
        for pi in pissues:
            issues.append(f"{p.relative_to(root)}: {pi}")

    titles_map = {}
    for p, rel, meta, body, has_fm in parsed:
        titles_map.setdefault(p.stem, []).append(rel)
    for stem, rels in titles_map.items():
        if len(rels) > 1:
            issues.append(f"duplicate title '{stem}' used by: {', '.join(str(r) for r in rels)}")

    alias_map = {}
    for p, rel, meta, body, has_fm in parsed:
        aliases = meta.get("aliases")
        if isinstance(aliases, list):
            for a in aliases:
                alias_map.setdefault(a, []).append(rel)
    for alias, rels in alias_map.items():
        if len(rels) > 1:
            issues.append(f"duplicate alias '{alias}' used by: {', '.join(str(r) for r in rels)}")
        if alias in titles_map:
            issues.append(
                f"alias '{alias}' (used by {rels[0]}) collides with an existing note title")

    resolvable = set(titles_map) | set(alias_map)

    for p, rel, meta, body, has_fm in parsed:
        body_no_code = re.sub(r"```.*?```", "", body, flags=re.S)
        body_no_code = re.sub(r"`[^`\n]*`", "", body_no_code)
        is_rules = rel.name in ("AGENTS.md", "CLAUDE.md") or rel.parts[0] == "_system"
        is_repo_doc = (rel.name in ("CLAUDE.md", "README.md", "SECURITY.md")
                        or rel.parts[0] in ("docs", "schemas", "tests"))

        if len(rel.parts) > 2:
            issues.append(f"{rel}: nested deeper than one folder")
        if "—" in p.name:
            issues.append(f"{rel}: em dash in file name")

        if not is_repo_doc:
            missing = [k for k in REQUIRED if k not in meta]
            if missing:
                issues.append(f"{rel}: frontmatter missing {', '.join(missing)}")
            status = meta.get("status")
            if isinstance(status, str) and status not in VALID_STATUS:
                issues.append(f"{rel}: invalid status '{status}'")
            area = meta.get("area")
            if isinstance(area, str) and area not in VALID_AREA:
                issues.append(f"{rel}: invalid area '{area}'")
            review = meta.get("review")
            if isinstance(review, str) and review not in REVIEW_DAYS:
                issues.append(f"{rel}: invalid review cadence '{review}'")
            for datefield in ("created", "modified", "last_verified"):
                v = meta.get(datefield)
                if isinstance(v, str) and not DATE_RE.match(v):
                    issues.append(f"{rel}: bad {datefield} '{v}', expected YYYY-MM-DD")

        for t in WIKILINK.findall(body_no_code):
            t = t.strip()
            if t and t not in resolvable:
                issues.append(f"{rel}: broken link [[{t}]]")

        for docref in DOC_REF.findall(body):
            if ".." in docref:
                issues.append(f"{rel}: document reference escapes the vault: `{docref}`")
            elif not (root / docref).exists():
                issues.append(f"{rel}: linked document not found: `{docref}`")

        if "—" in body_no_code and not is_rules:
            issues.append(f"{rel}: contains em dash")

        lv, rv = meta.get("last_verified"), meta.get("review")
        if isinstance(lv, str) and rv in REVIEW_DAYS and DATE_RE.match(lv):
            verified = datetime.strptime(lv, "%Y-%m-%d").date()
            if verified > today:
                issues.append(f"{rel}: last_verified '{lv}' is in the future")
            else:
                age = (today - verified).days
                if age > REVIEW_DAYS[rv]:
                    issues.append(f"{rel}: review overdue ({rv}, last verified {lv})")

        dl = meta.get("deadline")
        if isinstance(dl, str):
            if DATE_RE.match(dl):
                d = datetime.strptime(dl, "%Y-%m-%d").date()
                days_out = (d - today).days
                if 0 <= days_out <= deadline_days:
                    issues.append(f"{rel}: deadline in {days_out} day(s) ({dl})")
                elif days_out < 0:
                    issues.append(f"{rel}: deadline passed ({dl})")
            else:
                issues.append(f"{rel}: bad deadline '{dl}', expected YYYY-MM-DD")

        n = body_no_code.count("#annahme")
        if n:
            notices.append(f"{rel}: {n} open assumption(s)")

    now = root / "NOW.md"
    if now.exists():
        for line in now.read_text(encoding="utf-8").splitlines():
            m = re.match(r"- (\d{4}-\d{2}(?:-\d{2})?)", line)
            if not m:
                continue
            d = m.group(1) + ("-01" if len(m.group(1)) == 7 else "")
            try:
                dt = datetime.strptime(d, "%Y-%m-%d").date()
            except ValueError:
                issues.append(f"NOW.md: unparseable date in line: {line[:70]}")
                continue
            if (today - dt).days > 30 and dt <= today:
                issues.append(f"NOW.md: older than 30 days, move into its note: {line[:70]}")

    marker = root / ".sensitive-vault"
    placeholder_index = root / "_index.md"
    still_template = False
    if placeholder_index.exists():
        still_template = "[Replace this paragraph" in placeholder_index.read_text(encoding="utf-8")
    if not marker.exists() and not still_template:
        notices.append(
            "vault-marker: no .sensitive-vault file found. If this is a real portfolio "
            "(not the shipped template), consider creating one with init_vault.py "
            "or by hand, see SECURITY.md.")

    return issues, notices


def main(argv=None):
    ap = argparse.ArgumentParser(description="Vault health check.")
    ap.add_argument("--vault", default=None,
                     help="Path to the vault root. Default: SECOND_BRAIN_ROOT env var, "
                          "else the folder two levels above this script.")
    ap.add_argument("--deadline-days", type=int, default=30,
                     help="Lookahead window for upcoming deadlines, in days (default: 30).")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args(argv)

    try:
        root = vaultlib.resolve_root(args.vault)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2

    try:
        issues, notices = check_vault(root, deadline_days=args.deadline_days)
    except Exception as e:  # noqa: BLE001 - report, don't traceback
        print(f"internal error while linting {root}: {e}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(jsonlib.dumps(
            {"root": str(root), "issues": issues, "notices": notices}, indent=2))
    else:
        print(f"Checked vault at {root}")
        print(f"\nISSUES ({len(issues)})")
        for i in issues:
            print("  -", i)
        print(f"\nNOTICES ({len(notices)})")
        for i in notices:
            print("  -", i)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
