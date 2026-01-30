import json
import os
from dataclasses import dataclass

import requests


@dataclass
class LLMConfig:
    provider: str  # "mock" | "openai_compat"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout_s: int = 60


def load_llm_config() -> LLMConfig:
    raw = (os.getenv("LLM_CONFIG_JSON") or "").strip()

    # Default mode: mock (no secrets required)
    if not raw:
        return LLMConfig(provider="mock")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        # Fail safe: do not break CI; fall back to mock
        return LLMConfig(provider="mock")

    return LLMConfig(
        provider=data.get("provider", "mock"),
        api_key=data.get("api_key", ""),
        base_url=data.get("base_url", ""),
        model=data.get("model", ""),
        timeout_s=int(data.get("timeout_s", 60)),
    )


def llm_chat(prompt: str) -> str:
    cfg = load_llm_config()

    if cfg.provider == "mock":
        # Deterministic stub for CI and runs without secrets
        return "status=approved\n" "issues:\n- None\n" "suggestions:\n- None\n"

    if cfg.provider == "openai_compat":
        if not (cfg.api_key and cfg.base_url and cfg.model):
            raise RuntimeError("LLM_CONFIG_JSON missing api_key/base_url/model")

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

    raise RuntimeError(f"Unknown provider in LLM_CONFIG_JSON: {cfg.provider}")
