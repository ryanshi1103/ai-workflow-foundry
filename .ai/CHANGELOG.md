# CHANGELOG

## 2026-08-02 — Mobile Reliability and Deployment Preservation

### Added
- ConnectBot Chinese input guidance using the built-in floating text field
- Regression coverage for preserving Codex profile `[projects]` trust entries
- OpenAI HTTPS endpoint coverage in the non-interactive launcher tests

### Changed
- Codex preflight now checks DNS, TCP, and TLS against `api.openai.com` instead of TCP port 53 on a public DNS server
- Launcher tests explicitly isolate inherited SSH variables, so local and remote cases behave consistently
- Legacy launcher structure tests resolve the source tree dynamically and use an isolated temporary HOME
- Codex profile deployment preserves machine-local project trust and writes profiles with mode `600`

### Maintenance
- Python bytecode caches are no longer tracked by Git; ignored files remain available locally
- Full regression result: 58 launcher structure checks, 35 Codex/remote checks, 4 deployment-preservation checks, and 11 Python tests passed

## 2026-08-01 — v3.1: Mobile SSH Remote Safety

### Added
- SSH remote-session detection and visible remote banner
- Extra `remote-yes` acknowledgement for remote `danger-full-access` and `bypassPermissions`
- Fedora Tailscale + OpenSSH setup script that preserves enforcing SELinux and restricts SSH to `tailscale0`
- Android + Tailscale + SSH + tmux operating guide
- Remote safe-mode and high-risk confirmation regression coverage
- End-to-end OPPO Reno9 verification through Tailscale, ConnectBot, OpenSSH, tmux, and the deployed `cc` menu
- Persistent ConnectBot host with a phone-local Ed25519 key and one-tap tmux auto-attach

### Changed
- README and project state document the mobile control workflow
- Launcher regression suite expanded from 27 to 33 passing checks
- Deployment version and backup labels updated to v3.1

## 2026-07-13 — v3.0: OpenAI Codex GPT-5.6 Sol Integration

### Added
- OpenAI Codex GPT-5.6 Sol as third native tool in `cc` launcher
- Four Codex profiles: manual, readonly, auto, full-access
- Codex-specific permission menu with approval_policy + sandbox_mode mapping
- Preflight checks: binary, version (>=0.144.0), profile validity, network
- Preflight cache (`codex-preflight`) for network checks (24h TTL)
- Graceful degradation when GPT-5.6 Sol is unavailable
- `docs/CODEX-INTEGRATION.md` — full integration documentation
- `docs/ARCHITECTURE.md` — architecture overview
- `docs/INSTALLATION.md` — installation guide
- `config/codex/` — profile templates and Codex AGENTS.md
- Backup and rollback support in deploy script

### Changed
- `bin/cc` — updated to v3.0 with three-tool menu
- Menu title: "Claude / DeepSeek / Codex 项目启动器"
- `.gitignore` — added auth.json, *.token exclusions

### Preserved
- Claude native launch unchanged
- DeepSeek V4 Pro launch unchanged
- Project selection, recent projects, project creation all unchanged
- `cc-projects-maintain` periodic maintenance unchanged
- `CC_ACTIVE_PROJECT` single source of truth pattern preserved
# 2026-08-02 — 手机单 VPN 出口节点

- 增加 `scripts/setup-mobile-exit-node.sh`，支持启用和撤销 Tailscale 出口节点。
- 增加持久 IPv4/IPv6 转发配置，复用现有 Clash/Mihomo TUN。
- 增加精确的 firewalld `tailscale-ssh` → `mihomo-tun` 转发策略，避免出口流量被 Fedora 默认区域策略过滤。
- 扩展手机远程健康检查，覆盖出口路由、转发状态和 Mihomo 接口。
- 修正 Fedora root-only `sshd_config.d` 目录造成的普通用户误报。
- 修复 Android Tailscale DNS 接管导致的公网域名解析失败，并完成出口 IP、GitHub、ChatGPT、Cloudflare、SSH 和 cc 实机验证。
