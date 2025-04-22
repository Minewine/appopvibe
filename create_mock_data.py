#!/usr/bin/env python3
"""
Script to create a mock report file for testing when API is unavailable.
Run this on your production server to create the necessary mock data file.
"""
import os
import logging

# Setup path
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS_FOLDER = os.path.join(APP_ROOT, 'reports')
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# File path for mock report
MOCK_REPORT_PATH = os.path.join(REPORTS_FOLDER, 'report_2025-04-21T05-05-11Z.md')

# Mock report content
MOCK_REPORT = """# CV Analysis Report — 2025-04-21T05:05:11Z UTC

## Language
English

## Candidate CV
Sample CV content for testing purposes.

## Job Description
Sample job description for testing the application.

## LLM Analysis
This is a mock analysis that will be shown when the API call fails.

The candidate shows strong potential for the position with relevant skills and experience. 
Here's a breakdown of the match:

### Key Strengths:
- Technical skills align with requirements
- Relevant experience in the industry
- Good communication skills demonstrated

### Areas for Improvement:
- Consider adding more quantifiable achievements
- Could benefit from more specific examples
- Highlight leadership experience more prominently

### Recommendations:
1. Reorganize CV to emphasize most relevant experience
2. Add metrics and results to demonstrate impact
3. Tailor personal statement to match job description more closely

## Rewritten CV
```
JOHN DOE
Software Developer
john.doe@example.com | (555) 123-4567 | linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Dedicated Software Developer with 5+ years of experience creating robust applications and services. Proficient in Python, JavaScript, and cloud technologies with a proven track record of delivering high-quality solutions that meet business requirements.

TECHNICAL SKILLS
- Languages: Python, JavaScript, TypeScript, SQL
- Frameworks: Flask, React, Node.js
- Tools: Git, Docker, CI/CD, AWS

PROFESSIONAL EXPERIENCE

Senior Software Developer | Tech Solutions Inc. | 2020-Present
- Led development of customer-facing API platform processing 5M+ requests daily
- Reduced application loading time by 40% through optimization techniques
- Mentored 4 junior developers, improving team productivity by 25%

Software Developer | InnovateSoft | 2018-2020
- Developed and maintained e-commerce platform serving 10,000+ daily users
- Implemented automated testing that reduced bug reports by 35%
- Collaborated with cross-functional teams to deliver projects on time and on budget

EDUCATION
Bachelor of Science in Computer Science | University Tech | 2018
```
"""

# Create the mock report file
try:
    with open(MOCK_REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(MOCK_REPORT)
    print(f"Successfully created mock report at: {MOCK_REPORT_PATH}")
except Exception as e:
    print(f"Error creating mock report: {str(e)}")

print("\nTo apply this mock data, make sure your passenger_wsgi.py contains:")
print("os.environ['USE_MOCK_DATA'] = 'true'")
print("\nThen restart your application with: touch tmp/restart.txt")