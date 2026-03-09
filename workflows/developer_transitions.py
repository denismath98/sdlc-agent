from core.state import SDLCState
from nodes.developer import run_developer_for_issue


def apply_developer_issue_step(state: SDLCState) -> SDLCState:
    issue_number = state.get("issue_number")
    if not issue_number:
        raise RuntimeError(
            "Cannot run developer issue step without issue_number in state."
        )

    iteration = state.get("iteration", 1)
    developer_result = run_developer_for_issue(issue_number, iteration=iteration)

    state["branch_name"] = developer_result.branch_name or state.get("branch_name", "")
    state["pr_number"] = developer_result.pr_number
    state["done"] = developer_result.success

    state["history"].append(
        f"developer_flow: initial implementation completed "
        f"(success={developer_result.success}, issue={issue_number}, pr={developer_result.pr_number})"
    )

    return state
