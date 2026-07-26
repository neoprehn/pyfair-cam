"""
Tests für den to_pyfair()-Adapter (Phase 3, Pfad "vuln" / A).

``pyfair`` ist eine optionale Abhängigkeit (Extra ``pyfair-cam[pyfair]``) –
Tests, die es tatsächlich importieren, werden übersprungen, wenn es nicht
installiert ist. Die reine Validierung (mode-Fehler) läuft immer, da sie
pyfair gar nicht erst importiert.
"""

import numpy as np
import pytest

from pyfair_cam import BetaPert, FairCamModel, LogNormal, ResistiveControl

pyfair = pytest.importorskip("pyfair")


def create_model_without_controls():
    model = FairCamModel(name="Adapter Test", n_simulations=2_000)
    model.input_threat_frequency(BetaPert(low=1, mode=5, high=10))
    model.input_loss_magnitude(LogNormal(mean=100_000, stdev=50_000))
    return model


def create_model_with_control():
    model = create_model_without_controls()
    model.add_resistive_control(
        ResistiveControl(
            name="EDR",
            intended_efficacy=0.8,
            variant_efficacy=0.1,
            variance_frequency=2,
            variance_duration=3,
            coverage=0.9,
        )
    )
    return model


def test_unknown_mode_raises_value_error():
    model = create_model_without_controls()
    with pytest.raises(ValueError):
        model.to_pyfair(mode="not-a-mode")


def test_cs_mode_raises_not_implemented():
    model = create_model_without_controls()
    with pytest.raises(NotImplementedError):
        model.to_pyfair(mode="cs")


def test_without_controls_matches_cam_result_exactly():
    """Validierung aus ROADMAP.md: identische Inputs ohne Controls
    -> CAM-Ergebnis == reines pyfair (Susceptibility = 1 für alle Trials)."""
    model = create_model_without_controls()
    fair_model, cam_result = model.to_pyfair(mode="vuln", random_seed=7)

    assert np.all(cam_result["susceptibility"] == 1.0)

    pyfair_risk = fair_model.export_results()["Risk"].to_numpy()
    np.testing.assert_allclose(pyfair_risk, cam_result["risk"])


def test_pyfair_model_uses_same_n_simulations():
    model = create_model_without_controls()
    fair_model, cam_result = model.to_pyfair(mode="vuln")
    assert len(fair_model.export_results()) == model.n_simulations
    assert len(cam_result["risk"]) == model.n_simulations


def test_controls_reduce_risk_via_pyfair():
    baseline_model = create_model_without_controls()
    baseline_fair, _ = baseline_model.to_pyfair(mode="vuln", random_seed=1)

    controlled_model = create_model_with_control()
    controlled_fair, cam_result = controlled_model.to_pyfair(mode="vuln", random_seed=1)

    assert np.mean(cam_result["susceptibility"]) < 1.0
    baseline_mean = baseline_fair.export_results()["Risk"].mean()
    controlled_mean = controlled_fair.export_results()["Risk"].mean()
    assert controlled_mean < baseline_mean


def test_pyfair_vulnerability_matches_cam_susceptibility():
    model = create_model_with_control()
    fair_model, cam_result = model.to_pyfair(mode="vuln", random_seed=3)

    pyfair_vuln = fair_model.export_results()["Vulnerability"].to_numpy()
    np.testing.assert_allclose(pyfair_vuln, cam_result["susceptibility"])
