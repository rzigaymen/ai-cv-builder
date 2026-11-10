# AI CV Builder

AI-assisted tooling for producing evidence-based, ATS-friendly CVs and
one-page cover letters from structured Markdown and JSON inputs.

This repository contains the reusable local generators, deterministic
validation, tests, and Agent Skills used to coordinate a job-application
workflow. It is not a hosted application and does not include a model API,
candidate profile, application history, or generated documents.

## Architecture

```text
Candidate profile + job posting
             |
             v
     Agent Skills (.github/skills)
             |
             v
  CV Markdown / cover-letter JSON
             |
             v
 scripts/cv_builder.py      scripts/cover_letter_builder.py
             |
             v
      DOCX and validated A4 PDF
```

- **Agent Skills** define evidence, privacy, tailoring, assessment, and
  orchestration rules.
- **CV builder** renders the supported Markdown dialect to DOCX and can use
  Microsoft Word to measure, export, and validate a one-page A4 PDF.
- **Cover-letter builder** renders structured JSON and validates the exported
  one-page A4 PDF.
- **Tests** protect the CV parser and content contracts. They do not perform
  end-to-end AI evaluation.

## Features

- Evidence-first CV tailoring rules that distinguish professional work,
  projects, education, ongoing work, and basic knowledge.
- Canonical section ordering and minimum bullet-count validation.
- Adaptive readable layout selection for one-page CVs and cover letters.
- A4, page-count, text-extraction, and structural PDF checks when Word is
  available.
- Reusable skills for job assessment, CV tailoring, cover-letter generation,
  and complete application orchestration.
- Safe job-folder naming for local application workspaces.

## Requirements

- Python 3.10 or newer (the project is developed and tested locally on
  Windows).
- Dependencies in [`requirements.txt`](requirements.txt).
- Microsoft Word is required only for pagination measurement and PDF export.
- A compatible AI assistant is required to execute the Agent Skills. This
  repository does not provide an AI model or API credentials.

## Installation

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Run the contract tests:

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

## Usage

Copy and adapt the safe examples:

- [`examples/profile.example.md`](examples/profile.example.md) shows the
  expected factual profile structure. Keep real profiles outside a public
  repository.
- [`examples/cv.example.md`](examples/cv.example.md) is a generator-compatible
  CV draft.
- [`examples/cover-letter.example.json`](examples/cover-letter.example.json)
  is the structured cover-letter input.

Generate a DOCX CV:

```powershell
python scripts\cv_builder.py examples\cv.example.md output\Candidate_CV
```

Generate and validate a one-page CV PDF through Microsoft Word:

```powershell
python scripts\cv_builder.py examples\cv.example.md output\Candidate_CV --pdf
```

Generate and validate a cover-letter PDF:

```powershell
python scripts\cover_letter_builder.py examples\cover-letter.example.json output\Candidate_Cover_Letter.pdf
```

The Agent Skills are stored under
[`.github/skills`](.github/skills) and can be installed or invoked according
to the host assistant's skill conventions. The application orchestrator
creates local `output/Company_JobTitle/drafts/` workspaces; those outputs are
intentionally ignored by Git.

## Privacy and security

Do not commit a real profile, contact details, generated applications,
employer-specific job descriptions, credentials, or API tokens. Review
`git diff --cached` and run a secret scanner before publishing. The included
examples use fictional names and placeholder contact details.

## Current limitations

- PDF export depends on Microsoft Word's Windows COM automation.
- The renderer supports a deliberately small Markdown dialect rather than
  arbitrary Markdown.
- The project provides deterministic formatting and validation, not a
  complete quality guarantee for AI-generated wording.
- Job-posting retrieval, model selection, and agent execution depend on the
  host AI assistant.
- There is no web UI, hosted service, database, authentication layer, or
  automated GitHub publishing workflow.

## License

MIT. See [`LICENSE`](LICENSE).
