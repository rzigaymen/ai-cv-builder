---
name: cv-tailoring
description: "Tailor a concise, ATS-friendly Markdown CV from a candidate profile and a provided job description or job assessment. Use when generating, adapting, or reviewing a CV for a specific role."
---

# CV Tailoring

Create a truthful, concise CV tailored to a specific job while preserving the distinctions and limitations documented in the master profile.

## When to Use

- The user provides a job description, job posting text, or job assessment and asks for a tailored CV.
- The user asks to adapt, rewrite, or optimize a CV for a specific company or role.
- The user asks explicitly to generate a CV draft.

Do not use this skill to assess job fit without producing a CV; use the job-assessment skill for that task.

## Source of Truth

1. Read the candidate profile before drafting. See [`profile.example.md`](../../../examples/profile.example.md) for the expected structure.
2. Treat the supplied profile as the authoritative source for experience, education, projects, skills, certifications, dates, and status.
3. Use only the provided job description or job assessment to identify the target role, company, priorities, keywords, and relevant evidence. When invoked by `apply-job`, consume `drafts/job_description.md` and `drafts/job_assessment.md` as the verified shared inputs; do not retrieve the vacancy again. The job posting is not evidence that the candidate possesses a qualification.
4. If the profile or job input is unavailable, incomplete, inaccessible, or ambiguous in a way that affects accuracy, flag the missing information and ask for clarification rather than guessing.
5. Use the degree naming convention that matches the application language and the supplied profile.

## Evidence and Accuracy Rules

- Prioritize verified, relevant professional experience over academic or aspirational material.
- Label or place coursework, academic foundations, ongoing projects, and basic skills so they cannot be mistaken for completed professional work.
- Never invent achievements, responsibilities, metrics, outcomes, dates, employers, tools, proficiency levels, certifications, or project completion.
- Do not infer technical proficiency merely because a technology appears in a planned or ongoing project.
- Exclude unverified projects and certifications. If an unverified item is important to the role, list it under `Missing or Unverified Information` rather than in the CV experience or skills sections.
- Do not present operational experience as professional cybersecurity engineering experience unless the profile explicitly supports that claim.
- Do not upgrade basic, introductory, academic, or developing knowledge into advanced or professional expertise.
- Preserve ongoing status for incomplete work; do not describe planned experiments or results as completed. For ongoing projects, use `laufend` in German and `in progress` or `ongoing` in English only when the source confirms the project is ongoing.
- Do not append `abgeschlossen`, `completed`, or `finished` to completed project titles. Show the project title plainly and preserve its actual completion date.
- For completed personal projects, preserve the exact source date in the factual profile but write the presentation date as the year only (for example, `2026`, not `August 2026`). Do not add a completion-status word. Ongoing projects retain their accurate date range and may use the language-appropriate ongoing label when useful.
- Avoid redundant status labels when the date or surrounding wording already communicates the status clearly.
- Flag material gaps, conflicting dates, unclear scope, and information requiring confirmation.
- Never use keyword stuffing or repeat a keyword without supporting evidence.
- Treat explicitly protected profile information, such as verified languages and levels, as immutable unless the user authorizes a change. Do not remove or alter it for job relevance, space, or one-page fitting.

## Professional Writing Standard

- Write polished, natural professional English or German appropriate for established employers.
- Prefer specific actions, responsibilities, tools, and documented outcomes over generic traits or abstract claims.
- Use strong, accurate action verbs and the employer's terminology only where it matches documented evidence.
- Do not simplify meaningful work into vague phrases such as "investigate information", "support processes", or "foundational knowledge" when the profile provides more specific substance.
- Do not use childish, informal, awkward, buzzword-heavy, or artificially sophisticated language. Maintain grammatical consistency and natural sentence structure.
- Keep summaries concise but evidence-led: state the candidate's relevant work, projects, tools, and target contribution rather than repeating generic student or beginner disclaimers.
- When shortening for one page, remove repetition and low-relevance detail first; combine overlapping bullets intelligently. Never replace a specific responsibility or technical detail with a weaker generic statement merely to save space.
- Review every bullet as a real employer would: it must identify what was done, in what context, and with which relevant tools or result when documented.
- Use a measured two-way content-fit loop before finalizing a PDF. If the rendered one-page document has substantial usable space remaining, compare the selected evidence against the profile and add omitted, role-relevant responsibilities or project details using the adaptive targets below. If it is too long, remove repetition and low-value detail first. Never use larger fonts or arbitrary blank spacing as a substitute for missing substance.
- Enforce these minimums for every included application: every professional-experience entry has at least 3 substantive bullets, and every selected-project entry has at least 2 substantive bullets. If the page does not fit, omit a lower-priority project or shorten repetition; never weaken evidence or split one responsibility into filler.

## Procedure

1. Read and classify all professional experience, projects, skills, education, certifications, dates, and status markers in the profile. In an `apply-job` run, use the already loaded unchanged profile context rather than rereading it for each downstream drafting step:
   - Verified professional experience
   - Completed projects
   - Ongoing projects
   - Education and coursework
   - Basic or developing skills
   - Verified certifications
   - Unverified or excluded claims
2. Parse the job input into role title, company, responsibilities, required qualifications, preferred qualifications, technologies, and domain keywords. Preserve the distinction between required and preferred items.
3. Compare every documented project and professional experience item against the actual responsibilities and requirements. Independently rank candidates by role relevance and strength of supporting evidence, then select only the strongest material that fits the available CV space. A tailored CV may omit less relevant projects, but omissions must never delete or alter material in the supplied profile.
4. Do not automatically include the Microsoft 365/IAM, IDPS, or automation projects in every application. Select them only when their verified scope materially supports the target role. Distinguish completed hands-on implementation, ongoing work, and theoretical knowledge.
5. Select only evidence that is both documented and relevant. Rank evidence in this order:
   1. Direct professional experience
   2. Completed, documented project experience
   3. Relevant ongoing project experience, explicitly marked as ongoing
   4. Education or coursework
   5. Basic or developing skills
6. Map selected evidence to the job's highest-priority requirements. Rephrase accurately using the job's terminology where it matches documented evidence, but do not claim a stronger level of proficiency.
7. Draft a concise Markdown CV with ATS-readable headings, plain text, reverse-chronological dates, standard job titles, and simple bullets. Avoid tables, columns, icons, graphics, text boxes, and decorative symbols. When the established local DOCX/PDF generator will be used, format entry titles as `**Title**` (not `### Title`) because its supported Markdown dialect treats bold lines as structured entries with compact date metadata.
8. Add a `Missing or Unverified Information` section only when needed for the requested deliverable. Do not include assessment notes, availability questions, or uncertainty reports in a finished CV unless the user explicitly requires them.
9. Review every bullet and skill against the profile and job input. Remove unsupported claims, duplicated keywords, vague filler, and irrelevant detail.
10. Render the draft with the local generator and inspect the measured occupied area. If substantial usable space remains, perform one deliberate content revision using verified profile evidence, then render and measure again. Stop when additions would harm readability, relevance, or the one-page requirement.
11. Preserve the existing DOCX/PDF generator and its formatting; do not modify `scripts/cv_builder.py` as part of CV tailoring.
12. If the user explicitly asked to generate a CV, save the final draft to `output/<company>_CV_Draft.md`, replacing `<company>` with a filesystem-safe company name. If no company is stated, use `output/Target_Company_CV_Draft.md` and flag the missing company name. Do not create this output file unless CV generation was explicitly requested.
13. If the user specifies a different output filename, follow that explicit path instead of the default draft filename.

## Output Format

Use this structure, omitting empty sections:

```markdown
# [Full Name]
[City, Country] | [Email] | [Phone] | [LinkedIn or portfolio, if verified]

## Professional Summary
[Two to four sentences aligned with the role and supported by the profile.]

## Professional Experience
**[Job Title] — [Employer]**
[Location] | [Start date] – [End date or Present]
- [Evidence-backed responsibility or contribution relevant to the role.]

## Selected Projects
**[Project] — [laufend / in progress / ongoing when confirmed]**
[Institution or context] | [Date]
- [Accurate scope, activities, and status.]

## Education
**[Degree] — [Institution]**
[Dates]
- [Relevant coursework only when useful for the target role.]

## Technical Skills
- [Category]: [Documented skills with accurate proficiency qualifiers.]

## Languages
- [Language]: [Documented level]

## Certifications
- [Verified certification only]

## Missing or Unverified Information
- [Specific item requiring confirmation or not documented.]
```

## Final Quality Check

- The CV is concise and tailored to the stated role.
- Every claim is supported by the supplied candidate profile.
- Professional work, completed projects, ongoing projects, coursework, and basic skills are clearly distinguished.
- Project selection is deliberate: all profile material was reviewed, and only the strongest role-relevant evidence was included for the available CV space.
- The degree name follows the application language convention.
- Unverified projects and certifications are excluded from positive claims.
- No invented metrics, achievements, results, dates, or proficiency.
- ATS-readable Markdown uses standard headings and searchable text.
- Finished CVs omit assessment-only notes and missing-information reports; those belong in the assessment workflow, not the application document.
- Any material missing information is explicitly flagged.
- When generation was explicitly requested, the draft exists at the required `output/<company>_CV_Draft.md` path.
- For the established one-page template, content is prioritized by role relevance and evidence strength, while the mandatory bullet minimums remain non-negotiable.
- Treat visual hierarchy as a protected requirement: keep a noticeable header-to-summary gap, clear major-section separation, readable body text, consistent bullet spacing, and right-aligned dates. If one-page fitting fails, shorten repetitive summaries, skills, and bullets before accepting cramped typography or collapsed spacing.
- Before finalizing, perform a writing-quality review: confirm that every bullet is specific and meaningful, the summary is concise rather than generic, technical actions are accurately described, wording sounds like a competent real applicant, and no content was weakened solely to satisfy one-page validation.
- Before PDF approval, compare the rendered language section with the protected entries in the supplied profile; fail the draft if any language or proficiency differs. Shorten repetitive bullets or lower-value descriptions before touching protected profile information.
- If PDF generation is requested, the source uses the generator-compatible bold entry-title format and contains no assessment-only uncertainty section.
- Project status labels are applied consistently across all applications: completed projects have no completion word appended to the title, while confirmed ongoing projects use the language-appropriate ongoing label only when useful.
- The fixed section order is mandatory: Professional Summary, Professional Experience, Selected Projects, Education, Technical Skills, Languages, and optional Certifications. Use translated headings without changing the order.
- Treat these headings as canonical section identities, not free-form placement: the local generator normalizes recognized German and English headings and renders them in that fixed order even when draft Markdown is misordered. Unknown headings are invalid and must be corrected rather than silently placed.
- Education contains only the verified degree, institution, dates, and location where appropriate; never include coursework or module descriptions.
- When an education title does not fit beside its date, put the full title on its own line and render location plus date together on the next line, with location left-aligned and date right-aligned using the generator's measured tab stop. Never use repeated spaces or an isolated location line.
- Before rendering, run `scripts/cv_builder.py`; its deterministic source validation must pass for section order, bullet minimums, education content, protected languages, and project dates/statuses. A failed validation is a failed draft, not a reason to bypass the gate.
