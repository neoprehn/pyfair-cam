"""
Tests für FairCamModel und FairCamSimulator
"""

import pytest
import numpy as np
from pyfair_cam import (
    FairCamModel,
    FairCamSimulator,
    BetaPert,
    LogNormal,
    ResistanceFactor,
)


def create_basic_model():
    model = FairCamModel(name="Test Modell")
    model.input_threat_frequency(BetaPert(low=1, mode=5, high=10))
    model.input_loss_magnitude(LogNormal(mean=100_000, stdev=50_000))
    return model


def test_simulator_runs():
    model = create_basic_model()
    sim = FairCamSimulator(n_simulations=1_000, seed=42)
    results = sim.run(model)
    assert len(results) == 1_000


def test_results_are_positive():
    model = create_basic_model()
    sim = FairCamSimulator(n_simulations=1_000, seed=42)
    results = sim.run(model)
    assert np.all(results >= 0)


def test_seed_reproducibility():
    model = create_basic_model()
    sim1 = FairCamSimulator(n_simulations=1_000, seed=42)
    sim2 = FairCamSimulator(n_simulations=1_000, seed=42)
    results1 = sim1.run(model)
    results2 = sim2.run(model)
    np.testing.assert_array_equal(results1, results2)


def test_statistics():
    model = create_basic_model()
    sim = FairCamSimulator(n_simulations=10_000, seed=42)
    sim.run(model)
    stats = sim.get_statistics()
    assert 'mean' in stats
    assert 'p95' in stats
    assert 'p99' in stats
    assert stats['p99'] >= stats['p95'] >= stats['mean']


def test_resistance_factor():
    factor = ResistanceFactor(BetaPert(low=0.3, mode=0.6, high=0.9))
    losses = np.full(1000, 100_000.0)
    reduced = factor.apply(losses, seed=42)
    assert np.all(reduced <= losses)
