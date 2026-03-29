from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

Vector = np.ndarray


def deterministic_text_embedder(text: str, dim: int = 96) -> Vector:
    """
    Lightweight deterministic embedder for local semantic approximation.

    This is not a production embedder. Its role is only to provide a stable
    vector layer that complements lexical/contextual scoring.
    """
    vec = np.zeros(dim, dtype=float)

    for token in tokenize(text):
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


def split_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"[.!?\n]+", text)
    return [p.strip() for p in parts if p.strip()]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def count_matches(tokens: List[str], terms: List[str]) -> int:
    token_set = set(tokens)
    score = 0
    for term in terms:
        term_tokens = tokenize(term)
        if not term_tokens:
            continue

        if len(term_tokens) == 1:
            if term_tokens[0] in token_set:
                score += 1
        else:
            # Phrase match: all phrase tokens present
            if all(t in token_set for t in term_tokens):
                score += len(term_tokens)
    return score


@dataclass
class SubcontextProfile:
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    anchors: List[str] = field(default_factory=list)
    intent_markers: List[str] = field(default_factory=list)
    negative_markers: List[str] = field(default_factory=list)

    def canonical_text(self) -> str:
        parts = [
            self.name,
            self.description,
            *self.keywords,
            *self.anchors,
            *self.intent_markers,
        ]
        return " ".join(parts)


@dataclass
class ContextProfile:
    name: str
    description: str
    reality_anchor: str
    semantic_anchors: List[str]
    keywords: List[str]
    intent_markers: List[str]
    negative_markers: List[str]
    default_axioms: List[str]
    default_knowledge: List[str]
    clarification_prompts: List[str]
    subcontexts: List[SubcontextProfile] = field(default_factory=list)

    def canonical_text(self) -> str:
        parts = [
            self.name,
            self.description,
            self.reality_anchor,
            *self.semantic_anchors,
            *self.keywords,
            *self.intent_markers,
            *[sub.canonical_text() for sub in self.subcontexts],
        ]
        return " ".join(parts)


@dataclass
class ContextScore:
    context_name: str
    score: float
    lexical_score: float
    anchor_score: float
    intent_score: float
    negative_score: float
    vector_score: float
    coherence_score: float
    best_subcontext: Optional[str]


@dataclass
class ContextMatchResult:
    best_context: Optional[ContextProfile]
    best_subcontext: Optional[str]
    best_score: float
    ranked_scores: List[ContextScore]
    is_ambiguous: bool
    needs_clarification: bool
    candidate_contexts: List[str]
    clarification_question: Optional[str]
    metadata: Dict[str, object] = field(default_factory=dict)


class ContextMatrix:
    """
    Hierarchical local context matcher.

    It combines:
    - keyword evidence
    - semantic anchor evidence
    - intent markers
    - negative evidence
    - per-sentence coherence
    - lightweight vector similarity

    Goal:
    identify a stable contextual reference field before ACE evaluation.
    """

    def __init__(
        self,
        profiles: Optional[List[ContextProfile]] = None,
        *,
        ambiguity_margin: float = 0.10,
        match_threshold: float = 0.28,
        strong_match_threshold: float = 0.42,
        embed_dim: int = 96,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.profiles = profiles or self._default_profiles()
        self.ambiguity_margin = ambiguity_margin
        self.match_threshold = match_threshold
        self.strong_match_threshold = strong_match_threshold
        self.embed_dim = embed_dim

        self.weights = weights or {
            "keywords": 0.28,
            "anchors": 0.24,
            "intent": 0.12,
            "negative": 0.14,
            "vector": 0.08,
            "subcontext": 0.12,
            "coherence": 0.04,
        }

        self._profile_embeddings: Dict[str, Vector] = {
            profile.name: deterministic_text_embedder(
                profile.canonical_text(),
                dim=self.embed_dim,
            )
            for profile in self.profiles
        }

        self._subcontext_embeddings: Dict[Tuple[str, str], Vector] = {}
        for profile in self.profiles:
            for sub in profile.subcontexts:
                self._subcontext_embeddings[(profile.name, sub.name)] = deterministic_text_embedder(
                    sub.canonical_text(),
                    dim=self.embed_dim,
                )

    def match_context(self, text: str) -> ContextMatchResult:
        text = text.strip()
        if not text:
            return ContextMatchResult(
                best_context=None,
                best_subcontext=None,
                best_score=0.0,
                ranked_scores=[],
                is_ambiguous=True,
                needs_clarification=True,
                candidate_contexts=[],
                clarification_question="I need some input before I can identify the relevant context.",
                metadata={"reason": "empty_input"},
            )

        sentences = split_sentences(text)
        if not sentences:
            sentences = [text]

        overall_tokens = tokenize(text)
        query_vec = deterministic_text_embedder(text, dim=self.embed_dim)

        scored_profiles: List[Tuple[ContextProfile, ContextScore]] = []

        for profile in self.profiles:
            lexical_hits = count_matches(overall_tokens, profile.keywords)
            anchor_hits = count_matches(overall_tokens, profile.semantic_anchors)
            intent_hits = count_matches(overall_tokens, profile.intent_markers)
            negative_hits = count_matches(overall_tokens, profile.negative_markers)
            vector_sim = cosine_similarity(
                query_vec,
                self._profile_embeddings[profile.name],
            )

            best_subcontext_name, sub_score = self._score_subcontexts(
                profile,
                text,
                overall_tokens,
            )

            formal_priority_bonus = 0.0
            if profile.name == "formal_structure":
                if any(
                    term in overall_tokens
                    for term in [
                        "prove",
                        "proof",
                        "theorem",
                        "derivative",
                        "integral",
                        "equation",
                    ]
                ):
                    formal_priority_bonus = 0.12

            practical_penalty = 0.0
            if profile.name == "practical_operations":
                if any(
                    term in overall_tokens
                    for term in [
                        "prove",
                        "proof",
                        "theorem",
                        "derivative",
                        "integral",
                        "equation",
                    ]
                ):
                    practical_penalty = 0.10

            coherence_score = self._compute_sentence_coherence(profile, sentences)

            lexical_score = min(lexical_hits / 4.0, 1.0)
            anchor_score = min(anchor_hits / 4.0, 1.0)
            intent_score = min(intent_hits / 3.0, 1.0)
            negative_score = min(negative_hits / 3.0, 1.0)
            vector_score = max(vector_sim, 0.0)

            total = (
                self.weights["keywords"] * lexical_score
                + self.weights["anchors"] * anchor_score
                + self.weights["intent"] * intent_score
                - self.weights["negative"] * negative_score
                + self.weights["vector"] * vector_score
                + self.weights["subcontext"] * sub_score
                + self.weights["coherence"] * coherence_score
                + formal_priority_bonus
                - practical_penalty
            )

            total = max(total, 0.0)

            scored_profiles.append(
                (
                    profile,
                    ContextScore(
                        context_name=profile.name,
                        score=total,
                        lexical_score=lexical_score,
                        anchor_score=anchor_score,
                        intent_score=intent_score,
                        negative_score=negative_score,
                        vector_score=vector_score,
                        coherence_score=coherence_score,
                        best_subcontext=best_subcontext_name,
                    ),
                )
            )

        scored_profiles.sort(key=lambda item: item[1].score, reverse=True)

        ranked_scores = [score for _, score in scored_profiles]
        best_profile, best_score_obj = scored_profiles[0]
        best_score = best_score_obj.score
        second_score = scored_profiles[1][1].score if len(scored_profiles) > 1 else -1.0

        is_ambiguous = (
            len(scored_profiles) > 1
            and abs(best_score - second_score) < self.ambiguity_margin
        )

        low_confidence = best_score < self.match_threshold

        # Strong match rule:
        # if score is high enough and lexical/anchor evidence is meaningful, avoid unnecessary questions
        evidence_strength = (
            best_score_obj.lexical_score
            + best_score_obj.anchor_score
            + best_score_obj.intent_score
        )

        strong_match = (
            best_score >= self.strong_match_threshold
            and evidence_strength >= 0.40
            and not is_ambiguous
        )

        needs_clarification = (low_confidence or is_ambiguous) and not strong_match

        candidate_contexts = [profile.name for profile, _ in scored_profiles[:3]]
        clarification_question = None

        if needs_clarification:
            clarification_question = self._build_clarification_question(
                top_scored=scored_profiles[:3],
                low_confidence=low_confidence,
                ambiguous=is_ambiguous,
            )

        return ContextMatchResult(
            best_context=None if low_confidence else best_profile,
            best_subcontext=best_score_obj.best_subcontext,
            best_score=best_score,
            ranked_scores=ranked_scores,
            is_ambiguous=is_ambiguous,
            needs_clarification=needs_clarification,
            candidate_contexts=candidate_contexts,
            clarification_question=clarification_question,
            metadata={
                "sentence_count": len(sentences),
                "second_score": second_score,
                "match_threshold": self.match_threshold,
                "strong_match_threshold": self.strong_match_threshold,
                "ambiguity_margin": self.ambiguity_margin,
                "best_evidence_strength": evidence_strength,
            },
        )

    def _score_subcontexts(
        self,
        profile: ContextProfile,
        text: str,
        tokens: List[str],
    ) -> Tuple[Optional[str], float]:
        if not profile.subcontexts:
            return None, 0.0

        query_vec = deterministic_text_embedder(text, dim=self.embed_dim)

        best_name = None
        best_score = 0.0

        for sub in profile.subcontexts:
            kw_hits = count_matches(tokens, sub.keywords)
            anchor_hits = count_matches(tokens, sub.anchors)
            intent_hits = count_matches(tokens, sub.intent_markers)
            neg_hits = count_matches(tokens, sub.negative_markers)

            lexical = min(kw_hits / 3.0, 1.0)
            anchor = min(anchor_hits / 3.0, 1.0)
            intent = min(intent_hits / 2.0, 1.0)
            negative = min(neg_hits / 2.0, 1.0)

            vec = cosine_similarity(
                query_vec,
                self._subcontext_embeddings[(profile.name, sub.name)],
            )

            total = (
                0.40 * lexical
                + 0.25 * anchor
                + 0.15 * intent
                + 0.20 * max(vec, 0.0)
                - 0.20 * negative
            )
            total = max(total, 0.0)

            if total > best_score:
                best_score = total
                best_name = sub.name

        return best_name, min(best_score, 1.0)

    def _compute_sentence_coherence(
        self,
        profile: ContextProfile,
        sentences: List[str],
    ) -> float:
        if len(sentences) <= 1:
            return 0.0

        hits = 0
        for sentence in sentences:
            tokens = tokenize(sentence)
            sentence_hits = (
                count_matches(tokens, profile.keywords)
                + count_matches(tokens, profile.semantic_anchors)
                + count_matches(tokens, profile.intent_markers)
            )
            if sentence_hits > 0:
                hits += 1

        return hits / len(sentences)

    def _build_clarification_question(
        self,
        top_scored: List[Tuple[ContextProfile, ContextScore]],
        *,
        low_confidence: bool,
        ambiguous: bool,
    ) -> str:
        names = [profile.name for profile, _ in top_scored]

        readable = {
            "physical_reality": "physical or scientific",
            "formal_structure": "mathematical or logical",
            "technical_systems": "technical or troubleshooting",
            "history_and_society": "historical or social",
            "psychology_and_person": "psychological or personal",
            "ethics_and_values": "ethical or moral",
            "aesthetics_and_art": "artistic or aesthetic",
            "spirituality_and_meaning": "existential or spiritual",
            "practical_operations": "practical or operational",
        }

        labels = [readable.get(name, name) for name in names]

        if ambiguous and len(labels) >= 2:
            return (
                "I want to make sure I understand your request correctly. "
                f"Are you asking from a {labels[0]} perspective or a {labels[1]} perspective?"
            )

        if low_confidence and labels:
            joined = ", ".join(labels[:3])
            return (
                "I need a bit more context before answering well. "
                f"Is your question mainly {joined}, or something else?"
            )

        return (
            "I need a bit more context before answering. "
            "Could you clarify the domain or perspective of your request?"
        )

    @staticmethod
    def _default_profiles() -> List[ContextProfile]:
        return [
            ContextProfile(
                name="physical_reality",
                description="Scientific questions about the natural world, matter, energy, organisms, and observable processes.",
                reality_anchor="natural law and observable physical reality",
                semantic_anchors=[
                    "science",
                    "physical process",
                    "natural law",
                    "biological process",
                    "causal explanation",
                ],
                keywords=[
                    "physics", "chemistry", "biology", "astronomy", "gravity",
                    "atom", "cell", "energy", "matter", "evolution",
                    "planet", "star", "scientific", "natural", "organism",
                ],
                intent_markers=[
                    "why does", "how does", "what causes", "scientific explanation",
                    "physical explanation",
                ],
                negative_markers=[
                    "server", "boot", "configuration", "proof", "theorem",
                    "beauty", "painting", "faith",
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
                    "Are you asking about a physical process, biological process, or scientific explanation?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="physics",
                        description="Physical systems, forces, energy, motion, and matter.",
                        keywords=["physics", "force", "motion", "mass", "energy", "gravity"],
                        anchors=["physical law", "matter", "causality"],
                        intent_markers=["why does", "how does", "what happens"],
                    ),
                    SubcontextProfile(
                        name="biology",
                        description="Life, organisms, cells, evolution, and biological processes.",
                        keywords=["biology", "cell", "organism", "gene", "evolution", "anatomy"],
                        anchors=["living system", "biological process"],
                        intent_markers=["why do", "how do", "what causes"],
                    ),
                ],
            ),
            ContextProfile(
                name="formal_structure",
                description="Questions about mathematics, proof, logic, symbolic systems, and formal computation.",
                reality_anchor="logical consistency and formal validity",
                semantic_anchors=[
                    "formal system",
                    "logical validity",
                    "proof structure",
                    "symbolic derivation",
                    "mathematical reasoning",
                    "calculus",
                    "analytic proof",
                ],
                keywords=[
                    "math", "mathematics", "proof", "prove", "theorem",
                    "equation", "derivative", "integral", "logic",
                    "formula", "algebra", "calculus", "compute",
                    "differentiate", "derivation", "lemma", "symbolic",
                ],
                intent_markers=[
                    "how do i prove", "show that", "derive", "calculate", "solve", "prove a derivative", "prove this",
                ],
                negative_markers=[
                    "server", "emotion", "anxiety", "painting", "faith",
                    "boot", "network",
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
                    "Is this a mathematical, logical, or computational question?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="calculus",
                        description="Derivatives, integrals, limits, and continuous change.",
                        keywords=["derivative", "integral", "limit", "function", "calculus"],
                        anchors=["continuous change", "formal derivation"],
                        intent_markers=["prove", "derive", "calculate"],
                    ),
                    SubcontextProfile(
                        name="logic_and_proof",
                        description="Formal validity, proof methods, and symbolic reasoning.",
                        keywords=["proof", "logic", "theorem", "lemma", "proposition"],
                        anchors=["valid inference", "formal proof"],
                        intent_markers=["show that", "prove", "demonstrate"],
                    ),
                ],
            ),
            ContextProfile(
                name="technical_systems",
                description="Questions about software, infrastructure, systems, configuration, failures, and troubleshooting.",
                reality_anchor="functional system behavior and technical constraints",
                semantic_anchors=[
                    "system state",
                    "configuration consistency",
                    "functional diagnosis",
                    "error interpretation",
                ],
                keywords=[
                    "server", "boot", "network", "vm", "virtual machine",
                    "config", "configuration", "storage", "disk", "database",
                    "error", "bug", "issue", "system", "troubleshooting",
                    "docker", "proxmox", "vmware", "truenas",
                ],
                intent_markers=[
                    "how do i fix", "why is", "failing to", "not booting",
                    "diagnose", "recover", "configure",
                ],
                negative_markers=[
                    "beauty", "faith", "purpose", "meaning of life",
                    "painting", "ethics",
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
                    "Is this about diagnosis, configuration, recovery, or system design?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="infrastructure_and_servers",
                        description="Servers, virtualization, storage, networking, and operational infrastructure.",
                        keywords=["server", "boot", "vm", "storage", "hypervisor", "network"],
                        anchors=["system state", "infrastructure behavior"],
                        intent_markers=["failing", "recover", "configure", "fix"],
                    ),
                    SubcontextProfile(
                        name="software_and_debugging",
                        description="Software behavior, bugs, runtime issues, and debugging.",
                        keywords=["bug", "error", "crash", "code", "debug", "exception"],
                        anchors=["runtime behavior", "software state"],
                        intent_markers=["fix", "debug", "why is", "how do i"],
                    ),
                ],
            ),
            ContextProfile(
                name="history_and_society",
                description="Questions about historical events, society, institutions, politics, and collective processes.",
                reality_anchor="documented evidence and social reality",
                semantic_anchors=[
                    "historical evidence",
                    "social process",
                    "institutional structure",
                    "documented event",
                ],
                keywords=[
                    "history", "historical", "society", "social", "culture",
                    "politics", "government", "institution", "war", "revolution",
                    "document", "archive", "period", "civilization",
                ],
                intent_markers=[
                    "what happened", "why did", "how did", "historical context",
                ],
                negative_markers=[
                    "server", "derivative", "anxiety", "painting technique",
                    "soul", "faith",
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
                    "Are you asking about a historical event, a social issue, or an institutional matter?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="history",
                        description="Past events, periods, causes, and consequences.",
                        keywords=["history", "historical", "period", "event", "revolution"],
                        anchors=["documented event", "historical record"],
                        intent_markers=["what happened", "why did", "how did"],
                    ),
                    SubcontextProfile(
                        name="society_and_politics",
                        description="Institutions, politics, culture, and social dynamics.",
                        keywords=["society", "politics", "government", "institution", "culture"],
                        anchors=["social reality", "institutional process"],
                        intent_markers=["why does", "how does", "social issue"],
                    ),
                ],
            ),
            ContextProfile(
                name="psychology_and_person",
                description="Questions about emotion, behavior, cognition, distress, motivation, and personal experience.",
                reality_anchor="human experience and behavior",
                semantic_anchors=[
                    "inner state",
                    "human behavior",
                    "subjective experience",
                    "personal meaning",
                ],
                keywords=[
                    "anxiety", "emotion", "feel", "feeling", "mind", "sad",
                    "motivation", "behavior", "personality", "stress",
                    "fear", "depression", "thought", "psychology",
                ],
                intent_markers=[
                    "why do i feel", "why do people feel", "what am i feeling",
                    "why am i", "how do i deal with",
                ],
                negative_markers=[
                    "server", "derivative", "equation", "boot", "virtual machine",
                    "painting technique",
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
                    "Are you asking about emotion, behavior, mental state, or personal meaning?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="emotion_and_distress",
                        description="Emotional states, anxiety, sadness, fear, and distress.",
                        keywords=["anxiety", "stress", "fear", "sad", "emotion", "feel"],
                        anchors=["inner state", "subjective distress"],
                        intent_markers=["why do i feel", "why do people feel", "what am i feeling"],
                    ),
                    SubcontextProfile(
                        name="behavior_and_motivation",
                        description="Behavior, habits, decisions, and human motivation.",
                        keywords=["behavior", "motivation", "habit", "decision", "reaction"],
                        anchors=["human action", "behavioral pattern"],
                        intent_markers=["why do i", "why do people", "how can i"],
                    ),
                ],
            ),
            ContextProfile(
                name="ethics_and_values",
                description="Questions about what is right, responsible, fair, or morally justified.",
                reality_anchor="moral reasoning and human responsibility",
                semantic_anchors=[
                    "moral judgment",
                    "human responsibility",
                    "right action",
                    "value conflict",
                ],
                keywords=[
                    "ethics", "moral", "right", "wrong", "justice",
                    "fair", "responsibility", "duty", "should i",
                    "should we", "harm", "good", "evil",
                ],
                intent_markers=[
                    "is it wrong", "should i", "should we", "is it ethical",
                ],
                negative_markers=[
                    "server", "derivative", "boot", "database", "vmware",
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
                    "Is this mainly a moral question, a practical decision, or a personal dilemma?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="moral_decision",
                        description="Questions about what should be done or avoided.",
                        keywords=["should", "wrong", "ethical", "fair", "responsibility"],
                        anchors=["moral choice", "right action"],
                        intent_markers=["should i", "should we", "is it wrong"],
                    ),
                ],
            ),
            ContextProfile(
                name="aesthetics_and_art",
                description="Questions about beauty, art, style, expression, and interpretation.",
                reality_anchor="human aesthetic experience and symbolic expression",
                semantic_anchors=[
                    "aesthetic value",
                    "symbolic expression",
                    "artistic meaning",
                    "form and style",
                ],
                keywords=[
                    "art", "beauty", "beautiful", "painting", "music",
                    "literature", "poem", "film", "style", "design",
                    "aesthetic", "artist",
                ],
                intent_markers=[
                    "what makes", "why is this beautiful", "what does this mean",
                    "how should i interpret",
                ],
                negative_markers=[
                    "server", "boot", "derivative", "equation", "anxiety diagnosis",
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
                    "Are you asking about artistic meaning, artistic technique, or aesthetic value?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="artistic_interpretation",
                        description="Meaning, symbolism, beauty, and interpretation in art.",
                        keywords=["beauty", "beautiful", "meaning", "symbol", "interpret"],
                        anchors=["aesthetic value", "symbolic expression"],
                        intent_markers=["what makes", "what does this mean", "why is this beautiful"],
                    ),
                    SubcontextProfile(
                        name="artistic_technique",
                        description="Style, craft, execution, composition, and technique.",
                        keywords=["style", "technique", "composition", "design", "craft"],
                        anchors=["form", "artistic method"],
                        intent_markers=["how do i", "how is this made"],
                    ),
                ],
            ),
            ContextProfile(
                name="spirituality_and_meaning",
                description="Questions about purpose, meaning, faith, transcendence, and ultimate orientation.",
                reality_anchor="existential meaning and transcendent orientation",
                semantic_anchors=[
                    "existential meaning",
                    "ultimate purpose",
                    "spiritual reality",
                    "transcendent orientation",
                ],
                keywords=[
                    "meaning", "life", "purpose", "faith", "god",
                    "soul", "existence", "spiritual", "transcendence",
                    "why am i here", "meaning of life",
                ],
                intent_markers=[
                    "what is the meaning", "what is the purpose", "why am i here",
                    "spiritual meaning",
                ],
                negative_markers=[
                    "server", "boot", "derivative", "database", "error code",
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
                    "Are you asking about existential meaning, faith, or personal purpose?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="existential_question",
                        description="Questions about the meaning of life, existence, and ultimate purpose.",
                        keywords=["meaning of life", "purpose", "existence", "why am i here", "meaning"],
                        anchors=["existential meaning", "ultimate purpose"],
                        intent_markers=["what is the meaning", "what is the purpose"],
                    ),
                    SubcontextProfile(
                        name="faith_and_spirituality",
                        description="Questions about God, soul, faith, and spiritual life.",
                        keywords=["faith", "god", "soul", "spiritual", "prayer"],
                        anchors=["spiritual reality", "transcendent orientation"],
                        intent_markers=["what does faith mean", "spiritual meaning"],
                    ),
                ],
            ),
            ContextProfile(
                name="practical_operations",
                description="Questions asking what to do, how to proceed, how to organize action, or how to decide practically.",
                reality_anchor="practical constraints and decision execution",
                semantic_anchors=[
                    "practical action",
                    "goal-oriented execution",
                    "decision procedure",
                    "operational sequence",
                ],
                keywords=[
                    "how do i", "steps", "procedure", "plan", "workflow",
                    "do this", "organize", "execute", "what should i do",
                    "decision", "option", "next step",
                ],
                intent_markers=[
                    "how do i", "what should i do", "what are the steps", "help me decide",
                    "how can i proceed", "step by step",
                ],
                negative_markers=[
                    "theorem", "derivative", "integral", "equation", "proof",
                    "logic", "calculus", "formula", "painting symbolism", "faith in god",
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
                    "Are you asking for a plan, a step-by-step procedure, or help deciding between options?"
                ],
                subcontexts=[
                    SubcontextProfile(
                        name="procedure",
                        description="Step-by-step action, workflow, and execution.",
                        keywords=["steps", "procedure", "workflow", "do this", "execute"],
                        anchors=["operational sequence", "practical action"],
                        intent_markers=["how do i", "what are the steps"],
                    ),
                    SubcontextProfile(
                        name="decision_support",
                        description="Choosing between options or deciding what to do next.",
                        keywords=["decide", "option", "choice", "should i", "next step"],
                        anchors=["decision procedure", "goal-oriented action"],
                        intent_markers=["what should i do", "help me decide"],
                    ),
                ],
            ),
        ]