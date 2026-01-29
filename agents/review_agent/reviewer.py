import argparse
import os
import re
from typing import Optional

from github import Github

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


def ensure_label(repo, name: str, color: str) -> None:
    try:
        repo.get_label(name)
    except Exception:
        repo.create_label(
            name=name, color=color, description="Auto label by AI reviewer"
        )


def extract_issue_number(pr_body: str) -> Optional[int]:
    # expects "Closes #123"
    m = re.search(r"Closes\s+#(\d+)", pr_body or "", flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, required=True)
    args = parser.parse_args()

    gh = Github(get_token())
    repo = gh.get_repo(get_repo_full_name())
    pr = repo.get_pull(args.pr)

    ensure_label(repo, APPROVED_LABEL, "2da44e")  # green
    ensure_label(repo, NEEDS_FIX_LABEL, "d1242f")  # red

    issue_no = extract_issue_number(pr.body or "")
    issue_text = ""
    if issue_no:
        issue = repo.get_issue(issue_no)
        issue_text = (issue.body or "").strip()

    # Minimal reviewer logic for skeleton:
    # Since this job runs after CI succeeded (needs: ci), we approve.
    status = "approved"
    issues = ["CI passed. Skeleton reviewer approves this iteration."]
    suggestions = ["Next step: implement real diff/requirements analysis."]

    review_body = (
        "AI-REVIEW:\n"
        f"status={status}\n"
        "issues:\n" + "\n".join([f"- {x}" for x in issues]) + "\n"
        "suggestions:\n" + "\n".join([f"- {x}" for x in suggestions]) + "\n\n"
        "Context:\n"
        f"- Issue: #{issue_no if issue_no else 'N/A'}\n"
        f"- Issue details length: {len(issue_text)}\n"
    )

    # Remove needs-fix if present, add approved
    current_labels = [label.name for label in pr.get_labels()]
    if NEEDS_FIX_LABEL in current_labels:
        pr.remove_from_labels(NEEDS_FIX_LABEL)
    pr.add_to_labels(APPROVED_LABEL)

    # Publish as PR comment + as a Review (comment-only)
    pr.create_issue_comment(review_body)
    pr.create_review(body=review_body, event="COMMENT")

    print(f"OK: Reviewed PR #{args.pr} -> {status}")


if __name__ == "__main__":
    main()
