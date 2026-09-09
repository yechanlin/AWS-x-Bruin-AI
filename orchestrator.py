"""Runs the six-stage pipeline end to end (parallel research -> ClubBrief -> parallel coaching) and assembles the FinalReport; shared by the CLI and the /clubapply/run endpoint."""

from __future__ import annotations

import logging

import asyncio
from datetime import datetime
from typing import Optional

from .schemas import (
    InputSpec,
    FinalReport,
    InstagramFindings,
    WebsiteFindings,
)
from .agents import (
    instagram_agent,
    website_agent,
    summarizer_agent,
    resume_tailor,
    application_coach,
    interview_coach,
)

logger = logging.getLogger(__name__)


async def run_clubapply(input_data: InputSpec) -> FinalReport:
    logger.info("[Orchestrator] Launching IG + Web tasks in parallel")
    ig_task = instagram_agent.run(input_data.instagramUrl, is_online=input_data.isOnline)
    web_task = website_agent.run(input_data.websiteUrl, is_online=input_data.isOnline)

    ig_res: Optional[InstagramFindings]
    web_res: Optional[WebsiteFindings]

    ig_res, web_res = await asyncio.gather(ig_task, web_task)
    logger.info("[Orchestrator] Received IG + Web outputs")

    logger.info("[Orchestrator] Running summarizer agent")
    summary = await summarizer_agent.run((ig_res, web_res))

    logger.info("[Orchestrator] Running resume, application, and interview stages in parallel")
    resume, application, interview = await asyncio.gather(
        resume_tailor.run(summary, input_data.resumePath, input_data.clubName, input_data.schoolName),
        application_coach.run(summary, input_data.applicationQuestions),
        interview_coach.run(summary),
    )

    ts = datetime.utcnow().isoformat()
    report = FinalReport(
        input=input_data,
        instagram=ig_res,
        website=web_res,
        brief=summary,
        resume=resume,
        application=application,
        interview=interview,
        timestamp=ts,
    )
    logger.info("[Orchestrator] Aggregation complete, returning FinalReport")
    return report
