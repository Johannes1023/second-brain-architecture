A Second Brain for Real Estate Investing: A Local-Only AI Memory System for Property Management

A portable, plain-text knowledge base that gives a fully local AI model, running in LM Studio, Ollama, or any offline runner, persistent, structured context about a rental property portfolio. Nothing in this vault is ever sent to a cloud API. That single constraint is the design.

## TL;DR

- Plain Markdown files in a flat folder structure, versioned in git, covering every property, tenant, lease, and deadline a small landlord manages.
- Built to be read exclusively by models that run on your own hardware. No cloud tool ever touches this vault, by rule, not by convention.
- Because nothing leaves the machine, the vault stores the complete operational record: owner identity, tenant data, bank details for rent transfers, invoices, tax-relevant figures. There is no redaction layer, because there is nothing to redact from.
- One universal operating manual (`AGENTS.md`) that any local agent reads first, so it behaves like a briefed property manager on the first message.
- Two dependency-free Python scripts generate an index and single-file exports and run a linter for schema completeness, broken links, stale reviews and upcoming deadlines.
- Ships as a working template: real folder structure, real templates, real example notes with fictional data, real scripts that run out of the box. Clone it, replace the examples with your own portfolio, done.

## The problem this solves

Running a small rental portfolio without a management company means holding a lot of state in your head or scattered across email threads, PDFs, and spreadsheets: which lease is eligible for its next index-linked rent adjustment, when the operating-cost statement for a given unit is due, what a contractor quoted for a repair eight months ago, what the handover protocol recorded at move-in. AI assistants are a natural fit for this kind of work, drafting a rent-adjustment letter, checking a cost statement against a lease, summarizing a maintenance history, but only if they have the underlying facts, and the underlying facts here include bank details, tenant identity data, and financial figures that have no business anywhere near a cloud vendor's servers.

Most people solve this by either avoiding AI tools for anything sensitive, which means doing that work by hand, or by using a cloud tool anyway and hoping the vendor's data handling is fine with it. This repository is a third option: build the AI's context entirely offline, so the question of whether a cloud vendor should see your bank details never comes up, because it never can.

## The security model, precisely

"Local" is a network boundary. It removes exactly one risk: a third party receiving your data because you sent it to their API. It does not remove device theft, malware, a misconfigured backup, or a git remote pushed somewhere by accident. Getting this precise matters, because "it's local so it's safe" is the kind of claim that falls apart the first time someone asks a follow-up question.

What actually protects this vault, once it holds real bank details and tenant data:

| Control | What it addresses |
|---|---|
| Full-disk encryption on every device the vault lives on | Device theft or loss |
| No cloud sync of the raw vault folder (a NAS on your own LAN, or an encrypted sync tool, is fine; a consumer cloud drive is not) | Backup exposure |
| Git kept local, or pushed only to a private remote you control, never a public one | Accidental disclosure, and the fact that git history keeps everything forever, deletions included |
| OS-level access control if the vault sits on a shared machine or NAS | Other users or accounts on the same hardware |
| The hard rule in `AGENTS.md`: never point a cloud-backed tool at this vault, never paste an export into one | The one risk local-only actually solves |

None of this is exotic. It is the same baseline you would want for any folder holding bank statements, and it is achievable with tools you likely already have.

### A note on the GDPR, for anyone tempted to skip it because this is "just local"

Running this vault does not exempt you from data protection law. A private landlord processing tenant personal data is a controller under the GDPR regardless of where the data is stored, and the household exemption does not cover letting property as an economic activity. The reason the data categories below are fine to store is not that they are local, it is that they are necessary to perform the tenancy contract (Art. 6(1)(b) GDPR): you cannot collect rent without bank details, cannot issue a compliant invoice without an address, cannot enforce a deposit claim without a handover record. Data minimisation (Art. 5(1)(c)) is satisfied because every field below earns its place in running the tenancy, not because a field-level filter removed anything. Local-only changes the security architecture. It does not change the legal basis, and it does not change your retention obligations once a tenancy ends.

## What this vault stores

Everything the tenancy relationship actually requires, at the resolution that requires:

- Owner identity, address, and the role each owner plays (see `Co-Owners/`)
- Tenant name, contact details, lease terms, deposit amount and where it is held
- Bank details for rent and deposit transfers
- Invoices, receipts, and contractor details for maintenance
- Tax-relevant figures: rent history, operating-cost statements, depreciation
- Correspondence history and handover protocols

There is no separate "restricted" tier and no export-time redaction, because every export this vault produces is for a model running on the same hardware the data already lives on. If you ever adapt this template to also work with a cloud tool, that assumption breaks, and you would need to reintroduce a filtering step, not remove one.

## Architecture

### Folder map

```
vault/
├── AGENTS.md       # Operating manual for any local AI tool (read first)
├── CLAUDE.md       # One-line pointer to AGENTS.md (tool-convention compatibility)
├── NOW.md          # Rolling log: open deadlines, recent changes, current focus
├── _index.md       # Generated map of every note with a one-line description
├── _system/        # Rules for AI, note templates, maintenance scripts
├── _export/        # Generated single-file exports, for a model with no file access
├── Properties/     # One note per property or unit: object data, valuation, ownership
├── Tenants/        # One note per tenant: lease terms, bank details, correspondence
├── Finance/        # Rent roll, operating-cost statements, tax-relevant figures
├── Maintenance/    # Repairs, contractor history, warranties (create on first use)
├── Legal/          # Lease-law references, index-rent mechanics (create on first use)
├── Co-Owners/      # Ownership shares, decision log (create on first use)
└── Archive/        # Superseded leases and closed cases (create on demand)
```

One folder level, period. This is a deliberate constraint: it forces every note to earn a clear, unique title instead of hiding behind path context, which is exactly what makes wikilink-by-title (`[[Note Name]]`, no paths) work reliably as the portfolio grows.

### Frontmatter schema

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

- `review` feeds the linter: a note tagged `review: quarterly` that hasn't been `last_verified` in 92 days gets flagged as stale, which catches a rent figure that no longer matches the current lease.
- `deadline` (optional, `YYYY-MM-DD`) drives date-bound work: notice periods, statement due dates, index-rent adjustment windows. The linter flags any `deadline` inside a lookahead window, and flags one already passed.
- Tenant notes add `lease_start` / `lease_end`. Maintenance notes add `contractor` and `warranty_until`.

There used to be a `sensitivity` field here (`shared` / `owner-only` / `restricted`) in an earlier, cloud-hybrid version of this design. It existed only to control what a redaction step removed before an export left the machine. Once nothing ever leaves the machine, that field has no job left to do, so it is gone. If you fork this for a setup where you do sometimes want a cloud tool involved, that is the field you would need to bring back, along with the export-time filtering it used to drive.

### The read order

```mermaid
flowchart TD
    A[Local AI opens the vault] --> B["_system/Communication Preferences.md<br/>(binding response rules)"]
    B --> C["NOW.md<br/>(open deadlines, current focus)"]
    C --> D["_index.md<br/>(map of every note)"]
    D --> E{Task needs more detail?}
    E -->|Yes| F[Open the specific property/tenant/finance<br/>note(s) named in the index]
    E -->|No| G[Answer]
    F --> G
```

This bounds a typical interaction to four file reads plus whatever notes the task actually needs, instead of a scan that grows with the portfolio. The index grows by one line per note, which is why the catalog stores a one-line `description` rather than a summary.

## Getting started

1. Clone or download this repository.
2. Install [LM Studio](https://lmstudio.ai) (or Ollama, or any local model runner) and download a model that runs entirely offline, Gemma is a reasonable default. Confirm it works with no network connection before trusting it with real data.
3. Either point your local agent framework's file access at this folder, so it can follow the read order in `AGENTS.md` directly, or, if you're using a plain chat UI with no file access, run `python3 _system/build_export.py` and paste the resulting `_export/PORTFOLIO.md` into the system prompt.
4. Replace the example notes in `Properties/`, `Tenants/`, and `Finance/` with your own portfolio. Delete the "example data" notices as you go.
5. Update the paragraph in `_index.md` and the notice at the top of `AGENTS.md` to describe your own setup, then remove both notices.
6. Run `python3 _system/lint.py` and fix what it flags.

Everything here runs on a stock Python 3 install, no `pip install` required, which matters if the vault ends up living on a NAS rather than a developer machine.

## Automation

**`lint.py`**: a health check that runs before every editing session or scheduled maintenance pass:
- Frontmatter completeness on every note
- Broken wikilinks (a `[[Note]]` reference to a title that doesn't exist)
- Folder-depth violations (anything nested more than one level deep)
- Overdue reviews, based on `review` cadence vs. `last_verified`
- Upcoming and passed `deadline` values
- Stale entries in the `NOW.md` rolling log
- Open, unconfirmed assumptions still tagged `#annahme`

**`build_export.py`**: regenerates the `_index.md` catalog between two HTML-comment markers, and rebuilds `_export/PORTFOLIO.md` (a short brief for a chat UI's system prompt) and `_export/PORTFOLIO-full.md` (every note, concatenated). Both exports include everything, with no tier or filter, because a local-only vault has nothing to redact.

Both scripts share a small helper module, `vaultlib.py`, that walks the vault and parses frontmatter with a single regex, no YAML library dependency.

## Maintenance workflow

| Cadence | Action |
|---|---|
| After every editing session | Update `NOW.md`, bump `modified` on touched notes, run the linter |
| When properties, tenants, or notes are added or renamed | Rebuild the catalog and exports |
| Monthly | Run the linter, prune `NOW.md` entries older than 30 days into their permanent notes, re-verify notes due for review, rebuild exports, check the deadline lookahead |
| Before pasting into a chat UI with no file access | Regenerate the export and hand over that fresh copy |

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Storage format | Markdown + YAML frontmatter | Universally parseable, diffable, human-readable |
| AI runtime | Local model runner (LM Studio, Ollama), a model like Gemma | Runs entirely offline, nothing to send anywhere |
| Editor | Obsidian, core plugins only | Wikilinks, backlinks, and graph view come for free; core content never depends on a community plugin |
| Linking | Title-based wikilinks (`[[Note Name]]`) | No path coupling; notes can be reorganized without breaking references |
| Scripting | Python 3, standard library only | No dependency management, runs anywhere including a NAS, easy to audit |
| Version control | Git, kept local or pushed only to a private remote | Audit trail for who changed which lease fact and when; never a public remote for a real portfolio |
| Sync | A NAS on your own LAN, or an encrypted sync tool | File-level sync between co-owners without a consumer cloud drive in the path |

## Why this is worth building

Managing rental property without a management company means being the accountant, the correspondent, and the record keeper at once, and AI tools are genuinely useful for that work. The obstacle has never been capability, it has been trust: handing bank details and tenant records to a cloud vendor is a real cost, not a hypothetical one. Building the entire system to run offline removes that cost by construction rather than by policy. The governance rules that remain, one fact in one place, every fact dated, a linter instead of good intentions, are the same discipline any shared record needs, local or not.

---

This document, and the example notes in this repository, contain no real personal, tenant, or financial data. Every value is fictional and clearly marked as such. Replace it with your own before operating a real portfolio from this vault.
