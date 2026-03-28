from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

Vector = np.ndarray


def deterministic_text_embedder(text: str, dim: int = 64) -> Vector:
    """
    Lightweight deterministic embedder for local context matching.

    This is a local approximation layer for context routing.
    It is not intended as a production semantic embedder.
    """
    vec = np.zeros(dim, dtype=float)

    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i in range(dim):
            vec[i] += digest[i % len(digest)] / 255.0

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec


def cosine_similarity(a: Vector, b: Vector) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)

    if na == 0 or nb == 0:
        return 0.0

    return float(np.dot(a, b) / (na * nb))


@dataclass
class ContextProfile:
    name: str
    description: str
    reality_anchor: str
    semantic_anchors: List[str]
    default_axioms: List[str]
    default_knowledge: List[str]
    clarification_prompts: List[str]
    subcontexts: List[str] = field(default_factory=list)

    def canonical_text(self) -> str:
        parts = [
            self.name,
            self.description,
            self.reality_anchor,
            *self.semantic_anchors,
            *self.subcontexts,
        ]
        return " ".join(parts)


@dataclass
class ContextScore:
    context_name: str
    score: float


@dataclass
class ContextMatchResult:
    best_context: Optional[ContextProfile]
    best_score: float
    ranked_scores: List[ContextScore]
    is_ambiguous: bool
    needs_clarification: bool
    candidate_contexts: List[str]
    clarification_question: Optional[str]
    metadata: Dict[str, object] = field(default_factory=dict)


class ContextMatrix:
    def __init__(
        self,
        profiles: Optional[List[ContextProfile]] = None,
        *,
        ambiguity_margin: float = 0.08,
        match_threshold: float = 0.35,
        embed_dim: int = 64,
    ) -> None:
        self.profiles = profiles or self._default_profiles()
        self.ambiguity_margin = ambiguity_margin
        self.match_threshold = match_threshold
        self.embed_dim = embed_dim

        self._profile_embeddings: Dict[str, Vector] = {
            profile.name: deterministic_text_embedder(
                profile.canonical_text(),
                dim=self.embed_dim,
            )
            for profile in self.profiles
        }

    def match_context(self, text: str) -> ContextMatchResult:
        query_vec = deterministic_text_embedder(text, dim=self.embed_dim)

        scored: List[tuple[ContextProfile, float]] = []
        for profile in self.profiles:
            score = cosine_similarity(query_vec, self._profile_embeddings[profile.name])
            scored.append((profile, score))

        scored.sort(key=lambda item: item[1], reverse=True)

        ranked_scores = [
            ContextScore(context_name=profile.name, score=score)
            for profile, score in scored
        ]

        if not scored:
            return ContextMatchResult(
                best_context=None,
                best_score=0.0,
                ranked_scores=[],
                is_ambiguous=True,
                needs_clarification=True,
                candidate_contexts=[],
                clarification_question="I could not identify a reliable context for this request. Could you clarify what kind of question this is?",
                metadata={"reason": "no_context_profiles_available"},
            )

        best_profile, best_score = scored[0]
        second_score = scored[1][1] if len(scored) > 1 else -1.0

        is_ambiguous = (
            len(scored) > 1
            and abs(best_score - second_score) < self.ambiguity_margin
        )

        needs_clarification = best_score < self.match_threshold or is_ambiguous

        candidate_contexts = [profile.name for profile, _ in scored[:3]]

        clarification_question = None
        if needs_clarification:
            clarification_question = self._build_clarification_question(
                scored[:3],
                low_confidence=best_score < self.match_threshold,
                ambiguous=is_ambiguous,
            )

        return ContextMatchResult(
            best_context=None if needs_clarification and best_score < self.match_threshold else best_profile,
            best_score=best_score,
            ranked_scores=ranked_scores,
            is_ambiguous=is_ambiguous,
            needs_clarification=needs_clarification,
            candidate_contexts=candidate_contexts,
            clarification_question=clarification_question,
            metadata={
                "match_threshold": self.match_threshold,
                "ambiguity_margin": self.ambiguity_margin,
                "second_score": second_score,
            },
        )

    def _build_clarification_question(
        self,
        top_scored: List[tuple[ContextProfile, float]],
        *,
        low_confidence: bool,
        ambiguous: bool,
    ) -> str:
        names = [profile.name for profile, _ in top_scored]

        if low_confidence and names:
            options = ", ".join(names)
            return (
                "I am not yet confident about the context of your request. "
                f"Is this mainly about {options}, or something else?"
            )

        if ambiguous and len(top_scored) >= 2:
            p1 = top_scored[0][0]
            p2 = top_scored[1][0]
            return (
                "Your request could belong to more than one context. "
                f"Are you asking from a {p1.name} perspective or a {p2.name} perspective?"
            )

        return (
            "I need a bit more context before answering. "
            "Could you clarify the perspective or domain of your request?"
        )

    @staticmethod
    def _default_profiles() -> List[ContextProfile]:
        return [
            ContextProfile(
                name="physical_reality",
                description="Questions about nature, physical processes, matter, energy, and the observable world.",
                reality_anchor="natural law and observable physical reality",
                semantic_anchors=[
                    "physics",
                    "chemistry",
                    "biology",
                    "astronomy",
                    "natural process",
                ],
                default_axioms=[
                    "preserve empirical consistency",
                    "avoid unsupported physical claims",
                ],
                default_knowledge=[
                    "observable phenomena",
                    "natural law",
                    "causal explanation",
                ],
                clarification_prompts=[
                    "Are you asking about a physical process, a biological process, or a scientific explanation?",
                ],
                subcontexts=[
                    "physics",
                    "chemistry",
                    "biology",
                    "astronomy",
                    "earth science",
                ],
            ),
            ContextProfile(
                name="formal_structure",
                description="Questions about mathematics, logic, proof, computation, and formal symbolic systems.",
                reality_anchor="logical consistency and formal validity",
                semantic_anchors=[
                    "mathematics",
                    "logic",
                    "proof",
                    "formal system",
                    "computation",
                ],
                default_axioms=[
                    "preserve logical validity",
                    "avoid contradiction",
                ],
                default_knowledge=[
                    "formal rules",
                    "symbolic structure",
                    "derivation",
                ],
                clarification_prompts=[
                    "Is this a mathematical, logical, or computational question?",
                ],
                subcontexts=[
                    "mathematics",
                    "logic",
                    "computer science",
                    "formal proof",
                ],
            ),
            ContextProfile(
                name="technical_systems",
                description="Questions about tools, software, servers, networks, infrastructure, troubleshooting, and applied engineering systems.",
                reality_anchor="functional system behavior and technical constraints",
                semantic_anchors=[
                    "software",
                    "server",
                    "network",
                    "configuration",
                    "error",
                    "troubleshooting",
                ],
                default_axioms=[
                    "preserve technical precision",
                    "avoid unsupported assumptions",
                ],
                default_knowledge=[
                    "system state",
                    "configuration",
                    "observed symptoms",
                ],
                clarification_prompts=[
                    "Is this about diagnosis, configuration, recovery, or design?",
                ],
                subcontexts=[
                    "software",
                    "networking",
                    "virtualization",
                    "storage",
                    "troubleshooting",
                ],
            ),
            ContextProfile(
                name="history_and_society",
                description="Questions about historical events, institutions, public life, society, culture, and collective processes.",
                reality_anchor="documented evidence and social reality",
                semantic_anchors=[
                    "history",
                    "society",
                    "institution",
                    "politics",
                    "culture",
                    "documented event",
                ],
                default_axioms=[
                    "preserve documentary caution",
                    "distinguish evidence from interpretation",
                ],
                default_knowledge=[
                    "historical records",
                    "social context",
                    "institutional process",
                ],
                clarification_prompts=[
                    "Are you asking about a historical event, a social issue, or an institutional matter?",
                ],
                subcontexts=[
                    "history",
                    "politics",
                    "sociology",
                    "culture",
                    "institutions",
                ],
            ),
            ContextProfile(
                name="psychology_and_person",
                description="Questions about emotion, motivation, behavior, cognition, personal experience, and inner states.",
                reality_anchor="human experience and behavior",
                semantic_anchors=[
                    "emotion",
                    "behavior",
                    "motivation",
                    "mind",
                    "experience",
                    "personal state",
                ],
                default_axioms=[
                    "preserve interpretive caution",
                    "avoid unsupported diagnosis",
                ],
                default_knowledge=[
                    "subjective experience",
                    "behavioral context",
                    "human cognition",
                ],
                clarification_prompts=[
                    "Are you asking about emotion, behavior, or personal meaning?",
                ],
                subcontexts=[
                    "emotion",
                    "motivation",
                    "behavior",
                    "cognition",
                    "mental health",
                ],
            ),
            ContextProfile(
                name="ethics_and_values",
                description="Questions about right and wrong, moral judgment, obligation, responsibility, and value conflicts.",
                reality_anchor="moral reasoning and human responsibility",
                semantic_anchors=[
                    "ethics",
                    "values",
                    "responsibility",
                    "justice",
                    "right and wrong",
                ],
                default_axioms=[
                    "preserve moral clarity",
                    "distinguish descriptive from normative claims",
                ],
                default_knowledge=[
                    "moral framework",
                    "human action",
                    "value conflict",
                ],
                clarification_prompts=[
                    "Is this mainly a moral question, a practical decision, or a personal dilemma?",
                ],
                subcontexts=[
                    "ethics",
                    "moral dilemma",
                    "justice",
                    "responsibility",
                ],
            ),
            ContextProfile(
                name="aesthetics_and_art",
                description="Questions about beauty, expression, form, style, music, literature, image, and artistic interpretation.",
                reality_anchor="human aesthetic experience and symbolic expression",
                semantic_anchors=[
                    "art",
                    "beauty",
                    "music",
                    "painting",
                    "literature",
                    "style",
                ],
                default_axioms=[
                    "preserve interpretive openness",
                    "avoid reducing aesthetic meaning to pure fact",
                ],
                default_knowledge=[
                    "symbolic expression",
                    "form",
                    "aesthetic experience",
                ],
                clarification_prompts=[
                    "Are you asking about artistic meaning, technique, or aesthetic value?",
                ],
                subcontexts=[
                    "music",
                    "painting",
                    "literature",
                    "film",
                    "design",
                ],
            ),
            ContextProfile(
                name="spirituality_and_meaning",
                description="Questions about purpose, ultimate meaning, transcendence, faith, spiritual reality, and existential interpretation.",
                reality_anchor="existential meaning and transcendent orientation",
                semantic_anchors=[
                    "meaning",
                    "purpose",
                    "faith",
                    "spirituality",
                    "existence",
                    "transcendence",
                ],
                default_axioms=[
                    "preserve existential seriousness",
                    "avoid flattening spiritual language into triviality",
                ],
                default_knowledge=[
                    "meaning",
                    "purpose",
                    "spiritual perspective",
                ],
                clarification_prompts=[
                    "Are you asking about existential meaning, spiritual belief, or personal purpose?",
                ],
                subcontexts=[
                    "faith",
                    "purpose",
                    "existential question",
                    "spiritual life",
                ],
            ),
            ContextProfile(
                name="practical_operations",
                description="Questions about what to do, how to proceed, execution steps, operational choices, and concrete action.",
                reality_anchor="practical constraints and decision execution",
                semantic_anchors=[
                    "action",
                    "steps",
                    "procedure",
                    "execution",
                    "decision",
                    "workflow",
                ],
                default_axioms=[
                    "preserve practical usefulness",
                    "avoid unnecessary abstraction when action is requested",
                ],
                default_knowledge=[
                    "constraints",
                    "goal",
                    "available actions",
                ],
                clarification_prompts=[
                    "Are you asking for a plan, a procedure, or help deciding between options?",
                ],
                subcontexts=[
                    "workflow",
                    "procedure",
                    "execution",
                    "decision support",
                ],
            ),
        ]
