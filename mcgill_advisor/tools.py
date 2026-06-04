from __future__ import annotations

import re
from typing import Annotated

from agents import function_tool
from pydantic import Field

from .fixtures import COURSE_BY_CODE, COURSES, PREREQUISITES, STUDENT_PROFILE
from .models import (
    CourseMatch,
    CourseSearchResult,
    PolicyRisk,
    PolicyRiskReport,
    PrerequisiteCheckResult,
    PrerequisiteStatus,
    StudentProfile,
)


def normalize_course_code(raw_code: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]", "", raw_code).upper()
    match = re.fullmatch(r"([A-Z]{3,4})([0-9]{3})", compact)
    if not match:
        return " ".join(raw_code.upper().split())
    return f"{match.group(1)} {match.group(2)}"


def get_student_profile(student_id: str) -> StudentProfile:
    if student_id != STUDENT_PROFILE.student_id:
        raise ValueError(
            f"Unknown student_id {student_id!r}; this prototype only has demo-student."
        )
    return STUDENT_PROFILE


def extract_course_codes(text: str) -> list[str]:
    matches = re.findall(r"\b[A-Za-z]{3,4}\s*-?\s*[0-9]{3}\b", text)
    normalized = [normalize_course_code(match) for match in matches]
    return list(dict.fromkeys(normalized))


def _score_course(query: str, course_code: str) -> tuple[int, list[str]]:
    course = COURSE_BY_CODE[course_code]
    normalized_query = query.lower()
    query_terms = re.findall(r"[a-z0-9]+", normalized_query)
    score = 0
    reasons: list[str] = []

    if normalize_course_code(query) == course.code:
        score += 100
        reasons.append("exact course-code match")

    searchable_parts = {
        "code": course.code.lower(),
        "title": course.title.lower(),
        "department": course.department.lower(),
        "tags": " ".join(course.tags).lower(),
        "description": course.description.lower(),
    }

    for term in query_terms:
        if term in searchable_parts["code"]:
            score += 7
            reasons.append(f"code contains {term}")
        if term in searchable_parts["title"]:
            score += 5
            reasons.append(f"title mentions {term}")
        if term in searchable_parts["tags"]:
            score += 4
            reasons.append(f"tagged {term}")
        if term in searchable_parts["department"]:
            score += 3
            reasons.append(f"department matches {term}")
        if term in searchable_parts["description"]:
            score += 2
            reasons.append(f"description mentions {term}")

    return score, reasons


def search_courses_impl(query: str, limit: int) -> CourseSearchResult:
    limit = max(1, min(limit, len(COURSES)))
    scored: list[CourseMatch] = []

    for course in COURSES:
        score, reasons = _score_course(query, course.code)
        if score <= 0:
            continue
        scored.append(
            CourseMatch(
                code=course.code,
                title=course.title,
                credits=course.credits,
                terms=course.terms,
                tags=course.tags,
                match_score=score,
                why_matched="; ".join(dict.fromkeys(reasons)),
            )
        )

    scored.sort(key=lambda item: (-item.match_score, item.code))
    return CourseSearchResult(query=query, matches=scored[:limit])


def check_prerequisites_impl(
    course_codes: list[str],
    student_id: str,
) -> PrerequisiteCheckResult:
    student = get_student_profile(student_id)
    completed = {normalize_course_code(code) for code in student.completed_courses}
    current = {normalize_course_code(code) for code in student.current_courses}
    checks: list[PrerequisiteStatus] = []

    for raw_code in course_codes:
        code = normalize_course_code(raw_code)
        required = PREREQUISITES.get(code, [])
        met = [prereq for prereq in required if prereq in completed]
        in_progress = [prereq for prereq in required if prereq in current]
        missing = [
            prereq for prereq in required if prereq not in completed and prereq not in current
        ]
        eligible = len(missing) == 0

        if not required:
            note = "No prerequisites listed in the fake fixture table."
        elif missing:
            note = "Missing prerequisite(s): " + ", ".join(missing)
        elif in_progress:
            note = "Eligible if in-progress prerequisite(s) are completed: " + ", ".join(
                in_progress
            )
        else:
            note = "All listed prerequisites are completed."

        checks.append(
            PrerequisiteStatus(
                course_code=code,
                eligible=eligible,
                met_prerequisites=met,
                in_progress_prerequisites=in_progress,
                missing_prerequisites=missing,
                note=note,
            )
        )

    return PrerequisiteCheckResult(student_id=student.student_id, checks=checks)


def flag_policy_risk_impl(
    course_codes: list[str],
    requested_credits: int,
    student_id: str,
) -> PolicyRiskReport:
    student = get_student_profile(student_id)
    normalized_codes = [normalize_course_code(code) for code in course_codes]
    completed = {normalize_course_code(code) for code in student.completed_courses}
    current = {normalize_course_code(code) for code in student.current_courses}
    prereq_checks = check_prerequisites_impl(normalized_codes, student.student_id)
    risks: list[PolicyRisk] = []

    if requested_credits > student.max_recommended_credits:
        risks.append(
            PolicyRisk(
                course_code="TERM LOAD",
                severity="high",
                message=(
                    f"Requested {requested_credits} credits exceeds the demo "
                    f"student limit of {student.max_recommended_credits}."
                ),
                requires_advisor_approval=True,
            )
        )

    prereq_by_code = {check.course_code: check for check in prereq_checks.checks}

    for code in normalized_codes:
        course = COURSE_BY_CODE.get(code)
        if course is None:
            risks.append(
                PolicyRisk(
                    course_code=code,
                    severity="medium",
                    message="Course code is not in the fake fixture catalog.",
                    requires_advisor_approval=True,
                )
            )
            continue

        if code in completed:
            risks.append(
                PolicyRisk(
                    course_code=code,
                    severity="info",
                    message=f"{code} is already completed in the demo profile.",
                    requires_advisor_approval=False,
                )
            )

        if code in current:
            risks.append(
                PolicyRisk(
                    course_code=code,
                    severity="info",
                    message=f"{code} is already in progress in the demo profile.",
                    requires_advisor_approval=False,
                )
            )

        prereq_status = prereq_by_code.get(code)
        if prereq_status and prereq_status.missing_prerequisites:
            risks.append(
                PolicyRisk(
                    course_code=code,
                    severity="high",
                    message=(
                        f"{code} has missing prerequisite(s): "
                        + ", ".join(prereq_status.missing_prerequisites)
                    ),
                    requires_advisor_approval=True,
                )
            )

        if student.year in {"U0", "U1"} and course.level >= 400:
            risks.append(
                PolicyRisk(
                    course_code=code,
                    severity="medium",
                    message=f"{code} is a 400-level course for a {student.year} demo student.",
                    requires_advisor_approval=True,
                )
            )

    return PolicyRiskReport(
        student_id=student.student_id,
        requested_credits=requested_credits,
        risks=risks,
    )


@function_tool
def search_courses(
    query: Annotated[
        str,
        Field(description="Search phrase, interest area, or fictional course code."),
    ],
    limit: Annotated[
        int,
        Field(ge=1, le=10, description="Maximum number of fake course matches to return."),
    ],
) -> CourseSearchResult:
    """Search the tiny fake McGill-style course catalog."""

    return search_courses_impl(query=query, limit=limit)


@function_tool
def check_prerequisites(
    course_codes: Annotated[
        list[str],
        Field(description="Fictional course codes to check, such as ['COMP 250']."),
    ],
    student_id: Annotated[
        str,
        Field(description="Use 'demo-student' for the included fake profile."),
    ],
) -> PrerequisiteCheckResult:
    """Check fake prerequisite rules for the demo student profile."""

    return check_prerequisites_impl(course_codes=course_codes, student_id=student_id)


@function_tool
def flag_policy_risk(
    course_codes: Annotated[
        list[str],
        Field(description="Fictional course codes being considered."),
    ],
    requested_credits: Annotated[
        int,
        Field(ge=0, le=30, description="Total term credits requested by the student."),
    ],
    student_id: Annotated[
        str,
        Field(description="Use 'demo-student' for the included fake profile."),
    ],
) -> PolicyRiskReport:
    """Flag fake policy-style advising risks for candidate courses."""

    return flag_policy_risk_impl(
        course_codes=course_codes,
        requested_credits=requested_credits,
        student_id=student_id,
    )
