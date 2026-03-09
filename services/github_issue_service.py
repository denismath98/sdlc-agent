from dataclasses import dataclass

from services.github_service import get_repo


@dataclass
class IssueData:
    number: int
    title: str
    body: str


def get_issue(issue_number: int):
    repo = get_repo()
    return repo.get_issue(number=issue_number)


def load_issue_data(issue_number: int) -> IssueData:
    issue = get_issue(issue_number)

    return IssueData(
        number=issue.number,
        title=issue.title or "",
        body=issue.body or "",
    )


def create_issue_comment(issue_number: int, body: str) -> None:
    issue = get_issue(issue_number)
    issue.create_comment(body)
