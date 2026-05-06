from dataclasses import dataclass
from typing import Literal

from .field_competition import FieldCompetitionResult


ProcessingMode = Literal["full", "light", "short", "reject"]


@dataclass
class RuntimePolicyResult:
    decision: str
    processing_mode: ProcessingMode
    route: str
    confidence: float
    reason: str


@dataclass
class RuntimePolicyProfile:
    name: str = "enterprise"
    contradiction_threshold: float = 0.58
    strong_cost_threshold: float = 0.50
    strong_margin_threshold: float = 0.20
    light_cost_threshold: float = 0.65
    light_margin_threshold: float = 0.15


ENTERPRISE_PROFILE = RuntimePolicyProfile(
    name="enterprise",
    contradiction_threshold=0.58,
    strong_cost_threshold=0.50,
    strong_margin_threshold=0.20,
    light_cost_threshold=0.65,
    light_margin_threshold=0.15,
)


AGGRESSIVE_PROFILE = RuntimePolicyProfile(
    name="aggressive",
    contradiction_threshold=0.52,
    strong_cost_threshold=0.45,
    strong_margin_threshold=0.18,
    light_cost_threshold=0.60,
    light_margin_threshold=0.12,
)


SAFE_PROFILE = RuntimePolicyProfile(
    name="safe",
    contradiction_threshold=0.50,
    strong_cost_threshold=0.45,
    strong_margin_threshold=0.25,
    light_cost_threshold=0.58,
    light_margin_threshold=0.18,
)


def decide_runtime_policy(
    competition: FieldCompetitionResult,
    coherence_risk: float,
    profile: RuntimePolicyProfile = ENTERPRISE_PROFILE,
) -> RuntimePolicyResult:
    """
    ACE Runtime Firewall policy.

    This policy is based on the criterion discovered in the ACE Atlas experiments:

        best_field + best_cost + field_margin + coherence_risk

    The gateway does not claim universal factual truth.
    It decides whether an input is semantically stable enough for full inference.
    """

    if coherence_risk > profile.contradiction_threshold:
        return RuntimePolicyResult(
            decision="CONTRADICTION_RISK",
            processing_mode="short",
            route="none",
            confidence=0.90,
            reason="high_coherence_risk",
        )

    if (
        competition.best_cost < profile.strong_cost_threshold
        and competition.field_margin > profile.strong_margin_threshold
    ):
        return RuntimePolicyResult(
            decision=f"ROUTE_{competition.best_field.upper()}",
            processing_mode="full",
            route=competition.best_field,
            confidence=0.90,
            reason="clear_field_winner",
        )

    if (
        competition.best_cost < profile.light_cost_threshold
        and competition.field_margin > profile.light_margin_threshold
    ):
        return RuntimePolicyResult(
            decision=f"ROUTE_{competition.best_field.upper()}_LIGHT",
            processing_mode="light",
            route=competition.best_field,
            confidence=0.72,
            reason="moderate_field_winner",
        )

    if competition.field_margin <= profile.light_margin_threshold:
        return RuntimePolicyResult(
            decision="LOW_MARGIN_AMBIGUOUS",
            processing_mode="light",
            route="ambiguous",
            confidence=0.60,
            reason="weak_field_margin",
        )

    return RuntimePolicyResult(
        decision="OUT_OF_FIELD",
        processing_mode="short",
        route="none",
        confidence=0.75,
        reason="high_cost_no_clear_field",
    )