from dataclasses import dataclass
from typing import Dict, Optional

from .field_competition import FieldCompetitionResult, analyze_field_competition
from .runtime_policy import (
    ENTERPRISE_PROFILE,
    RuntimePolicyProfile,
    RuntimePolicyResult,
    decide_runtime_policy,
)


@dataclass
class RuntimeFirewallResult:
    decision: str
    processing_mode: str
    route: str
    confidence: float
    reason: str
    best_field: str
    best_cost: float
    second_field: str
    second_cost: float
    field_margin: float
    coherence_risk: float
    costs: Dict[str, float]


class SemanticRuntimeFirewall:
    """
    ACE Semantic Runtime Firewall.

    This class expects precomputed semantic field costs.

    It does not compute embeddings directly.
    It applies the runtime criterion:

        best_field + best_cost + field_margin + coherence_risk
    """

    def __init__(
        self,
        profile: Optional[RuntimePolicyProfile] = None,
    ) -> None:
        self.profile = profile or ENTERPRISE_PROFILE

    def analyze(
        self,
        costs: Dict[str, float],
        coherence_risk: float = 0.0,
    ) -> RuntimeFirewallResult:
        competition: FieldCompetitionResult = analyze_field_competition(costs)

        policy: RuntimePolicyResult = decide_runtime_policy(
            competition=competition,
            coherence_risk=coherence_risk,
            profile=self.profile,
        )

        return RuntimeFirewallResult(
            decision=policy.decision,
            processing_mode=policy.processing_mode,
            route=policy.route,
            confidence=policy.confidence,
            reason=policy.reason,
            best_field=competition.best_field,
            best_cost=competition.best_cost,
            second_field=competition.second_field,
            second_cost=competition.second_cost,
            field_margin=competition.field_margin,
            coherence_risk=float(coherence_risk),
            costs=competition.costs,
        )