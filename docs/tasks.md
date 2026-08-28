# Project Tasks

## 已完成
<!-- session:20260805-151008-claude-198a0a -->
- [x] ## 验收完成 — APPROVED ✅
<!-- session:20260805-151008-claude-198a0a -->
- [x] | 15 个 root shim 文件删除 | ✅ 全部清除，AST 级合约测试守卫 |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | 5 个 intra-package 导入修复 | ✅ `..project` → `.project` 等全部修正 |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | Cross-subpackage 显式导入 | ✅ `..policy.runtime` 替代 `..utils` |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | 兼容层 (`ai_project_manager`) | ✅ 直接映射到 canonical 模块 |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | 架构合约测试 | ✅ 7 tests — 导入可用性、shim 缺失、AST 守卫、CLI 导出、Provider 隔离 |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | 运行时测试 | ✅ 6 tests — lifecycle、policy、recovery、finalize（全管道 + 失败路径） |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | 全部测试套件 | ✅ 103 passed + 35 subtests |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | `flowfoundry validate` | ✅ 4 components, 1 contract, 16 capabilities |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | Git 工作区 | ✅ 干净，2 个结构化提交 |
<!-- session:20260805-151008-claude-198a0a -->
- [x] | 回滚路径 | ✅ 已记录 revert 命令 + pre-migration tag |
<!-- session:20260805-151008-claude-198a0a -->
- [x] Now set up the shared collaboration directory structure.
<!-- session:20260805-151008-claude-198a0a -->
- [x] The worktree isolation restricts writes to the worktree itself. I'll set up the collaboration directory within the worktree.
<!-- session:20260805-151008-claude-198a0a -->
- [x] Queue is empty — Codex hasn't created checkpoints yet. Let me proactively review the current HEAD while waiting.
<!-- session:20260805-151008-claude-198a0a -->
- [x] Architecture agent completed — all claims verified. Now let me write the comprehensive Phase 2.1 review.
<!-- session:20260805-151008-claude-198a0a -->
- [x] ### Reviews Completed
<!-- session:20260805-151008-claude-198a0a -->
- [x] ✅ Finalization decomposition: 882-line monolith → 6-line facade + 5 focused modules
<!-- session:20260805-151008-claude-198a0a -->
- [x] ✅ Launcher deduplication: genuine shared `_launch_session()` core
<!-- session:20260805-151008-claude-198a0a -->
- [x] ✅ Stable APIs: `lifecycle` (20 exports) and `sessions` (9 exports) with lazy loading
<!-- session:20260805-151008-claude-198a0a -->
- [x] ✅ Circular import prevention: `__getattr__` + subprocess contract test
<!-- session:20260805-150012-claude-27eec5 -->
- [x] I have a clear picture. Let me set up tasks and begin execution.

## 进行中

## 未完成

## 已取消

## 等待用户确认

