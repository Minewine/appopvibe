
# CV vs Job Description Analyzer — Technical Specification  
**Version:** 1.0  **Date:** 2025‑04‑21

---

## 1 Overview
A Flask web application that compares a candidate’s CV against a job description (JD) via an LLM accessed through OpenRouter.  
Key capabilities:

* Multilingual UI and prompt handling  
* ATS‑focused analysis with actionable feedback  
* Optional AI‑generated, ATS‑optimised rewritten CV  
* All inputs and outputs persisted to timestamped Markdown reports  

---

## 2 Functional Requirements

### 2.1 Frontend  
| Module | Feature | Notes |
|--------|---------|-------|
| **Main Form** | Two `<textarea>` controls: **CV** and **JD** | Required |
| | Language selector (`<select>`) | EN, FR (extensible) |
| | “Rewrite my CV” checkbox | Triggers second LLM call |
| | **Submit** button | POST to `/submit` |
| **Result Page** | Render Markdown analysis | Use *markdown2* |
| | Render rewritten CV (if requested) | Below analysis |
| | Download report `.md` | `<a download>` element |

### 2.2 Backend (Flask)
| Route | Method | Responsibility |
|-------|--------|----------------|
| `/` | GET | Serve form |
| `/submit` | POST | • Build prompt(s)  • Call OpenRouter  • Persist Markdown  • Render result |
| `/reports/<filename>` | GET | Secure download of stored report |

### 2.3 CV Rewriting Module
* Triggered when `rewrite_cv=true`.  
* Uses dedicated prompt (`CV_REWRITE_PROMPT_TEMPLATE`) matching selected language.  
* Output replaces candidate’s original formatting with clean Markdown‑formatted CV sections.

---

## 3 Prompt Management
* Prompt templates stored in `prompts/` per language (e.g. `prompts_en.py`).  
* Analysis prompt: `FULL_ANALYSIS_PROMPT_TEMPLATE_<LANG>`  
* Rewrite prompt: `CV_REWRITE_PROMPT_TEMPLATE_<LANG>`  
* Language codes follow ISO 639‑1; auto‑detection optional (`langdetect`).  

---

## 4 OpenRouter Integration
* **Endpoint:** `https://openrouter.ai/api/v1/chat/completions`  
* **Auth:** `OPENROUTER_API_KEY` from environment (.env).  
* **Payload skeleton:**  
  ```json
  {
    "model": "<provider>/<model>",
    "messages": [{"role":"user","content": "<PROMPT>"}],
    "temperature": 0.7,
    "stream": false
  }
  ```  
* HTTP errors & non‑200 codes logged and surfaced to user.

---

## 5 Data Persistence
* Reports saved to `reports/report_<UTC‑timestamp>.md`.  
* Markdown schema:

  ```markdown
  # CV Analysis Report — 2025‑04‑21T14‑33‑12Z

  ## Language
  English

  ## Candidate CV
  <original CV>

  ## Job Description
  <original JD>

  ## LLM Analysis
  <analysis markdown>

  ## Rewritten CV
  <rewritten CV (optional)>
  ```

* Retention: configurable via `REPORT_RETENTION_DAYS`.

---

## 6 Non‑Functional Requirements
| Category | Requirement |
|----------|-------------|
| **Security** | API key in env; CSRF protection; input size limits; rate limiting (Flask‑Limiter) |
| **Privacy** | Reports stored locally only; no third‑party storage |
| **Performance** | LLM timeout 45 s; async HTTP with `httpx`; gunicorn workers = CPU×2 |
| **Accessibility** | WCAG 2.1 AA colouring; keyboard navigation |
| **Internationalisation** | Unicode throughout; RTL readiness |
| **Maintainability** | PEP 8; pre‑commit hooks; .env.example |
| **Testing** | Pytest unit & integration; Cypress E2E |
| **Deployment** | Dockerfile + docker‑compose; Nginx reverse proxy; CI/CD on GitHub Actions |
| **Observability** | Structured JSON logs; Sentry integration (optional) |

---

## 7 Technology Stack
* **Backend:** Python 3.12, Flask 3.x, httpx, python‑dotenv  
* **Frontend:** HTML5, Jinja2, Bootstrap 5, HTMX (optional)  
* **Markdown:** markdown2 for render; Bleach for sanitisation  
* **Testing:** pytest, coverage, Cypress  
* **Containerisation:** Docker, docker‑compose

---

## 8 Directory Layout
```
project_root/
├─ app.py
├─ templates/
│  ├─ form.html
│  └─ result.html
├─ prompts/
│  ├─ prompts_en.py
│  ├─ prompts_fr.py
├─ reports/
├─ static/            # custom CSS/JS
├─ .env
├─ Dockerfile
└─ requirements.txt
```

---

## 9 Open Questions / Assumptions
1. User authentication is out‑of‑scope (single‑user tool).  
2. Max CV/JD size assumed ≤ 30 KB each; beyond that returns 413.  
3. Default model set to `mistralai/mistral-7b`.  

---

## 10 Future Enhancements
* PDF & DOCX upload with automatic text extraction  
* Vector‑store history for user‑specific fine‑tuning loops  
* Email/Slack delivery of report  
* WebSocket streaming of analysis for progress feedback  
* API endpoint for programmatic access  

---

## 11 Glossary
| Term | Meaning |
|------|---------|
| **ATS** | Applicant Tracking System |
| **JD** | Job Description |
| **LLM** | Large Language Model |
| **OpenRouter** | Gateway for routing requests to multiple LLM providers |

---
