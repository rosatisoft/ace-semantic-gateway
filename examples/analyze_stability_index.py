import csv
from pathlib import Path
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_PATH = BASE_DIR / "dataset" / "ace_runtime_benchmark_results_v1.csv"


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def stability_index(row):
    best_cost = to_float(row["best_cost"])
    margin = to_float(row["field_margin"])
    density = to_float(row.get("best_density"))

    if best_cost <= 0:
        return 0.0

    return (margin * density) / best_cost


def main():
    with RESULTS_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row["stability_index"] = stability_index(row)

    print("=" * 100)
    print("ACE STABILITY INDEX ANALYSIS")
    print("=" * 100)

    by_label = defaultdict(list)

    for row in rows:
        by_label[row["label"]].append(row)

    print("\nCATEGORY AVERAGES")
    print("-" * 100)

    for label, items in sorted(by_label.items()):
        avg_cost = sum(to_float(r["best_cost"]) for r in items) / len(items)
        avg_margin = sum(to_float(r["field_margin"]) for r in items) / len(items)
        avg_density = sum(to_float(r.get("best_density")) for r in items) / len(items)
        avg_stability = sum(r["stability_index"] for r in items) / len(items)

        print(
            label,
            "count=", len(items),
            "avg_cost=", round(avg_cost, 4),
            "avg_margin=", round(avg_margin, 4),
            "avg_density=", round(avg_density, 4),
            "avg_stability=", round(avg_stability, 6),
        )

    print("\nLOWEST STABILITY CASES")
    print("-" * 100)

    for row in sorted(rows, key=lambda r: r["stability_index"])[:25]:
        print(
            row["id"],
            "|", row["label"],
            "| stability=", round(row["stability_index"], 6),
            "| cost=", round(to_float(row["best_cost"]), 4),
            "| margin=", round(to_float(row["field_margin"]), 4),
            "| density=", round(to_float(row.get("best_density")), 4),
            "|", row["text"],
        )

    print("\nHIGHEST STABILITY CASES")
    print("-" * 100)

    for row in sorted(rows, key=lambda r: r["stability_index"], reverse=True)[:25]:
        print(
            row["id"],
            "|", row["label"],
            "| stability=", round(row["stability_index"], 6),
            "| cost=", round(to_float(row["best_cost"]), 4),
            "| margin=", round(to_float(row["field_margin"]), 4),
            "| density=", round(to_float(row.get("best_density")), 4),
            "|", row["text"],
        )


if __name__ == "__main__":
    main()