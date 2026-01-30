import argparse
import os
import re
import subprocess
from datetime import datetime
from typing import Dict, Tuple

from github import Auth, Github
from agents.llm_client import llm_chat

AI_DIR = ".ai"
MAX_ITERATIONS = 3


# -------------------- utils --------------------


def sh(cmd: list[str]) -> str:
    res = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return res.stdout.strip()


def ensure_git_identity() -> None:
    sh(["git", "config", "user.name", "code-agent[bot]"])
    sh(["git", "config", "user.email", "code-agent[bot]@users.noreply.github.com"])


def maybe_format_with_black() -> str:
    try:
        subprocess.run(
            ["python", "-m", "black", "."],
            check=True,
            text=True,
            capture_output=True,
        )
        return "black: formatted"
    except Exception as e:
        return f"black: skipped ({e})"


def commit_if_needed(message: str) -> bool:
    sh(["git", "add", "-A"])
    status = sh(["git", "status", "--porcelain"])
    if not status.strip():
        return False
    sh(["git", "commit", "-m", message])
    return True


def get_repo_full_name() -> str:
    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("GITHUB_REPOSITORY missing")
    return repo


def gh_client() -> Github:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN missing")
    return Github(auth=Auth.Token(token))


# -------------------- LLM CODE GENERATION --------------------

CODE_PROMPT = """
You are a senior software engineer.

Task:
Implement the GitHub Issue described below by writing real code.

Rules:
- Write real Python code.
- Create files if they do not exist.
- Modify files if they already exist.
- Do NOT write diffs.
- Do NOT explain anything.
- Do NOT add markdown.

Output format (STRICT):
For each file, output:

FILE: path/to/file.py
<full file content>

You may output multiple FILE blocks.

Issue title:
{title}

Issue body:
{body}
""".strip()


def parse_files_from_llm(text: str) -> Dict[str, str]:
    """
    Parses:
    FILE: path
    <content>
    """
    files: Dict[str, str] = {}
    current_path = None
    buffer = []

    for line in text.splitlines():
        if line.startswith("FILE: "):
            if current_path:
                files[current_path] = "\n".join(buffer).rstrip() + "\n"
            current_path = line.replace("FILE: ", "").strip()
            buffer = []
        else:
            buffer.append(line)

    if current_path:
        files[current_path] = "\n".join(buffer).rstrip() + "\n"

    return files


def write_files(files: Dict[str, str]) -> None:
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


# -------------------- main flows --------------------


def handle_issue_mode(repo, issue_number: int) -> None:
    issue = repo.get_issue(number=issue_number)
    title = issue.title or ""
    body = issue.body or ""

    ensure_git_identity()

    branch = f"issue-{issue_number}"
    sh(["git", "checkout", "-B", branch, repo.default_branch])

    os.makedirs(AI_DIR, exist_ok=True)
    with open(f"{AI_DIR}/issue-{issue_number}.md", "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{body}\n\nGenerated: {datetime.utcnow()}")

    prompt = CODE_PROMPT.format(title=title, body=body)
    raw, mode = llm_chat(prompt)

    files = parse_files_from_llm(raw)

    if not files:
        issue.create_comment(f"Code Agent: LLM returned no files (mode={mode}).")
        return

    write_files(files)
    fmt = maybe_format_with_black()

    committed = commit_if_needed(f"Implement issue #{issue_number}")
    sh(["git", "push", "-u", "origin", branch])

    pr = repo.create_pull(
        title=f"Implement #{issue_number}: {title}",
        body=f"Closes #{issue_number}\n\nAI-ITERATION: 1",
        head=branch,
        base=repo.default_branch,
    )

    issue.create_comment(f"Code Agent: created PR #{pr.number}. {fmt}")


def handle_pr_iteration_mode(repo, pr_number: int) -> None:
    pr = repo.get_pull(pr_number)

    m = re.search(r"AI-ITERATION:\s*(\d+)", pr.body or "")
    iteration = int(m.group(1)) if m else 1

    if iteration >= MAX_ITERATIONS:
        pr.create_issue_comment("Code Agent: iteration limit reached.")
        return

    issue_number = None
    m = re.search(r"Closes\s+#(\d+)", pr.body or "")
    if m:
        issue_number = int(m.group(1))

    issue_title = ""
    issue_body = ""
    if issue_number:
        issue = repo.get_issue(number=issue_number)
        issue_title = issue.title or ""
        issue_body = issue.body or ""

    ensure_git_identity()
    sh(["git", "checkout", "-B", pr.head.ref, f"origin/{pr.head.ref}"])

    prompt = CODE_PROMPT.format(title=issue_title, body=issue_body)
    raw, mode = llm_chat(prompt)

    files = parse_files_from_llm(raw)
    if not files:
        pr.create_issue_comment(f"Code Agent: no code generated (mode={mode}).")
        return

    write_files(files)
    fmt = maybe_format_with_black()

    if not commit_if_needed(f"Fix after review (iteration {iteration + 1})"):
        pr.create_issue_comment("Code Agent: no effective changes.")
        return

    sh(["git", "push"])

    pr.edit(
        body=re.sub(
            r"AI-ITERATION:\s*\d+",
            f"AI-ITERATION: {iteration + 1}",
            pr.body,
        )
    )

    pr.create_issue_comment(f"Code Agent: pushed iteration {iteration + 1}. {fmt}")


# -------------------- entry --------------------


def main() -> None:
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--issue", type=int)
    g.add_argument("--pr", type=int)
    args = parser.parse_args()

    repo = gh_client().get_repo(get_repo_full_name())

    if args.issue:
        handle_issue_mode(repo, args.issue)
    else:
        handle_pr_iteration_mode(repo, args.pr)


if __name__ == "__main__":
    main()
