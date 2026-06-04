import asyncio

from mcgill_advisor.agent import build_agent
from mcgill_advisor.evals import EvalResult, evaluate_case, format_eval_report, load_eval_cases
from mcgill_advisor.guardrails import evaluate_advisor_approval_need
from mcgill_advisor.models import CourseRecommendation
from mcgill_advisor.tools import (
    check_prerequisites_impl,
    flag_policy_risk_impl,
    search_courses_impl,
)


def test_agent_is_single_named_agent() -> None:
    agent = build_agent(model="gpt-5-nano")

    assert agent.name == "McGillCourseAdvisorAgent"
    assert len(agent.tools) == 3
    assert agent.handoffs == []
    assert agent.output_type is CourseRecommendation
    assert agent.input_guardrails[0].name == "AdvisorApprovalRequiredGuardrail"
    assert agent.input_guardrails[0].run_in_parallel is False


def test_search_courses_finds_programming_path() -> None:
    result = search_courses_impl("programming software", limit=3)
    codes = [match.code for match in result.matches]

    assert "COMP 250" in codes


def test_prerequisite_check_reports_missing_comp_250() -> None:
    result = check_prerequisites_impl(["COMP 251"], "demo-student")
    check = result.checks[0]

    assert check.course_code == "COMP 251"
    assert check.eligible is False
    assert "COMP 250" in check.missing_prerequisites
    assert "MATH 240" in check.in_progress_prerequisites


def test_policy_risk_flags_400_level_and_missing_prereq() -> None:
    result = flag_policy_risk_impl(["COMP 421"], 3, "demo-student")
    messages = " ".join(risk.message for risk in result.risks)

    assert "400-level" in messages
    assert "COMP 251" in messages
    assert any(risk.requires_advisor_approval for risk in result.risks)


def test_guardrail_blocks_overload_requests() -> None:
    decision = evaluate_advisor_approval_need("Can I take 15 credits this term?")

    assert decision.requires_approval is True
    assert "15 credits" in decision.matched_terms


def test_eval_cases_include_edge_or_failure_cases() -> None:
    cases = load_eval_cases()
    edge_or_failure_cases = [
        case
        for case in cases
        if case["name"].startswith(("edge:", "failure:"))
        or case.get("expected_outcome") in {"guardrail_blocked", "api_or_tool_failure"}
    ]

    assert len(edge_or_failure_cases) >= 2


def test_eval_report_prints_agent_output_and_status() -> None:
    report = format_eval_report(
        [
            EvalResult(
                name="sample live case",
                input="sample user input",
                passed=True,
                details=["passed"],
                outcome="recommendation",
                agent_output='{"student_id": "demo-student", "summary": "sample output"}',
            )
        ]
    )

    assert "Case: sample live case" in report
    assert "Input: sample user input" in report
    assert "Live agent output:" in report
    assert '"student_id": "demo-student"' in report
    assert "Eval result: PASS [recommendation] (passed)" in report


def test_eval_error_output_includes_student_id(monkeypatch) -> None:
    async def fake_run_live_recommendation(prompt: str, model: str | None = None):
        raise RuntimeError("simulated connection failure")

    monkeypatch.setattr(
        "mcgill_advisor.evals.run_live_recommendation",
        fake_run_live_recommendation,
    )

    result = asyncio.run(
        evaluate_case(
            {
                "name": "simulated live failure",
                "input": "Can I take a fake course?",
                "expected_outcome": "api_or_tool_failure",
            }
        )
    )

    assert result.passed is True
    assert result.input == "Can I take a fake course?"
    assert '"student_id": "demo-student"' in result.agent_output
