from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import numpy as np
from openai import OpenAI

from atlas.core import (
    AtlasRuntimeEvaluator,
    SemanticFieldLoader,
    decide_runtime_action,
)


@dataclass
class AtlasGuardResult:
    input: str
    action: str
    allow_llm: bool
    processing_mode: str
    route: str
    reason: str
    best_field: str
    best_cost: float
    second_field: str
    second_cost: float
    field_margin: float
    best_density: float
    density_margin: float
    stability_index: float
    clarification: Optional[str]
    costs: Dict[str, float]
    densities: Dict[str, float]
    profile: str


class OpenAITextEmbedder:
    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.client = OpenAI()
        self.model = model

    def embed(self, text: str) -> np.ndarray:
        response = self.client.embeddings.create(
            model=self.model,
            input=[text],
        )
        return np.array(response.data[0].embedding, dtype=float)


class AtlasGatewayAdapter:
    """
    Adapter between ACE Semantic Gateway and ACE Atlas.

    ACE Atlas provides:
    - semantic fields
    - runtime evaluation
    - stability metrics
    - semantic dispersion gate policy

    ACE Semantic Gateway provides:
    - API surface
    - profile selection
    - middleware response formatting
    - future LLM orchestration
    """

    def __init__(
        self,
        fields_dir: Optional[str | Path] = None,
        profile: str = "enterprise",
        embedder: Optional[OpenAITextEmbedder] = None,
    ) -> None:
        self.profile = profile
        self.base_dir = Path(__file__).resolve().parent.parent

        self.fields_dir = (
            Path(fields_dir)
            if fields_dir is not None
            else self.base_dir / "fields"
        )

        self.embedder = embedder or OpenAITextEmbedder()

        self.atlas = SemanticFieldLoader(self.fields_dir).load_all()
        self.evaluator = AtlasRuntimeEvaluator(self.atlas)

    def guard(self, text: str) -> AtlasGuardResult:
        vector = self.embedder.embed(text)

        evaluation = self.evaluator.evaluate(
            text=text,
            vector=vector,
        )

        decision = decide_runtime_action(evaluation)

        allow_llm = decision.action in {"ALLOW", "ALLOW_LIGHT"}

        clarification = None
        if decision.action == "CLARIFY":
            clarification = self._build_clarification(
                text=text,
                best_field=evaluation.best_field,
                reason=decision.reason,
            )

        processing_mode = {
            "ALLOW": "full",
            "ALLOW_LIGHT": "light",
            "CLARIFY": "short",
        }.get(decision.action, "short")

        route = (
            evaluation.best_field
            if decision.action in {"ALLOW", "ALLOW_LIGHT"}
            else "clarify"
        )

        return AtlasGuardResult(
            input=text,
            action=decision.action,
            allow_llm=allow_llm,
            processing_mode=processing_mode,
            route=route,
            reason=decision.reason,
            best_field=evaluation.best_field,
            best_cost=float(evaluation.best_cost),
            second_field=evaluation.second_field,
            second_cost=float(evaluation.second_cost),
            field_margin=float(evaluation.field_margin),
            best_density=float(evaluation.stability.best_density),
            density_margin=float(evaluation.stability.density_margin),
            stability_index=float(evaluation.stability_index),
            clarification=clarification,
            costs={
                name: float(value)
                for name, value in evaluation.costs.items()
            },
            densities={
                name: float(value)
                for name, value in evaluation.densities.items()
            },
            profile=self.profile,
        )

    def _build_clarification(
        self,
        *,
        text: str,
        best_field: str,
        reason: str,
    ) -> str:
        field_hint = best_field.replace("_", " ")

        if reason == "low_stability":
            return (
                "I need a little more context before answering reliably. "
                f"Are you asking from a {field_hint} perspective?"
            )

        if reason == "weak_field_margin":
            return (
                "Your request may fit more than one semantic field. "
                "Could you clarify the intended context or objective?"
            )

        if reason == "high_cost":
            return (
                "The request does not clearly fit a stable contextual field. "
                "Could you add more details about what you want to resolve?"
            )

        return (
            "I need more context before giving a reliable answer. "
            "Could you clarify the intended domain, goal, or situation?"
        )