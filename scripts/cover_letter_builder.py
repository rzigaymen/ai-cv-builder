"""Generate and validate a one-page cover-letter PDF through Microsoft Word."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

try:
    from cv_builder import export_pdf_with_word, measure_with_word
except ImportError:
    from scripts.cv_builder import export_pdf_with_word, measure_with_word


FONT = "Aptos"
TEXT = RGBColor(35, 35, 35)
MUTED = RGBColor(78, 78, 78)
MARGIN_MM = 22


@dataclass(frozen=True)
class LetterLayout:
    body_size: float
    body_line_spacing: float
    paragraph_after: float
    greeting_after: float
    closing_after: float
    metadata_size: float = 10.2
    subject_before: float = 22
    subject_after: float = 9


LAYOUT_PROFILES = (
    LetterLayout(11.0, 1.18, 8.5, 9, 18, subject_before=33, subject_after=33),
    LetterLayout(10.8, 1.15, 7.5, 8, 16, subject_before=33, subject_after=33),
    LetterLayout(10.5, 1.10, 5.5, 7, 14, subject_before=31, subject_after=31),
)


def _remove_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "nil")


def _set_cell_margins(cell, top=0, start=0, bottom=0, end=0) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _set_run(run, size=10.8, bold=False, color=TEXT) -> None:
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def _set_paragraph(paragraph, after=0, before=0, line=1.08) -> None:
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def _add_text(
    document,
    text,
    *,
    size=10.8,
    bold=False,
    align=None,
    after=0,
    before=0,
    color=TEXT,
    line=1.08,
):
    paragraph = document.add_paragraph()
    if align is not None:
        paragraph.alignment = align
    _set_paragraph(paragraph, after=after, before=before, line=line)
    run = paragraph.add_run(text)
    _set_run(run, size=size, bold=bold, color=color)
    return paragraph


def _configure_document(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(MARGIN_MM)
    section.bottom_margin = Mm(MARGIN_MM)
    section.left_margin = Mm(MARGIN_MM)
    section.right_margin = Mm(MARGIN_MM)
    section.header_distance = Mm(8)
    section.footer_distance = Mm(8)
    vertical_alignment = OxmlElement("w:vAlign")
    vertical_alignment.set(qn("w:val"), "center")
    section._sectPr.append(vertical_alignment)
    normal = document.styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(10.8)
    normal.font.color.rgb = TEXT
    normal.paragraph_format.line_spacing = 1.08
    normal.paragraph_format.space_after = Pt(0)
    for style_name in ("Cover Letter Body", "Cover Letter Meta"):
        if style_name not in document.styles:
            style = document.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
        else:
            style = document.styles[style_name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        style.font.size = Pt(10.8 if style_name.endswith("Body") else 9.5)


def _format_application_date(content: dict) -> str:
    """Format only the application date; recipient location is rendered separately."""
    application_date = content.get("date") or date.today().strftime("%d. %B %Y")
    return application_date


def render_letter(
    content: dict, output_docx: Path, layout: LetterLayout = LAYOUT_PROFILES[0]
) -> None:
    required = ("applicant_name", "email", "phone", "company", "location", "subject", "greeting", "paragraphs", "closing")
    missing = [key for key in required if not content.get(key)]
    if missing:
        raise ValueError("Missing required cover-letter fields: {}".format(", ".join(missing)))
    if not isinstance(content["paragraphs"], list) or not content["paragraphs"]:
        raise ValueError("The paragraphs field must be a non-empty list.")

    document = Document()
    _configure_document(document)

    header = document.add_table(rows=1, cols=2)
    header.autofit = False
    header.columns[0].width = Mm(92)
    header.columns[1].width = Mm(74)
    _remove_table_borders(header)
    for cell in header.rows[0].cells:
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        _set_cell_margins(cell)
    sender = header.cell(0, 1).paragraphs[0]
    sender.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_paragraph(sender, after=0, line=1.0)
    run = sender.add_run(content["applicant_name"])
    _set_run(run, size=11, bold=True)
    for value in (content["email"], content["phone"], content.get("city", "Example City")):
        p = header.cell(0, 1).add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _set_paragraph(p, line=1.0)
        _set_run(p.add_run(value), size=9.5, color=MUTED)

    _add_text(document, "", after=5)
    recipient_block = document.add_table(rows=1, cols=2)
    recipient_block.autofit = False
    recipient_block.columns[0].width = Mm(92)
    recipient_block.columns[1].width = Mm(74)
    _remove_table_borders(recipient_block)
    for cell in recipient_block.rows[0].cells:
        _set_cell_margins(cell)
    left = recipient_block.cell(0, 0)
    left.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    company = left.paragraphs[0]
    _set_paragraph(company, after=0, line=1.0)
    _set_run(company.add_run(content["company"]), size=10.8, bold=True)
    recipient_location = left.add_paragraph()
    _set_paragraph(recipient_location, after=0, line=1.0)
    _set_run(recipient_location.add_run(content["location"]), size=10.2, color=MUTED)
    date_cell = recipient_block.cell(0, 1)
    date_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.BOTTOM
    application_date = date_cell.paragraphs[0]
    application_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_paragraph(application_date, after=0, line=1.0)
    _set_run(
        application_date.add_run(_format_application_date(content)),
        size=layout.metadata_size,
        color=TEXT,
    )
    _add_text(
        document,
        content["subject"],
        size=11,
        bold=True,
        before=layout.subject_before,
        after=layout.subject_after,
    )
    _add_text(
        document,
        content["greeting"],
        size=layout.body_size,
        after=layout.greeting_after,
        line=layout.body_line_spacing,
    )
    for paragraph_text in content["paragraphs"]:
        if not isinstance(paragraph_text, str) or not paragraph_text.strip():
            raise ValueError("Each cover-letter paragraph must be non-empty text.")
        _add_text(
            document,
            paragraph_text.strip(),
            size=layout.body_size,
            after=layout.paragraph_after,
            line=layout.body_line_spacing,
        )
    _add_text(
        document,
        content["closing"],
        size=layout.body_size,
        after=layout.closing_after,
        line=layout.body_line_spacing,
    )
    _add_text(
        document,
        content["applicant_name"],
        size=layout.body_size,
        after=0,
        line=layout.body_line_spacing,
    )

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_docx)


def select_adaptive_layout(content: dict, output_docx: Path) -> tuple[LetterLayout, object]:
    """Choose the largest readable profile that fits the actual letter on one page."""
    measurements = []
    for index, layout in enumerate(LAYOUT_PROFILES):
        render_letter(content, output_docx, layout)
        measurement = measure_with_word(output_docx)
        if measurement is None:
            raise RuntimeError("Word pagination is required for cover-letter layout validation.")
        measurements.append(measurement)
        if measurement.pages == 1:
            return layout, measurement
    return LAYOUT_PROFILES[-1], measurements[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a one-page cover-letter PDF using Word.")
    parser.add_argument("input_json", type=Path, help="Structured cover-letter JSON input")
    parser.add_argument("output_pdf", type=Path, help="Destination PDF path")
    parser.add_argument("--keep-docx", action="store_true", help="Keep the temporary DOCX for inspection")
    args = parser.parse_args()
    if not args.input_json.exists():
        parser.error("Input JSON does not exist: {}".format(args.input_json))
    try:
        content = json.loads(args.input_json.read_text(encoding="utf-8"))
        if not isinstance(content, dict):
            raise ValueError("Input JSON must contain an object.")
        docx_path = args.output_pdf.with_suffix(".tmp.docx")
        layout, measurement = select_adaptive_layout(content, docx_path)
        render_letter(content, docx_path, layout)
        _, validation = export_pdf_with_word(
            docx_path,
            args.output_pdf,
            [content["company"], content["subject"], content["applicant_name"]],
        )
        print("Created PDF: {}".format(args.output_pdf))
        print(
            "Layout: body={:.1f}pt, line={:.2f}, paragraph-spacing={:.1f}pt".format(
                layout.body_size, layout.body_line_spacing, layout.paragraph_after
            )
        )
        print("Word page count: {}".format(measurement.pages))
        print("Pages: {}".format(validation.pages))
        print("A4: {}".format(validation.is_a4))
        print("Selectable text: passed")
        if not args.keep_docx and docx_path.exists():
            docx_path.unlink()
        return 0
    except Exception as exc:
        print("Cover-letter generation failed: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
