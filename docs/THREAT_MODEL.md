# Threat model

Assets, actors, and mitigations for a real vault built from this template. See `SECURITY.md` for the overall model this fits into.

## Assets

| Asset | Where it lives | Why it matters |
|---|---|---|
| Tenant identity and contact data | `Tenants/` | Personal data, contractual obligation to protect it |
| Bank details (rent, deposits, loans) | `Finance/`, `Tenants/` | Direct financial exposure if leaked |
| Owner identity and ownership shares | `Co-Owners/` | Personal data, financial exposure |
| Correspondence history | `Tenants/`, `Property Management/` | Can reveal disputes, notice periods, negotiating position |
| Tax figures | `Taxes/` | Financial exposure, regulatory sensitivity |
| The vault's git history (if any) | Wherever you `git init` a real vault | Old, deleted, or superseded versions of all of the above |
| Exports (`_export/PORTFOLIO.md`, `_export/PORTFOLIO-full.md`) | `<vault>/_export/` | Full, unredacted copies of everything above, in one file each |

## Actors and scenarios

| Actor / scenario | What could go wrong | Mitigation | Status |
|---|---|---|---|
| A cloud AI tool (ChatGPT, Claude.ai, a hosted API) pointed at the vault | Full vault contents sent to a third party | `AGENTS.md` rule 0  (procedural); loopback-only model runner config (`docs/LOCAL_MODEL_CONFIG.md`, procedural: this repo cannot enforce a model runner's own network calls) | Documented, not technically enforced |
| A device with the vault on it is lost or stolen | An attacker with physical access reads everything | Full-disk encryption on the device and the NAS | Documented (`docs/NAS_SETUP.md`), applied by you |
| The vault folder is inside (or gets moved into) a cloud-sync folder | Every version syncs to a consumer cloud drive | `init_vault.py`'s cloud-sync path heuristic (warns, does not block) | Partially enforced (heuristic only) |
| A real valt gets a public git remote, accidentally or by cloning a setup script that adds one | Full history, including deleted/old data, becomes public | Never automated (`init_vault.py` never runs `git init`); documented in `SECURITY.md`'s Git section | Documented, not technically enforced |
| Another user on a shared machine or NAS reads the vault | Confidentiality breach without any AI involved at all | OS/NAS file permissions (`docs/NAS_SETUP.md`) | Documented, applied by you |
| A coding/GitHub agent (working on this repository) is asked to read or use real vault data | Real data enters a cloud AI session, or ends up committed to this public repo | Environment separation (`docs/AGENT_PERMISSIONS.md`); this repository's own scope rules (see its `AGENTS.md` and the project's own instructions to any coding agent working on it) | Enforced by this session's own scoping decisions; not machine-enforced against a differently-instructed agent |
| An export (`_export/*.md`) is copied somewhere other than the machine it was built on | Full, unredacted data leaves the local-only boundary | Treat exports as fully sensitive; `docs/EXTERNAL_SHARING.md`'s planned redacted tier is not built yet | Not yet mitigated, exports are unredacted today |
| A vault note's body contains pasted correspondence with embedded instruction-like text | A model reading the note is steered by content that isn't actually from the owner | Procedural: treat note bodies as data, `AGENTS.md`'s own rules as the only instruction source | Documented, not technically enforced (no prompt-injection filtering exists in this tooling) |
| A backup of the vault is itself unencrypted, or synced to a cloud backup service | Same exposure as a cloud-sync folder, one step removed | `docs/BACKUP_RESTORE.md` | Documented, applied by you |
| A malformed or corrupted note crashes the linter mid-run, masking other issues | Real problems go unnoticed because the tool never finished | `lint.py`'s per-file try/except: a broken note is reported as an issue, never a crash | Enforced (test: `test_malformed_file_never_raises`, `test_run_continues_past_unreadable_note`) |

## Explicitly out of scope for this repository's own tooling

This repository ships code, docs, schemas, and tests. It does not and cannot ship, or enforce at runtime:

- Your NAS's or OS's actual ACL/permission configuration.
- Network-level blocking of a model runner's outbound calls.
- Encryption of the disk or backup volume the vault lives on.
- Detection of a git remote added to a *real* vault's own separate git repository (this repository has no visibility into a vault that lives outside it).
- A CI pipeline (none exists yet; the fictional-data-only rule is upheld by test design and review, not by an automated gate).
- Redaction of exports before they leave the local machine (the redacted "external-redacted" export tier described in `docs/EXTERNAL_SHARING.md` is a design, not yet implemented).

Where a mitigation's status above says "documented, not technically enforced," that is the honest state: a Markdown file can describe the right setup, it cannot apply it to your NAS or your model runner's network config for you.
