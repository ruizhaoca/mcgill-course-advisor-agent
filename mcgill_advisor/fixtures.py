from __future__ import annotations

from .models import Course, StudentProfile


COURSES: list[Course] = [
    Course(
        code="COMP 202",
        title="Foundations of Programming",
        department="Computer Science",
        credits=3,
        level=200,
        terms=["Fall", "Winter"],
        tags=["programming", "python", "intro"],
        description="A fictional introduction to computational thinking and Python programming.",
    ),
    Course(
        code="COMP 250",
        title="Data Structures Studio",
        department="Computer Science",
        credits=3,
        level=200,
        terms=["Fall", "Winter"],
        tags=["programming", "data structures", "software"],
        description="A fictional studio course on lists, trees, maps, and testing.",
    ),
    Course(
        code="COMP 251",
        title="Algorithms for Everyday Systems",
        department="Computer Science",
        credits=3,
        level=200,
        terms=["Winter"],
        tags=["algorithms", "proofs", "systems"],
        description="A fictional algorithms course using scheduling, routing, and ranking examples.",
    ),
    Course(
        code="COMP 302",
        title="Programming Languages Workshop",
        department="Computer Science",
        credits=3,
        level=300,
        terms=["Fall"],
        tags=["programming", "languages", "software"],
        description="A fictional survey of language design, interpreters, and type systems.",
    ),
    Course(
        code="COMP 421",
        title="Applied Databases Lab",
        department="Computer Science",
        credits=3,
        level=400,
        terms=["Winter"],
        tags=["data", "databases", "systems"],
        description="A fictional lab on relational design, transactions, and query planning.",
    ),
    Course(
        code="MATH 133",
        title="Vectors, Matrices, and Models",
        department="Mathematics",
        credits=3,
        level=100,
        terms=["Fall", "Winter"],
        tags=["linear algebra", "math", "models"],
        description="A fictional linear algebra course for science students.",
    ),
    Course(
        code="MATH 141",
        title="Calculus for Discovery II",
        department="Mathematics",
        credits=4,
        level=100,
        terms=["Winter"],
        tags=["calculus", "math"],
        description="A fictional second calculus course with applications and modeling.",
    ),
    Course(
        code="MATH 240",
        title="Discrete Structures",
        department="Mathematics",
        credits=3,
        level=200,
        terms=["Fall", "Winter"],
        tags=["discrete math", "proofs", "logic"],
        description="A fictional course on logic, sets, induction, and graph basics.",
    ),
    Course(
        code="ECON 208",
        title="Micro Decisions and Public Life",
        department="Economics",
        credits=3,
        level=200,
        terms=["Fall"],
        tags=["economics", "society", "policy"],
        description="A fictional elective connecting microeconomics with public decisions.",
    ),
    Course(
        code="HIST 210",
        title="Montreal Ideas in Motion",
        department="History",
        credits=3,
        level=200,
        terms=["Fall", "Winter"],
        tags=["writing", "society", "humanities"],
        description="A fictional writing-focused humanities course about urban ideas.",
    ),
]

COURSE_BY_CODE: dict[str, Course] = {course.code: course for course in COURSES}

PREREQUISITES: dict[str, list[str]] = {
    "COMP 250": ["COMP 202"],
    "COMP 251": ["COMP 250", "MATH 240"],
    "COMP 302": ["COMP 250"],
    "COMP 421": ["COMP 251"],
    "MATH 141": ["MATH 140"],
    "MATH 240": ["MATH 133"],
}

STUDENT_PROFILE = StudentProfile(
    student_id="demo-student",
    program="BSc Computer Science, U1",
    year="U1",
    completed_courses=["COMP 202", "MATH 133", "MATH 140", "ECON 208"],
    current_courses=["MATH 240"],
    interests=["software", "data", "ethics"],
    max_recommended_credits=12,
)

POLICY_RULES: list[str] = [
    "This prototype treats missing prerequisites as a high policy risk.",
    "More than 12 requested credits requires advisor approval for the demo student.",
    "A U1 student requesting a 400-level course is flagged for advisor review.",
    "Completed or in-progress courses are flagged to avoid duplicate registration.",
]
