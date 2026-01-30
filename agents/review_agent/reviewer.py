import argparse
import os
import re
from dataclasses import dataclass
from typing import Optional

from github import Github

from agents.llm_client import llm_chat

APPROVED_LABEL = "ai:approved"
NEEDS_FIX_LABEL = "ai:needs-fix"


@dataclass
class ReviewResult:
    status: str  # "approved" | "needs-fix"
    issues: list[str]
    suggestions: list[str]
    issue_number: Optional[int]
    ci_state: Optional[str]


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
    m = re.search(r"Closes\s+#(\d+)", pr_body or "", flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def ci_state_for_pr(repo, pr) -> Optional[str]:
    """
    Best-effort CI state using combined status on PR head SHA.
    Returns: 'success' | 'failure' | 'error' | 'pending' | None
    """
    try:
        combined = repo.get_commit(pr.head.sha).get_combined_status()
        return combined.state
    except Exception:
        return None


def pr_has_substantive_changes(pr) -> bool:
    """
    Universal guardrail: a PR that only touches .ai/ (or has no real changes)
    should not be approved.
    """
    for f in pr.get_files():
        if f.filename.startswith(".ai/"):
            continue
        if (f.additions or 0) + (f.deletions or 0) > 0:
            return True
        if f.patch and f.patch.strip():
            return True
    return False


def collect_pr_diff(pr, max_chars: int = 6000) -> str:
    parts: list[str] = []
    for f in pr.get_files():
        parts.append(f"FILE: {f.filename} (+{f.additions}/-{f.deletions})")
        if f.patch:
            parts.append(f.patch)
        else:
            parts.append("[no patch available]")
        parts.append("")
    text = "\n".join(parts)
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[TRUNCATED]..."
    return text


def clamp(text: str, max_len: int) -> str:
    t = (text or "").strip()
    return t if len(t) <= max_len else (t[:max_len] + "\n...[TRUNCATED]...")


def parse_llm_status(llm_out: str) -> Optional[str]:
    t = (llm_out or "").lower()
    if "status=needs-fix" in t:
        return "needs-fix"
    if "status=approved" in t:
        return "approved"
    return None


def format_ai_review(res: ReviewResult, pr_number: int) -> str:
    issues_block = "\n".join([f"- {x}" for x in res.issues]) if res.issues else "- None"
    sugg_block = (
        "\n".join([f"- {x}" for x in res.suggestions]) if res.suggestions else "- None"
    )

    return (
        "AI-REVIEW:\n"
        f"status={res.status}\n"
        f"pr={pr_number}\n"
        f"issue={res.issue_number if res.issue_number else 'N/A'}\n"
        f"ci={res.ci_state if res.ci_state else 'unknown'}\n"
        "issues:\n"
        f"{issues_block}\n"
        "suggestions:\n"
        f"{sugg_block}\n"
    )


def write_job_summary(res: ReviewResult) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return

    lines = [
        "# AI Reviewer summary",
        "",
        f"**Status:** `{res.status}`",
        f"**CI:** `{res.ci_state if res.ci_state else 'unknown'}`",
        "",
        "## Issues",
    ]
    if res.issues:
        lines.extend([f"- {x}" for x in res.issues])
    else:
        lines.append("- None")

    lines.extend(["", "## Suggestions"])
    if res.suggestions:
        lines.extend([f"- {x}" for x in res.suggestions])
    else:
        lines.append("- None")

    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def apply_labels(pr, res: ReviewResult) -> None:
    """
    If needs-fix: touch the label (remove & add) to reliably trigger pull_request:labeled.
    If approved: set ai:approved and remove ai:needs-fix.
    """
    current = {lbl.name for lbl in pr.get_labels()}

    if res.status == "approved":
        if NEEDS_FIX_LABEL in current:
            pr.remove_from_labels(NEEDS_FIX_LABEL)
        pr.add_to_labels(APPROVED_LABEL)
        return

    # needs-fix
    if APPROVED_LABEL in current:
        pr.remove_from_labels(APPROVED_LABEL)
    if NEEDS_FIX_LABEL in current:
        pr.remove_from_labels(NEEDS_FIX_LABEL)
    pr.add_to_labels(NEEDS_FIX_LABEL)


def evaluate(repo, pr) -> ReviewResult:
    issues: list[str] = []
    suggestions: list[str] = []

    issue_no = extract_issue_number(pr.body or "")
    issue_text = ""

    if not issue_no:
        issues.append("PR body must contain `Closes #<issue>` to link requirements.")
        suggestions.append("Add `Closes #<issue_number>` to PR description.")
    else:
        try:
            issue = repo.get_issue(number=issue_no)
            issue_text = issue.body or ""
        except Exception:
            issues.append(f"Issue #{issue_no} not found or not accessible.")
            suggestions.append("Ensure PR references an existing Issue.")

    ci_state = ci_state_for_pr(repo, pr)

    # Critical gate: failing CI => needs-fix
    if ci_state in ("failure", "error"):
        issues.append(f"CI is failing ({ci_state}).")
        suggestions.append("Fix CI failures and push updates.")

    # Universal critical-ish gate: totally empty / scaffold-only PR => needs-fix
    if not pr_has_substantive_changes(pr):
        issues.append("PR has no substantive changes outside .ai/ (scaffold-only).")
        suggestions.append("Implement the requested functionality in code changes.")

    # If CI pending, we do NOT fail the PR; we only advise.
    if ci_state == "pending":
        suggestions.append("CI is still running (pending). Wait for CI to finish.")

    status = "approved" if not issues else "needs-fix"
    return ReviewResult(
        status=status,
        issues=issues,
        suggestions=suggestions,
        issue_number=issue_no,
        ci_state=ci_state,
    )


def main() -> None:
    import argparse
    import os
    import re
    from dataclasses import dataclass
    from typing import Optional

    from github import Github

    from agents.llm_client import llm_chat

    APPROVED_LABEL = "ai:approved"
    NEEDS_FIX_LABEL = "ai:needs-fix"

    @dataclass
    class ReviewResult:
        status: str  # "approved" | "needs-fix"
        issues: list[str]
        suggestions: list[str]
        issue_number: Optional[int]
        ci_state: Optional[str]

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
        m = re.search(r"Closes\s+#(\d+)", pr_body or "", flags=re.IGNORECASE)
        return int(m.group(1)) if m else None

    def ci_state_for_pr(repo, pr) -> Optional[str]:
        try:
            combined = repo.get_commit(pr.head.sha).get_combined_status()
            return combined.state
        except Exception:
            return None

    def pr_has_substantive_changes(pr) -> bool:
        """
        Universal guardrail: PR must change something outside .ai/
        (otherwise it's scaffold-only and should be needs-fix).
        """
        for f in pr.get_files():
            if f.filename.startswith(".ai/"):
                continue
            if (f.additions or 0) + (f.deletions or 0) > 0:
                return True
            if f.patch and f.patch.strip():
                return True
        return False

    def collect_pr_diff(pr, max_chars: int = 8000) -> str:
        parts: list[str] = []
        for f in pr.get_files():
            parts.append(f"FILE: {f.filename} (+{f.additions}/-{f.deletions})")
            parts.append(f.patch if f.patch else "[no patch available]")
            parts.append("")
        text = "\n".join(parts)
        return (
            text
            if len(text) <= max_chars
            else (text[:max_chars] + "\n...[TRUNCATED]...")
        )

    def clamp(text: str, max_len: int) -> str:
        t = (text or "").strip()
        return t if len(t) <= max_len else (t[:max_len] + "\n...[TRUNCATED]...")

    def parse_llm_status(llm_out: str) -> Optional[str]:
        t = (llm_out or "").lower()
        if "status=needs-fix" in t:
            return "needs-fix"
        if "status=approved" in t:
            return "approved"
        return None

    def format_ai_review(res: ReviewResult, pr_number: int) -> str:
        issues_block = (
            "\n".join([f"- {x}" for x in res.issues]) if res.issues else "- None"
        )
        sugg_block = (
            "\n".join([f"- {x}" for x in res.suggestions])
            if res.suggestions
            else "- None"
        )
        return (
            "AI-REVIEW:\n"
            f"status={res.status}\n"
            f"pr={pr_number}\n"
            f"issue={res.issue_number if res.issue_number else 'N/A'}\n"
            f"ci={res.ci_state if res.ci_state else 'unknown'}\n"
            "issues:\n"
            f"{issues_block}\n"
            "suggestions:\n"
            f"{sugg_block}\n"
        )

    def write_job_summary(res: ReviewResult) -> None:
        path = os.environ.get("GITHUB_STEP_SUMMARY")
        if not path:
            return
        lines = [
            "# AI Reviewer summary",
            "",
            f"**Status:** `{res.status}`",
            f"**CI:** `{res.ci_state if res.ci_state else 'unknown'}`",
            "",
            "## Issues",
        ]
        lines += [f"- {x}" for x in res.issues] if res.issues else ["- None"]
        lines += ["", "## Suggestions"]
        lines += [f"- {x}" for x in res.suggestions] if res.suggestions else ["- None"]
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def apply_labels(pr, status: str) -> None:
        """
        IMPORTANT: "touch" needs-fix label so pull_request:labeled triggers every time.
        """
        current = {lbl.name for lbl in pr.get_labels()}

        if status == "approved":
            if NEEDS_FIX_LABEL in current:
                pr.remove_from_labels(NEEDS_FIX_LABEL)
            pr.add_to_labels(APPROVED_LABEL)
            return

        # needs-fix
        if APPROVED_LABEL in current:
            pr.remove_from_labels(APPROVED_LABEL)
        if NEEDS_FIX_LABEL in current:
            pr.remove_from_labels(NEEDS_FIX_LABEL)
        pr.add_to_labels(NEEDS_FIX_LABEL)

    def main() -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--pr", type=int, required=True)
        args = parser.parse_args()

        gh = Github(get_token())
        repo = gh.get_repo(get_repo_full_name())
        pr = repo.get_pull(args.pr)

        ensure_label(repo, APPROVED_LABEL, "2da44e")
        ensure_label(repo, NEEDS_FIX_LABEL, "d1242f")

        issue_no = extract_issue_number(pr.body or "")
        issue_text = ""
        if issue_no:
            try:
                issue = repo.get_issue(number=issue_no)
                issue_text = clamp(issue.body or "", 2000)
            except Exception:
                issue_text = ""

        ci_state = ci_state_for_pr(repo, pr)

        issues: list[str] = []
        suggestions: list[str] = []

        # Critical: failing CI is always needs-fix
        if ci_state in ("failure", "error"):
            issues.append(f"CI is failing ({ci_state}).")
            suggestions.append("Fix CI failures and push updates.")

        # Critical: scaffold-only PR is needs-fix (independent of CI state)
        if not pr_has_substantive_changes(pr):
            issues.append("PR has no substantive changes outside .ai/ (scaffold-only).")
            suggestions.append("Implement the requested functionality in code changes.")

        # Pending is not an error, but we mention it
        if ci_state == "pending":
            suggestions.append("CI is still running (pending). Wait for CI to finish.")

        status = "approved" if not issues else "needs-fix"

        # LLM semantic review: only used to DOWNGRADE or to confirm when deterministic is clean.
        diff_text = collect_pr_diff(pr, max_chars=8000)
        prompt = f"""
    You are a strict code reviewer.

    Definition of DONE:
    - The PR is DONE only if the PR diff clearly implements the Issue requirements.
    - If you cannot confirm implementation from the diff, you MUST return needs-fix.
    - Be strict. No guessing.

    Issue:
    {issue_text}

    PR diff:
    {diff_text}

    Return EXACTLY:

    status=approved|needs-fix
    issues:
    - ...
    suggestions:
    - ...
    """.strip()

        llm_out, llm_mode = llm_chat(prompt)
        llm_out = (llm_out or "").strip()
        llm_status = parse_llm_status(llm_out)

        suggestions.append(f"LLM mode: {llm_mode}")
        if llm_out:
            suggestions.append("LLM output:")
            suggestions.append(clamp(llm_out, 2500))

        # If deterministic found issues => keep needs-fix.
        # If deterministic clean => use LLM decision if parsable.
        if not issues and llm_status in ("approved", "needs-fix"):
            status = llm_status
            if status == "needs-fix":
                issues.append("LLM review: requirements likely not met.")

        res = ReviewResult(
            status=status,
            issues=issues,
            suggestions=suggestions,
            issue_number=issue_no,
            ci_state=ci_state,
        )

        body = format_ai_review(res, pr_number=args.pr)
        write_job_summary(res)
        pr.create_issue_comment(body)
        pr.create_review(body=body, event="COMMENT")

        apply_labels(pr, res.status)

        print(f"OK: Reviewed PR #{args.pr} -> {res.status}")

    if __name__ == "__main__":
        main()


if __name__ == "__main__":
    main()
