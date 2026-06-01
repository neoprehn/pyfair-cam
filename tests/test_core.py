"""
Tests für die reinen FAIR-CAM Kernformeln (core.py).

Die Erwartungswerte werden direkt aus den Formeln in
01_FAIR_CAM_Core_Concepts.md abgeleitet.
"""

import numpy as np
import pytest

from pyfair_cam import reliability, operational_efficacy, combined_susceptibility


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
