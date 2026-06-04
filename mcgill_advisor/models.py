from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Course(BaseModel):
    """Small fictional course fixture."""

    model_config = ConfigDict(frozen=True)

    code: str
    title: str
    department: str
    credits: int
    level: int
    terms: list[str]
    tags: list[str]
    description: str


class StudentProfile(BaseModel):
    """Single fake student profile used by the prototype."""

    student_id: str
    program: str
    year: str
    completed_courses: list[str]
    current_courses: list[str]
    interests: list[str]
    max_recommended_credits: int


class CourseMatch(BaseModel):
    code: str
    title: str
    credits: int
    terms: list[str]
    tags: list[str]
    match_score: int
    why_matched: str


class CourseSearchResult(BaseModel):
    query: str
    matches: list[CourseMatch]


class PrerequisiteStatus(BaseModel):
    course_code: str
    eligible: bool
    met_prerequisites: list[str]
    in_progress_prerequisites: list[str]
    missing_prerequisites: list[str]
    note: str


class PrerequisiteCheckResult(BaseModel):
    student_id: str
    checks: list[PrerequisiteStatus]


RiskSeverity = Literal["info", "medium", "high"]


class PolicyRisk(BaseModel):
    course_code: str
    severity: RiskSeverity
    message: str
    requires_advisor_approval: bool


class PolicyRiskReport(BaseModel):
    student_id: str
    requested_credits: int
    risks: list[PolicyRisk]


class RecommendedCourse(BaseModel):
    code: str = Field(..., description="Fictional McGill-style course code.")
    title: str = Field(..., description="Fictional course title.")
    credits: int = Field(..., description="Credit value for the fake fixture course.")
    rationale: str = Field(..., description="Why this course fits the request.")
    prerequisite_status: str = Field(..., description="Short prerequisite status.")


class CourseRecommendation(BaseModel):
    """Structured final output for the single course-advisor agent."""

    student_id: str = Field(..., description="The fake student profile used for advising.")
    summary: str = Field(..., description="Brief advising summary.")
    recommended_courses: list[RecommendedCourse] = Field(
        ..., description="Recommended fictional courses."
    )
    policy_risks: list[str] = Field(
        ..., description="Policy-style risks or caveats found in the fixture rules."
    )
    required_approvals: list[str] = Field(
        ..., description="Items that need human advisor approval in this prototype."
    )
    next_steps: list[str] = Field(..., description="Suggested next steps for the student.")


class GuardrailDecision(BaseModel):
    guardrail_name: str
    requires_approval: bool
    matched_terms: list[str]
    reasons: list[str]
