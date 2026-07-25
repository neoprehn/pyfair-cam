"""
Tests für die Verteilungen (`pyfair_cam.simulator.distributions`).
"""

import numpy as np
import pytest

from pyfair_cam import BetaPert, Poisson


def test_beta_pert_symmetric_mode_matches_target_stdev():
    """Regressionstest: bei mode == (low+high)/2 (mean == mode) muss die
    tatsächliche Stichproben-Stdev der Zielformel stdev = range/(gamma+2)
    entsprechen. Ein früherer Sonderfall lieferte hier fälschlich
    alpha = beta = gamma/2 + 1 (Vose-Formel) statt der zu dieser
    Moment-Matching-Parametrisierung passenden Werte -> Stdev war ~13% zu groß.
    """
    low, mode, high, gamma = 0, 50, 100, 4
    target_stdev = (high - low) / (gamma + 2)

    dist = BetaPert(low=low, mode=mode, high=high, gamma=gamma)
    samples = dist.sample(200_000, np.random.default_rng(42))

    assert samples.std() == pytest.approx(target_stdev, rel=0.02)


def test_beta_pert_boundary_modes_do_not_raise():
    """mode an den Rändern (low bzw. high) darf keine Division durch 0 auslösen."""
    BetaPert(low=0, mode=0, high=100).sample(10, np.random.default_rng(1))
    BetaPert(low=0, mode=100, high=100).sample(10, np.random.default_rng(1))


def test_poisson_without_range_is_deterministic_lambda():
    """range_=0 (Default) entspricht der bisherigen festen Rate."""
    samples = Poisson(lam=4).sample(50_000, np.random.default_rng(1))
    assert samples.mean() == pytest.approx(4, abs=0.1)


def test_poisson_with_range_widens_variance():
    """Unsicherheit über lambda (analog pyfair _gen_poisson) erhöht die
    Varianz gegenüber reinem Poisson(lam) mit fester Rate, Mittelwert bleibt
    ungefähr gleich."""
    rng = np.random.default_rng(1)
    fixed = Poisson(lam=4).sample(100_000, rng)
    uncertain = Poisson(lam=4, range_=0.4).sample(100_000, rng)

    assert uncertain.mean() == pytest.approx(4, abs=0.15)
    assert uncertain.var() > fixed.var()
