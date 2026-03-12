import argparse

from nodes.planner import plan_github_issue
from nodes.reviewer import review_and_apply_pull_request
from workflows.pr_flow import run_pr_flow
from workflows.review_flow import run_review_flow
from workflows.sdlc_flow import run_sdlc_issue_flow


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    issue_parser = subparsers.add_parser("issue")
    issue_parser.add_argument("--issue", type=int, required=True)

    pr_parser = subparsers.add_parser("pr")
    pr_parser.add_argument("--pr", type=int, required=True)

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("--pr", type=int, required=True)

    review_apply_parser = subparsers.add_parser("review-apply")
    review_apply_parser.add_argument("--pr", type=int, required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--issue", type=int, required=True)

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

    if args.command == "review-apply":
        result = review_and_apply_pull_request(args.pr)
        print(result)
        return

    if args.command == "plan":
        result = plan_github_issue(args.issue)
        print(result)
        return


if __name__ == "__main__":
    main()
