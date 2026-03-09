from core.state import SDLCState


def decide_next_step(state: SDLCState) -> str:
    review_status = state.get("review_status")
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 3)

    if review_status == "approved":
        return "approve"

    if iteration >= max_iterations:
        return "stop"

    return "rework"


def apply_decision_to_state(state: SDLCState) -> SDLCState:
    state["decision"] = decide_next_step(state)
    state["history"].append(
        f"decision_flow: decision={state['decision']} (iteration={state['iteration']})"
    )
    return state
