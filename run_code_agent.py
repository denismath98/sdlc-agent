import argparse
import os
import re
import subprocess
from datetime import datetime
from typing import Optional

from github import Auth, Github

MAX_ITERATIONS = 3
AI_DIR = ".ai"


def sh(cmd: list[str]) -> str:
    """Run command and return stdout. Raises on non-zero exit."""
    res = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return res.stdout.strip()


def safe_branch_name(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\-_.]+", "-", text).strip("-")
    return text[:60] if len(text) > 60 else text


def ensure_git_identity() -> None:
    sh(["git", "config", "user.name", "code-agent[bot]"])
    sh(["git", "config", "user.email", "code-agent[bot]@users.noreply.github.com"])


def commit_change(message: str) -> None:
    sh(["git", "add", "-A"])
    sh(["git", "commit", "-m", message])


def push_branch(branch: str) -> None:
    # No force push: some repos/rulesets disallow it.
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


def gh_client() -> Github:
    # New-style auth API (no deprecation warnings)
    return Github(auth=Auth.Token(get_token()))


def find_existing_pr(gh_repo, head: str) -> Optional[int]:
    pulls = gh_repo.get_pulls(state="open", head=head)
    for pr in pulls:
        return pr.number
    return None


def extract_issue_number_from_pr(pr_body: str) -> Optional[int]:
    m = re.search(r"Closes\s+#(\d+)", pr_body or "", flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_iteration(pr_body: str) -> int:
    m = re.search(r"AI-ITERATION:\s*(\d+)", pr_body or "")
    return int(m.group(1)) if m else 1


def bump_iteration(pr_body: str, new_iter: int) -> str:
    body = pr_body or ""
    if re.search(r"AI-ITERATION:\s*\d+", body):
        return re.sub(r"AI-ITERATION:\s*\d+", f"AI-ITERATION: {new_iter}", body)
    return body.strip() + f"\n\nAI-ITERATION: {new_iter}\n"


def extract_latest_ai_review(pr) -> str:
    comments = list(pr.get_issue_comments())
    for c in reversed(comments):
        txt = (c.body or "").strip()
        if txt.startswith("AI-REVIEW:"):
            return txt
    return ""


def checkout_default_branch(base_branch: str) -> None:
    sh(["git", "fetch", "origin", base_branch])
    sh(["git", "checkout", base_branch])
    sh(["git", "reset", "--hard", f"origin/{base_branch}"])


def checkout_remote_branch(branch: str) -> None:
    sh(["git", "fetch", "origin", branch])
    sh(["git", "checkout", "-B", branch, f"origin/{branch}"])


def write_ai_issue_file(issue_number: int, title: str, body: str) -> str:
    os.makedirs(AI_DIR, exist_ok=True)
    out_path = os.path.join(AI_DIR, f"issue-{issue_number}.md")
    now = datetime.utcnow().isoformat() + "Z"
    content = (
        f"# Issue {issue_number}\n\n"
        f"## Title\n{title}\n\n"
        f"## Body\n{body}\n\n"
        f"## Generated\n{now}\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def apply_iteration_fix(
    issue_number: Optional[int], iteration: int, ai_review: str
) -> str:
    """
    Deterministic "fix" for demo:
    - ensure .ai/issue-<n>.md exists (or .ai/issue-unknown.md)
    - append an iteration note and whether AI-REVIEW was detected
    """
    os.makedirs(AI_DIR, exist_ok=True)
    if issue_number:
        out_path = os.path.join(AI_DIR, f"issue-{issue_number}.md")
    else:
        out_path = os.path.join(AI_DIR, "issue-unknown.md")

    # ensure file exists
    if not os.path.exists(out_path):
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("# Auto-generated placeholder\n")

    with open(out_path, "a", encoding="utf-8") as f:
        f.write("\n\n## Auto-fix iteration\n")
        f.write(f"- iteration: {iteration}\n")
        f.write(f"- ai_review_detected: {'yes' if ai_review else 'no'}\n")

    return out_path


def handle_issue_mode(gh_repo, issue_number: int) -> None:
    issue = gh_repo.get_issue(number=issue_number)
    title = issue.title or f"Issue {issue_number}"
    body = issue.body or ""

    repo_full = get_repo_full_name()
    owner = repo_full.split("/")[0]
    base_branch = gh_repo.default_branch
    branch = f"issue-{issue_number}-{safe_branch_name(title)}"

    ensure_git_identity()
    checkout_default_branch(base_branch)

    # create local branch from default branch
    sh(["git", "checkout", "-B", branch])

    # deterministic scaffold change
    created_path = write_ai_issue_file(issue_number, title, body)

    # commit if there are changes
    status = sh(["git", "status", "--porcelain"])
    if status:
        commit_change(f"Implement Issue #{issue_number}: scaffold change")
        push_branch(branch)
    else:
        # ensure branch exists remotely
        push_branch(branch)

    head = f"{owner}:{branch}"
    existing = find_existing_pr(gh_repo, head=head)

    pr_title = f"Implement #{issue_number}: {title}"
    pr_body = (
        f"Closes #{issue_number}\n\n"
        "AI-ITERATION: 1\n\n"
        f"Auto-generated initial scaffold. Created `{created_path}`.\n"
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

    print(f"OK: PR #{pr.number} for Issue #{issue_number}")


def handle_pr_iteration_mode(gh_repo, pr_number: int) -> None:
    pr = gh_repo.get_pull(pr_number)

    current_iter = parse_iteration(pr.body or "")
    if current_iter >= MAX_ITERATIONS:
        pr.create_issue_comment(
            f"Code Agent: reached iteration limit ({MAX_ITERATIONS}). Stopping."
        )
        print("STOP: iteration limit reached")
        return

    next_iter = current_iter + 1
    issue_number = extract_issue_number_from_pr(pr.body or "")
    ai_review = extract_latest_ai_review(pr)

    ensure_git_identity()

    # checkout PR branch and apply fix
    branch = pr.head.ref
    checkout_remote_branch(branch)

    touched = apply_iteration_fix(
        issue_number=issue_number, iteration=next_iter, ai_review=ai_review
    )

    status = sh(["git", "status", "--porcelain"])
    if status:
        commit_change(f"Fix based on AI review (iteration {next_iter})")
        push_branch(branch)

    # bump iteration in PR body
    pr.edit(body=bump_iteration(pr.body or "", next_iter))
    pr.create_issue_comment(
        f"Code Agent: applied fixes for iteration {next_iter} and pushed updates. "
        f"Touched `{touched}`."
    )

    print(f"OK: updated PR #{pr_number} iteration {next_iter}")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--issue", type=int)
    group.add_argument("--pr", type=int)
    args = parser.parse_args()

    gh = gh_client()
    gh_repo = gh.get_repo(get_repo_full_name())

    if args.issue is not None:
        handle_issue_mode(gh_repo, args.issue)
        return

    if args.pr is not None:
        handle_pr_iteration_mode(gh_repo, args.pr)
        return


if __name__ == "__main__":
    main()
