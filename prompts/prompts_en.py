"""
English prompts for CV Analyzer
"""

FULL_ANALYSIS_PROMPT_TEMPLATE_EN = """
I need you to analyze a CV (resume) against a job description.

CV:
```
{cv}
```

Job Description:
```
{jd}
```

Please provide a comprehensive analysis in Markdown format with the following distinct sections:

### Overall Match Score
- Provide a percentage score (0-100%) indicating how well the CV matches the job description requirements. Briefly justify the score.

### Keyword Analysis
- **Keywords Matched:** List key skills, technologies, or qualifications from the job description found in the CV.
- **Keywords Missing:** List important keywords from the job description *not* found in the CV.

### Skill Gap Analysis
- Identify specific skills or experience areas mentioned in the job description where the candidate appears to be lacking based on the CV.

### Section-Based Suggestions
- **Summary/Profile:** Provide specific suggestions to improve the CV's summary section for this job.
- **Experience:** Suggest improvements or ways to rephrase experience bullet points to better align with the job description.
- **Skills:** Recommend additions or changes to the skills section.
- **Education/Other:** Note any relevant suggestions for other CV sections.

### Strengths
- Summarize the main strengths of the candidate's profile for this specific role.

### Weaknesses/Areas for Improvement
- Summarize the main weaknesses or areas where the CV could be significantly improved for this role, beyond keyword additions.

Be direct, concise, and provide actionable advice under each section.
"""

CV_REWRITE_PROMPT_TEMPLATE_EN = """
I need you to rewrite the following CV to optimize it for ATS (Applicant Tracking Systems) based on this job description.

CV:
```
{cv}
```

Job Description:
```
{jd}
```

Please rewrite the CV in Markdown format to:
1. Incorporate relevant keywords from the job description.
2. Highlight transferable skills and relevant experiences.
3. Use quantifiable achievements where possible.
4. Maintain a clean, professional structure with clear section headings.
5. Ensure all important information from the original CV is preserved.
6. Focus on making the CV pass ATS filters while remaining truthful.

Format the CV in clean Markdown with appropriate headings for each section.
"""
