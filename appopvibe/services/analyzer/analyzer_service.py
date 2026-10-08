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
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Model did not return JSON")
        blob = text[start:end + 1]
        blob = re.sub(r",\s*([}\]])", r"\1", blob)
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return json.loads(blob, strict=False)

    async def analyze_cv_jd(self, cv_text: str, jd_text: str, language: str = "en") -> str:
        self.logger.info(
            "Analyzing CV (%s chars) against JD (%s chars) in %s",
            len(cv_text), len(jd_text), language,
        )
        raw = await self.llm_service.generate(
            prompt=self.prompt_templates["analysis"].format(cv=cv_text, jd=jd_text),
            system=self.prompt_templates["system"],
            temperature=0.2,
            max_tokens=1400,
            json_mode=True,
        )
        if raw.startswith("Error:"):
            return raw
        try:
            data = self._parse_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            self.logger.warning("Analysis JSON failed: %s", exc)
            return raw
        rendered = render_analysis(data, language)
        self.logger.info("Analysis completed, score=%s", data.get("score"))
        return rendered

    async def rewrite_cv(self, cv_text: str, jd_text: str, language: str = "en") -> str:
        self.logger.info("Rewriting CV in %s", language)
        raw = await self.llm_service.generate(
            prompt=self.prompt_templates["rewrite"].format(cv=cv_text, jd=jd_text),
            system=self.prompt_templates["rewrite_system"],
            temperature=0.3,
            max_tokens=1200,
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
