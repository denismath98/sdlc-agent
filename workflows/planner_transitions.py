from core.state import SDLCState
from nodes.planner import plan_github_issue


def apply_planner_step(state: SDLCState) -> SDLCState:
    issue_number = state.get("issue_number")
    if not issue_number:
        raise RuntimeError("Cannot run planner step without issue_number in state.")

    plan_result = plan_github_issue(issue_number)
    state["plan"] = plan_result.plan
    state["history"].append(
        f"planner_flow: plan generated (issue={issue_number}, steps={len(plan_result.plan)})"
    )
    return state
