from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Sequence

from agents import InputGuardrailTripwireTriggered
from dotenv import load_dotenv

from .agent import run_live_recommendation
from .evals import DEFAULT_EVAL_CASES_PATH, format_eval_report, run_evals
from .guardrails import GUARDRAIL_NAME
from .models import CourseRecommendation


def _print_recommendation(recommendation: CourseRecommendation) -> None:
    print(json.dumps(recommendation.model_dump(), indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcgill-advisor",
        description="Single-agent fictional McGill course advising prototype.",
    )
    parser.add_argument("prompt", nargs="?", help="Student advising question.")
    parser.add_argument(
        "--evals",
        action="store_true",
        help="Run live OpenAI Agents SDK eval cases and exit.",
    )
    parser.add_argument(
        "--eval-path",
        type=Path,
        default=DEFAULT_EVAL_CASES_PATH,
        help="Path to eval cases JSON.",
    )
    parser.add_argument(
        "--model",
        help="Override OPENAI_MODEL for live SDK runs.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.evals:
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key "
                "before running live evals."
            )
            return 2
        results, failures = asyncio.run(run_evals(args.eval_path, model=args.model))
        print(format_eval_report(results))
        return 1 if failures else 0

    if not args.prompt:
        parser.print_help()
        return 2

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
        return 2

    try:
        recommendation = asyncio.run(
            run_live_recommendation(args.prompt, model=args.model)
        )
    except InputGuardrailTripwireTriggered:
        print(
            json.dumps(
                {
                    "blocked_by": GUARDRAIL_NAME,
                    "message": (
                        "This request requires human advisor approval in the prototype."
                    ),
                },
                indent=2,
            )
        )
        return 3

    _print_recommendation(recommendation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
