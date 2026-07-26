"""
Tests für FairCamReport.to_html() (Phase 4).

Prüft strukturelle Eigenschaften des generierten HTML/SVG (balancierte Tags,
erwartete Abschnitte je nach Modellkonfiguration, keine NaN/Inf in Zahlen) –
kein Pixel-/Rendering-Vergleich, dafür fehlt in dieser Umgebung ein Browser.
"""

import re

import numpy as np
import pytest

from pyfair_cam import (
    BetaPert,
    DetectionResponseFactor,
    FairCamModel,
    FairCamReport,
    FairCamSimulator,
    LogNormal,
    ResistiveControl,
    Stage,
)


def _balanced(html: str, tag: str) -> bool:
    return len(re.findall(f"<{tag}[ >]", html)) == len(re.findall(f"</{tag}>", html))


def create_minimal_model():
    """Ohne Controls, ohne Detection/Response – der einfachste gültige Fall."""
    model = FairCamModel(name="Report Minimal", n_simulations=500)
    model.input_threat_frequency(BetaPert(low=1, mode=5, high=10))
    model.input_loss_magnitude(LogNormal(mean=100_000, stdev=50_000))
    return model


def create_model_with_controls():
    model = create_minimal_model()
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
    model.add_resistive_control(
        ResistiveControl(name="MFA", intended_efficacy=0.6, coverage=0.95)
    )
    return model


def create_model_with_detection_response():
    model = FairCamModel(name="Report Detection", n_simulations=500)
    model.input_threat_frequency(BetaPert(low=1, mode=5, high=10))
    model.add_resistive_control(
        ResistiveControl(name="EDR", intended_efficacy=0.8, coverage=0.9)
    )
    stages = [
        Stage(
            name="Initial Access", coverage=0.95, visibility=0.70, vis_reliability=0.95,
            recognition=0.40, rec_reliability=0.90, monitoring_cadence=0.042,
            mon_reliability=0.95, duration=0.25, progression_probability=0.90,
            review_independence=0.40,
        ),
        Stage(
            name="Execution", coverage=0.85, visibility=0.60, vis_reliability=0.90,
            recognition=0.45, rec_reliability=0.80, monitoring_cadence=0.042,
            mon_reliability=0.88, duration=0.25, progression_probability=0.95,
            review_independence=0.45,
        ),
    ]
    dr = DetectionResponseFactor(
        name="Kill-Chain",
        stages=stages,
        stage_outcome_map={1: "early", 2: "late"},
        loss_distributions={
            "early": BetaPert(low=2_000, mode=8_000, high=30_000),
            "late": BetaPert(low=200_000, mode=500_000, high=2_000_000),
            DetectionResponseFactor.FULL_IMPACT: BetaPert(low=1_000_000, mode=3_000_000, high=5_000_000),
            DetectionResponseFactor.ATTACKER_FAILS: BetaPert(low=2_000, mode=5_000, high=15_000),
        },
        t_containment=BetaPert(low=1, mode=3, high=10),
        t_resilience=BetaPert(low=2, mode=7, high=21),
        concurrency=BetaPert(low=0.2, mode=0.4, high=0.6),
    )
    model.set_detection_response(dr)
    return model


def run_report(model, seed=42):
    sim = FairCamSimulator(n_simulations=model.n_simulations, seed=seed)
    sim.run(model)
    return FairCamReport(sim)


def test_to_html_without_run_raises():
    sim = FairCamSimulator(n_simulations=500, seed=1)
    report = FairCamReport(sim)
    with pytest.raises(RuntimeError):
        report.to_html()


def test_minimal_model_produces_valid_shell():
    report = run_report(create_minimal_model())
    out = report.to_html()

    assert out.startswith("<!doctype html>")
    assert 'data-theme="dark"' in out
    assert _balanced(out, "html")
    assert _balanced(out, "section")
    assert _balanced(out, "svg")
    assert _balanced(out, "table")
    # Keine Controls, keine Detection/Response -> diese Abschnitte fehlen.
    assert "Control-Wirksamkeit" not in out
    assert "Outcome-Klassen" not in out


def test_model_with_controls_includes_control_sections():
    report = run_report(create_model_with_controls())
    out = report.to_html()

    assert "Control-Wirksamkeit" in out
    assert "Vorher/Nachher: Wirkung der Controls" in out
    assert "EDR" in out
    assert "MFA" in out
    assert _balanced(out, "svg")
    assert _balanced(out, "table")


def test_model_with_detection_response_includes_stage_sections():
    report = run_report(create_model_with_detection_response())
    out = report.to_html()

    assert "Outcome-Klassen" in out
    assert "Loss Magnitude: Vorher/Nachher" in out
    assert DetectionResponseFactor.FULL_IMPACT in out
    assert DetectionResponseFactor.ATTACKER_FAILS in out


def test_no_nan_in_output():
    report = run_report(create_model_with_detection_response())
    out = report.to_html()
    assert "nan" not in out.lower()
    assert np.all(np.isfinite(report.simulator.get_results()))


def test_to_html_writes_file(tmp_path):
    report = run_report(create_minimal_model())
    out_path = tmp_path / "report.html"
    html = report.to_html(str(out_path))

    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8") == html


def test_pyfair_comparison_section_optional():
    pytest.importorskip("pyfair")
    report = run_report(create_model_with_controls())

    out_without = report.to_html()
    assert "pyfair-Andockpunkte" not in out_without

    out_with = report.to_html(threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8))
    assert "pyfair-Andockpunkte" in out_with


def test_before_after_section_does_not_mutate_model():
    model = create_model_with_controls()
    n_controls_before = len(model._controls)
    report = run_report(model)
    report.to_html()
    assert len(model._controls) == n_controls_before


def test_charts_use_theme_aware_colors_not_literal_hex():
    """Datenfarben müssen CSS-Variablen sein (Theme-Toggle), keine fest
    codierten Hex-Werte, die beim Umschalten stehen bleiben würden."""
    report = run_report(create_model_with_controls())
    out = report.to_html()
    assert "var(--cat-" in out
    assert "var(--accent)" in out


def test_report_statistics_match_simulator():
    from pyfair_cam.report.simple_report import _fmt_currency

    model = create_minimal_model()
    sim = FairCamSimulator(n_simulations=500, seed=7)
    sim.run(model)
    report = FairCamReport(sim)
    out = report.to_html()

    stats = sim.get_statistics()
    assert np.isfinite(stats["mean"])
    assert _fmt_currency(stats["mean"]) in out
    assert _fmt_currency(stats["p95"]) in out
