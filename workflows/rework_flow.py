from core.models import DeveloperResult, ReviewDecisionResult, StatefulDeveloperResult
from workflows.pr_flow import run_pr_flow
from workflows.review_decision_flow import run_review_and_decide


def run_review_decide_rework_once(
    pr_number: int,
) -> tuple[ReviewDecisionResult, StatefulDeveloperResult | None]:
    decision_result = run_review_and_decide(pr_number)

    if decision_result.decision != "rework":
        return decision_result, None

    developer_flow_result = run_pr_flow(pr_number)
    return decision_result, developer_flow_result
