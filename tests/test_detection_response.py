"""
Tests für Stage / DetectionResponseFactor (Detection & Response, Phase 2).
"""

import numpy as np
import pytest

from pyfair_cam import (
    BetaPert,
    Constant,
    DetectionResponseFactor,
    Stage,
    effective_parameter,
    reviews_per_stage,
    stage_detection_probability,
)

# KB-Stage-1-Zeile (04_Detection_Response_Measurement.md), alles PointEstimate
# (Skalare) -> deterministisch, damit dieser Test die Stage-Klassen-Verdrahtung
# prüft, nicht Zufall.
STAGE_1_KWARGS = dict(
    name="Initial Access",
    coverage=0.95,
    visibility=0.70,
    vis_reliability=0.95,
    recognition=0.40,
    rec_reliability=0.90,
    monitoring_cadence=0.042,
    mon_reliability=0.95,
    duration=0.25,
    progression_probability=0.90,
    review_independence=0.40,
)


def test_stage_detection_probability_matches_core():
    stage = Stage(**STAGE_1_KWARGS)
    rng = np.random.default_rng(1)
    n = 500
    p_detect, params = stage.detection_probability(n, rng)

    # PointEstimate-Parameter -> jeder Trial liefert denselben Wert
    assert np.all(p_detect == p_detect[0])

    v_eff = effective_parameter(STAGE_1_KWARGS["visibility"], STAGE_1_KWARGS["vis_reliability"])
    r_eff = effective_parameter(STAGE_1_KWARGS["recognition"], STAGE_1_KWARGS["rec_reliability"])
    lam = reviews_per_stage(
        STAGE_1_KWARGS["duration"], STAGE_1_KWARGS["monitoring_cadence"], STAGE_1_KWARGS["mon_reliability"]
    )
    expected = stage_detection_probability(
        STAGE_1_KWARGS["coverage"], v_eff, r_eff, STAGE_1_KWARGS["review_independence"], lam
    )
    assert float(p_detect[0]) == pytest.approx(float(expected), rel=1e-9)


def test_stage_sample_returns_all_ten_parameters():
    stage = Stage(**STAGE_1_KWARGS)
    rng = np.random.default_rng(2)
    params = stage.sample(100, rng)
    expected_keys = {
        "coverage", "visibility", "vis_reliability", "recognition", "rec_reliability",
        "monitoring_cadence", "mon_reliability", "duration", "progression_probability",
        "review_independence",
    }
    assert set(params.keys()) == expected_keys
    for key, values in params.items():
        assert values.shape == (100,)


# ---------------------------------------------------------------------------
# DetectionResponseFactor – vollständiges 6-Stufen-Ransomware-Szenario aus
# 04_Detection_Response_Measurement.md. Ground Truth (unabhängig nachgerechnet,
# siehe test_core.py-Kommentar zu den Stage-1/6-Abweichungen der KB selbst):
#   Early=82.49%  Mid=8.80%  Late=0.230%  Full Impact=0.062%  Attacker Fails=8.41%
# KB-Kopfzahlen (grobe Plausibilität): 81.8 / 8.97 / 0.24 / 0.065 / 8.9 %
# ---------------------------------------------------------------------------

KB_STAGE_PARAMS = [
    # name, cov, v, rel_v, r, rel_r, m, rel_m, tau, p, rho
    ("Initial Access", 0.95, 0.70, 0.95, 0.40, 0.90, 0.042, 0.95, 0.25, 0.90, 0.40),
    ("Persistence", 0.98, 0.85, 0.95, 0.60, 0.92, 0.042, 0.95, 0.50, 0.85, 0.55),
    ("Priv Escalation", 0.96, 0.80, 0.94, 0.75, 0.90, 0.042, 0.94, 0.50, 0.80, 0.60),
    ("Lateral Movement", 0.92, 0.90, 0.96, 0.65, 0.88, 0.042, 0.92, 1.00, 0.75, 0.65),
    ("Data Staging", 0.88, 0.75, 0.92, 0.55, 0.85, 0.042, 0.90, 0.75, 0.70, 0.50),
    ("Execution", 0.85, 0.60, 0.90, 0.45, 0.80, 0.042, 0.88, 0.25, 0.95, 0.45),
]

# Stufen 1-2 -> early, 3-4 -> mid, 5-6 -> late (vgl. KB "Outcome Class Summary")
KB_STAGE_OUTCOME_MAP = {1: "early", 2: "early", 3: "mid", 4: "mid", 5: "late", 6: "late"}

KB_LOSS_DISTRIBUTIONS = {
    "early": BetaPert(low=2_000, mode=8_000, high=30_000),
    "mid": BetaPert(low=25_000, mode=75_000, high=250_000),
    "late": BetaPert(low=200_000, mode=500_000, high=2_000_000),
    DetectionResponseFactor.FULL_IMPACT: BetaPert(low=1_000_000, mode=3_000_000, high=5_000_000),
    DetectionResponseFactor.ATTACKER_FAILS: BetaPert(low=2_000, mode=5_000, high=15_000),
}

EXPECTED_OUTCOME_PROBS = {
    "early": 0.8249,
    "mid": 0.0880,
    "late": 0.00230,
    DetectionResponseFactor.FULL_IMPACT: 0.00062,
    DetectionResponseFactor.ATTACKER_FAILS: 0.08415,
}


def build_kb_scenario(loss_distributions=None):
    stages = [
        Stage(
            name=name, coverage=cov, visibility=v, vis_reliability=rel_v,
            recognition=r, rec_reliability=rel_r, monitoring_cadence=m,
            mon_reliability=rel_m, duration=tau, progression_probability=p,
            review_independence=rho,
        )
        for (name, cov, v, rel_v, r, rel_r, m, rel_m, tau, p, rho) in KB_STAGE_PARAMS
    ]
    return DetectionResponseFactor(
        name="Ransomware Szenario",
        stages=stages,
        stage_outcome_map=KB_STAGE_OUTCOME_MAP,
        loss_distributions=loss_distributions or KB_LOSS_DISTRIBUTIONS,
    )


def test_full_ransomware_scenario_outcome_classes():
    factor = build_kb_scenario()
    n = 200_000
    rng = np.random.default_rng(42)
    result = factor.simulate(n, rng)

    counts = {cls: np.mean(result["outcome_class"] == cls) for cls in EXPECTED_OUTCOME_PROBS}

    # Enger Check gegen die selbst nachgerechneten Werte
    for cls, expected in EXPECTED_OUTCOME_PROBS.items():
        assert counts[cls] == pytest.approx(expected, abs=0.005), cls

    # Lockere Plausibilitätsprüfung gegen die KB-Kopfzahlen (siehe Modul-Docstring:
    # KB reproduziert Stage 1/6 nicht exakt aus ihrer eigenen Formel, daher nur
    # als grober Sanity-Check, nicht als exakter Test)
    kb_headline = {"early": 0.818, "mid": 0.0897, "late": 0.0024,
                   DetectionResponseFactor.FULL_IMPACT: 0.00065,
                   DetectionResponseFactor.ATTACKER_FAILS: 0.089}
    for cls, expected in kb_headline.items():
        assert counts[cls] == pytest.approx(expected, abs=0.015), cls


def test_loss_magnitude_mean_matches_kb_expected_loss():
    factor = build_kb_scenario()
    n = 200_000
    rng = np.random.default_rng(7)
    result = factor.simulate(n, rng)
    # KB: E[Loss_gross] = $21,501 (aus KB-eigenen Klassenwahrscheinlichkeiten);
    # unsere nachgerechnete Kaskade ergibt ~$21,232 (siehe test_core.py) ->
    # großzügige Toleranz, MC-Rauschen + kleine Wahrscheinlichkeitsverschiebung.
    assert result["loss_magnitude"].mean() == pytest.approx(21_500, rel=0.1)


def test_seed_reproducibility_detection_response():
    factor1 = build_kb_scenario()
    factor2 = build_kb_scenario()
    r1 = factor1.simulate(5_000, np.random.default_rng(99))
    r2 = factor2.simulate(5_000, np.random.default_rng(99))
    np.testing.assert_array_equal(r1["outcome_class"], r2["outcome_class"])
    np.testing.assert_array_equal(r1["detected_at_stage"], r2["detected_at_stage"])
    np.testing.assert_array_equal(r1["loss_magnitude"], r2["loss_magnitude"])


def test_every_trial_gets_an_outcome_class():
    factor = build_kb_scenario()
    result = factor.simulate(10_000, np.random.default_rng(3))
    assert not np.any(result["outcome_class"] == "")


def test_detected_at_stage_consistency():
    factor = build_kb_scenario()
    result = factor.simulate(20_000, np.random.default_rng(5))
    outcome_class = result["outcome_class"]
    detected_at_stage = result["detected_at_stage"]

    not_detected = detected_at_stage == -1
    assert np.all(
        np.isin(
            outcome_class[not_detected],
            [DetectionResponseFactor.FULL_IMPACT, DetectionResponseFactor.ATTACKER_FAILS],
        )
    )
    detected = detected_at_stage > 0
    assert np.all(np.isin(outcome_class[detected], list(KB_STAGE_OUTCOME_MAP.values())))


def test_lm_selected_from_correct_distribution():
    constant_distributions = {
        "early": Constant(1.0),
        "mid": Constant(2.0),
        "late": Constant(3.0),
        DetectionResponseFactor.FULL_IMPACT: Constant(4.0),
        DetectionResponseFactor.ATTACKER_FAILS: Constant(5.0),
    }
    factor = build_kb_scenario(loss_distributions=constant_distributions)
    result = factor.simulate(20_000, np.random.default_rng(11))

    value_by_class = {"early": 1.0, "mid": 2.0, "late": 3.0,
                       DetectionResponseFactor.FULL_IMPACT: 4.0,
                       DetectionResponseFactor.ATTACKER_FAILS: 5.0}
    for cls, value in value_by_class.items():
        mask = result["outcome_class"] == cls
        if np.any(mask):
            np.testing.assert_allclose(result["loss_magnitude"][mask], value)


def test_outcome_class_unaffected_by_unrelated_distribution_change():
    # Ändert man nur die Full-Impact-Verteilung, dürfen Klassenzuordnung und
    # detected_at_stage für ALLE Trials unverändert bleiben (Klassifikation
    # passiert vor der LM-Ziehung) -> Regressionsschutz gegen Stream-Kopplung.
    baseline = build_kb_scenario()
    changed_distributions = dict(KB_LOSS_DISTRIBUTIONS)
    changed_distributions[DetectionResponseFactor.FULL_IMPACT] = BetaPert(
        low=500_000, mode=1_000_000, high=2_000_000
    )
    changed = build_kb_scenario(loss_distributions=changed_distributions)

    r1 = baseline.simulate(20_000, np.random.default_rng(17))
    r2 = changed.simulate(20_000, np.random.default_rng(17))

    np.testing.assert_array_equal(r1["outcome_class"], r2["outcome_class"])
    np.testing.assert_array_equal(r1["detected_at_stage"], r2["detected_at_stage"])


def test_detection_response_factor_validates_stage_outcome_map():
    stages = [Stage(name="S1", coverage=0.9, visibility=0.8, vis_reliability=0.9,
                     recognition=0.5, rec_reliability=0.9, monitoring_cadence=0.1,
                     mon_reliability=0.9, duration=1.0, progression_probability=0.5)]
    with pytest.raises(ValueError):
        DetectionResponseFactor(
            name="broken", stages=stages, stage_outcome_map={1: "early", 2: "mid"},
            loss_distributions=KB_LOSS_DISTRIBUTIONS,
        )


def test_detection_response_factor_rejects_reserved_class_names():
    stages = [Stage(name="S1", coverage=0.9, visibility=0.8, vis_reliability=0.9,
                     recognition=0.5, rec_reliability=0.9, monitoring_cadence=0.1,
                     mon_reliability=0.9, duration=1.0, progression_probability=0.5)]
    with pytest.raises(ValueError):
        DetectionResponseFactor(
            name="broken", stages=stages,
            stage_outcome_map={1: DetectionResponseFactor.FULL_IMPACT},
            loss_distributions=KB_LOSS_DISTRIBUTIONS,
        )


def test_detection_response_factor_requires_matching_loss_distributions():
    stages = [Stage(name="S1", coverage=0.9, visibility=0.8, vis_reliability=0.9,
                     recognition=0.5, rec_reliability=0.9, monitoring_cadence=0.1,
                     mon_reliability=0.9, duration=1.0, progression_probability=0.5)]
    with pytest.raises(ValueError):
        DetectionResponseFactor(
            name="broken", stages=stages, stage_outcome_map={1: "early"},
            loss_distributions={"early": Constant(1.0)},  # fehlt: full_impact, attacker_fails
        )


def test_response_time_requires_configuration():
    factor = build_kb_scenario()
    with pytest.raises(ValueError):
        factor.response_time(100, np.random.default_rng(1))


def test_response_time_matches_core_formula():
    factor = DetectionResponseFactor(
        name="mit Response-Zeiten",
        stages=[Stage(name="S1", coverage=0.9, visibility=0.8, vis_reliability=0.9,
                       recognition=0.5, rec_reliability=0.9, monitoring_cadence=0.1,
                       mon_reliability=0.9, duration=1.0, progression_probability=0.5)],
        stage_outcome_map={1: "early"},
        loss_distributions={
            "early": Constant(1.0),
            DetectionResponseFactor.FULL_IMPACT: Constant(2.0),
            DetectionResponseFactor.ATTACKER_FAILS: Constant(3.0),
        },
        t_containment=Constant(5.0),
        t_resilience=Constant(20.0),
        concurrency=Constant(0.4),
    )
    result = factor.response_time(10, np.random.default_rng(1))
    np.testing.assert_allclose(result, 23.0)
