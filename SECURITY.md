# Security model

This file says precisely what protects the data in a real vault built from this template, what does not, and where the line sits between what this repository can enforce in code and what only your own hardware and habits can enforce. If you read one file before putting real data anywhere near this template, read this one.

## The core design: two separate things, physically apart

This repository is a **framework**: code, docs, a JSON Schema, fictional example notes, and tests built from synthetic data generated at test time. Nothing in it is real.

A **real vault** (your actual properties, tenants, bank details, correspondence) is a different thing, created by `_system/init_vault.py` **outside this repository**, typically on a NAS or an encrypted local volume you control. The two are connected only by the tooling (`vaultlib.py`, `lint.py`, `build_export.py`), which accepts any vault path via `--vault` or `SECOND_BRAIN_ROOT`. They are never the same folder, and this repository's own git history should never contain a single real fact.

This split exists because a rule written in a Markdown file (`AGENTS.md` rule 0: "never point a cloud tool at this vault") is a request to whichever model reads it, not a technical control. A local model that respects the rule protects you. A cloud tool pointed at the same folder, a misconfigured sync client, or a public git remote does not care what `AGENTS.md` says. Physical separation of the real vault from this public repository is what keeps a mistake in the framework code from ever being a mistake with real data.

## What is actually enforced today, and by what

| Claim | Enforced by | How |
|---|---|---|
| This repo contains no real data | Human discipline + code review | Every example note is fictional; tests generate synthetic vaults in a temp directory, never read the example notes (see `tests/vault_helpers.py`) |
| Tooling defaults to a script-relative path, never a hardcoded absolute path to "the" vault | `vaultlib.resolve_root()` | CLI `--vault` > `SECOND_BRAIN_ROOT` env var > the folder this script ships in. An explicit value that does not resolve to a real directory raises, it never silently falls back |
| A new vault starts without example data or stale dates | `init_vault.py` | Copies only rules and scripts, never the example notes; re-stamps `created`/`modified`/`last_verified` to today |
| A new vault is never created inside this repository | `init_vault.py` | Refuses (`SystemExit`) if the destination resolves inside `REPO_ROOT` |
| A new vault is never created on top of existing files | `init_vault.py` | Refuses if the destination exists and is non-empty |
| A vault folder that looks like it sits in a cloud-sync folder is flagged | `init_vault.py` | String match against known provider folder names (Dropbox, OneDrive, Google Drive, iCloud Drive, Box Sync) in the destination path. This is a **warning, not a block**: it is a heuristic on a path string, easy to defeat with a renamed folder, and does not detect sync configured at the OS level on a folder with an innocuous name |
| A vault is marked as sensitive so tooling can tell a real vault from a template | `.sensitive-vault` marker + `lint.py`'s vault-marker notice | `init_vault.py` writes the marker automatically. If it is missing and the vault no longer looks like the unmodified template, `lint.py` prints a **notice** (not a failing issue) suggesting one be added |
| Exports never leave the vault they were built from | `build_export.py` | Only ever writes into `<vault>/_export/`, resolved from the same `--vault`/`SECOND_BRAIN_ROOT` value used to read the vault |
| A vault's own git history cannot leak by accident | Not enforced by this repo | See "Git" below |

## What "local-only" removes, and what it does not

"Local" removes exactly one risk: a cloud vendor, or anyone on the network path to one, ever receiving your data. It removes that risk completely, by never making the request in the first place, provided you actually follow rule 0 in `AGENTS.md`. It does **not** protect against any of these, which is why the table above is short:

| Risk | What actually protects against it |
|---|---|
| Device theft or loss | Full-disk encryption on the machine and the NAS |
| A backup exposing the data | No cloud-sync client pointed at the vault folder; encrypted backups |
| A shared machine or NAS's other users reading the vault | OS-level file permissions / ACLs, see `docs/NAS_SETUP.md` |
| A real vault's git history reaching a public remote | Never adding a public remote; see "Git", below |
| A local model quietly using a cloud API as a fallback | Configuring the model runner for loopback-only network access, see `docs/LOCAL_MODEL_CONFIG.md` |
| A coding agent (this repository's own kind of AI helper) reading real vault contents | Environment separation, see `docs/AGENT_PERMISSIONS.md` |
| A copy of the vault, or an export, ending up somewhere it should not | Treating every export deliberately, see `docs/EXTERNAL_SHARING.md` |

None of this is exotic. It is the same baseline you would want for any folder full of bank statements, whether or not an AI ever reads it.

## Git

`init_vault.py` deliberately does **not** run `git init` on a new vault. If you want version history for your real vault:

- Initialize git yourself, on the NAS or machine that holds the vault, not from this repository.
- Never add a public remote (GitHub, GitLab, etc.) to a real vault's repository. If you want off-machine history, push only to a private remote you control, or skip git and rely on your backup strategy instead.
- Double-check `git remote -v` after any `git clone`-based setup step, since a clone can carry a remote over without you typing it.

This repository's own git history is public by design (it is the framework), which is exactly why a real vault must never be a subfolder or a fork of it with real data added in place. Use `init_vault.py`'s external destination for that reason.

## Threat model, and what is explicitly out of scope for this session's implementation

The full breakdown of assets, actors, and mitigations lives in `docs/THREAT_MODEL.md`. In short: this repository ships the parts of the design a coding agent working in a cloud sandbox can actually build and test: path handling, a bootstrap tool, a hardened linter, schemas, docs, fictional-data tests. It does not and cannot ship:

- Your NAS's or OS's actual access-control configuration (`docs/NAS_SETUP.md` documents how, but has to be applied by you, on your hardware).
- Network-level enforcement that a model runner never calls out to a cloud endpoint (`docs/LOCAL_MODEL_CONFIG.md` documents how to configure this in LM Studio/Ollama; this repository cannot reach into your model runner's process to enforce it).
- A finished "Approved-Outbox" redacted-export tier. `build_export.py` today produces two local, unredacted exports (`PORTFOLIO.md`, `PORTFOLIO-full.md`), both meant to stay on the same machine. A reviewed, redacted external-sharing tier is designed in `docs/EXTERNAL_SHARING.md` but not yet built; treat any export from this vault as fully sensitive until that changes.
- CI enforcement of the fictional-data-only rule (there is no CI pipeline in this repository yet; the rule is currently upheld by test design and code review only).

## Prompt-injection awareness

A local AI reading this vault still reads untrusted text if any note ever contains content pasted from an email, a PDF-derived OCR dump, or similar. Treat a note's *body* as data, and `AGENTS.md`'s rules as the only source of instructions, the same boundary this repository's own tooling observes with your requests. If you paste correspondence into a note verbatim, be aware that a sufficiently capable model reading it could, in principle, be steered by text embedded in that correspondence claiming to be an instruction. The mitigation is procedural, not technical: know what you paste in, and remember that only you and `AGENTS.md`'s own rules can authorize an action, never a vault note's body text.

## See also

- `docs/THREAT_MODEL.md`: assets, actors, mitigations, explicitly out of scope
- `docs/NAS_SETUP.md`: OS/NAS permissions for a real vault
- `docs/LOCAL_MODEL_CONFIG.md`: configuring LM Studio/Ollama for loopback-only, no cloud fallback
- `docs/AGENT_PERMISSIONS.md`: the two-environment isolation model, and what a coding agent in this repository is and is not allowed to do
- `docs/BACKUP_RESTORE.md`: backing up a real vault without a cloud-sync tool
- `docs/EXTERNAL_SHARING.md`: the export tiers, current and planned
