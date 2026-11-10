---
name: apply-job
description: "Coordinate the complete local job-application workflow from one public job-posting URL: retrieve and verify the exact vacancy, assess eligibility, tailor the CV, write a job-specific cover letter, generate and validate both PDFs, and organize all outputs in a job-specific folder."
user-invocable: true
disable-model-invocation: true
argument-hint: "[job posting URL]"
---

# Apply for a Job

Use `/apply-job <job posting URL>` to prepare one complete application locally. This is an orchestration workflow: reuse the existing skills and generators rather than duplicating their drafting or assessment rules.

## Required inputs and source of truth

- Read the candidate profile supplied by the user (see [`examples/profile.example.md`](../../../examples/profile.example.md) for the expected structure) through the existing assessment, CV-tailoring, and cover-letter skills.
- Use the exact public job posting URL supplied by the user.
- Use the existing skills:
  - [`job-assessment`](../job-assessment/SKILL.md) for vacancy retrieval, identity verification, eligibility, and fit assessment.
  - [`cv-tailoring`](../cv-tailoring/SKILL.md) for evidence selection and concise CV Markdown.
  - [`cover-letter`](../cover-letter/SKILL.md) for the independent, truthful cover letter.
- Use the existing local generators:
  - [`cv_builder.py`](../../../scripts/cv_builder.py)
  - [`cover_letter_builder.py`](../../../scripts/cover_letter_builder.py)

Do not modify the candidate's source profile, the job-assessment skill, the cover-letter skill, the cover-letter generator, or the approved CV design during this workflow.

## Execution sequence

### Credit-efficient orchestration rules

- Retrieve and verify the public vacancy exactly once per application.
- Treat `drafts/job_description.md` as the shared, authoritative extraction for assessment, CV tailoring, and cover-letter drafting. Downstream skills must not browse the URL again unless a material fact is missing or conflicting.
- Load unchanged reference material once per application where possible. Do not reread reference PDFs, generator source, or unrelated project files during downstream steps.
- Prefer the existing deterministic Python generators and local validation for filenames, folders, PDF creation, page counts, text extraction, and integrity checks. Use AI only for assessment, evidence selection, tailored CV wording, cover-letter wording, and genuine quality issues.
- Do not perform repeated model rewrites or additional planning/review passes once the draft meets the stated quality checks.
- Keep tool results concise: request summaries and validation results rather than full document or terminal contents.

### 1. Retrieve and verify the exact vacancy

Retrieve the URL with the available web retrieval/browser tools. Prefer the employer's exact vacancy page; cross-check an authoritative employer page when possible. Establish all of the following before drafting:

- Employer and exact position title
- Job ID or requisition ID, if advertised
- Original URL and source URL(s)
- Every advertised work location
- Remote/hybrid/on-site conditions and required travel
- Posting language
- Responsibilities, required qualifications, preferred qualifications, technologies, degree requirements, language requirements, employment details, and advertised start date

Do not merge similarly titled postings. If the complete posting cannot be accessed, save the accessible facts and clearly record what is missing. Ask the user to paste the missing job description only when the inaccessible information is necessary to assess or draft accurately.

Create a safe job folder with:

```text
output/
  Company_JobTitle/
    drafts/
      job_description.md
```

Use [`safe_job_folder.py`](./scripts/safe_job_folder.py) for deterministic filesystem-safe naming and folder creation. If a folder for the same verified employer/title/job ID already exists, reuse it. Do not overwrite an existing final PDF or draft without explicit approval; use a clearly named test folder for test runs.

Use the helper's `application_filenames(language)` convention for final PDF names:

| Application language | CV PDF | Cover-letter PDF |
|---|---|---|
| English | `Candidate_CV.pdf` | `Candidate_Cover_Letter.pdf` |
| German | `Candidate_Lebenslauf.pdf` | `Candidate_Anschreiben.pdf` |

These candidate-based names apply inside each existing company/job-specific folder. Do not rename, delete, or overwrite previously generated files; if a target name already exists, stop and request approval before replacing it or use an explicitly named test output.

Write `drafts/job_description.md` with the exact URL, identity fields, source attribution, posting language, all extracted material facts, and an explicit unavailable-information section when needed.

Do not retrieve the same vacancy again after this draft is complete. If an authoritative cross-check is needed, perform it during this step and record the result in the draft.

### 2. Assess eligibility and suitability

Invoke the existing `job-assessment` workflow using `drafts/job_description.md` and the candidate profile. Save the result to `drafts/job_assessment.md`. The assessment must consume the saved extraction and must not fetch the URL again.

Apply these established user preferences:

- The candidate's stated location and commuting constraints are acceptable.
- Remote work is acceptable when the employer permits work from the candidate's stated location.
- Do not assume willingness to relocate; use the profile's stated constraints.
- Start dates are negotiable and are not automatic rejection criteria.

If a confirmed hard location constraint fails, stop before generating application documents. Preserve the retrieval and assessment drafts and report the exact reason. Do not turn unresolved location details into a rejection.

Do not ask questions already answered by the vacancy or profile. Keep the assessment grounded in documented evidence and distinguish professional experience, projects, coursework, basic knowledge, and missing evidence.

### 3. Tailor the CV

Invoke the existing `cv-tailoring` workflow with the saved job description and assessment. Reuse the unchanged profile context already loaded for this application, then select only the strongest relevant evidence for a concise, readable one-page CV.

The CV must:

- Use the vacancy's language.
- Use `B.Sc. Computer Engineering` for English applications.
- Use `B.Sc. Technische Informatik (Computer Engineering)` for German applications.
- Never append `completed`, `finished`, or `abgeschlossen` to a completed project title.
- Use `in progress`/`ongoing` in English or `laufend` in German only for confirmed ongoing work, and avoid redundant labels.
- Preserve factual dates and status.
- Avoid repeated information and omit less relevant projects when space requires prioritization.
- Use generator-compatible bold entry titles (`**Title**`), not `### Title`.
- Exclude assessment-only uncertainty or missing-information reports from the finished CV.
- Follow the fixed section order: Professional Summary, Professional Experience, Selected Projects, Education, Technical Skills, Languages, and optional Certifications. Never reorder sections to match vacancy priorities.
- The CV generator enforces this canonical order for recognized German and English headings and rejects unknown headings; do not rely on the AI draft's source order.
- Include at least 3 substantive bullets for every included professional-experience entry and at least 2 for every included project. Omit a lower-priority project rather than violating these minimums.
- Exclude all coursework/module descriptions from Education. Education must retain the verified degree, institution, dates, and location where appropriate.
- Use year-only dates for completed personal projects; preserve genuine date ranges for ongoing projects and month/year ranges for employment and education.

Save the Markdown to `drafts/cv_draft.md`. Do not overwrite the original reviewed or optimized CV.

### 4. Write the cover letter

Invoke the existing `cover-letter` workflow with the saved job description, latest assessment, and unchanged profile context. Draft independently from the CV, in the posting's language, using the actual current date, verified employer, exact role title, and eligible location.

Keep the tone natural, specific, professional, and understated. Do not invent employer motivations, achievements, recipients, or qualifications. Save:

- `drafts/cover_letter_draft.md` — readable Markdown working content.
- A temporary JSON payload for the existing generator, removed after successful generation and validation.

### 5. Generate both PDFs

Inspect the current CLI before execution if an interface has changed. From the repository root, use the existing `.venv`:

```powershell
& '.\.venv\Scripts\python.exe' '.\scripts\cv_builder.py' `
  '.\output\Company_JobTitle\drafts\cv_draft.md' `
  '.\output\Company_JobTitle\Candidate_CV' `
  '--fit-one-page' '--pdf'

& '.\.venv\Scripts\python.exe' '.\scripts\cover_letter_builder.py' `
  '.\output\Company_JobTitle\drafts\cover_letter.json' `
  '.\output\Company_JobTitle\Candidate_Cover_Letter.pdf'
```

The CV generator is a fail-closed quality gate, not a page-count helper. It validates the Markdown before rendering and validates the exported PDF's section order, protected content, A4/one-page dimensions, rendered image, and metadata coordinates. Do not treat a DOCX or PDF as successful if `cv_builder.py` reports a contract or visual-quality failure. Do not replace an existing final PDF until the temporary PDF passes all of those checks.

For German applications, substitute `Candidate_Lebenslauf` for the CV output prefix and `Candidate_Anschreiben.pdf` for the cover-letter output path. The CV output prefix and cover-letter output path must be in the job folder, not directly under `output/`. Temporary DOCX files may be created by the generators, but remove only files created during this run after successful validation. Never delete or move historical application files.

The CV generator provides a visible blank-line-equivalent gap between section headings and a larger two-line-equivalent gap after the candidate header before the summary. Treat this visual hierarchy, readable body text, consistent bullet spacing, and right-aligned dates as protected requirements. Always retain `--fit-one-page --pdf`: adaptive fitting may reduce spacing and typography only within the generator's configured readable minimums; if the content still does not fit, shorten repetitive content rather than collapsing spacing, and PDF export must refuse any result that is not exactly one A4 page.

Before final PDF generation, use the generator's Word pagination measurement to assess occupied content area, not only page count. If a one-page CV has substantial usable space, revise the tailored Markdown once with omitted, verified, job-relevant evidence (using adaptive bullet targets rather than quotas), then render and measure again. If it is too long, remove repetition and low-relevance detail before any protected typography or spacing is reduced. Do not fill space with generic statements or enlarged fonts.

### 6. Validate before declaring success

Validate both PDFs with the local PDF libraries and, when available, an actual browser/PDF rendering:

CV:

- Exactly one page and A4 dimensions.
- Extractable/selectable text.
- All essential sections present.
- Correct employer-relevant content, dates, degree name, language, and project statuses.
- Protected profile fields match the supplied candidate profile. 
- No completed-status suffixes.
- No missing or assessment-only sections.
- No title/date overlap, clipped text, or unreadable typography.

Cover letter:

- Exactly one page and A4 dimensions.
- Extractable/selectable text.
- Exact employer and position title.
- Current application date and correct language.
- No unrelated application references.
- Natural, job-specific content without invented claims.
- No clipped text or overlap.

Do not claim visual validation unless the PDF was actually rendered and inspected. If either component fails, preserve successful drafts and artifacts, report the failure precisely, and do not claim the application is complete.

## Required final structure

```text
output/
  Company_JobTitle/
    Candidate_CV.pdf or Candidate_Lebenslauf.pdf
    Candidate_Cover_Letter.pdf or Candidate_Anschreiben.pdf
    drafts/
      job_description.md
      job_assessment.md
      cv_draft.md
      cover_letter_draft.md
```

Keep final PDFs at the job-folder root and Markdown working files inside `drafts/`. Do not create additional nested folders or scatter new application files directly under `output/`.

## Final report

Report the verified employer/title/location, assessment result, folder path, files created, PDF validation results, whether visual inspection was performed, and any unresolved limitations. Include the exact reusable command:

```text
/apply-job <JOB_POSTING_URL>
```
