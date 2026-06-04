from __future__ import annotations

import re
from typing import Any

from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, input_guardrail

from .models import GuardrailDecision


GUARDRAIL_NAME = "AdvisorApprovalRequiredGuardrail"


APPROVAL_TERMS: dict[str, str] = {
    "override": "Course overrides require a human advisor in this prototype.",
    "waive": "Prerequisite waivers require a human advisor in this prototype.",
    "bypass": "Bypassing requirements requires a human advisor in this prototype.",
    "overload": "Credit overload requests require a human advisor in this prototype.",
    "guarantee enrollment": "Enrollment guarantees cannot be provided by this prototype.",
    "graduate course": "Graduate-course requests require human advisor review.",
}


def _stringify_agent_input(agent_input: str | list[Any]) -> str:
    if isinstance(agent_input, str):
        return agent_input
    return " ".join(str(item) for item in agent_input)


def evaluate_advisor_approval_need(user_input: str) -> GuardrailDecision:
    lowered = user_input.lower()
    matched_terms: list[str] = []
    reasons: list[str] = []

    for term, reason in APPROVAL_TERMS.items():
        if term in lowered:
            matched_terms.append(term)
            reasons.append(reason)

    credit_matches = re.findall(r"\b([0-9]{2})\s*credits?\b", lowered)
    for raw_number in credit_matches:
        credits = int(raw_number)
        if credits > 12:
            matched_terms.append(f"{credits} credits")
            reasons.append(
                f"{credits} credits exceeds the demo student's 12-credit advising threshold."
            )

    return GuardrailDecision(
        guardrail_name=GUARDRAIL_NAME,
        requires_approval=bool(reasons),
        matched_terms=list(dict.fromkeys(matched_terms)),
        reasons=list(dict.fromkeys(reasons)),
    )


@input_guardrail(name=GUARDRAIL_NAME, run_in_parallel=False)
async def AdvisorApprovalRequiredGuardrail(
    context: RunContextWrapper[Any],
    agent: Agent[Any],
    agent_input: str | list[Any],
) -> GuardrailFunctionOutput:
    """Block requests that should be handled by a human advisor."""

    del context, agent
    decision = evaluate_advisor_approval_need(_stringify_agent_input(agent_input))
    return GuardrailFunctionOutput(
        output_info=decision.model_dump(),
        tripwire_triggered=decision.requires_approval,
    )
