from typing import List, Optional, TypedDict


class SDLCState(TypedDict):
    issue_number: int
    issue_title: str
    issue_body: str

    branch_name: str
    pr_number: Optional[int]

    iteration: int
    max_iterations: int

    plan: List[str]
    changed_files: List[str]

    ci_status: Optional[str]
    ci_summary: List[str]

    review_status: Optional[str]
    review_issues: List[str]
    review_suggestions: List[str]

    decision: Optional[str]
    history: List[str]

    done: bool
