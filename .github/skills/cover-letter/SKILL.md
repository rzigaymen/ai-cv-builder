---
name: cover-letter
description: "Create a fresh, tailored one-page cover letter from an exact job posting, a candidate profile, and an optional job assessment. Use when generating application letters or cover-letter PDFs."
---

# Cover Letter Generation

Create a truthful, individually tailored cover letter for one application. This skill does not translate or reuse a previous employer's letter.

## Required sources

1. Read the supplied candidate profile as the factual source of experience, education, projects, skills, dates, and status. See [`profile.example.md`](../../../examples/profile.example.md) for the expected structure. When orchestrated by `apply-job`, reuse the unchanged profile context already loaded for the application.
2. Read and verify the original job description. When orchestrated by `apply-job`, consume the verified `drafts/job_description.md` and `drafts/job_assessment.md` produced earlier; do not retrieve the posting again. Match the exact employer, position title, job ID, locations, and URL before drafting. Do not substitute a similarly titled vacancy.
3. Use the latest job assessment when available, especially its verified responsibilities, location, and unresolved facts. The posting is not evidence that the candidate possesses a requirement.

## Drafting procedure

1. Extract the employer, exact position title, application language, recipient or hiring team if identifiable, eligible office location, and current application date. Never invent a recipient name or company address.
2. Independently rank the candidate's verified professional experience, completed projects, ongoing projects, education, and skills against the actual responsibilities. Select only the strongest relevant evidence that fits one page.
3. Distinguish professional experience, completed hands-on work, ongoing work, coursework, and basic knowledge. Never claim production deployment, enterprise scale, advanced proficiency, completed experiments, metrics, or outcomes not documented in the supplied profile.
4. Write approximately 250–330 words, adjusting for the application. Use natural German for German postings and natural professional English for English postings. Use:
   - an opening naming the role and a specific reason for interest;
   - relevant academic or project evidence;
   - relevant professional or practical evidence;
   - a concise, natural conclusion.
5. Explain why the work interests the candidate and how documented experience relates to it. Do not repeat the CV line by line, use generic motivation, flatter the employer, or claim unverified personal motivations.
6. Use degree names exactly as supplied in the candidate profile, translated only when the application language requires it.
7. Use a neutral professional greeting when no hiring manager is identified. Never carry over company names, subjects, dates, or wording from another application.

## Style constraints

Use natural, straightforward, professional language: confident but modest, specific, and readable. Avoid exaggerated enthusiasm, desperation, empty corporate buzzwords, repeated “I am excited to apply” openings, and long technology lists without context.

## Output and design

Provide structured content to `scripts/cover_letter_builder.py`. The generator creates a temporary DOCX and exports a validated PDF through Microsoft Word. The intended output is a single A4 portrait page with:

- sender contact details aligned upper right;
- employer name and verified location aligned left;
- current date near the top;
- a two-column recipient/date block: the verified employer name and employer location on the left, with only the actual application date right-aligned and vertically aligned with the location line;
- bold subject;
- left-aligned paragraphs with clear separation;
- approximately two blank text-line heights after the recipient/date block before the bold subject, and after the bold subject before the greeting; use explicit paragraph spacing rather than empty paragraphs;
- Add one additional body-line height to both subject gaps when the approved layout already has the two-line spacing, and vertically center the complete letter block on the A4 page. Keep the text alignment unchanged: recipient/company left, date right, body left, and sender/contact header right.
- professional greeting and closing;
- plain white background, readable 10.5–11 pt text, and no logos or decorative graphics.
- The generator must select typography and spacing by measuring the actual letter with Word. Try the preferred readable profile first (approximately 11 pt body text, 1.15–1.20 line spacing, and visible paragraph separation); reduce spacing before reducing body text, and never reduce below 10.5 pt solely to force one-page output.
- Do not accept a one-page result as sufficient visual validation: inspect paragraph separation, readable text, balanced whitespace, and formal header/signature placement.

Save the written draft as `output/<Company>_Cover_Letter_Draft.md` when requested and the final PDF as `output/<Company>_Cover_Letter.pdf`. The Markdown is an intermediate, not an attachment.

## Final checks

- Confirm exact company, role, date, language, and location.
- Confirm every factual claim against the supplied candidate profile.
- Confirm no prior-application references remain.
- Confirm the PDF is exactly one A4 page, selectable/extractable, and has no clipped or overlapping content.
- Report material unresolved facts instead of guessing.
