from core.models import ReviewDecisionResult
from workflows.decision_flow import decide_next_step
from workflows.review_flow import run_review_flow


def run_review_and_decide(pr_number: int) -> ReviewDecisionResult:
    review_flow_result = run_review_flow(pr_number)
    decision = decide_next_step(review_flow_result.state)

    return ReviewDecisionResult(
        review_result=review_flow_result.result,
        state=review_flow_result.state,
        decision=decision,
    )
