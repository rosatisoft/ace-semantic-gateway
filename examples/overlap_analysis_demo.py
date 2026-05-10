import json
from pathlib import Path

from gateway.embedding_router import EmbeddingRouter
from gateway.runtime_firewall import SemanticRuntimeFirewall


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = BASE_DIR / "dataset" / "semantic_overlap_dataset_v1.json"

def main():
    router = EmbeddingRouter()
    firewall = SemanticRuntimeFirewall()

    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    print("=" * 100)
    print("ACE SEMANTIC OVERLAP ANALYSIS")
    print("=" * 100)

    for item in data:
        text = item["text"]

        semantic_profile = router.analyze_text(text)

        result = firewall.analyze(
            costs=semantic_profile.costs,
            coherence_risk=semantic_profile.coherence_risk,
        )

        print("-" * 100)
        print("TEXT:", text)
        print("CATEGORY:", item["category"])
        print("EXPECTED:", item["expected_primary"], "/", item["expected_secondary"])
        print("DECISION:", result.decision)
        print("MODE:", result.processing_mode)
        print("BEST:", result.best_field, round(result.best_cost, 4))
        print("SECOND:", result.second_field, round(result.second_cost, 4))
        print("MARGIN:", round(result.field_margin, 4))
        print("COHERENCE:", round(result.coherence_risk, 4))
        print("COSTS:", {k: round(v, 4) for k, v in result.costs.items()})


if __name__ == "__main__":
    main()