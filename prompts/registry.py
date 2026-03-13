from prompts.developer_prompt import CODE_PROMPT
from prompts.reviewer_prompt import REVIEWER_PROMPT

PROMPT_REGISTRY = {
    "developer.code": CODE_PROMPT,
    "reviewer.semantic": REVIEWER_PROMPT,
}


def get_prompt(name: str) -> str:
    if name not in PROMPT_REGISTRY:
        raise KeyError(f"Unknown prompt: {name}")
    return PROMPT_REGISTRY[name]
