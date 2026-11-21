# Linux and iPhone: manual SMB transfer

The desktop app currently offers read-only Linux Samba diagnostics. It cannot
create or manage an SMB share yet. This guide describes a manual setup for a
trusted local network; it is not a four-platform connectivity claim.

## On the Linux computer

Install Samba using your distribution's package manager. Create a dedicated
folder containing only files you intend to share. Configure a named SMB share
for that folder with guest access disabled and an authenticated local account.
Set the Samba password interactively on the computer. Check both Samba share
permissions and filesystem permissions. On SELinux systems, use a label scoped
to the dedicated folder; do not broadly enable sharing of the entire home
directory to solve a permission error.

Allow SMB on the intended local network profile only. TCP port 445 must not be
forwarded from your router to the internet. Public or isolated Wi-Fi networks
may block device-to-device traffic even when both devices are connected.

## On the iPhone

Open **Files → Browse → More → Connect to Server**. Enter the computer's local
hostname or current LAN address, such as `smb://computer.local`, choose
**Registered User**, and enter the Samba account. Select the dedicated named
share, not an automatically offered home directory.

To upload documents, open their location in Files, select one or more items,
and choose **Move** to the share. To preserve the source, use the available
copy/export action. Photos live in the Photos app; use **Select → Share →
Save to Files**, then choose the share or first save locally and move from Files.
An app's private data must be exported through that app's sharing interface.
The iPhone Files app does not expose every app's internal storage.

For the current app scope and remaining acceptance work, see the
[File Bridge plan](desktop-file-bridge-plan.md).

## References

- [Apple: connect iPhone to a file server](https://support.apple.com/guide/iphone/iphe9aff429a/ios)
- [Apple: organize files on iPhone](https://support.apple.com/guide/iphone/iphab82e0798/ios)
- [Samba usershare documentation](https://www.samba.org/samba/docs/current/man-html/net.8.html)
