"""Generate a realistic multi-page engineering PDF to exercise the parser.

Pages: cover, table of contents, technical description, regulations,
a vector drawing, and an equipment specification table (mixed RU/EN headers
plus a multiline/continuation row and a duplicate row).
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.flowables import Flowable

FONT = "DejaVuSans"
FONT_B = "DejaVuSans-Bold"
pdfmetrics.registerFont(TTFont(FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(
    TTFont(FONT_B, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
)


class Drawing(Flowable):
    """A fake mechanical drawing: many vector lines, little text."""

    def __init__(self, w=170 * mm, h=200 * mm):
        super().__init__()
        self.width, self.height = w, h

    def draw(self):
        c = self.canv
        c.setLineWidth(0.6)
        # grid
        for x in range(0, int(self.width), 8 * mm.__int__() if False else 20):
            c.line(x, 0, x, self.height)
        for y in range(0, int(self.height), 20):
            c.line(0, y, self.width, y)
        # some "machine" geometry
        c.setLineWidth(1.5)
        c.rect(30, 40, 110 * mm.__int__() if False else 300, 250)
        c.circle(180, 165, 70)
        c.circle(180, 165, 40)
        for ang in range(0, 360, 30):
            import math
            x = 180 + 70 * math.cos(math.radians(ang))
            y = 165 + 70 * math.sin(math.radians(ang))
            c.line(180, 165, x, y)
        c.line(0, 0, self.width, self.height)
        c.line(0, self.height, self.width, 0)


def build(path="sample_engineering.pdf"):
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["Normal"], fontName=FONT, fontSize=10,
                          leading=14)
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontName=FONT_B, fontSize=22)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=FONT_B, fontSize=14)

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=20 * mm)
    story = []

    # --- Page 1: cover ---
    story += [Spacer(1, 60 * mm),
              Paragraph("ПРОЕКТНАЯ ДОКУМЕНТАЦИЯ", h1),
              Spacer(1, 8 * mm),
              Paragraph("Система отопления и вентиляции<br/>Объект: БЦ «Меридиан»", h2),
              Spacer(1, 40 * mm),
              Paragraph("Заказчик: ООО «СтройИнвест» · 2026 г.", body),
              PageBreak()]

    # --- Page 2: table of contents ---
    story += [Paragraph("Содержание", h2), Spacer(1, 6 * mm)]
    toc = [
        "1. Техническое описание .......................................... 3",
        "2. Нормативные требования ..................................... 4",
        "3. Чертёж узла ..................................................... 5",
        "4. Спецификация оборудования ............................... 6",
    ]
    for line in toc:
        story.append(Paragraph(line, body))
    story.append(PageBreak())

    # --- Page 3: technical description (prose, no table) ---
    story += [Paragraph("1. Техническое описание", h2), Spacer(1, 4 * mm)]
    para = ("Настоящий раздел содержит пояснительную записку и общие сведения о "
            "проектируемой системе отопления и вентиляции. Назначение системы — "
            "поддержание нормируемых параметров микроклимата. " * 6)
    story += [Paragraph(para, body), PageBreak()]

    # --- Page 4: regulations ---
    story += [Paragraph("2. Нормативные требования", h2), Spacer(1, 4 * mm)]
    reg = ("Проектирование выполнено в соответствии с ГОСТ 30494-2011, "
           "СНиП 41-01-2003 и СП 60.13330. Стандарт ISO 9001 применяется к "
           "системе менеджмента качества. Требования пожарной безопасности "
           "согласно нормативным документам. " * 4)
    story += [Paragraph(reg, body), PageBreak()]

    # --- Page 5: drawing ---
    story += [Paragraph("3. Чертёж узла (план)", h2), Spacer(1, 4 * mm),
              Drawing(), PageBreak()]

    # --- Page 6: equipment specification table (mixed RU/EN headers) ---
    story += [Paragraph("4. Спецификация оборудования", h2), Spacer(1, 4 * mm)]
    data = [
        ["№", "Артикул", "Наименование", "Описание", "Кол-во", "Ед.", "Price"],
        ["1", "GR-25-60", "Насос циркуляционный Grundfos UPS 25-60",
         "230В, 1ф", "3", "шт", "18000"],
        ["", "", "класс энергоэфф. A", "", "", "", ""],   # continuation row
        ["2", "BV-DN50-SS", "Шаровой кран DN50 нержавеющий", "PN40", "8", "шт", "3100"],
        ["3", "ABB-S203-C16", "Автоматический выключатель ABB S203 C16",
         "16А, 3P", "12", "шт", "1500"],
        ["4", "VVG-3x2.5", "Кабель ВВГнг 3х2.5", "ГОСТ 31996", "350", "м", "82"],
        ["5", "DUCT-200", "Воздуховод оцинкованный 200мм", "0.5мм", "60", "м", "540"],
        ["6", "PUMP-X1", "Насос дренажный универсальный X1", "погружной",
         "2", "шт", "9500"],
        # duplicate of row 2 -> must be removed in Step 4
        ["2", "BV-DN50-SS", "Шаровой кран DN50 нержавеющий", "PN40", "8", "шт", "3100"],
    ]
    tbl = Table(data, colWidths=[10*mm, 26*mm, 52*mm, 24*mm, 16*mm, 12*mm, 18*mm])
    tbl.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT, 8),
        ("FONT", (0, 0), (-1, 0), FONT_B, 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E1F2")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tbl)

    doc.build(story)
    print(f"wrote {path}")


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "sample_engineering.pdf")
