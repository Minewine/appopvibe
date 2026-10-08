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
        if not isinstance(row, dict):
            lines.append(f"| {row} |  |  |  |")
            continue
        lines.append(
            f"| {row.get('dimension', '')} | {row.get('weight', '')} | {row.get('score', '')} | {row.get('gap', '')} |"
        )
    lines += ["", f"## 2. {t['must']}", ""]
    for item in data.get("must_haves") or []:
        if not isinstance(item, dict):
            lines.append(f"- {item}")
            continue
        status = t["status"].get(item.get("status"), item.get("status", ""))
        lines.append(f"- **{status}:** {item.get('requirement', '')} — {item.get('evidence', '')}")
    kw = data.get("keywords") or {}
    if isinstance(kw, list):
        kw = {"exact_matches": [str(item) for item in kw]}
    if isinstance(kw, dict) and any(kw.get(key) for key in ("exact_matches", "synonyms_already_in_cv", "missing_exact_terms", "do_not_add")):
        lines += ["", f"## 3. {t['keywords']}", ""]
        exact = kw.get("exact_matches") or ["—"]
        if isinstance(exact, str):
            exact = [exact]
        lines.append("- Exact: " + ", ".join(str(item) for item in exact))
        syn = [
            f"{s.get('cv_term')} → {s.get('jd_term')}"
            for s in (kw.get("synonyms_already_in_cv") or [])
            if isinstance(s, dict)
        ]
        lines.append("- Already said another way: " + ", ".join(syn or ["—"]))
        missing = kw.get("missing_exact_terms") or ["—"]
        banned = kw.get("do_not_add") or ["—"]
        lines.append("- Missing exact terms: " + ", ".join(str(item) for item in (missing if isinstance(missing, list) else [missing])))
        lines.append("- Do not add: " + ", ".join(str(item) for item in (banned if isinstance(banned, list) else [banned])))
    strengths = data.get("strengths") or []
    if strengths:
        lines += ["", f"## 4. {t['strengths']}", ""]
        for item in strengths:
            if isinstance(item, dict):
                lines.append(f"- {item.get('point', '')} ({item.get('evidence', '')})")
            else:
                lines.append(f"- {item}")
    risks = data.get("risks") or []
    if risks:
        lines += ["", f"## 5. {t['risks']}", ""]
        for item in risks:
            if isinstance(item, dict):
                lines.append(f"- {item.get('point', '')} — {item.get('how_to_handle', '')}")
            else:
                lines.append(f"- {item}")
    edits = data.get("edits") or []
    if edits:
        lines += ["", f"## 6. {t['edits']}", ""]
        for item in edits:
            if isinstance(item, dict):
                lines.append(f"- **{item.get('section', '')}:** {item.get('rewrite', '')}")
                lines.append(f"  - Why: {item.get('why', '')}")
            else:
                lines.append(f"- {item}")
    questions = data.get("interview_prompts") or []
    if questions:
        lines += ["", f"## 7. {t['interview']}", ""]
        for q in questions:
            lines.append(f"- {q}")
    if data.get("honesty_check"):
        lines += ["", f"## 8. {t['honesty']}", "", str(data.get("honesty_check")), ""]
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


def render_letter(data: dict, language: str = "en") -> str:
    subject_label = "Subject" if language == "en" else "Objet"
    facts_label = "Facts used" if language == "en" else "Faits utilisés"
    omitted_label = "Not claimed" if language == "en" else "Non revendiqué"
    lines = [f"**{subject_label}:** {data.get('subject', '')}", "", data.get("letter") or ""]
    facts = data.get("facts_used") or []
    if facts:
        lines += ["", f"### {facts_label}", ""]
        lines.extend(f"- {item}" for item in facts)
    omitted = data.get("requirements_not_claimed") or []
    if omitted:
        lines += ["", f"### {omitted_label}", ""]
        lines.extend(f"- {item}" for item in omitted)
    return "\n".join(lines).strip()
