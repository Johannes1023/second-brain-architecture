#!/usr/bin/env python3
import sys; sys.dont_write_bytecode = True
"""Regenerates the note catalog in _index.md and builds single-file exports.
Usage: python3 _system/build_export.py [--vault PATH]
  _export/PORTFOLIO.md       short brief for a chat UI with no file access
  _export/PORTFOLIO-full.md  every note, concatenated, for the same case

This vault is local-only by design (see AGENTS.md rule 0): both exports include
every note, with no tier or redaction step, because nothing produced here is
ever meant to leave your own hardware. This script only ever writes into the
vault it was pointed at (its own _export/ folder), never anywhere else.

Writes are atomic: each output is written to a temporary file next to its
final path and then moved into place, so a crash or a full disk mid-write
cannot leave a half-written _index.md or export behind.
"""
import argparse
import os
import sys
from datetime import date

import vaultlib

START, END = "<!-- catalog:start -->", "<!-- catalog:end -->"
ORDER = ["System", "Properties", "Tenants", "Finance", "Taxes", "Maintenance",
         "Legal", "Property Management", "Co-Owners"]


def _atomic_write(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def catalog(root):
    """Returns (catalog_text, duplicate_titles). A duplicate title is a real
    problem (which note does [[Title]] even point to?), so the caller decides
    whether to refuse to write rather than silently pick one."""
    rows, seen, dupes = {}, set(), set()
    for p in vaultlib.notes(root=root, include_system=True):
        if p.parent == root:
            continue
        if p.stem in seen:
            dupes.add(p.stem)
        seen.add(p.stem)
        meta, _, _ = vaultlib.parse(p)
        rows.setdefault(meta.get("area", "Other"), []).append(
            f"- [[{p.stem}]]: {meta.get('description', '')}")
    out = []
    for area in ORDER + sorted(set(rows) - set(ORDER)):
        if area in rows:
            out.append(f"\n### {area}\n")
            out.extend(rows[area])
    return "\n".join(out).strip(), dupes


def body_of(root, rel):
    _, body, _ = vaultlib.parse(root / rel)
    return body.strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rebuild the vault catalog and exports.")
    ap.add_argument("--vault", default=None,
                     help="Path to the vault root. Default: SECOND_BRAIN_ROOT env var, "
                          "else the folder two levels above this script.")
    args = ap.parse_args(argv)

    try:
        root = vaultlib.resolve_root(args.vault)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2

    cat, dupes = catalog(root)
    if dupes:
        print("Refusing to write: duplicate note title(s) would make [[links]] ambiguous:",
              file=sys.stderr)
        for d in sorted(dupes):
            print(f"  - {d}", file=sys.stderr)
        print("Run _system/lint.py for the full list of files involved.", file=sys.stderr)
        return 2

    idx = root / "_index.md"
    if not idx.exists():
        print(f"error: {idx} not found, is --vault pointed at a real vault root?",
              file=sys.stderr)
        return 2
    text = idx.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"error: {idx} is missing the {START} / {END} catalog markers", file=sys.stderr)
        return 2
    head, rest = text.split(START, 1)
    tail = rest.split(END, 1)[1]
    _atomic_write(idx, f"{head}{START}\n{cat}\n{END}{tail}")

    stamp = date.today().isoformat()
    export_dir = root / "_export"
    export_dir.mkdir(exist_ok=True)

    short = [
        f"# Portfolio brief (export {stamp})",
        "Generated from this vault. Do not edit; rebuild with build_export.py.",
        body_of(root, "_system/Communication Preferences.md"),
        body_of(root, "NOW.md"),
        "# Catalog\n\nFull details exist in the vault / PORTFOLIO-full.md.\n\n" + cat,
    ]
    _atomic_write(export_dir / "PORTFOLIO.md", "\n\n---\n\n".join(short) + "\n")

    full = [f"# Portfolio, full export ({stamp})",
            "Every note in the vault. Generated; do not edit."]
    for p in vaultlib.notes(root=root, include_system=True):
        meta, body, _ = vaultlib.parse(p)
        if p.name == "CLAUDE.md":
            continue
        full.append(
            f"<!-- source: {p.relative_to(root)} | verified {meta.get('last_verified', '?')} -->"
            f"\n{body.strip()}")
    _atomic_write(export_dir / "PORTFOLIO-full.md", "\n\n---\n\n".join(full) + "\n")

    for f in ("_export/PORTFOLIO.md", "_export/PORTFOLIO-full.md"):
        s = (root / f).read_text(encoding="utf-8")
        print(f"{f}: {len(s)} chars, ~{len(s) // 4} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
