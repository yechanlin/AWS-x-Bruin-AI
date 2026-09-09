<p align="center">
  <img src="docs/images/clubapply-banner.svg" alt="ClubApply — Find your fit. Tell your story." width="100%" />
</p>

<h1 align="center">ClubApply</h1>
<p align="center"><strong>Know the club. Connect your experience. Show up prepared.</strong></p>
<p align="center">An AI-assisted workspace for university club applications, resume preparation, and interviews.</p>

<p align="center">
  <a href="https://main.d8qdpc5eyzotl.amplifyapp.com/">Open the live app</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#run-locally">Run locally</a> ·
  <a href="docs/AMPLIFY.md">AWS deployment</a>
</p>

<p align="center">
  <img alt="Built for AWS × Bruin AI" src="https://img.shields.io/badge/BUILT_FOR-AWS_%C3%97_BRUIN_AI-e0b45c?style=for-the-badge" />
  <img alt="Frontend: React" src="https://img.shields.io/badge/FRONTEND-REACT-61dafb?style=for-the-badge" />
  <img alt="Backend: FastAPI" src="https://img.shields.io/badge/BACKEND-FASTAPI-009688?style=for-the-badge" />
</p>

---

## Why ClubApply exists

Applying to a university club can mean piecing together a website, an Instagram profile, a resume, and a list of questions—then figuring out how they relate to each other.

**ClubApply brings that preparation into one workflow.** Students provide the club they are interested in, their experience, and the questions they need to answer. The application researches available club sources and produces a club overview, application guidance, resume suggestions, and optional interview preparation.

Originally built for the **AWS × Bruin AI Hackathon at UCLA in October 2025**, the project now includes a React frontend on AWS Amplify Hosting and a container-based FastAPI backend on AWS Lambda.

## From interest to application

| Step | What you provide | What happens |
| --- | --- | --- |
| **1. Choose your club** | Club, school, role, application stage, and optional website/Instagram URLs | Establish the context for your application |
| **2. Add your experience** | A text-based PDF resume or manually entered education, projects, experience, and skills | Give the coaching stages material to work with |
| **3. Prepare your answers** | Questions entered directly or imported from a `.txt` file | Generate answer guidance, resume edits, and preparation matched to your selected stage |

The interface supports **online applications**, **coffee chats/networking**, and **interview preparation**. Results include expandable sections for the club brief, answer structure, and resume suggestions.

**Try it:** [Open ClubApply](https://main.d8qdpc5eyzotl.amplifyapp.com/), enter a club and your experience, then add a question such as “Why do you want to join this club?” You can try the workflow without a resume by entering experience manually. Supplied source URLs enrich the research; missing or inaccessible sources limit what the app can learn.

## Architecture

The frontend is delivered to the browser by Amplify. The browser sends HTTPS requests to a Lambda Function URL, where Mangum adapts the incoming event for FastAPI. Python coordinates research and coaching, then returns JSON for React to display.

```mermaid
flowchart TB
    subgraph Delivery[Build and deployment]
        Git[GitHub main branch] -->|Automatic frontend build| Amplify[AWS Amplify Hosting]
        Docker[Backend Docker image] -->|Push image| ECR[Amazon ECR]
    end

    Amplify -->|HTML, CSS and JavaScript| Browser[Student browser / React]
    Browser -->|HTTPS API requests| URL[Lambda Function URL]

    subgraph Backend[AWS Lambda]
        URL --> Adapter[Mangum adapter]
        Adapter --> API[FastAPI API]
        API --> Workflow[Research and coaching workflow]
    end

    ECR -.->|Image used by Lambda deployment| Adapter
    Workflow --> Sources[Public club website / Instagram]
    Workflow --> Models[Model adapters / Bedrock, OpenAI, Gemini]
    Workflow -->|Structured results| API
    API -->|JSON response| Browser

    classDef aws fill:#fff3dc,stroke:#c78923,color:#172538;
    classDef app fill:#e8f2ff,stroke:#527aab,color:#172538;
    class Amplify,ECR,URL aws;
    class Browser,API,Workflow,Adapter app;
```

**Two independent deployment paths:** a push to `main` triggers the Amplify frontend build. Backend changes require building a Docker image, pushing it to ECR, and updating Lambda. A Git push alone does not redeploy Python.

### Inside a guidance request

The active web interface calls `/agents/application-coach`. Research sources run concurrently. Once a club brief is available, application and resume coaching run concurrently, with interview preparation added for the relevant application stages.

```mermaid
flowchart TD
    Club[Club details and optional source URLs] --> Web[Website research]
    Club --> IG[Instagram research]
    Web --> Brief[Shared ClubBrief]
    IG --> Brief
    Description[Provided description when no sources are supplied] --> Brief

    PDF[PDF resume] --> Extract[Extract resume text]
    Manual[Manually entered experience] --> Experience[Applicant context]
    Extract --> Experience

    Brief --> Application[Application coach]
    Brief --> Resume[Resume tailor]
    Brief --> Interview[Interview coach / optional]
    Experience --> Application
    Experience --> Resume
    Experience --> Interview
    Questions[Application questions] --> Application

    Application --> Result[Guidance, resume edits, preparation and source warnings]
    Resume --> Result
    Interview --> Result
    Result --> UI[React results view]
```

PDF uploads return extracted text to the frontend, which includes it in the guidance request. This avoids relying on a file persisting across separate Lambda invocations.

### Six specialized stages

| Stage | Responsibility |
| --- | --- |
| **Website researcher** | Fetch and analyze available public club website content |
| **Instagram researcher** | Extract useful signals from accessible public profile content |
| **Summarizer** | Combine findings into a shared `ClubBrief` |
| **Resume tailor** | Suggest ways to connect applicant experience to the club |
| **Application coach** | Develop responses and answer strategies for application questions |
| **Interview coach** | Generate preparation topics and practice guidance |

The CLI and `/clubapply/run` expose a separate six-stage orchestrator that assembles a Pydantic `FinalReport`. The web endpoint composes its own workflow from the same stage modules; it does not call that orchestrator directly.

These stages use **Python `asyncio`, specialized prompts, Pydantic models, and direct model SDKs**. The historical `clubapply_strands` package name remains, but the current implementation does not instantiate Strands Agents or a Strands Swarm.

## Engineering decisions

- **A shared brief:** Research is distilled into one structured representation used by the coaching stages.
- **Concurrent work:** Independent research and coaching tasks overlap; blocking model, HTTP, and PDF work is offloaded to worker threads.
- **Multiple model providers:** Adapters support AWS Bedrock, OpenAI, and Gemini. The preferred provider is tried first, followed by other configured providers. If all attempts fail, stages can use heuristic fallbacks.
- **Explicit demo mode:** `LLM_PROVIDER=offline` disables model calls for a credential-free local demonstration. Generic fallback output is not evidence of a successful model call.
- **Separate hosting responsibilities:** Amplify publishes the React build; Lambda executes Python on demand; ECR stores the backend image.
- **Browser integration:** `REACT_APP_API_URL` supplies the backend address at build time, and backend CORS settings allow the deployed frontend origin.

## Built with

| Layer | Technologies |
| --- | --- |
| Interface | React 19, JavaScript, CSS, Tailwind styling |
| API | Python 3.11+, FastAPI, Pydantic, Mangum |
| Workflow | `asyncio`, specialized research and coaching modules |
| Model integrations | AWS Bedrock, OpenAI, Google Gemini |
| Hosting | AWS Amplify Hosting, AWS Lambda, Amazon ECR, Docker |
| Frontend delivery | GitHub integration, `amplify.yml`, npm |
| Verification | Jest and React Testing Library; manual deployment smoke checks |

## Run locally

Prerequisites: **Python 3.11+**, **Node.js/npm**, and Git.

```sh
git clone https://github.com/yechanlin/AWS-x-Bruin-AI.git
cd AWS-x-Bruin-AI
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Start the API in one terminal. This example disables model calls so you can explore without API credentials:

```sh
LLM_PROVIDER=offline uvicorn clubapply_strands.server.app:app --reload --port 8000
```

Start React in a second terminal:

```sh
cd client
npm ci
npm start
```

Open **http://localhost:3000**. The API exposes a health check at **http://localhost:8000/health** and interactive endpoint documentation at **http://localhost:8000/docs**.

### Enable model-backed guidance

Copy `.env.example` to `.env` and configure a supported provider. Keep credentials in the backend environment; the frontend only needs the public API URL.

```sh
cp .env.example .env
```

| Setting | Purpose |
| --- | --- |
| `LLM_PROVIDER` | Preferred provider: `bedrock`, `openai`, `gemini`, or `offline` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI credentials and model selection |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Gemini credentials and model selection |
| `AWS_PROFILE` / `AWS_DEFAULT_REGION` / `BEDROCK_MODEL_ID` | Local AWS identity, region, and Bedrock model selection |
| `LLM_TIMEOUT_SECONDS` | Model attempt timeout; defaults to 20 seconds |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins accepted by backend CORS |
| `REACT_APP_API_URL` | Frontend build/start variable; defaults to `http://localhost:8000` |

Use model IDs available to your account and supported by the adapters. On Lambda, Bedrock can use the function's execution role. Restart the API without the `LLM_PROVIDER=offline` command override to enable configured model calls. Offline model mode does not disable source fetching in the web API.

### CLI workflow

```sh
LLM_PROVIDER=offline clubapply-strands \
  --club "Example Club" \
  --school "UCLA" \
  --resume ./resume.pdf \
  --questions '["Why this club?", "Describe a relevant project."]'
```

The CLI writes a structured report under `out/`. Supply your own PDF. Add `--online` to enable source fetching; omitting it does not itself disable model calls.

## AWS deployment

**Live frontend:** [ClubApply on Amplify](https://main.d8qdpc5eyzotl.amplifyapp.com/)

| Component | Deployment behavior |
| --- | --- |
| Frontend | GitHub `main` → Amplify → `npm ci` → `npm run build` → publish `client/build` |
| Backend | Docker build → ECR push → Lambda image update |
| API access | Public Function URL, with both URL-invocation permissions and application CORS |

See [Amplify setup and deployment notes](docs/AMPLIFY.md) and the [backend deployment guide](docs/DEPLOYMENT.md). The latter retains the earlier S3 frontend alternative; Amplify is the active frontend host.

Hosting and model use are subject to provider pricing and account allowances; this project does not promise a zero-cost deployment.

## Repository map

```text
AWS-x-Bruin-AI/
├── client/                 React application and UI tests
│   └── src/services/       Frontend API client
├── server/
│   ├── app.py              FastAPI routes and web guidance workflow
│   └── lambda_handler.py   Mangum entry point for Lambda
├── agents/                 Six research/coaching stages and model adapters
├── tools/                  URL fetching and PDF text extraction
├── schemas.py              Shared Pydantic data models
├── orchestrator.py         Full six-stage pipeline for CLI and API
├── main.py                 CLI entry point
├── Dockerfile              Lambda backend image
├── amplify.yml             Frontend build configuration
├── scripts/                Deployment helpers
└── docs/                   Architecture walkthroughs and deployment notes
```

## Verification and current scope

Run the frontend tests and production build:

```sh
CI=true npm --prefix client test -- --watchAll=false --runInBand
npm --prefix client run build
```

The UI tests cover manual experience submission, PDF upload handling, and the interview/question-import path with mocked API calls. Live smoke checks have verified frontend delivery, Lambda health, CORS, and a manual-input guidance request; these are not a comprehensive backend integration suite.

ClubApply is a **hackathon prototype**. Public-source access can fail, Instagram coverage is limited by what is publicly accessible, and model failures may produce generic templates. Authentication, rate limiting, stronger URL-fetch protections, and production data-handling controls remain future work. CORS is a browser policy, not authentication. Use demo information when exploring the public app.

There is no persistent application database or vector-retrieval system in the current architecture.

## Explore further

- [Project walkthrough](docs/PROJECT_GUIDE.md)
- [AWS Amplify deployment](docs/AMPLIFY.md)
- [Backend deployment](docs/DEPLOYMENT.md)
- [Local testing notes](docs/LOCAL_TESTING.md)

For contributions, open an issue or pull request with the problem, the proposed behavior, and how you verified it. Keep frontend and backend deployment requirements clear, and never commit credentials.

---

<p align="center"><em>Your experience is the starting point. ClubApply helps you connect it to the opportunity.</em></p>
