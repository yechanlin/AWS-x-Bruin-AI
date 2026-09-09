"""CLI entry point: parses arguments, runs the full ClubApply pipeline via orchestrator.py, saves a JSON report to out/, and optionally opens an interactive InterviewChat."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv

from .schemas import InputSpec, model_to_dict
from .orchestrator import run_clubapply
from .agents.interview_coach import InterviewChat
from .logging_config import setup_logging

# Load provider API keys from .env at the repo root before anything reads them.
load_dotenv(Path(__file__).resolve().parent / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ClubApply Strands – multi-agent CLI to tailor applications."
    )
    parser.add_argument("--club", required=True, help="Club name")
    parser.add_argument("--school", required=True, help="School name")
    parser.add_argument("--instagram", dest="instagram", default=None, help="Instagram URL")
    parser.add_argument("--website", dest="website", default=None, help="Website URL")
    parser.add_argument("--resume", dest="resume", required=True, help="Path to resume PDF")
    parser.add_argument(
        "--questions",
        dest="questions",
        default=None,
        help="JSON list of application questions",
    )
    parser.add_argument(
        "--online",
        dest="online",
        action="store_true",
        help="Fetch live website/Instagram (default: False)",
    )
    parser.add_argument(
        "--chat",
        dest="chat",
        action="store_true",
        help="Enter interview chat after generating report",
    )
    return parser.parse_args()


def ensure_out_dir() -> Path:
    base = Path(__file__).resolve().parent / "out"
    base.mkdir(parents=True, exist_ok=True)
    return base


def parse_questions(q: Optional[str]) -> Optional[List[str]]:
    if not q:
        return None
    try:
        data = json.loads(q)
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return data
    except Exception:
        pass
    # Fallback: split by '||' or ';'
    return [s.strip() for s in q.split("||") if s.strip()] or None


async def main_async():
    args = parse_args()
    setup_logging("cli.log")

    print("Starting ClubApply Strands...")
    input_spec = InputSpec(
        clubName=args.club,
        schoolName=args.school,
        instagramUrl=args.instagram,
        websiteUrl=args.website,
        resumePath=args.resume,
        applicationQuestions=parse_questions(args.questions),
        isOnline=bool(args.online),
    )

    print("Running InstagramAgent ...")
    print("Running WebsiteAgent ...")
    report = await run_clubapply(input_spec)
    print("Summarizing club signals ...")
    print("Tailoring resume ...")
    print("Coaching applications ...")
    print("Preparing interviews ...")
    print("Aggregation complete ✅")

    out_dir = ensure_out_dir()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = input_spec.clubName.lower().replace(" ", "_")
    out_path = out_dir / f"{ts}_{safe_name}.json"

    # Pydantic v1/v2 compatibility
    content = model_to_dict(report)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    print(f"Saved report → {out_path}")

    if args.chat:
        print("\nEntering InterviewCoach chat. Type 'exit' to quit.\n")
        chat = InterviewChat(args.club, args.school, report.brief)
        try:
            while True:
                user = input("you> ").strip()
                if user.lower() in {"exit", "quit"}:
                    break
                reply = chat.chat(user)
                print(f"coach> {reply}\n")
        except KeyboardInterrupt:
            print("\nBye!")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
