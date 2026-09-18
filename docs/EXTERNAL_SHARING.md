# External sharing and export tiers

Everything this vault stores is sensitive by default (see `SECURITY.md`). This document is about the one case where something needs to leave the vault anyway, such as a figure for a tax advisor, a note for a co-owner, or an answer for a contractor, and what this repository currently gives you for that versus what is designed but not yet built.

## The three tiers, as designed

| Tier | Contents | Where it may go | Status |
|---|---|---|---|
| `local-full` | Every note, unredacted, concatenated | Stays on the machine that built it; pasted into a local model with no file access | **Implemented**: this is `_export/PORTFOLIO-full.md`, built by `build_export.py` |
| `local-scoped` | A shorter brief: communication preferences, `NOW.md`, and the catalog (titles and one-line descriptions, not full note bodies) | Stays on the machine that built it; pasted into a local model with no file access when the full export is more than the model needs | **Implemented, but not redacted**: this is `_export/PORTFOLIO.md`. It is *shorter* than the full export, not *safer*: descriptions and titles can still name tenants, addresses, or figures. Treat it exactly as sensitively as `local-full` |
| `external-redacted` (the "Approved-Outbox" tier) | Only fields explicitly marked shareable, for a specific external recipient, with everything else stripped | Outside the local-only boundary, deliberately, to a tax advisor, a co-owner without vault access, a contractor | **Not implemented.** No such export exists in `build_export.py` today |

## Why the third tier matters, and why it isn't just "redact the full export"

A tax advisor needs specific figures, not the tenant correspondence history sitting next to them in the same note. A co-owner without vault access might need the decision log in `Co-Owners/`, not the tenants' bank details in `Finance/`. Doing this safely means the vault owner explicitly marking which fields, or which whole notes, are approved to leave, per recipient, rather than trusting a general-purpose redaction pass to guess correctly every time (a redaction filter that misses one field is a leak; a field that was never marked shareable in the first place cannot leak through this path).

The planned design, not yet built:

1. A field- or note-level `shareable: true` marker (or an explicit allowlist file) that a human sets deliberately, per note or per field, never by default.
2. A new export mode, something like `python3 _system/build_export.py --outbox <recipient-name>`, that includes only what's marked for that recipient and fails loudly (like `build_export.py`'s existing duplicate-title refusal) if the request would include something not marked.
3. Output written somewhere clearly distinct from `_export/` (an `_export/outbox/<recipient>/` path has been discussed but not decided), so it's never confused with the two local-only exports at a glance.

## Until that tier exists

- Treat `PORTFOLIO.md` and `PORTFOLIO-full.md` as fully sensitive. Neither is meant to leave the machine that built it.
- If you need to share something specific today, copy the specific fact by hand into whatever channel you're sharing it through (an email, a message to your tax advisor), the same guidance `AGENTS.md` rule 0 already gives for a cloud AI tool: copy the fact, never the file.
- Do not build an ad hoc export script for "just this once" sharing need without going back to `SECURITY.md` and this document first; an unreviewed one-off script is exactly how a redaction gap gets introduced.
