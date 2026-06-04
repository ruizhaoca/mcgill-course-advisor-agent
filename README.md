# McGill Course Advisor Agent Prototype

## 1. Project Overview

This project is a small but real single-agent system built with the OpenAI Agents
SDK for a fictional McGill-style course advising use case. The agent helps a demo
student reason about possible next courses by searching a small fake catalog,
checking prerequisites, flagging policy-style risks, and returning a structured
recommendation.

Course advising was chosen as the decision-making domain because it requires
combining several constraints: student goals, completed courses, prerequisites,
term load, course level, and escalation rules. That makes it a useful prototype
domain for testing tool use, structured output, guardrails, and evals without
using real student records or real university policy data.

## 2. Scope and Assumptions

This is a single-agent prototype. It is not a multi-agent system, not a
production deployment, and not an official McGill advising tool.

The project uses fake fixtures only:

- A small fictional course catalog
- A fictional prerequisite table
- One demo student profile
- Simple fictional policy-style rules

The system should not be interpreted as modeling real McGill advising,
requirements, enrollment rules, program rules, or course availability.

## 3. Project Structure

```text
mcgill-course-advisor-agent/
+-- mcgill_advisor/
|   +-- agent.py              # McGillCourseAdvisorAgent definition and runner
|   +-- cli.py                # Command-line interface for live runs and evals
|   +-- evals.py              # Eval loading, execution, scoring, and reporting
|   +-- fixtures.py           # Fake catalog, prerequisites, student, and rules
|   +-- guardrails.py         # AdvisorApprovalRequiredGuardrail logic
|   +-- models.py             # Pydantic input/output and tool data models
|   +-- tools.py              # Typed tools exposed to the agent
+-- evals/
|   +-- course_advisor_eval_cases.json
+-- evidence/
|   +-- eval_report_before_fix.txt
|   +-- eval_report_after_fix.txt
|   +-- test_fixture_tools_report.txt
|   +-- reflection_paper.pdf
+-- tests/
|   +-- test_fixture_tools.py
+-- .env.example              # Template for local API key configuration
+-- pyproject.toml            # Package metadata and dependencies
+-- README.md
```

The core agent implementation is in `mcgill_advisor/agent.py`. The fake data is
in `mcgill_advisor/fixtures.py`. The tool implementations are in
`mcgill_advisor/tools.py`. The structured output models are in
`mcgill_advisor/models.py`. The blocking guardrail is in
`mcgill_advisor/guardrails.py`. Eval cases are stored in `evals/`. Evidence,
run reports, and the reflection paper are stored in `evidence/`. Local tests are
stored in `tests/`.

## 4. Setup Instructions

Clone the repository and enter the project directory:

```powershell
git clone https://github.com/ruizhaoca/mcgill-course-advisor-agent.git
cd mcgill-course-advisor-agent
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

Install the project and development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The package dependencies are declared in `pyproject.toml`. The `dev` extra
installs `pytest` for the local test suite.

## 5. API Key Configuration

The live agent and live evals require an OpenAI API key. Start from the tracked
template:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` locally:

```text
OPENAI_API_KEY=sk-your-key-here
```

Do not commit the real API key to GitHub. The `.env` file is ignored by
`.gitignore`; `.env.example` is safe to commit because it contains no secret.

You can optionally set a default model:

```text
OPENAI_MODEL=gpt-5-nano
```

## 6. How to Run the Live Agent

Run the live OpenAI Agents SDK agent from the command line:

```powershell
python -m mcgill_advisor.cli "I completed COMP 202 and want a programming-heavy next term."
```

After installation, the console script can also be used:

```powershell
mcgill-advisor "Suggest two courses for a U1 CS student interested in data."
```

To override the model for one run:

```powershell
python -m mcgill_advisor.cli --model gpt-5-nano "Suggest two eligible courses."
```

## 7. How to Run Evals

Run the eval suite with:

```powershell
python -m mcgill_advisor.cli --evals
```

The eval file is `evals/course_advisor_eval_cases.json`. The project includes at
least 5 eval cases and at least 2 edge or failure cases, including cases for
guardrail blocking and unknown or invalid course requests.

For each case, the eval runner prints the case name, input, live agent output,
eval result, and final pass/fail summary.

## 8. Agent Design

The single agent is `McGillCourseAdvisorAgent`. Its purpose is to advise the demo
student using only the fictional fixtures exposed through tools. The agent is
instructed to:

- Search the fake course catalog for candidate courses
- Check prerequisites for `demo-student`
- Flag policy-style risks before recommending a course
- Avoid recommending courses that are unknown, already completed, in progress,
  missing prerequisites, or risky enough to require advisor approval
- Return only the `CourseRecommendation` structured output

No handoffs or multi-agent process are used because the assignment prototype is
intended to demonstrate one clear agent loop with typed tools, structured output,
guardrails, and evals. Splitting this small fake domain into multiple agents
would add complexity without improving the prototype's decision quality.

## 9. Typed Tools

The agent uses three typed tools from `mcgill_advisor/tools.py`:

- `search_courses`: Searches the small fake course catalog by interest area,
  keyword, or course code and returns ranked fake course matches.
- `check_prerequisites`: Checks whether the demo student has completed or is
  currently taking the fictional prerequisites for requested courses.
- `flag_policy_risk`: Flags fictional advising risks such as high term load,
  missing prerequisites, already completed courses, in-progress courses, unknown
  courses, and upper-level course concerns for the demo profile.

The tools are typed with Pydantic models so the agent receives predictable,
validated tool inputs and outputs.

## 10. Structured Output

The live agent returns a `CourseRecommendation` object defined in
`mcgill_advisor/models.py`. The object includes fields such as the student ID,
summary, recommended courses, policy risks, required approvals, and next steps.

Structured output is useful because downstream code and evals can inspect stable
fields instead of parsing free-form prose. The eval runner uses this structure to
check recommended course codes, forbidden course codes, expected terms, and
failure outcomes.

## 11. Guardrail and Approval Logic

The named blocking guardrail is `AdvisorApprovalRequiredGuardrail`, implemented
in `mcgill_advisor/guardrails.py`.

It blocks requests that should require human advisor approval in this fictional
prototype, such as:

- Prerequisite overrides
- Credit overloads
- Guaranteed enrollment or seat requests
- Program, degree, graduation, or official policy exceptions

When the guardrail trips, the CLI returns a blocked response instead of a course
recommendation. This keeps the prototype from pretending it can approve decisions
that should be escalated to a human advisor.

## 12. State Strategy

What is stored:

- Fake course catalog
- Fake prerequisite table
- Demo student profile
- Fictional policy-style rules

What is passed:

- User prompt
- Course codes
- Student ID
- Requested credits
- Optional model argument

What is recomputed:

- Search results
- Prerequisite status
- Policy risks
- Guardrail decisions
- Eval results
- Final recommendations

The project does not persist live conversation state or real student data. Each
CLI run recomputes the relevant tool results from the fake fixtures.

## 13. Evidence Packet

The evidence packet is stored in `evidence/`. This folder is the project location
for traces, logs, screenshots, run transcripts, and evaluation reports used for
submission.

Included evidence files:

- `evidence/eval_report_before_fix.txt`
- `evidence/eval_report_after_fix.txt`
- `evidence/test_fixture_tools_report.txt`

If additional traces, screenshots, or run transcripts are produced, they should
also be placed in `evidence/` so the full submission packet stays together.

## 14. Reflection Paper

The 1-2 page reflection paper is stored at:

```text
evidence/reflection_paper.pdf
```

It discusses what failed during development, what improved after fixes and evals,
and what risks remain in the prototype.

## 15. Limitations and Risks

- The catalog is small and fictional.
- The prerequisite table and policy rules are simplified fixtures.
- The guardrail is rule-based and may miss requests phrased in unexpected ways.
- Live model behavior can vary across runs and model versions.
- The system cannot replace official human advising.
- The project does not use real McGill data, real student records, or real
  production deployment safeguards.

## 16. Reproducibility Checklist

A professor or TA can rerun the project after cloning the GitHub repository with
the following steps:

- Clone the repository and enter the project directory.
- Create and activate a Python 3.10+ virtual environment.
- Run `python -m pip install -e ".[dev]"`.
- Copy `.env.example` to `.env`.
- Add a real `OPENAI_API_KEY` to `.env` without committing it.
- Run the live agent with `python -m mcgill_advisor.cli "<sample prompt>"`.
- Run evals with `python -m mcgill_advisor.cli --evals`.
- Run local tests with `python -m pytest`.
- Review evidence files in `evidence/`.
- Review the reflection paper at `evidence/reflection_paper.pdf`.
