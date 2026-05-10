from gateway.embedding_router import EmbeddingRouter


def test_embedding_router_routes_operational_signal():
    router = EmbeddingRouter()

    profile = router.analyze_text("Paris is the capital of France.")

    assert profile.costs["operational"] < profile.costs["conceptual"]
    assert profile.costs["operational"] < profile.costs["narrative"]


def test_embedding_router_routes_narrative_signal():
    router = EmbeddingRouter()

    profile = router.analyze_text("The dragon guarded the ancient kingdom.")

    assert profile.costs["narrative"] < profile.costs["conceptual"]
    assert profile.costs["narrative"] < profile.costs["operational"]


def test_embedding_router_routes_conceptual_signal():
    router = EmbeddingRouter()

    profile = router.analyze_text("Meaning depends on context.")

    assert profile.costs["conceptual"] < profile.costs["operational"]
    assert profile.costs["conceptual"] < profile.costs["narrative"]


def test_embedding_router_detects_coherence_risk():
    router = EmbeddingRouter()

    profile = router.analyze_text("Truth is true and false at the same time.")

    assert profile.coherence_risk > 0.5