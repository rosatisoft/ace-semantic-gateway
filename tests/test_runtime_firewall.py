from gateway.runtime_firewall import SemanticRuntimeFirewall


def test_runtime_firewall_routes_clear_operational():
    fw = SemanticRuntimeFirewall()

    result = fw.analyze(
        costs={
            "conceptual": 0.85,
            "operational": 0.25,
            "narrative": 0.87,
        },
        coherence_risk=0.10,
    )

    assert result.decision == "ROUTE_OPERATIONAL"
    assert result.processing_mode == "full"
    assert result.route == "operational"


def test_runtime_firewall_routes_clear_narrative():
    fw = SemanticRuntimeFirewall()

    result = fw.analyze(
        costs={
            "conceptual": 0.83,
            "operational": 0.82,
            "narrative": 0.26,
        },
        coherence_risk=0.10,
    )

    assert result.decision == "ROUTE_NARRATIVE"
    assert result.processing_mode == "full"
    assert result.route == "narrative"


def test_runtime_firewall_detects_low_margin_ambiguity():
    fw = SemanticRuntimeFirewall()

    result = fw.analyze(
        costs={
            "conceptual": 0.70,
            "operational": 0.67,
            "narrative": 0.68,
        },
        coherence_risk=0.10,
    )

    assert result.decision == "LOW_MARGIN_AMBIGUOUS"
    assert result.processing_mode == "light"


def test_runtime_firewall_detects_contradiction_risk():
    fw = SemanticRuntimeFirewall()

    result = fw.analyze(
        costs={
            "conceptual": 0.30,
            "operational": 0.75,
            "narrative": 0.80,
        },
        coherence_risk=0.70,
    )

    assert result.decision == "CONTRADICTION_RISK"
    assert result.processing_mode == "short"