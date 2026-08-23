# CC Launcher — Adaptive Layout Examples

Rendered by `examples/render_launcher_mockups.py` through the exact
frame builders the live TUI uses (`flowfoundry.workspace.cli.tui`).
Every scenario is machine-verified: all box lines share one display
width (CJK-aware), nothing exceeds the terminal, and degradation
follows the tier order (truncate branch → hide branch → hide status
→ truncate name).

## 1. short names (100×24)

```
╭─ CC ─────────────────────╮
│ › FlowFoundry  main    ● │
│   System       master  ● │
│   VPN          main    ● │
╰──────────────────────────╯
↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出
```

## 2. very long names, wide (160×24)

```
╭─ CC · Projects ───────────────────────────────────────────╮
│ › Hunan-University-Motivation-PPT  slides-2026          ● │
│   ai-workflow-foundry              portfolio-migration  ● │
│   meeting-media-desktop            product              ● │
│   personal-knowledge-base-v2       main                 ● │
╰───────────────────────────────────────────────────────────╯
↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出
```

## 3. narrow 80-col terminal

```
╭─ CC · Projects ───────────────────────────────────────────╮
│ › Hunan-University-Motivation-PPT  slides-2026          ● │
│   ai-workflow-foundry              portfolio-migration  ● │
│   meeting-media-desktop            product              ● │
│   personal-knowledge-base-v2       main                 ● │
╰───────────────────────────────────────────────────────────╯
↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出
```

## 3b. 45-col: branch hidden

```
╭─ CC ─────────────────────────────────╮
│ › Hunan-University-Motivation-PPT  ● │
│   ai-workflow-foundry              ● │
│   meeting-media-desktop            ● │
│   personal-knowledge-base-v2       ● │
╰──────────────────────────────────────╯
Enter 打开  q 退出
```

## 3c. 30-col: status hidden

```
╭─ CC ─────────────────────╮
│ › Hunan-University-Moti… │
│   ai-workflow-foundry    │
│   meeting-media-desktop  │
│   personal-knowledge-ba… │
╰──────────────────────────╯
Enter 打开  q 退出
```

## 4. wide terminal, full columns (160×24)

```
╭─ CC · Projects ───────────────────────────────────────────╮
│   ai-workflow-foundry              portfolio-migration  ● │
│   meeting-media-auto               master               ● │
│ › meeting-media-desktop            product              ● │
│   Hunan-University-Motivation-PPT  slides-2026          ● │
│   personal-knowledge-base-v2       main                 ● │
╰───────────────────────────────────────────────────────────╯
↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出
```

## 5. only 3 projects (100×40)

```
╭─ CC ─────────────────────╮
│   FlowFoundry  main    ● │
│ › System       master  ● │
│   VPN          main    ● │
╰──────────────────────────╯
↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出
```

## 6. 20 projects, scrolling viewport (80×24)

```
╭─ CC · Projects ───────────────────────────────────────────╮
│   ai-workflow-foundry              portfolio-migration  ● │
│   meeting-media-auto               master               ● │
│   meeting-media-desktop            product              ● │
│   Hunan-University-Motivation-PPT  slides-2026          ● │
│   personal-knowledge-base-v2       main                 ● │
│   family-budget-sheets             main                 ● │
│   garden-planner                   develop              ● │
│   chess-clock                      master               ● │
│   bike-repair-log                  main                 ● │
│   leetcode-notes                   study                ● │
│   recipe-box                       main                 ● │
│   travel-log                       master               ● │
│ › home-automation                  feature/sensors      ● │
│   study-flashcards                 main                 ● │
│   web-clipper                      main                 ● │
│   backup-scripts                   master               ● │
│   podcast-notes                    main                 ● │
│   workout-tracker                  main                 ● │
╰───────────────────────────────────────────────────────────╯
↑↓ 13/20 选择  Enter 打开  / 搜索  Tab 更多  q 退出
```

## detail screen (120×24)

```
╭─ ai-workflow-foundry ──────────╮
│   portfolio-migration  ● clean │
│                                │
│ › Auto      DeepSeek · plan    │
│   Codex     不可用             │
│   DeepSeek                     │
│   Claude                       │
╰────────────────────────────────╯
↑↓ 选择  Enter 启动  Tab 项目  q 退出
```

## detail screen, narrow (60×24)

```
╭─ ai-workflow-foundry ──────────────────────────────────╮
│   feature/very-long-branch-name-for-media-sy…  ● clean │
│                                                        │
│ › Auto      DeepSeek · plan                            │
│   Codex     不可用                                     │
│   DeepSeek                                             │
│   Claude                                               │
╰────────────────────────────────────────────────────────╯
↑↓ 选择  Enter 启动  Tab 项目  q 退出
```

## permission screen (100×24)

```
╭─ ai-workflow-foundry · Claude ╮
│   Manual       default        │
│   acceptEdits  acceptEdits    │
│ › plan         只读规划       │
│   auto         自动执行       │
│   bypass       完全访问       │
╰───────────────────────────────╯
↑↓ 选择  Enter 启动  Tab 返回  q 返回
```

## line input (80×24)

```
╭─ CC · 新建项目 ───────────╮
│ 名称: meeti▊ng-media-auto │
╰───────────────────────────╯
Enter 确认  Esc 取消
```
