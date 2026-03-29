from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .context_matrix import ContextMatchResult


@dataclass
class ContextField:
    context_name: str
    subcontext_name: Optional[str]
    reference_prompt: str
    axioms: List[str]
    knowledge: List[str]
    anchors: List[str]
    metadata: Dict[str, object] = field(default_factory=dict)


class ContextFieldBuilder:
    """
    Build a contextual reference field from a matched context.

    This converts context detection into a structured semantic field
    that can later be used to construct the ACE reference subspace.
    """

    def build(self, match: ContextMatchResult) -> Optional[ContextField]:
        if match.best_context is None:
            return None

        context = match.best_context
        sub_name = match.best_subcontext
        sub = None

        if sub_name is not None:
            for item in context.subcontexts:
                if item.name == sub_name:
                    sub = item
                    break

        anchors = list(context.semantic_anchors)
        axioms = list(context.default_axioms)
        knowledge = list(context.default_knowledge)

        if sub is not None:
            anchors.extend(sub.anchors)
            knowledge.extend(sub.keywords)
            knowledge.extend(sub.intent_markers)

        reference_prompt = self._build_reference_prompt(
            context_name=context.name,
            context_description=context.description,
            reality_anchor=context.reality_anchor,
            subcontext_name=sub.name if sub else None,
            subcontext_description=sub.description if sub else None,
        )

        return ContextField(
            context_name=context.name,
            subcontext_name=sub.name if sub else None,
            reference_prompt=reference_prompt,
            axioms=self._unique_clean(axioms),
            knowledge=self._unique_clean(knowledge),
            anchors=self._unique_clean(anchors),
            metadata={
                "best_score": match.best_score,
                "candidate_contexts": match.candidate_contexts,
                "is_ambiguous": match.is_ambiguous,
                "needs_clarification": match.needs_clarification,
            },
        )

    def _build_reference_prompt(
        self,
        *,
        context_name: str,
        context_description: str,
        reality_anchor: str,
        subcontext_name: Optional[str],
        subcontext_description: Optional[str],
    ) -> str:
        parts = [
            f"context: {context_name}",
            f"description: {context_description}",
            f"reality anchor: {reality_anchor}",
        ]

        if subcontext_name:
            parts.append(f"subcontext: {subcontext_name}")
        if subcontext_description:
            parts.append(f"subcontext description: {subcontext_description}")

        return " | ".join(parts)

    def _unique_clean(self, items: List[str]) -> List[str]:
        seen = set()
        output: List[str] = []

        for item in items:
            clean = item.strip()
            if not clean:
                continue
            if clean not in seen:
                seen.add(clean)
                output.append(clean)

        return output