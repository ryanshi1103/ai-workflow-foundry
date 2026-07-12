# AI Project Workspace Manager

AI 工具链的全局项目管理、启动和维护系统。

## 组件

- **cc** — Claude / DeepSeek 统一启动器，支持项目导航、模型选择和权限模式
- **cc-projects-maintain** — ~/Projects 定期维护系统（快速/深度维护、隔离清理）
- **ai-project-manager** — AI 会话的项目创建、追踪、整理和恢复（Python 包）
- **auto_name** — 基于项目内容的自动命名检测
- **maintain** — 项目分类、重复检测、隔离和索引生成

## 安装

```bash
# 从源码部署
./scripts/deploy.sh

# 验证部署
./scripts/verify.sh
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

## 许可证

MIT License — 参见 LICENSE 文件。
