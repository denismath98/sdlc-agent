from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from core.state import SDLCState


@dataclass
class PlanResult:
    plan: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class CIResult:
    status: str
    summary: List[str] = field(default_factory=list)


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


@dataclass
class ReviewDecisionResult:
    review_result: ReviewResult
    state: "SDLCState"
    decision: str


@dataclass
class FullIterationResult:
    first_review_result: ReviewResult
    first_state: "SDLCState"
    first_decision: str
    developer_result: Optional[DeveloperResult] = None
    second_review_result: Optional[ReviewResult] = None
    second_state: Optional["SDLCState"] = None
    second_decision: Optional[str] = None
