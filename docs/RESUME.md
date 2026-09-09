# Resume bullets and interview preparation

## Suggested resume entry

**ClubApply | AWS × Bruin AI Hackathon, UCLA**  
Python, FastAPI, React, AWS Bedrock, Pydantic

- Built a full-stack club application assistant using React and FastAPI, combining public club research and PDF resume analysis to generate application strategies, resume feedback, and interview preparation.
- Designed a six-stage AI workflow that transforms website and Instagram findings into a shared, validated club brief for specialized resume, application, and interview coaching.
- Implemented model-provider adapters for AWS Bedrock, OpenAI, and Gemini, with structured JSON validation and heuristic fallbacks for unavailable or invalid model responses.

These describe repository capabilities. If teammates owned some components, adjust “built,” “designed,” and “implemented” to reflect your contribution. Name AWS Bedrock prominently only if you can explain its adapter and distinguish implemented integration from a verified live demo or deployment.

## Optional bullet after understanding the polish changes

- Optimized independent research and coaching stages with concurrent execution and worker-thread offloading, adding regression tests for concurrency, provider routing, crawler behavior, and offline report generation.

Choose three bullets total for a typical resume. For backend roles, replace the broad second bullet with the optimization bullet once you can explain and defend the change. For AI roles, emphasize shared context, validation, and evidence quality.

## Claims to leave out until verified

- Percentage latency improvements, user counts, acceptance-rate gains, accuracy gains, or cost reductions: no supporting measurements are present.
- “Deployed on AWS”: the repository demonstrates an inference adapter, not deployment infrastructure.
- “Built with Strands Swarm”: the executable implementation uses direct model SDKs and asyncio.
- RAG, semantic search, or vector database integration: not implemented.
- Voice interviews and Word resume parsing: not implemented. Manual profile text now reaches coaching prompts, but live personalization is not yet validated.
- Automated resume rewriting/export: the output is suggested edits, not an edited resume document.

Hackathon participation and October 2025 come from the original README. Confirm the event date, team size, personal ownership, and any award or judging outcome before adding those details.

## A 45-second project explanation

“I built ClubApply during the AWS × Bruin AI Hackathon to help students apply to university clubs. It gathers public information about a club, turns that into a structured brief, and reuses that context for resume feedback, application strategies, and interview preparation. The system has a React frontend, a FastAPI backend, and six specialized Python stages, with a Bedrock inference adapter and alternate providers. During a later polish pass, I addressed blocking calls inside async functions and ran independent stages concurrently. The biggest remaining challenge is making missing source evidence and generic fallback advice explicit so the guidance stays trustworthy.”

Adapt “I built” to match your actual role, and only use the optimization sentence once you understand the implementation.

## Questions an interviewer may ask

**Why multiple stages instead of one large prompt?** Each stage has a focused input/output contract, which makes failures easier to isolate. A shared brief keeps downstream prompts consistent. The tradeoff is multiple model calls, extra latency, and propagation of any error in the brief.

**What does AWS do?** The Bedrock adapter creates a boto3 runtime client, builds an Anthropic message payload, invokes an enabled model, extracts text, parses JSON, and lets the stage validate its schema. Authentication uses AWS's credential mechanisms. That does not establish cloud deployment of the web application.

**Why was async insufficient?** An async function must yield for other coroutines to progress. Synchronous HTTP/model calls did not yield. Offloading those calls with `asyncio.to_thread` lets the event loop schedule other stages, while `gather` joins their results.

**What must remain sequential?** The summarizer needs the research findings. Coaching needs the resulting brief. Resume, application, and interview coaching do not depend on each other, so they can overlap.

**How do you prevent hallucinations?** Today schema validation only checks output shape, and prompts/fallbacks do not fully prevent fabricated facts. The next step is source provenance, explicit missing-evidence states, student-grounded examples, and fixture-based factuality evaluation.

**What happens when Instagram is blocked?** It is best-effort public HTML fetching. The heuristic fallback may return generic findings. A strong next improvement is to carry fetch status and evidence warnings through to the visible report instead of presenting generic content as researched fact.

**What would you change before launch?** Complete the application UI, constrain and clean up uploads, prevent arbitrary path access and unsafe network fetching, add authentication and controlled CORS, and put bounds and observability around provider calls.

## Evidence to collect for stronger bullets

Keep a short record of your personal contributions and team ownership. Capture a successful demo with sample data. Measure repeated request latency before/after optimization and record conditions. Create a small evaluation set of club pages, resumes, and questions, then score factual support and usefulness. Add metrics to bullets only after those measurements exist.
