from core.models import PlanResult
from services.llm_service import llm_chat
from services.github_issue_service import load_issue_data
from prompts.registry import get_prompt


def parse_plan_output(text: str) -> PlanResult:
    plan: list[str] = []
    acceptance_criteria: list[str] = []

    section = None
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()

        if lower.startswith("plan:"):
            section = "plan"
            continue

        if lower.startswith("acceptance_criteria:"):
            section = "acceptance_criteria"
            continue

        if line.startswith("- "):
            item = line[2:].strip()
            if not item:
                continue

            if section == "plan":
                plan.append(item)
            elif section == "acceptance_criteria":
                acceptance_criteria.append(item)

    return PlanResult(
        plan=plan,
        acceptance_criteria=acceptance_criteria,
    )


def build_planner_prompt(issue_title: str, issue_body: str) -> str:
    template = get_prompt("planner.issue")
    return template.format(
        title=issue_title,
        body=issue_body,
    )


def plan_issue(issue_title: str, issue_body: str) -> PlanResult:
    prompt = build_planner_prompt(issue_title, issue_body)
    llm_out, _ = llm_chat(prompt)

    result = parse_plan_output(llm_out)

    if not result.plan:
        result.plan = [
            "Inspect the existing code related to the requested functionality.",
            "Implement the required code changes.",
            "Add or update tests for the new behavior.",
            "Verify that the changes satisfy the issue requirements.",
        ]

    if not result.acceptance_criteria:
        result.acceptance_criteria = [
            "The implementation matches the issue requirements.",
            "The code changes are substantive.",
            "Relevant tests pass successfully.",
        ]

    return result


def plan_github_issue(issue_number: int) -> PlanResult:
    issue_data = load_issue_data(issue_number)
    return plan_issue(issue_data.title, issue_data.body)
