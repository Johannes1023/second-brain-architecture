# Agent permissions: two environments, never one

This project involves two distinct kinds of AI agent, and keeping them separate is as important as keeping the vault itself off the cloud. Confusing the two, even once, is how real data ends up somewhere it shouldn't.

## The two environments

| | Local knowledge agent | Coding / GitHub agent |
|---|---|---|
| What it is | LM Studio, Ollama, llama.cpp, or a local agent script reading the real vault | A cloud-based coding assistant (of exactly the kind writing this sentence) working on this public repository |
| Where it runs | Your own hardware, no cloud fallback (see `docs/LOCAL_MODEL_CONFIG.md`) | Anthropic's (or another vendor's) cloud infrastructure |
| What it may read | The real vault, wherever `init_vault.py` put it | This repository only: framework code, docs, schemas, fictional example notes, synthetic test fixtures |
| What it may never read | Nothing is off-limits to it within the vault it's pointed at; that's the point of keeping it local | The real vault, under any framing. Not "just to help debug," not "just the schema-relevant fields," not via a screenshot, a paste, or a summary |
| What it may write | The real vault, following `AGENTS.md`'s rules (one fact one place, dated, etc.) | This repository's own files: code, docs, tests, fictional examples |
| Governing rule | `AGENTS.md` rule 0 and the rest of that file | The scope given to it for this repository, and the boundary in this document |

## What a coding/GitHub agent working on this repository is authorized to do

- Improve the framework code (`_system/*.py`, `vaultlib.py`, `lint.py`, `build_export.py`, `init_vault.py`).
- Write and maintain documentation (this file, `SECURITY.md`, the rest of `docs/`, `README.md`, `AGENTS.md`).
- Create and maintain fictional example notes and synthetic test vaults (see `tests/vault_helpers.py`: every test vault is generated fresh, in a temp directory, never read from a committed fixture that could be mistaken for real data).
- Implement and run tests and, when one exists, CI, against fictional data only.
- Create secure configuration templates (schemas, `.sensitive-vault` marker format, example `--vault`/`SECOND_BRAIN_ROOT` usage) for a human to apply to their own real vault.

## What a coding/GitHub agent working on this repository must never do

- Request access to a real NAS-hosted vault, in any form, including "just to verify the tooling works against real data."
- Use real notes, or data resembling real notes, as test fixtures. Test data is always synthetic and generated at test-run time.
- Generate realistic-looking sensitive example data (a plausible IBAN, a real-looking tenant name paired with a real-looking address) even for illustration. Example data in this repository should read as obviously fictional.
- Upload, copy, or otherwise transmit the private vault, in whole or in part, anywhere, including into its own context window via a user-provided attachment, unless the human explicitly overrides this for a specific, narrow reason and understands what they're doing.
- Add cloud-model access as an option for the local knowledge agent's configuration (no "cloud fallback" toggle, no hosted-API code path, not even disabled by default).
- Enable telemetry of any kind on the vault-reading side of this project.
- Build automatic cloud fallback into any script in this repository.
- Send a full, unredacted export to an external target. (See `docs/EXTERNAL_SHARING.md` for what "external" and "redacted" mean here, and the current state of that boundary.)

## The `.sensitive-vault` marker

`init_vault.py` writes a `.sensitive-vault` file into every vault it creates. It exists so that tooling, and any agent reading a `--vault` path, has a machine-checkable signal that a given folder is a real, sensitive vault rather than this repository's own template or a scratch test fixture. `lint.py` checks for it and prints a **notice** (not a blocking issue) when it is missing from something that no longer looks like the unmodified template, a nudge, not an enforced gate, consistent with this phase's scoping decision to implement fail-closed enforcement later rather than half-build it now (see `SECURITY.md`'s enforcement table).

Practical implication for an agent: a `--vault` path whose folder contains a `.sensitive-vault` marker should be treated as carrying real, sensitive data, full stop, regardless of what else is or isn't in it yet.

## Write-access and confirmation

Within the real vault, an agent (human-directed local model or otherwise) making a destructive change (deleting a note, overwriting a fact that conflicts with what's already recorded, moving something to `Archive/`) should get explicit confirmation from the vault's owner first, the same standard `AGENTS.md` section 3 already sets for a human editor ("Delete notes only when the owner explicitly asks"). This document does not add new tooling to enforce that gate; it restates that the rule applies to an agent exactly as it applies to a person, and that "the agent decided this was probably fine" is not the same thing as the owner asking.
