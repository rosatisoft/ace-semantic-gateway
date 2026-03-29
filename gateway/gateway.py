from dataclasses import dataclass
from typing import Any, Dict, Optional

from .ace_layer import ACELayer
from .context_field import ContextFieldBuilder
from .context_matrix import ContextMatrix


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
        clarification_message_template: str = "{question}",
        ace_layer: Optional[ACELayer] = None,
        context_matrix: Optional[ContextMatrix] = None,
        context_field_builder: Optional[ContextFieldBuilder] = None,
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
        self.clarification_message_template = clarification_message_template

        self.ace_layer = ace_layer or ACELayer()
        self.context_matrix = context_matrix or ContextMatrix()
        self.context_field_builder = context_field_builder or ContextFieldBuilder()

    def process_request(self, prompt: str) -> GatewayResult:
        context_match = self.context_matrix.match_context(prompt)

        if context_match.needs_clarification:
            question = context_match.clarification_question or (
                "I need a bit more context before answering."
            )

            result = GatewayResult(
                decision="clarify",
                path="context_refinement",
                score=context_match.best_score,
                response=self.clarification_message_template.format(question=question),
                metadata={
                    "reason": "Context is ambiguous or insufficiently grounded",
                    "context_match": {
                        "best_context": (
                            context_match.best_context.name
                            if context_match.best_context
                            else None
                        ),
                        "best_subcontext": context_match.best_subcontext,
                        "best_score": context_match.best_score,
                        "candidate_contexts": context_match.candidate_contexts,
                        "is_ambiguous": context_match.is_ambiguous,
                        "needs_clarification": context_match.needs_clarification,
                    },
                },
            )
            self._log_result(result)
            return result

        context_field = self.context_field_builder.build(context_match)
        if context_field is None:
            result = GatewayResult(
                decision="clarify",
                path="context_refinement",
                score=context_match.best_score,
                response="I need more context before I can evaluate this request safely.",
                metadata={"reason": "Context field could not be built"},
            )
            self._log_result(result)
            return result

        ace_result = self.ace_layer.compute_origin_cost_from_field(
            candidate=prompt,
            reference_prompt=context_field.reference_prompt,
            axioms=context_field.axioms,
            knowledge=context_field.knowledge,
        )
        score = ace_result.origin_cost

        if self.verbose:
            print(
                f"[ACE] score={score:.4f} "
                f"ace_threshold={self.ace_threshold:.4f} "
                f"deep_threshold={self.deep_threshold:.4f}"
            )
            print(
                f"[CTX] context={context_field.context_name} "
                f"subcontext={context_field.subcontext_name}"
            )

        metadata = {
            "reason": "",
            "context": {
                "context_name": context_field.context_name,
                "subcontext_name": context_field.subcontext_name,
                "reference_prompt": context_field.reference_prompt,
                "axioms": context_field.axioms,
                "knowledge": context_field.knowledge,
                "anchors": context_field.anchors,
                "metadata": context_field.metadata,
            },
            "ace": {
                "origin_cost": ace_result.origin_cost,
                "residual_norm": ace_result.residual_norm,
                "projected_norm": ace_result.projected_norm,
                "total_energy": ace_result.total_energy,
                "details": ace_result.metadata,
            },
        }

        if score < self.ace_threshold:
            metadata["reason"] = "Low semantic deviation inside contextual field"
            result = GatewayResult(
                decision="answer",
                path="fast",
                score=score,
                response=self._fast_path(prompt),
                metadata=metadata,
            )
            self._log_result(result)
            return result

        if score < self.deep_threshold:
            metadata["reason"] = "Moderate semantic instability inside contextual field"
            result = GatewayResult(
                decision="clarify",
                path="deep",
                score=score,
                response=self._deep_analysis(prompt),
                metadata=metadata,
            )
            self._log_result(result)
            return result

        metadata["reason"] = "High semantic instability inside contextual field"
        result = GatewayResult(
            decision="abstain",
            path="blocked",
            score=score,
            response=self.abstain_message,
            metadata=metadata,
        )
        self._log_result(result)
        return result

    def _fast_path(self, prompt: str) -> str:
        return self.fast_message_template.format(prompt=prompt)

    def _deep_analysis(self, prompt: str) -> str:
        return self.deep_message

    def _log_result(self, result: GatewayResult) -> None:
        if self.verbose:
            print(
                f"[ACE] decision={result.decision} "
                f"path={result.path} "
                f"score={result.score:.4f}"
            )