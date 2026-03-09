from core.models import FullIterationResult
from workflows.state_transitions import apply_decision_step
from workflows.pr_flow import run_pr_flow
from workflows.review_flow import run_review_flow


def run_full_iteration_once(pr_number: int) -> FullIterationResult:
    first_review_flow = run_review_flow(pr_number)
    first_decision = apply_decision_step(first_review_flow.state)

    if first_decision != "rework":
        return FullIterationResult(
            first_review_result=first_review_flow.result,
            first_state=first_review_flow.state,
            first_decision=first_decision,
        )

    developer_flow = run_pr_flow(pr_number)
    if not developer_flow.result.success:
        return FullIterationResult(
            first_review_result=first_review_flow.result,
            first_state=first_review_flow.state,
            first_decision=first_decision,
            developer_result=developer_flow.result,
        )

    second_review_flow = run_review_flow(pr_number)
    second_decision = apply_decision_step(second_review_flow.state)

    return FullIterationResult(
        first_review_result=first_review_flow.result,
        first_state=first_review_flow.state,
        first_decision=first_decision,
        developer_result=developer_flow.result,
        second_review_result=second_review_flow.result,
        second_state=second_review_flow.state,
        second_decision=second_decision,
    )
