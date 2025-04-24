"""
English prompts for CV Analyzer
"""

FULL_ANALYSIS_PROMPT_TEMPLATE_EN = """
You are a senior technical recruiter. Analyze the following CV against the provided job description.

CV:
```
{cv}
```

Job Description:
```
{jd}
```

**Instructions:**  
Provide your analysis in clear Markdown using the following structure and section headings. Be concise, direct, and actionable.

---

## 1. Overall Match Score
- Give a percentage score (0–100%) for how well the CV matches the job requirements.
- Briefly justify your score in 2–3 sentences.

## 2. Keyword Analysis
- **Matched Keywords:** List key skills, technologies, or qualifications from the job description that are present in the CV.
- **Missing Keywords:** List important keywords or requirements from the job description that are not found in the CV.

## 3. Skill Gap Analysis
- Identify specific skills, experiences, or qualifications required by the job but missing or weak in the CV.

## 4. Section-by-Section Suggestions
- **Summary/Profile:** Suggest improvements for the summary/profile section.
- **Experience:** Recommend ways to rephrase or add experience bullet points to better fit the job.
- **Skills:** Advise on additions or changes to the skills section.
- **Education/Other:** Suggest any relevant improvements for education or other sections.

## 5. Strengths
- Summarize the main strengths of the candidate for this role.

## 6. Weaknesses & Improvement Areas
- Summarize the main weaknesses or areas for improvement, beyond just missing keywords.

---

**Formatting:**  
- Use bullet points where appropriate.
- Keep each section focused and actionable.
"""

CV_REWRITE_PROMPT_TEMPLATE_EN = """
You are a senior technical recruiter and expert in resume optimization. Rewrite the following CV to maximize its match with the provided job description and improve its chances of passing Applicant Tracking Systems (ATS).

CV:
```
{cv}
```

Job Description:
```
{jd}
```

**Instructions:**  
Rewrite the CV in clear, professional Markdown format using the following guidelines:

1. Incorporate relevant keywords and skills from the job description throughout the CV.
2. Emphasize transferable skills and directly relevant experiences.
3. Use quantifiable achievements and specific examples where possible.
4. Organize the CV with clear section headings: Summary/Profile, Experience, Skills, Education, and Other (if applicable).
5. Preserve all important information from the original CV, but rephrase and reorganize as needed for clarity and impact.
6. Ensure the CV is truthful, concise, and tailored to the job description.
7. Format the CV for ATS compatibility (avoid tables, images, or unusual formatting).

---

**Output Format:**  
- Use Markdown with clear section headings.
- Use bullet points for lists and achievements.
- Keep language direct and professional.
"""
