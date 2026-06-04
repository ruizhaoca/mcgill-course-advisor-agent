from __future__ import annotations

import os

from agents import Agent, Runner

from .guardrails import AdvisorApprovalRequiredGuardrail
from .models import CourseRecommendation
from .tools import check_prerequisites, flag_policy_risk, search_courses


DEFAULT_MODEL = "gpt-5-nano"


AGENT_INSTRUCTIONS = """
You are a single-agent course advising prototype for a fictional McGill-style catalog.

Use only the fake fixture data exposed through the tools. Do not invent real McGill
requirements, course availability, policies, or program rules. Make it clear that the
response is a prototype planning aid, not official advising.

Workflow:
1. Use search_courses with a small limit such as 5 to find candidate fake courses.
2. Use check_prerequisites with student_id "demo-student" before recommending courses.
3. Use flag_policy_risk with student_id "demo-student" for candidate courses.
4. Return only a CourseRecommendation structured output.

The recommended_courses list is for courses the demo student can reasonably take now.
Do not put a course in recommended_courses if it has missing prerequisites, needs advisor
approval, is unknown to the fake catalog, is already completed or in progress, or has a
high/medium policy risk. You may still discuss requested-but-ineligible courses in the
summary, policy_risks, required_approvals, and next_steps fields.

If the user asks about an ineligible course, explain why it is not currently recommended
and suggest the next eligible step when one is visible from the fake prerequisite data.
For unknown course codes, state that the course was not found in the fake catalog and do
not recommend it. Do not use handoffs or describe any multi-agent process.
""".strip()


def build_agent(model: str | None = None) -> Agent:
    return Agent(
        name="McGillCourseAdvisorAgent",
        instructions=AGENT_INSTRUCTIONS,
        model=model or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
        tools=[search_courses, check_prerequisites, flag_policy_risk],
        input_guardrails=[AdvisorApprovalRequiredGuardrail],
        output_type=CourseRecommendation,
    )


McGillCourseAdvisorAgent = build_agent


async def run_live_recommendation(
    prompt: str,
    model: str | None = None,
) -> CourseRecommendation:
    result = await Runner.run(build_agent(model=model), prompt)
    final_output = result.final_output

    if isinstance(final_output, CourseRecommendation):
        return final_output

    if isinstance(final_output, dict):
        return CourseRecommendation.model_validate(final_output)

    return CourseRecommendation.model_validate_json(str(final_output))
