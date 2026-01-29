import argparse
import os
import re
import subprocess
from datetime import datetime
from typing import Optional

from github import Github


def sh(cmd: list[str]) -> str:
    res = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return res.stdout.strip()


def safe_branch_name(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\-_.]+", "-", s).strip("-")
    return s[:60] if len(s) > 60 else s


def ensure_git_identity() -> None:
    sh(["git", "config", "user.name", "code-agent[bot]"])
    sh(["git", "config", "user.email", "code-agent[bot]@users.noreply.github.com"])


def create_or_update_branch(branch: str) -> None:
    # ensure we're on default branch (assume main; if not, actions/checkout usually checks PR branch only,
    # but for issues workflow it checks default branch)
    sh(["git", "checkout", "-B", branch])


def commit_change(message: str) -> None:
    sh(["git", "add", "-A"])
    sh(["git", "commit", "-m", message])


def push_branch(branch: str) -> None:
    sh(["git", "push", "-u", "origin", branch])


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


def find_existing_pr(gh_repo, head: str) -> Optional[int]:
    # head format for PyGithub: "owner:branch"
    pulls = gh_repo.get_pulls(state="open", head=head)
    for pr in pulls:
        return pr.number
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    args = parser.parse_args()

    gh = Github(get_token())
    repo_full = get_repo_full_name()
    gh_repo = gh.get_repo(repo_full)

    issue = gh_repo.get_issue(number=args.issue)
    title = issue.title or f"Issue {args.issue}"
    body = issue.body or ""

    owner = repo_full.split("/")[0]
    base_branch = gh_repo.default_branch  # main/master
    branch = f"issue-{args.issue}-{safe_branch_name(title)}"

    ensure_git_identity()

    # Make sure we start from default branch latest
    sh(["git", "fetch", "origin", base_branch])
    sh(["git", "checkout", base_branch])
    sh(["git", "reset", "--hard", f"origin/{base_branch}"])

    # Create/update branch
    create_or_update_branch(branch)

    # Minimal deterministic "change" so that PR exists
    os.makedirs(".ai", exist_ok=True)
    out_path = f".ai/issue-{args.issue}.md"
    now = datetime.utcnow().isoformat() + "Z"
    content = (
        f"# Issue {args.issue}\n\n"
        f"## Title\n{title}\n\n"
        f"## Body\n{body}\n\n"
        f"## Generated\n{now}\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Commit (if no changes, skip commit)
    status = sh(["git", "status", "--porcelain"])
    if status:
        commit_change(f"Implement Issue #{args.issue}: scaffold change")
        push_branch(branch)
    else:
        # still push branch to ensure it exists remotely
        push_branch(branch)

    head = f"{owner}:{branch}"
    existing = find_existing_pr(gh_repo, head=head)

    pr_title = f"Implement #{args.issue}: {title}"
    pr_body = (
        f"Closes #{args.issue}\n\n"
        f"AI-ITERATION: 1\n\n"
        f"Auto-generated initial scaffold change.\n"
    )

    if existing:
        pr = gh_repo.get_pull(existing)
        pr.create_issue_comment("Code Agent: updated branch with new changes.")
        issue.create_comment(f"Code Agent: updated existing PR #{pr.number}")
    else:
        pr = gh_repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch,
            base=base_branch,
            draft=False,
        )
        issue.create_comment(f"Code Agent: created PR #{pr.number}")

    print(f"OK: PR #{pr.number} for Issue #{args.issue}")


if __name__ == "__main__":
    main()