"""
ResistanceFactor – FAIR-CAM Widerstandsfaktor.

Misst die Fähigkeit von Controls, einem Angriff zu widerstehen.
Wert zwischen 0 (kein Widerstand) und 1 (vollständiger Widerstand).
"""

import numpy as np
from typing import Optional


class ResistanceFactor:
    """FAIR-CAM Resistance – Wie stark widerstehen Controls einem Angriff?"""

    def __init__(self, distribution, **params):
        self.distribution = distribution
        self.params = params

    def sample(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Sampelt Resistance-Werte (0-1)."""
        samples = self.distribution.sample(n, seed)
        return np.clip(samples, 0, 1)

    def apply(self, threat_samples: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
        """Wendet Resistance auf Bedrohungssamples an."""
        resistance = self.sample(len(threat_samples), seed)
        return threat_samples * (1 - resistance)
