import pytest

from gateway.field_competition import analyze_field_competition


def test_field_competition_detects_best_field():
    result = analyze_field_competition(
        {
            "conceptual": 0.80,
            "operational": 0.25,
            "narrative": 0.70,
        }
    )

    assert result.best_field == "operational"
    assert result.best_cost == pytest.approx(0.25)
    assert result.second_field == "narrative"
    assert result.field_margin == pytest.approx(0.45)


def test_field_competition_requires_two_fields():
    with pytest.raises(ValueError):
        analyze_field_competition({"conceptual": 0.20})


def test_field_competition_rejects_empty_costs():
    with pytest.raises(ValueError):
        analyze_field_competition({})