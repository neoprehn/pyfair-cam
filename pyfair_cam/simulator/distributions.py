"""
Wahrscheinlichkeitsverteilungen für den FAIR-CAM Monte Carlo Simulator.
Alle Verteilungen sind vektorisiert (numpy) für maximale Performance.
"""

import numpy as np
from scipy import stats


class BetaPert:
    """
    BetaPERT Verteilung – Drei-Punkt-Schätzung (min, wahrscheinlich, max).
    Wird für FAIR-CAM Faktoren wie Resistance und Susceptibility genutzt.
    """
    def __init__(self, low: float, mode: float, high: float, gamma: float = 4):
        self.low = low
        self.mode = mode
        self.high = high
        self.gamma = gamma

    def sample(self, n: int, seed: int = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)
        mean = (self.low + self.gamma * self.mode + self.high) / (self.gamma + 2)
        if mean == self.low:
            return np.full(n, self.low)
        alpha = (mean - self.low) * (2 * self.mode - self.low - self.high)
        alpha /= (self.mode - mean) * (self.high - self.low)
        beta = alpha * (self.high - mean) / (mean - self.low)
        samples = stats.beta.rvs(alpha, beta, size=n)
        return self.low + samples * (self.high - self.low)


class LogNormal:
    """Lognormal-Verteilung – ideal für Verlusthöhen (rechts-schief)."""
    def __init__(self, mean: float, stdev: float):
        self.mean = mean
        self.stdev = stdev

    def sample(self, n: int, seed: int = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)
        mu = np.log(self.mean ** 2 / np.sqrt(self.stdev ** 2 + self.mean ** 2))
        sigma = np.sqrt(np.log(1 + (self.stdev / self.mean) ** 2))
        return np.random.lognormal(mu, sigma, n)


class Normal:
    """Normalverteilung – für symmetrische Größen."""
    def __init__(self, mean: float, stdev: float):
        self.mean = mean
        self.stdev = stdev

    def sample(self, n: int, seed: int = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)
        return np.random.normal(self.mean, self.stdev, n)


class Uniform:
    """Gleichverteilung – wenn keine Präferenz bekannt."""
    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high

    def sample(self, n: int, seed: int = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)
        return np.random.uniform(self.low, self.high, n)


class Poisson:
    """Poisson-Verteilung – für Häufigkeiten (Events pro Zeitraum)."""
    def __init__(self, lam: float):
        self.lam = lam

    def sample(self, n: int, seed: int = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)
        return np.random.poisson(self.lam, n)


class Bernoulli:
    """Bernoulli-Verteilung – für Ja/Nein Events (z.B. Vulnerability)."""
    def __init__(self, p: float):
        self.p = p

    def sample(self, n: int, seed: int = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)
        return np.random.binomial(1, self.p, n).astype(float)
