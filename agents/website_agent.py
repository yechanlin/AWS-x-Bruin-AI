"""Crawls a club's website (same-domain, up to 5 pages) and asks the LLM to extract WebsiteFindings, falling back to keyword heuristics when no model is available."""

from __future__ import annotations

import asyncio
import logging

from typing import Optional, List

from ..schemas import WebsiteFindings
from ..tools.fetch_url import crawl_website
from .llm_utils import call_openai_json

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You read a club website. Return JSON: {about, mission_values[], how_to_join, "
    "events[], criteria[], links[], keywords[], warnings[]}. "
    "Only report facts actually present in the provided text - dates, legal status, "
    "GPA/experience requirements, meeting times, and similar specifics must not be "
    "invented. If a field isn't clearly supported by the text, return an empty "
    "array (or empty string) for it rather than guessing - never null."
)


async def run(website_url: Optional[str], is_online: bool = True) -> WebsiteFindings:
    logger.info(f"[WebsiteAgent] start url={website_url} online={is_online}")
    if not website_url:
        return WebsiteFindings(warnings=["No website URL provided."])

    combined_text = ""
    links: List[str] = []
    if is_online:
        logger.info("[WebsiteAgent] crawling website up to 5 pages...")
        combined_text, links = await asyncio.to_thread(crawl_website, website_url, max_pages=5)

    user_prompt = (
        f"URL: {website_url}\n\n"
        f"Pages crawled: {len(links)}\n\n"
        f"Text (truncated):\n{combined_text[:8000]}\n\n"
        "Find About/Mission, joining info, events, criteria, links, and keywords."
    )

    logger.info("[WebsiteAgent] calling LLM for JSON parse...")
    data = await asyncio.to_thread(call_openai_json, SYSTEM_PROMPT, user_prompt)
    if data:
        try:
            if "links" not in data:
                data["links"] = links
            return WebsiteFindings(**data)
        except Exception as e:
            logger.warning(f"[WebsiteAgent] LLM JSON parse failed ({e}), using fallback")

    # Heuristic fallback parsing
    logger.info("[WebsiteAgent] using heuristic fallback")
    about = None
    mission_values: List[str] = []
    how_to_join = None
    events: List[str] = []
    criteria: List[str] = []
    keywords: List[str] = []
    warnings: List[str] = []

    if not combined_text:
        warnings.append("No website content fetched.")
    else:
        tl = combined_text.lower()
        if "mission" in tl or "about" in tl:
            about = "Club site mentions About and Mission sections."
        if "apply" in tl or "join" in tl or "recruit" in tl:
            how_to_join = "See website for application or join instructions."
        if "workshop" in tl or "info session" in tl or "recruitment" in tl:
            events.append("Workshops or recruitment events")
        if "gpa" in tl or "experience" in tl or "requirements" in tl:
            criteria.append("Experience or GPA requirements may apply")
        if "project" in tl:
            keywords.append("projects")
        if "mentorship" in tl:
            keywords.append("mentorship")

    return WebsiteFindings(
        about=about,
        mission_values=mission_values,
        how_to_join=how_to_join,
        events=events,
        criteria=criteria,
        links=links,
        keywords=list(set(keywords)),
        warnings=warnings,
    )
