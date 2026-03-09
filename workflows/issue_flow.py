from core.models import DeveloperResult, StatefulDeveloperResult
from core.state import SDLCState
from services.github_issue_service import load_issue_data
from nodes.planner import plan_github_issue
from nodes.developer import run_developer_for_issue


def build_initial_issue_state(issue_number: int) -> SDLCState:
    issue_data = load_issue_data(issue_number)
    plan_result = plan_github_issue(issue_number)

    return SDLCState(
        issue_number=issue_data.number,
        issue_title=issue_data.title,
        issue_body=issue_data.body,
        branch_name="",
        pr_number=None,
        iteration=1,
        max_iterations=3,
        plan=plan_result.plan,
        changed_files=[],
        ci_status=None,
        ci_summary=[],
        review_status=None,
        review_issues=[],
        review_suggestions=[],
        done=False,
        decision=None,
        history=[],
    )


def run_issue_flow(issue_number: int) -> StatefulDeveloperResult:
    state = build_initial_issue_state(issue_number)

    result = run_developer_for_issue(issue_number, iteration=state["iteration"])

    state["branch_name"] = result.branch_name or ""
    state["pr_number"] = result.pr_number
    state["history"].append(
        f"issue_flow: developer run completed (success={result.success}, issue={issue_number})"
    )

    if result.success:
        state["done"] = True

    return StatefulDeveloperResult(
        result=result,
        state=state,
    )
