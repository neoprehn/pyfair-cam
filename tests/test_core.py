"""
Tests für die reinen FAIR-CAM Kernformeln (core.py).

Die Erwartungswerte werden direkt aus den Formeln in
01_FAIR_CAM_Core_Concepts.md abgeleitet.
"""

import numpy as np
import pytest

from pyfair_cam import (
    combined_susceptibility,
    detection_within_time,
    effective_parameter,
    expected_gross_loss,
    operational_efficacy,
    pert_mean,
    progression_reach_probability,
    reliability,
    response_time,
    reviews_per_stage,
    stage_detection_probability,
)


def test_reliability_no_variance_is_one():
    # VF = 0 → immer im Soll-Zustand
    assert reliability(0, 30) == pytest.approx(1.0)


def test_reliability_formula():
    # Rel = (1 - 12/365)^10
    expected = (1 - 12 / 365) ** 10
    assert float(reliability(12, 10)) == pytest.approx(expected)


def test_reliability_vd_zero_is_one():
    # Dauer 0 → keine Wirkung der Varianz
    assert float(reliability(50, 0)) == pytest.approx(1.0)


def test_operational_efficacy_perfect_control():
    # Rel=1, IntEff=1, Cov=1 → OpEff = 1
    assert float(operational_efficacy(1.0, 1.0, 1.0, 0.0)) == pytest.approx(1.0)


def test_operational_efficacy_formula():
    # OpEff = Cov × [Rel×IntEff + (1-Rel)×VarEff]
    cov, rel, int_eff, var_eff = 0.9, 0.8, 0.7, 0.1
    expected = cov * (rel * int_eff + (1 - rel) * var_eff)
    assert float(operational_efficacy(cov, rel, int_eff, var_eff)) == pytest.approx(expected)


def test_operational_efficacy_coverage_scales():
    # Halbe Coverage → halbe OpEff (bei sonst gleichen Werten)
    full = float(operational_efficacy(1.0, 0.9, 0.8, 0.0))
    half = float(operational_efficacy(0.5, 0.9, 0.8, 0.0))
    assert half == pytest.approx(full / 2)


def test_combined_susceptibility_single():
    opeff = np.array([0.6, 0.6])
    np.testing.assert_allclose(combined_susceptibility([opeff]), [0.4, 0.4])


def test_combined_susceptibility_two_controls():
    # (1-0.5) × (1-0.5) = 0.25
    a = np.array([0.5])
    b = np.array([0.5])
    np.testing.assert_allclose(combined_susceptibility([a, b]), [0.25])


def test_combined_susceptibility_monotonic():
    # Mehr Controls → niemals höhere Susceptibility
    a = np.array([0.4])
    one = combined_susceptibility([a])
    two = combined_susceptibility([a, np.array([0.3])])
    assert two[0] <= one[0]


def test_combined_susceptibility_empty_raises():
    with pytest.raises(ValueError):
        combined_susceptibility([])


# ---------------------------------------------------------------------------
# Detection & Response (Phase 2) – Ground Truth aus dem 6-Stufen-Ransomware-
# Beispiel in 04_Detection_Response_Measurement.md, Cov/V/RelV/R/RelR/M/RelM/
# tau/P/rho je Stage. Werte unabhängig nachgerechnet (siehe Roadmap-Notiz):
# die KB reproduziert bei Stage 1 und 6 ihre eigenen P(Detect)-Zahlen nicht
# exakt aus Formel + Tabelle (Stufen 2-5 passen exakt) – wir folgen der
# dokumentierten Formel wörtlich, nicht den abgedruckten Beispielzahlen.
# ---------------------------------------------------------------------------

KB_STAGES = [
    # cov,  v,    rel_v, r,    rel_r, m,     rel_m, tau,  p,    rho
    (0.95, 0.70, 0.95, 0.40, 0.90, 0.042, 0.95, 0.25, 0.90, 0.40),
    (0.98, 0.85, 0.95, 0.60, 0.92, 0.042, 0.95, 0.50, 0.85, 0.55),
    (0.96, 0.80, 0.94, 0.75, 0.90, 0.042, 0.94, 0.50, 0.80, 0.60),
    (0.92, 0.90, 0.96, 0.65, 0.88, 0.042, 0.92, 1.00, 0.75, 0.65),
    (0.88, 0.75, 0.92, 0.55, 0.85, 0.042, 0.90, 0.75, 0.70, 0.50),
    (0.85, 0.60, 0.90, 0.45, 0.80, 0.042, 0.88, 0.25, 0.95, 0.45),
]
KB_V_EFF = [0.665, 0.8075, 0.752, 0.864, 0.69, 0.54]
KB_R_EFF = [0.36, 0.552, 0.675, 0.572, 0.4675, 0.36]
KB_LAMBDA = [5.6548, 11.3095, 11.1905, 21.9048, 16.0714, 5.2381]
KB_P_DETECT = [0.40153, 0.785989, 0.721539, 0.794876, 0.603362, 0.298693]
KB_P_REACH = [1.0, 0.53862289, 0.09798048, 0.02182701, 0.00335794, 0.00093232]


def test_effective_parameter_visibility_and_recognition():
    for (cov, v, rel_v, r, rel_r, *_rest), v_eff, r_eff in zip(KB_STAGES, KB_V_EFF, KB_R_EFF):
        assert float(effective_parameter(v, rel_v)) == pytest.approx(v_eff, rel=1e-3)
        assert float(effective_parameter(r, rel_r)) == pytest.approx(r_eff, rel=1e-3)


def test_reviews_per_stage_matches_kb_table():
    for (*_front, m, rel_m, tau, _p, _rho), lam in zip(KB_STAGES, KB_LAMBDA):
        assert float(reviews_per_stage(tau, m, rel_m)) == pytest.approx(lam, rel=1e-3)


def test_stage_detection_probability_matches_recomputed_kb_values():
    for (cov, v, rel_v, r, rel_r, m, rel_m, tau, _p, rho), v_eff, r_eff, lam, pdet in zip(
        KB_STAGES, KB_V_EFF, KB_R_EFF, KB_LAMBDA, KB_P_DETECT
    ):
        result = stage_detection_probability(cov, v_eff, r_eff, rho, lam)
        assert float(result) == pytest.approx(pdet, rel=1e-3)


def test_stage_detection_probability_rho_zero_special_case():
    # Sonderfall: P(Detect) = Cov x V_eff x R_eff (kein Grenzwert der allg. Formel)
    result = stage_detection_probability(coverage=0.9, v_eff=0.8, r_eff=0.5, rho=0.0, lam=10)
    assert float(result) == pytest.approx(0.9 * 0.8 * 0.5)


def test_stage_detection_probability_bound_is_coverage_times_visibility():
    # Mathematische Obergrenze: Detection kann Cov x V_eff nie überschreiten,
    # auch nicht bei sehr vielen Reviews.
    result = stage_detection_probability(coverage=0.9, v_eff=0.8, r_eff=0.5, rho=1.0, lam=10_000)
    assert float(result) == pytest.approx(0.9 * 0.8, rel=1e-6)


def test_stage_detection_probability_monotonic_in_lambda():
    low = stage_detection_probability(coverage=0.9, v_eff=0.8, r_eff=0.5, rho=0.5, lam=2)
    high = stage_detection_probability(coverage=0.9, v_eff=0.8, r_eff=0.5, rho=0.5, lam=8)
    assert float(high) >= float(low)


def test_progression_reach_probability_chain_matches_kb():
    reach = 1.0
    reaches = [reach]
    for (*_front, p, _rho), pdet in zip(KB_STAGES[:-1], KB_P_DETECT[:-1]):
        reach = float(progression_reach_probability(reach, pdet, p))
        reaches.append(reach)
    for computed, expected in zip(reaches, KB_P_REACH):
        assert computed == pytest.approx(expected, rel=1e-2)


def test_response_time_fully_sequential():
    # alpha=0 -> vollstaendig sequenziell: T = Tc + Ts
    assert float(response_time(5, 20, 0.0)) == pytest.approx(25.0)


def test_response_time_fully_parallel():
    # alpha=1 -> vollstaendig parallel: T = max(Tc, Ts)
    assert float(response_time(5, 20, 1.0)) == pytest.approx(20.0)


def test_response_time_partial_overlap():
    assert float(response_time(5, 20, 0.4)) == pytest.approx(23.0)


def test_pert_mean_matches_kb_outcome_classes():
    # E[X] = (min + 4*mode + max) / 6, aus der KB-Tabelle der bedingten Verlustklassen
    assert float(pert_mean(2_000, 8_000, 30_000)) == pytest.approx(10_666.67, rel=1e-4)
    assert float(pert_mean(25_000, 75_000, 250_000)) == pytest.approx(95_833.33, rel=1e-4)
    assert float(pert_mean(200_000, 500_000, 2_000_000)) == pytest.approx(700_000.0, rel=1e-4)
    assert float(pert_mean(1_000_000, 3_000_000, 5_000_000)) == pytest.approx(3_000_000.0, rel=1e-4)
    assert float(pert_mean(2_000, 5_000, 15_000)) == pytest.approx(6_166.67, rel=1e-4)


def test_expected_gross_loss_matches_kb_worked_example():
    # KB verwendet ihre eigenen (abgedruckten) Klassenwahrscheinlichkeiten -> $21,501
    probs = [0.818, 0.0897, 0.0024, 0.00065, 0.089]
    means = [10_666.67, 95_833.33, 700_000.0, 3_000_000.0, 6_166.67]
    assert expected_gross_loss(probs, means) == pytest.approx(21_501, rel=1e-3)


def test_detection_within_time_equals_stage_probability_at_full_duration():
    cov, v_eff, r_eff, rho, m, rel_m, tau = 0.9, 0.8, 0.5, 0.5, 0.042, 0.95, 0.5
    lam = reviews_per_stage(tau, m, rel_m)
    expected = stage_detection_probability(cov, v_eff, r_eff, rho, lam)
    result = detection_within_time(cov, v_eff, r_eff, rho, m, rel_m, time_budget=tau)
    assert float(result) == pytest.approx(float(expected))


def test_detection_within_time_zero_budget_is_zero():
    result = detection_within_time(0.9, 0.8, 0.5, 0.5, 0.042, 0.95, time_budget=0)
    assert float(result) == pytest.approx(0.0)


def test_detection_within_time_monotonic_in_budget():
    kwargs = dict(coverage=0.9, v_eff=0.8, r_eff=0.5, rho=0.5, monitoring_cadence=0.042, monitoring_reliability=0.95)
    short = detection_within_time(**kwargs, time_budget=0.1)
    long = detection_within_time(**kwargs, time_budget=2.0)
    assert float(long) >= float(short)
