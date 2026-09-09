"""Generates per-question application strategies (structure, do/don'ts, example answer) from a ClubBrief."""

from __future__ import annotations

import logging
import asyncio

import json
from typing import List, Optional

from ..schemas import ClubBrief, ApplicationSuggestions, model_to_dict
from .llm_utils import call_openai_json


logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You craft strategies for application forms. Return ONLY valid JSON matching exactly: "
    '{"club_rundown": "a 1-3 sentence plain-text summary of the club, as a single string - not an object", '
    '"values_alignment": [{"value": string, "how_to_show_it": string}], '
    '"question_strategies": [{"question": string, "structure": string, "do_donts": string[], '
    '"example_answer": "string, \\u2264150 words"}]}'
)


async def run(brief: ClubBrief, questions: Optional[List[str]], resume_text: str = "") -> ApplicationSuggestions:
    logger.info(f"[ApplicationCoachAgent] start questions_count={(len(questions) if questions else 0)}")
    user_prompt = (
        "ClubBrief:\n" + json.dumps(model_to_dict(brief), indent=2) + "\n\n"
        + "Application questions (if any):\n" + ("\n".join(questions or []) or "(none provided)") + "\n\n"
        + "Applicant experience:\n" + resume_text[:8000] + "\n\n"
        + "Keep examples concise (≤150 words). Use only supplied applicant facts; use placeholders for missing facts and never invent metrics."
    )

    logger.info("[ApplicationCoachAgent] calling LLM for strategies...")
    data = await asyncio.to_thread(call_openai_json, SYSTEM_PROMPT, user_prompt)
    if data:
        try:
            return ApplicationSuggestions(**data)
        except Exception as e:
            logger.warning(f"[ApplicationCoachAgent] LLM JSON parse failed ({e}), using fallback")

    # Fallback
    values_alignment = [
        {"value": v, "how_to_show_it": "Show measurable impact, teamwork, and initiative in relevant stories."}
        for v in (brief.mission_values or [])[:3]
    ]
    qs = questions or [
        "Why this club?",
        "Describe a relevant project.",
    ]
    question_strategies = []
    for q in qs:
        question_strategies.append(
            {
                "question": q,
                "structure": "Context → Action → Result → Reflection",
                "do_donts": ["Do quantify", "Do align with what_matters_most", "Don't be generic"],
                "example_answer": "I joined X to tackle Y. I led Z action, resulting in A% improvement. This taught me B, which aligns with C."
            }
        )

    logger.info("[ApplicationCoachAgent] using heuristic fallback")
    return ApplicationSuggestions(
        club_rundown=brief.overview,
        values_alignment=values_alignment,
        question_strategies=question_strategies,
    )
