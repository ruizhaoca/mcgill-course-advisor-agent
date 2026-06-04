"""Fictional McGill-style course advising prototype."""

from .agent import McGillCourseAdvisorAgent, build_agent
from .models import CourseRecommendation

__all__ = [
    "CourseRecommendation",
    "McGillCourseAdvisorAgent",
    "build_agent",
]
