"""Content-aware adaptive layout engine for the ``cc`` launcher UI.

Design principle: never fit content into a fixed box.  Measure content
first, choose columns, then calculate width/height, align, and render.

    content
    → measure
    → choose columns
    → choose visible metadata
    → calculate width/height
    → align
    → render

Everything here is pure (no terminal I/O) so the same code path renders
mockups, tests, and the live TUI.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Display width (terminal cell semantics, CJK-aware)
# ---------------------------------------------------------------------------

_SGR_RE = re.compile(r"\x1b\[[0-9;:]*m")

# Code points that occupy zero terminal cells.
_ZERO_WIDTH_RANGES = (
    (0x00AD, 0x00AD),  # soft hyphen
    (0x0300, 0x036F),  # combining diacritics
    (0x0483, 0x0489),  # combining Cyrillic
    (0x0591, 0x05BD),  # combining Hebrew
    (0x0610, 0x061A),  # combining Arabic
    (0x064B, 0x065F),  # combining Arabic
    (0x0670, 0x0670),
    (0x06D6, 0x06ED),  # combining Arabic
    (0x07EB, 0x07F3),  # combining NKo
    (0x0E31, 0x0E31),  # combining Thai
    (0x0E34, 0x0E3A),
    (0x0E47, 0x0E4E),
    (0x0EB1, 0x0EB9),  # combining Lao
    (0x0EBB, 0x0EBC),
    (0x0EC8, 0x0ECD),
    (0x1039, 0x103A),  # combining Myanmar
    (0x1160, 0x11FF),  # Hangul jungseong/jongseong
    (0x135D, 0x135F),  # combining Ethiopic
    (0x1AB0, 0x1AFF),  # combining marks ext.
    (0x1DC0, 0x1DFF),  # combining marks supp.
    (0x200B, 0x200F),  # ZWSP, ZWNJ, ZWJ, LRM, RLM
    (0x202A, 0x202E),  # bidi controls
    (0x2060, 0x2064),  # WJ, invisible operators
    (0x20D0, 0x20FF),  # combining marks for symbols
    (0xFE00, 0xFE0F),  # variation selectors
    (0xFE20, 0xFE2F),  # combining half marks
    (0xFEFF, 0xFEFF),  # BOM / ZWNBSP
    (0xE0100, 0xE01EF),  # variation selectors supp.
)

# Code points that occupy two terminal cells (East Asian Wide/Fullwidth,
# emoji, CJK).
_WIDE_RANGES = (
    (0x1100, 0x115F),  # Hangul Jamo
    (0x2329, 0x232A),  # angle brackets
    (0x2E80, 0x303E),  # CJK radicals .. CJK symbols and punctuation
    (0x3041, 0x33FF),  # Hiragana .. CJK compatibility
    (0x3400, 0x4DBF),  # CJK Ext A
    (0x4E00, 0x9FFF),  # CJK unified ideographs
    (0xA000, 0xA4CF),  # Yi syllables
    (0xA960, 0xA97F),  # Hangul Jamo Ext A
    (0xAC00, 0xD7A3),  # Hangul syllables
    (0xF900, 0xFAFF),  # CJK compatibility ideographs
    (0xFE10, 0xFE19),  # vertical forms
    (0xFE30, 0xFE6F),  # CJK compatibility forms
    (0xFF00, 0xFF60),  # fullwidth forms
    (0xFFE0, 0xFFE6),  # fullwidth signs
    (0x1F300, 0x1F64F),  # emoji: misc symbols and pictographs
    (0x1F680, 0x1F6FF),  # emoji: transport
    (0x1F900, 0x1F9FF),  # emoji: supplemental symbols
    (0x20000, 0x2FFFD),  # CJK Ext B+
    (0x30000, 0x3FFFD),  # CJK Ext G+
)


def _in_ranges(cp: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    index = bisect.bisect_right(ranges, (cp, 0x10FFFF))
    if index == 0:
        return False
    lo, hi = ranges[index - 1]
    return lo <= cp <= hi


def char_width(ch: str) -> int:
    """Terminal cell width of a single character (wide → 2, combining → 0)."""
    if not ch:
        return 0
    cp = ord(ch)
    if cp < 0x20 or cp == 0x7F:
        return 0
    if _in_ranges(cp, _ZERO_WIDTH_RANGES):
        return 0
    if _in_ranges(cp, _WIDE_RANGES):
        return 2
    return 1


def display_width(text: str) -> int:
    """Display width of a string in terminal cells.

    ANSI SGR sequences are ignored, so coloured text measures the same as
    plain text.  CJK/emoji count as 2 cells; combining marks count as 0.
    """
    return sum(char_width(ch) for ch in _SGR_RE.sub("", text))


# ---------------------------------------------------------------------------
# Truncation and padding (by display width, never byte length)
# ---------------------------------------------------------------------------

_ELLIPSIS = "…"


def truncate(text: str, width: int, ellipsis: str = _ELLIPSIS) -> str:
    """Truncate ``text`` to at most ``width`` cells, appending an ellipsis.

    Returns the original string unchanged when it already fits.
    """
    if width < 0:
        raise ValueError("truncate width must be >= 0")
    if display_width(text) <= width:
        return text
    if width == 0:
        return ""
    if display_width(ellipsis) > width:
        return ""
    budget = width - display_width(ellipsis)
    out: list[str] = []
    used = 0
    for ch in text:
        w = char_width(ch)
        if w == 0:
            out.append(ch)  # keep zero-width marks attached to their glyph
            continue
        if used + w > budget:
            break
        out.append(ch)
        used += w
    return "".join(out) + ellipsis


def pad(text: str, width: int, align: str = "left", fill: str = " ") -> str:
    """Pad ``text`` to exactly ``width`` cells using display-width semantics."""
    current = display_width(text)
    if current >= width:
        return text
    gap = width - current
    if align == "right":
        return fill * gap + text
    if align == "center":
        left = gap // 2
        return fill * left + text + fill * (gap - left)
    return text + fill * gap


# ---------------------------------------------------------------------------
# Column planning (choose columns and visible metadata from content + space)
# ---------------------------------------------------------------------------

MARKER_SELECTED = "›"
MARKER_PLAIN = " "
MARKER_WIDTH = 2  # marker glyph + one space

GAP = 2  # cells between columns
STATUS_WIDTH = 1  # fixed status cell (e.g. ●)
MIN_BRANCH_WIDTH = 6  # below this, a truncated branch column is useless


@dataclass(frozen=True)
class ColumnPlan:
    """How the project-list columns are laid out for a given space budget."""

    marker_width: int
    name_width: int
    branch_width: int  # 0 → branch column hidden
    show_status: bool
    inner_width: int

    def branch_visible(self) -> bool:
        return self.branch_width > 0


def plan_project_columns(
    rows: list[tuple[str, str, str]],
    available_inner: int,
    *,
    gap: int = GAP,
    status_width: int = STATUS_WIDTH,
    marker_width: int = MARKER_WIDTH,
    min_branch_width: int = MIN_BRANCH_WIDTH,
) -> ColumnPlan:
    """Choose column widths for (name, branch, status) rows.

    Degradation tiers, in order, when space runs out:

    1. full:    name + branch + status
    2. medium:  name + truncated branch + status
    3. narrow:  name + status
    4. tiny:    name only (names truncated as a last resort)

    ``available_inner`` is the cap in cells for content inside the box.
    """
    available_inner = max(available_inner, marker_width)
    name_width = max((display_width(r[0]) for r in rows), default=0)
    branch_width = max((display_width(r[1]) for r in rows if r[1]), default=0)
    show_status = any(r[2] for r in rows)

    def inner_with(branch_w: int, status: bool) -> int:
        total = marker_width + name_width
        if branch_w:
            total += gap + branch_w
        if status:
            total += gap + status_width
        return total

    full = inner_with(branch_width, show_status)
    if full <= available_inner:
        return ColumnPlan(marker_width, name_width, branch_width, show_status, full)

    # Tier 2: keep branch but truncate it.
    if branch_width:
        spare = available_inner - marker_width - name_width - gap
        if show_status:
            spare -= gap + status_width
        if spare >= min_branch_width:
            return ColumnPlan(
                marker_width, name_width, spare, show_status, available_inner
            )

    # Tier 3: drop branch.
    narrow = inner_with(0, show_status)
    if narrow <= available_inner:
        return ColumnPlan(marker_width, name_width, 0, show_status, narrow)

    # Tier 4: status is secondary information — hide it before names get ugly.
    tiny = inner_with(0, False)
    if tiny <= available_inner:
        return ColumnPlan(marker_width, name_width, 0, False, tiny)

    # Even names don't fit: truncate them.
    final_name = max(available_inner - marker_width, 1)
    return ColumnPlan(marker_width, final_name, 0, False, available_inner)


def render_project_row(
    row: tuple[str, str, str],
    plan: ColumnPlan,
    *,
    selected: bool = False,
) -> str:
    """Render one (name, branch, status) row under ``plan``, cell-aligned."""
    name, branch, status = row
    marker = MARKER_SELECTED if selected else MARKER_PLAIN
    cells = [marker + " " + pad(truncate(name, plan.name_width), plan.name_width)]
    if plan.branch_visible():
        branch_cell = truncate(branch, plan.branch_width) if branch else ""
        cells.append(pad(branch_cell, plan.branch_width))
    if plan.show_status:
        cells.append(status if status else " ")
    return (" " * GAP).join(cells) if len(cells) > 1 else cells[0]


# ---------------------------------------------------------------------------
# Box renderer (width = content, never a fixed frame)
# ---------------------------------------------------------------------------

def _border_line(left: str, title: str, inner: int, right: str) -> str:
    # ╭─ {title} ───────╮  — the space after the title guarantees the line
    # matches the rows exactly (title + space + fill == inner).
    fill = inner - display_width(title) - 1
    return left + " " + title + " " + ("─" * fill if fill > 0 else "") + right


def render_box(
    title: str,
    rows: list[str],
    *,
    footer: str = "",
    min_width: int = 16,
    width_cap: int | None = None,
) -> str:
    """Render a rounded box sized to its content.

    ``rows`` are pre-aligned content lines (all equal display width, or the
    box pads the rest).  The box width is ``min(content, width_cap)``;
    ``title`` and ``footer`` are truncated rather than allowed to overflow.
    """
    if width_cap is not None:
        title = truncate(title, max(width_cap - 2, 0))
    inner = max([display_width(r) for r in rows] + [display_width(title) + 1])
    inner = max(inner, min_width)
    if width_cap is not None:
        inner = min(inner, width_cap)

    lines = [_border_line("╭─", title, inner, "╮")]
    for row in rows:
        lines.append("│ " + pad(truncate(row, inner), inner) + " │")
    lines.append("╰" + "─" * (inner + 2) + "╯")
    if footer:
        lines.append(truncate(footer, width_cap or display_width(footer)))
    return "\n".join(lines)
