"""
FairCamReport – Einfacher Report für FAIR-CAM Simulationsergebnisse.
"""

import pandas as pd


class FairCamReport:
    """Erstellt Reports aus FairCamSimulator Ergebnissen."""

    def __init__(self, simulator):
        self.simulator = simulator

    def get_summary(self) -> pd.DataFrame:
        """Gibt eine Zusammenfassung der Simulationsergebnisse zurück."""
        return self.simulator.export_results()

    def get_lec(self) -> pd.DataFrame:
        """Gibt die Loss Exceedance Curve zurück."""
        return self.simulator.get_lec()

    def print_summary(self):
        """Gibt eine lesbare Zusammenfassung aus."""
        stats = self.simulator.get_statistics()
        print(f"\n{'='*50}")
        print(f"  FAIR-CAM Simulationsergebnisse")
        print(f"{'='*50}")
        components = self.simulator.get_components()
        mean_susc = float(components['susceptibility'].mean())
        mean_lef = float(components['lef'].mean())
        print(f"  Mittlere Susceptibility: {mean_susc:.1%}")
        print(f"  Mittlere LEF:            {mean_lef:.2f} Loss-Events/Jahr")
        print(f"  ALE (Erwartungswert):  € {stats['mean']:,.0f}")
        print(f"  Median:                € {stats['median']:,.0f}")
        print(f"  VaR 95%:               € {stats['p95']:,.0f}")
        print(f"  VaR 99%:               € {stats['p99']:,.0f}")
        print(f"  Min:                   € {stats['min']:,.0f}")
        print(f"  Max:                   € {stats['max']:,.0f}")
        print(f"{'='*50}\n")
