"""
FairCamModel – FAIR-CAM Hauptmodell (Frequenz- und Loss-Magnitude-Seite).

Modelliert Risiko nach der FAIR/FAIR-CAM-Taxonomie:

    Risk = LEF × LM
    LEF  = TEF × Susceptibility
    Susceptibility = Π (1 - OpEffᵢ)      über alle resistiven Controls (OR-Logik)

Wichtig (FAIR-CAM-konform):
    - Resistive Controls wirken auf die *Frequenz-Seite* (Susceptibility),
      NICHT als Multiplikator auf die Loss Magnitude.
    - Ohne Controls ist Susceptibility = 1.0 (jedes Threat-Event wird zum Loss-Event).
    - Die Loss Magnitude kommt entweder aus einer flachen Verteilung
      (``input_loss_magnitude``) oder aus einem stage-gated Detection/Response-
      Modell (``set_detection_response``) – beide schließen sich gegenseitig aus.

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
        self._detection_response = None
        self._controls = []

    def input_threat_frequency(self, distribution):
        """Setzt die Threat Event Frequency (TEF), Events pro Jahr."""
        self._tef = as_distribution(distribution)
        return self

    def input_loss_magnitude(self, distribution):
        """Setzt die Loss Magnitude (LM) pro Loss-Event.

        Schließt sich mit ``set_detection_response`` aus.
        """
        if self._detection_response is not None:
            raise ValueError(
                "input_loss_magnitude() und set_detection_response() schließen sich "
                "gegenseitig aus."
            )
        self._lm = as_distribution(distribution)
        return self

    def set_detection_response(self, factor):
        """Setzt ein stage-gated Detection/Response-Modell (``DetectionResponseFactor``)
        als Quelle der Loss Magnitude.

        Schließt sich mit ``input_loss_magnitude`` aus.
        """
        if self._lm is not None:
            raise ValueError(
                "set_detection_response() und input_loss_magnitude() schließen sich "
                "gegenseitig aus."
            )
        self._detection_response = factor
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
            ``risk`` – jeweils numpy-Arrays der Länge ``n``. Ist ein
            ``DetectionResponseFactor`` gesetzt, zusätzlich ``outcome_class``
            und ``detected_at_stage``.
        """
        if self._tef is None:
            raise ValueError("TEF muss gesetzt sein.")
        if self._lm is None and self._detection_response is None:
            raise ValueError("LM oder DetectionResponseFactor müssen gesetzt sein.")

        tef = self._tef.sample(n, rng)
        susc = self.susceptibility(n, rng)
        lef = tef * susc

        result = {"tef": tef, "susceptibility": susc, "lef": lef}

        if self._detection_response is not None:
            dr = self._detection_response.simulate(n, rng)
            lm = dr["loss_magnitude"]
            result["outcome_class"] = dr["outcome_class"]
            result["detected_at_stage"] = dr["detected_at_stage"]
        else:
            lm = self._lm.sample(n, rng)

        result["loss_magnitude"] = lm
        result["risk"] = lef * lm
        return result

    def to_pyfair(self, mode="vuln", n_simulations=None, random_seed=42):
        """Baut ein pyfair-``FairModel`` aus diesem CAM-Modell.

        Dünner Wrapper um :func:`pyfair_cam.adapter.to_pyfair`. Benötigt das
        optionale ``pyfair``-Paket (Extra ``pyfair-cam[pyfair]``) – siehe
        dort für Details, Parameter und Rückgabewert.
        """
        from ..adapter.to_pyfair import to_pyfair as _to_pyfair

        return _to_pyfair(
            self, mode=mode, n_simulations=n_simulations, random_seed=random_seed
        )
