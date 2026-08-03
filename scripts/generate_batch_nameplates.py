#!/usr/bin/env python3
"""Generate editable one-up and two-up nameplate decks from a CSV name list."""

import argparse
import csv
import re
from pathlib import Path

try:
    import uno
    from com.sun.star.awt import Point, Size
except ModuleNotFoundError:  # Allows pure helpers and tests without LibreOffice.
    uno = None
    Point = Size = None


MM100 = 100
WINE = 0x850D22
GOLD = 0xB8955A
BLACK = 0x141414
GRAY = 0x555555
SERIF = "Noto Serif CJK SC"
SANS = "Noto Sans CJK SC"


def mm(value):
    return int(round(value * MM100))


def safe_stem(value):
    """Return a readable filename component without path separators."""
    stem = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", "-", value).strip(" .-")
    return stem or "nameplates"


def property_value(name, value):
    if uno is None:
        raise RuntimeError("LibreOffice PyUNO is required to generate PowerPoint files")
    item = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
    item.Name = name
    item.Value = value
    return item


def set_text_style(shape, font, size_pt, color, bold=False, align=0):
    cursor = shape.getText().createTextCursor()
    cursor.gotoEnd(True)
    cursor.CharFontName = font
    cursor.CharFontNameAsian = font
    cursor.CharHeight = float(size_pt)
    cursor.CharHeightAsian = float(size_pt)
    cursor.CharColor = color
    cursor.CharWeight = 150.0 if bold else 100.0
    cursor.CharWeightAsian = 150.0 if bold else 100.0
    cursor.ParaAdjust = align


class Deck:
    def __init__(self, desktop, width_mm, height_mm):
        self.doc = desktop.loadComponentFromURL(
            "private:factory/simpress", "_blank", 0, ()
        )
        self.pages = self.doc.getDrawPages()
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.solid = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
        self.no_fill = uno.Enum("com.sun.star.drawing.FillStyle", "NONE")
        self.no_line = uno.Enum("com.sun.star.drawing.LineStyle", "NONE")
        self.solid_line = uno.Enum("com.sun.star.drawing.LineStyle", "SOLID")

    def page(self, index):
        if index == 0:
            page = self.pages.getByIndex(0)
        else:
            page = self.pages.insertNewByIndex(index)
        page.Width = mm(self.width_mm)
        page.Height = mm(self.height_mm)
        return page

    def rect(self, page, x, y, w, h, fill, line=None, line_width=0.2):
        shape = self.doc.createInstance("com.sun.star.drawing.RectangleShape")
        shape.Position = Point(mm(x), mm(y))
        shape.Size = Size(mm(w), mm(h))
        shape.FillStyle = self.solid if fill is not None else self.no_fill
        if fill is not None:
            shape.FillColor = fill
        shape.LineStyle = self.solid_line if line is not None else self.no_line
        if line is not None:
            shape.LineColor = line
            shape.LineWidth = mm(line_width)
        page.add(shape)

    def text(self, page, x, y, w, h, value, font, size_pt, color,
             bold=False, align=0, rotation=0):
        shape = self.doc.createInstance("com.sun.star.drawing.TextShape")
        shape.Position = Point(mm(x), mm(y))
        shape.Size = Size(mm(w), mm(h))
        shape.FillStyle = self.no_fill
        shape.LineStyle = self.no_line
        shape.TextAutoGrowHeight = False
        shape.TextAutoGrowWidth = False
        shape.TextVerticalAdjust = uno.Enum(
            "com.sun.star.drawing.TextVerticalAdjust", "CENTER"
        )
        shape.RotateAngle = int(rotation * 100)
        page.add(shape)
        shape.String = value
        set_text_style(shape, font, size_pt, color, bold=bold, align=align)

    def line(self, page, x1, y1, x2, y2, color=0x777777, width=0.2):
        shape = self.doc.createInstance("com.sun.star.drawing.LineShape")
        shape.Position = Point(mm(x1), mm(y1))
        shape.Size = Size(mm(x2 - x1), mm(y2 - y1))
        shape.LineStyle = self.solid_line
        shape.LineColor = color
        shape.LineWidth = mm(width)
        page.add(shape)

    def save(self, output_path):
        output = Path(output_path).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        self.doc.storeAsURL(
            uno.systemPathToFileUrl(str(output)),
            (
                property_value("FilterName", "Impress MS PowerPoint 2007 XML"),
                property_value("Overwrite", True),
            ),
        )
        self.doc.close(True)


def name_size(name):
    if len(name) <= 2:
        return 68.0
    if len(name) == 3:
        return 61.0
    return 52.0


def add_card(deck, page, x, y, name, class_label, organization_label,
             english_label,
             include_instructions=False):
    width = 148.5
    deck.rect(page, x, y, width, 210, 0xFFFFFF, line=0x222222,
              line_width=0.25)
    deck.rect(page, x, y, width, 17, WINE)
    deck.rect(page, x, y + 17, width, 0.6, GOLD)
    deck.rect(page, x, y + 123, width, 0.6, GOLD)
    deck.rect(page, x, y + 123.6, width, 16.4, WINE)

    # Upper display face: upside down in the flat file, upright after folding.
    deck.text(page, x + 58, y + 12.5, 50, 10, class_label,
              SERIF, 13.5, 0xFFFFFF, bold=True, rotation=180)
    deck.text(page, x + 140.5, y + 11, 50, 8, english_label,
              SANS, 9.0, 0xE6CFAA, align=2, rotation=180)
    deck.text(page, x + 119.5, y + 50, 90.5, 27, name,
              SERIF, name_size(name), BLACK, bold=True, align=3,
              rotation=180)
    deck.text(page, x + 140.5, y + 60, 69.5, 8,
              organization_label, SANS, 9.2, 0x781126,
              bold=True, align=2, rotation=180)

    # Lower display face: upright in the flat file.
    face_y = y + 70
    deck.text(page, x + 8, face_y + 3.5, 80, 8,
              organization_label, SANS, 9.2, 0x781126,
              bold=True)
    deck.text(page, x + 28, face_y + 22, 92.5, 27, name,
              SERIF, name_size(name), BLACK, bold=True, align=3)
    deck.text(page, x + 8, face_y + 55, 45, 8, english_label,
              SANS, 9.0, 0xE6CFAA)
    deck.text(page, x + 78, face_y + 54.5, 62.5, 9, class_label,
              SERIF, 13.5, 0xFFFFFF, bold=True, align=2)

    for score_y in (y + 70, y + 140):
        score_x = x
        while score_x < x + width:
            deck.line(page, score_x, score_y,
                      min(score_x + 2.2, x + width), score_y)
            score_x += 3.8

    if include_instructions:
        deck.text(page, 35, 260, 140, 7,
                  "实线裁切 · 虚线压痕后折叠 · 按 100% / 实际大小打印",
                  SANS, 8.8, GRAY, align=3)
        deck.text(page, 35, 266, 140, 7,
                  "展开 148.5 × 210 mm；三面各 70 mm",
                  SANS, 8.8, GRAY, align=3)


def connect():
    if uno is None:
        raise RuntimeError(
            "LibreOffice PyUNO is unavailable; install the distro's LibreOffice Python bindings"
        )
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_ctx
    )
    ctx = resolver.resolve(
        "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
    )
    return ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", ctx
    )


def read_names(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if rows and "姓名" not in rows[0]:
        raise ValueError("CSV must contain a 姓名 column")
    return [row["姓名"].strip() for row in rows if row["姓名"].strip()]


def main(csv_path, output_dir, class_label, organization_label, english_label):
    names = read_names(csv_path)
    if not names:
        raise SystemExit("name list is empty")
    output_dir = Path(output_dir)
    count = len(names)
    desktop = connect()

    one_up = Deck(desktop, 210, 297)
    for index, name in enumerate(names):
        page = one_up.page(index)
        add_card(
            one_up, page, 30.75, 43.5, name, class_label,
            organization_label, english_label,
            include_instructions=True,
        )
    label_stem = safe_stem(class_label)
    one_up.save(
        output_dir / f"{label_stem}_姓名牌_{count}人_单个版_可编辑.pptx"
    )

    two_up = Deck(desktop, 297, 210)
    for page_index in range((len(names) + 1) // 2):
        page = two_up.page(page_index)
        first = page_index * 2
        add_card(
            two_up, page, 0, 0, names[first], class_label,
            organization_label, english_label,
        )
        if first + 1 < len(names):
            add_card(
                two_up, page, 148.5, 0, names[first + 1], class_label,
                organization_label, english_label,
            )
    two_up.save(
        output_dir / f"{label_stem}_姓名牌_{count}人_两拼版_可编辑.pptx"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="CSV containing a 姓名 column")
    parser.add_argument("output_dir", help="directory for generated files")
    parser.add_argument(
        "--class-label",
        default="示例班级",
        help="class or group text printed on each card",
    )
    parser.add_argument(
        "--organization-label",
        default="示例活动",
        help="organization or event text printed on each card",
    )
    parser.add_argument(
        "--english-label",
        default="WELCOME",
        help="short English label printed on each card",
    )
    args = parser.parse_args()
    main(
        args.csv_path,
        args.output_dir,
        args.class_label,
        args.organization_label,
        args.english_label,
    )
