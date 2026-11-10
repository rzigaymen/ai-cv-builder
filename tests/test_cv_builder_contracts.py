import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import cv_builder


VALID_DRAFT = """\
# Alex Morgan
Example City | alex.morgan@example.com | +49 30 000000

## Berufliche Zusammenfassung
Kurzprofil.

## Berufliche Erfahrung
**Role — Company**
Example City | March 2026 – Present
- One responsibility.
- Another responsibility.
- A third responsibility.

## Ausgewählte Projekte
**Automation Project**
Personal project | 2026
- First substantive responsibility.
- Second substantive responsibility.
**Ongoing Project**
Example University | October 2026 – Present
- First substantive responsibility.
- Second substantive responsibility.

## Ausbildung
**B.Sc. Computer Engineering — Example University**
Example City | October 2024 – Present

## Technische Kenntnisse
- Git and Python.

## Sprachen
- German: C1
- English: C1
- French: B2
- Arabic: Native

## Zertifikate
- Oracle AI Foundations
"""


class CvBuilderContractTests(unittest.TestCase):
    def write_draft(self, text: str) -> Path:
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", encoding="utf-8", delete=False
        )
        handle.write(text)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_valid_draft_satisfies_contracts(self):
        self.assertEqual(cv_builder.validate_cv_source(self.write_draft(VALID_DRAFT)), ())

    def test_project_month_is_rejected_for_completed_projects(self):
        draft = VALID_DRAFT.replace("Personal project | 2026", "Personal project | August 2026")
        errors = cv_builder.validate_cv_source(self.write_draft(draft))
        self.assertTrue(any("year-only" in error for error in errors))

    def test_coursework_is_rejected(self):
        draft = VALID_DRAFT.replace("Example City | October 2024 – Present", "Relevant coursework: Networks")
        errors = cv_builder.validate_cv_source(self.write_draft(draft))
        self.assertTrue(any("coursework" in error.lower() for error in errors))

    def test_bullet_minimums_are_rejected(self):
        draft = VALID_DRAFT.replace("- A third responsibility.\n", "")
        errors = cv_builder.validate_cv_source(self.write_draft(draft))
        self.assertTrue(any("minimum is 3" in error for error in errors))

    def test_completed_project_presentation_is_year_only(self):
        self.assertEqual(
            cv_builder.presentation_date("August 2026", "Selected Projects"), "2026"
        )

    def render_docx_paragraphs(self, text: str) -> list[str]:
        from docx import Document

        source = self.write_draft(text)
        output = Path(tempfile.mktemp(suffix=".docx"))
        self.addCleanup(lambda: output.unlink(missing_ok=True))
        cv_builder.build_docx(source, output)
        return [paragraph.text for paragraph in Document(output).paragraphs if paragraph.text]

    def test_long_german_education_title_uses_aligned_second_row(self):
        draft = VALID_DRAFT.replace(
            "B.Sc. Computer Engineering",
            "Example University and Computer Engineering",
            1,
        )
        paragraphs = self.render_docx_paragraphs(draft)
        title_index = next(
            index
            for index, paragraph in enumerate(paragraphs)
            if paragraph.startswith("Example University and Computer Engineering")
        )
        self.assertEqual(paragraphs[title_index + 1], "Example City")

    def test_short_english_education_title_keeps_date_on_title_row(self):
        draft = VALID_DRAFT.replace(
            "## Ausbildung",
            "## Education",
        ).replace(
            "**B.Sc. Computer Engineering — Example University**\n"
            "Example City | October 2024 – Present",
            "**B.Sc. Computer Engineering — Example University**\n"
            "Example City | October 2024 – Present",
        ).replace(
            "## Berufliche Zusammenfassung",
            "## Professional Summary",
        ).replace(
            "## Berufliche Erfahrung",
            "## Professional Experience",
        ).replace(
            "## Ausgewählte Projekte",
            "## Selected Projects",
        ).replace(
            "## Technische Kenntnisse",
            "## Technical Skills",
        ).replace(
            "## Sprachen",
            "## Languages",
        ).replace(
            "## Zertifikate",
            "## Certifications",
        )
        paragraphs = self.render_docx_paragraphs(draft)
        title_index = paragraphs.index(
            "B.Sc. Computer Engineering — Example University\tOctober 2024 – Present"
        )
        self.assertEqual(paragraphs[title_index + 1], "Example City")

    def test_misordered_german_markdown_renders_projects_before_education(self):
        draft = VALID_DRAFT.replace(
            "## Ausgewählte Projekte", "## __PROJECTS__", 1
        ).replace("## Ausbildung", "## Ausgewählte Projekte", 1).replace(
            "## __PROJECTS__", "## Ausbildung", 1
        )
        paragraphs = self.render_docx_paragraphs(draft)
        self.assertLess(
            paragraphs.index("AUSGEWÄHLTE PROJEKTE"),
            paragraphs.index("AUSBILDUNG"),
        )

    def test_misordered_english_markdown_renders_projects_before_education(self):
        draft = VALID_DRAFT.replace("## Berufliche Zusammenfassung", "## Professional Summary")
        draft = draft.replace("## Berufliche Erfahrung", "## Professional Experience")
        draft = draft.replace("## Ausgewählte Projekte", "## Selected Projects")
        draft = draft.replace("## Ausbildung", "## Education")
        draft = draft.replace("## Technische Kenntnisse", "## Technical Skills")
        draft = draft.replace("## Sprachen", "## Languages")
        draft = draft.replace("## Zertifikate", "## Certifications")
        draft = draft.replace(
            "## Selected Projects", "## __PROJECTS__", 1
        ).replace("## Education", "## Selected Projects", 1).replace(
            "## __PROJECTS__", "## Education", 1
        )
        misordered = draft
        paragraphs = self.render_docx_paragraphs(misordered)
        self.assertLess(
            paragraphs.index("SELECTED PROJECTS"),
            paragraphs.index("EDUCATION"),
        )

    def test_rendered_pdf_heading_validation_rejects_misordered_sections(self):
        text = "\n".join(
            [
                "PROFESSIONAL SUMMARY",
                "PROFESSIONAL EXPERIENCE",
                "EDUCATION",
                "SELECTED PROJECTS",
                "TECHNICAL SKILLS",
                "LANGUAGES",
            ]
        )
        errors = cv_builder.validate_extracted_pdf(text)
        self.assertTrue(any("section order" in error.lower() for error in errors))

    def test_unknown_heading_is_not_silently_reordered(self):
        draft = VALID_DRAFT.replace("## Sprachen", "## Additional Information")
        errors = cv_builder.validate_cv_source(self.write_draft(draft))
        self.assertTrue(any("unrecognized" in error.lower() for error in errors))


if __name__ == "__main__":
    unittest.main()
