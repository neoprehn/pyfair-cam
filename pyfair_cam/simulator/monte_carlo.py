"""
FairCamSimulator – Die Wurstmaschine 🌭

Monte Carlo Simulator für FAIR-CAM Faktoren.
Vektorisiert mit numpy für maximale Performance.
"""

import numpy as np
import pandas as pd
from typing import Optional


class FairCamSimulator:
    """
    Monte Carlo Simulator für FAIR-CAM Modelle.

    Eigenschaften:
    - Vektorisiert (numpy) – kein Python-Loop
    - Reproduzierbar (Seed-basiert)
    - Konfigurierbare Anzahl Simulationen
    - Berechnet LEC, ALE, VaR und Perzentile
    """

    def __init__(self, n_simulations: int = 10_000, seed: Optional[int] = None):
        self.n_simulations = n_simulations
        self.seed = seed
        self._results = None

    def run(self, model) -> np.ndarray:
        """Hauptmethode – startet die Simulation."""
        if self.seed is not None:
            np.random.seed(self.seed)
        self._results = model.calculate(self.n_simulations, self.seed)
        return self._results

    def get_results(self) -> np.ndarray:
        """Gibt die Simulationsergebnisse zurück."""
        if self._results is None:
            raise RuntimeError("Simulation wurde noch nicht ausgeführt. Bitte run() aufrufen.")
        return self._results

    def get_statistics(self) -> dict:
        """Berechnet statistische Kennzahlen der Ergebnisse."""
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
        """
        Berechnet die Loss Exceedance Curve (LEC).
        Gibt DataFrame mit Verlusthöhe und Überschreitungswahrscheinlichkeit zurück.
        """
        r = self.get_results()
        losses = np.linspace(r.min(), r.max(), n_points)
        exceedance = [np.mean(r >= loss) for loss in losses]
        return pd.DataFrame({'loss': losses, 'exceedance_probability': exceedance})

    def get_ale(self) -> float:
        """Annual Loss Expectancy – Erwartungswert der Verluste."""
        return float(np.mean(self.get_results()))

    def get_var(self, confidence: float = 0.95) -> float:
        """Value at Risk – Verlust der mit (1-confidence) Wahrscheinlichkeit überschritten wird."""
        return float(np.percentile(self.get_results(), confidence * 100))

    def export_results(self) -> pd.DataFrame:
        """Exportiert alle Ergebnisse als DataFrame."""
        stats = self.get_statistics()
        return pd.DataFrame([stats])
