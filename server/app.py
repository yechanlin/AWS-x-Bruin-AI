"""FastAPI app exposing the agent pipeline over HTTP: resume upload, per-agent debug endpoints, the live UI's /agents/application-coach, and the full /clubapply/run pipeline."""

from __future__ import annotations

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..schemas import (
    InputSpec,
    InstagramFindings,
    WebsiteFindings,
    ClubBrief,
    FinalReport,
    model_to_dict,
)
from ..agents import instagram_agent, website_agent, summarizer_agent, resume_tailor, application_coach, interview_coach
from ..orchestrator import run_clubapply
from ..agents.llm_utils import call_llm_json
from ..tools.pdf_reader import read_pdf_text
from ..logging_config import setup_logging

# Load provider API keys from .env at the repo root before anything reads them.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
setup_logging("backend.log")

app = FastAPI(title="ClubApply Strands API", version="0.1.0")

# Defaults to "*" so local dev works with no config. Set ALLOWED_ORIGINS to a
# comma-separated list (e.g. the deployed frontend's URL) for any public
# deployment. Note this only constrains browsers - it is not access control;
# direct callers (curl, scripts) ignore CORS entirely.
_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    provider = (os.getenv("LLM_PROVIDER") or "").lower().strip()
    configured = provider not in {"offline", "none"} and (
        bool(provider) or any(os.getenv(key) for key in ["OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "AWS_PROFILE", "AWS_ACCESS_KEY_ID"])
    )
    return {"ok": True, "model_mode": "configured" if configured else "offline"}


@app.post("/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    """Extract resume text in-memory and return it directly - no server-side
    file is written or persisted, so this works the same whether the next
    request (which needs that text) lands on this same process or, on a
    serverless deployment, a completely different one."""
    filename = file.filename or "resume.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF resumes are supported.")
    content = await file.read(5 * 1024 * 1024 + 1)
    await file.close()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Resume must be smaller than 5 MB.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(400, "This file is not a valid PDF.")
    text = await asyncio.to_thread(read_pdf_text, content, 3)
    if not text or text.startswith("PDF_READ_ERROR:"):
        raise HTTPException(400, "Could not extract resume text. Use a text-based PDF or enter your details manually.")
    return {"resume_text": text[:16000], "name": filename}


class InstagramReq(BaseModel):
    profile_url: str
    online: Optional[bool] = True


@app.post("/agents/instagram-analyzer")
async def instagram_analyzer(req: InstagramReq):
    res = await instagram_agent.run(req.profile_url, is_online=bool(req.online))
    return model_to_dict(res)


class WebsiteReq(BaseModel):
    website_url: str
    online: Optional[bool] = True


@app.post("/agents/website-analyzer")
async def website_analyzer(req: WebsiteReq):
    res = await website_agent.run(req.website_url, is_online=bool(req.online))
    return model_to_dict(res)


class SummarizerReq(BaseModel):
    instagram: Optional[Dict[str, Any]] = None
    website: Optional[Dict[str, Any]] = None
    content: Optional[str] = None


@app.post("/agents/summarizer")
async def summarizer(req: SummarizerReq):
    # If IG/Web provided, use the core summarizer_agent
    if req.instagram is not None and req.website is not None:
        ig = InstagramFindings(**req.instagram)
        web = WebsiteFindings(**req.website)
        brief = await summarizer_agent.run((ig, web))
        return model_to_dict(brief)
    # Otherwise, accept raw content and summarize via LLM
    if req.content:
        system = (
            "Summarize the content into: {overview, mission_values[], what_they_look_for[], "
            "sample_events[], keywords[], what_matters_most[5]} as JSON."
        )
        data = await asyncio.to_thread(call_llm_json, system, req.content)
        if data:
            try:
                return ClubBrief(**data).dict()
            except Exception:
                pass
        # Fallback minimal brief
        return ClubBrief(
            overview=req.content[:400],
            mission_values=[],
            what_they_look_for=["initiative", "teamwork", "communication"],
            sample_events=[],
            keywords=[],
            what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
        ).dict()
    return {"error": "Provide instagram+website or content"}


class ResumeTailorReq(BaseModel):
    resume_path: str
    job_description: Optional[str] = None
    club_name: Optional[str] = None
    school_name: Optional[str] = None


@app.post("/agents/resume-tailor")
async def resume_tailor_ep(req: ResumeTailorReq):
    # Build a lightweight brief from job description if provided
    if req.job_description:
        brief = ClubBrief(
            overview=req.job_description[:400],
            mission_values=[],
            what_they_look_for=["initiative", "relevant experience", "teamwork"],
            sample_events=[],
            keywords=[],
            what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
        )
    else:
        brief = ClubBrief(
            overview="Tailored resume suggestions",
            mission_values=[],
            what_they_look_for=["initiative", "relevant experience", "teamwork"],
            sample_events=[],
            keywords=[],
            what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
        )
    res = await resume_tailor.run(
        brief, req.resume_path, req.club_name or "Club", req.school_name or "School"
    )
    return model_to_dict(res)


class InterviewCoachReq(BaseModel):
    club_name: str
    school_name: str
    job_description: Optional[str] = None


@app.post("/agents/interview-coach")
async def interview_coach_ep(req: InterviewCoachReq):
    brief = ClubBrief(
        overview=req.job_description or f"Interview prep for {req.club_name} at {req.school_name}",
        mission_values=[],
        what_they_look_for=["initiative", "teamwork", "communication"],
        sample_events=[],
        keywords=[],
        what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
    )
    res = await interview_coach.run(brief)
    return model_to_dict(res)


class ApplicationCoachReq(BaseModel):
    job_description: Optional[str] = None
    questions: Optional[List[str]] = None
    # Optional signals to enrich the brief
    website_url: Optional[str] = None
    instagram_url: Optional[str] = None
    # Optional resume path to tailor suggestions; if omitted, generic edits are returned
    resume_path: Optional[str] = None
    resume_text: Optional[str] = Field(default=None, max_length=16000)
    include_interview: bool = False
    club_name: Optional[str] = None
    school_name: Optional[str] = None


@app.post("/agents/application-coach")
async def application_coach_ep(req: ApplicationCoachReq):
    # Try to enrich the brief using website/instagram if available
    web_findings: Optional[WebsiteFindings] = None
    ig_findings: Optional[InstagramFindings] = None

    # Heuristically parse a website URL from job_description if not explicitly provided
    website_url = req.website_url
    if not website_url and req.job_description:
        import re as _re
        m = _re.search(r"https?://[^\s]+", req.job_description)
        if m:
            website_url = m.group(0)

    # Independent sources overlap; preserve a usable result if one source fails.
    web_result, ig_result = await asyncio.gather(
        website_agent.run(website_url, is_online=True),
        instagram_agent.run(req.instagram_url, is_online=True),
        return_exceptions=True,
    )
    web_findings = web_result if isinstance(web_result, WebsiteFindings) else None
    ig_findings = ig_result if isinstance(ig_result, InstagramFindings) else None

    if website_url or req.instagram_url:
        # Use summarizer to create a better ClubBrief
        ig_model = ig_findings or InstagramFindings()
        web_model = web_findings or WebsiteFindings()
        brief = await summarizer_agent.run((ig_model, web_model))
    else:
        # Minimal brief from provided description
        brief = ClubBrief(
            overview=req.job_description or "Application strategies",
            mission_values=[],
            what_they_look_for=["initiative", "teamwork", "communication"],
            sample_events=[],
            keywords=[],
            what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
        )

    resume_text = req.resume_text or ""
    if req.resume_path:
        resume_text = await asyncio.to_thread(read_pdf_text, req.resume_path, max_pages=3)
        if not resume_text or resume_text.startswith("PDF_READ_ERROR:"):
            raise HTTPException(400, "Could not read the resume. Upload a text-based PDF again.")

    tasks = [
        application_coach.run(brief, req.questions or [], resume_text=resume_text),
        resume_tailor.run(brief, req.resume_path or "__NO_FILE__",
                          req.club_name or "Club", req.school_name or "School", resume_text=resume_text),
    ]
    if req.include_interview:
        tasks.append(interview_coach.run(brief, resume_text=resume_text))
    results = await asyncio.gather(*tasks)
    app_suggestions, resume_suggestions = results[:2]
    warnings = []
    if (await health())["model_mode"] == "offline":
        warnings.append("Offline demo: these are generic templates, not AI-generated personalized recommendations.")
    if not website_url and not req.instagram_url:
        warnings.append("No club sources supplied; guidance uses your description only.")
    for source, result in [("Website", web_result), ("Instagram", ig_result)]:
        if isinstance(result, Exception):
            warnings.append(f"{source} research failed; available information was used.")
        else:
            warnings.extend(f"{source}: {warning}" for warning in result.warnings)
    if not resume_text:
        warnings.append("No resume content supplied; resume advice is generic.")

    # Compose response ensuring the three requested sections are explicit
    resp = {
        "warnings": warnings,
        "interview": model_to_dict(results[2]) if req.include_interview else None,
        "club": {
            "overview": brief.overview,
            "mission_values": brief.mission_values,
            "what_matters_most": brief.what_matters_most,
        },
        "answers": [
            {
                "question": qs.get("question"),
                "structure": qs.get("structure"),
                "do_donts": qs.get("do_donts"),
                "example_answer": qs.get("example_answer"),
            }
            for qs in (app_suggestions.question_strategies or [])
        ],
        "resume": model_to_dict(resume_suggestions),
        # include original application suggestions for compatibility with existing UI
        "application": model_to_dict(app_suggestions),
        "brief": model_to_dict(brief),
    }
    return resp


@app.post("/clubapply/run")
async def clubapply_run(spec: InputSpec):
    report = await run_clubapply(spec)
    return model_to_dict(report)
