from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from core.state import SDLCState


@dataclass
class ReviewResult:
    status: str
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    issue_number: Optional[int] = None
    ci_state: Optional[str] = None


@dataclass
class DeveloperResult:
    success: bool
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None
    message: str = ""


@dataclass
class StatefulDeveloperResult:
    result: DeveloperResult
    state: "SDLCState"


@dataclass
class StatefulReviewResult:
    result: ReviewResult
    state: "SDLCState"
