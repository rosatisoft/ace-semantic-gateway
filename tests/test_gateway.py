import pytest

from gateway import SemanticGateway


def test_fast_path_answer():
    gw = SemanticGateway(ace_threshold=1.0, deep_threshold=2.0)
    result = gw.process_request(
        prompt="Hello world",
        axioms=["preserve consistency"],
        knowledge=["semantic control"],
    )
    assert result.decision == "answer"
    assert result.path == "fast"


def test_deep_path_clarify():
    gw = SemanticGateway(ace_threshold=0.0, deep_threshold=1.0)
    result = gw.process_request(
        prompt="Explain a contradiction in semantic identity",
        axioms=["preserve consistency"],
        knowledge=["semantic control"],
    )
    assert result.decision == "clarify"
    assert result.path == "deep"


def test_abstain_when_thresholds_are_tight():
    gw = SemanticGateway(ace_threshold=0.0, deep_threshold=0.0)
    result = gw.process_request(
        prompt="This request contains conflicting semantic signals",
        axioms=["a1"],
        knowledge=["k1"],
    )
    assert result.decision == "abstain"
    assert result.path == "blocked"


def test_invalid_threshold_order_raises():
    with pytest.raises(ValueError):
        SemanticGateway(ace_threshold=0.70, deep_threshold=0.40)