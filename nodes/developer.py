from core.models import DeveloperResult
from nodes.planner import plan_github_issue
from services.file_service import parse_files_from_llm, write_files
from services.github_issue_service import (
    create_issue_comment as create_issue_comment_for_issue,
    load_issue_data,
)
from services.github_service import (
    create_pr_comment,
    create_pull_request,
    extract_issue_number_from_pr_body,
    extract_iteration_from_pr_body,
    get_pull_request,
    get_repo,
    update_pr_iteration,
    get_latest_ai_review_comment,
)
from services.git_service import (
    checkout_new_branch,
    commit_if_needed,
    ensure_git_identity,
    maybe_format_with_black,
    push_branch,
)
from services.ai_artifacts_service import write_issue_artifact
from services.llm_service import llm_chat
from services.sdlc_config_service import load_sdlc_config
from services.code_context_service import extract_context_file_paths, read_context_files
from prompts.registry import get_prompt


def build_developer_prompt(
    issue_title: str,
    issue_body: str,
    plan: list[str],
    review_feedback: str = "",
    code_context: str = "",
) -> str:
    plan_block = (
        "\n".join(f"- {step}" for step in plan)
        if plan
        else "- Реализовать требуемые изменения."
    )

    feedback_block = review_feedback.strip() if review_feedback else "Нет"

    context_block = code_context.strip() if code_context else "Контекстные файлы не предоставлены."

    template = get_prompt("developer.code")
    return template.format(
        title=issue_title,
        body=issue_body,
        plan=plan_block,
        feedback=feedback_block,
        code_context=context_block,
    )


def extract_rework_feedback(ai_review_text: str) -> str:
    text = (ai_review_text or "").strip()
    if not text:
        return ""

    lines = text.splitlines()
    useful_lines: list[str] = []
    capture = False

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.startswith("issues:"):
            capture = True
            useful_lines.append("Review issues:")
            continue

        if line.startswith("suggestions:"):
            useful_lines.append("Review suggestions:")
            continue

        if capture:
            useful_lines.append(line)

    result = "\n".join(x for x in useful_lines if x.strip()).strip()
    return result


def run_developer_for_issue(issue_number: int, iteration: int = 1) -> DeveloperResult:
    repo = get_repo()
    issue_data = load_issue_data(issue_number)
    plan_result = plan_github_issue(issue_number)

    ensure_git_identity()

    write_issue_artifact(
        issue_number=issue_number,
        title=issue_data.title,
        body=issue_data.body,
    )

    branch_name = f"issue-{issue_number}"
    config = load_sdlc_config()
    base_branch = config.default_branch or repo.default_branch
    print(f"Using configured base branch: {base_branch}")
    checkout_new_branch(branch_name, base_branch)

    context_paths = extract_context_file_paths(issue_data.body or "")
    code_context = read_context_files(context_paths)
    prompt = build_developer_prompt(
        issue_title=issue_data.title,
        issue_body=issue_data.body,
        plan=plan_result.plan,
        code_context=code_context,
    )

    raw, mode = llm_chat(prompt)
    files = parse_files_from_llm(raw)

    if not files:
        return DeveloperResult(
            success=False,
            branch_name=branch_name,
            pr_number=None,
            message=f"LLM returned no files (mode={mode}).",
        )

    write_files(files)
    fmt_result = maybe_format_with_black()

    committed = commit_if_needed(
        f"Implement issue #{issue_number} (iteration {iteration})"
    )
    if not committed:
        return DeveloperResult(
            success=False,
            branch_name=branch_name,
            pr_number=None,
            message=f"No effective changes were produced. {fmt_result}",
        )

    push_branch(branch_name, set_upstream=True)

    pr = create_pull_request(
        repo=repo,
        title=f"Implement #{issue_number}: {issue_data.title}",
        body=f"Closes #{issue_number}\n\nAI-ITERATION: {iteration}",
        head=branch_name,
        base=base_branch,
    )

    create_issue_comment_for_issue(
        issue_number,
        f"Code Agent: created PR #{pr.number}. {fmt_result}",
    )

    return DeveloperResult(
        success=True,
        branch_name=branch_name,
        pr_number=pr.number,
        message=f"Developer changes applied, pushed, and PR #{pr.number} created. {fmt_result}",
    )


def run_developer_for_pr(pr_number: int) -> DeveloperResult:
    config = load_sdlc_config()
    pr = get_pull_request(pr_number)
    iteration = extract_iteration_from_pr_body(pr.body or "")

    if iteration >= config.max_iterations:
        create_pr_comment(pr, "Code Agent: iteration limit reached.")
        return DeveloperResult(
            success=False,
            branch_name=pr.head.ref,
            pr_number=pr.number,
            message="Iteration limit reached.",
        )

    issue_number = extract_issue_number_from_pr_body(pr.body or "")
    issue_title = ""
    issue_body = ""

    if issue_number:
        issue_data = load_issue_data(issue_number)
        issue_title = issue_data.title
        issue_body = issue_data.body

    ensure_git_identity()
    checkout_new_branch(pr.head.ref, f"origin/{pr.head.ref}")

    plan = []
    if issue_number:
        plan_result = plan_github_issue(issue_number)
        plan = plan_result.plan

    latest_ai_review = get_latest_ai_review_comment(pr)
    review_feedback = extract_rework_feedback(latest_ai_review)

    context_paths = extract_context_file_paths(issue_body or "")
    code_context = read_context_files(context_paths)

    prompt = build_developer_prompt(
        issue_title=issue_title,
        issue_body=issue_body,
        plan=plan,
        review_feedback=review_feedback,
        code_context=code_context,
    )

    raw, mode = llm_chat(prompt)
    files = parse_files_from_llm(raw)

    if not files:
        create_pr_comment(pr, f"Code Agent: no code generated (mode={mode}).")
        return DeveloperResult(
            success=False,
            branch_name=pr.head.ref,
            pr_number=pr.number,
            message=f"No code generated (mode={mode}).",
        )

    write_files(files)
    fmt_result = maybe_format_with_black()

    next_iteration = iteration + 1
    committed = commit_if_needed(f"Fix after review (iteration {next_iteration})")
    if not committed:
        create_pr_comment(pr, "Code Agent: no effective changes.")
        return DeveloperResult(
            success=False,
            branch_name=pr.head.ref,
            pr_number=pr.number,
            message=f"No effective changes. {fmt_result}",
        )

    push_branch(pr.head.ref, set_upstream=False)
    update_pr_iteration(pr, next_iteration)

    create_pr_comment(
        pr,
        f"Code Agent: pushed iteration {next_iteration}. {fmt_result}",
    )

    return DeveloperResult(
        success=True,
        branch_name=pr.head.ref,
        pr_number=pr.number,
        message=f"Iteration {next_iteration} pushed successfully. {fmt_result}",
    )
