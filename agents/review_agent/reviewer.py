import argparse
import os
import re
from dataclasses import dataclass
from typing import Optional, Set

from github import Github

from agents.llm_client import llm_chat

APPROVED_LABEL = "ai:approved"
NEEDS_FIX_LABEL = "ai:needs-fix"

# Extract file paths mentioned in Issue text (universal, not task-specific)
FILE_RE = re.compile(r"(?:(?:^|[\s`]))((?:src|tests|agents)/[A-Za-z0-9_\-./]+\.py)")


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


# -------------------- Deterministic gates --------------------


def pr_changed_files(pr) -> Set[str]:
    return {f.filename for f in pr.get_files()}


def pr_has_substantive_changes(pr) -> bool:
    """
    True if PR has any meaningful change outside .ai/:
    - non-empty patch
    - or additions/deletions > 0
    """
    for f in pr.get_files():
        if f.filename.startswith(".ai/"):
            continue
        if (f.additions or 0) + (f.deletions or 0) > 0:
            return True
        if f.patch and f.patch.strip():
            return True
    return False


def extract_paths_from_issue(text: str) -> Set[str]:
    return {m.group(1) for m in FILE_RE.finditer(text or "")}


def summarize_requirements(issue_text: str) -> str:
    """
    Provide a tiny deterministic summary for the LLM:
    - explicit file paths mentioned in the Issue (if any)
    """
    paths = sorted(extract_paths_from_issue(issue_text))
    if not paths:
        return "No explicit file paths mentioned in Issue."
    lines = ["Explicit file paths mentioned in Issue:"]
    for p in paths[:30]:
        lines.append(f"- {p}")
    if len(paths) > 30:
        lines.append(f"...and {len(paths) - 30} more.")
    return "\n".join(lines)


def ci_state_for_pr(repo, pr) -> Optional[str]:
    """
    Best-effort CI state using combined status on PR head SHA.
    Returns: 'success' | 'failure' | 'error' | 'pending' | None
    """
    try:
        sha = pr.head.sha
        combined = repo.get_commit(sha=sha).get_combined_status()
        return combined.state
    except Exception:
        return None


# -------------------- Evaluation --------------------


def evaluate(repo, pr) -> ReviewResult:
    issues: list[str] = []
    suggestions: list[str] = []

    issue_no = extract_issue_number(pr.body or "")
    issue_text = ""

    # Gate 0: PR must reference an Issue
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

    # Gate 1: CI must be green (never approve failing/pending)
    ci_state = ci_state_for_pr(repo, pr)
    if ci_state in ("failure", "error"):
        issues.append(f"CI is failing on PR head ({ci_state}).")
        suggestions.append("Fix CI failures and push updates.")
    elif ci_state == "pending":
        issues.append("CI is still running (pending).")
        suggestions.append("Wait for CI to finish before approval.")

    # Gate 2: PR must have substantive changes (outside .ai/)
    if not pr_has_substantive_changes(pr):
        issues.append("PR does not contain substantive code changes (outside .ai/).")
        suggestions.append(
            "Implement the required functionality; avoid scaffold-only changes."
        )

    # Gate 3: If Issue explicitly mentions files, PR must modify them
    if issue_text:
        required_paths = extract_paths_from_issue(issue_text)
        if required_paths:
            changed = pr_changed_files(pr)
            missing = sorted(p for p in required_paths if p not in changed)
            if missing:
                issues.append(
                    "PR does not modify files explicitly required by the Issue: "
                    + ", ".join(missing)
                )
                suggestions.append(
                    "Update the PR to include changes in the required files."
                )

    status = "approved" if not issues else "needs-fix"
    return ReviewResult(
        status=status,
        issues=issues,
        suggestions=suggestions,
        issue_number=issue_no,
    )


# -------------------- Output helpers --------------------


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

    lines = [
        "# AI Reviewer summary",
        "",
        f"**Status:** `{res.status}`",
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
    current = {lbl.name for lbl in pr.get_labels()}

    if res.status == "approved":
        if NEEDS_FIX_LABEL in current:
            pr.remove_from_labels(NEEDS_FIX_LABEL)
        pr.add_to_labels(APPROVED_LABEL)
        return

    # needs-fix: remove approved and "touch" needs-fix to trigger labeled event every time
    if APPROVED_LABEL in current:
        pr.remove_from_labels(APPROVED_LABEL)
    if NEEDS_FIX_LABEL in current:
        pr.remove_from_labels(NEEDS_FIX_LABEL)
    pr.add_to_labels(NEEDS_FIX_LABEL)


def collect_pr_diff(pr, max_chars: int = 6000) -> str:
    """
    Collect PR diff (best-effort). Keep small to reduce LLM cost/errors.
    """
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


# -------------------- Main --------------------


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

    # LLM advisory layer (cannot override deterministic failures)
    diff_text = collect_pr_diff(pr, max_chars=6000)

    issue_text = ""
    if res.issue_number:
        try:
            issue = repo.get_issue(number=res.issue_number)
            issue_text = clamp(issue.body or "", 1500)
        except Exception:
            issue_text = ""

    req_summary = summarize_requirements(issue_text)

    prompt = f"""
You are an AI code reviewer. Verify that the PR implementation matches the Issue requirements.

Definition of DONE:
- The PR diff implements the requested changes from the Issue.
- If the Issue asks to create/modify specific files or functions, those changes MUST be present in the diff.
- If implementation is missing, incomplete, unrelated, or not confirmable from the diff => status MUST be needs-fix.
- Be strict. No guessing.

You will be given:
- Issue (source of truth for requirements)
- PR diff (source of truth for implementation)

Requirements summary:
{req_summary}

Issue:
{issue_text}

PR diff:
{diff_text}

Return a strict review in EXACTLY this format (no extra text):

status=approved|needs-fix
issues:
- <bullet 1>
- <bullet 2>
suggestions:
- <bullet 1>
- <bullet 2>

Rules:
- If changes do NOT match the Issue, status=needs-fix.
- If the diff is mostly empty, scaffolding-only, or only touches metadata, status=needs-fix.
- If tests are required by the Issue but not present in the diff, status=needs-fix.
- If you are uncertain, status=needs-fix.
- Keep it short (max ~8 bullets total).
""".strip()

    llm_out, llm_mode = llm_chat(prompt)
    llm_out = (llm_out or "").strip()
    res.suggestions.append(f"LLM mode: {llm_mode}")

    # LLM may only DOWNGRADE approval, never upgrade
    if llm_out and "status=needs-fix" in llm_out and res.status == "approved":
        res.status = "needs-fix"
        res.issues.append("LLM review: potential mismatch with requirements.")
        res.suggestions.append("See LLM output in comment.")

    if llm_out:
        res.suggestions.append("LLM output:")
        res.suggestions.append(clamp(llm_out, 2500))
    else:
        res.suggestions.append("LLM produced no output.")

    body = format_ai_review(res, pr_number=args.pr)

    write_job_summary(res)
    pr.create_issue_comment(body)
    pr.create_review(body=body, event="COMMENT")

    apply_labels(pr, res)

    print(f"OK: Reviewed PR #{args.pr} -> {res.status}")


if __name__ == "__main__":
    main()
