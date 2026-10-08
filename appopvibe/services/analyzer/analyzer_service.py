"""
CV analyzer service that processes CVs and job descriptions.
"""
import json
import logging
import re
from typing import Any, Dict

from appopvibe.services.llm.llm_service import LLMService
from appopvibe.services.report.render_analysis import render_analysis, render_rewrite, render_letter


class AnalyzerService:
    """Service for analyzing CV and job description matches."""

    def __init__(self, llm_service: LLMService, prompt_templates: Dict[str, str]):
        self.llm_service = llm_service
        self.prompt_templates = prompt_templates
        self.logger = logging.getLogger(__name__)

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        text = (raw or "").strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        if start == -1:
            raise ValueError("Model did not return JSON")
        blob = text[start:]
        blob = re.sub(r",\s*([}\]])", r"\1", blob)
        blob = _close_json(blob)
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return json.loads(blob, strict=False)

    async def _ask(self, prompt: str, system: str, max_tokens: int) -> Dict[str, Any]:
        raw = await self.llm_service.generate(
            prompt=prompt,
            system=system,
            temperature=0.2,
            max_tokens=max_tokens,
            json_mode=True,
        )
        if raw.startswith("Error:"):
            return {"error": raw, "raw": raw}
        try:
            data = self._parse_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            self.logger.warning("JSON failed: %s", exc)
            return {"error": raw, "raw": raw}
        if not isinstance(data, dict):
            return {"error": raw, "raw": raw}
        data["raw"] = raw
        return data


    def _salvage_score(self, raw: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        score = re.search(r'"score"\s*:\s*(\d+)', raw)
        advice = re.search(r'"recommendation"\s*:\s*"([^"]*)"', raw)
        line = re.search(r'"oneline"\s*:\s*"([^"]*)"', raw) or re.search(r'"one_line"\s*:\s*"([^"]*)"', raw)
        if score:
            data["score"] = int(score.group(1))
        if advice:
            data["recommendation"] = advice.group(1)
        if line:
            data["one_line"] = line.group(1)
        rows = []
        for dim, weight, row_score, gap in re.findall(
            r'"dimension"\s*:\s*"([^"]*)".*?"weight"\s*:\s*(\d+).*?"score"\s*:\s*(\d+).*?"gap"\s*:\s*"([^"]*)"',
            raw,
            flags=re.S,
        ):
            rows.append({"dimension": dim, "weight": int(weight), "score": int(row_score), "gap": gap})
        if rows:
            data["rubric"] = rows
        return data

    def _score_from_rubric(self, data: Dict[str, Any]) -> None:
        rows = [row for row in data.get("rubric") or [] if isinstance(row, dict)]
        weights = [float(row.get("weight") or 0) for row in rows]
        scores = [float(row.get("score") or 0) for row in rows]
        total = sum(weights)
        if total:
            data["score"] = round(sum(w * s for w, s in zip(weights, scores)) / total)

    async def analyze_cv_jd(self, cv_text: str, jd_text: str, language: str = "en") -> str:
        self.logger.info("Scoring CV (%s chars) against JD (%s chars)", len(cv_text), len(jd_text))
        lang = "French" if language == "fr" else "English"
        score = await self._ask(
            f"Score this CV against this job description. Respond in {lang}. "
            "Use only stated facts. Return JSON with score, recommendation "
            "(strong_match, possible_match, weak_match, do_not_apply_yet), one_line, "
            "and rubric rows for must_have_skills, domain, seniority, impact, keywords. "
            "Each row has dimension, weight, score 0-100, evidence, gap. "
            "Weights must sum to 100. Absent is not stated, not proof of a missing skill.\n\n"
            f"<cv>\n{cv_text}\n</cv>\n<job_description>\n{jd_text}\n</job_description>",
            self.prompt_templates["system"],
            900,
        )
        if not (score.get("score") or score.get("rubric") or score.get("one_line") or score.get("oneline")):
            salvaged = self._salvage_score(score.get("raw") or "")
            if not salvaged.get("score"):
                return score.get("raw") or score.get("error") or "The model did not return a score."
            score = salvaged
        if not score.get("one_line"):
            score["one_line"] = score.get("oneline") or score.get("oneLine") or ""
        self._score_from_rubric(score)
        details = await self._ask(
            "Using the same CV and job description, return JSON with must_haves, keywords, "
            "strengths, risks, edits, interview_prompts, honesty_check. Keep each list to 4 items. "
            f"Respond in {lang}. Do not invent facts.\n\n"
            f"<cv>\n{cv_text}\n</cv>\n<job_description>\n{jd_text}\n</job_description>",
            self.prompt_templates["system"],
            900,
        )
        if not details.get("error"):
            score.update({k: v for k, v in details.items() if k != "score"})
        try:
            rendered = render_analysis(score, language)
        except Exception as exc:
            self.logger.exception("Render failed: %s", exc)
            return score.get("raw") or str(score)
        self.logger.info("Analysis completed, score=%s", score.get("score"))
        return rendered

    async def rewrite_cv(self, cv_text: str, jd_text: str, language: str = "en") -> str:
        self.logger.info("Rewriting CV in %s", language)
        raw = await self.llm_service.generate(
            prompt=self.prompt_templates["rewrite"].format(cv=cv_text, jd=jd_text),
            system=self.prompt_templates["rewrite_system"],
            temperature=0.3,
            max_tokens=1600,
            json_mode=True,
        )
        if raw.startswith("Error:"):
            return raw
        try:
            data = self._parse_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            self.logger.warning("Rewrite JSON failed: %s", exc)
            return raw
        rendered = render_rewrite(data, language)
        self.logger.info("CV rewriting completed, result length: %s", len(rendered))
        return rendered

    async def draft_letter(self, cv_text: str, jd_text: str, language: str = "en") -> str:
        self.logger.info("Drafting cover letter in %s", language)
        raw = await self.llm_service.generate(
            prompt=self.prompt_templates["letter"].format(cv=cv_text, jd=jd_text),
            system=self.prompt_templates["letter_system"],
            temperature=0.4,
            max_tokens=1200,
            json_mode=True,
        )
        if raw.startswith("Error:"):
            return raw
        try:
            data = self._parse_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            self.logger.warning("Letter JSON failed: %s", exc)
            return raw
        rendered = render_letter(data, language)
        self.logger.info("Cover letter completed, result length: %s", len(rendered))
        return rendered

    async def process_submission(
        self, cv_text: str, jd_text: str, language: str = "en",
        rewrite: bool = False, cover_letter: bool = False,
    ) -> Dict[str, str]:
        self.logger.info("Processing submission (rewrite=%s, letter=%s)", rewrite, cover_letter)
        import asyncio
        result = {"analysis": await self.analyze_cv_jd(cv_text, jd_text, language)}
        if rewrite:
            await asyncio.sleep(2)
            result["rewritten_cv"] = await self.rewrite_cv(cv_text, jd_text, language)
        if cover_letter:
            await asyncio.sleep(2)
            result["cover_letter"] = await self.draft_letter(cv_text, jd_text, language)
        return result

def _close_json(blob: str) -> str:
    """Close a reply that was cut off by the token limit."""
    out = []
    stack = []
    in_string = False
    escape = False
    for ch in blob:
        out.append(ch)
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack:
            stack.pop()
    if in_string:
        out.append('"')
    out.append("".join(reversed(stack)))
    return "".join(out)
