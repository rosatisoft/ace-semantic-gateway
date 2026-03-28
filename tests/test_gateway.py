from gateway import SemanticGateway


def test_fast_path_answer():
    gw = SemanticGateway(ace_threshold=0.35, deep_threshold=0.65)
    result = gw.process_request(
        prompt="Hello world",
        axioms=[],
        knowledge=[],
    )
    assert result.decision == "answer"
    assert result.path == "fast"


def test_deep_path_clarify():
    gw = SemanticGateway(ace_threshold=0.05, deep_threshold=0.30)
    result = gw.process_request(
        prompt="Explain a highly ambiguous philosophical contradiction in detail",
        axioms=["preserve consistency"],
        knowledge=["semantic control"],
    )
    assert result.decision == "clarify"
    assert result.path == "deep"


def test_abstain_when_instability_is_high():
    gw = SemanticGateway(ace_threshold=0.01, deep_threshold=0.02)
    result = gw.process_request(
        prompt="This is a very long unstable request full of conflicting semantic signals",
        axioms=["a1", "a2", "a3"],
        knowledge=["k1", "k2", "k3"],
    )
    assert result.decision == "abstain"
    assert result.path == "blocked"
