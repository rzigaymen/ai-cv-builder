"""Build a structured, ATS-friendly CV from Markdown.

The renderer intentionally supports the small Markdown dialect used by the CV
source: headings, bold entry titles, paragraphs, and unordered lists.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor


@dataclass(frozen=True)
class LayoutConfig:
    font_name: str = "Aptos"
    page_width_mm: float = 210
    page_height_mm: float = 297
    margin_horizontal_mm: float = 18
    margin_vertical_mm: float = 18
    header_footer_distance_mm: float = 6
    name_size: float = 19
    contact_size: float = 9.5
    section_size: float = 11.5
    entry_size: float = 10.5
    metadata_size: float = 9.5
    body_size: float = 10
    body_line_spacing: float = 1.1
    header_name_after: float = 1
    header_contact_after: float = 8
    section_before: float = 10
    section_after: float = 2.5
    entry_before: float = 3
    entry_after: float = 1
    metadata_after: float = 2
    body_after: float = 2.5
    bullet_after: float = 2
    bullet_indent_mm: float = 5.2
    bullet_first_line_indent_mm: float = -3.7
    date_title_char_width_pt: float = 4.7
    date_char_width_pt: float = 4.2
    date_min_gap_pt: float = 42


DesignConfig = LayoutConfig
DESIGN = LayoutConfig()
MIN_BODY_SIZE = 9.5
MIN_NAME_SIZE = 17
MIN_SECTION_SIZE = 10
MIN_ENTRY_SIZE = 9.5
MIN_METADATA_SIZE = 8.5
MIN_BODY_LINE_SPACING = 1.05
MIN_HEADER_CONTACT_AFTER = 8
MIN_SECTION_BEFORE = 9
MIN_SECTION_AFTER = 2.5
MIN_ENTRY_BEFORE = 2
MIN_ENTRY_AFTER = 1
MIN_METADATA_AFTER = 1.5
MIN_BODY_AFTER = 1.5
MIN_BULLET_AFTER = 1.5
MAX_BODY_SIZE = 10.5
MAX_NAME_SIZE = 20
MAX_SECTION_SIZE = 11.5
MAX_ENTRY_SIZE = 10.5
MAX_METADATA_SIZE = 9.5
FONT_NAME = DESIGN.font_name
BODY_SIZE = Pt(DESIGN.body_size)
MUTED = RGBColor(78, 78, 78)
ACCENT = "2F5597"
TEXT = RGBColor(35, 35, 35)
NAME_COLOR = RGBColor(30, 55, 90)
CONTENT_WIDTH_MM = DESIGN.page_width_mm - 2 * DESIGN.margin_horizontal_mm
CONTENT_WIDTH_PT = CONTENT_WIDTH_MM * 72 / 25.4
DATE_MONTH = (
    r"(?:jan(?:uary|uar)?|feb(?:ruary|ruar)?|märz|maerz|mar(?:ch)?|"
    r"apr(?:il)?|mai|may|jun(?:e|i)?|jul(?:y|i)?|aug(?:ust)?|"
    r"sep(?:tember|t)?|okt(?:ober)?|oct(?:ober)?|nov(?:ember)?|"
    r"dez(?:ember)?|dec(?:ember)?)"
)
DATE_ENDPOINT = r"(?:present|heute|\d{4}|[a-zäöü]+[\s-]+\d{4})"
DATE_PATTERN = re.compile(
    rf"(?i)^(?:\d{{4}}|{DATE_MONTH}\s+\d{{4}})"
    rf"(?:\s*[–-]\s*{DATE_ENDPOINT})?$"
)
PROTECTED_LANGUAGE_PATTERNS: tuple[tuple[str, str], ...] = ()
CANONICAL_SECTION_ORDER = (
    "professional summary",
    "professional experience",
    "selected projects",
    "education",
    "technical skills",
    "languages",
    "certifications",
)
EXPECTED_SECTION_ORDER = CANONICAL_SECTION_ORDER[:6]
SECTION_ALIASES = {
    "professional summary": {
        "professional summary",
        "berufliche zusammenfassung",
        "profil",
        "zusammenfassung",
    },
    "professional experience": {
        "professional experience",
        "berufliche erfahrung",
        "berufserfahrung",
    },
    "selected projects": {
        "selected projects",
        "ausgewählte projekte",
        "ausgewaehlte projekte",
        "technical projects",
        "technische projekte",
    },
    "education": {"education", "ausbildung", "bildung"},
    "technical skills": {
        "technical skills",
        "technical skills & tools",
        "technische kenntnisse",
        "technische fähigkeiten",
        "technische faehigkeiten",
    },
    "languages": {"languages", "sprachen"},
    "certifications": {"certifications", "zertifikate", "zertifizierungen"},
}
COURSEWORK_PATTERN = re.compile(
    r"(?i)\b(?:relevant\s+(?:coursework|modules?|academic areas?)|"
    r"relevante\s+(?:studieninhalte|module)|relevante\s+studieninhalte)\b"
)
COMPLETION_WORD_PATTERN = re.compile(
    r"(?i)\b(?:completed|complete|finished|abgeschlossen|fertiggestellt)\b"
)


def strip_inline_markdown(text: str) -> str:
    """Remove presentation-only Markdown markers without changing wording."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("**", "").replace("__", "").replace("`", "")


def validate_protected_languages(
    text: str, patterns: tuple[tuple[str, str], ...] = PROTECTED_LANGUAGE_PATTERNS
) -> tuple[str, ...]:
    """Return configured protected profile languages missing from rendered text."""
    normalized = re.sub(r"\s+", " ", text).casefold()
    return tuple(
        label
        for pattern, label in PROTECTED_LANGUAGE_PATTERNS
        if not re.search(pattern, normalized)
    )


def canonical_section_heading(heading: str) -> str | None:
    normalized = re.sub(r"\s+", " ", heading.strip().casefold())
    for canonical, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return canonical
    return None


def order_sections(sections: list[dict]) -> list[dict]:
    """Return recognized sections in the immutable canonical order."""
    by_name: dict[str, dict] = {}
    unknown: list[str] = []
    duplicates: list[str] = []
    for section in sections:
        canonical = canonical_section_heading(section["heading"])
        if canonical is None:
            unknown.append(section["heading"])
        elif canonical in by_name:
            duplicates.append(section["heading"])
        else:
            by_name[canonical] = section
    if unknown:
        raise ValueError(
            "CV contains unrecognized section heading(s): {}.".format(
                ", ".join(unknown)
            )
        )
    if duplicates:
        raise ValueError(
            "CV contains duplicate section heading(s): {}.".format(
                ", ".join(duplicates)
            )
        )
    return [
        by_name[canonical]
        for canonical in CANONICAL_SECTION_ORDER
        if canonical in by_name
    ]


def _entry_bullet_counts(section: dict) -> list[tuple[str, int]]:
    entries: list[tuple[str, int]] = []
    current_title: str | None = None
    bullets = 0
    for item in section["items"]:
        if item["kind"] == "title":
            if current_title is not None:
                entries.append((current_title, bullets))
            current_title = item["text"]
            bullets = 0
        elif item["kind"] == "bullet" and current_title is not None:
            bullets += 1
    if current_title is not None:
        entries.append((current_title, bullets))
    return entries


def validate_cv_source(
    input_path: Path, *, require_protected_languages: bool = False
) -> tuple[str, ...]:
    """Validate all deterministic CV contracts before any document is rendered."""
    raw_text = input_path.read_text(encoding="utf-8")
    name, contact, sections = parse_markdown(input_path)
    errors: list[str] = []
    canonical_sections = [canonical_section_heading(s["heading"]) for s in sections]
    if not name or not contact:
        errors.append("CV name and contact line are required.")
    if any(section is None for section in canonical_sections):
        errors.append("CV contains an unrecognized section heading.")
    recognized = [section for section in canonical_sections if section is not None]
    if len(recognized) != len(set(recognized)):
        errors.append("Each recognized CV section may appear at most once.")
    if COURSEWORK_PATTERN.search(raw_text):
        errors.append("Coursework/module descriptions are not allowed in Education.")

    section_by_name = {
        canonical: section
        for canonical, section in zip(canonical_sections, sections)
        if canonical is not None
    }
    for required in EXPECTED_SECTION_ORDER:
        if required not in section_by_name:
            errors.append("Missing required section: {}.".format(required.title()))

    for section_name, minimum in (
        ("professional experience", 3),
        ("selected projects", 2),
    ):
        section = section_by_name.get(section_name)
        if section is None:
            continue
        entries = _entry_bullet_counts(section)
        if not entries:
            errors.append("{} must contain at least one entry.".format(section_name.title()))
        for title, bullet_count in entries:
            if bullet_count < minimum:
                errors.append(
                    "{} entry '{}' has {} bullet(s); minimum is {}.".format(
                        section_name.title(), title, bullet_count, minimum
                    )
                )

    projects = section_by_name.get("selected projects")
    if projects is not None:
        items = projects["items"]
        for index, item in enumerate(items):
            if item["kind"] != "title":
                continue
            metadata = ""
            if index + 1 < len(items) and items[index + 1]["kind"] == "text":
                metadata = items[index + 1]["text"]
            date_match = re.search(
                rf"(?i)(\d{{4}}|{DATE_MONTH}\s+\d{{4}}(?:\s*[–-]\s*{DATE_ENDPOINT})?)$",
                metadata,
            )
            if date_match:
                date_text = date_match.group(1).strip()
                ongoing = bool(re.search(r"(?i)(present|heute)$", date_text))
                if not ongoing and not re.fullmatch(r"\d{4}", date_text):
                    errors.append(
                        "Completed project '{}' must use a year-only date.".format(
                            item["text"]
                        )
                    )
                if ongoing and not re.search(r"(?i)[–-]", date_text):
                    errors.append(
                        "Ongoing project '{}' must use a date range.".format(item["text"])
                    )
            if COMPLETION_WORD_PATTERN.search(item["text"]) or (
                "completed" in metadata.casefold()
                or "abgeschlossen" in metadata.casefold()
            ):
                errors.append(
                    "Completed project '{}' must not use a completion label.".format(
                        item["text"]
                    )
                )

    if require_protected_languages:
        missing_languages = validate_protected_languages(raw_text)
        if missing_languages:
            errors.append(
                "Missing protected language entries: {}.".format(
                    ", ".join(missing_languages)
                )
            )
    return tuple(errors)


def parse_markdown(path: Path) -> tuple[str, str, list[dict]]:
    """Parse the CV into a title, contact line, and structured sections."""
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    name = strip_inline_markdown(lines.pop(0).lstrip("# ").strip()) if lines else ""
    while lines and not lines[0].strip():
        lines.pop(0)
    contact = strip_inline_markdown(lines.pop(0).strip()) if lines else ""

    sections: list[dict] = []
    current: dict | None = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            current = {"heading": strip_inline_markdown(heading.group(1).strip()), "items": []}
            sections.append(current)
            continue
        if current is None:
            continue
        if line.startswith("- "):
            current["items"].append({"kind": "bullet", "text": strip_inline_markdown(line[2:].strip())})
        elif line.startswith("**") and line.endswith("**"):
            current["items"].append({"kind": "title", "text": strip_inline_markdown(line)})
        else:
            current["items"].append({"kind": "text", "text": strip_inline_markdown(line)})
    return name, contact, sections


def set_paragraph_spacing(
    paragraph, before=0, after=0, line=DESIGN.body_line_spacing
) -> None:
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Mm(DESIGN.page_width_mm)
    section.page_height = Mm(DESIGN.page_height_mm)
    section.top_margin = Mm(DESIGN.margin_vertical_mm)
    section.bottom_margin = Mm(DESIGN.margin_vertical_mm)
    section.left_margin = Mm(DESIGN.margin_horizontal_mm)
    section.right_margin = Mm(DESIGN.margin_horizontal_mm)
    section.header_distance = Mm(DESIGN.header_footer_distance_mm)
    section.footer_distance = Mm(DESIGN.header_footer_distance_mm)

    normal = document.styles["Normal"]
    normal.font.name = FONT_NAME
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)
    normal.font.size = BODY_SIZE
    normal.font.color.rgb = TEXT
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = DESIGN.body_line_spacing

    for name, size, color in (
        ("CV Section", DESIGN.section_size, ACCENT),
        ("CV Contact", DESIGN.contact_size, "4E4E4E"),
        ("CV Entry", DESIGN.entry_size, "232323"),
        ("CV Metadata", DESIGN.metadata_size, "4E4E4E"),
        ("CV Body", DESIGN.body_size, "232323"),
        ("CV Bullet", DESIGN.body_size, "232323"),
    ):
        if name not in document.styles:
            style = document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        else:
            style = document.styles[name]
        style.font.name = FONT_NAME
        style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.line_spacing = DESIGN.body_line_spacing
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)


def add_bottom_border(paragraph, color="B7C9E2", size="4") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    borders.append(bottom)
    p_pr.append(borders)


def add_header(document: Document, name: str, contact: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(
        paragraph, after=DESIGN.header_name_after, line=DESIGN.body_line_spacing
    )
    run = paragraph.add_run(name)
    run.bold = True
    run.font.name = FONT_NAME
    run.font.size = Pt(DESIGN.name_size)
    run.font.color.rgb = NAME_COLOR

    paragraph = document.add_paragraph(style="CV Contact")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(
        paragraph, after=DESIGN.header_contact_after, line=DESIGN.body_line_spacing
    )
    run = paragraph.add_run(contact)
    run.font.name = FONT_NAME
    run.font.size = Pt(DESIGN.contact_size)
    run.font.color.rgb = MUTED
    add_bottom_border(paragraph)


def add_section_heading(document: Document, heading: str) -> None:
    paragraph = document.add_paragraph(style="CV Section")
    paragraph.paragraph_format.keep_with_next = True
    set_paragraph_spacing(
        paragraph,
        before=DESIGN.section_before,
        after=DESIGN.section_after,
        line=DESIGN.body_line_spacing,
    )
    run = paragraph.add_run(heading.upper())
    run.bold = True
    add_bottom_border(paragraph)


def title_fits_with_date(title: str, date: str) -> bool:
    """Use the measured content width to keep title/date rows on one line."""
    estimated_title = sum(
        (DESIGN.date_title_char_width_pt * (1.25 if character.isupper() else 1))
        for character in title
    )
    estimated_date = sum(
        DESIGN.date_char_width_pt * (1.1 if character.isupper() else 1)
        for character in date
    )
    return (
        estimated_title + estimated_date + DESIGN.date_min_gap_pt
        <= CONTENT_WIDTH_PT
    )


def add_title(document: Document, title: str, date: str | None = None) -> None:
    paragraph = document.add_paragraph(style="CV Entry")
    paragraph.paragraph_format.keep_with_next = True
    set_paragraph_spacing(
        paragraph,
        before=DESIGN.entry_before,
        after=DESIGN.entry_after,
        line=DESIGN.body_line_spacing,
    )
    if date and title_fits_with_date(title, date):
        paragraph.paragraph_format.tab_stops.add_tab_stop(
            Mm(CONTENT_WIDTH_MM), alignment=WD_TAB_ALIGNMENT.RIGHT
        )
    run = paragraph.add_run(title)
    run.bold = True
    run.font.name = FONT_NAME
    run.font.size = Pt(DESIGN.entry_size)
    if date:
        if title_fits_with_date(title, date):
            date_run = paragraph.add_run("\t" + date)
            date_run.font.name = FONT_NAME
            date_run.font.size = Pt(DESIGN.metadata_size)
            date_run.font.color.rgb = MUTED
        else:
            add_metadata(document, date, keep_with_next=True)


def is_date(text: str) -> bool:
    return bool(DATE_PATTERN.fullmatch(text.strip()))


def presentation_date(text: str, section_heading: str) -> str:
    """Use year-only dates for completed personal projects in the rendered CV."""
    if "project" not in section_heading.casefold():
        return text
    if re.fullmatch(rf"(?i){DATE_MONTH}\s+(\d{{4}})", text.strip()):
        return re.fullmatch(r"(?i).*?(\d{4})", text.strip()).group(1)
    return text


def add_metadata(
    document: Document, text: str, *, keep_with_next: bool = False
) -> None:
    """Render location/date metadata without constraining the content column."""
    parts = [part.strip() for part in text.split("|", 1)]
    if len(parts) == 2 and is_date(parts[1]):
        paragraph = document.add_paragraph(style="CV Metadata")
        paragraph.paragraph_format.keep_with_next = keep_with_next
        paragraph.paragraph_format.tab_stops.add_tab_stop(
            Mm(CONTENT_WIDTH_MM), alignment=WD_TAB_ALIGNMENT.RIGHT
        )
        set_paragraph_spacing(
            paragraph, after=DESIGN.metadata_after, line=DESIGN.body_line_spacing
        )
        for value in (parts[0], "\t" + parts[1]):
            run = paragraph.add_run(value)
            run.font.name = FONT_NAME
            run.font.size = Pt(DESIGN.metadata_size)
            run.font.color.rgb = MUTED
        return
    if is_date(text):
        paragraph = document.add_paragraph(style="CV Metadata")
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        paragraph.paragraph_format.keep_with_next = keep_with_next
        set_paragraph_spacing(
            paragraph, after=DESIGN.metadata_after, line=DESIGN.body_line_spacing
        )
        run = paragraph.add_run(text)
        run.font.name = FONT_NAME
        run.font.size = Pt(DESIGN.metadata_size)
        run.font.color.rgb = MUTED
        return
    paragraph = document.add_paragraph(style="CV Metadata")
    paragraph.paragraph_format.keep_with_next = keep_with_next
    set_paragraph_spacing(
        paragraph, after=DESIGN.metadata_after, line=DESIGN.body_line_spacing
    )
    run = paragraph.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(DESIGN.metadata_size)
    run.font.color.rgb = MUTED


def add_location_date(
    document: Document, location: str, date: str, *, keep_with_next: bool = True
) -> None:
    """Render location and date on one deliberate, aligned metadata row."""
    paragraph = document.add_paragraph(style="CV Metadata")
    paragraph.paragraph_format.keep_with_next = keep_with_next
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Mm(CONTENT_WIDTH_MM), alignment=WD_TAB_ALIGNMENT.RIGHT
    )
    set_paragraph_spacing(
        paragraph, after=DESIGN.metadata_after, line=DESIGN.body_line_spacing
    )
    for value in (location, "\t" + date):
        run = paragraph.add_run(value)
        run.font.name = FONT_NAME
        run.font.size = Pt(DESIGN.metadata_size)
        run.font.color.rgb = MUTED


def add_body_line(
    document: Document, text: str, *, bullet=False, muted=False, after: float | None = None
) -> None:
    paragraph = document.add_paragraph(style="CV Bullet" if bullet else "CV Body")
    paragraph.paragraph_format.left_indent = (
        Mm(DESIGN.bullet_indent_mm) if bullet else Mm(0)
    )
    paragraph.paragraph_format.first_line_indent = (
        Mm(DESIGN.bullet_first_line_indent_mm) if bullet else Mm(0)
    )
    paragraph.paragraph_format.keep_together = bullet
    if after is None:
        after = DESIGN.bullet_after if bullet else DESIGN.body_after
    set_paragraph_spacing(
        paragraph, before=0, after=after, line=DESIGN.body_line_spacing
    )
    if bullet:
        bullet_run = paragraph.add_run("\u2022\t")
        bullet_run.font.size = BODY_SIZE
        paragraph.paragraph_format.tab_stops.add_tab_stop(Mm(DESIGN.bullet_indent_mm))
    run = paragraph.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = BODY_SIZE
    if muted:
        run.font.color.rgb = MUTED


def render_section(document: Document, section: dict) -> None:
    add_section_heading(document, section["heading"])
    items = section["items"]
    project_section = section["heading"]
    index = 0
    while index < len(items):
        item = items[index]
        if item["kind"] == "title":
            title = item["text"]
            date: str | None = None
            extra_metadata: list[str] = []
            if index + 1 < len(items) and items[index + 1]["kind"] == "text":
                candidate = items[index + 1]["text"]
                parts = [part.strip() for part in candidate.split("|", 1)]
                if is_date(candidate):
                    rendered_date = presentation_date(candidate, project_section)
                    if title_fits_with_date(title, rendered_date):
                        add_title(document, title, rendered_date)
                    elif (
                        index + 2 < len(items)
                        and items[index + 2]["kind"] == "text"
                        and not is_date(items[index + 2]["text"])
                    ):
                        add_title(document, title)
                        add_location_date(
                            document, items[index + 2]["text"], rendered_date
                        )
                        index += 1
                    else:
                        add_title(document, title)
                        add_metadata(document, rendered_date, keep_with_next=True)
                    index += 1
                elif len(parts) == 2 and is_date(parts[1]):
                    rendered_date = presentation_date(parts[1], project_section)
                    if title_fits_with_date(title, rendered_date):
                        add_title(document, title, rendered_date)
                        add_metadata(document, parts[0], keep_with_next=True)
                    else:
                        add_title(document, title)
                        add_location_date(document, parts[0], rendered_date)
                    title = ""
                    index += 1
                elif len(parts) == 2 and is_date(parts[0]):
                    rendered_date = presentation_date(parts[0], project_section)
                    if title_fits_with_date(title, rendered_date):
                        add_title(document, title, rendered_date)
                        add_metadata(document, parts[1], keep_with_next=True)
                    else:
                        add_title(document, title)
                        add_location_date(document, parts[1], rendered_date)
                    title = ""
                    index += 1
            if title:
                add_title(document, title, date)
            for metadata in extra_metadata:
                add_body_line(document, metadata, muted=True, after=DESIGN.metadata_after)
            index += 1
            while index < len(items) and items[index]["kind"] == "text":
                metadata = items[index]["text"]
                add_body_line(document, metadata, muted=True, after=DESIGN.metadata_after)
                index += 1
            continue
        if item["kind"] == "bullet":
            add_body_line(document, item["text"], bullet=True)
        else:
            add_body_line(document, item["text"])
        index += 1


def build_docx(input_path: Path, output_path: Path) -> None:
    _render_docx(input_path, output_path, DESIGN)


@dataclass(frozen=True)
class PageMeasurement:
    pages: int
    utilization: float | None = None


@dataclass(frozen=True)
class PdfValidation:
    pages: int
    is_a4: bool
    extracted_text: str
    missing_sections: tuple[str, ...]
    visual_issues: tuple[str, ...] = ()


def _set_active_layout(config: LayoutConfig) -> None:
    global DESIGN, FONT_NAME, BODY_SIZE, CONTENT_WIDTH_MM, CONTENT_WIDTH_PT
    DESIGN = config
    FONT_NAME = config.font_name
    BODY_SIZE = Pt(config.body_size)
    CONTENT_WIDTH_MM = config.page_width_mm - 2 * config.margin_horizontal_mm
    CONTENT_WIDTH_PT = CONTENT_WIDTH_MM * 72 / 25.4


def _render_docx(input_path: Path, output_path: Path, config: LayoutConfig) -> None:
    _set_active_layout(config)
    name, contact, sections = parse_markdown(input_path)
    sections = order_sections(sections)
    document = Document()
    configure_document(document)
    add_header(document, name, contact)
    for section in sections:
        render_section(document, section)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def _open_private_word():
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        raise RuntimeError(
            "PDF export requires pywin32 in the active Python environment."
        ) from None

    pythoncom.CoInitialize()
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        return pythoncom, word
    except Exception:
        pythoncom.CoUninitialize()
        raise


def _measure_open_word_document(document) -> PageMeasurement:
    document.Repaginate()
    pages = int(document.ComputeStatistics(2))  # wdStatisticPages
    utilization = None
    if pages == 1:
        last_range = document.Range(document.Content.End - 1, document.Content.End)
        bottom = float(last_range.Information(6))  # wdVerticalPositionRelativeToPage
        usable_height = (
            DESIGN.page_height_mm - DESIGN.margin_vertical_mm * 2
        ) * 72 / 25.4
        if bottom > 0 and usable_height > 0:
            utilization = min(1.0, bottom / usable_height)
    return PageMeasurement(pages, utilization)


def measure_with_word(docx_path: Path) -> PageMeasurement | None:
    """Measure a saved DOCX with a private, invisible Word instance."""
    try:
        pythoncom, word = _open_private_word()
    except (ImportError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return None

    document = None
    try:
        document = word.Documents.Open(
            str(docx_path.resolve()), ReadOnly=True, AddToRecentFiles=False
        )
        return _measure_open_word_document(document)
    except Exception as exc:
        print("Word pagination measurement failed: {}".format(exc), file=sys.stderr)
        return None
    finally:
        if document is not None:
            try:
                document.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def _scaled_spacing(config: LayoutConfig, factor: float) -> LayoutConfig:
    return replace(
        config,
        body_line_spacing=max(
            MIN_BODY_LINE_SPACING, 1 + (config.body_line_spacing - 1) * factor
        ),
        header_name_after=max(
            config.header_name_after * factor, DESIGN.header_name_after
        ),
        header_contact_after=max(
            config.header_contact_after * factor, MIN_HEADER_CONTACT_AFTER
        ),
        section_before=max(config.section_before * factor, MIN_SECTION_BEFORE),
        section_after=max(config.section_after * factor, MIN_SECTION_AFTER),
        entry_before=max(config.entry_before * factor, MIN_ENTRY_BEFORE),
        entry_after=max(config.entry_after * factor, MIN_ENTRY_AFTER),
        metadata_after=max(config.metadata_after * factor, MIN_METADATA_AFTER),
        body_after=max(config.body_after * factor, MIN_BODY_AFTER),
        bullet_after=max(config.bullet_after * factor, MIN_BULLET_AFTER),
    )


def _scaled_fonts(config: LayoutConfig, factor: float) -> LayoutConfig:
    return replace(
        config,
        body_size=max(MIN_BODY_SIZE, min(MAX_BODY_SIZE, config.body_size * factor)),
        name_size=max(MIN_NAME_SIZE, min(MAX_NAME_SIZE, config.name_size * factor)),
        section_size=max(
            MIN_SECTION_SIZE, min(MAX_SECTION_SIZE, config.section_size * factor)
        ),
        entry_size=max(MIN_ENTRY_SIZE, min(MAX_ENTRY_SIZE, config.entry_size * factor)),
        metadata_size=max(
            MIN_METADATA_SIZE, min(MAX_METADATA_SIZE, config.metadata_size * factor)
        ),
    )


def validate_extracted_pdf(text: str) -> tuple[str, ...]:
    """Validate contracts that must survive Markdown-to-PDF conversion."""
    errors: list[str] = []
    headings: list[str] = []
    for line in text.splitlines():
        canonical = canonical_section_heading(line.strip())
        if canonical is not None:
            headings.append(canonical)
    expected_headings = [
        canonical for canonical in CANONICAL_SECTION_ORDER if canonical in headings
    ]
    if (
        headings != expected_headings
        or headings[: len(EXPECTED_SECTION_ORDER)] != list(EXPECTED_SECTION_ORDER)
    ):
        errors.append("Rendered PDF section order is invalid.")
    for required in EXPECTED_SECTION_ORDER:
        if required not in headings:
            errors.append(
                "Rendered PDF is missing required section: {}.".format(
                    required.title()
                )
            )
    if COURSEWORK_PATTERN.search(text):
        errors.append("Rendered PDF contains a coursework/module description.")
    missing_languages = validate_protected_languages(text)
    if missing_languages:
        errors.append(
            "Rendered PDF is missing protected language entries: {}.".format(
                ", ".join(missing_languages)
            )
        )
    return tuple(errors)


def inspect_rendered_pdf(pdf_path: Path) -> tuple[str, ...]:
    """Rasterize the PDF and inspect text coordinates for metadata alignment."""
    try:
        import fitz
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "Post-render visual validation requires PyMuPDF and pypdf."
        ) from exc

    issues: list[str] = []
    with fitz.open(str(pdf_path)) as pdf_document:
        if len(pdf_document) != 1:
            issues.append("Visual inspection requires exactly one rendered page.")
        for page in pdf_document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
            if pixmap.width < 900 or pixmap.height < 1200:
                issues.append("Rendered page image is below the readability inspection resolution.")
            if not pixmap.samples:
                issues.append("Rendered page image is empty.")

    reader = PdfReader(str(pdf_path))
    coordinate_rows: list[tuple[float, float, str]] = []
    for page in reader.pages:
        def visitor(text, _cm, _tm, _font, _size):
            if text and text.strip():
                coordinate_rows.append((float(_tm[4]), float(_tm[5]), text.strip()))

        page.extract_text(visitor_text=visitor)
    rows: dict[int, list[tuple[float, str]]] = {}
    for x, y, text in coordinate_rows:
        rows.setdefault(round(y), []).append((x, text))
    for values in rows.values():
        line = " ".join(text for _, text in sorted(values))
        date_match = re.search(
            rf"(?i)\b(?:\d{{4}}|{DATE_MONTH}\s+\d{{4}})(?:\s*[–-]\s*(?:present|heute|\d{{4}}))?\b",
            line,
        )
        if not date_match:
            continue
        date_x = min(
            x for x, text in values if date_match.group(0).casefold() in text.casefold()
        ) if any(
            date_match.group(0).casefold() in text.casefold() for _, text in values
        ) else None
        if date_x is None:
            continue
        non_date_x = [x for x, text in values if text != date_match.group(0)]
        if non_date_x and date_x <= max(non_date_x) and "\t" not in line:
            issues.append("A date is not right-aligned relative to its metadata row.")
            break
    return tuple(issues)


def select_adaptive_layout(input_path: Path, output_path: Path) -> tuple[LayoutConfig, PageMeasurement | None]:
    """Choose a readable one-page configuration using Word's real pagination."""
    temp_path = output_path.with_name(".cv-layout-measurement.docx")
    try:
        _render_docx(input_path, temp_path, DESIGN)
        measurement = measure_with_word(temp_path)
        if measurement is None:
            return DESIGN, None
        selected = DESIGN
        selected_measurement = measurement

        if measurement.pages > 1:
            spacing_config = DESIGN
            for spacing_factor in (0.9, 0.8, 0.7, 0.6):
                spacing_config = _scaled_spacing(DESIGN, spacing_factor)
                _render_docx(input_path, temp_path, spacing_config)
                measured = measure_with_word(temp_path)
                if measured is None:
                    return DESIGN, None
                selected, selected_measurement = spacing_config, measured
                if measured.pages == 1:
                    break
            if selected_measurement.pages > 1:
                for font_factor in (0.97, 0.94, 0.91):
                    font_config = _scaled_fonts(selected, font_factor)
                    _render_docx(input_path, temp_path, font_config)
                    measured = measure_with_word(temp_path)
                    if measured is None:
                        return DESIGN, None
                    selected, selected_measurement = font_config, measured
                    if measured.pages == 1:
                        break
        # Under-filled documents stay at the readable base layout. Content
        # allocation belongs to CV tailoring; typography must not be enlarged
        # or spacing changed merely to consume available page area.
        return selected, selected_measurement
    finally:
        if temp_path.exists():
            temp_path.unlink()


def export_pdf_with_word(
    docx_path: Path,
    pdf_path: Path,
    expected_sections: list[str],
    *,
    validate_profile_languages: bool = False,
) -> tuple[PageMeasurement, PdfValidation]:
    """Export and validate a one-page PDF using an isolated Word instance."""
    try:
        pythoncom, word = _open_private_word()
    except (ImportError, RuntimeError) as exc:
        raise RuntimeError(str(exc)) from exc

    docx_document = None
    export_failed = False
    try:
        docx_document = word.Documents.Open(
            str(docx_path.resolve()), ReadOnly=True, AddToRecentFiles=False
        )
        docx_measurement = _measure_open_word_document(docx_document)
        if docx_measurement.pages != 1:
            raise RuntimeError(
                "DOCX is {} pages after adaptive fitting; refusing to export a two-page PDF.".format(
                    docx_measurement.pages
                )
            )

        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        docx_document.ExportAsFixedFormat(
            OutputFileName=str(pdf_path.resolve()),
            ExportFormat=17,  # wdExportFormatPDF
            OpenAfterExport=False,
            OptimizeFor=0,  # wdExportOptimizeForPrint
            Range=0,  # wdExportAllDocument
            Item=0,  # wdExportDocumentContent
            IncludeDocProps=True,
            KeepIRM=True,
            CreateBookmarks=0,
            DocStructureTags=True,
            BitmapMissingFonts=True,
            UseISO19005_1=False,
        )
        docx_document.Close(False)
        docx_document = None

        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            raise RuntimeError("Word did not create a nonempty PDF.")

        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError(
                "PDF validation requires pypdf in the active Python environment."
            ) from None
        pdf_reader = PdfReader(str(pdf_path))
        pdf_pages = len(pdf_reader.pages)
        first_page = pdf_reader.pages[0]
        width_pt = float(first_page.mediabox.width)
        height_pt = float(first_page.mediabox.height)
        a4_width_pt = 210 * 72 / 25.4
        a4_height_pt = 297 * 72 / 25.4
        is_a4 = (
            abs(width_pt - a4_width_pt) <= 1.0
            and abs(height_pt - a4_height_pt) <= 1.0
        )
        extracted_text = "\n".join(
            page.extract_text() or "" for page in pdf_reader.pages
        )
        structural_errors = validate_extracted_pdf(extracted_text)
        missing_sections = tuple(
            section
            for section in expected_sections
            if section.casefold() not in re.sub(r"\s+", " ", extracted_text).casefold()
        )
        visual_issues = inspect_rendered_pdf(pdf_path)
        validation = PdfValidation(
            pages=pdf_pages,
            is_a4=is_a4,
            extracted_text=extracted_text,
            missing_sections=missing_sections,
            visual_issues=structural_errors + visual_issues,
        )
        if validation.pages != 1:
            raise RuntimeError(
                "Exported PDF has {} pages; exactly one page is required.".format(
                    validation.pages
                )
            )
        if not validation.is_a4:
            raise RuntimeError(
                "Exported PDF page size is not A4 ({:.1f} x {:.1f} pt).".format(
                    width_pt, height_pt
                )
            )
        if validation.missing_sections:
            raise RuntimeError(
                "Exported PDF text is missing sections: {}.".format(
                    ", ".join(validation.missing_sections)
                )
            )
        if validation.visual_issues:
            raise RuntimeError(
                "Rendered PDF quality validation failed: {}.".format(
                    " ".join(validation.visual_issues)
                )
            )
        if not extracted_text.strip():
            raise RuntimeError("Exported PDF text could not be extracted.")
        if validate_profile_languages:
            missing_languages = validate_protected_languages(extracted_text)
            if missing_languages:
                raise RuntimeError(
                    "Exported PDF is missing protected language entries: {}.".format(
                        ", ".join(missing_languages)
                    )
                )
        return docx_measurement, validation
    except Exception:
        export_failed = True
        raise
    finally:
        if docx_document is not None:
            try:
                docx_document.Close(False)
            except Exception:
                pass
        try:
            word.Quit()
        finally:
            pythoncom.CoUninitialize()
        if export_failed and pdf_path.exists():
            pdf_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a DOCX CV and optionally a PDF from Markdown.")
    parser.add_argument("input_markdown", type=Path, help="Path to the source Markdown CV")
    parser.add_argument("output_prefix", type=Path, help="Output path prefix, without .docx or .pdf")
    parser.add_argument(
        "--fit-one-page",
        action="store_true",
        help="Adapt typography and spacing using Microsoft Word pagination.",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Export and validate a one-page A4 PDF using Microsoft Word.",
    )
    args = parser.parse_args()
    if not args.input_markdown.exists():
        parser.error("input Markdown file does not exist: {}".format(args.input_markdown))
    source_errors = validate_cv_source(args.input_markdown)
    if source_errors:
        parser.error("CV contract validation failed:\n- " + "\n- ".join(source_errors))
    docx_path = args.output_prefix.with_suffix(".docx")
    pdf_path = args.output_prefix.with_suffix(".pdf")
    measurement = None
    selected_layout = DESIGN
    if args.fit_one_page or args.pdf:
        selected_layout, measurement = select_adaptive_layout(args.input_markdown, docx_path)
    _render_docx(args.input_markdown, docx_path, selected_layout)
    print("Created DOCX: {}".format(docx_path))
    if args.fit_one_page or args.pdf:
        if measurement is None:
            print("Word page count: not verified (Word COM unavailable or failed)")
        else:
            print("Word page count: {}".format(measurement.pages))
            if measurement.utilization is not None:
                print("Page utilization: {:.0%}".format(measurement.utilization))
        print(
            "Layout: body={:.1f}pt, name={:.1f}pt, heading={:.1f}pt, "
            "entry={:.1f}pt, metadata={:.1f}pt, line={:.2f}, "
            "section={:.2f}pt, entry-spacing={:.2f}pt, bullet={:.2f}pt, "
            "margins={:.1f}mm".format(
                selected_layout.body_size,
                selected_layout.name_size,
                selected_layout.section_size,
                selected_layout.entry_size,
                selected_layout.metadata_size,
                selected_layout.body_line_spacing,
                selected_layout.section_before + selected_layout.section_after,
                selected_layout.entry_before + selected_layout.entry_after,
                selected_layout.bullet_after,
                selected_layout.margin_horizontal_mm,
            )
        )
    if args.pdf:
        _, pdf_validation = export_pdf_with_word(
            docx_path,
            pdf_path,
            [section["heading"] for section in parse_markdown(args.input_markdown)[2]],
            validate_profile_languages=True,
        )
        print("Created PDF: {}".format(pdf_path))
        print("PDF page count: {}".format(pdf_validation.pages))
        print("PDF page size: A4")
        print("PDF text extraction: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
