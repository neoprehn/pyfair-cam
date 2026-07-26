"""
End-to-End-Test: vollständiges Ransomware-Szenario durch to_pyfair() (Phase 3).

Baut dasselbe Szenario wie examples/ransomware_scenario.py nach (Resistive
Control auf der Frequenz-Seite + stage-gated Detection/Response-Kill-Chain
auf der Loss-Magnitude-Seite) und rechnet es über
``FairCamModel.to_pyfair(mode="vuln")`` durch ein natives pyfair-Modell.

``pyfair`` ist eine optionale Abhängigkeit – dieser Test wird übersprungen,
wenn es nicht installiert ist.
"""

import numpy as np
import pytest

from pyfair_cam import (
    BetaPert,
    DetectionResponseFactor,
    FairCamModel,
    Poisson,
    ResistiveControl,
    Stage,
)

pytest.importorskip("pyfair")

N = 3_000


def build_ransomware_model():
    stages = [
        Stage(
            name="Initial Access", coverage=0.95, visibility=0.70, vis_reliability=0.95,
            recognition=0.40, rec_reliability=0.90, monitoring_cadence=0.042,
            mon_reliability=0.95, duration=0.25, progression_probability=0.90,
            review_independence=0.40,
        ),
        Stage(
            name="Persistence", coverage=0.98, visibility=0.85, vis_reliability=0.95,
            recognition=0.60, rec_reliability=0.92, monitoring_cadence=0.042,
            mon_reliability=0.95, duration=0.50, progression_probability=0.85,
            review_independence=0.55,
        ),
        Stage(
            name="Priv Escalation", coverage=0.96, visibility=0.80, vis_reliability=0.94,
            recognition=0.75, rec_reliability=0.90, monitoring_cadence=0.042,
            mon_reliability=0.94, duration=0.50, progression_probability=0.80,
            review_independence=0.60,
        ),
        Stage(
            name="Lateral Movement", coverage=0.92, visibility=0.90, vis_reliability=0.96,
            recognition=0.65, rec_reliability=0.88, monitoring_cadence=0.042,
            mon_reliability=0.92, duration=1.00, progression_probability=0.75,
            review_independence=0.65,
        ),
        Stage(
            name="Data Staging", coverage=0.88, visibility=0.75, vis_reliability=0.92,
            recognition=0.55, rec_reliability=0.85, monitoring_cadence=0.042,
            mon_reliability=0.90, duration=0.75, progression_probability=0.70,
            review_independence=0.50,
        ),
        Stage(
            name="Execution", coverage=0.85, visibility=0.60, vis_reliability=0.90,
            recognition=0.45, rec_reliability=0.80, monitoring_cadence=0.042,
            mon_reliability=0.88, duration=0.25, progression_probability=0.95,
            review_independence=0.45,
        ),
    ]
    stage_outcome_map = {1: "early", 2: "early", 3: "mid", 4: "mid", 5: "late", 6: "late"}
    loss_distributions = {
        "early": BetaPert(low=2_000, mode=8_000, high=30_000),
        "mid": BetaPert(low=25_000, mode=75_000, high=250_000),
        "late": BetaPert(low=200_000, mode=500_000, high=2_000_000),
        DetectionResponseFactor.FULL_IMPACT: BetaPert(low=1_000_000, mode=3_000_000, high=5_000_000),
        DetectionResponseFactor.ATTACKER_FAILS: BetaPert(low=2_000, mode=5_000, high=15_000),
    }
    detection_response = DetectionResponseFactor(
        name="Ransomware Kill-Chain",
        stages=stages,
        stage_outcome_map=stage_outcome_map,
        loss_distributions=loss_distributions,
        t_containment=BetaPert(low=1, mode=3, high=10),
        t_resilience=BetaPert(low=2, mode=7, high=21),
        concurrency=BetaPert(low=0.2, mode=0.4, high=0.6),
    )

    model = FairCamModel(name="Ransomware Szenario (E2E)", n_simulations=N)
    model.input_threat_frequency(BetaPert(low=5, mode=10, high=20))
    model.add_resistive_control(
        ResistiveControl(
            name="EDR / Anti-Malware",
            intended_efficacy=BetaPert(low=0.70, mode=0.85, high=0.95),
            variant_efficacy=BetaPert(low=0.02, mode=0.10, high=0.25),
            variance_frequency=Poisson(lam=4, range_=0.4),
            variance_duration=BetaPert(low=2, mode=5, high=10),
            coverage=BetaPert(low=0.85, mode=0.95, high=0.99),
        )
    )
    model.set_detection_response(detection_response)
    return model


def test_ransomware_scenario_end_to_end_via_pyfair():
    model = build_ransomware_model()
    fair_model, cam_result = model.to_pyfair(mode="vuln", random_seed=42)

    # Control wirkt tatsächlich (Susceptibility zwischen 0 und 1, nicht an
    # den Rändern hängend).
    assert 0.0 < np.mean(cam_result["susceptibility"]) < 1.0

    # pyfair-Risk stimmt exakt mit dem CAM-Risk überein (Pfad A liefert per
    # Definition dieselben Zahlen, siehe test_adapter.py) - hier zusätzlich
    # für ein volles Szenario mit Detection/Response statt flacher LM geprüft.
    pyfair_risk = fair_model.export_results()["Risk"].to_numpy()
    np.testing.assert_allclose(pyfair_risk, cam_result["risk"])
    assert np.all(pyfair_risk >= 0)
    assert np.mean(pyfair_risk) > 0

    # Outcome-Klassen (Datengrundlage für die spätere Parallel-Anzeige,
    # siehe ROADMAP.md "Rechenprinzip LM-Seite") sind vollständig und
    # plausibel über mehrere Klassen verteilt, nicht in einer Klasse geklumpt.
    outcome_class = cam_result["outcome_class"]
    assert len(outcome_class) == N
    expected_classes = {
        "early", "mid", "late",
        DetectionResponseFactor.FULL_IMPACT,
        DetectionResponseFactor.ATTACKER_FAILS,
    }
    seen_classes = set(np.unique(outcome_class))
    assert seen_classes <= expected_classes
    assert len(seen_classes) > 1

    assert "detected_at_stage" in cam_result
    assert len(cam_result["detected_at_stage"]) == N
