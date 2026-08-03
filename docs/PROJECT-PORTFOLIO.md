# 项目组合观察与命名方案

盘点日期：2026-08-01

本清单基于 `/home/ryan/Projects` 下 13 个活跃顶层目录的 README、交付物、
源码结构、Git 状态和现有项目索引整理。目录名统一建议使用小写
`kebab-case`；产品显示名可以保留中文。隔离区不是活跃项目，不计入 13 个项目。

## 组合概览

| 组合 | 项目 | 结论 |
|---|---|---|
| AI 工具基础设施 | `ai-project-workspace-manager` | 唯一源码与部署真源，继续保留 |
| AI 工具遗留工作区 | `claude-switcher-setup`、`codex-claude` | 内容已进入主项目或属于早期构建，核验后归档 |
| 会映产品线 | `meeting-media-auto`、`meeting-media-desktop` | 前者为 Linux/Web 研发工作台，后者为 Windows/Android 发行仓库，两者不是重复项目 |
| 设备与数据 | `PhotoTransform`、`phone-control` | 分别负责照片安全归档和 OPPO 手机优化 |
| 内容与视觉交付 | `A`、`Hunan-University-Motivation-PPT`、`System` | 分别为营地印刷物料、湖南四校演示、GRUB 主题 |
| 网络部署 | `VPN` | Shadowrocket、VLESS、Hysteria 2 与 Mihomo 配置 |
| 数据应用 | `social-negative-monitor` | 已从“负面监控”演进为通用反馈分析系统 |
| 电商自动化 | `taobao-auto-shop` | 已从 `A` 拆出的独立原型候选，尚未完成生产验证 |

## 规范名称

| 当前目录 | 规范显示名 | 建议目录名 | 处理建议 |
|---|---|---|---|
| `A` | 研学营印刷物料 | `camp-print-materials` | 子项目已拆出；待 Git 工作区干净后改名 |
| `Hunan-University-Motivation-PPT` | 湖南四校文化动员演示 | `hunan-four-universities-presentation` | 统一为小写 kebab-case；交付物完整 |
| `PhotoTransform` | OPPO 手机照片安全归档 | `oppo-photo-archive` | 高优先级改名；“Transform”与实际归档职责不符 |
| `System` | Minimal Focus GRUB 主题 | `grub-minimal-focus-theme` | 高优先级改名；当前只是泛化容器，真实项目位于同名子目录 |
| `VPN` | Shadowrocket VPN 部署工具 | `shadowrocket-vpn-deployment` | 建议改名；现名过泛 |
| `ai-project-workspace-manager` | AI Project Workspace Manager | `ai-project-workspace-manager` | 保持不变；设为核心基础设施 |
| `claude-switcher-setup` | Codex 接入会话归档 | `codex-integration-session-archive` | 不建议先改名；确认主项目已完整吸收后进入隔离区 |
| `codex-claude` | AI Project Manager 早期构建 | `ai-project-manager-legacy` | 先核对未合并文件，再归档或按此名保留 |
| `meeting-media-auto` | 会映 Linux/Web 工作台 | `huiying-media-workbench` | 产品品牌稳定后改名；注意同步部署路径与文档 |
| `meeting-media-desktop` | 会映桌面发行项目 | `huiying-desktop-release` | 与工作台分开保留；包含 Windows 和 Android 发行工作 |
| `phone-control` | OPPO 手机控制与优化 | `oppo-phone-control` | 建议改名；README 中残留的 `phone-cleaner` 结构说明需同步修订 |
| `social-negative-monitor` | 反馈分析系统 | `feedback-analysis-system` | 建议改名；当前名称已不能覆盖正向、体验和人工复核能力 |
| `taobao-auto-shop` | 淘宝虚拟商品自动贩卖系统 | `taobao-auto-shop` | 保持名称；独立原型候选，先做安全审查和真实能力验证 |

## 整理顺序

1. `A` 中的 `taobao-auto-shop` 已无损拆为独立顶层项目；剩余印刷物料仓库应在
   未提交工作得到保全后命名为 `camp-print-materials`。
2. 再处理三个泛化或失真的目录名：`PhotoTransform`、`System`、`VPN`。
3. 核验 `claude-switcher-setup` 和 `codex-claude` 相对
   `ai-project-workspace-manager` 的唯一文件；只在确认合并完成后归档。
4. 最后统一产品线名称。会映两个仓库存在部署脚本、数据路径和文档引用，改名应在
   工作区干净并完成引用搜索后进行。
5. 每次只改一个项目；改名前提交或备份未提交工作，改后同步 README、项目元数据、
   最近项目索引和所有硬编码路径，再运行该项目自己的测试。

## 当前风险

- 多数项目存在未提交或未跟踪文件；本次盘点不执行目录移动或重命名。
- `A` 的项目边界混杂已解除，但仓库仍有大量未提交交付物，暂不改根目录名。
- `System` 外层没有 README，真实 GRUB 项目多嵌套一层，容易被维护器误判。
- `claude-switcher-setup` 和 `codex-claude` 的 README 仍是自动生成占位内容，
  不应继续作为活跃基础设施入口。
- `_trash-review/20260801/phone-photo-archive` 是照片归档会话残留；真实成果在
  `PhotoTransform`，当前隔离方向合理，但不应在未复核保留期前删除。

## GitHub 作品集状态

2026-08-03 开始以“有意义、可验证、无隐私风险”为公开标准，而不是将所有
项目机械公开。

| GitHub 仓库 | 可见性 | 作品集角色 |
|---|---|---|
| `grub-minimal-focus-theme` | 公开 | 视觉系统工具；GPL-3.0、预览、回滚和 EFI 验证完整 |
| `feedback-analysis-system` | 公开 | Python/Streamlit 数据应用；干净发布快照、90 项测试 |
| `oppo-phone-control` | 公开 | Android/ADB 防御性自动化工具 |
| `oppo-photo-archive` | 公开 | Android 照片事务式归档；SHA-256、原子安装、显式删除门与 4 项测试 |
| `confera-media-skills` | 公开 | 10 个媒体 AI Skill；候选输出、人工审核、禁止越权执行，3 项契约测试 |
| `print-ready-nameplate-generator` | 公开 | CSV 到可编辑 A4 姓名牌 PPTX；虚构示例、路径安全与真实 LibreOffice 验证 |
| `ai-workspace-manager` | 公开 | 核心工具的可移植脱敏快照；统一启动、项目维护、会话恢复与 108 项回归检查 |
| `ai-project-workspace-manager` | 私有 | 核心工具；待脱敏本机路径和运维文档后再评估公开 |
| `hunan-four-universities-presentation` | 私有 | 演示设计；已上传，待补全逐图许可记录后再评估公开 |
| `huiying-media-workbench` | 私有 | 会映 Linux/Web 研发仓库；496 项严格测试通过后上传 |
| `huiying-desktop-release` | 私有 | 会映 Windows/Android 商业发行候选；保留产品与基线分支 |
| `taobao-auto-shop` | 私有 | 未验证原型，不进入公开作品集 |

公开主页文案的源文件为 [GitHub Portfolio](GITHUB-PORTFOLIO.md)。

GitHub 账号 `ryanshi1103` 的公开简介已设置为：
“Building local-first software, safety-conscious automation, and practical system tools.”
七个原创公开作品仓库均已采用小写 `kebab-case` 命名，具备仓库简介、README 与
`branding/logo.png`。其中 `confera-media-skills` 将会映项目的 10 个原创 Skill
整理为独立作品；官方/第三方 Skill 不计为个人原创。GitHub 的 `Projects` 标签是项目看板，不是代码仓库列表；
作品应从 `Repositories` 查看。个人主页置顶仓库需要在 GitHub 网页端通过
`Customize your pins` 设置，公开 API 不提供该写操作。
