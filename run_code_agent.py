import argparse
import os
import re
import json
import subprocess
from datetime import datetime
from typing import Optional, Tuple

from github import Auth, Github

from agents.llm_client import llm_chat

MAX_ITERATIONS = 3
AI_DIR = ".ai"

# Safety rails: do not allow the agent to change dangerous files/paths.
ALLOWED_PATH_PREFIXES = ("agents/", "tests/", "src/", ".ai/")
ALLOWED_EXACT = ("README.md",)
DENY_PATH_PREFIXES = (".github/workflows/",)
DENY_EXACT = ("pyproject.toml", "docker-compose.yml", "Dockerfile")

MAX_DIFF_CHARS = 12000
LLM_PREVIEW_CHARS = 500


def sh(cmd: list[str]) -> str:
    res = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return res.stdout.strip()


def safe_branch_name(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\-_.]+", "-", text).strip("-")
    return text[:60] if len(text) > 60 else text


def ensure_git_identity() -> None:
    sh(["git", "config", "user.name", "code-agent[bot]"])
    sh(["git", "config", "user.email", "code-agent[bot]@users.noreply.github.com"])


def maybe_format_with_black() -> str:
    """Best-effort format. Never fails the agent run."""
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


def commit_change(message: str) -> bool:
    """Returns True if commit created, False if nothing to commit."""
    sh(["git", "add", "-A"])
    status = sh(["git", "status", "--porcelain"])
    if not status.strip():
        return False
    sh(["git", "commit", "-m", message])
    return True


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


def gh_client() -> Github:
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


# -------------------- LLM patch generation helpers --------------------


def repo_file_tree(max_files: int = 120) -> str:
    """
    IMPORTANT: keep this small to avoid huge prompts that cause HF Router to return reasoning only.
    """
    files = sh(["git", "ls-files"]).splitlines()
    files = [f for f in files if not f.startswith("build/")]
    # Prefer likely relevant dirs first
    preferred = []
    rest = []
    for f in files:
        if f.startswith(("src/", "tests/", "agents/")):
            preferred.append(f)
        else:
            rest.append(f)
    ordered = preferred + rest
    return "\n".join(ordered[:max_files])


def build_code_prompt(issue_title: str, issue_body: str, ai_review: str) -> str:
    tree = repo_file_tree()
    return f"""
SYSTEM:
You are a senior software engineer acting as a GitHub Code Agent.

DEVELOPER (ABSOLUTE RULES):
Return ONLY a valid JSON object with EXACT keys:
- "patch": string (a unified diff for `git apply`)
- "notes": string (1-2 short lines)

Rules for JSON:
- Output MUST be valid JSON (double quotes, no trailing commas).
- No markdown, no code fences, no extra text before/after JSON.

Rules for patch:
- patch MUST start with "diff --git a/".
- Do NOT include lines starting with: "index ", "new file mode", "deleted file mode".
- For new files you MUST use exactly: "--- /dev/null" and "+++ b/<path>".
- NEVER output '--- dev/null' (without slash).
- Every changed file MUST have at least one @@ hunk.
- Inside hunks, every line MUST start with '+', '-', ' ', or '\\'.
- Keep changes minimal and directly related to Issue / review feedback.

Safety constraints:
- Forbidden exact files: {DENY_EXACT}
- Forbidden path prefixes: {DENY_PATH_PREFIXES}
- Allowed path prefixes: {ALLOWED_PATH_PREFIXES}
- Allowed exact files: {ALLOWED_EXACT}

Repository file list (partial):
{tree}

Issue title:
{issue_title}

Issue body:
{issue_body}

Latest AI review feedback (fix these issues if present):
{ai_review}

OUTPUT (JSON only):
""".strip()


def _preview(text: str, n: int = LLM_PREVIEW_CHARS) -> str:
    t = (text or "").strip()
    if len(t) <= n:
        return t
    return t[:n] + "..."


def sanitize_llm_patch(text: str) -> str:
    t = (text or "").replace("\r\n", "\n").strip()
    if "```" in t:
        t = t.replace("```diff", "").replace("```", "").strip()
    idx = t.find("diff --git")
    if idx != -1:
        t = t[idx:]
    if t and not t.endswith("\n"):
        t += "\n"
    return t


def extract_patch_from_llm(text: str) -> Tuple[str, str]:
    """
    Returns (patch, notes). Supports:
    1) JSON: {"patch": "...", "notes": "..."}
    2) Fallback: raw unified diff starting from 'diff --git'
    """
    raw = (text or "").strip()

    # 1) Try pure JSON
    if raw.startswith("{"):
        try:
            obj = json.loads(raw)
            patch = (obj.get("patch") or "").strip()
            notes = (obj.get("notes") or "").strip()
            return patch, notes
        except Exception:
            pass

    # 2) Try to find JSON object inside text (common when model adds extra lines)
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            patch = (obj.get("patch") or "").strip()
            notes = (obj.get("notes") or "").strip()
            return patch, notes
        except Exception:
            pass

    # 3) Fallback to diff extraction
    idx = raw.find("diff --git")
    if idx != -1:
        return raw[idx:].strip(), ""

    return "", ""


def looks_like_unified_diff(t: str) -> bool:
    s = (t or "").lstrip()
    if not s.startswith("diff --git"):
        return False
    if "\n--- " not in s or "\n+++ " not in s:
        return False
    if "\n@@ " not in s:
        return False
    return True


def _path_is_allowed(path: str) -> bool:
    if path in ALLOWED_EXACT:
        return True
    return any(path.startswith(p) for p in ALLOWED_PATH_PREFIXES)


def diff_touches_forbidden(diff_text: str) -> Optional[str]:
    for line in diff_text.splitlines():
        if (
            line.startswith("+++ b/")
            or line.startswith("--- a/")
            or line.startswith("--- /dev/null")
        ):
            if line.startswith("--- /dev/null"):
                continue
            if line.startswith("+++ b/"):
                path = line[6:]
            else:
                path = line[6:]
            if not path or path == "/dev/null":
                continue
            if path in DENY_EXACT:
                return f"attempted to modify forbidden file: {path}"
            if any(path.startswith(p) for p in DENY_PATH_PREFIXES):
                return f"attempted to modify forbidden path: {path}"
            if not _path_is_allowed(path):
                return f"attempted to modify non-allowed path: {path}"
    return None


def normalize_dev_null(diff_text: str) -> str:
    diff_text = diff_text.replace("\r\n", "\n")
    diff_text = re.sub(r"(?m)^---\s+(?:a/)?dev/null\s*$", "--- /dev/null", diff_text)
    diff_text = re.sub(r"(?m)^\+\+\+\s+(?:b/)?dev/null\s*$", "+++ /dev/null", diff_text)
    return diff_text


def repair_unified_diff(diff_text: str) -> str:
    lines = diff_text.replace("\r\n", "\n").splitlines()
    out: list[str] = []
    in_hunk = False

    for line in lines:
        # Always treat these as STRUCTURAL, even if we were in a hunk
        if line.startswith("diff --git "):
            in_hunk = False
            out.append(line.rstrip())
            continue
        if line.startswith(("--- ", "+++ ")):
            in_hunk = False
            out.append(line.rstrip())
            continue
        if line.startswith("@@ "):
            in_hunk = True
            out.append(line.rstrip())
            continue

        if not in_hunk:
            out.append(line.rstrip())
            continue

        # Inside hunk: valid prefixes
        if line.startswith(("+", "-", " ", "\\")):
            out.append(line.rstrip())
            continue

        if line.strip() == "":
            out.append("+")
            continue

        out.append(("+" + line).rstrip())

    fixed = "\n".join(out)
    if not fixed.endswith("\n"):
        fixed += "\n"
    return fixed


def fix_bare_hunk_headers(diff_text: str) -> str:
    """
    Some models output invalid hunk headers like '@@' without ranges.
    This function upgrades bare hunks to a valid form for new-file patches:
      @@ -0,0 +1,N @@
    where N is the count of added lines until the next structural marker.
    """
    lines = diff_text.replace("\r\n", "\n").splitlines()
    out: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip() == "@@":
            # Count added lines until next structural marker
            j = i + 1
            added = 0
            while j < len(lines):
                nxt = lines[j]
                if nxt.startswith(("diff --git ", "--- ", "+++ ", "@@ ")):
                    break
                if nxt.startswith("+") or nxt == "+":
                    added += 1
                j += 1

            # Fallback if somehow zero
            if added <= 0:
                added = 1

            out.append(f"@@ -0,0 +1,{added} @@")
            i += 1
            continue

        out.append(line)
        i += 1

    fixed = "\n".join(out)
    if not fixed.endswith("\n"):
        fixed += "\n"
    return fixed


def canonicalize_llm_patch(patch: str) -> str:
    """
    Turn 'almost-unified-diff' produced by LLM into a strict unified diff that git can apply.
    Fixes:
    - Splits into sections by 'diff --git'
    - Normalizes /dev/null markers
    - Fixes bare '@@' headers by converting to '@@ -0,0 +1,N @@'
    - Ensures all hunk lines are prefixed (+/-/space)
    - Strips trailing whitespace
    """
    txt = (patch or "").replace("\r\n", "\n").strip()
    if "diff --git" not in txt:
        return ""

    # Keep only from first diff header
    txt = txt[txt.find("diff --git") :]

    # Split into file sections
    parts = re.split(r"(?m)^(?=diff --git )", txt)
    sections = [p for p in parts if p.strip()]

    out_sections: list[str] = []

    for sec in sections:
        lines = sec.splitlines()
        sec_out: list[str] = []

        in_hunk = False
        pending_bare_hunk = False
        bare_hunk_added = 0

        for line in lines:
            line = line.rstrip()

            # Structural lines reset hunk state
            if line.startswith("diff --git "):
                in_hunk = False
                pending_bare_hunk = False
                sec_out.append(line)
                continue

            if line.startswith("--- "):
                in_hunk = False
                pending_bare_hunk = False
                # normalize dev/null variants
                line = re.sub(r"^---\s+(?:a/)?dev/null$", "--- /dev/null", line)
                sec_out.append(line)
                continue

            if line.startswith("+++ "):
                in_hunk = False
                pending_bare_hunk = False
                line = re.sub(r"^\+\+\+\s+(?:b/)?dev/null$", "+++ /dev/null", line)
                sec_out.append(line)
                continue

            if line.startswith("@@ "):
                in_hunk = True
                pending_bare_hunk = False
                sec_out.append(line)
                continue

            if line.strip() == "@@":
                # bare hunk header, we will replace it later once we know N
                in_hunk = True
                pending_bare_hunk = True
                bare_hunk_added = 0
                sec_out.append("@@ __BARE__ @@")
                continue

            if not in_hunk:
                # Allow only known structural metadata or empty lines; keep as-is
                sec_out.append(line)
                continue

            # Inside hunk
            if line.startswith(("diff --git ", "--- ", "+++ ")):
                # If model accidentally emits structural lines inside hunk, close hunk
                in_hunk = False
                pending_bare_hunk = False
                sec_out.append(line)
                continue

            if line.startswith(("+", "-", " ", "\\")):
                sec_out.append(line)
                if pending_bare_hunk and (line.startswith("+") or line == "+"):
                    bare_hunk_added += 1
                continue

            if line == "":
                sec_out.append("+")
                if pending_bare_hunk:
                    bare_hunk_added += 1
                continue

            # Missing prefix -> treat as added line
            sec_out.append("+" + line)
            if pending_bare_hunk:
                bare_hunk_added += 1

        # Fix placeholder bare hunk header if present
        fixed_sec: list[str] = []
        for ln in sec_out:
            if ln == "@@ __BARE__ @@":
                n = bare_hunk_added if bare_hunk_added > 0 else 1
                fixed_sec.append(f"@@ -0,0 +1,{n} @@")
            else:
                fixed_sec.append(ln)

        # Ensure ends with newline
        out_sections.append("\n".join(fixed_sec).rstrip() + "\n")

    return "\n".join(out_sections).rstrip() + "\n"


def apply_unified_diff(diff_text: str) -> None:
    diff_text = canonicalize_llm_patch(diff_text)

    p = subprocess.run(
        ["git", "apply", "--whitespace=fix"],
        input=diff_text,
        text=True,
        capture_output=True,
    )
    if p.returncode == 0:
        return

    p2 = subprocess.run(
        ["git", "apply", "--3way", "--whitespace=fix"],
        input=diff_text,
        text=True,
        capture_output=True,
    )
    if p2.returncode == 0:
        return

    err1 = (p.stderr or "").strip()
    err2 = (p2.stderr or "").strip()
    raise RuntimeError(
        ("git apply failed:\n" + err1 + "\n---\n3way failed:\n" + err2).strip()
    )


def llm_generate_diff(prompt: str) -> Tuple[str, str, str]:
    raw, mode = llm_chat(prompt)
    raw = raw or ""
    cleaned = sanitize_llm_patch(raw)

    if not cleaned.strip():
        return "", mode, raw
    if not looks_like_unified_diff(cleaned):
        return "", mode, raw

    cleaned = cleaned[:MAX_DIFF_CHARS]
    return cleaned, mode, raw


def attempt_llm_patch(
    issue_title: str, issue_body: str, ai_review: str
) -> Tuple[bool, str, str, str]:
    """
    Returns (applied, mode, message, raw_preview)
    """

    def json_patch_prompt(core: str) -> str:
        # Оборачиваем любой core-текст в требование JSON
        return (
            core.strip()
            + "\n\n"
            + 'OUTPUT (JSON only): {"patch": "...", "notes": "..."}\n'
            + "Rules:\n"
            + "- Output MUST be valid JSON only. No extra text.\n"
            + '- JSON keys must be exactly: "patch", "notes".\n'
            + '- "patch" MUST be a unified diff starting with: diff --git a/\n'
            + "- Do NOT include lines starting with: index , new file mode, deleted file mode.\n"
            + "- For new files use exactly: --- /dev/null and +++ b/<path>\n"
            + "- Inside hunks, every line must start with '+', '-', ' ', or '\\\\'.\n"
        )

    def llm_generate_patch(prompt: str) -> Tuple[str, str, str]:
        """
        Returns (patch_text, llm_mode, raw_text)
        patch_text may be empty if parsing/sanity failed
        """
        raw, llm_mode = llm_chat(prompt)
        raw = raw or ""

        patch, _notes = extract_patch_from_llm(raw)  # <- ты добавлял эту функцию
        patch = sanitize_llm_patch(patch)  # <- у тебя уже есть
        if not patch or "diff --git" not in patch:
            return "", llm_mode, raw
        return patch, llm_mode, raw

    # -------- 1) main attempt --------
    base_prompt = build_code_prompt(issue_title, issue_body, ai_review=ai_review)
    prompt = json_patch_prompt(base_prompt)

    diff_text, llm_mode, raw1 = llm_generate_patch(prompt)
    raw_used = raw1

    # -------- 2) retry if empty --------
    if not diff_text:
        retry_core = f"""
Return a patch for `git apply` as JSON.

Issue:
{issue_title}
{issue_body}

Review feedback to fix:
{ai_review}
""".strip()

        diff_text, llm_mode2, raw2 = llm_generate_patch(json_patch_prompt(retry_core))
        llm_mode = llm_mode2
        raw_used = raw2

    if not diff_text:
        return (
            False,
            llm_mode,
            "no unified diff produced (sanity check failed)",
            _preview(raw_used),
        )

    # -------- 3) forbid checks --------
    reason = diff_touches_forbidden(diff_text)
    if reason:
        return False, llm_mode, f"patch rejected: {reason}", _preview(raw_used)

    # -------- 4) apply --------
    try:
        apply_unified_diff(diff_text)
        return True, llm_mode, "patch applied", _preview(raw_used)

    except Exception as e:
        # -------- 5) repair retry --------
        repair_core = f"""
Your previous patch failed to apply.

Return a NEW patch (JSON) that WILL apply cleanly with `git apply`.
If a file exists, MODIFY it. If missing, CREATE it using exactly:
--- /dev/null
+++ b/<path>
and @@ hunks.

Issue:
{issue_title}
{issue_body}

AI review feedback:
{ai_review}
""".strip()

        diff3, llm_mode3, raw3 = llm_generate_patch(json_patch_prompt(repair_core))
        if not diff3:
            return (
                False,
                llm_mode3,
                f"failed to apply patch; repair retry produced no diff. original error: {e}",
                _preview(raw3),
            )

        reason2 = diff_touches_forbidden(diff3)
        if reason2:
            return (
                False,
                llm_mode3,
                f"repair patch rejected: {reason2}",
                _preview(raw3),
            )

        try:
            apply_unified_diff(diff3)
            return True, llm_mode3, "patch applied (repair retry)", _preview(raw3)
        except Exception as e2:
            return (
                False,
                llm_mode3,
                f"failed to apply patch after repair retry: {e2}",
                _preview(raw3),
            )


# -------------------- Main flows --------------------


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
    sh(["git", "checkout", "-B", branch])

    created_path = write_ai_issue_file(issue_number, title, body)

    applied, llm_mode, msg, raw_preview = attempt_llm_patch(title, body, ai_review="")
    fmt_msg = maybe_format_with_black()

    issue.create_comment(
        f"Code Agent: LLM mode={llm_mode}; {msg}. {fmt_msg}\n\n"
        f"LLM preview (first {LLM_PREVIEW_CHARS} chars):\n{raw_preview}"
    )

    committed = commit_change(f"Implement Issue #{issue_number}")
    push_branch(branch)

    head = f"{owner}:{branch}"
    existing = find_existing_pr(gh_repo, head=head)

    pr_title = f"Implement #{issue_number}: {title}"
    pr_body = (
        f"Closes #{issue_number}\n\n"
        "AI-ITERATION: 1\n\n"
        f"Created `{created_path}`.\n"
        f"LLM mode: {llm_mode}; result: {msg}\n"
        f"{fmt_msg}\n"
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

    issue_number = extract_issue_number_from_pr(pr.body or "")
    ai_review = extract_latest_ai_review(pr)

    issue_title = ""
    issue_body = ""
    if issue_number:
        issue = gh_repo.get_issue(number=issue_number)
        issue_title = issue.title or ""
        issue_body = issue.body or ""

    ensure_git_identity()
    branch = pr.head.ref
    checkout_remote_branch(branch)

    applied, llm_mode, msg, raw_preview = attempt_llm_patch(
        issue_title, issue_body, ai_review=ai_review
    )
    fmt_msg = maybe_format_with_black()

    if not applied:
        pr.create_issue_comment(
            f"Code Agent: LLM patch not applied (mode={llm_mode}): {msg}. {fmt_msg}\n"
            "No changes committed; iteration not bumped.\n\n"
            f"LLM preview (first {LLM_PREVIEW_CHARS} chars):\n{raw_preview}"
        )
        print(f"OK: no patch applied for PR #{pr_number}")
        return

    committed = commit_change(f"Fix based on AI review (iteration {current_iter + 1})")
    if not committed:
        pr.create_issue_comment(
            f"Code Agent: patch applied but resulted in no net changes. {fmt_msg}\n"
            "Iteration not bumped."
        )
        print(f"OK: no net changes for PR #{pr_number}")
        return

    push_branch(branch)

    next_iter = current_iter + 1
    pr.edit(body=bump_iteration(pr.body or "", next_iter))
    pr.create_issue_comment(
        f"Code Agent: iteration {next_iter} pushed updates. "
        f"LLM mode={llm_mode}; {msg}. {fmt_msg}"
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

    handle_pr_iteration_mode(gh_repo, args.pr)


if __name__ == "__main__":
    main()
