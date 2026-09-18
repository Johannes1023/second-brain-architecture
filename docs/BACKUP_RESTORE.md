# Backup and restore

A local-only vault has no cloud copy by design (see `SECURITY.md`), which means it also has no vendor-managed backup. Losing the device or the NAS without a backup means losing the vault. This document is practical guidance, not enforced by any tool in this repository.

## What to back up

- The whole vault folder, as created by `init_vault.py`: every note, `_system/`, `_index.md`, `NOW.md`, the `.sensitive-vault` marker.
- `_export/` is generated (`build_export.py` rebuilds it from the notes) and does not need its own backup, though including it is harmless.
- If you keep scanned documents under `Documents/` (see `AGENTS.md`'s folder map and `lint.py`'s document-reference check), back those up too; they are usually the largest part of the vault by size and the least reproducible if lost.

## How, without reintroducing a cloud-sync risk

- An encrypted external drive, rotated off-site periodically (a second drive kept elsewhere, swapped on a schedule).
- A NAS's own built-in backup feature targeting a second, separate device, not a cloud target.
- If you do want an off-site, off-your-LAN backup, use a provider and workflow that encrypts before upload with a key only you hold (client-side encryption), not a consumer sync client pointed at the live vault folder. The distinction that matters is whether the vault's live folder is what's being watched and synced (the risk `SECURITY.md` and `init_vault.py`'s heuristic warn about) versus an already-encrypted backup archive being uploaded as an opaque blob after the fact.
- Whatever tool you use, verify it does not phone the file contents anywhere for "AI-powered search" or similar features some backup and sync tools now bundle by default; check its own settings, not just its marketing name.

## Restore

- Periodically (at minimum, once, right after you set the backup up) actually restore into a scratch location and run `python3 _system/lint.py --vault <restored-path>` against it. A backup nobody has ever restored is a hope, not a backup.
- After a real restore (not a drill), re-run the linter and check `NOW.md` and any `deadline`-bearing notes for anything that needed attention while the backup was your only copy.

## Versioned history as a complement to backups

If you keep a local (never public) git repository for your real vault (see `SECURITY.md`'s Git section), that gives you point-in-time history, which is a different thing from a backup: it protects against "I broke this note" and "what did this say last month," not against "the disk died." Keep both if you can; a git history that lives on the same disk as the vault it tracks does not survive that disk's failure.
