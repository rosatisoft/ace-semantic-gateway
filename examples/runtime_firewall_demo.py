from gateway.runtime_firewall import SemanticRuntimeFirewall


def print_result(title, result):
    print("=" * 60)
    print(title)
    print("=" * 60)

    print("decision:", result.decision)
    print("processing_mode:", result.processing_mode)
    print("route:", result.route)
    print("confidence:", result.confidence)

    print("best_field:", result.best_field)
    print("best_cost:", round(result.best_cost, 4))

    print("second_field:", result.second_field)
    print("field_margin:", round(result.field_margin, 4))

    print("coherence_risk:", round(result.coherence_risk, 4))
    print()


fw = SemanticRuntimeFirewall()


# ============================================================
# FACTUAL
# ============================================================

factual = fw.analyze(
    costs={
        "conceptual": 0.82,
        "operational": 0.24,
        "narrative": 0.88,
    },
    coherence_risk=0.08,
)

print_result("FACTUAL INPUT", factual)


# ============================================================
# CONCEPTUAL
# ============================================================

conceptual = fw.analyze(
    costs={
        "conceptual": 0.18,
        "operational": 0.71,
        "narrative": 0.80,
    },
    coherence_risk=0.12,
)

print_result("CONCEPTUAL INPUT", conceptual)


# ============================================================
# NARRATIVE
# ============================================================

narrative = fw.analyze(
    costs={
        "conceptual": 0.78,
        "operational": 0.83,
        "narrative": 0.22,
    },
    coherence_risk=0.10,
)

print_result("NARRATIVE INPUT", narrative)


# ============================================================
# AMBIGUOUS
# ============================================================

ambiguous = fw.analyze(
    costs={
        "conceptual": 0.68,
        "operational": 0.70,
        "narrative": 0.72,
    },
    coherence_risk=0.20,
)

print_result("AMBIGUOUS INPUT", ambiguous)


# ============================================================
# CONTRADICTION
# ============================================================

contradiction = fw.analyze(
    costs={
        "conceptual": 0.28,
        "operational": 0.74,
        "narrative": 0.81,
    },
    coherence_risk=0.72,
)

print_result("CONTRADICTION INPUT", contradiction)