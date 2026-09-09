"""Fuses InstagramFindings and WebsiteFindings into one ClubBrief - the shared context every downstream coaching stage consumes."""

from __future__ import annotations

import logging
import asyncio

import json
from typing import Tuple

from ..schemas import InstagramFindings, WebsiteFindings, ClubBrief, model_to_dict
from .llm_utils import call_openai_json


logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Merge InstagramFindings + WebsiteFindings into a ClubBrief. "
    "Return ONLY valid JSON, no markdown or prose, matching exactly: "
    '{"overview": string, "mission_values": string[], "what_they_look_for": string[], '
    '"sample_events": string[], "keywords": string[], "what_matters_most": string[5]}. '
    "Only synthesize from facts already present in the two findings objects - do not "
    "add specifics (dates, numbers, names) that aren't supported by them; "
    "what_they_look_for and what_matters_most may be reasonable inferences, but "
    "overview/mission_values/sample_events must not invent new facts."
)


async def run(results: Tuple[InstagramFindings, WebsiteFindings]) -> ClubBrief:
    logger.info("[SummarizerAgent] start: merging IG + Web findings")
    ig, web = results

    user_prompt = (
        "InstagramFindings:\n" + json.dumps(model_to_dict(ig), indent=2) + "\n\n"
        + "WebsiteFindings:\n" + json.dumps(model_to_dict(web), indent=2) + "\n\n"
        + "Fuse to a concise ClubBrief."
    )

    logger.info("[SummarizerAgent] calling LLM to fuse findings...")
    data = await asyncio.to_thread(call_openai_json, SYSTEM_PROMPT, user_prompt)
    if data:
        try:
            # Ensure exactly 5 items in what_matters_most if possible
            wmm = data.get("what_matters_most", [])
            if len(wmm) > 5:
                data["what_matters_most"] = wmm[:5]
            elif len(wmm) < 5:
                data["what_matters_most"] = wmm + ["impact", "initiative", "teamwork", "quality", "fit"][: 5 - len(wmm)]
            return ClubBrief(**data)
        except Exception as e:
            logger.warning(f"[SummarizerAgent] LLM JSON parse failed ({e}), using fallback")

    # Fallback deterministic merge
    keywords = list({*(ig.keywords or []), *(web.keywords or [])})
    overview = "A student organization with public outreach and events."
    mission_values = (web.mission_values or [])[:3]
    what_they_look_for = [
        "Demonstrated initiative",
        "Interest in the club's domain",
        "Team collaboration",
    ]
    sample_events = (web.events or [])[:5]
    what_matters_most = [
        "commitment",
        "relevant experience",
        "teamwork",
        "communication",
        "fit with mission",
    ]

    logger.info("[SummarizerAgent] using heuristic fallback")
    return ClubBrief(
        overview=overview,
        mission_values=mission_values,
        what_they_look_for=what_they_look_for,
        sample_events=sample_events,
        keywords=keywords,
        what_matters_most=what_matters_most,
    )
