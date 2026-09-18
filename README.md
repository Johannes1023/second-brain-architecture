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
# second-brain-architecture
Tool-agnostic AI knowledge base for property management: plain Markdown, enforced schema, sensitivity tiers, dependency-free Python tooling.
