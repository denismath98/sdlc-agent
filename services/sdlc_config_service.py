import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CIConfig:
    enable_black_check: bool = True
    enable_pytest: bool = True


@dataclass
class ReviewConfig:
    require_ci_success: bool = True

    diff_max_chars: int = 8000
    issue_max_chars: int = 2000
    llm_output_max_chars: int = 2500


@dataclass
class SDLCConfig:
    default_branch: str = "main"
    max_iterations: int = 3
    repo_path: str = "."
    python_version: str = "3.11"
    ci: CIConfig = field(default_factory=CIConfig)
    review: ReviewConfig = field(default_factory=ReviewConfig)


def _safe_json_load(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_sdlc_config() -> SDLCConfig:
    config_path = os.getenv("SDLC_CONFIG_PATH", ".sdlc-agent/config.json")
    data = _safe_json_load(Path(config_path))

    ci_data = data.get("ci") if isinstance(data.get("ci"), dict) else {}
    review_data = data.get("review") if isinstance(data.get("review"), dict) else {}

    return SDLCConfig(
        default_branch=str(data.get("default_branch", "main")),
        max_iterations=int(data.get("max_iterations", 3)),
        repo_path=str(data.get("repo_path", ".")),
        python_version=str(data.get("python_version", "3.11")),
        ci=CIConfig(
            enable_black_check=bool(ci_data.get("enable_black_check", True)),
            enable_pytest=bool(ci_data.get("enable_pytest", True)),
        ),
        review=ReviewConfig(
            require_ci_success=review_data.get("require_ci_success", True),
            diff_max_chars=review_data.get("diff_max_chars", 8000),
            issue_max_chars=review_data.get("issue_max_chars", 3000),
            llm_output_max_chars=review_data.get("llm_output_max_chars", 4000),
        ),
    )
