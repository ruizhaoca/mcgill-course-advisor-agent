from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents import InputGuardrailTripwireTriggered
from pydantic import ValidationError

from .agent import run_live_recommendation
from .fixtures import STUDENT_PROFILE
from .guardrails import GUARDRAIL_NAME
from .models import CourseRecommendation


DEFAULT_EVAL_CASES_PATH = (
    Path(__file__).resolve().parents[1] / "evals" / "course_advisor_eval_cases.json"
)


@dataclass(frozen=True)
class EvalResult:
    name: str
    input: str
    passed: bool
    details: list[str]
    outcome: str
    agent_output: str


def load_eval_cases(path: Path = DEFAULT_EVAL_CASES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _contains_all(haystack: str, needles: list[str]) -> list[str]:
    lowered = haystack.lower()
    return [needle for needle in needles if needle.lower() not in lowered]


def _render_recommendation_text(recommendation: CourseRecommendation) -> str:
    return " ".join(
        [
            recommendation.summary,
            " ".join(recommendation.policy_risks),
            " ".join(recommendation.required_approvals),
            " ".join(recommendation.next_steps),
            " ".join(
                f"{course.code} {course.title} {course.rationale} {course.prerequisite_status}"
                for course in recommendation.recommended_courses
            ),
        ]
    )


def _base_output_payload() -> dict[str, Any]:
    return {"student_id": STUDENT_PROFILE.student_id}


def _format_agent_output(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2)


def _expected_guardrail_result(case: dict[str, Any]) -> EvalResult:
    details: list[str] = []
    expected_guardrail = case.get("expected_guardrail_name", GUARDRAIL_NAME)
    if expected_guardrail != GUARDRAIL_NAME:
        details.append(f"expected guardrail {expected_guardrail}, got {GUARDRAIL_NAME}")

    agent_output = _format_agent_output(
        {
            **_base_output_payload(),
            "blocked_by": GUARDRAIL_NAME,
            "message": "This request requires human advisor approval in the prototype.",
        }
    )

    return EvalResult(
        name=case["name"],
        input=case["input"],
        passed=not details,
        details=details or [f"blocked by {GUARDRAIL_NAME}"],
        outcome="guardrail_blocked",
        agent_output=agent_output,
    )


async def evaluate_case(case: dict[str, Any], model: str | None = None) -> EvalResult:
    details: list[str] = []
    prompt = case["input"]
    expected_outcome = case.get("expected_outcome", "recommendation")

    try:
        recommendation = await run_live_recommendation(prompt, model=model)
    except InputGuardrailTripwireTriggered:
        if expected_outcome == "guardrail_blocked":
            return _expected_guardrail_result(case)
        return EvalResult(
            name=case["name"],
            input=prompt,
            passed=False,
            details=[f"unexpectedly blocked by {GUARDRAIL_NAME}"],
            outcome="guardrail_blocked",
            agent_output=_format_agent_output(
                {
                    **_base_output_payload(),
                    "blocked_by": GUARDRAIL_NAME,
                    "message": (
                        "This request requires human advisor approval in the prototype."
                    ),
                }
            ),
        )
    except (ValidationError, json.JSONDecodeError) as exc:
        return EvalResult(
            name=case["name"],
            input=prompt,
            passed=expected_outcome == "structured_output_failure",
            details=[f"structured output validation failed: {exc}"],
            outcome="structured_output_failure",
            agent_output=_format_agent_output(
                {
                    **_base_output_payload(),
                    "error_type": "structured_output_failure",
                    "message": str(exc),
                }
            ),
        )
    except Exception as exc:
        return EvalResult(
            name=case["name"],
            input=prompt,
            passed=expected_outcome == "api_or_tool_failure",
            details=[f"{type(exc).__name__}: {exc}"],
            outcome="api_or_tool_failure",
            agent_output=_format_agent_output(
                {
                    **_base_output_payload(),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            ),
        )

    if expected_outcome != "recommendation":
        details.append(
            f"expected outcome {expected_outcome}, got recommendation"
        )

    recommended_codes = {course.code for course in recommendation.recommended_courses}

    missing_expected_codes = [
        code for code in case.get("expected_course_codes", []) if code not in recommended_codes
    ]
    if missing_expected_codes:
        details.append(f"missing expected recommended course(s): {missing_expected_codes}")

    forbidden_codes = [
        code for code in case.get("forbidden_course_codes", []) if code in recommended_codes
    ]
    if forbidden_codes:
        details.append(f"recommended forbidden course(s): {forbidden_codes}")

    missing_terms = _contains_all(
        _render_recommendation_text(recommendation),
        case.get("expected_terms", []),
    )
    if missing_terms:
        details.append(f"missing expected text term(s): {missing_terms}")

    return EvalResult(
        name=case["name"],
        input=prompt,
        passed=not details,
        details=details or ["passed"],
        outcome="recommendation",
        agent_output=_format_agent_output(recommendation.model_dump()),
    )


async def run_evals(
    path: Path = DEFAULT_EVAL_CASES_PATH,
    model: str | None = None,
) -> tuple[list[EvalResult], int]:
    results: list[EvalResult] = []
    for case in load_eval_cases(path):
        results.append(await evaluate_case(case, model=model))
        await asyncio.sleep(0.2)

    failures = sum(1 for result in results if not result.passed)
    return results, failures


def format_eval_report(results: list[EvalResult]) -> str:
    lines = ["McGill advisor live Agents SDK evals"]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.extend(
            [
                "",
                f"Case: {result.name}",
                f"Input: {result.input}",
                "Live agent output:",
                result.agent_output,
                f"Eval result: {status} [{result.outcome}] ({'; '.join(result.details)})",
            ]
        )
    lines.append(
        f"Summary: {sum(1 for result in results if result.passed)}/{len(results)} passed"
    )
    return "\n".join(lines)
