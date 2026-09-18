#!/usr/bin/env python3
import sys; sys.dont_write_bytecode = True
"""Vault health check. Usage: python3 _system/lint.py [--deadline-days N]
Checks: frontmatter, broken wikilinks, folder depth, em dashes, overdue reviews,
upcoming deadlines, stale NOW.md lines, open assumptions (#annahme).

This vault is local-only by design (see AGENTS.md rule 0), so this linter does
NOT scan for "sensitive" data such as IBANs or IDs: storing that data here is
intentional, not a leak. If you ever export or copy content out of this vault,
that is the moment to think about what leaves, not before.
"""
import re
from datetime import date, datetime
from vaultlib import ROOT, notes, parse

TODAY = date.today()
DEADLINE_LOOKAHEAD_DAYS = 30
REQUIRED = ["description", "created", "modified", "last_verified", "review", "status", "area"]
REVIEW_DAYS = {"monthly": 31, "quarterly": 92, "yearly": 366}
WIKILINK = re.compile(r"!?\[\[([^\]|#^]+)")

issues, infos = [], []
files = list(notes(include_templates=False))
titles = {p.stem for p in files}

for p in files:
    rel = p.relative_to(ROOT)
    meta, body, has_fm = parse(p)
    body_no_code = re.sub(r"```.*?```", "", body, flags=re.S)
    body_no_code = re.sub(r"`[^`\n]*`", "", body_no_code)
    is_rules = rel.name in ("AGENTS.md", "CLAUDE.md") or rel.parts[0] == "_system"

    if len(rel.parts) > 2:
        issues.append(f"{rel}: nested deeper than one folder")
    if "—" in p.name:
        issues.append(f"{rel}: em dash in file name")
    if rel.name != "CLAUDE.md":
        missing = [k for k in REQUIRED if k not in meta]
        if missing:
            issues.append(f"{rel}: frontmatter missing {', '.join(missing)}")

    for t in WIKILINK.findall(body_no_code):
        t = t.strip()
        if t and t not in titles:
            issues.append(f"{rel}: broken link [[{t}]]")

    if "—" in body_no_code and not is_rules:
        issues.append(f"{rel}: contains em dash")

    lv, rv = meta.get("last_verified"), meta.get("review")
    if isinstance(lv, str) and rv in REVIEW_DAYS:
        try:
            age = (TODAY - datetime.strptime(lv, "%Y-%m-%d").date()).days
            if age > REVIEW_DAYS[rv]:
                issues.append(f"{rel}: review overdue ({rv}, last verified {lv})")
        except ValueError:
            issues.append(f"{rel}: bad last_verified '{lv}'")

    dl = meta.get("deadline")
    if isinstance(dl, str):
        try:
            d = datetime.strptime(dl, "%Y-%m-%d").date()
            days_out = (d - TODAY).days
            if 0 <= days_out <= DEADLINE_LOOKAHEAD_DAYS:
                issues.append(f"{rel}: deadline in {days_out} day(s) ({dl})")
            elif days_out < 0:
                issues.append(f"{rel}: deadline passed ({dl})")
        except ValueError:
            issues.append(f"{rel}: bad deadline '{dl}'")

    n = body_no_code.count("#annahme")
    if n:
        infos.append(f"{rel}: {n} open assumption(s)")

now = ROOT / "NOW.md"
if now.exists():
    section = ""
    for line in now.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line
        m = re.match(r"- (\d{4}-\d{2}(?:-\d{2})?)", line)
        if m and section.startswith("## Recent"):
            d = m.group(1) + ("-01" if len(m.group(1)) == 7 else "")
            dt = datetime.strptime(d, "%Y-%m-%d").date()
            if (TODAY - dt).days > 30 and dt <= TODAY:
                issues.append(f"NOW.md: older than 30 days, move into its note: {line[:70]}")

print(f"Checked {len(files)} notes on {TODAY}")
print(f"\nISSUES ({len(issues)})")
for i in issues:
    print("  -", i)
print(f"\nOPEN ASSUMPTIONS ({len(infos)} notes)")
for i in infos:
    print("  -", i)
sys.exit(1 if issues else 0)
