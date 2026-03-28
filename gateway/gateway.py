from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class GatewayResult:
    decision: str
    path: str
    score: float
    response: str
    metadata: Dict[str, Any]


class SemanticGateway:
    def __init__(
        self,
        ace_threshold: float = 0.35,
        deep_threshold: float = 0.65,
    ) -> None:
        self.ace_threshold = ace_threshold
        self.deep_threshold = deep_threshold

    def process_request(
        self,
        prompt: str,
        axioms: Optional[List[str]] = None,
        knowledge: Optional[List[str]] = None,
    ) -> GatewayResult:
        axioms = axioms or []
        knowledge = knowledge or []

        score = self._compute_origin_cost(prompt, axioms, knowledge)

        if score < self.ace_threshold:
            response = self._fast_path(prompt)
            return GatewayResult(
                decision="answer",
                path="fast",
                score=score,
                response=response,
                metadata={"reason": "Low semantic deviation"},
            )

        if score < self.deep_threshold:
            response = self._deep_analysis(prompt, axioms, knowledge)
            return GatewayResult(
                decision="clarify",
                path="deep",
                score=score,
                response=response,
                metadata={"reason": "Moderate semantic instability"},
            )

        return GatewayResult(
            decision="abstain",
            path="blocked",
            score=score,
            response="The request is too semantically unstable to answer safely.",
            metadata={"reason": "High semantic instability"},
        )

    def _compute_origin_cost(
        self,
        prompt: str,
        axioms: List[str],
        knowledge: List[str],
    ) -> float:
        # Placeholder score until ACE integration is connected.
        signal = len(prompt.split()) + len(axioms) + len(knowledge)
        return min(signal / 100.0, 1.0)

    def _fast_path(self, prompt: str) -> str:
        return f"FAST PATH: responding directly to '{prompt}'"

    def _deep_analysis(
        self,
        prompt: str,
        axioms: List[str],
        knowledge: List[str],
    ) -> str:
        return (
            "DEEP PATH: semantic deviation detected. "
            "Escalating to axiomatic analysis for further reasoning."
        )
