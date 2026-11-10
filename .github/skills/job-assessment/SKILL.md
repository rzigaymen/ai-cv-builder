---
name: job-assessment
description: "Assess a job opportunity against the documented professional profile. Use when evaluating a job description, job posting, role fit, qualifications, location eligibility, or interview preparation."
---

# Job Opportunity Assessment

Assess a job posting against the user's documented experience and produce a grounded Markdown report. Do not create or revise a CV as part of this skill.

## Procedure

1. Read the candidate profile supplied for the assessment (see [`profile.example.md`](../../../examples/profile.example.md) for the expected structure). In an `apply-job` run, use the unchanged profile context already loaded by the orchestrator for downstream steps. Treat it as the source of truth for the candidate's background; do not infer experience from career interests or from the job posting.
2. Accept either pasted job-description text or a job-posting URL. For a URL, retrieve and verify the exact vacancy once, then save the complete extracted facts to `drafts/job_description.md`. If that file is supplied by `apply-job`, treat it as the verified source and do not browse or retrieve the URL again.
3. Establish job identity before interpreting the content. Record and match the exact vacancy title, employer, job ID, and original URL. Distinguish the exact vacancy from similarly titled, older, internship, or related postings. Never combine postings; if a source contains multiple locations or differs from another source, attribute each fact to its source and resolve conflicts using the exact title and job ID. Do not repeat internet searches for facts already recorded and attributed in the shared draft.
4. Prefer sources in this order: the exact LinkedIn vacancy, the employer's exact vacancy identified by the same job ID, then clearly identified third-party listings. Cross-check conflicting sources rather than silently substituting a similar vacancy. If the full posting cannot be accessed or verified, say exactly what was unavailable and do not invent missing requirements.
5. Extract and organize every material item in the complete accessible posting:
   - Required qualifications
   - Preferred qualifications
   - Responsibilities
   - Technologies, tools, and methods
   - Degree/field requirements and completed-semester requirements
   - Languages and proficiency requirements
   - Working hours, employment type, contract duration, and start date
   - All advertised workplace locations, remote/hybrid conditions, and required client travel
   Preserve the posting's stated priority and distinguish explicit requirements from inferred expectations. Do not label an item unknown if it appears in an accessible authoritative source.
6. Verify location separately from technical fit:
   - Extract all exact-vacancy locations, not only the first city shown.
   - Prefer the exact vacancy's locations over a generic careers page or a similarly titled posting.
   - The candidate's stated location or a confirmed compatible remote/hybrid arrangement passes the geographical filter.
   - The candidate's stated commuting area is acceptable; a fully remote role is acceptable when the employer permits work from that location.
   - An on-site role outside the candidate's stated commuting area without a compatible alternative is not suitable.
   - Never reject a multi-location vacancy when one listed location satisfies the profile's stated constraints.
   - Distinguish the regular workplace from occasional client travel. Treat required travel as a separate practical consideration.
   - Report unresolved remote/hybrid details separately; do not convert uncertainty into a location rejection.
   - Record the advertised start date, but treat it as negotiable unless the employer explicitly makes it mandatory. Never use an unconfirmed start-date difference as an automatic rejection criterion or downgrade technical fit solely for that reason.
7. Compare every extracted item with explicit evidence in the supplied candidate profile. For each requirement, use one of these evidence labels:
   - **Demonstrated professional experience** — explicitly performed in a professional role.
   - **Demonstrated project experience** — explicitly implemented or practiced in a project; state whether completed or ongoing.
   - **Coursework / academic foundation** — covered in education or coursework, not professional experience.
   - **Ongoing project / developing** — currently being studied, planned, or practiced; do not imply completion or results.
   - **Basic knowledge / practical exposure** — explicitly described as basic, introductory, or limited.
   - **Missing evidence** — the profile does not document the qualification or experience.
   - **Unverified** — the profile itself says the claim needs confirmation. Do not count it as established evidence.

   Do not promote coursework, an ongoing project, basic knowledge, transferable operational experience, or an unverified claim into professional technical experience. When evidence is partial or adjacent, state what is documented and what remains unproven.
8. Identify strengths supported by evidence, the most consequential gaps, and focused interview-preparation priorities. Prioritize mandatory qualifications, location eligibility, and responsibilities over preferred items. Suggest preparation topics, not fabricated stories or achievements.
9. Make one qualitative recommendation:
   - **Strong fit** — the documented evidence directly supports most central required qualifications and responsibilities, with no critical unsupported requirement.
   - **Plausible / stretch fit** — there is relevant evidence or transferable experience, but one or more significant requirements are only partially supported, developing, or missing.
   - **Poor fit** — several central requirements are unsupported or the role's core work substantially exceeds documented experience.

   Justify the recommendation with specific evidence and gaps. If the posting or profile is incomplete, state the limitation and qualify the recommendation. Never calculate or state a numerical match percentage or imply precision unsupported by the evidence.
10. Produce a concise, structured Markdown report using the format below. Cite the exact vacancy source, job ID, and profile sections or job-posting wording so the reasoning is traceable. Clearly flag only genuinely unresolved facts.

## Report Format

# Job Assessment: [Role title] — [Company, if stated]

**Exact vacancy:** [Exact title] — [Employer] — [Job ID]  
**Original URL:** [Provided posting URL]  
**Confirmed workplace locations:** [All locations from the exact vacancy, with source attribution]  
**Location eligibility:** **Passed**, **Not suitable**, or **Requires verification** — [brief reason; separate remote/hybrid and travel considerations]  
**Verified mandatory requirements:** [Bulleted or semicolon-separated list, or "None stated/accessibly verified"]  
**Assessment basis:** supplied candidate profile and the complete accessible content of the exact vacancy  
**Recommendation:** **Strong fit**, **Plausible / stretch fit**, or **Poor fit** — [brief justified summary]

## Role Summary
[Briefly summarize the role's main work and requirements.]

## Qualifications and Responsibilities
| Posting item | Priority / type | Profile evidence and source | Assessment |
|---|---|---|---|
| [Requirement, preference, responsibility, or technology] | [Required / Preferred / Responsibility / Technology] | [Documented evidence or "Not documented"] | [Evidence label and concise comparison] |

Include every material item extracted from the posting. Split compound requirements into separate rows when their evidence differs.

Do not include a generic "Questions to Clarify" heading. Add it only when a material fact remains unresolved after checking the exact vacancy and authoritative employer source. Never ask the user to provide information already stated in the posting. Do not ask generic questions merely to fill the template.

## Strengths
- [Evidence-backed strength and why it matters for this role.]

## Gaps and Unverified Claims
- [Missing or partial evidence, its importance, and any claim that must be verified.]
- State "None identified" only when applicable; do not omit material gaps.

## Interview Preparation Priorities
1. [Role-specific topic or requirement to prepare for, grounded in the posting and actual experience.]
2. [Next priority.]

## Recommendation Rationale
[Explain why the recommendation follows from the most important supported and unsupported requirements. Note information that could change the assessment.]

## Questions to Clarify
- Include this section only when necessary. Ask only about material unresolved facts, such as an unverified location arrangement, mandatory travel, or a profile claim marked unverified.

## Evidence and Accuracy Rules

- Never fabricate or embellish experience, technical proficiency, certifications, projects, achievements, metrics, or outcomes.
- The user's profile explicitly marks the IDPS seminar as ongoing, Python and several other skills as basic or introductory, and some certification/project claims as requiring verification. Preserve those distinctions whenever relevant.
- Do not use prior CV descriptions or the job posting itself as evidence that the user has a qualification. Treat profile claims marked for confirmation as **Unverified** until the user confirms them.
- Do not infer proficiency from a technology's mere mention in an ongoing or planned project. Distinguish planning, study, implementation, and completed results.
- Prefer employer-confirmed information over third-party summaries, and identify third-party information explicitly.
- Do not replace an inaccessible exact vacancy with a similarly titled vacancy. If the exact vacancy cannot be verified, state the limitation and qualify the recommendation.
- If clarification is necessary to decide whether a claim is established, ask the user rather than assuming. Ask only after all accessible authoritative sources have been checked.
