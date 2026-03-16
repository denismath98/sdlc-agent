import argparse
import os
import re
from typing import Optional

from core.models import ReviewResult
from prompts.registry import get_prompt
from services.github_service import (
    apply_labels,
    ci_state_for_pr,
    create_issue_comment,
    ensure_ai_labels,
    get_repo,
)
from services.llm_service import llm_chat
from services.sdlc_config_service import load_sdlc_config


def build_reviewer_prompt(issue_text: str, diff_text: str) -> str:
    template = get_prompt("reviewer.semantic")
    return template.format(
        issue=issue_text,
        diff=diff_text,
    )


def extract_issue_number(pr_body: str) -> Optional[int]:
    m = re.search(r"Closes\s+#(\d+)", pr_body or "", flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def pr_has_substantive_changes(pr) -> bool:
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
        text if len(text) <= max_chars else (text[:max_chars] + "\n...[TRUNCATED]...")
    )


def clamp(text: str, max_len: int) -> str:
    t = (text or "").strip()
    return t if len(t) <= max_len else (t[:max_len] + "\n...[TRUNCATED]...")


def read_log_tail(path: str, max_chars: int = 2500) -> str:
    p = (path or "").strip()
    if not p:
        return ""
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read().strip()
        if len(data) > max_chars:
            return data[-max_chars:]
        return data
    except Exception:
        return ""


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


def ci_state_from_workflow_env() -> Optional[str]:
    conclusion = (os.getenv("CI_WORKFLOW_CONCLUSION") or "").strip().lower()

    if not conclusion:
        return None

    if conclusion == "success":
        return "success"

    if conclusion in (
        "failure",
        "timed_out",
        "cancelled",
        "startup_failure",
        "action_required",
    ):
        return "failure"

    if conclusion in ("neutral", "skipped"):
        return "error"

    return None


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


def evaluate(repo, pr) -> ReviewResult:
    config = load_sdlc_config()

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

    ci_workflow_name = (os.getenv("CI_WORKFLOW_NAME") or "").strip()
    ci_workflow_conclusion = (os.getenv("CI_WORKFLOW_CONCLUSION") or "").strip().lower()
    ci_finished_via_workflow = bool(ci_workflow_conclusion)

    if ci_workflow_name:
        suggestions.append(f"CI workflow source: {ci_workflow_name}")

    pytest_exit = (os.getenv("PYTEST_EXIT_CODE") or "").strip()
    black_exit = (os.getenv("BLACK_EXIT_CODE") or "").strip()
    pytest_log_path = (os.getenv("PYTEST_LOG_PATH") or "").strip()
    black_log_path = (os.getenv("BLACK_LOG_PATH") or "").strip()

    if pytest_exit and pytest_exit != "0":
        issues.append("Pytest failed (tests are red).")
        suggestions.append("Fix failing tests and push updates.")
        tail = read_log_tail(pytest_log_path, max_chars=2500)
        if tail:
            suggestions.append("Pytest log tail:")
            suggestions.append(tail)

    if black_exit and black_exit != "0":
        issues.append("Black check failed (formatting).")
        suggestions.append("Run black and commit formatted changes.")
        tail = read_log_tail(black_log_path, max_chars=1500)
        if tail:
            suggestions.append("Black log tail:")
            suggestions.append(tail)

    if not pytest_exit and not black_exit and config.review.require_ci_success:
        if ci_state in ("failure", "error"):
            issues.append(f"CI is failing ({ci_state}).")
            suggestions.append("Fix CI failures and push updates.")

        elif ci_state == "pending" and not ci_finished_via_workflow:
            issues.append(
                "CI is still running (pending). Final approval is not allowed yet."
            )
            suggestions.append("Wait for CI to finish before approving the PR.")

        elif ci_state is None and not ci_finished_via_workflow:
            issues.append("CI status is unknown. Final approval is not allowed yet.")
            suggestions.append(
                "Ensure CI has started and finished successfully before approval."
            )

    if not pr_has_substantive_changes(pr):
        issues.append("PR has no substantive changes outside .ai/ (scaffold-only).")
        suggestions.append("Implement the requested functionality in code changes.")

    status = "approved" if not issues else "needs-fix"

    diff_text = collect_pr_diff(pr, max_chars=config.review.diff_max_chars)
    issue_text = clamp(issue_text, config.review.issue_max_chars)

    prompt = build_reviewer_prompt(issue_text=issue_text, diff_text=diff_text)

    llm_out, llm_mode = llm_chat(prompt)
    llm_out = (llm_out or "").strip()
    llm_status = parse_llm_status(llm_out)

    suggestions.append(f"LLM mode: {llm_mode}")
    if llm_out:
        suggestions.append("LLM output:")
        suggestions.append(clamp(llm_out, config.review.llm_output_max_chars))
    else:
        suggestions.append("LLM produced no output.")

    if status == "approved" and llm_status == "needs-fix":
        status = "needs-fix"
        issues.append("LLM review: requirements likely not met.")

    return ReviewResult(
        status=status,
        issues=issues,
        suggestions=suggestions,
        issue_number=issue_no,
        ci_state=ci_state,
    )


def review_pull_request(pr_number: int) -> ReviewResult:
    """
    Safe review mode: only compute review result, no GitHub side effects.
    """
    repo = get_repo()
    pr = repo.get_pull(pr_number)

    ensure_ai_labels(repo)
    return evaluate(repo, pr)


def apply_review_result(pr_number: int, res: ReviewResult) -> None:
    """
    Apply review result to GitHub: comment, summary, labels.
    """
    repo = get_repo()
    pr = repo.get_pull(pr_number)

    body = format_ai_review(res, pr_number=pr_number)
    write_job_summary(res)
    create_issue_comment(pr, body)
    apply_labels(pr, res.status)


def review_and_apply_pull_request(pr_number: int) -> ReviewResult:
    """
    Full review mode with GitHub side effects.
    """
    res = review_pull_request(pr_number)
    apply_review_result(pr_number, res)
    return res


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, required=True)
    args = parser.parse_args()

    try:
        res = review_and_apply_pull_request(args.pr)
        print(f"OK: Reviewed PR #{args.pr} -> {res.status}")
    except Exception as e:
        repo = get_repo()
        pr = repo.get_pull(args.pr)

        body = (
            "AI-REVIEW:\n"
            "status=needs-fix\n"
            f"pr={args.pr}\n"
            "issue=N/A\n"
            "ci=unknown\n"
            "issues:\n"
            f"- Reviewer crashed: {e}\n"
            "suggestions:\n"
            "- Check reviewer workflow logs.\n"
        )
        try:
            create_issue_comment(pr, body)
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
