"""Render analysis JSON to the markdown report the current app already expects."""

SECTION = {
    "en": {
        "score": "Overall match",
        "must": "Must-haves",
        "keywords": "Keywords",
        "strengths": "Strengths",
        "risks": "Risks",
        "edits": "Edits you can paste",
        "interview": "Likely interview questions",
        "honesty": "Honesty check",
        "status": {"met": "met", "partial": "partial", "missing": "missing"},
    },
    "fr": {
        "score": "Correspondance",
        "must": "Exigences indispensables",
        "keywords": "Mots-clés",
        "strengths": "Points forts",
        "risks": "Risques",
        "edits": "Modifications à coller",
        "interview": "Questions d'entretien probables",
        "honesty": "Contrôle d'honnêteté",
        "status": {"met": "couvert", "partial": "partiel", "missing": "manquant"},
    },
}


def render_analysis(data: dict, language: str = "en") -> str:
    t = SECTION.get(language, SECTION["en"])
    lines = [
        f"## 1. {t['score']}",
        f"**{data.get('score', '—')}/100 — {data.get('recommendation', '')}**",
        "",
        data.get("one_line", ""),
        "",
        "| Dimension | Weight | Score | Gap |",
        "|---|---:|---:|---|",
    ]
    for row in data.get("rubric") or []:
        lines.append(
            f"| {row.get('dimension', '')} | {row.get('weight', '')} | {row.get('score', '')} | {row.get('gap', '')} |"
        )
    lines += ["", f"## 2. {t['must']}", ""]
    for item in data.get("must_haves") or []:
        status = t["status"].get(item.get("status"), item.get("status", ""))
        lines.append(f"- **{status}:** {item.get('requirement', '')} — {item.get('evidence', '')}")
    kw = data.get("keywords") or {}
    lines += ["", f"## 3. {t['keywords']}", ""]
    lines.append("- Exact: " + ", ".join(kw.get("exact_matches") or ["—"]))
    syn = [
        f"{s.get('cv_term')} → {s.get('jd_term')}"
        for s in (kw.get("synonyms_already_in_cv") or [])
        if isinstance(s, dict)
    ]
    lines.append("- Already said another way: " + ", ".join(syn or ["—"]))
    lines.append("- Missing exact terms: " + ", ".join(kw.get("missing_exact_terms") or ["—"]))
    lines.append("- Do not add: " + ", ".join(kw.get("do_not_add") or ["—"]))
    lines += ["", f"## 4. {t['strengths']}", ""]
    for item in data.get("strengths") or []:
        lines.append(f"- {item.get('point', '')} ({item.get('evidence', '')})")
    lines += ["", f"## 5. {t['risks']}", ""]
    for item in data.get("risks") or []:
        lines.append(f"- {item.get('point', '')} — {item.get('how_to_handle', '')}")
    lines += ["", f"## 6. {t['edits']}", ""]
    for item in data.get("edits") or []:
        lines.append(f"- **{item.get('section', '')}:** {item.get('rewrite', '')}")
        lines.append(f"  - Why: {item.get('why', '')}")
    lines += ["", f"## 7. {t['interview']}", ""]
    for q in data.get("interview_prompts") or []:
        lines.append(f"- {q}")
    lines += ["", f"## 8. {t['honesty']}", "", str(data.get("honesty_check", "")), ""]
    return "\n".join(lines)


def render_rewrite(data: dict, language: str = "en") -> str:
    title = "Omitted keywords" if language == "en" else "Mots-clés omis"
    changes_title = "What changed" if language == "en" else "Ce qui a changé"
    lines = [data.get("cv_markdown") or ""]
    omitted = data.get("omitted_keywords") or []
    if omitted:
        lines += ["", f"### {title}", ""]
        lines.extend(f"- {item}" for item in omitted)
    changes = data.get("changes") or []
    if changes:
        lines += ["", f"### {changes_title}", ""]
        for item in changes:
            if isinstance(item, dict):
                lines.append(
                    f"- **{item.get('section', '')}:** {item.get('what_changed', '')} ({item.get('source_fact', '')})"
                )
    return "\n".join(lines).strip()
