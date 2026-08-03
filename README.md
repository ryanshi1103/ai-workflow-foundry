# AI Project Workspace Manager

AI 工具链的全局项目管理、启动和维护系统。

## 组件

- **cc** — Claude / DeepSeek 统一启动器，支持项目导航、模型选择和权限模式
- **cc-projects-maintain** — ~/Projects 定期维护系统（快速/深度维护、隔离清理）
- **ai-project-manager** — AI 会话的项目创建、追踪、整理和恢复（Python 包）
- **auto_name** — 基于项目内容的自动命名检测
- **maintain** — 项目分类、重复检测、隔离和索引生成

`cc` 的项目选择器区分“主项目”和“托管发布/归档目录”。公开快照、扩展包、
GitHub 主页克隆和遗留复核目录不会挤占主项目列表，但仍可从 `m` 子菜单进入。
每周快速维护会对配置为自动更新的托管 Git 仓库执行安全快进同步；工作区有改动、
本地领先、分支分叉或没有上游时只报告，不覆盖本地内容。

## 安装

```bash
# 从源码部署
./scripts/deploy.sh

# 验证部署
./scripts/verify.sh
```

## cc 启动器回归测试

`tests/test-cc-eof-fix.sh` 使用临时 HOME 和假的 `codex`/`aiproj` 命令，覆盖
Codex 四种权限、danger-full-access 二次确认、stdin/EOF 安全取消、旧缓存修复，
OpenAI HTTPS 预检，以及 Claude/DeepSeek 分支；测试会显式隔离 SSH 环境变量，
最终 `exec` 会被截获，不会启动真实 AI 会话。

当前基础回归包括 64 项 `cc` 菜单/路径检查、35 项权限与 EOF 检查，以及
14 项 Python 维护器测试。

```bash
./tests/test-cc.sh
./tests/test-cc-eof-fix.sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py'

# 手动检查/同步托管仓库
cc-projects-maintain --sync-managed --dry-run
cc-projects-maintain --sync-managed
```

正式部署会备份现有 Codex profile、更新源码管理的模型与权限键，并保留 profile 中
由 Codex 写入的本机 `[projects]` 信任记录；profile 权限统一为 `600`。

## 手机远程控制

Android 手机可通过 Tailscale 私网和 Fedora OpenSSH 进入电脑的真实终端，并在 `tmux` 中运行同一个
`cc`，完整保留项目、工具和权限选择。远程完全访问模式会额外要求
`remote-yes`。安装与使用说明见 [手机远程控制 cc](docs/MOBILE-REMOTE.md)。
电脑端故障排查可运行只读检查：

```bash
./scripts/check-mobile-remote.sh
```

如需让手机在同一个 Tailscale VPN 中同时远控电脑并经电脑的 Clash/Mihomo 访问
互联网，可配置本机出口节点：

```bash
./scripts/setup-mobile-exit-node.sh
```

## 用户级部署路径

| 组件 | 路径 |
|------|------|
| cc 启动器 | `~/.local/bin/cc` |
| 维护命令 | `~/.local/bin/cc-projects-maintain` |
| AI PM CLI | `~/.local/bin/aiproj` |
| Python 包 | `~/.local/share/ai-project-manager/ai_project_manager/` |
| 维护配置 | `~/.config/cc-projects/` |
| systemd 定时器 | `~/.config/systemd/user/cc-projects-*` |
| 全局规则 | `~/.claude/CLAUDE.md`, `~/.claude-deepseek/CLAUDE.md` |

## 项目结构

```
ai-project-workspace-manager/
├── src/ai_project_manager/   # Python 包源码
├── bin/                       # 用户级可执行脚本
├── config/                    # 配置模板和 systemd 单元
├── docs/                      # 架构、安装、维护文档
├── tests/                     # 测试套件
├── scripts/                   # 部署和验证脚本
└── .ai/                       # 项目元数据
```

## 项目组合

`~/Projects` 的项目边界、规范显示名、建议目录名和整理顺序记录在
[项目组合观察与命名方案](docs/PROJECT-PORTFOLIO.md)。目录改名必须在工作区干净、
硬编码路径已盘点且项目测试通过后逐个执行。
公开 GitHub 作品集的个人主页源文件见
[GitHub Portfolio](docs/GITHUB-PORTFOLIO.md)。

跨项目的共享能力已整理为公开旗舰
[FlowFoundry AI](https://github.com/ryanshi1103/ai-workflow-foundry)：只将真实共享的
Workspace Manager 底座物理纳入，Confera、反馈分析和文档自动化通过明确契约关联，
Android、GRUB、演示与实验项目继续保持独立边界。

## 许可证

MIT License — 参见 LICENSE 文件。
