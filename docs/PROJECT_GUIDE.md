# Understanding ClubApply end to end

## The problem and product

Students applying to clubs need to research the organization, connect their experience to its priorities, answer short questions, and prepare for interviews. ClubApply puts these activities into a shared workflow. Its central design choice is to create one structured **ClubBrief** and reuse it across specialized coaching stages.

Think of it as a research assistant handing the same notes to a resume reviewer, an application coach, and an interview coach.

## Follow one application through the code

1. **Collect inputs.** `main.py` parses CLI arguments into `schemas.InputSpec`: club, school, optional source URLs, resume path, questions, and source-fetching mode. Alternatively, `server/app.py` accepts the same model at `/clubapply/run`.
2. **Collect evidence.** `agents/instagram_agent.py` fetches public HTML and extracts text. `agents/website_agent.py` crawls the root page plus links from that page, capped at five pages. This is a shallow HTML crawler; it does not execute JavaScript or authenticate to Instagram.
3. **Structure evidence.** Both stages ask a model for JSON, then validate it as `InstagramFindings` or `WebsiteFindings`. On absent/invalid model output they return heuristic findings.
4. **Create shared context.** `agents/summarizer_agent.py` combines the findings into `ClubBrief`: overview, mission, desired qualities, events, keywords, and five priorities.
5. **Generate guidance.** `agents/resume_tailor.py` extracts up to three PDF pages and combines the text with the brief. `agents/application_coach.py` combines the brief with questions. `agents/interview_coach.py` produces likely questions, story prompts, and a pitch template. The full CLI pipeline sends the resume only to the resume stage. The active application API now sends extracted/manual experience to application and optional interview coaching as well. Offline outputs remain generic templates.
6. **Validate and return.** `orchestrator.py` assembles a `FinalReport`. The CLI serializes it into `out/`; the API returns JSON. Pydantic checks structural correctness, not factual accuracy.

## How the browser differs

`client/src/index.js` mounts `App.js`, a three-step form. It gathers club details, a resume or manual profile, then application questions. Submission uploads the resume, if supplied, and calls `/agents/application-coach` through `services/api.js`.

That endpoint researches available sources, generates a brief, and returns application strategies plus resume edits. The full CLI orchestrator additionally generates interview preparation. The dashboard and reusable agent components are present but are not the active route in `App.js`.

The local testing pass repaired the active form's focus loss, connected manual resume text to all requested coaching stages, implemented plain-text question import, and made the interview/coffee-chat selections produce text preparation. PDF uploads now validate the file signature, size (5 MB), and extractable text. Offline mode and missing-source warnings are visible in results. Contact fields are not sent to coaching models; experience, education, projects, skills, and achievements are.

Remaining UI limitations: voice conversation and Word/PDF question-document import are not implemented. The unused dashboard/interview service still needs consolidation with the active form. File inputs support PDF resumes and plain-text questions in the active journey.

## Model layer and AWS's role

`agents/llm_utils.py` centralizes provider selection and JSON parsing. The OpenAI adapter calls chat completions; Gemini uses `google-genai` (the maintained SDK, migrated off the retired `google-generativeai` package); Bedrock uses `boto3` to call `bedrock-runtime.invoke_model` with Anthropic message-format JSON. Every configured provider is tried in turn - falling back to the next on error, invalid credentials, or a timeout (`LLM_TIMEOUT_SECONDS`) - before a stage drops to its heuristic template.

AWS supplies inference when the Bedrock adapter is selected. The repository contains no verified deployment infrastructure for Lambda, ECS, S3, or other AWS services. Participating in the AWS hackathon does not by itself establish that the application was deployed on AWS.

Each stage owns its prompt and output model. This is an orchestrated LLM workflow with six specialized stages. The code does not implement autonomous handoffs, tool selection, an agent planning loop, or a functioning Strands Swarm. Describe it this way if an interviewer asks what “multi-agent” means here.

There is also no implemented embedding index, vector database, semantic search, or RAG retrieval. Optional dependency comments in the old README were ideas, not evidence of those capabilities.

## Optimization implemented in this polish pass

The original agent functions used `async def` but called synchronous `requests`, model SDKs, and PDF parsing without yielding. `asyncio.gather` cannot overlap blocking calls that occupy the event-loop thread. Independent work therefore still ran serially.

The agent functions now offload those blocking operations to worker threads. The orchestrator explicitly uses `asyncio.gather` for both sources, waits for the brief, and then gathers the three coaching stages. The active application API also overlaps source work and application/resume guidance. The speculative Swarm import fallback was removed to make execution predictable.

With stage durations I (Instagram), W (website), S (summary), R (resume), A (application), and V (interview), the idealized dependency path changes from:

```text
Before: I + W + S + R + A + V
After:  max(I, W) + S + max(R, A, V)
```

This is a scheduling model, not a measured speedup. Provider throttling, thread scheduling, retries, and contention can change actual results. The number of model calls is unchanged, so the optimization does not inherently reduce token cost. Thread offloading also does not provide cancellation of an in-flight synchronous provider request or unlimited capacity.

Other changes:

- Editable package metadata makes imports work from the actual `AWS-x-Bruin-AI` checkout.
- `python-multipart` is declared for FastAPI upload routes.
- Explicit OpenAI selection wins even if Gemini keys exist.
- Offline provider mode ignores existing credentials for reproducible demos.
- Standard URL joining handles relative paths; fragment normalization avoids duplicate fetches, and exact origin comparison rejects lookalike domain prefixes. This is crawl scoping, not complete SSRF protection.
- Serialization prefers Pydantic's modern `model_dump` when available.
- Regression tests use thread barriers to prove overlapping execution instead of asserting fragile wall-clock thresholds.

## Prioritized next improvements

| Priority | Work | Evidence of completion |
| --- | --- | --- |
| 1 | Extend the tested application journey with cancellation, request timeouts, and accessible file controls | Browser test from club input through tailored results, including an error case |
| 1 | Surface missing evidence and fallback mode in all outputs | Blocked crawl, malformed JSON, and unreadable PDF each produce a visible explanation |
| 1 | Ground advice in source text and actual student experience; use placeholders for unprovided outcomes | An evaluation set catches invented club facts and invented applicant metrics |
| 1 before public hosting | Replace arbitrary resume paths with scoped upload IDs, add size/type validation, cleanup, source URL/redirect/private-network protections, and authentication | API tests reject unsafe paths, oversized uploads, private destinations, and unauthorized access |
| 2 | Consolidate the UI and CLI around a shared pipeline/service layer | Both entry points produce equivalent brief and guidance for the same fixture |
| 2 | Add provider timeouts, bounded concurrency, client reuse, structured errors, and explicit model-fallback policy | Slow/throttled provider tests terminate predictably and report what happened |
| 2 | Choose and validate a primary provider; update legacy adapters and pin a tested dependency set | Successful live smoke test plus reproducible lockfile |
| 3 | Add timing, token usage, cached public source content, and a fixture evaluation suite | Report latency distributions, cost per run, cache hit rate, and factuality scores |
| 3 | Integrate real Strands Agents if their tool/handoff features serve a concrete need | Executed Strands pipeline and tests; resume claims can then name the framework |

Avoid adding vector retrieval solely to increase the technology list. The current source corpus is at most a few pages per run; first improve provenance, correctness, and the working user flow.

## How to learn and demo it

Read in this order: `schemas.py` → `orchestrator.py` → `tools/fetch_url.py` → `agents/website_agent.py` → `agents/summarizer_agent.py` → `agents/resume_tailor.py` → `agents/llm_utils.py` → `server/app.py` → `client/src/App.js`.

Run the offline CLI, open the JSON, and map each report section to its generating stage. Run the regression tests. Next, configure one provider and use a PDF containing fictional sample experience with a public club website. Inspect whether each recommendation is supported by the source text and resume. A successful HTTP response is insufficient to establish useful guidance.

For a future performance claim, hold inputs, provider/model, cache state, and generation settings constant; record repeated baseline and optimized runs, report sample size and median/p95, and distinguish live results from stubbed benchmarks. Do not turn synthetic concurrency tests into a production latency percentage.
