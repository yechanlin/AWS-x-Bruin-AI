"""Generates interview prep (likely questions, stories, pitch template) from a ClubBrief, plus InterviewChat, an interactive REPL helper used by the CLI's --chat mode."""

from __future__ import annotations

import logging
import asyncio

import json
from typing import List

from ..schemas import ClubBrief, InterviewPrep, model_to_dict
from .llm_utils import call_openai_json


logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You simulate a realistic interview. Return JSON: {similar_experiences_summary, likely_questions[], "
    "stories_to_prepare[], quick_pitch_template, followup_questions[], links[]}"
)


async def run(brief: ClubBrief, resume_text: str = "") -> InterviewPrep:
    logger.info("[InterviewCoachAgent] start generating prep")
    user_prompt = (
        "ClubBrief:\n" + json.dumps(model_to_dict(brief), indent=2) + "\n\n"
        + "Applicant experience:\n" + resume_text[:8000] + "\n\n"
        + "Generate likely questions, short pitch template, and useful links. Do not invent applicant experiences; use placeholders for missing facts."
    )

    logger.info("[InterviewCoachAgent] calling LLM for interview prep...")
    data = await asyncio.to_thread(call_openai_json, SYSTEM_PROMPT, user_prompt)
    if data:
        try:
            return InterviewPrep(**data)
        except Exception as e:
            logger.warning(f"[InterviewCoachAgent] LLM JSON parse failed ({e}), using fallback")

    # Fallback
    likely_questions: List[str] = [
        "Walk me through a project relevant to our club.",
        "Why this club at this school?",
        "Tell me about a time you led a team.",
        "How would you contribute in your first semester?",
        "What events or initiatives would you propose?",
    ]
    stories_to_prepare = [
        "Leadership under ambiguity",
        "Impact with measurable results",
        "Collaboration and conflict resolution",
    ]
    quick_pitch_template = (
        "Hi, I'm [Name], a [Year/Major]. I care about [Mission-aligned theme]. "
        "I led [Project] that achieved [Metric]. I'd bring [Skill/Initiative] to [Club]."
    )
    followup_questions = [
        "What does success look like for new members?",
        "How do teams choose projects and measure outcomes?",
        "What mentorship or training is available?",
    ]
    logger.info("[InterviewCoachAgent] using heuristic fallback")
    return InterviewPrep(
        similar_experiences_summary="Prepare 2–3 stories mapped to what_matters_most.",
        likely_questions=likely_questions,
        stories_to_prepare=stories_to_prepare,
        quick_pitch_template=quick_pitch_template,
        followup_questions=followup_questions,
        links=[],
    )


class InterviewChat:
    def __init__(self, club_name: str, school_name: str, brief: ClubBrief):
        self.club_name = club_name
        self.school_name = school_name
        self.brief = brief
        self.history = []  # list of (role, content)

    def chat(self, user_input: str) -> str:
        system = (
            f"You simulate a realistic interview for {self.club_name} at {self.school_name}. "
            "Keep responses succinct and probing."
        )
        # Build conversation
        conv = "\n".join([f"{r.upper()}: {c}" for r, c in self.history[-6:]])
        user_prompt = (
            "ClubBrief:\n" + json.dumps(model_to_dict(self.brief), indent=2) + "\n\n"
            + f"Conversation so far:\n{conv}\n\n"
            + f"User: {user_input}\nAssistant:"
        )
        logger.info("[InterviewChat] LLM chat turn")
        data = call_openai_json(system, user_prompt)
        if data is not None:
            # If the model returned JSON, flatten to text
            reply = str(data)
        else:
            # No JSON expected here; try a simple flow with heuristics
            reply = (
                "Thanks — tell me about a time you drove measurable impact. "
                "What was the context, what did you do, and what changed?"
            )
        logger.info("[InterviewChat] reply ready")
        self.history.append(("user", user_input))
        self.history.append(("assistant", reply))
        return reply
