from core.state import SDLCState
from services.github_issue_service import load_issue_data


def build_issue_graph_state(issue_number: int) -> SDLCState:
    issue_data = load_issue_data(issue_number)

    return SDLCState(
        issue_number=issue_data.number,
        issue_title=issue_data.title,
        issue_body=issue_data.body,
        branch_name="",
        pr_number=None,
        iteration=1,
        max_iterations=3,
        plan=[],
        changed_files=[],
        ci_status=None,
        ci_summary=[],
        review_status=None,
        review_issues=[],
        review_suggestions=[],
        decision=None,
        history=[],
        done=False,
    )
