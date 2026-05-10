import csv
from pathlib import Path
from collections import Counter, defaultdict


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_PATH = BASE_DIR / "dataset" / "ace_runtime_benchmark_results_v1.csv"


def load_rows():
    with RESULTS_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def density_summary(row):
    return {
        "conceptual": round(to_float(row.get("conceptual_density")) or 0.0, 4),
        "operational": round(to_float(row.get("operational_density")) or 0.0, 4),
        "narrative": round(to_float(row.get("narrative_density")) or 0.0, 4),
    }


def main():
    rows = load_rows()

    ambiguous = [
        row for row in rows
        if row["decision"] == "LOW_MARGIN_AMBIGUOUS"
    ]

    print("=" * 100)
    print("ACE LOW MARGIN AMBIGUITY ANALYSIS")
    print("=" * 100)
    print("Total rows:", len(rows))
    print("LOW_MARGIN_AMBIGUOUS:", len(ambiguous))
    print()

    print("By label:")
    print(dict(Counter(row["label"] for row in ambiguous)))
    print()

    print("Best field distribution:")
    print(dict(Counter(row["best_field"] for row in ambiguous)))
    print()

    print("Second field distribution:")
    print(dict(Counter(row["second_field"] for row in ambiguous)))
    print()

    print("Best / second pairs:")
    pairs = Counter(
        (row["best_field"], row["second_field"])
        for row in ambiguous
    )
    for pair, count in pairs.most_common():
        print(pair, count)

    print()
    print("=" * 100)
    print("LOWEST MARGINS")
    print("=" * 100)

    ambiguous_sorted = sorted(
        ambiguous,
        key=lambda row: to_float(row["field_margin"]) or 0.0
    )

    for row in ambiguous_sorted[:30]:
        print("-" * 100)
        print("ID:", row["id"])
        print("LABEL:", row["label"])
        print("TEXT:", row["text"])
        print("EXPECTED:", row["expected_primary"], "/", row["expected_secondary"])
        print("BEST:", row["best_field"], round(to_float(row["best_cost"]) or 0.0, 4))
        print("SECOND:", row["second_field"], round(to_float(row["second_cost"]) or 0.0, 4))
        print("MARGIN:", round(to_float(row["field_margin"]) or 0.0, 4))
        print("COSTS:",
              {
                  "conceptual": round(to_float(row["conceptual_cost"]) or 0.0, 4),
                  "operational": round(to_float(row["operational_cost"]) or 0.0, 4),
                  "narrative": round(to_float(row["narrative_cost"]) or 0.0, 4),
              })

        print("DENSITIES:", density_summary(row))

        print("BEST_DENSITY:",
              round(to_float(row.get("best_density")) or 0.0, 4))

    print()
    print("=" * 100)
    print("CATEGORY AVERAGES")
    print("=" * 100)

    by_label = defaultdict(list)
    density_by_label = defaultdict(list)

    for row in ambiguous:
        margin = to_float(row["field_margin"])
        best_cost = to_float(row["best_cost"])

        best_density = to_float(row.get("best_density"))

        if margin is not None and best_cost is not None:
            by_label[row["label"]].append((margin, best_cost))

        if best_density is not None:
            density_by_label[row["label"]].append(best_density)

    for label, values in sorted(by_label.items()):
        avg_margin = sum(v[0] for v in values) / len(values)
        avg_best_cost = sum(v[1] for v in values) / len(values)

        avg_density = 0.0

        if density_by_label[label]:
            avg_density = (
                sum(density_by_label[label]) /
                len(density_by_label[label])
            )

        print(
            label,
            "count=", len(values),
            "avg_margin=", round(avg_margin, 4),
            "avg_best_cost=", round(avg_best_cost, 4),
            "avg_density=", round(avg_density, 4),
        )


if __name__ == "__main__":
    main()