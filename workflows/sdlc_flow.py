from core.models import StatefulDeveloperResult
from workflows.issue_flow import run_issue_flow


def run_sdlc_issue_flow(issue_number: int) -> StatefulDeveloperResult:
    return run_issue_flow(issue_number)
