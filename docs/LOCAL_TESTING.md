# Local test results — September 7, 2026

The React frontend and FastAPI backend were started locally and tested through the browser. No cloud deployment was created or verified. The backend was started with `LLM_PROVIDER=offline`; successful UI results in this pass are heuristic templates, not live model inference.

## Running locally

Frontend: http://localhost:3000  
API: http://127.0.0.1:8000  
API reference: http://127.0.0.1:8000/docs

To restart in two terminals from the repository root:

```sh
# Terminal 1
source .venv/bin/activate
LLM_PROVIDER=offline python -m uvicorn clubapply_strands.server.app:app --host 127.0.0.1 --port 8000

# Terminal 2
cd client
BROWSER=none HOST=127.0.0.1 npm start
```

For a real AI run, stop the offline backend and restart it with a configured provider as described in the README. Keep credentials in your local shell or credential manager, not in chat or committed files. The health endpoint reports configuration mode, not proof that a provider is reachable or authorized.

## Verified

- Manual profile: typing retains focus; form advances; experience reaches all requested model prompts in API tests; browser displays completed application results.
- PDF path: fictional sample PDF selected in the browser, uploaded successfully, parsed, and used in the completed application flow.
- Question import: `.txt` file populates two question fields, and submitted results match those questions.
- Interview and coffee-chat selections: both reach text preparation; likely questions, stories, pitch template, and follow-up questions render.
- Live public website fetching: https://datascienceunion.com returned five successful page fetches, followed by a completed result in the browser. The old README URL, `dsu.ucla.edu`, failed DNS resolution; that failure produced a visible source warning.
- Error behavior verified manually: invalid/oversized PDFs are rejected, missing resume paths produce a readable 400 error, and frontend upload errors are displayed without issuing a coaching request.
- Production frontend build passes: from `client`, `CI=true npm run build`.

The `tests/` unittest/TestClient suite from this pass was removed; verification is manual (through the browser) plus the backend log described below. Refresh the app to start a fresh application.

## Backend logs

The backend now writes every agent-stage trace, LLM provider call, and HTTP request to `logs/backend.log` (rotating, `logs/` is gitignored) in addition to the console — no manual output redirection needed. Tail it while testing:

```sh
tail -f logs/backend.log
```

Look for `[LLM] OpenAI call model=...` / `[LLM] Gemini call model=...` / `[LLM] Bedrock attempt ...` lines to confirm a real provider was actually invoked, versus `[<Agent>] using heuristic fallback` when it wasn't. Failures (`[LLM] ... call failed: ...`, `[fetch_url] ERROR ...`) are logged at WARNING level so they're easy to grep for.

## Fixes made during testing

The nested personal-information component remounted on each keystroke; it is now a stable component. Manual experience is submitted and reused for application, resume, and optional interview prompts. Question import now reads plain text. The voice placeholder was replaced with working text preparation. PDF inputs match backend support and enforce file/size/text validation. API errors and offline/source warnings appear inline. Changing inputs clears stale results.

## Still unverified or unfinished

- Live Bedrock/OpenAI/Gemini inference, credentials, model availability, response quality, provider errors, and real inference latency.
- Successful Instagram extraction; no Instagram URL was supplied in this test. Public HTML fetching may be blocked or return a login page.
- Voice interaction and Word resumes; these are not supported by the tested flow.
- Deployed cloud behavior, multiple users, authentication, upload ownership/cleanup, SSRF protections, restrictive CORS, and provider timeouts.
- The crawler fetched a cart page and both root slash variants on the live site. Prioritizing about/apply pages and canonicalizing root URLs would improve the small crawl budget.
- Provider fallbacks can still occur silently in configured mode. Add per-stage model/fallback status before treating every displayed result as successful inference.

The local app is ready for a hands-on offline trial. Complete a live provider run and deployment hardening before public cloud hosting.
