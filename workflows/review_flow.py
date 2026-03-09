from core.models import ReviewResult, StatefulReviewResult
from core.state import SDLCState
from services.github_service import (
    extract_issue_number_from_pr_body,
    extract_iteration_from_pr_body,
    get_pull_request,
)
from services.github_issue_service import load_issue_data
from nodes.reviewer import review_pull_request


def build_review_state(pr_number: int) -> SDLCState:
    pr = get_pull_request(pr_number)

    issue_number = extract_issue_number_from_pr_body(pr.body or "")
    iteration = extract_iteration_from_pr_body(pr.body or "")

    issue_title = ""
    issue_body = ""

    if issue_number:
        issue_data = load_issue_data(issue_number)
        issue_title = issue_data.title
        issue_body = issue_data.body

    return SDLCState(
        issue_number=issue_number or 0,
        issue_title=issue_title,
        issue_body=issue_body,
        branch_name=pr.head.ref,
        pr_number=pr.number,
        iteration=iteration,
        max_iterations=3,
        plan=[],
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


def run_review_flow(pr_number: int) -> StatefulReviewResult:
    state = build_review_state(pr_number)
    result = review_pull_request(pr_number)

    state["review_status"] = result.status
    state["review_issues"] = result.issues
    state["review_suggestions"] = result.suggestions
    state["ci_status"] = result.ci_state
    state["decision"] = None
    state["history"].append(
        f"review_flow: review completed (status={result.status}, pr={pr_number})"
    )

    if result.status == "approved":
        state["done"] = True

    return StatefulReviewResult(
        result=result,
        state=state,
    )
