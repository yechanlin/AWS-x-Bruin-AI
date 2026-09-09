"""Extracts resume PDF text and asks the LLM for tailored bullet/fix suggestions scored against a ClubBrief."""

from __future__ import annotations

import logging
import asyncio

import json
from typing import Optional

from ..schemas import ClubBrief, ResumeSuggestions, model_to_dict
from ..tools.pdf_reader import read_pdf_text
from .llm_utils import call_openai_json


logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a strict resume reviewer. Given ClubBrief and resume text, never invent applicant achievements or metrics; use placeholders where facts are missing. "
    "Return JSON: {top5_fixes[], tailored_bullets[], format_warnings[], ATS_suggestions[]}"
)


async def run(brief: ClubBrief, resume_path: str, club_name: Optional[str] = None, school_name: Optional[str] = None, resume_text: Optional[str] = None) -> ResumeSuggestions:
    logger.info(f"[ResumeTailorAgent] start resume_path={resume_path}")
    if resume_text is None:
        resume_text = await asyncio.to_thread(read_pdf_text, resume_path, max_pages=3)

    sys = SYSTEM_PROMPT.replace("You are a strict resume reviewer.", f"You are a strict resume reviewer for {club_name or 'the club'} at {school_name or 'the school'}.")
    user_prompt = (
        "ClubBrief:\n" + json.dumps(model_to_dict(brief), indent=2) + "\n\n"
        + "Resume text (first pages):\n" + resume_text[:8000] + "\n\n"
        + "Provide concrete bullet suggestions tailored to the club's keywords and what_matters_most."
    )

    logger.info("[ResumeTailorAgent] calling LLM for tailored suggestions...")
    data = await asyncio.to_thread(call_openai_json, sys, user_prompt)
    if data:
        try:
            # Ensure capped lengths
            data["top5_fixes"] = (data.get("top5_fixes") or [])[:5]
            data["tailored_bullets"] = (data.get("tailored_bullets") or [])[:8]
            return ResumeSuggestions(**data)
        except Exception as e:
            logger.warning(f"[ResumeTailorAgent] LLM JSON parse failed ({e}), using fallback")

    # Fallback
    bullets = []
    for kw in (brief.keywords or [])[:5]:
        bullets.append(f"Drove a {kw}-focused project delivering measurable outcomes (e.g., metrics, quality, time).")
    top5 = [
        "Quantify impact in each bullet (numbers, %).",
        "Front-load action verbs and outcomes.",
        "Prioritize club-relevant projects near top.",
        "Tighten formatting to one page (10–11pt).",
        "Ensure consistent tense and punctuation.",
    ]
    logger.info("[ResumeTailorAgent] using heuristic fallback")
    return ResumeSuggestions(
        top5_fixes=top5,
        tailored_bullets=bullets,
        format_warnings=["Check margins, alignment, and consistent section headers."],
        ATS_suggestions=["Use standard headings; avoid images/tables that break parsing."]
    )
