from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, List, Optional

import numpy as np

from ace import ACEScorer

Embedder = Callable[[str], np.ndarray]


@dataclass
class ACELayerResult:
    origin_cost: float
    residual_norm: float
    projected_norm: float
    total_energy: float
    metadata: dict


def deterministic_text_embedder(text: str, dim: int = 64) -> np.ndarray:
    """
    Lightweight deterministic embedder for local testing.

    This is only for validating the ACE pipeline end-to-end.
    It is not a production semantic embedder.
    """
    vec = np.zeros(dim, dtype=float)

    tokens = text.lower().split()
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i in range(dim):
            vec[i] += digest[i % len(digest)] / 255.0

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec


class ACELayer:
    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        *,
        center_subspace: bool = True,
        default_rank: Optional[int] = None,
        svd_tol: float = 1e-10,
        lambda_o: float = 1.0,
    ) -> None:
        self.embedder = embedder or deterministic_text_embedder
        self.center_subspace = center_subspace
        self.default_rank = default_rank
        self.svd_tol = svd_tol
        self.lambda_o = float(lambda_o)

    def _build_scorer(self, *, center_subspace: bool) -> ACEScorer:
        return ACEScorer(
            center_subspace=center_subspace,
            default_rank=self.default_rank,
            svd_tol=self.svd_tol,
            lambda_o=self.lambda_o,
        )

    def compute_origin_cost(
        self,
        *,
        prompt: str,
        axioms: Optional[List[str]] = None,
        knowledge: Optional[List[str]] = None,
        candidate: Optional[str] = None,
    ) -> ACELayerResult:
        """
        Backward-compatible origin cost computation.

        If no axioms or knowledge are provided, a minimal fallback context is used
        so the reference subspace does not collapse.
        """
        axioms = axioms or []
        knowledge = knowledge or []
        candidate = candidate or prompt

        if not axioms and not knowledge:
            axioms = ["semantic consistency"]
            knowledge = ["context grounding"]

        prompt_embedding = self.embedder(prompt)
        axiom_embeddings = [self.embedder(item) for item in axioms]
        knowledge_embeddings = [self.embedder(item) for item in knowledge]
        candidate_embedding = self.embedder(candidate)

        reference_count = 1 + len(axiom_embeddings) + len(knowledge_embeddings)
        use_centering = self.center_subspace and reference_count > 1

        scorer = self._build_scorer(center_subspace=use_centering)

        score = scorer.score_candidate(
            prompt_embedding=prompt_embedding,
            axiom_embeddings=axiom_embeddings,
            knowledge_embeddings=knowledge_embeddings,
            candidate_embedding=candidate_embedding,
            candidate_label="request",
        )

        return ACELayerResult(
            origin_cost=float(score.origin_cost),
            residual_norm=float(score.residual_norm),
            projected_norm=float(score.projected_norm),
            total_energy=float(score.total_energy),
            metadata=score.details or {},
        )

    def compute_origin_cost_from_field(
        self,
        *,
        candidate: str,
        reference_prompt: str,
        axioms: List[str],
        knowledge: List[str],
    ) -> ACELayerResult:
        """
        Compute origin cost from a pre-built contextual reference field.

        This is the preferred method for the semantic gateway:
        context_matrix -> context_field -> ACE subspace -> candidate evaluation
        """
        prompt_embedding = self.embedder(reference_prompt)
        axiom_embeddings = [self.embedder(item) for item in axioms]
        knowledge_embeddings = [self.embedder(item) for item in knowledge]
        candidate_embedding = self.embedder(candidate)

        reference_count = 1 + len(axiom_embeddings) + len(knowledge_embeddings)
        use_centering = self.center_subspace and reference_count > 1

        scorer = self._build_scorer(center_subspace=use_centering)

        score = scorer.score_candidate(
            prompt_embedding=prompt_embedding,
            axiom_embeddings=axiom_embeddings,
            knowledge_embeddings=knowledge_embeddings,
            candidate_embedding=candidate_embedding,
            candidate_label="request",
        )

        return ACELayerResult(
            origin_cost=float(score.origin_cost),
            residual_norm=float(score.residual_norm),
            projected_norm=float(score.projected_norm),
            total_energy=float(score.total_energy),
            metadata=score.details or {},
        )