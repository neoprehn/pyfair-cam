"""
FairCamModel – FAIR-CAM Hauptmodell (Frequenz-Seite).

Modelliert Risiko nach der FAIR/FAIR-CAM-Taxonomie:

    Risk = LEF × LM
    LEF  = TEF × Susceptibility
    Susceptibility = Π (1 - OpEffᵢ)      über alle resistiven Controls (OR-Logik)

Wichtig (FAIR-CAM-konform):
    - Resistive Controls wirken auf die *Frequenz-Seite* (Susceptibility),
      NICHT als Multiplikator auf die Loss Magnitude.
    - Ohne Controls ist Susceptibility = 1.0 (jedes Threat-Event wird zum Loss-Event).
    - Die Reaktion auf die Loss Magnitude (Detection/Response) ist bewusst NOCH
      NICHT enthalten und wird in einer späteren Iteration ergänzt.

Das Modell ist zustandsarm: ``calculate(n, rng)`` zieht alle Zufallsgrößen aus
dem übergebenen ``numpy.random.Generator``. Es ruft selbst NIE ``np.random.seed``.
"""

import numpy as np

from ..core import combined_susceptibility
from ..simulator.distributions import as_distribution


class FairCamModel:
    """FAIR-CAM Modell – verbindet TEF, resistive Controls und LM zu einem Risiko."""

    def __init__(self, name: str, n_simulations: int = 10_000):
        self.name = name
        self.n_simulations = n_simulations
        self._tef = None
        self._lm = None
        self._controls = []

    def input_threat_frequency(self, distribution):
        """Setzt die Threat Event Frequency (TEF), Events pro Jahr."""
        self._tef = as_distribution(distribution)
        return self

    def input_loss_magnitude(self, distribution):
        """Setzt die Loss Magnitude (LM) pro Loss-Event."""
        self._lm = as_distribution(distribution)
        return self

    def add_resistive_control(self, control):
        """Fügt ein resistives Control (FAIR-CAM Resistance) hinzu."""
        self._controls.append(control)
        return self

    def susceptibility(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Berechnet die (kombinierte) Susceptibility über ``n`` Iterationen.

        Ohne Controls: 1.0. Mit Controls: Π (1 - OpEffᵢ).
        """
        if not self._controls:
            return np.ones(n)
        opeff_list = [c.operational_efficacy(n, rng) for c in self._controls]
        return combined_susceptibility(opeff_list)

    def calculate(self, n: int, rng: np.random.Generator) -> dict:
        """Führt die Modellrechnung durch und gibt alle Zwischengrößen zurück.

        Returns
        -------
        dict
            Schlüssel: ``tef``, ``susceptibility``, ``lef``, ``loss_magnitude``,
            ``risk`` – jeweils numpy-Arrays der Länge ``n``.
        """
        if self._tef is None or self._lm is None:
            raise ValueError("TEF und Loss Magnitude müssen gesetzt sein.")

        tef = self._tef.sample(n, rng)
        susc = self.susceptibility(n, rng)
        lef = tef * susc
        lm = self._lm.sample(n, rng)
        risk = lef * lm

        return {
            "tef": tef,
            "susceptibility": susc,
            "lef": lef,
            "loss_magnitude": lm,
            "risk": risk,
        }
