from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class FieldCompetitionResult:
    best_field: str
    best_cost: float
    second_field: str
    second_cost: float
    field_margin: float
    costs: Dict[str, float]


def analyze_field_competition(costs: Dict[str, float]) -> FieldCompetitionResult:
    """
    Analyze competition between semantic fields.

    The key criterion is not absolute cost alone, but:
    - which field wins
    - how low the winning cost is
    - how clearly it wins over the second-best field
    """

    if not costs:
        raise ValueError("costs cannot be empty")

    if len(costs) < 2:
        raise ValueError("at least two fields are required for competition")

    sorted_costs: Tuple[Tuple[str, float], ...] = tuple(
        sorted(costs.items(), key=lambda item: item[1])
    )

    best_field, best_cost = sorted_costs[0]
    second_field, second_cost = sorted_costs[1]

    return FieldCompetitionResult(
        best_field=best_field,
        best_cost=float(best_cost),
        second_field=second_field,
        second_cost=float(second_cost),
        field_margin=float(second_cost - best_cost),
        costs=dict(costs),
    )