from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
from openai import OpenAI

from .origin_cost import origin_cost


Vector = np.ndarray


@dataclass
class EmbeddingProfile:
    costs: Dict[str, float]
    densities: Dict[str, float]
    coherence_risk: float


class OpenAIEmbeddingProvider:
    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.client = OpenAI()
        self.model = model

    def embed(self, texts: List[str]) -> List[Vector]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        return [
            np.array(item.embedding, dtype=float)
            for item in response.data
        ]


class EmbeddingRouter:
    """
    Embedding router using saved SVD semantic field bases.

    It loads:
      fields/conceptual/basis.npy
      fields/operational/basis.npy
      fields/narrative/basis.npy

    Then computes:
      origin_cost(text_vector, field_basis)
    """

    def __init__(self, embedding_provider: OpenAIEmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or OpenAIEmbeddingProvider()
        self.base_dir = Path(__file__).resolve().parent.parent
        self.fields_dir = self.base_dir / "fields"
        self.field_bases, self.field_vectors = self._load_field_artifacts()

    def analyze_text(self, text: str) -> EmbeddingProfile:
        vector = self.embedding_provider.embed([text])[0]

        costs = {
            field_name: origin_cost(vector, basis)
            for field_name, basis in self.field_bases.items()
        }

        densities = {
            field_name: density_score(vector, anchors, top_k=5)
            for field_name, anchors in self.field_vectors.items()
        }

        coherence_risk = estimate_coherence_risk(text)

        return EmbeddingProfile(
            costs=costs,
            densities=densities,
            coherence_risk=coherence_risk,
        )

    def _load_field_artifacts(self):
        field_bases = {}
        field_vectors = {}

        for field_name in ["conceptual", "operational", "narrative", "scientific", "legal", "business"]:
            field_dir = self.fields_dir / field_name
            basis_path = field_dir / "basis.npy"
            vectors_path = field_dir / "vectors.npy"

            if not basis_path.exists():
                raise FileNotFoundError(
                    f"Missing field basis: {basis_path}. "
                    "Run: python examples/build_field_matrix.py"
                )

            if not vectors_path.exists():
                raise FileNotFoundError(
                    f"Missing field vectors: {vectors_path}. "
                    "Run: python examples/build_field_matrix.py"
                )

            field_bases[field_name] = np.load(basis_path)
            field_vectors[field_name] = np.load(vectors_path)

        return field_bases, field_vectors


def estimate_coherence_risk(text: str) -> float:
    text = text.lower()

    contradiction_markers = [
        "true and false",
        "false and true",
        "completely false and completely true",
        "exists and does not exist",
        "nothing exists and everything exists",
        "square circle",
        "occurred and never occurred",
        "present and absent",
        "entirely present and entirely absent",
        "cause occurs after its own effect",
        "larger and smaller than itself",
        "identical and not identical",
        "meaningful and meaningless",
    ]

    if any(marker in text for marker in contradiction_markers):
        return 0.95

    return 0.10

def cosine_similarity(a: Vector, b: Vector) -> float:
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)

    if a_norm == 0 or b_norm == 0:
        return 0.0

    return float(np.dot(a, b) / (a_norm * b_norm))


def density_score(vector: Vector, anchor_vectors: np.ndarray, top_k: int = 5) -> float:
    """
    Estimate semantic density around a vector.

    Higher density means the input is close to several anchors
    within the winning field.

    This is different from origin_cost:
    - origin_cost measures distance to the field subspace.
    - density_score measures local support inside the field.
    """

    if len(anchor_vectors) == 0:
        return 0.0

    similarities = [
        cosine_similarity(vector, anchor)
        for anchor in anchor_vectors
    ]

    similarities = sorted(similarities, reverse=True)

    k = min(top_k, len(similarities))

    return float(sum(similarities[:k]) / k)