from langgraph.graph import END, StateGraph

from core.state import SDLCState
from workflows.developer_transitions import apply_developer_issue_step
from workflows.planner_transitions import apply_planner_step
from workflows.state_transitions import (
    apply_decision_step,
    apply_review_step,
    apply_rework_step,
)


def planner_node(state: SDLCState) -> SDLCState:
    return apply_planner_step(state)


def developer_node(state: SDLCState) -> SDLCState:
    return apply_developer_issue_step(state)


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


def build_sdlc_graph():
    graph = StateGraph(SDLCState)

    graph.add_node("planner", planner_node)
    graph.add_node("developer", developer_node)
    graph.add_node("review", review_node)
    graph.add_node("decide", decide_node)
    graph.add_node("rework", rework_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "developer")
    graph.add_edge("developer", "review")
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
