ContextProfile(
    name="psychology",
    description="Questions about emotion, cognition, behavior, and personal experience",
    reality_anchor="human behavior and lived experience",
    semantic_anchors=[
        "emotion",
        "motivation",
        "behavior",
        "mental state",
    ],
    default_axioms=[
        "preserve interpretive caution",
        "avoid unsupported diagnosis",
    ],
    default_knowledge=[
        "subjective experience",
        "behavioral context",
    ],
    clarification_prompts=[
        "Are you asking about emotion, behavior, or meaning?",
        "Is this about a personal experience or a general explanation?",
    ],
)
