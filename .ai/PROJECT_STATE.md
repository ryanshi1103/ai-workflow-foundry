# AI Project Workspace Manager — 项目状态

## 项目概述

AI 工具链的全局项目管理、启动和维护系统。整合了 cc 启动器、AI Project Manager、Projects 定期维护器和自动命名系统。

## 当前状态

**活跃开发中** — Round 2 项目归并完成。

### 已完成
- [x] cc 统一启动器 v2.1（移除手动重命名菜单，支持项目导航）
- [x] AI Project Manager 核心（会话追踪、整理、恢复）
- [x] Projects 定期维护系统（cc-projects-maintain）
- [x] 自动项目命名检测（auto_name.py）
- [x] 项目分类和隔离系统（maintain.py）
- [x] systemd 用户定时器（每周快速维护、每月深度维护、隔离清理）
- [x] Round 2 项目归并：合并 13、automated-test-suite、cc-launcher-v2-0-deployment-cleanup-scri

### 待完成
- [ ] 端到端部署测试
- [ ] systemd timer 实际运行验证
- [ ] 隔离区清理（_trash-review 复核）

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

2026-07-13 — Round 2 项目归并
