import os
import re
from typing import Optional

from github import Auth, Github

APPROVED_LABEL = "ai:approved"
NEEDS_FIX_LABEL = "ai:needs-fix"


def get_repo_full_name() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("GITHUB_REPOSITORY env var is missing")
    return repo


def get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env var is missing")
    return token


def get_github_client() -> Github:
    return Github(auth=Auth.Token(get_token()))


def get_repo():
    gh = get_github_client()
    return gh.get_repo(get_repo_full_name())


def get_pull_request(pr_number: int):
    repo = get_repo()
    return repo.get_pull(pr_number)


def ensure_label(repo, name: str, color: str) -> None:
    try:
        repo.get_label(name)
    except Exception:
        repo.create_label(
            name=name,
            color=color,
            description="Auto label by AI reviewer",
        )


def ensure_ai_labels(repo) -> None:
    ensure_label(repo, APPROVED_LABEL, "2da44e")
    ensure_label(repo, NEEDS_FIX_LABEL, "d1242f")


def ci_state_for_pr(repo, pr) -> Optional[str]:
    try:
        combined = repo.get_commit(pr.head.sha).get_combined_status()
        return combined.state
    except Exception:
        return None


def apply_labels(pr, status: str) -> None:
    current = {lbl.name for lbl in pr.get_labels()}

    if status == "approved":
        if NEEDS_FIX_LABEL in current:
            pr.remove_from_labels(NEEDS_FIX_LABEL)
        pr.add_to_labels(APPROVED_LABEL)
        return

    if APPROVED_LABEL in current:
        pr.remove_from_labels(APPROVED_LABEL)
    if NEEDS_FIX_LABEL in current:
        pr.remove_from_labels(NEEDS_FIX_LABEL)
    pr.add_to_labels(NEEDS_FIX_LABEL)


def create_issue_comment(pr, body: str) -> None:
    pr.create_issue_comment(body)


def create_pull_request(repo, title: str, body: str, head: str, base: str):
    return repo.create_pull(
        title=title,
        body=body,
        head=head,
        base=base,
    )


def extract_issue_number_from_pr_body(pr_body: str):
    m = re.search(r"Closes\s+#(\d+)", pr_body or "", flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def extract_iteration_from_pr_body(pr_body: str) -> int:
    m = re.search(r"AI-ITERATION:\s*(\d+)", pr_body or "", flags=re.IGNORECASE)
    return int(m.group(1)) if m else 1


def update_pr_iteration(pr, iteration: int) -> None:
    new_body = re.sub(
        r"AI-ITERATION:\s*\d+",
        f"AI-ITERATION: {iteration}",
        pr.body or "",
    )
    pr.edit(body=new_body)


def create_pr_comment(pr, body: str) -> None:
    pr.create_issue_comment(body)


def get_pr_issue_comments(pr, limit: int = 10) -> list[str]:
    comments = []
    try:
        for comment in pr.get_issue_comments():
            body = (comment.body or "").strip()
            if body:
                comments.append(body)
    except Exception:
        return []

    if limit > 0:
        return comments[-limit:]
    return comments


def get_latest_ai_review_comment(pr) -> str:
    comments = get_pr_issue_comments(pr, limit=20)
    for body in reversed(comments):
        if body.startswith("AI-REVIEW:"):
            return body
    return ""
