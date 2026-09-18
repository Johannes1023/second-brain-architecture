---
description: Operating manual for any local AI tool that reads or writes this vault. Read first.
created: 2026-01-01
modified: 2026-01-01
last_verified: 2026-01-01
review: quarterly
status: active
area: System
aliases: [CLAUDE.md, README]
tags: [meta]
---

# This vault: operating manual

This is a template. Replace this notice, the example notes, and the paragraph in `_index.md` with your own portfolio before relying on it, then delete this line.

This folder is a portable, local-only knowledge base for managing a small rental portfolio. Any AI tool that runs entirely on your own hardware, LM Studio, Ollama, llama.cpp, or a local agent script, should be able to read it and know the current state of the portfolio. This file is the single operating manual. `CLAUDE.md` only points here.

## 0. Local-only, by design

> [!IMPORTANT] Hard rule
> Never point a cloud-hosted AI tool (ChatGPT, Claude.ai, Gemini, Copilot, or any hosted API) at this vault, and never paste its contents into one. This vault stores the complete operational record of a rental business, including bank details, tenant identity data, and financial figures, deliberately, because it is only ever read by models that run on your own hardware. Sending that record to a third-party API would defeat the entire design. If you ever need a cloud tool's help with something in this vault, copy only the specific fact you need into that conversation by hand, never a file or an export.

This single rule is why the data policy below looks different from a typical "minimize what you store" guide: the risk that policy defends against, a vendor or a network intercepting your data, does not apply here. The risk that remains is device security, covered in the README's security model section.

## 1. Read order

Stop as soon as you have enough context.

1. `_system/Communication Preferences.md`: how to respond (binding)
2. `NOW.md`: what is active right now (max 30 days old)
3. `_index.md`: map of all notes with one-line descriptions
4. The specific note(s) the task needs

Never scan the whole vault for a general question. Ignore `Archive/`, `_export/`, `.obsidian/` and `*.tar.gz` unless explicitly asked.

## 2. Folder map (flat: max one folder level)

| Path | Contains |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Rules for AI tools |
| `NOW.md` | Current focus, recent developments, upcoming, open questions |
| `_index.md` | Map of every note |
| `_system/` | Instructions to AI, templates, maintenance scripts |
| `_export/` | Generated single-file exports, for a model with no file access. Never edit by hand |
| `Properties/` | One note per property or unit: object data, valuation, ownership |
| `Tenants/` | One note per tenant: lease terms, contact, bank details for rent, handover, correspondence |
| `Finance/` | Rent roll, operating-cost statements, tax-relevant figures |
| `Maintenance/` | Repairs, contractor history, warranties (create on first use) |
| `Legal/` | Lease-law references, index-rent mechanics (create on first use) |
| `Co-Owners/` | Ownership shares, decision log, cost-split agreements (create on first use) |
| `Archive/` | Only if needed: superseded notes, prefix `ARCHIVED` |

Rules: no sub-folders inside areas. If an area grows, split into more files with clear names (`Unit - Ground Floor.md`), not into folders. New top-level folders only after a deliberate decision.

## 3. Hard rules

> [!IMPORTANT] Data policy
> This vault stores what running the portfolio actually requires: owner identity and address, tenant name and contact data, lease terms, bank details for rent and deposits, invoices and receipts, tax-relevant figures, correspondence history. That is a deliberate choice, justified by contract necessity, not an oversight. It is safe only because of rule 0 above: nothing in this vault is ever sent to a third party. See the README's security model for what actually protects this data (device encryption, access control, backup hygiene), since "local" is a network boundary, not a lock.

> [!IMPORTANT] Assumptions are tagged
> If sources conflict and it is not certain which is right, write the most likely value and tag it inline: `#annahme (Quelle: ..., unbestätigt)`. Also add `annahme` to the note's `tags`. Remove the tag once confirmed.

- **One fact, one place.** Each fact lives in exactly one note. Other notes link to it (`[[Note Name]]`) instead of repeating it.
- **Every fact is dated.** Time-dependent statements carry "(Stand YYYY-MM)". Update `modified` and `last_verified` when you touch or verify a note.
- **Update over create.** Search titles and `aliases` before creating a note.
- **Deleting.** Delete notes only when the owner explicitly asks, and then remove every mention. Otherwise superseded notes go to `Archive/` with prefix `ARCHIVED `.
- **Tenant confidentiality between co-owners' other contacts.** This vault is for the owners and their AI tools. Do not repeat its contents to a contractor, an advisor, or anyone outside the ownership group without being asked to.
- **Style in notes:** no em dashes, specific over abstract. One language per note.
- **Never touch `.obsidian/`.**

## 4. Frontmatter (required on every note)

```yaml
---
description: One line. What the note covers and when to read it.
created: YYYY-MM-DD
modified: YYYY-MM-DD
last_verified: YYYY-MM-DD
review: monthly | quarterly | yearly
status: draft | active | evergreen | archived
area: Properties | Tenants | Finance | Maintenance | Legal | Co-Owners | System
aliases: []
tags: []
---
```

- `review`: how often `last_verified` must be refreshed. `lint.py` flags overdue notes.
- `deadline` (optional, `YYYY-MM-DD`): a date-bound item, a notice period, a statement due date, the earliest date for the next index-rent adjustment. `lint.py` flags any `deadline` inside its lookahead window.
- Tenant notes add `lease_start` / `lease_end`. Maintenance notes add `contractor` and `warranty_until`.

## 5. Links and syntax

- Wikilinks by title only: `[[Note Name]]`, `[[Note Name|label]]`. No paths in links. Titles are unique across the vault.
- File names: letters, digits, spaces, `-`. No em dashes, no slashes.
- Callouts: `> [!IMPORTANT]`, `> [!WARNING]`, `> [!NOTE]`, `> [!QUESTION]`. They read fine as plain Markdown in any tool.
- Speculation and forecasts: mark with an explicit note, do not state them as fact.
- Core content must not depend on plugins (Dataview, Templater).

## 6. NOW.md rules

- Sections: Active, Recent developments, Upcoming, Open questions.
- Every line starts with a date `YYYY-MM-DD` or `YYYY-MM` and links the relevant note.
- Entries older than 30 days: move the durable fact into its note, then remove the line.
- Max 3 new lines per session.

## 7. Maintenance

| When | What |
|---|---|
| After every editing session | Update `NOW.md`; update `modified`; run `python3 _system/lint.py` |
| When notes are added or renamed | Run `python3 _system/build_export.py` (regenerates the catalog in `_index.md` and the exports) |
| Monthly | Run lint, clean `NOW.md`, verify notes with `review: monthly`, rebuild exports, check the `deadline` lookahead |
| Before pasting into a local model without file access | Run `build_export.py`, then paste `_export/PORTFOLIO.md` (short) or `_export/PORTFOLIO-full.md` (complete) |

Source of truth: this vault. Nothing else holds a newer version of these facts, because nothing else ever receives a copy.

## 8. Tool notes

- **LM Studio (recommended):** point it at this folder if you are running an agent framework with file access, or paste `_export/PORTFOLIO.md` into the system prompt if you are using the plain chat UI with a model like Gemma.
- **Ollama or llama.cpp with a local agent script:** follow the read order above; the convention does not require any particular runtime.
- **Any local file-reading agent:** `AGENTS.md` is picked up by convention.
- **Chat UI with no file access:** use `_export/PORTFOLIO.md` as a system prompt or project file.
