import subprocess


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


def checkout_new_branch(branch_name: str, base_ref: str) -> None:
    sh(["git", "checkout", "-B", branch_name, base_ref])


def push_branch(branch_name: str, set_upstream: bool = True) -> None:
    if set_upstream:
        sh(["git", "push", "-u", "origin", branch_name])
    else:
        sh(["git", "push"])
