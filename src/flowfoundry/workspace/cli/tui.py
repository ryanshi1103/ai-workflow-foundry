"""Adaptive interactive TUI for the ``cc`` launcher (TTY sessions only).

Every screen is laid out by the content-aware engine in :mod:`layout`:
content is measured first, columns are chosen, then width/height follow.
Nothing is forced into a fixed frame.

The module splits into three layers:

* terminal plumbing — raw-mode key reading and in-place frame redraws
* pure frame builders — strings in, strings out (used by tests and mockups)
* screen loops — interactive flows returning launch decisions

Auto mode resolves the last-used provider and permission profile per
project, falls back to a safe default, and only asks when the choice is
ambiguous.  Availability (binary present, profile configured) is part of
the decision.
"""

from __future__ import annotations

import codecs
import json
import os
import select
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:  # non-POSIX platforms (tests, docs) fall back to line input
    import termios
except ImportError:  # pragma: no cover
    termios = None  # type: ignore[assignment]

from ..providers import CLAUDE_PERMISSION_MODES, CODEX_PROFILES, claude_config_dir
from . import launcher
from .layout import (
    GAP,
    display_width,
    pad,
    plan_project_columns,
    render_box,
    render_project_row,
    truncate,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUTO_CONFIG_FILE = launcher.RECENT_STATE_DIR / "auto-config.json"

# Provider keys in launch configs (same vocabulary as the prompt launcher).
PROVIDER_CLAUDE = "c"
PROVIDER_DEEPSEEK = "d"
PROVIDER_CODEX = "o"

_PROVIDER_ORDER = [PROVIDER_CLAUDE, PROVIDER_DEEPSEEK, PROVIDER_CODEX]

# Short, display-safe labels for the TUI (the prompt flow keeps full names).
PROVIDER_LABELS = {
    PROVIDER_CLAUDE: "Claude",
    PROVIDER_DEEPSEEK: "DeepSeek",
    PROVIDER_CODEX: "Codex",
}

_CLAUDE_MODE_LABELS = {
    "m": ("Manual", "default"),
    "e": ("acceptEdits", "acceptEdits"),
    "p": ("plan", "只读规划"),
    "a": ("auto", "自动执行"),
    "b": ("bypass", "完全访问"),
}

_CODEX_MODE_LABELS = {
    "m": ("manual", "workspace-write · on-request"),
    "p": ("readonly", "read-only · never"),
    "a": ("auto", "workspace-write · never"),
    "b": ("full-access", "danger-full-access · never"),
}

_DEFAULT_MODE = {PROVIDER_CLAUDE: "p", PROVIDER_DEEPSEEK: "p", PROVIDER_CODEX: "m"}

# ANSI SGR codes (only emitted when the frame is rendered for a TTY).
_SGR_DIM = "2"
_SGR_BRIGHT = "1"
_SGR_GREEN = "32"
_SGR_YELLOW = "33"
_SGR_CYAN = "36"

DOT_CLEAN = "●"
DOT_DIRTY = "●"
DOT_NONE = "·"

# Space reserved around the box: one margin line above, footer + margin below.
_BOX_OVERHEAD = 4

MENU_BACK = "back"  # tab: return to the previous screen
MENU_ACTIONS = "actions"  # tab: open the actions overlay

# ---------------------------------------------------------------------------
# Terminal plumbing
# ---------------------------------------------------------------------------


def colors_enabled() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _sgr(text: str, code: str, enabled: bool) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if enabled else text


def dim(text: str, enabled: bool = True) -> str:
    return _sgr(text, _SGR_DIM, enabled)


class RawTerm:
    """Raw-mode terminal with in-place frame redraw and UTF-8 key reading."""

    def __init__(self) -> None:
        self._fd = sys.stdin.fileno()
        self._saved: list = []
        self._active = False
        self._decoder = codecs.getincrementaldecoder("utf-8")()
        self._lines_rendered = 0

    # -- lifecycle ---------------------------------------------------------

    def enter(self) -> None:
        if self._active or termios is None:
            return
        self._saved = termios.tcgetattr(self._fd)
        raw = termios.tcgetattr(self._fd)
        raw[3] &= ~(termios.ICANON | termios.ECHO)
        termios.tcsetattr(self._fd, termios.TCSADRAIN, raw)
        self._write("\x1b[?25l")  # hide cursor
        self._active = True

    def exit(self) -> None:
        if not self._active:
            return
        self._write("\x1b[?25h")  # show cursor
        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved)
        self._active = False

    def _write(self, data: str) -> None:
        os.write(sys.stdout.fileno(), data.encode("utf-8", errors="replace"))
        sys.stdout.flush()

    # -- rendering ---------------------------------------------------------

    def redraw(self, frame: str) -> None:
        """Repaint the frame in place, clearing any stale lines."""
        lines = frame.split("\n")
        out: list[str] = []
        if self._lines_rendered:
            out.append(f"\x1b[{self._lines_rendered}A")
        for line in lines:
            out.append("\x1b[2K" + line + "\r\n")
        for _ in range(max(0, self._lines_rendered - len(lines))):
            out.append("\x1b[2K\r\n")
        self._lines_rendered = len(lines)
        self._write("".join(out))

    # -- input -------------------------------------------------------------

    def read_key(self) -> str:
        """Read one logical key: 'up' 'down' 'left' 'right' 'enter' 'tab'
        'backspace' 'esc' 'eof', or a single printable character."""
        data = self._read_bytes(1)
        if not data:
            return "eof"
        if data == b"\x1b":
            return self._read_escape()
        if data in (b"\r", b"\n"):
            return "enter"
        if data == b"\t":
            return "tab"
        if data in (b"\x7f", b"\x08"):
            return "backspace"
        if data == b"\x04":
            return "eof"
        if data[0] < 0x20:
            return ""
        return self._decode(data)

    def _read_bytes(self, count: int) -> bytes:
        try:
            return os.read(self._fd, count)
        except (InterruptedError, OSError):
            return b""

    def _decode(self, data: bytes) -> str:
        try:
            return self._decoder.decode(data)
        except UnicodeDecodeError:
            self._decoder.reset()
            return ""

    def _read_escape(self) -> str:
        if not select.select([self._fd], [], [], 0.05)[0]:
            return "esc"
        seq = self._read_bytes(4)
        mapping = {
            b"[A": "up",
            b"[B": "down",
            b"[C": "right",
            b"[D": "left",
            b"[H": "home",
            b"[5~": "pageup",
            b"[6~": "pagedown",
            b"OA": "up",
            b"OB": "down",
            b"OC": "right",
            b"OD": "left",
        }
        for prefix, key in mapping.items():
            if seq.startswith(prefix):
                return key
        # Partial or unknown sequence (Alt+key, F-keys): swallow the rest.
        return "esc" if not seq else ""


# ---------------------------------------------------------------------------
# Git metadata (cached per path for the lifetime of a screen)
# ---------------------------------------------------------------------------

_git_cache: dict[str, tuple[str, str, str]] = {}


def git_info(path: Path, *, refresh: bool = False) -> tuple[str, str, str]:
    """Return (branch, dot, dot_kind) for a project directory.

    dot_kind is 'clean', 'dirty', or 'none' (not a git repository).  The
    result is cached because a 20-project list must not spawn 40 git
    processes per keypress.
    """
    key = str(path)
    if not refresh and key in _git_cache:
        return _git_cache[key]

    branch, dot, kind = "", DOT_NONE, "none"
    try:
        top = subprocess.run(
            ["git", "-C", key, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        ).stdout.strip()
        if top:
            branch = subprocess.run(
                ["git", "-C", key, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=3,
            ).stdout.strip()
            status = subprocess.run(
                ["git", "-C", key, "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=3,
            ).stdout
            kind = "clean" if not status.strip() else "dirty"
            dot = DOT_CLEAN
    except (OSError, subprocess.SubprocessError):
        pass
    _git_cache[key] = (branch, dot, kind)
    return _git_cache[key]


# ---------------------------------------------------------------------------
# Auto mode state (recent project, last provider, last permission profile)
# ---------------------------------------------------------------------------


def load_auto_config() -> dict:
    if AUTO_CONFIG_FILE.is_file():
        try:
            return json.loads(AUTO_CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_auto_config(cfg: dict) -> None:
    AUTO_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = AUTO_CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(AUTO_CONFIG_FILE)


def provider_availability() -> dict[str, bool]:
    claude_ok = launcher._find_executable("claude") is not None
    return {
        PROVIDER_CLAUDE: claude_ok,
        PROVIDER_DEEPSEEK: claude_ok and claude_config_dir("deepseek").is_dir(),
        PROVIDER_CODEX: launcher._find_executable("codex") is not None,
    }


def resolve_auto(project: Path) -> tuple[str, str]:
    """Resolve the auto launch configuration for a project.

    Priority: remembered choice for this project → remembered global
    provider → first available provider.  The mode follows the project's
    remembered choice, else a safe default (plan / manual).
    """
    avail = provider_availability()
    cfg = load_auto_config()
    remembered = cfg.get("projects", {}).get(str(project), {}) or {}
    provider = ""
    for candidate in (remembered.get("provider"), cfg.get("last_provider")):
        if candidate in _PROVIDER_ORDER and avail.get(candidate):
            provider = candidate
            break
    if not provider:
        provider = next(
            (key for key in _PROVIDER_ORDER if avail.get(key)),
            PROVIDER_CLAUDE,
        )
    valid_modes = (
        _CODEX_MODE_LABELS if provider == PROVIDER_CODEX else _CLAUDE_MODE_LABELS
    )
    if (
        remembered.get("provider") == provider
        and remembered.get("mode") in valid_modes
    ):
        mode = remembered["mode"]
    else:
        mode = _DEFAULT_MODE[provider]
    return provider, mode


def _record_launch(project: Path, provider: str, mode: str) -> None:
    cfg = load_auto_config()
    cfg.setdefault("projects", {})[str(project)] = {"provider": provider, "mode": mode}
    cfg["last_provider"] = provider
    save_auto_config(cfg)


# ---------------------------------------------------------------------------
# Pure frame builders (used by tests, mockups, and the live TUI alike)
# ---------------------------------------------------------------------------


def _inner_cap(term_width: int) -> int:
    return max(term_width - 6, 10)


def _max_viewport(term_height: int) -> int:
    return max(4, term_height - _BOX_OVERHEAD - 2)


def _window(item_count: int, selected: int, max_rows: int) -> tuple[int, int]:
    viewport = max(4, min(item_count, max_rows))
    start = 0
    if selected >= start + viewport:
        start = selected - viewport + 1
    if selected < start:
        start = selected
    return start, viewport


@dataclass
class ProjectEntry:
    path: Path
    name: str
    branch: str = ""
    dot: str = DOT_NONE
    dot_kind: str = "none"

    @property
    def row(self) -> tuple[str, str, str]:
        return (self.name, self.branch, self.dot)


def build_projects_frame(
    *,
    title: str,
    entries: list[ProjectEntry],
    selected: int,
    term_size: tuple[int, int],
    footer: str = "",
    start: int | None = None,
    viewport: int | None = None,
    colors: bool = False,
) -> str:
    """Render the project list: aligned name/branch/status columns in a
    box that hugs the content, degrading columns as the terminal narrows."""
    term_w, term_h = term_size
    cap = _inner_cap(term_w)
    if viewport is None:
        _, viewport = _window(len(entries), selected, _max_viewport(term_h))
    if start is None:
        start, _ = _window(len(entries), selected, _max_viewport(term_h))
    visible = entries[start : start + viewport]

    plan = plan_project_columns([e.row for e in visible], cap)
    rows: list[str] = []
    for i, entry in enumerate(visible):
        index = start + i
        line = render_project_row(entry.row, plan, selected=index == selected)
        if colors:
            line = line.replace(
                entry.dot, _sgr(entry.dot, _dot_code(entry.dot_kind), True)
            ) if entry.dot in line else line
            if index == selected:
                line = _sgr(line, _SGR_BRIGHT, True)
        rows.append(line)

    if footer:
        if len(entries) > viewport:
            footer = footer.replace("↑↓", f"↑↓ {selected + 1}/{len(entries)}", 1)
        footer = dim(footer, colors)
    return render_box(title, rows, footer=footer, width_cap=cap)


def _dot_code(kind: str) -> str:
    if kind == "clean":
        return _SGR_GREEN
    if kind == "dirty":
        return _SGR_YELLOW
    return _SGR_DIM


def build_list_frame(
    *,
    title: str,
    items: list[tuple[str, str]],
    selected: int,
    term_size: tuple[int, int],
    footer: str = "",
    start: int | None = None,
    viewport: int | None = None,
    colors: bool = False,
    warn_indexes: frozenset[int] = frozenset(),
) -> str:
    """Render a generic label+meta menu (providers, permission modes, …)."""
    term_w, term_h = term_size
    cap = _inner_cap(term_w)
    if viewport is None or start is None:
        start, viewport = _window(len(items), selected, _max_viewport(term_h))

    label_w = max((display_width(label) for label, _ in items), default=0)
    meta_w = max((display_width(meta) for _, meta in items), default=0)
    inner = 2 + label_w + (GAP + meta_w if meta_w else 0)
    inner = min(inner, cap)
    if meta_w and inner < 2 + label_w + GAP + 6:
        meta_w = 0  # metadata is secondary: hide it before labels get ugly

    rows: list[str] = []
    for i in range(start, min(start + viewport, len(items))):
        label, meta = items[i]
        label_cell = truncate(label, label_w)
        line = pad("›" if i == selected else " ", 1) + " " + pad(label_cell, label_w)
        if meta_w:
            line += " " * GAP + truncate(meta, meta_w)
        if i in warn_indexes:
            line = _sgr(line, _SGR_YELLOW, colors)
        elif i == selected:
            line = _sgr(line, _SGR_BRIGHT, colors)
        elif colors:
            line = dim(line)
        rows.append(line)

    footer = dim(footer, colors)
    return render_box(title, rows, footer=footer, width_cap=cap)


def build_detail_frame(
    *,
    project: Path,
    branch: str,
    dot: str,
    dot_kind: str,
    items: list[tuple[str, str]],
    selected: int,
    term_size: tuple[int, int],
    footer: str = "",
    colors: bool = False,
    remote: bool = False,
) -> str:
    """Render the project detail screen: branch + git status on the first
    line (status right-aligned), then the provider list including Auto."""
    term_w, _ = term_size
    cap = _inner_cap(term_w)

    label_w = max((display_width(label) for label, _ in items), default=0)
    meta_w = max((display_width(meta) for _, meta in items), default=0)
    body_inner = 2 + label_w + (GAP + meta_w if meta_w else 0)

    kind_label = {"clean": "clean", "dirty": "dirty"}.get(dot_kind, "非Git")
    status_text = f"{dot} {kind_label}"
    status_w = display_width(status_text)

    title = project.name + (" · SSH" if remote else "")

    # Line 1's natural content contributes to the box width; only a narrow
    # terminal shrinks the branch slot (2 indent + 2 gap before the status).
    natural_branch = branch or "·"
    inner = max(
        body_inner,
        display_width(natural_branch) + 2 + 2 + status_w,
        display_width(title) + 1,
    )
    inner = min(inner, cap)
    branch_cell = truncate(natural_branch, max(inner - status_w - 4, 0))

    line1 = pad("  " + branch_cell, inner - status_w) + status_text
    if colors:
        line1 = line1.replace(dot, _sgr(dot, _dot_code(dot_kind), True))

    rows = [line1, ""]
    for i, (label, meta) in enumerate(items):
        marker = "›" if i == selected else " "
        row = marker + " " + pad(truncate(label, label_w), label_w)
        if meta_w:
            row += " " * GAP + truncate(meta, max(meta_w, 6))
        if i == selected:
            row = _sgr(row, _SGR_BRIGHT, colors)
        elif colors:
            row = dim(row)
        rows.append(row)

    return render_box(
        title,
        [pad(r, inner) for r in rows],
        footer=dim(footer, colors),
        width_cap=cap,
    )


def build_input_frame(
    *,
    title: str,
    prompt: str,
    buffer: str,
    cursor: int,
    term_size: tuple[int, int],
    footer: str = "",
    colors: bool = False,
) -> str:
    """Render a single-line text input inside an adaptive box."""
    term_w, _ = term_size
    cap = _inner_cap(term_w)
    display = buffer[:cursor] + "▊" + buffer[cursor:]
    rows = [f"{prompt}: {display}"]
    return render_box(
        title,
        rows,
        footer=dim(footer, colors),
        width_cap=cap,
    )


# ---------------------------------------------------------------------------
# Screen loops
# ---------------------------------------------------------------------------


def _term_size() -> tuple[int, int]:
    size = shutil.get_terminal_size((80, 24))
    return max(size.columns, 20), max(size.lines, 8)


def _list_loop(
    term: RawTerm,
    *,
    title: str,
    items: list[tuple[str, str]],
    footer: str,
    selected: int = 0,
    warn_indexes: frozenset[int] = frozenset(),
) -> int | None:
    """Arrow-key menu over generic items; returns the chosen index."""
    colors = colors_enabled()
    while True:
        size = _term_size()
        start, viewport = _window(len(items), selected, _max_viewport(size[1]))
        frame = build_list_frame(
            title=title,
            items=items,
            selected=selected,
            term_size=size,
            footer=footer,
            start=start,
            viewport=viewport,
            colors=colors,
            warn_indexes=warn_indexes,
        )
        term.redraw(frame)
        key = term.read_key()
        if key in ("up", "k"):
            selected = max(selected - 1, 0)
        elif key in ("down", "j"):
            selected = min(selected + 1, len(items) - 1)
        elif key == "enter":
            return selected
        elif key == "tab":
            return None  # footer contract: Tab returns to the previous screen
        elif key in ("esc", "q", "eof"):
            return None


def _projects_loop(
    term: RawTerm,
    *,
    title: str,
    entries: list[ProjectEntry],
    footer: str,
    selected: int = 0,
    searchable: bool = True,
) -> ProjectEntry | str | None:
    """Project list with aligned columns, scroll viewport, and / search.

    Returns a ProjectEntry on Enter, 'actions' on Tab, or None on quit.
    """
    colors = colors_enabled()
    search = ""
    searching = False

    def matches(entry: ProjectEntry, query: str) -> bool:
        needle = query.casefold()
        return needle in entry.name.casefold() or needle in entry.branch.casefold()

    while True:
        visible = [e for e in entries if not search or matches(e, search)]
        if selected >= len(visible):
            selected = len(visible) - 1
        size = _term_size()
        start, viewport = _window(len(visible), selected, _max_viewport(size[1]))
        if searching:
            foot = f"搜索: {search}▊   Enter 打开  Esc 清除"
        else:
            foot = footer
        frame = build_projects_frame(
            title=title,
            entries=visible,
            selected=selected,
            term_size=size,
            footer=foot,
            start=start,
            viewport=viewport,
            colors=colors,
        )
        term.redraw(frame)
        key = term.read_key()
        if searching:
            if key == "backspace":
                search = search[:-1]
                selected = 0
            elif key == "esc":
                searching, search = False, ""
            elif key in ("up", "k") and visible:
                selected = max(selected - 1, 0)
            elif key in ("down", "j") and visible:
                selected = min(selected + 1, len(visible) - 1)
            elif key == "enter" and visible:
                return visible[selected]
            elif key == "eof":
                return None
            elif len(key) == 1 and key.isprintable():
                search += key
                selected = 0
            continue
        if key in ("up", "k"):
            selected = max(selected - 1, 0)
        elif key in ("down", "j"):
            selected = min(selected + 1, len(visible) - 1)
        elif key == "enter" and visible:
            return visible[selected]
        elif key == "tab":
            return MENU_ACTIONS
        elif key == "/" and searchable:
            searching, search, selected = True, "", 0
        elif key in ("esc", "q", "eof"):
            return None


def _line_input(
    term: RawTerm,
    *,
    title: str,
    prompt: str,
    initial: str = "",
    footer: str = "Enter 确认  Esc 取消",
) -> str | None:
    """Single-line text input with cursor editing (UTF-8/CJK safe)."""
    colors = colors_enabled()
    buffer, cursor = initial, len(initial)
    while True:
        frame = build_input_frame(
            title=title,
            prompt=prompt,
            buffer=buffer,
            cursor=cursor,
            term_size=_term_size(),
            footer=footer,
            colors=colors,
        )
        term.redraw(frame)
        key = term.read_key()
        if key == "enter":
            return buffer
        if key in ("esc", "eof"):
            return None
        if key == "backspace":
            if cursor > 0:
                buffer = buffer[: cursor - 1] + buffer[cursor:]
                cursor -= 1
        elif key == "left":
            cursor = max(cursor - 1, 0)
        elif key == "right":
            cursor = min(cursor + 1, len(buffer))
        elif key == "home":
            cursor = 0
        elif len(key) == 1 and key.isprintable():
            buffer = buffer[:cursor] + key + buffer[cursor:]
            cursor += 1


# ---------------------------------------------------------------------------
# Screen flows
# ---------------------------------------------------------------------------


def _project_entries(paths: list[Path]) -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []
    for path in paths:
        branch, dot, kind = git_info(path)
        entries.append(
            ProjectEntry(
                path=path,
                name=path.name,
                branch=branch,
                dot=dot,
                dot_kind=kind,
            )
        )
    return entries


def _list_projects() -> list[ProjectEntry]:
    if not launcher.PROJECTS_ROOT.is_dir():
        return []
    dirs: list[Path] = []
    for d in sorted(launcher.PROJECTS_ROOT.iterdir()):
        if not d.is_dir():
            continue
        if d.name.startswith("_") or d.name.startswith("."):
            continue
        if launcher.is_timestamp_session_dir(d.name):
            continue
        if d.name == "_recovery-review":
            continue
        if launcher.project_picker_group(d.name) != "primary":
            continue
        if launcher.has_git(d):
            dirs.insert(0, d)
        else:
            dirs.append(d)
    return _project_entries(dirs)


def _create_project_dir(name: str) -> Path | None:
    target = launcher.PROJECTS_ROOT / name
    if target.is_dir():
        return target
    try:
        target.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "-C", str(target), "init"], capture_output=True, timeout=10
        )
    except OSError:
        return None
    return target


def _ask_project_name(term: RawTerm) -> Path | None:
    """Prompt for a new project name with the same safety rules as the
    prompt flow (no separators, no traversal), then create it."""
    while True:
        name = _line_input(term, title="CC · 新建项目", prompt="名称")
        if name is None:
            return None
        name = name.strip()
        if not name:
            continue
        if "/" in name or ".." in name or name.startswith("~"):
            _list_loop(
                term,
                title="CC · 新建项目",
                items=[("名称不能包含路径分隔符或特殊字符", "按 Enter 返回")],
                footer="Enter 返回",
            )
            continue
        target = _create_project_dir(name)
        if target is None:
            _list_loop(
                term,
                title="CC · 新建项目",
                items=[("项目创建失败", "按 Enter 返回")],
                footer="Enter 返回",
            )
            continue
        return target


def _ask_manual_path(term: RawTerm) -> Path | None:
    """Prompt for a project path (~ expands), validated to be a directory."""
    while True:
        raw = _line_input(term, title="CC · 手动路径", prompt="路径")
        if raw is None:
            return None
        p = Path(raw.replace("~", str(Path.home()))).resolve()
        if p.is_dir():
            return p
        _list_loop(
            term,
            title="CC · 手动路径",
            items=[("路径不存在或不是目录", str(p))],
            footer="Enter 返回",
        )


def projects_screen(term: RawTerm) -> Path | None:
    """Main project picker: list + actions overlay (recent/manual/create)."""
    selected = 0
    while True:
        entries = _list_projects()
        if not entries:
            action = _list_loop(
                term,
                title="CC · Projects",
                items=[
                    ("当前目录", str(Path.cwd())),
                    ("在 ~/Projects 新建项目", ""),
                    ("手动输入项目路径", ""),
                    ("退出", ""),
                ],
                footer="↑↓  Enter 确认  q 退出",
            )
            if action is None:
                return None
            if action == 0:
                return Path.cwd()
            if action == 1:
                target = _ask_project_name(term)
                if target is None:
                    continue
                return target
            if action == 2:
                path = _ask_manual_path(term)
                if path is not None:
                    return path
                continue
            return None

        result = _projects_loop(
            term,
            title="CC · Projects",
            entries=entries,
            footer="↑↓ 选择  Enter 打开  / 搜索  Tab 更多  q 退出",
            selected=selected,
        )
        if result is None:
            return None
        if isinstance(result, ProjectEntry):
            return result.path
        # actions overlay
        action = _list_loop(
            term,
            title="CC · 更多操作",
            items=[
                ("当前目录", str(Path.cwd())),
                ("最近项目", ""),
                ("在 ~/Projects 新建项目", ""),
                ("手动输入项目路径", ""),
                ("返回项目列表", ""),
            ],
            footer="↑↓  Enter 确认  q 返回",
        )
        if action is None:
            continue
        if action == 0:
            return Path.cwd()
        if action == 1:
            recent = [Path(p) for p in launcher.recent_entries() if Path(p).is_dir()]
            if not recent:
                continue
            pick = _projects_loop(
                term,
                title="CC · 最近项目",
                entries=_project_entries(recent),
                footer="↑↓ 选择  Enter 打开  / 搜索  q 返回",
            )
            if isinstance(pick, ProjectEntry):
                return pick.path
            continue
        if action == 2:
            target = _ask_project_name(term)
            if target is None:
                continue
            return target
        if action == 3:
            path = _ask_manual_path(term)
            if path is not None:
                return path
            continue
        # 返回项目列表
        continue


def git_init_screen(term: RawTerm, project: Path) -> str | None:
    """Ask how to handle a non-git directory.  Returns
    'init', 'open', 'back', or None (quit)."""
    choice = _list_loop(
        term,
        title=f"{project.name} · 非 Git 目录",
        items=[
            ("初始化 Git 后打开", f"{project}"),
            ("直接打开，不初始化 Git", f"{project}"),
            ("返回项目列表", ""),
            ("退出", ""),
        ],
        footer="↑↓  Enter 确认  q 退出",
    )
    if choice is None:
        return None
    return ("init", "open", "back", "quit")[choice]


def _provider_items(avail: dict[str, bool]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for key in _PROVIDER_ORDER:
        label = PROVIDER_LABELS[key]
        if not avail.get(key):
            items.append((label, "不可用"))
        else:
            items.append((label, ""))
    return items


def permission_screen(term: RawTerm, project: Path, provider: str) -> dict | None:
    """Permission/profile selection for one provider.  Returns a launch
    config dict, or None to go back."""
    if provider in (PROVIDER_CLAUDE, PROVIDER_DEEPSEEK):
        labels = _CLAUDE_MODE_LABELS
        order = ["m", "e", "p", "a", "b"]
    else:
        labels = _CODEX_MODE_LABELS
        order = ["m", "p", "a", "b"]
    items = [(labels[k][0], labels[k][1]) for k in order]
    title = f"{project.name} · {PROVIDER_LABELS[provider]}"
    index = _list_loop(
        term,
        title=title,
        items=items,
        footer="↑↓ 选择  Enter 启动  Tab 返回  q 返回",
        warn_indexes=frozenset(i for i, k in enumerate(order) if k == "b"),
    )
    if index is None:
        return None
    mode_key = order[index]
    if provider == PROVIDER_CODEX:
        cfg = CODEX_PROFILES[mode_key]
        return {
            "provider": provider,
            "mode": mode_key,
            "profile": cfg["profile"],
            "is_full": cfg["is_full"],
        }
    cfg = CLAUDE_PERMISSION_MODES[mode_key]
    return {
        "provider": provider,
        "mode": mode_key,
        "perm_mode": cfg["mode"],
        "bypass": cfg["bypass"],
    }


def detail_screen(term: RawTerm, project: Path) -> dict | str | None:
    """Provider selection after a project is chosen.  Returns a launch
    config dict, MENU_BACK to re-pick a project, or None to quit."""
    avail = provider_availability()
    auto_provider, auto_mode = resolve_auto(project)
    branch, dot, kind = git_info(project)
    selected = 0
    while True:
        auto_labels = (
            _CODEX_MODE_LABELS
            if auto_provider == PROVIDER_CODEX
            else _CLAUDE_MODE_LABELS
        )
        if avail.get(auto_provider):
            auto_meta = f"{PROVIDER_LABELS[auto_provider]} · {auto_labels[auto_mode][0]}"
        else:
            auto_meta = "未检测到可用工具"
        items = [("Auto", auto_meta)] + _provider_items(avail)
        frame = build_detail_frame(
            project=project,
            branch=branch,
            dot=dot,
            dot_kind=kind,
            items=items,
            selected=selected,
            term_size=_term_size(),
            footer="↑↓ 选择  Enter 启动  Tab 项目  q 退出",
            colors=colors_enabled(),
            remote=launcher._is_remote,
        )
        term.redraw(frame)
        key = term.read_key()
        if key in ("up", "k"):
            selected = max(selected - 1, 0)
        elif key in ("down", "j"):
            selected = min(selected + 1, len(items) - 1)
        elif key == "enter":
            if selected == 0:
                if not avail.get(auto_provider):
                    continue
                # Bypass/full-access never auto-launches: ask explicitly.
                if auto_mode == "b" or (
                    auto_provider == PROVIDER_CODEX
                    and CODEX_PROFILES[auto_mode]["is_full"]
                ):
                    cfg = permission_screen(term, project, auto_provider)
                    if cfg is not None:
                        return cfg
                    continue
                return _launch_cfg(auto_provider, auto_mode)
            provider = _PROVIDER_ORDER[selected - 1]
            if not avail.get(provider):
                continue
            cfg = permission_screen(term, project, provider)
            if cfg is not None:
                return cfg
            continue
        elif key == "tab":
            return MENU_BACK
        elif key in ("esc", "q", "eof"):
            return None


def _launch_cfg(provider: str, mode: str) -> dict:
    """Build the launch config for a resolved (provider, mode) pair."""
    if provider == PROVIDER_CODEX:
        profile = CODEX_PROFILES[mode]
        return {
            "provider": provider,
            "mode": mode,
            "profile": profile["profile"],
            "is_full": profile["is_full"],
        }
    profile = CLAUDE_PERMISSION_MODES[mode]
    return {
        "provider": provider,
        "mode": mode,
        "perm_mode": profile["mode"],
        "bypass": profile["bypass"],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def tui_main() -> int:
    """Run the adaptive interactive launcher.  Only called when stdin and
    stdout are TTYs (see launcher.main)."""
    term = RawTerm()
    project: Path | None = launcher._fast_determine_project()
    try:
        term.enter()
        while True:
            if project is None:
                project = projects_screen(term)
                if project is None:
                    return 0
            launcher.add_to_recent(project)

            if not launcher.has_git(project):
                action = git_init_screen(term, project)
                if action in (None, "quit"):
                    return 0
                if action == "back":
                    project = None
                    continue
                if action == "init":
                    subprocess.run(
                        ["git", "-C", str(project), "init"],
                        capture_output=True,
                        timeout=10,
                    )
                git_info(project, refresh=True)

            cfg = detail_screen(term, project)
            if cfg is None:
                return 0
            if cfg == MENU_BACK:
                project = None
                continue

            term.exit()
            # Everything below runs with the terminal restored.
            if cfg["provider"] == PROVIDER_CODEX:
                if not launcher._codex_preflight(project, cfg["profile"]):
                    term.enter()
                    retry = _list_loop(
                        term,
                        title="Codex 启动前检查失败",
                        items=[
                            ("返回项目", str(project)),
                            ("退出", ""),
                        ],
                        footer="↑↓  Enter 确认  q 退出",
                    )
                    if retry == 0:
                        continue
                    return 0
                if cfg["is_full"] and not launcher._confirm_remote(
                    "Codex danger-full-access"
                ):
                    return 1
                _record_launch(project, PROVIDER_CODEX, cfg["mode"])
                return launcher._launch_codex(project, cfg["profile"])

            provider_name = (
                "deepseek" if cfg["provider"] == PROVIDER_DEEPSEEK else "claude"
            )
            if cfg["bypass"] and not launcher._confirm_remote(
                "Claude/DeepSeek bypassPermissions"
            ):
                return 1
            _record_launch(project, cfg["provider"], cfg["mode"])
            return launcher._launch_claude(
                project, provider_name, cfg["perm_mode"], cfg["bypass"]
            )
    except KeyboardInterrupt:
        return 0
    finally:
        term.exit()


def is_tui_session() -> bool:
    """True when the adaptive TUI should run instead of the prompt flow."""
    if os.environ.get("_CC_PLAIN") == "1":
        return False
    return sys.stdin.isatty() and sys.stdout.isatty() and termios is not None
