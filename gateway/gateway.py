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
        verbose: bool = False,
        fast_message_template: str = "FAST PATH: responding directly to '{prompt}'",
        deep_message: str = (
            "DEEP PATH: semantic deviation detected. "
            "Escalating to deeper analysis."
        ),
        abstain_message: str = (
            "The request is too semantically unstable to answer safely."
        ),
    ) -> None:
        if ace_threshold < 0 or deep_threshold < 0:
            raise ValueError("Thresholds must be non-negative.")
        if ace_threshold > deep_threshold:
            raise ValueError(
                "ace_threshold must be less than or equal to deep_threshold."
            )

        self.ace_threshold = ace_threshold
        self.deep_threshold = deep_threshold
        self.verbose = verbose
        self.fast_message_template = fast_message_template
        self.deep_message = deep_message
        self.abstain_message = abstain_message

    def process_request(
        self,
        prompt: str,
        axioms: Optional[List[str]] = None,
        knowledge: Optional[List[str]] = None,
    ) -> GatewayResult:
        axioms = axioms or []
        knowledge = knowledge or []

        score = self._compute_origin_cost(prompt, axioms, knowledge)

        if self.verbose:
            print(
                f"[ACE] score={score:.4f} "
                f"ace_threshold={self.ace_threshold:.4f} "
                f"deep_threshold={self.deep_threshold:.4f}"
            )

        if score < self.ace_threshold:
            result = GatewayResult(
                decision="answer",
                path="fast",
                score=score,
                response=self._fast_path(prompt),
                metadata={"reason": "Low semantic deviation"},
            )
            self._log_result(result)
            return result

        if score < self.deep_threshold:
            result = GatewayResult(
                decision="clarify",
                path="deep",
                score=score,
                response=self._deep_analysis(prompt, axioms, knowledge),
                metadata={"reason": "Moderate semantic instability"},
            )
            self._log_result(result)
            return result

        result = GatewayResult(
            decision="abstain",
            path="blocked",
            score=score,
            response=self.abstain_message,
            metadata={"reason": "High semantic instability"},
        )
        self._log_result(result)
        return result

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
        return self.fast_message_template.format(prompt=prompt)

    def _deep_analysis(
        self,
        prompt: str,
        axioms: List[str],
        knowledge: List[str],
    ) -> str:
        return self.deep_message

    def _log_result(self, result: GatewayResult) -> None:
        if self.verbose:
            print(
                f"[ACE] decision={result.decision} "
                f"path={result.path} "
                f"score={result.score:.4f}"
            )