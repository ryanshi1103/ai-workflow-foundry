# CC Launcher — Adaptive Layout Design

The `cc` launcher TUI uses a content-aware adaptive layout engine.  No
fixed-width frame: content is measured first, columns are chosen, then
width/height follow.  Machine-verified renders live in
[launcher-layout-examples.md](launcher-layout-examples.md).

## Architecture

| Module | Role |
|--------|------|
| `src/flowfoundry/workspace/cli/layout.py` | Pure engine: display width, truncation, column planning, box renderer |
| `src/flowfoundry/workspace/cli/tui.py` | Raw-mode terminal, frame builders, screen flows, auto mode |
| `src/flowfoundry/workspace/cli/launcher.py` | TTY gate + launch orchestration (prompt flow unchanged for non-TTY) |
| `examples/render_launcher_mockups.py` | Renders + verifies scenarios through the production frame builders |

The frame builders are pure functions (strings in, strings out) — the
mockup renderer, the unit tests, and the live TUI all call the same code,
so alignment contracts are verified on the same path that draws the
terminal.

## Measurement

`layout.display_width` counts terminal cells, not bytes:

- CJK / wide / emoji code points → 2 cells
- combining marks, variation selectors, zero-width controls → 0 cells
- ANSI SGR sequences are stripped before measuring (color never breaks alignment)

`truncate` and `pad` operate on the same cell semantics; truncation only
happens when the terminal requires it and always ends in `…`.

## Column planning (project list)

For rows of `(name, branch, status)` the planner computes natural widths
from the visible content, then degrades in a fixed tier order when the
terminal narrows:

1. **full** — name + branch + status
2. **medium** — name + truncated branch + status
3. **narrow** — name + status
4. **very narrow** — name only (names truncated as the last resort)

Secondary information disappears before the layout gets ugly.  The box
width is `min(content, terminal − margin)` — short content gets a small
box, long content expands to the terminal limit, never beyond it.

## Height

Visible rows = `min(item count, terminal height − overhead)`.  Three
projects render three rows; twenty projects render a compact scrolling
viewport whose window follows the selection.  The footer shows a
`↑↓ 13/20` counter only while scrolling is possible.

## Footers

Per-screen, only the keys that act on that screen:

- projects: `↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出`
- detail: `↑↓ 选择  Enter 启动  Tab 项目  q 退出`
- permission: `↑↓ 选择  Enter 启动  Tab 返回  q 返回`
- input: `Enter 确认  Esc 取消`

## Project detail

Branch + git status on the first line (status right-aligned to the box
edge), then the provider list.  Line 1's natural content contributes to
the box width; a narrow terminal shrinks the branch slot before anything
else.

## Auto mode

`Auto` is the first row of the detail screen.  Resolution order:

1. remembered choice for this project (`~/.local/state/cc-launcher/auto-config.json`)
2. remembered global provider
3. first available provider (binary present, profile configured)

The permission mode follows the remembered choice, else a safe default
(`plan` for Claude/DeepSeek, `manual` for Codex).  Enter on `Auto`
launches directly when the configuration is unambiguous and safe;
bypass/full-access always opens the explicit permission screen.
Availability is part of the decision — an unavailable provider is dimmed
and never auto-selected.

## TTY gate

`launcher.main` uses the TUI only when stdin and stdout are both TTYs
and `_CC_PLAIN` is unset.  Scripts, pipes, and tests keep the original
line-prompt flow byte-for-byte.
