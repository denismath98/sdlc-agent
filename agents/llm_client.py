import os
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class LLMConfig:
    provider: str  # "openai_compat" or "yandexgpt" or "mock"
    api_key: str
    base_url: str
    model: str
    timeout_s: int = 60


def load_llm_config() -> LLMConfig:
    provider = os.getenv("LLM_PROVIDER", "mock")
    api_key = os.getenv("LLM_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "")
    model = os.getenv("LLM_MODEL", "")
    return LLMConfig(provider=provider, api_key=api_key, base_url=base_url, model=model)


def llm_chat(prompt: str) -> str:
    """
    Minimal LLM client.
    Supports:
    - provider=mock -> returns a deterministic stub
    - provider=openai_compat -> OpenAI-compatible /v1/chat/completions
    """
    cfg = load_llm_config()

    if cfg.provider == "mock":
        # Deterministic output for CI / local runs without secrets
        return "status=approved\n" "issues:\n- None\n" "suggestions:\n- None\n"

    if cfg.provider == "openai_compat":
        if not (cfg.api_key and cfg.base_url and cfg.model):
            raise RuntimeError("Missing LLM_* env vars for openai_compat provider")

        url = cfg.base_url.rstrip("/") + "/v1/chat/completions"
        headers = {"Authorization": f"Bearer {cfg.api_key}"}
        payload = {
            "model": cfg.model,
            "messages": [
                {"role": "system", "content": "You are a strict code reviewer."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        r = requests.post(url, json=payload, headers=headers, timeout=cfg.timeout_s)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

    raise RuntimeError(f"Unknown LLM_PROVIDER: {cfg.provider}")
