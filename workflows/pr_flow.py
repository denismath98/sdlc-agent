from core.models import DeveloperResult, StatefulDeveloperResult
from core.state import SDLCState
from services.github_service import (
    extract_issue_number_from_pr_body,
    extract_iteration_from_pr_body,
    get_pull_request,
)
from services.github_issue_service import load_issue_data
from nodes.planner import plan_github_issue
from nodes.developer import run_developer_for_pr


def build_pr_state(pr_number: int) -> SDLCState:
    pr = get_pull_request(pr_number)

    issue_number = extract_issue_number_from_pr_body(pr.body or "")
    iteration = extract_iteration_from_pr_body(pr.body or "")

    issue_title = ""
    issue_body = ""
    plan = []

    if issue_number:
        issue_data = load_issue_data(issue_number)
        issue_title = issue_data.title
        issue_body = issue_data.body

        plan_result = plan_github_issue(issue_number)
        plan = plan_result.plan

    return SDLCState(
        issue_number=issue_number or 0,
        issue_title=issue_title,
        issue_body=issue_body,
        branch_name=pr.head.ref,
        pr_number=pr.number,
        iteration=iteration,
        max_iterations=3,
        plan=plan,
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


def run_pr_flow(pr_number: int) -> StatefulDeveloperResult:
    state = build_pr_state(pr_number)
    result = run_developer_for_pr(pr_number)

    state["branch_name"] = result.branch_name or state["branch_name"]
    state["pr_number"] = result.pr_number or state["pr_number"]
    state["iteration"] = (
        state["iteration"] + 1 if result.success else state["iteration"]
    )

    state["history"].append(
        f"pr_flow: rework run completed (success={result.success}, pr={pr_number}, iteration={state['iteration']})"
    )

    if result.success:
        state["done"] = True

    return StatefulDeveloperResult(
        result=result,
        state=state,
    )
