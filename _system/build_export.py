#!/usr/bin/env python3
import sys; sys.dont_write_bytecode = True
"""Regenerates the note catalog in _index.md and builds single-file exports.
Usage: python3 _system/build_export.py
  _export/PORTFOLIO.md       short brief for a chat UI with no file access
  _export/PORTFOLIO-full.md  every note, concatenated, for the same case

This vault is local-only by design (see AGENTS.md rule 0): both exports include
every note, with no tier or redaction step, because nothing produced here is
ever meant to leave your own hardware. If you build a version of this vault
that syncs to a cloud-backed tool, that assumption no longer holds and this
script would need a filter added back in.
"""
from datetime import date
from vaultlib import ROOT, notes, parse

START, END = "<!-- catalog:start -->", "<!-- catalog:end -->"
ORDER = ["System", "Properties", "Tenants", "Finance", "Maintenance", "Legal", "Co-Owners"]


def catalog():
    rows = {}
    for p in notes(include_system=True):
        if p.parent == ROOT:
            continue
        meta, _, _ = parse(p)
        rows.setdefault(meta.get("area", "Other"), []).append(
            f"- [[{p.stem}]]: {meta.get('description', '')}")
    out = []
    for area in ORDER + sorted(set(rows) - set(ORDER)):
        if area in rows:
            out.append(f"\n### {area}\n")
            out.extend(rows[area])
    return "\n".join(out).strip()


def body_of(rel):
    _, body, _ = parse(ROOT / rel)
    return body.strip()


cat = catalog()
idx = ROOT / "_index.md"
text = idx.read_text(encoding="utf-8")
head, rest = text.split(START, 1)
tail = rest.split(END, 1)[1]
idx.write_text(f"{head}{START}\n{cat}\n{END}{tail}", encoding="utf-8")

stamp = date.today().isoformat()
(ROOT / "_export").mkdir(exist_ok=True)

short = [
    f"# Portfolio brief (export {stamp})",
    "Generated from this vault. Do not edit; rebuild with build_export.py.",
    body_of("_system/Communication Preferences.md"),
    body_of("NOW.md"),
    "# Catalog\n\nFull details exist in the vault / PORTFOLIO-full.md.\n\n" + cat,
]
(ROOT / "_export/PORTFOLIO.md").write_text("\n\n---\n\n".join(short) + "\n", encoding="utf-8")

full = [f"# Portfolio, full export ({stamp})",
        "Every note in the vault. Generated; do not edit."]
for p in notes(include_system=True):
    meta, body, _ = parse(p)
    if p.name == "CLAUDE.md":
        continue
    full.append(f"<!-- source: {p.relative_to(ROOT)} | verified {meta.get('last_verified', '?')} -->\n{body.strip()}")
(ROOT / "_export/PORTFOLIO-full.md").write_text("\n\n---\n\n".join(full) + "\n", encoding="utf-8")

for f in ("_export/PORTFOLIO.md", "_export/PORTFOLIO-full.md"):
    s = (ROOT / f).read_text(encoding="utf-8")
    print(f"{f}: {len(s)} chars, ~{len(s)//4} tokens")
