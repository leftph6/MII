#!/usr/bin/env python3
"""Build a review PDF from the versioned Markdown literature review."""

from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/research/bsc-market-intent-literature-review.md"
OUTPUT = ROOT / "output/pdf/bsc-market-intent-literature-review.pdf"
FONT_NAME = "STSong-Light"


def inline_markup(value: str) -> str:
    """Convert the small Markdown subset used by the review to ReportLab XML."""
    value = value.replace(r"\mid", "|")
    value = value.replace(r"\leq", "<=").replace(r"\geq", ">=")
    value = value.replace(r"\rightarrow", "->").replace(r"\to", "->")
    value = value.replace(r"\hat", "")
    value = value.replace("_{<= t}", "[<=t]").replace("_{<=t}", "[<=t]")
    links: list[str] = []

    def save_link(match: re.Match[str]) -> str:
        links.append(f'<link href="{match.group(2)}" color="#1d4ed8">{match.group(1)}</link>')
        return f"@@LINK{len(links) - 1}@@"

    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", save_link, value)
    value = escape(value, entities={"'": "&apos;"})
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    for index, link in enumerate(links):
        value = value.replace(f"@@LINK{index}@@", link)
    return value


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def table_rows(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and "|" in lines[index] and lines[index].strip():
        line = lines[index].strip()
        if not is_table_separator(line):
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
        index += 1
    return rows, index


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReviewTitle",
            parent=base["Title"],
            fontName=FONT_NAME,
            fontSize=20,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=8 * mm,
        ),
        "h1": ParagraphStyle(
            "ReviewH1",
            parent=base["Heading1"],
            fontName=FONT_NAME,
            fontSize=15,
            leading=20,
            textColor=colors.HexColor("#0f3b5d"),
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
        ),
        "h2": ParagraphStyle(
            "ReviewH2",
            parent=base["Heading2"],
            fontName=FONT_NAME,
            fontSize=11.5,
            leading=16,
            textColor=colors.HexColor("#155e75"),
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "ReviewBody",
            parent=base["BodyText"],
            fontName=FONT_NAME,
            fontSize=9.2,
            leading=14,
            alignment=TA_JUSTIFY,
            wordWrap="CJK",
            spaceAfter=2.2 * mm,
        ),
        "bullet": ParagraphStyle(
            "ReviewBullet",
            parent=base["BodyText"],
            fontName=FONT_NAME,
            fontSize=9,
            leading=13,
            leftIndent=5 * mm,
            firstLineIndent=-3 * mm,
            wordWrap="CJK",
            spaceAfter=1.2 * mm,
        ),
        "code": ParagraphStyle(
            "ReviewCode",
            parent=base["Code"],
            fontName=FONT_NAME,
            fontSize=7.5,
            leading=10,
            leftIndent=4 * mm,
            rightIndent=4 * mm,
            backColor=colors.HexColor("#f1f5f9"),
            borderColor=colors.HexColor("#cbd5e1"),
            borderWidth=0.4,
            borderPadding=3 * mm,
            spaceBefore=1 * mm,
            spaceAfter=3 * mm,
        ),
        "small": ParagraphStyle(
            "ReviewSmall",
            parent=base["BodyText"],
            fontName=FONT_NAME,
            fontSize=7.4,
            leading=10,
            wordWrap="CJK",
        ),
    }


def build_story() -> list[object]:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    style = styles()
    story: list[object] = []
    in_code = False
    code_lines: list[str] = []
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if stripped in {r"\[", r"\]"}:
            index += 1
            continue
        if stripped.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), style["code"]))
                code_lines = []
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(raw)
            index += 1
            continue
        if not stripped:
            index += 1
            continue
        if stripped.startswith("|") and "|" in stripped[1:]:
            rows, index = table_rows(lines, index)
            if rows:
                cell_count = max(len(row) for row in rows)
                normalized = [
                    [
                        Paragraph(inline_markup(cell), style["small"])
                        for cell in row + [""] * (cell_count - len(row))
                    ]
                    for row in rows
                ]
                table = Table(normalized, repeatRows=1, hAlign="LEFT", splitByRow=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#94a3b8")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                story.extend([Spacer(1, 1 * mm), table, Spacer(1, 2 * mm)])
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            level, text = len(heading.group(1)), heading.group(2)
            if level == 1 and not story:
                story.append(Paragraph(inline_markup(text), style["title"]))
            else:
                story.append(Paragraph(inline_markup(text), style["h1" if level == 1 else "h2"]))
            index += 1
            continue
        if stripped.startswith("- ") or re.match(r"^\d+\.\s", stripped):
            content = re.sub(r"^(?:- |\d+\.\s)", "", stripped)
            story.append(Paragraph("- " + inline_markup(content), style["bullet"]))
            index += 1
            continue
        story.append(Paragraph(inline_markup(stripped), style["body"]))
        index += 1
    if in_code and code_lines:
        story.append(Preformatted("\n".join(code_lines), style["code"]))
    return story


def add_page(canvas, document) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.setLineWidth(0.4)
    canvas.line(18 * mm, 13 * mm, width - 18 * mm, 13 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(18 * mm, 8 * mm, "Market Intent Inference · Literature Review · 2026-07-28")
    canvas.drawRightString(width - 18 * mm, 8 * mm, f"Page {document.page}")
    canvas.restoreState()


def main() -> None:
    global FONT_NAME
    unicode_font = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    if unicode_font.exists():
        FONT_NAME = "ArialUnicode"
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(unicode_font)))
        pdfmetrics.registerFontFamily(FONT_NAME, normal=FONT_NAME, bold=FONT_NAME, italic=FONT_NAME)
    else:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        FONT_NAME = "STSong-Light"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="BSC Meme Coin 市场微结构、角色/意图推理与强化学习文献综述",
        author="Market Intent Inference",
    )
    document.build(build_story(), onFirstPage=add_page, onLaterPages=add_page)
    print(OUTPUT)


if __name__ == "__main__":
    main()
