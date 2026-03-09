import argparse

from nodes.planner import plan_github_issue
from workflows.pr_flow import run_pr_flow
from workflows.review_flow import run_review_flow, build_review_state
from workflows.review_decision_flow import run_review_and_decide
from workflows.sdlc_flow import run_sdlc_issue_flow
from workflows.rework_flow import run_review_decide_rework_once
from workflows.full_iteration_flow import run_full_iteration_once
from workflows.state_transitions import (
    apply_decision_step,
    apply_review_step,
    apply_rework_step,
)
from workflows.langgraph_flow import build_review_rework_graph
from workflows.langgraph_sdlc_flow import build_sdlc_graph
from workflows.graph_state_builders import build_issue_graph_state


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    issue_parser = subparsers.add_parser("issue")
    issue_parser.add_argument("--issue", type=int, required=True)

    pr_parser = subparsers.add_parser("pr")
    pr_parser.add_argument("--pr", type=int, required=True)

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("--pr", type=int, required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--issue", type=int, required=True)

    decide_parser = subparsers.add_parser("decide")
    decide_parser.add_argument("--pr", type=int, required=True)

    rework_parser = subparsers.add_parser("rework-once")
    rework_parser.add_argument("--pr", type=int, required=True)

    iterate_parser = subparsers.add_parser("iterate-once")
    iterate_parser.add_argument("--pr", type=int, required=True)

    transition_review_parser = subparsers.add_parser("transition-review")
    transition_review_parser.add_argument("--pr", type=int, required=True)

    transition_rework_parser = subparsers.add_parser("transition-rework")
    transition_rework_parser.add_argument("--pr", type=int, required=True)

    transition_decide_parser = subparsers.add_parser("transition-decide")
    transition_decide_parser.add_argument("--pr", type=int, required=True)

    graph_parser = subparsers.add_parser("graph-review-rework")
    graph_parser.add_argument("--pr", type=int, required=True)

    graph_sdlc_parser = subparsers.add_parser("graph-sdlc")
    graph_sdlc_parser.add_argument("--issue", type=int, required=True)

    args = parser.parse_args()

    if args.command == "issue":
        flow_result = run_sdlc_issue_flow(args.issue)
        print(flow_result.result)
        print(flow_result.state)
        return

    if args.command == "pr":
        flow_result = run_pr_flow(args.pr)
        print(flow_result.result)
        print(flow_result.state)
        return

    if args.command == "review":
        flow_result = run_review_flow(args.pr)
        print(flow_result.result)
        print(flow_result.state)
        return

    if args.command == "plan":
        res = plan_github_issue(args.issue)
        print(res)
        return

    if args.command == "decide":
        decision_result = run_review_and_decide(args.pr)
        print(decision_result.review_result)
        print(decision_result.state)
        print(decision_result.decision)
        return

    if args.command == "rework-once":
        decision_result, developer_flow_result = run_review_decide_rework_once(args.pr)
        print(decision_result.review_result)
        print(decision_result.state)
        print(decision_result.decision)
        print(developer_flow_result)
        return

    if args.command == "iterate-once":
        iteration_result = run_full_iteration_once(args.pr)
        print(iteration_result.first_review_result)
        print(iteration_result.first_state)
        print(iteration_result.first_decision)
        print(iteration_result.developer_result)
        print(iteration_result.second_review_result)
        print(iteration_result.second_state)
        print(iteration_result.second_decision)
        return

    if args.command == "transition-review":
        state = build_review_state(args.pr)
        updated_state = apply_review_step(state)
        print(updated_state)
        return

    if args.command == "transition-rework":
        state = build_review_state(args.pr)
        updated_state = apply_rework_step(state)
        print(updated_state)
        return

    if args.command == "transition-decide":
        state = build_review_state(args.pr)
        decision = apply_decision_step(state)
        print(decision)
        print(state)
        return

    if args.command == "graph-review-rework":
        graph = build_review_rework_graph()
        initial_state = build_review_state(args.pr)
        final_state = graph.invoke(initial_state)
        print("FINAL STATE:")
        print(final_state)
        print("FINAL DECISION:")
        print(final_state.get("decision"))
        print("FINAL REVIEW STATUS:")
        print(final_state.get("review_status"))
        print("HISTORY:")
        for item in final_state.get("history", []):
            print(item)
        return

    if args.command == "graph-sdlc":
        graph = build_sdlc_graph()
        initial_state = build_issue_graph_state(args.issue)
        final_state = graph.invoke(initial_state)
        print("FINAL STATE:")
        print(final_state)
        print("FINAL DECISION:")
        print(final_state.get("decision"))
        print("FINAL PLAN:")
        print(final_state.get("plan"))
        print("FINAL PR:")
        print(final_state.get("pr_number"))
        print("HISTORY:")
        for item in final_state.get("history", []):
            print(item)
        return


if __name__ == "__main__":
    main()
