"""
Wahrscheinlichkeitsverteilungen für den FAIR-CAM Monte-Carlo-Simulator.

Einheitliches Interface: jede Verteilung implementiert ``sample(n, rng)``,
wobei ``rng`` ein ``numpy.random.Generator`` ist. Der Generator wird *einmal*
zentral im Simulator erzeugt und an alle Sample-Aufrufe durchgereicht.
So zieht jede Größe (TEF, LM, jeder Control-Parameter) aus *demselben*,
fortlaufenden Zufallsstrom → unabhängige, statistisch saubere Samples.

WICHTIG: Hier wird *niemals* ``np.random.seed()`` aufgerufen. Globales Seeding
würde die Ströme koppeln und die Monte-Carlo-Ergebnisse verfälschen.
"""

import numpy as np
from scipy import stats


class Distribution:
    """Basisklasse – definiert das Sample-Interface."""

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        raise NotImplementedError


def as_distribution(value):
    """Hilfsfunktion: wandelt Skalare in ``PointEstimate`` um, lässt Distributions durch."""
    if isinstance(value, Distribution):
        return value
    return PointEstimate(value)


class PointEstimate(Distribution):
    """Konstanter Wert – für sichere/bekannte Parameter (z.B. Coverage = 1.0)."""

    def __init__(self, value: float):
        self.value = float(value)

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return np.full(n, self.value)


# Alias für Lesbarkeit
Constant = PointEstimate


class BetaPert(Distribution):
    """
    BetaPERT-Verteilung – Drei-Punkt-Schätzung (low, mode, high).

    Parametrisierung identisch zu pyfair (FairBetaPert), damit beide
    Bibliotheken konsistente Ergebnisse liefern.
    """

    def __init__(self, low: float, mode: float, high: float, gamma: float = 4):
        if high <= low:
            raise ValueError('"low" muss kleiner als "high" sein.')
        if not (low <= mode <= high):
            raise ValueError('"mode" muss zwischen "low" und "high" liegen.')
        self.low, self.mode, self.high, self.gamma = low, mode, high, gamma
        rng_range = high - low
        mean = (low + gamma * mode + high) / (gamma + 2)
        stdev = rng_range / (gamma + 2)
        # Degenerierter Fall: mode == mean → symmetrisch, alpha = beta
        if np.isclose(mean, mode):
            alpha = beta = gamma / 2 + 1
        else:
            alpha = ((mean - low) / rng_range) * (((mean - low) * (high - mean) / stdev ** 2) - 1)
            beta = alpha * (high - mean) / (mean - low)
        self._dist = stats.beta(alpha, beta, loc=low, scale=rng_range)

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return self._dist.rvs(size=n, random_state=rng)


class LogNormal(Distribution):
    """Lognormal-Verteilung – ideal für Verlusthöhen (rechts-schief).

    Parametrisiert über den *arithmetischen* Mittelwert und die Standard-
    abweichung der Lognormal-Größe (nicht über mu/sigma des Logarithmus).
    """

    def __init__(self, mean: float, stdev: float):
        if mean <= 0:
            raise ValueError("LogNormal benötigt einen positiven Mittelwert.")
        self.mean = mean
        self.stdev = stdev
        self._mu = np.log(mean ** 2 / np.sqrt(stdev ** 2 + mean ** 2))
        self._sigma = np.sqrt(np.log(1 + (stdev / mean) ** 2))

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.lognormal(self._mu, self._sigma, n)


class Normal(Distribution):
    """Normalverteilung – für symmetrische Größen."""

    def __init__(self, mean: float, stdev: float):
        self.mean = mean
        self.stdev = stdev

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.normal(self.mean, self.stdev, n)


class Uniform(Distribution):
    """Gleichverteilung – wenn keine Präferenz bekannt ist."""

    def __init__(self, low: float, high: float):
        if high < low:
            raise ValueError('"low" darf nicht größer als "high" sein.')
        self.low = low
        self.high = high

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.uniform(self.low, self.high, n)


class Poisson(Distribution):
    """Poisson-Verteilung – für Häufigkeiten (Events pro Zeitraum)."""

    def __init__(self, lam: float):
        if lam < 0:
            raise ValueError("Poisson benötigt eine nicht-negative Rate (lam).")
        self.lam = lam

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.poisson(self.lam, n).astype(float)


class Bernoulli(Distribution):
    """Bernoulli-Verteilung – für Ja/Nein-Events (z.B. Vulnerability vorhanden)."""

    def __init__(self, p: float):
        if not (0.0 <= p <= 1.0):
            raise ValueError("Bernoulli p muss in [0, 1] liegen.")
        self.p = p

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.binomial(1, self.p, n).astype(float)
