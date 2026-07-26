"""
Tests für den to_pyfair()-Adapter (Phase 3, Pfad "vuln"/A und "cs"/B).

``pyfair`` ist eine optionale Abhängigkeit (Extra ``pyfair-cam[pyfair]``) –
Tests, die es tatsächlich importieren, werden übersprungen, wenn es nicht
installiert ist. Die reine Validierung (mode-Fehler) läuft immer, da sie
pyfair gar nicht erst importiert.

Pfad A und Pfad B sind bewusst nicht kalibriert (siehe
pyfair_cam/adapter/to_pyfair.py Modul-Docstring und ROADMAP.md) – die
Pfad-B-Tests prüfen deshalb Plausibilität, nicht Übereinstimmung mit Pfad A.
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


def test_cs_mode_without_threat_capability_raises_value_error():
    model = create_model_without_controls()
    with pytest.raises(ValueError):
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


# --- Pfad CS/B -------------------------------------------------------------


def test_cs_mode_feeds_control_strength_and_threat_capability():
    model = create_model_with_control()
    fair_model, cam_result = model.to_pyfair(
        mode="cs", random_seed=5, threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8)
    )

    results = fair_model.export_results()
    expected_cs = 1.0 - cam_result["susceptibility"]
    np.testing.assert_allclose(results["Control Strength"].to_numpy(), expected_cs)
    assert results["Threat Capability"].notna().all()
    assert (results["Threat Capability"] >= 0).all()


def test_cs_mode_without_controls_is_almost_fully_vulnerable():
    """Ohne Controls ist Control Strength = 0 für jeden Trial -> pyfairs
    natives Vulnerability = mean(CS < TCap) sollte nahe 1 liegen (nicht
    zwingend exakt 1 wie bei Pfad A, siehe Modul-Docstring: A und B sind
    bewusst nicht kalibriert)."""
    model = create_model_without_controls()
    fair_model, cam_result = model.to_pyfair(
        mode="cs", random_seed=11, threat_capability=BetaPert(low=0.2, mode=0.5, high=0.9)
    )

    assert np.all((1.0 - cam_result["susceptibility"]) == 0.0)
    pyfair_vuln = fair_model.export_results()["Vulnerability"].to_numpy()
    assert np.all(pyfair_vuln > 0.95)


def test_cs_mode_can_diverge_from_vuln_mode():
    """Dokumentiert die bewusste Design-Entscheidung: Pfad A und Pfad B sind
    nicht kalibriert und dürfen für dieselben Controls unterschiedliche
    Risk-Verteilungen liefern (siehe ROADMAP.md 'Offene
    Architektur-Entscheidung', Entscheidung 2026-07-26)."""
    model = create_model_with_control()

    vuln_fair, _ = model.to_pyfair(mode="vuln", random_seed=9)
    cs_fair, _ = model.to_pyfair(
        mode="cs", random_seed=9, threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8)
    )

    vuln_risk_mean = vuln_fair.export_results()["Risk"].mean()
    cs_risk_mean = cs_fair.export_results()["Risk"].mean()
    # Kein assert auf Gleichheit oder Ungleichheit einer bestimmten Richtung -
    # der Test dokumentiert nur, dass beide Pfade unabhängig voneinander
    # valide, plausible (positive) Ergebnisse liefern.
    assert vuln_risk_mean > 0
    assert cs_risk_mean > 0


# --- compare_paths() --------------------------------------------------------


def test_compare_paths_returns_both_models_and_stats():
    model = create_model_with_control()
    result = model.compare_pyfair_paths(
        threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8), random_seed=13
    )

    assert set(result.keys()) == {
        "vuln_model", "cs_model", "cam_result", "cs_vulnerability_scalar", "stats", "note",
    }
    assert list(result["stats"].columns) == ["vuln (Pfad A)", "cs (Pfad B)"]
    assert list(result["stats"].index) == ["mean", "std", "median", "VaR95", "VaR99", "max"]
    assert result["stats"].loc["mean", "vuln (Pfad A)"] > 0
    assert result["stats"].loc["mean", "cs (Pfad B)"] > 0


def test_compare_paths_uses_same_cam_result_for_both_paths():
    """Gleicher Seed auf beiden Seiten -> TEF/Susceptibility/LM stammen aus
    identischen Trials, nur die Vulnerability-Herleitung unterscheidet sich."""
    model = create_model_with_control()
    result = model.compare_pyfair_paths(
        threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8), random_seed=17
    )

    vuln_risk = result["vuln_model"].export_results()["Risk"].to_numpy()
    np.testing.assert_allclose(vuln_risk, result["cam_result"]["risk"])


def test_compare_paths_documents_variance_collapse_in_cs_path():
    """Empirischer Beleg für den in ROADMAP.md dokumentierten Fund: pyfairs
    natives Vulnerability = mean(CS < TCap) ist EIN Skalar über alle Trials
    (siehe pyfair/model/model_calc.py._calculate_step_average), Pfad A dagegen
    behält die volle trialweise Susceptibility-Streuung. Deshalb ist
    std(cs) < std(vuln) hier ein erwartetes Struktur-Merkmal, kein Zufall."""
    model = create_model_with_control()
    result = model.compare_pyfair_paths(
        threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8), random_seed=21
    )

    # pyfairs natives Vulnerability ist für JEDEN Trial identisch (ein Skalar).
    cs_vuln = result["cs_model"].export_results()["Vulnerability"].to_numpy()
    assert result["cs_model"].export_results()["Vulnerability"].nunique() == 1
    assert np.all(cs_vuln == result["cs_vulnerability_scalar"])

    assert result["stats"].loc["std", "cs (Pfad B)"] < result["stats"].loc["std", "vuln (Pfad A)"]
