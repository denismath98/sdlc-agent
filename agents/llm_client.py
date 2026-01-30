import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests


@dataclass
class LLMConfig:
    mode: str = "mock"  # mock | openai_chat | hf_inference | ollama_chat | custom_http
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout_s: int = 30
    temperature: float = 0.2
    max_tokens: int = 400
    headers: Dict[str, str] = None  # templated headers
    endpoints: Dict[str, str] = None  # endpoint paths


MOCK_TEXT = "status=approved\n" "issues:\n- None\n" "suggestions:\n- None\n"


def _safe_json_load(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return {}


def load_llm_config() -> LLMConfig:
    raw = (os.getenv("LLM_CONFIG_JSON") or "").strip()
    if not raw:
        return LLMConfig(mode="mock")

    data = _safe_json_load(raw)
    mode = (data.get("mode") or "mock").strip()

    headers = data.get("headers") or {}
    endpoints = data.get("endpoints") or {}

    return LLMConfig(
        mode=mode,
        base_url=(data.get("base_url") or "").strip(),
        api_key=(data.get("api_key") or "").strip(),
        model=(data.get("model") or "").strip(),
        timeout_s=int(data.get("timeout_s", 30)),
        temperature=float(data.get("temperature", 0.2)),
        max_tokens=int(data.get("max_tokens", 400)),
        headers=headers,
        endpoints=endpoints,
    )


def _render_template(s: str, cfg: LLMConfig) -> str:
    """
    Supports ${api_key} and {model}.
    """
    if s is None:
        return ""
    s = s.replace("${api_key}", cfg.api_key)
    s = s.replace("{model}", cfg.model)
    return s


def _build_headers(cfg: LLMConfig) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if cfg.headers:
        for k, v in cfg.headers.items():
            headers[str(k)] = _render_template(str(v), cfg)

    # Reasonable defaults
    headers.setdefault("Content-Type", "application/json")
    return headers


def _join_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _get_endpoint(cfg: LLMConfig, key: str, default_path: str) -> str:
    if cfg.endpoints and cfg.endpoints.get(key):
        return cfg.endpoints[key]
    return default_path


def _call_openai_chat(cfg: LLMConfig, prompt: str) -> str:
    path = _get_endpoint(cfg, "chat_completions", "/v1/chat/completions")
    url = _join_url(cfg.base_url, path)
    headers = _build_headers(cfg)

    payload = {
        "model": cfg.model or "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a strict code reviewer."},
            {"role": "user", "content": prompt},
        ],
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
    }

    r = requests.post(url, json=payload, headers=headers, timeout=cfg.timeout_s)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def _call_ollama_chat(cfg: LLMConfig, prompt: str) -> str:
    path = _get_endpoint(cfg, "ollama_chat", "/api/chat")
    url = _join_url(cfg.base_url, path)
    headers = _build_headers(cfg)

    payload = {
        "model": cfg.model or "llama3",
        "messages": [
            {"role": "system", "content": "You are a strict code reviewer."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": cfg.temperature},
    }

    r = requests.post(url, json=payload, headers=headers, timeout=cfg.timeout_s)
    r.raise_for_status()
    data = r.json()
    # Ollama: {"message": {"content": "..."}}
    return (data.get("message") or {}).get("content") or ""


def _call_hf_inference(cfg: LLMConfig, prompt: str) -> str:
    if not cfg.model:
        raise RuntimeError("hf_inference requires 'model' in LLM_CONFIG_JSON")

    path = _get_endpoint(cfg, "hf_model", "/models/{model}")
    path = _render_template(path, cfg)
    url = _join_url(cfg.base_url, path)
    headers = _build_headers(cfg)

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": min(cfg.max_tokens, 400),
            "return_full_text": False,
        },
    }

    r = requests.post(url, json=payload, headers=headers, timeout=cfg.timeout_s)
    r.raise_for_status()
    data = r.json()

    if (
        isinstance(data, list)
        and data
        and isinstance(data[0], dict)
        and "generated_text" in data[0]
    ):
        return data[0]["generated_text"]

    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"HF inference error: {data['error']}")

    return str(data)


def llm_chat(prompt: str) -> Tuple[str, str]:
    """
    Returns (text, mode_used). Never raises due to provider problems (safe for CI).
    """
    cfg = load_llm_config()

    # default: mock if no base_url/api_key or mode is mock
    if cfg.mode == "mock" or not cfg.base_url:
        return MOCK_TEXT, "mock"

    try:
        if cfg.mode == "openai_chat":
            return _call_openai_chat(cfg, prompt), "openai_chat"
        if cfg.mode == "ollama_chat":
            return _call_ollama_chat(cfg, prompt), "ollama_chat"
        if cfg.mode == "hf_inference":
            return _call_hf_inference(cfg, prompt), "hf_inference"
        if cfg.mode == "custom_http":
            # You can implement later; for now do not fail CI.
            return (
                MOCK_TEXT
                + "\nsuggestions:\n- LLM disabled: custom_http is not implemented.\n",
                "mock",
            )

        # Unknown mode -> safe fallback
        return (
            MOCK_TEXT + f"\nsuggestions:\n- LLM disabled: unknown mode '{cfg.mode}'.\n",
            "mock",
        )
    except Exception as e:
        # Never fail CI due to LLM issues
        return (
            MOCK_TEXT + f"\nsuggestions:\n- LLM not used: {e}\n",
            "mock",
        )
