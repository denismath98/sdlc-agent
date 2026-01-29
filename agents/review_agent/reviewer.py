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
            name=name,
            color=color,
            description="Auto label by AI reviewer",
        )


def extract_issue_number(pr_body: str) -> Optional[int]:
    m = re.search(r"Closes\s+#(\d+)", pr_body or "", flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def has_ai_issue_file(repo, pr) -> bool:
    # We expect a file like ".ai/issue-<n>.md"
    issue_no = extract_issue_number(pr.body or "")
    if not issue_no:
        return False
    expected = f".ai/issue-{issue_no}.md"
    try:
        pr.get_files()  # ensure permissions are fine
        for f in pr.get_files():
            if f.filename == expected:
                return True
    except Exception:
        return False
    return False


def evaluate(repo, pr) -> ReviewResult:
    issue_no = extract_issue_number(pr.body or "")
    issues: list[str] = []
    suggestions: list[str] = []

    if not issue_no:
        issues.append("PR body must contain `Closes #<issue>` to link requirements.")
        suggestions.append("Add `Closes #<issue_number>` to PR description.")
    else:
        # basic check: issue exists
        try:
            repo.get_issue(number=issue_no)
        except Exception:
            issues.append(f"Issue #{issue_no} not found or not accessible.")
            suggestions.append("Ensure PR references an existing Issue number.")

    if not has_ai_issue_file(repo, pr):
        issues.append(
            "Missing expected file `.ai/issue-<issue>.md` generated from Issue."
        )
        suggestions.append(
            "Ensure Code Agent creates `.ai/issue-<issue>.md` in the PR branch."
        )

    status = "approved" if not issues else "needs-fix"
    return ReviewResult(
        status=status, issues=issues, suggestions=suggestions, issue_number=issue_no
    )


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
        "issues:\n"
        f"{issues_block}\n"
        "suggestions:\n"
        f"{sugg_block}\n"
    )


def write_job_summary(res: ReviewResult) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return

    lines = []
    lines.append("# AI Reviewer summary")
    lines.append("")
    lines.append(f"**Status:** `{res.status}`")
    lines.append("")
    lines.append("## Issues")
    if res.issues:
        for x in res.issues:
            lines.append(f"- {x}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Suggestions")
    if res.suggestions:
        for x in res.suggestions:
            lines.append(f"- {x}")
    else:
        lines.append("- None")
    lines.append("")

    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def apply_labels(pr, res: ReviewResult) -> None:
    current = [lbl.name for lbl in pr.get_labels()]

    if res.status == "approved":
        if NEEDS_FIX_LABEL in current:
            pr.remove_from_labels(NEEDS_FIX_LABEL)
        pr.add_to_labels(APPROVED_LABEL)
    else:
        if APPROVED_LABEL in current:
            pr.remove_from_labels(APPROVED_LABEL)
        pr.add_to_labels(NEEDS_FIX_LABEL)


def collect_pr_diff(pr, max_chars: int = 20000) -> str:
    parts: list[str] = []
    for f in pr.get_files():
        parts.append(f"FILE: {f.filename}")
        if f.patch:
            parts.append(f.patch)
        parts.append("")  # spacer
    text = "\n".join(parts)
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[TRUNCATED]..."
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, required=True)
    args = parser.parse_args()

    gh = Github(get_token())
    repo = gh.get_repo(get_repo_full_name())
    pr = repo.get_pull(args.pr)

    ensure_label(repo, APPROVED_LABEL, "2da44e")  # green
    ensure_label(repo, NEEDS_FIX_LABEL, "d1242f")  # red

    res = evaluate(repo, pr)

    diff_text = collect_pr_diff(pr)
    issue_text = ""
    if res.issue_number:
        issue = repo.get_issue(number=res.issue_number)
        issue_text = (issue.body or "")[:5000]

    prompt = f"""
    Issue:
    {issue_text}

    PR diff:
    {diff_text}

    Task:
    Return a strict review in the following format:

    status=approved|needs-fix
    issues:
    - ...
    suggestions:
    - ...

    Rules:
    - If changes do not match the Issue, status=needs-fix.
    - If CI passed but logic seems wrong or missing, status=needs-fix.
    - Keep it short.
    """

    try:
        llm_out = llm_chat(prompt).strip()
        # примитивный парсинг: если LLM сказал needs-fix — учитываем
        if "status=needs-fix" in llm_out and res.status == "approved":
            res.status = "needs-fix"
            res.issues.append("LLM review: potential mismatch with requirements.")
            res.suggestions.append("See LLM output in comment.")
        # добавим LLM вывод в suggestions как артефакт
        res.suggestions.append("LLM output:")
        res.suggestions.append(llm_out)
    except Exception as e:
        # не ломаем pipeline, если LLM не настроен
        res.suggestions.append(f"LLM not used: {e}")

    body = format_ai_review(res, pr_number=args.pr)

    # publish summary (Actions UI)
    write_job_summary(res)

    # publish in PR
    pr.create_issue_comment(body)
    pr.create_review(body=body, event="COMMENT")

    apply_labels(pr, res)

    print(f"OK: Reviewed PR #{args.pr} -> {res.status}")


if __name__ == "__main__":
    main()
