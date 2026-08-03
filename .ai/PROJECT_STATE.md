# AI Project Workspace Manager — 项目状态

## 项目概述

AI 工具链的全局项目管理、启动和维护系统。整合了 cc 启动器、AI Project Manager、Projects 定期维护器和自动命名系统。

## 当前状态

**活跃开发中** — 项目组合盘点与命名规则已收敛。

### 已完成
- [x] cc 统一启动器 v3.1（支持 Claude、DeepSeek、OpenAI Codex GPT-5.6 Sol 与 SSH 手机远控）
- [x] AI Project Manager 核心（会话追踪、整理、恢复）
- [x] Projects 定期维护系统（cc-projects-maintain）
- [x] 自动项目命名检测（auto_name.py）
- [x] 项目分类和隔离系统（maintain.py）
- [x] systemd 用户定时器（每周快速维护、每月深度维护、隔离清理）
- [x] Round 2 项目归并：合并 13、automated-test-suite、cc-launcher-v2-0-deployment-cleanup-scri
- [x] OpenAI Codex GPT-5.6 Sol 集成（4 个 profile、预检、稳定降级）
- [x] 修复 cc Codex 预检缓存的 EOF/set -u 崩溃，并增加非交互回归测试
- [x] 完成 13 个活跃项目的组合盘点、规范命名方案和维护器识别安全修复
- [x] 将 `taobao-auto-shop` 从混合项目 `A` 无损拆分为独立顶层项目
- [x] 增加 Tailscale + Fedora OpenSSH 手机远控方案、远程会话提示和高权限二次确认
- [x] v3.1 正式部署与 17 项部署校验通过；电脑端 Tailscale/OpenSSH 已启用并限制到 `tailscale0`
- [x] OPPO Reno9 Pro+ 安装并校验 Tailscale 1.98.8 与 ConnectBot 1.10.9
- [x] OPPO 实机端到端验证：切换 v2rayNG → Tailscale、ping、ConnectBot SSH、`tmux` 和 `cc` 菜单均成功
- [x] ConnectBot 永久主机、手机本地 Ed25519 `cc-mobile` 密钥、免密认证和一键自动附加 tmux 已通过重启验证
- [x] 增加手机远程链路只读健康检查（服务、私网、防火墙、密钥权限、tmux、cc）
- [x] 将 Fedora 电脑发布为 Tailscale 出口节点，并通过 Clash/Mihomo TUN 转发手机互联网流量
- [x] Tailscale 出口节点后台批准、Android 选中、DNS 修复与境外 HTTPS/SSH 并行访问实测通过
- [x] 手机链路优化：OpenAI HTTPS 预检、SSH 环境隔离测试、ConnectBot 中文输入说明与 Codex profile 本地信任保留
- [x] 筛选并发布 GitHub 作品集：3 个公开精选作品、个人主页，以及会映与湖南演示的私有仓库

### 待完成
- [ ] systemd timer 实际运行验证
- [ ] 隔离区清理（_trash-review 复核）
- [ ] GPT-5.6 Sol 账户开放后完成烟雾测试

## 源码结构

```
src/ai_project_manager/   — Python 包（15 个模块）
bin/                       — 用户级可执行脚本
config/                    — 配置模板和 systemd 单元
tests/                     — 测试套件
scripts/                   — 部署和验证脚本
docs/                      — 文档
```

## 部署路径

| 源文件 | 部署目标 |
|--------|----------|
| bin/cc | ~/.local/bin/cc |
| bin/cc-projects-maintain | ~/.local/bin/cc-projects-maintain |
| bin/aiproj | ~/.local/bin/aiproj |
| src/ai_project_manager/* | ~/.local/share/ai-project-manager/ai_project_manager/ |
| config/systemd/* | ~/.config/systemd/user/ |
| config/maintenance.conf.example | ~/.config/cc-projects/maintenance.conf |

## 最后更新

2026-08-03 — 完成首批 GitHub 作品集筛选、脱敏发布与个人主页整理
