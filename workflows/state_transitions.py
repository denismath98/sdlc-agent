from core.state import SDLCState
from workflows.decision_flow import apply_decision_to_state
from workflows.pr_flow import run_pr_flow
from workflows.review_flow import run_review_flow


def apply_review_step(state: SDLCState) -> SDLCState:
    pr_number = state.get("pr_number")
    if not pr_number:
        raise RuntimeError("Cannot run review step without pr_number in state.")

    review_flow_result = run_review_flow(pr_number)
    updated_state = review_flow_result.state
    updated_state["history"] = state.get("history", []) + updated_state.get(
        "history", []
    )
    return updated_state


def apply_rework_step(state: SDLCState) -> SDLCState:
    pr_number = state.get("pr_number")
    if not pr_number:
        raise RuntimeError("Cannot run rework step without pr_number in state.")

    developer_flow_result = run_pr_flow(pr_number)
    updated_state = developer_flow_result.state
    updated_state["history"] = state.get("history", []) + updated_state.get(
        "history", []
    )
    return updated_state


def apply_decision_step(state: SDLCState) -> str:
    updated_state = apply_decision_to_state(state)
    return updated_state["decision"] or "rework"
