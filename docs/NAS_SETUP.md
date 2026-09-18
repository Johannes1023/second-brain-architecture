# NAS / OS setup for a real vault

Practical steps for hosting a real vault created by `init_vault.py` on a NAS or local machine. Nothing here is enforced by this repository's code; `init_vault.py` sets best-effort owner-only permissions on the files and folders it creates (see `SECURITY.md`'s enforcement table), but the durable setup is yours to apply and keep.

## Where to put it

- A NAS on your own LAN, or an encrypted local volume. Not a folder synced by a consumer cloud drive (Dropbox, OneDrive, Google Drive, iCloud Drive, Box); `init_vault.py` warns if the destination path looks like one of these, but the warning is a string match on the path, not a guarantee; renaming the folder defeats it, and a sync client configured on an innocuous-looking folder is invisible to this check entirely.
- Confirm no sync client is watching the parent folder, not just that the folder name doesn't mention a provider. Check the sync client's own configured folder list, not the vault's name.

## File permissions

- **Single-user machine or NAS account:** `init_vault.py` already sets owner-only read/write on everything it creates (`chmod 700` for directories, `600` for files, best-effort, some filesystems, notably network shares and exFAT, silently reject this, which is why it never raises on failure). Keep it that way: avoid `chmod -R 755` "to make it easier to browse" later.
- **Shared NAS with multiple accounts:** create a dedicated user or group for the vault, and set the share's ACL so only that user/group has access, at the share level, not just the file level. Most consumer NAS OSes (Synology DSM, QNAP QTS) expose this under the shared folder's permission settings, not the individual file's.
- **Multi-user desktop machine:** put the vault under your own home directory, not a shared `/Users/Shared` or `C:\Users\Public` location, and verify no other local account has read access to your home directory by default (this varies by OS default and is worth checking once, not assuming).

## Disk encryption

- Full-disk encryption on the machine or NAS the vault lives on (FileVault on macOS, BitLocker on Windows, LUKS on Linux, or your NAS vendor's volume encryption). This is what actually protects against device theft or loss; file permissions alone do not survive someone removing the physical disk.
- If the NAS supports per-share encryption in addition to full-volume encryption, use both; full-disk protects against the device leaving your control, per-share protects against another account or service on the same NAS.

## Network exposure

- Do not expose the vault's share over the internet (no port-forwarded SMB/NFS, no cloud-relay "access your NAS from anywhere" feature enabled for this specific share). If you need remote access, use a VPN into your own LAN, not a vendor's cloud-relay feature, since the latter routes at least metadata, and sometimes content, through the vendor's infrastructure.
- If the machine or NAS running your local model (see `docs/LOCAL_MODEL_CONFIG.md`) is different from the one holding the vault, the network path between them should be your own LAN or VPN only, never a path that transits the public internet unencrypted.

## Verifying the setup

There is no automated check for any of this from within the vault's own tooling (see `SECURITY.md`'s enforcement table for why). A reasonable manual check, repeated after any change to the NAS, the account, or the sync-client configuration on the machine:

1. From a different account on the same machine or NAS, confirm the vault folder is not readable.
2. Confirm the parent folder is not listed in any sync client's configured folders (check the client's settings, not the folder's contents).
3. Confirm the volume shows as encrypted in the OS's own disk-management tool.
4. Confirm the share, if any, is not reachable from outside your LAN (a quick check from a network outside your own, such as a phone on mobile data with Wi-Fi off, trying the NAS's external IP).
