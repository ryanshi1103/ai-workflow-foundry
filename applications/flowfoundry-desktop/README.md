# FlowFoundry Desktop

Computer-side control center for FlowFoundry's phone-and-computer connection. The target hosts are Windows and Linux; the target phones are iPhone and Android. File Bridge is its first module. Linux + iPhone is the first end-to-end acceptance pair.

## Current state

The React interface, Tauri command boundary, and a read-only environment command are present. On Linux, the native command checks whether Samba configuration parses, whether the SMB service is active, and whether the current user can list usershares. These checks do not change system state. Fedora native compilation and RPM packaging passed on one development host; the built app also remained open through a 10-second smoke run. Linux Samba and Windows SMB share management, account configuration, firewall changes, file operations, tray behavior, Android connection steps, and the Python Core bridge are **not implemented or verified**. The UI marks unavailable actions accordingly. Browser preview and RPM packaging are not device connection tests. See the [Linux + iPhone setup guide](../../docs/linux-iphone-setup.md) for a generic manual workflow.

## Local frontend check

```bash
npm ci
npm run build
npm run dev
```

Native development also needs Rust and the Tauri system prerequisites. Platform-specific bundle configuration targets Linux DEB/RPM and Windows NSIS EXE/MSI. A Fedora RPM was built locally but has not been installed or tested on another machine. Build and test each host separately.

## Boundary

- The webview cannot execute arbitrary shell commands or access arbitrary filesystem paths.
- SMB mutations will be owned by separate Linux Samba and Windows adapters and scoped to FlowFoundry-created shares.
- FlowFoundry Core integration will use a versioned protocol, rather than importing Python into the webview.
- iPhone uses Apple's built-in Files app and a registered Samba or Windows user, depending on the host; no iPhone companion app is required for the SMB flow.
- iPhone is first; Android is also in scope but its SMB client and connection steps need selection and device testing.

See [the implementation plan](../../docs/desktop-file-bridge-plan.md).
