from gateway.context_matrix import ContextMatrix


def test_meaning_of_life_maps_to_spirituality():
    cm = ContextMatrix()
    result = cm.match_context("What is the meaning of life?")

    assert result.best_context is not None
    assert result.best_context.name == "spirituality_and_meaning"
    assert result.best_subcontext == "existential_question"
    assert result.needs_clarification is False


def test_server_boot_maps_to_technical_systems():
    cm = ContextMatrix()
    result = cm.match_context(
        "Why is my server failing to boot after changing the storage controller?"
    )

    assert result.best_context is not None
    assert result.best_context.name == "technical_systems"
    assert result.best_subcontext == "infrastructure_and_servers"
    assert result.needs_clarification is False


def test_anxiety_maps_to_psychology():
    cm = ContextMatrix()
    result = cm.match_context("Why do people feel anxiety?")

    assert result.best_context is not None
    assert result.best_context.name == "psychology_and_person"
    assert result.best_subcontext == "emotion_and_distress"
    assert result.needs_clarification is False


def test_painting_beauty_maps_to_aesthetics():
    cm = ContextMatrix()
    result = cm.match_context("What makes a painting beautiful?")

    assert result.best_context is not None
    assert result.best_context.name == "aesthetics_and_art"
    assert result.best_subcontext == "artistic_interpretation"
    assert result.needs_clarification is False


def test_truth_hurts_maps_to_ethics():
    cm = ContextMatrix()
    result = cm.match_context("Should I tell the truth if it will hurt someone?")

    assert result.best_context is not None
    assert result.best_context.name == "ethics_and_values"
    assert result.best_subcontext == "moral_decision"
    assert result.needs_clarification is False


def test_derivative_prefers_formal_structure():
    cm = ContextMatrix()
    result = cm.match_context("How do I prove a derivative?")

    assert result.best_context is not None
    assert result.best_context.name == "formal_structure"
    assert result.best_subcontext in {"calculus", "logic_and_proof"}