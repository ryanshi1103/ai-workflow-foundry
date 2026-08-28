# Launcher EOF Compatibility

The line-oriented launcher remains the compatibility path for pipes, scripts,
non-interactive terminals, and the `_CC_PLAIN` override. Interactive terminals
may use the adaptive TUI.

## Release fix

The `cc` wrapper previously tested module availability by importing
`flowfoundry.cc`. That module is an executable entry point, so the probe itself
started the launcher and consumed stdin before the intended invocation. Piped
input consequently reached a second launcher at EOF.

The wrapper now uses a side-effect-free module-spec lookup and executes the
entry point exactly once. No provider or permission mode was removed.

## Preserved compatibility

`core/workspace-manager/tests/test-cc-eof-fix.sh` covers:

- all four Codex permission profiles;
- local and SSH-safe launch paths;
- the extra SSH confirmation for full access;
- incorrect confirmation and closed-stdin cancellation;
- legacy corrupt EOF-cache repair;
- provider and permission-menu return paths;
- Claude, DeepSeek-compatible, and Codex native CLI dispatch;
- native configuration isolation and project propagation; and
- the OpenAI HTTPS preflight contract.

The release result is 40 assertions passed and zero failed. Python launcher
tests provide additional prompt and layout coverage.
