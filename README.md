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
# A Second Brain for Real Estate Investing: A Tool-Agnostic AI Memory System for Property Management

**A portable, plain-text knowledge base that gives any AI tool, from Claude or ChatGPT to a local model running offline, persistent, structured and privacy-governed context about a rental property portfolio, without vendor lock-in and without a property management company.**

## TL;DR

- Plain Markdown files in a flat folder structure, versioned and synced like code, covering every property, tenant, lease, and deadline a small landlord manages.
- One universal "operating manual" (`AGENTS.md`) that any agentic AI tool reads first, by convention, so it behaves like a briefed property manager on the first message, not the hundredth.
- A generated index and two auto-built export files so even chat-only tools without file access can be given the same context.
- A data-governance layer baked into the format itself: every note is tagged with a sensitivity level, and a linter enforces what tenant and financial data may and may not be stored.
- Runs identically for a solo landlord, for co-owners sharing one property, and for fully local AI setups where no data ever leaves the house.
- Two dependency-free Python scripts plus a shared helper module, roughly 180 lines of standard-library Python in total, handle indexing, export generation, and health checks. No editor community plugins are required for the system to function.

## The problem this solves

Running a small rental portfolio without a management company means holding a lot of state in your head or scattered across email threads, PDFs, and spreadsheets: which lease is eligible for its next index-linked rent adjustment, when the operating-cost statement (*Betriebskostenabrechnung*) for a given unit is due, what a contractor quoted for a repair eight months ago, what the handover protocol recorded at move-in. AI assistants are a natural fit for this kind of work, drafting a rent-adjustment letter, checking a cost statement against the lease's allocation keys, summarizing a maintenance history, but only if they have the underlying facts. Every vendor's chat memory is a walled garden, resets when you switch tools, and drifts into two incompatible versions of the truth the moment you use more than one assistant.

A second brain inverts that relationship: the AI tools become clients of *your* property data, not the other way round. The source of truth is a folder of Markdown files you own, can read with any text editor, can diff in git, can sync to a home server, and can hand to literally any LLM, cloud or local. Any AI tool's own memory feature, if used at all, gets *filled from* this vault, never the reverse.

It also solves the co-ownership problem directly: when a property is owned jointly, the vault is the one place where object data, tenant history, and open items live, so both owners and any AI tool either of them uses are working from the same current facts instead of two private note piles.

## Design principles

| Principle | What it means in practice |
|---|---|
| **Tool-agnostic by construction** | Core content never depends on a plugin (no Dataview, no Templater syntax in the actual notes). Plain Markdown + YAML frontmatter + wikilinks reads correctly in Obsidian, VS Code, GitHub, or a raw file dump into a chat window. |
| **Single source of truth** | AI tools' own memory features are a cache, not a store. If a chat tool learns something new about a lease or a repair, that fact gets written back into the vault, not left stranded in the tool. |
| **One fact, one place** | A given lease term, rent figure, or deadline lives in exactly one note. Other notes reference it via a link instead of repeating it, so updates never fall out of sync between, say, a property note and a finance note. The generated files under `_export/` are the one deliberate exception: they are build artifacts, never hand-edited, and always reproducible from the notes. |
| **Flat structure** | Maximum one folder level. When a category grows too large, it splits into more clearly named files (`Unit - Ground Floor.md`, `Unit - 3rd Floor.md`), never into subfolders. This keeps the mental map small enough to hold in your head, keeps it usable by a co-owner who didn't build it, and keeps every AI tool's file-listing calls cheap. |
| **Every fact is dated** | Time-sensitive statements carry an explicit "as of" stamp. A rent amount, a vacancy status, or a valuation from eight months ago is marked as such, so an AI reading it doesn't treat it as current truth by default. |
| **Sensitivity is a first-class field** | Every note declares how exposed it may be (see below), enforced at read time by convention and at write time by the linter. This matters more, not less, once tenant and co-owner data is involved. |
| **Assumptions are tagged, not silently resolved** | When two sources disagree, for example a lease PDF and an email, and it isn't clear which is current, the system writes the likely value but flags it inline as an assumption, rather than quietly picking one. |

## Architecture

### Folder map

```
vault/
├── AGENTS.md       # Operating manual for any AI tool (read first)
├── CLAUDE.md       # One-line pointer to AGENTS.md (tool-specific convention)
├── NOW.md          # Rolling log: open deadlines, recent changes, current focus
├── _index.md       # Generated map of every note with a one-line description
├── _system/        # Rules for AI, note templates, maintenance scripts
├── _export/        # Generated single-file exports for tools without file access
├── Properties/     # One note per property or unit: object data, valuation, depreciation
├── Tenants/        # One note per tenant: lease terms, handover, correspondence history
├── Finance/        # Rent roll, deposits, operating-cost statements, tax-relevant figures
├── Maintenance/    # Repairs, contractor history, warranties, recurring service contracts
├── Legal/          # Lease-law references, index-rent mechanics, regulatory notes
├── Co-Owners/      # Ownership shares, decision log, cost-split agreements
└── Archive/        # Superseded leases and closed cases, created on demand
```

One folder level, period. No `Properties/BuildingA/Unit3/2026/`. This is a deliberate constraint: it forces every note to earn a clear, unique title instead of hiding behind path context, which is exactly what makes wikilink-by-title (`[[Note Name]]`, no paths) work reliably as the portfolio grows to more units.

### Frontmatter schema

Every note carries required YAML frontmatter. This is what turns a folder of Markdown files into a queryable dataset without a database:

```yaml
---
description: One line. What the note covers and when to read it.
created: YYYY-MM-DD
modified: YYYY-MM-DD
last_verified: YYYY-MM-DD
review: monthly | quarterly | yearly
status: draft | active | evergreen | archived
area: Properties | Tenants | Finance | Maintenance | Legal | Co-Owners | System
sensitivity: shared | owner-only | restricted
aliases: []
tags: []
---
```

- **`sensitivity`** is the field the export step reads, and it is enforced mechanically rather than by discipline: the generator takes a target tier and writes only notes at or below it. `shared` notes go into every export; `owner-only` notes are included in an owner's own export but omitted from the one handed to a co-owner or an external advisor; `restricted` notes are excluded from every export and from the generated catalog, so they exist in the vault but never reach a tool by default. The tier a note carries therefore determines its blast radius by construction, not by remembering to redact.
- **`review`** feeds directly into the linter: a lease note tagged `review: quarterly` that hasn't been `last_verified` in 92 days gets flagged as stale. That catches silent drift, for example a rent figure that no longer matches the current lease.
- **`deadline`** (optional, `YYYY-MM-DD`) is what actually drives date-bound work: notice periods, operating-cost statement due dates, the earliest permissible date for the next index-rent adjustment. The linter reports any note whose `deadline` falls inside a configurable lookahead window, which is a different check from `review` and should not be conflated with it.
- Category-specific notes extend the schema further (a lease note adds `lease_start` / `lease_end`, a maintenance note adds `contractor` and `warranty_until`), so the schema grows with the portfolio instead of requiring a rewrite.

### The read order

The single most important design decision is that no AI tool ever scans the whole vault. `AGENTS.md` defines a strict, short read order:

```mermaid
flowchart TD
    A[AI tool opens the vault] --> B["_system/Communication Preferences.md<br/>(binding response rules)"]
    B --> C["NOW.md<br/>(open deadlines, current focus)"]
    C --> D["_index.md<br/>(map of every note)"]
    D --> E{Task needs more detail?}
    E -->|Yes| F[Open the specific property/tenant/finance<br/>note(s) named in the index]
    E -->|No| G[Answer]
    F --> G
```

This bounds a typical interaction to four file reads plus the specific notes a task actually needs, instead of a scan that grows with the portfolio. The number of reads is constant; only the index itself grows, and it grows by one line per note, which is precisely why the catalog stores a one-line `description` rather than a summary. Same reasoning as an index or manifest in a large codebase: give the agent a cheap map first, let it open only what the task requires.

## Automation

Two dependency-free Python scripts, using only the standard library, keep the vault self-consistent:

**`lint.py`**: a health check that runs before every commit or scheduled maintenance pass:
- Frontmatter completeness (all required fields present on every property, tenant, and finance note)
- Broken wikilinks (a `[[Note]]` reference to a title that doesn't exist, for example a tenant note pointing at a property that was renamed)
- Folder-depth violations (anything nested more than one level deep)
- Regex-based sensitive-data detection (tax IDs, IBANs, ID numbers, phone numbers, secrets) scanned against a configurable pattern list, critical here because tenant records are exactly the kind of data that must not leak into an export
- Overdue reviews, based on `review` cadence vs. `last_verified`: a staleness check, not a calendar
- Upcoming `deadline` values inside the lookahead window: the actual date-bound check, kept separate from staleness
- Stale entries in the `NOW.md` rolling log
- Open, unconfirmed assumptions still tagged in the text

**`build_export.py`**: regenerates three artifacts from the same source notes:
1. **`_index.md` catalog**: rebuilds the "map of every note" section between two HTML-comment markers, grouped by area, from each note's frontmatter `description`. Everything outside the markers is hand-written and preserved, so the file is both a human document and a generated index.
2. **`_export/PORTFOLIO.md`**: a short brief (portfolio overview, binding communication rules, current open items, catalog) sized to fit a chat tool's custom-instructions or project-knowledge field.
3. **`_export/PORTFOLIO-full.md`**: every note at or below the requested sensitivity tier, concatenated into one file with a source-path and `last_verified` comment above each section. For tools with no persistent file access: paste it in once and the tool has the same context a file-access-capable tool would assemble over several reads.

Both scripts share a small helper module (about 30 lines) that walks the vault, skips generated and system directories, and parses frontmatter with a single regex, no YAML library dependency. The entire system runs on a stock Python 3 install, which matters when the host is a NAS rather than a developer machine.

## The AI-integration layer

This is the part that makes it genuinely tool-agnostic rather than "Obsidian plus one plugin for one AI vendor":

| Tool category | How it gets context |
|---|---|
| Agentic coding tools with file access (Claude Code, Cursor, Codex, etc.) | Read `AGENTS.md` (the emerging cross-tool convention) or `CLAUDE.md`, which simply points to it, and follow the read order live against the real files. |
| Chat tools without file access | Get `_export/PORTFOLIO.md` or `_export/PORTFOLIO-full.md` pasted in or uploaded as project knowledge. Regenerated on demand, current as of the last `build_export.py` run, which is the one caveat worth stating: an export is a snapshot, so it is rebuilt before it is handed over, not reused from last month. |
| Local, fully offline AI (e.g. LM Studio or another local model runner) | Point a local model at the vault directory or at a generated export. Because the vault is nothing but Markdown files with no API dependency, a local model gets the same structured context a cloud model would, under the same read-order convention, while tenant and financial data never leaves the machine. This is what makes the `restricted` tier practical rather than theoretical: those notes can be worked on exclusively by local models and excluded from every export a cloud tool would ever see. |
| Tools with live, incremental access | An MCP (Model Context Protocol) server can expose the vault to tools that support it over a local transport (stdio for a locally launched server, or HTTP/WebSocket on a loopback port), without changing anything about the underlying files. |
| Any future tool | Since the format is plain Markdown with YAML frontmatter and no proprietary syntax in the content itself, a new tool needs zero migration work, only a reader for the convention. |

The vault's own content is explicitly the source of truth. If a chat tool's built-in memory feature picks up a new fact mid-conversation, for example a new rent figure or a repair status, the workflow is to write that fact back into the relevant note (tagged as an assumption if unconfirmed), not to let it live only inside that vendor's memory store.

## Data governance

Every note's `sensitivity` field is backed by an explicit, enforced policy rather than a vague sense of "don't overshare," which matters especially once tenant personal data is part of the vault:

- **Never stored, anywhere in the vault:** tenant government ID or tax identifiers, bank account or card numbers, passwords and API keys, phone numbers, booking references, internal network details, and any detail about a tenant or contractor that goes beyond what the property relationship requires.
- **Allowed, at a controlled resolution:** property addresses and object data, tenant name and lease terms, rent and operating-cost figures with a timestamp, valuation and depreciation figures, maintenance and contractor history at a factual level.
- **`restricted` notes** are excluded from the generated index and from every export; they exist in the vault but are invisible to the default read path and to anything leaving the machine, which is the right place for a dispute or negotiation file that should not reach every AI tool or every co-owner's export.

The linter's regex bank catches common leakage patterns (structured ID formats, IBAN-shaped strings, secret-looking key=value pairs) automatically, so a policy violation fails a check rather than depending on someone remembering the rule at edit time.

Two limits are worth stating plainly rather than overselling the design. First, a regex bank catches formatted identifiers, not free-text disclosure: it will flag an IBAN and miss a paragraph that narrates a tenant's personal circumstances, so the field-level policy above, not the linter, is the actual control. Second, a private landlord processing tenant data is a controller under the GDPR, and the household exemption does not cover letting property as an economic activity. The practical consequence is that the allow-list above is not a stylistic preference but an application of data minimisation (Art. 5(1)(c) GDPR): store the categories the tenancy actually requires, at the coarsest resolution that still answers the question, and keep the retention boundary visible by archiving closed tenancies instead of letting them accumulate in the active set.

## A shared, multi-owner knowledge base

The structure was built for a portfolio owned and managed by more than one person. Hosted on a home server or NAS instead of a single laptop, with the vault synced to both co-owners, it functions as a lightweight, AI-readable virtual property manager: object data, tenants, lease terms, deadlines, and correspondence history live in the same flat, dated, frontmatter-tagged note structure described above. Any AI tool either owner uses, cloud or local, can be pointed at the shared vault to answer a lease question, draft tenant correspondence, check an operating-cost statement (*Betriebskostenabrechnung*) against the lease's allocation keys, or surface the next date-bound item, without either person having to re-explain the situation from scratch. The same governance rules apply and matter more here than anywhere else: every fact stays in one place, every fact is dated, and the `sensitivity` field controls what a given tool, export, or co-owner's context is allowed to see.

## Maintenance workflow

| Cadence | Action |
|---|---|
| After every editing session | Update `NOW.md`, bump `modified` on touched notes, run the linter |
| When properties, tenants, or notes are added or renamed | Rebuild the catalog and exports |
| Monthly | Run the linter, prune `NOW.md` entries older than 30 days into their permanent notes, re-verify notes due for monthly review, rebuild exports, review the `deadline` lookahead |
| Before using a chat-only tool | Regenerate the export at the appropriate sensitivity tier and hand over that fresh copy |

`NOW.md` is intentionally the only note that behaves like a log rather than a reference: short, dated, rolling entries under Active / Recent developments / Upcoming / Open questions, tuned in this context to open items like a pending handover, an unpaid operating-cost balance, or a notice period now running. Anything older than 30 days has to either graduate into a permanent note or be dropped, which keeps "what needs attention right now" cheap to read without letting it become a second, competing source of truth against the property and tenant notes themselves. The rule is enforced by the linter rather than by intent, which is the only reason it survives contact with a busy month.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Storage format | Markdown + YAML frontmatter | Universally parseable, diffable, human-readable, zero vendor lock-in |
| Editor | Obsidian, core plugins only | Wikilinks, backlinks, graph view, and daily notes come for free; explicitly avoids depending on community plugins for core content |
| Linking | Title-based wikilinks (`[[Note Name]]`) | No path coupling; notes can be reorganized without breaking references as the portfolio grows |
| Scripting | Python 3, standard library only | No dependency management, runs anywhere including a NAS, easy to audit |
| Version control | Git | Gives an audit trail of who changed which lease fact and when, makes the linter a pre-commit check, and turns co-owner edits into a merge instead of a conflict between two file copies |
| Sync | File-level sync (a NAS share, an editor's own sync, or the git remote itself) | Vault is just files; any mechanism that preserves a folder of `.md` files works, including sharing across co-owners |
| AI integration | `AGENTS.md` / `CLAUDE.md` convention + generated exports + optional MCP + local-model support | Meets each tool where it already looks for context, cloud or fully local, no custom integration per tool |

## Why this is worth building

Managing rental property without a management company means being the accountant, the correspondent, and the record keeper all at once, and doing it well depends entirely on not losing track of facts across leases, repairs, and years. A second brain built this way turns "the AI doesn't know my portfolio" from a permanent limitation into a one-time engineering problem, and turns "my co-owner and I have two different pictures of where things stand" into a non-issue by construction. The payoff compounds: every hour spent structuring a fact once means it never has to be re-explained to the next tool, the next model version, or the next lease renewal. And because the governance rules live in the format itself rather than in a vendor's settings page, the privacy guarantees around tenant data survive a tool migration, a switch to a local model, or a new co-owner joining, instead of resetting to whatever that vendor's defaults happen to be.

---

*This document describes the system design and conventions only. It intentionally contains no personal data, tenant information, property details, or real file names from the underlying vault, so it can be reused as a template for building an equivalent system from scratch.*
