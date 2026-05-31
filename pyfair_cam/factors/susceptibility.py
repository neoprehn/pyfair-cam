"""
SusceptibilityFactor – FAIR-CAM Anfälligkeitsfaktor.

Misst wie anfällig ein Asset für einen Angriff ist.
Wert zwischen 0 (nicht anfällig) und 1 (vollständig anfällig).
"""

import numpy as np
from typing import Optional


class SusceptibilityFactor:
    """FAIR-CAM Susceptibility – Wie anfällig ist das Asset?"""

    def __init__(self, distribution, **params):
        self.distribution = distribution
        self.params = params

    def sample(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Sampelt Susceptibility-Werte (0-1)."""
        samples = self.distribution.sample(n, seed)
        return np.clip(samples, 0, 1)

    def apply(self, event_samples: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
        """Filtert Events basierend auf Susceptibility."""
        susceptibility = self.sample(len(event_samples), seed)
        mask = np.random.random(len(event_samples)) < susceptibility
        return event_samples * mask
