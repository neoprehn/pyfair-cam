"""
FairCamModel – Hauptmodell für FAIR-CAM Simulationen.

Verbindet alle FAIR-CAM Faktoren und berechnet den Gesamtverlust.
"""

import numpy as np
from typing import Optional


class FairCamModel:
    """
    FAIR-CAM Modell – verbindet Faktoren zu einer Gesamtsimulation.

    Faktoren:
    - Threat Event Frequency (TEF)
    - Resistance (Control Strength)
    - Susceptibility (Asset Vulnerability)
    - Loss Magnitude (LM)
    - Detection & Response
    """

    def __init__(self, name: str, n_simulations: int = 10_000):
        self.name = name
        self.n_simulations = n_simulations
        self._factors = {}
        self._tef = None
        self._lm = None

    def input_threat_frequency(self, distribution):
        """Setzt die Bedrohungshäufigkeit (Threat Event Frequency)."""
        self._tef = distribution
        return self

    def input_loss_magnitude(self, distribution):
        """Setzt die Verlusthöhe (Loss Magnitude)."""
        self._lm = distribution
        return self

    def add_factor(self, name: str, factor):
        """Fügt einen FAIR-CAM Faktor hinzu."""
        self._factors[name] = factor
        return self

    def calculate(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Führt die Monte Carlo Simulation durch."""
        if self._tef is None or self._lm is None:
            raise ValueError("TEF und Loss Magnitude müssen gesetzt sein.")
        if seed is not None:
            np.random.seed(seed)
        tef_samples = self._tef.sample(n, seed)
        lm_samples = self._lm.sample(n, seed)
        losses = tef_samples * lm_samples
        for name, factor in self._factors.items():
            losses = factor.apply(losses, seed)
        return losses
