"""Shared helpers for lint.py and build_export.py. No third-party dependencies."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".obsidian", "Archive", "_export", ".git"}
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def notes(include_system=True, include_templates=False):
    for p in sorted(ROOT.rglob("*.md")):
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if not include_system and rel.parts[0] == "_system":
            continue
        if not include_templates and p.name.startswith("Template - "):
            continue
        yield p


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                v = v.strip()
                if v.startswith("[") and v.endswith("]"):
                    v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
                elif v.startswith('"') and v.endswith('"'):
                    v = v[1:-1]
                meta[k.strip()] = v
        body = text[m.end():]
    else:
        body = text
    return meta, body, bool(m)
