# FlowFoundry Desktop / File Bridge implementation plan

Status: four-platform scope confirmed; native Windows and Linux sharing, and iPhone and Android connections remain unverified.

## Product boundary

The two device sides are **computer and phone**. The target computer systems are **Windows and Linux**; the target phone systems are **iPhone and Android**. File Bridge uses one product, authorization, and evidence contract across them, with separate host adapters and phone connection guides. The first end-to-end acceptance pair is **Linux + iPhone**. Windows and Android remain in scope and need their own checks. The iPhone path uses the built-in Files app as a registered SMB user; a phone companion app is not required for that path. The Android SMB client and its exact steps are still to be selected and verified.

The existing scaffold uses a Tauri 2 shell with React and TypeScript and a narrow Rust command API. The computer host adapter will use Samba on Linux and the native SMB server on Windows. Neither host adapter is implemented yet. The Python FlowFoundry Core remains the source of truth for workspace, route and Worker selection, approvals, evidence, and recovery. Desktop owns user interaction and OS-specific work. The active goal path is `GoalRunner` with `ExecutionRoute` selection; the older `AgentRegistry` / `ApprovalGate` classes are not assumed to be active without a call-path check.

## GitHub reuse decision

| Source | Reuse | Reason |
| --- | --- | --- |
| [tauri-apps/create-tauri-app](https://github.com/tauri-apps/create-tauri-app) | Template structure and official commands | Maintained Apache-2.0 scaffold; this app is isolated under `applications/`. |
| [tauri-apps/plugins-workspace](https://github.com/tauri-apps/plugins-workspace) | Tray, autostart, dialog after capability review | Official Tauri 2 plugins; add only needed permissions. |
| [LocalSend](https://github.com/localsend/localsend) | UX and release-process reference | Its transfer protocol differs from SMB. No code copied. |
| [Dantdmnl/Share_Manager](https://github.com/Dantdmnl/Share_Manager) | Connection and diagnostics UX reference | Its PowerShell script maps *client* network shares; this product must host a share. No code copied. |
| Samba `net usershare` / `smb.conf` | Linux host integration | Inspect local Samba configuration and permissions before using usershares; never assume usershares are enabled. |
| Windows `SmbShare` and `NetSecurity` modules | Windows host integration | Use supported native management APIs, with explicit account, ACL, and firewall checks. |

Dependency licenses and version locks must be recorded before shipping binaries. A repository being public is not permission to import its code without license review.

## Modules and contracts

```text
React UI
  -> typed Tauri commands
    -> read-only diagnostics
    -> Linux Samba or Windows SMB host adapter (application-owned shares only)
    -> File Bridge policy and file operations
    -> versioned FlowFoundry Core adapter
```

The Linux adapter must inspect Samba availability, usershare policy, account access, canonical paths, filesystem permissions, and firewall exposure before proposing a change. The Windows adapter must validate share name, canonical path, account SID, local network profile, and existing firewall rules. Privileged operations on either host require precise user confirmation and a scoped elevated helper; the normal UI process stays unprivileged. Effective access depends on both SMB share policy and host filesystem permissions. Disabling a share removes only that named, application-owned share after checking active sessions; it never stops the system-wide SMB service.

File Bridge Agent tools accept registered root IDs and relative paths, never an arbitrary absolute path. They provide list, read, write, move, copy, and delete. Read-only access is the default. Delete, overwrite, and external-share writes require approval under the existing permission ceiling. Resolve and open paths safely against reparse points and symlinks; validate the actual opened object to avoid race-based escape. Deletes enter an application-managed 14-day recycle area where the workflow permits recovery, with an auditable retention job. This must not claim to control files independently deleted through SMB by an iPhone.

The Core bridge needs a versioned request/result envelope: request ID, principal, authorized root ID, action, approval reference, evidence path, and a redacted error type. It must reject schema versions or permissions it does not recognize. Recovery replays only safe idempotent operations; file mutations need operation IDs and a verified outcome before retry.

## Milestones and evidence

1. Shared desktop shell and contract: native window, typed command bridge, explicit unavailable states, visual layout. Frontend build must pass; native builds remain separate gates.
2. Linux read-only adapter: Samba availability, share state, account and filesystem permissions, network address, and firewall diagnostics. Configuration parsing, service state, and current-user usershare access are now wired to the native snapshot. A Fedora native build passed; network, firewall, and share diagnostics remain incomplete.
3. Linux + iPhone first connection: scoped, application-owned Samba share; copyable SMB address; iPhone Files registered-user guide. Verify create, connect, read/write as authorized, disconnect, and disable on real devices in a trusted LAN.
4. Windows adapter: native SMB diagnostics and scoped share lifecycle, with ACL, firewall, UAC, and rollback checks. Verify Windows + iPhone on real devices.
5. Android connection: select and document a compatible SMB client, then verify it against both Linux and Windows hosts. Client selection and device tests are pending.
6. Core integration: authorization roots, Agent tool routing, approval gates, evidence and recovery. Add root-escape, overwrite, deletion, and replay tests.
7. Distribution: build and test native Linux packages and Windows NSIS EXE/MSI separately, including install, upgrade, and uninstall. A build artifact alone does not prove device connectivity.

## Release risks

- TCP 445 is system-wide. A per-share firewall rule cannot isolate one SMB share from another. Existing broad allow rules and router exposure must be inspected before describing a host as LAN-only.
- Multi-NIC, VPN, public network profiles, IPv6, and changing addresses can make a displayed URL wrong. Show the selected interface and provide diagnostics.
- SMB sessions and open-file views are not complete historical transfer logs. Windows audit events are optional and system-wide; distinguish them from application operation records.
- Linux distributions differ in Samba, firewall, and packaging defaults; validate the supported distributions on real machines.
- Windows Home/Pro policies and account setup can differ. Validate supported editions and the Windows build matrix on real machines.
- Tauri native builds require Rust and platform prerequisites. A Fedora RPM build passed on one host; installation, other platforms, and phone connectivity through the app remain unverified.

## Sources

- [Tauri 2 Windows prerequisites](https://v2.tauri.app/start/prerequisites/)
- [Tauri 2 Windows installers](https://v2.tauri.app/distribute/windows-installer/)
- [Tauri command model](https://v2.tauri.app/develop/calling-rust/)
- [Windows New-SmbShare](https://learn.microsoft.com/en-us/powershell/module/smbshare/new-smbshare)
- [Windows Remove-SmbShare](https://learn.microsoft.com/en-us/powershell/module/smbshare/remove-smbshare)
- [Windows firewall rule API](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule)
- [Apple Files server connection](https://support.apple.com/en-au/guide/iphone/iphe9aff429a/27/ios/27)
- [Samba usershare configuration](https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html)
