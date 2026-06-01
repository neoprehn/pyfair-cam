"""
Tests für FairCamModel und FairCamSimulator (Integration / Verhalten).
"""

import numpy as np
from pyfair_cam import (
    FairCamModel,
    FairCamSimulator,
    BetaPert,
    LogNormal,
    ResistiveControl,
)


def create_basic_model():
    model = FairCamModel(name="Test Modell")
    model.input_threat_frequency(BetaPert(low=1, mode=5, high=10))
    model.input_loss_magnitude(LogNormal(mean=100_000, stdev=50_000))
    return model


def test_simulator_runs():
    sim = FairCamSimulator(n_simulations=1_000, seed=42)
    results = sim.run(create_basic_model())
    assert len(results) == 1_000


def test_results_are_positive():
    sim = FairCamSimulator(n_simulations=1_000, seed=42)
    results = sim.run(create_basic_model())
    assert np.all(results >= 0)


def test_seed_reproducibility():
    r1 = FairCamSimulator(n_simulations=1_000, seed=42).run(create_basic_model())
    r2 = FairCamSimulator(n_simulations=1_000, seed=42).run(create_basic_model())
    np.testing.assert_array_equal(r1, r2)


def test_different_seeds_differ():
    r1 = FairCamSimulator(n_simulations=1_000, seed=1).run(create_basic_model())
    r2 = FairCamSimulator(n_simulations=1_000, seed=2).run(create_basic_model())
    assert not np.array_equal(r1, r2)


def test_statistics_ordering():
    sim = FairCamSimulator(n_simulations=10_000, seed=42)
    sim.run(create_basic_model())
    stats = sim.get_statistics()
    assert stats['p99'] >= stats['p95'] >= stats['median']


def test_no_controls_susceptibility_is_one():
    """Ohne Controls: Susceptibility = 1.0, also LEF == TEF."""
    sim = FairCamSimulator(n_simulations=5_000, seed=7)
    sim.run(create_basic_model())
    comp = sim.get_components()
    np.testing.assert_allclose(comp['susceptibility'], 1.0)
    np.testing.assert_allclose(comp['lef'], comp['tef'])


def test_control_reduces_risk():
    """Ein resistives Control muss das erwartete Risiko senken."""
    base = create_basic_model()
    sim_base = FairCamSimulator(n_simulations=20_000, seed=42)
    sim_base.run(base)

    protected = create_basic_model()
    protected.add_resistive_control(
        ResistiveControl(name="C1", intended_efficacy=0.8, coverage=1.0)
    )
    sim_prot = FairCamSimulator(n_simulations=20_000, seed=42)
    sim_prot.run(protected)

    assert sim_prot.get_ale() < sim_base.get_ale()


def test_defense_in_depth_stacks():
    """Zwei Controls reduzieren die Susceptibility stärker als eines (OR-Logik)."""
    one = create_basic_model()
    one.add_resistive_control(ResistiveControl("C1", intended_efficacy=0.5, coverage=1.0))
    s_one = FairCamSimulator(n_simulations=10_000, seed=3)
    s_one.run(one)

    two = create_basic_model()
    two.add_resistive_control(ResistiveControl("C1", intended_efficacy=0.5, coverage=1.0))
    two.add_resistive_control(ResistiveControl("C2", intended_efficacy=0.5, coverage=1.0))
    s_two = FairCamSimulator(n_simulations=10_000, seed=3)
    s_two.run(two)

    assert s_two.get_components()['susceptibility'].mean() < \
        s_one.get_components()['susceptibility'].mean()


def test_tef_lm_independent():
    """Statistische Konsistenz: TEF und LM dürfen nicht korreliert sein
    (würde auf gekoppelte Zufallsströme / Seed-Bug hindeuten)."""
    sim = FairCamSimulator(n_simulations=50_000, seed=123)
    sim.run(create_basic_model())
    comp = sim.get_components()
    corr = np.corrcoef(comp['tef'], comp['loss_magnitude'])[0, 1]
    assert abs(corr) < 0.05
