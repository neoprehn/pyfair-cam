"""
DetectionResponseFactor – FAIR-CAM Erkennungs- und Reaktionsfaktor.

Misst die Effektivität von Detection und Response Controls.
Kombiniert Detection Time und Response Effectiveness.
"""

import numpy as np
from typing import Optional


class DetectionResponseFactor:
    """FAIR-CAM Detection & Response – Wie effektiv sind Erkennungs- und Reaktions-Controls?"""

    def __init__(self, detection_distribution, response_distribution):
        self.detection_distribution = detection_distribution
        self.response_distribution = response_distribution

    def sample_detection_time(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Sampelt Erkennungszeit (in Stunden/Tagen)."""
        return self.detection_distribution.sample(n, seed)

    def sample_response_effectiveness(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Sampelt Reaktionseffektivität (0-1)."""
        samples = self.response_distribution.sample(n, seed)
        return np.clip(samples, 0, 1)

    def apply(self, loss_samples: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
        """Reduziert Verluste basierend auf Detection & Response Effektivität."""
        effectiveness = self.sample_response_effectiveness(len(loss_samples), seed)
        return loss_samples * (1 - effectiveness)
