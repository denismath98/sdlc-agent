from langgraph.graph import END, StateGraph

from core.state import SDLCState
from workflows.state_transitions import (
    apply_decision_step,
    apply_review_step,
    apply_rework_step,
)


def review_node(state: SDLCState) -> SDLCState:
    return apply_review_step(state)


def rework_node(state: SDLCState) -> SDLCState:
    return apply_rework_step(state)


def decide_node(state: SDLCState) -> SDLCState:
    apply_decision_step(state)
    return state


def route_after_decision(state: SDLCState) -> str:
    decision = state.get("decision")

    if decision == "approve":
        return "approve"

    if decision == "stop":
        return "stop"

    return "rework"


def build_review_rework_graph():
    graph = StateGraph(SDLCState)

    graph.add_node("review", review_node)
    graph.add_node("decide", decide_node)
    graph.add_node("rework", rework_node)

    graph.set_entry_point("review")
    graph.add_edge("review", "decide")

    graph.add_conditional_edges(
        "decide",
        route_after_decision,
        {
            "approve": END,
            "stop": END,
            "rework": "rework",
        },
    )

    graph.add_edge("rework", "review")

    return graph.compile()
