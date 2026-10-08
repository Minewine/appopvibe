"""Build a one-page Swiss-style CV as a Word document."""
import io
import re
from typing import List, Tuple


RULE = "1F3A5F"

HEADINGS = {
    "en": {
        "summary": "Profile",
        "experience": "Professional experience",
        "projects": "Projects",
        "skills": "Skills",
        "education": "Education",
        "languages": "Languages",
        "other": "Additional information",
        "footer": "Curriculum vitae",
    },
    "fr": {
        "summary": "Profil",
        "experience": "Expérience professionnelle",
        "projects": "Projets",
        "skills": "Compétences",
        "education": "Formation",
        "languages": "Langues",
        "other": "Informations complémentaires",
        "footer": "Curriculum vitae",
    },
}

SECTION_MAP = {
    "summary": "summary",
    "profile": "summary",
    "summary/profile": "summary",
    "résumé": "summary",
    "résumé/profil": "summary",
    "profil": "summary",
    "experience": "experience",
    "expérience": "experience",
    "expérience professionnelle": "experience",
    "projects": "projects",
    "projets": "projects",
    "skills": "skills",
    "compétences": "skills",
    "education": "education",
    "formation": "education",
    "languages": "languages",
    "langues": "languages",
    "other": "other",
    "autre": "other",
}


def extract_rewritten_cv(report_markdown: str) -> Tuple[str, str]:
    """Return (cv_markdown, language code) from a saved report."""
    cv, language, _source = extract_cv_for_docx(report_markdown)
    return cv, language


def extract_cv_for_docx(report_markdown: str) -> Tuple[str, str, str]:
    """Return CV markdown, language, and source (rewritten or original)."""
    language = "fr" if re.search(r"Language:\s*Français", report_markdown) else "en"
    rewritten = re.search(
        r"## (?:Rewritten CV Optimized for ATS|CV réécrit, optimisé ATS)\n+(.*?)(?:\n## |\Z)",
        report_markdown,
        re.S,
    )
    if rewritten:
        cv = re.sub(
            r"\n### (?:Omitted keywords|Mots-clés omis|What changed|Ce qui a changé)\n.*",
            "",
            rewritten.group(1),
            flags=re.S,
        ).strip()
        if cv:
            return cv, language, "rewritten"
    original = re.search(r"## Original CV\n+```\n(.*?)\n```", report_markdown, re.S)
    if original and original.group(1).strip():
        return original.group(1).strip(), language, "original"
    return "", language, ""


def _set_run_font(run, name="Calibri", size=11, bold=False, color=None, italic=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def _add_bottom_border(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), RULE)
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def _heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text.upper())
    _set_run_font(run, size=11, bold=True, color=navy)
    _add_bottom_border(p)
    return p


def _parse_sections(cv_markdown: str) -> Tuple[str, List[str], List[Tuple[str, List[str]]]]:
    lines = cv_markdown.replace("\r\n", "\n").split("\n")
    name = ""
    contact: List[str] = []
    sections: List[Tuple[str, List[str]]] = []
    current = None
    bucket: List[str] = []
    for raw in lines:
        line = raw.strip()
        if line.startswith("## "):
            if current:
                sections.append((current, bucket))
            title = line[3:].strip().lower()
            current = SECTION_MAP.get(title, "other")
            bucket = []
            continue
        if not line or line.startswith("### "):
            continue
        if current is None and not name and not line.startswith(("-", "*")):
            name = line.lstrip("# ").strip()
            continue
        if current is None:
            contact.append(line.lstrip("-* ").strip())
            continue
        bucket.append(line)
    if current:
        sections.append((current, bucket))
    return name or "Curriculum vitae", contact, sections


def build_swiss_cv(cv_markdown: str, language: str = "en") -> bytes:
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Cm, Pt, RGBColor
    except ImportError as exc:
        raise RuntimeError(
            "Word export is not installed in this app. Run the appopvibe pip install python-docx, then restart."
        ) from exc
    navy = RGBColor(0x1F, 0x3A, 0x5F)
    muted = RGBColor(0x55, 0x55, 0x55)
    labels = HEADINGS.get(language, HEADINGS["en"])
    name, contact, sections = _parse_sections(cv_markdown)
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(1.7)
    section.right_margin = Cm(1.7)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    name_p = doc.add_paragraph()
    name_p.paragraph_format.space_after = Pt(0)
    name_run = name_p.add_run(name)
    _set_run_font(name_run, name="Calibri", size=22, bold=True, color=navy)

    if contact:
        contact_p = doc.add_paragraph()
        contact_p.paragraph_format.space_before = Pt(2)
        contact_p.paragraph_format.space_after = Pt(2)
        contact_run = contact_p.add_run("  ·  ".join(contact[:4]))
        _set_run_font(contact_run, size=10, color=muted)

    order = ["summary", "experience", "projects", "education", "skills", "languages", "other"]
    grouped = {key: items for key, items in sections}
    for key in order:
        items = grouped.get(key)
        if not items:
            continue
        _heading(doc, labels[key])
        for item in items:
            bullet = item.startswith(("-", "*"))
            text = item.lstrip("-* ").strip()
            if not text:
                continue
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.08
            if bullet:
                p.paragraph_format.left_indent = Cm(0.4)
                run = p.add_run("•  " + text)
            else:
                run = p.add_run(text)
                run.bold = True
            _set_run_font(run, size=11, bold=run.bold)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_run = footer.add_run(f"{labels['footer']}  ·  {name}")
    _set_run_font(footer_run, size=8, color=muted)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
