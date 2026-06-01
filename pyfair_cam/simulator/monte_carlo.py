"""
FairCamSimulator – Die Wurstmaschine 🌭

Monte-Carlo-Simulator für FAIR-CAM-Modelle.
Vektorisiert mit numpy für maximale Performance.

Reproduzierbarkeit:
    Der Simulator erzeugt aus ``seed`` *genau einen* ``numpy.random.Generator``
    und reicht ihn an das Modell durch. Alle Zufallsgrößen ziehen damit aus
    demselben, fortlaufenden Strom → unabhängige, reproduzierbare Samples.
    Es wird nie ``np.random.seed()`` (globaler Zustand) verwendet.
"""

import numpy as np
import pandas as pd
from typing import Optional


class FairCamSimulator:
    """Monte-Carlo-Simulator für FAIR-CAM-Modelle."""

    def __init__(self, n_simulations: int = 10_000, seed: Optional[int] = None):
        self.n_simulations = n_simulations
        self.seed = seed
        self._results = None      # np.ndarray der Risiko-Samples
        self._components = None    # dict mit allen Zwischengrößen

    def run(self, model) -> np.ndarray:
        """Startet die Simulation und gibt die Risiko-Samples zurück."""
        rng = np.random.default_rng(self.seed)
        self._components = model.calculate(self.n_simulations, rng)
        self._results = self._components["risk"]
        return self._results

    def get_results(self) -> np.ndarray:
        """Gibt die Risiko-Samples zurück."""
        if self._results is None:
            raise RuntimeError("Simulation wurde noch nicht ausgeführt. Bitte run() aufrufen.")
        return self._results

    def get_components(self) -> dict:
        """Gibt alle Zwischengrößen (tef, susceptibility, lef, lm, risk) zurück."""
        if self._components is None:
            raise RuntimeError("Simulation wurde noch nicht ausgeführt. Bitte run() aufrufen.")
        return self._components

    def get_statistics(self) -> dict:
        """Berechnet statistische Kennzahlen der Risiko-Samples."""
        r = self.get_results()
        return {
            'mean':   float(np.mean(r)),
            'median': float(np.median(r)),
            'stdev':  float(np.std(r)),
            'min':    float(np.min(r)),
            'max':    float(np.max(r)),
            'p10':    float(np.percentile(r, 10)),
            'p25':    float(np.percentile(r, 25)),
            'p50':    float(np.percentile(r, 50)),
            'p75':    float(np.percentile(r, 75)),
            'p90':    float(np.percentile(r, 90)),
            'p95':    float(np.percentile(r, 95)),
            'p99':    float(np.percentile(r, 99)),
        }

    def get_lec(self, n_points: int = 100) -> pd.DataFrame:
        """Berechnet die Loss Exceedance Curve (LEC)."""
        r = self.get_results()
        losses = np.linspace(r.min(), r.max(), n_points)
        exceedance = [float(np.mean(r >= loss)) for loss in losses]
        return pd.DataFrame({'loss': losses, 'exceedance_probability': exceedance})

    def get_ale(self) -> float:
        """Annual Loss Expectancy – Erwartungswert der Risiko-Samples."""
        return float(np.mean(self.get_results()))

    def get_var(self, confidence: float = 0.95) -> float:
        """Value at Risk – Perzentil der Risiko-Verteilung."""
        return float(np.percentile(self.get_results(), confidence * 100))

    def export_results(self) -> pd.DataFrame:
        """Exportiert die Kennzahlen als DataFrame."""
        return pd.DataFrame([self.get_statistics()])
