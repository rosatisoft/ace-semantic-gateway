import csv
import json
from pathlib import Path

from gateway.embedding_router import EmbeddingRouter
from gateway.runtime_firewall import SemanticRuntimeFirewall


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "dataset" / "ace_semantic_stability_benchmark_v1.json"
OUTPUT_PATH = BASE_DIR / "dataset" / "ace_runtime_benchmark_results_v1.csv"


def main():
    router = EmbeddingRouter()
    firewall = SemanticRuntimeFirewall()

    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    rows = []

    for item in data:
        profile = router.analyze_text(item["text"])

        result = firewall.analyze(
            costs=profile.costs,
            coherence_risk=profile.coherence_risk,
        )

        rows.append({
            "id": item["id"],
            "text": item["text"],
            "label": item["label"],
            "expected_primary": item["expected_primary"],
            "expected_secondary": item["expected_secondary"],
            "expected_mode": item["expected_mode"],
            "stability": item["stability"],
            "risk_level": item["risk_level"],
            "decision": result.decision,
            "processing_mode": result.processing_mode,
            "route": result.route,
            "best_field": result.best_field,
            "best_cost": result.best_cost,
            "second_field": result.second_field,
            "second_cost": result.second_cost,
            "field_margin": result.field_margin,
            "coherence_risk": result.coherence_risk,
            "conceptual_cost": result.costs.get("conceptual"),
            "operational_cost": result.costs.get("operational"),
            "narrative_cost": result.costs.get("narrative"),
            "conceptual_density": profile.densities.get("conceptual"),
            "operational_density": profile.densities.get("operational"),
            "narrative_density": profile.densities.get("narrative"),
            "best_density": profile.densities.get(result.best_field),
        })

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("=" * 80)
    print("ACE Runtime Benchmark")
    print("=" * 80)
    print("Dataset:", DATASET_PATH)
    print("Examples:", len(rows))
    print("Output:", OUTPUT_PATH)
    print()

    print("Processing modes:")
    counts = {}
    for row in rows:
        counts[row["processing_mode"]] = counts.get(row["processing_mode"], 0) + 1
    print(counts)

    print()
    print("Decisions:")
    decisions = {}
    for row in rows:
        decisions[row["decision"]] = decisions.get(row["decision"], 0) + 1
    print(decisions)


if __name__ == "__main__":
    main()