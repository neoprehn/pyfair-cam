"""
ResistiveControl – FAIR-CAM Resistive Control (Prevention/Resistance-Funktion).

Ein resistives Control reduziert die Wahrscheinlichkeit, dass ein Threat-Event
zu einem Loss-Event wird (FAIR-CAM: Resistance → wirkt auf die *Frequenz-Seite*
über die Susceptibility, NICHT auf die Loss Magnitude).

Jedes Control wird über fünf Parameter beschrieben (vgl. 01_FAIR_CAM_Core_Concepts):
    - intended_efficacy (IntEff) : Wirksamkeit im Soll-Zustand           [0..1]
    - variant_efficacy  (VarEff) : Rest-Wirksamkeit im Variant-Zustand   [0..1]
    - variance_frequency (VF)    : Variant-Häufigkeit pro Jahr           [/Jahr]
    - variance_duration  (VD)    : Variant-Dauer in Tagen                [Tage]
    - coverage          (Cov)    : Anteil der abgedeckten Population     [0..1]

Daraus berechnet das Control je Monte-Carlo-Iteration seine Operational
Efficacy (OpEff). Mehrere Controls werden im Modell über die OR-Logik
(Defense-in-Depth) zu einer kombinierten Susceptibility verrechnet.
"""

import numpy as np

from ..core import reliability, operational_efficacy
from ..simulator.distributions import as_distribution


class ResistiveControl:
    """Ein einzelnes resistives Control mit FAIR-CAM-Parametern.

    Alle Parameter dürfen entweder ein fester Wert (Skalar) oder eine
    Distribution sein. Skalare werden intern zu Punktschätzungen.
    """

    def __init__(
        self,
        name: str,
        intended_efficacy,
        variant_efficacy=0.0,
        variance_frequency=0.0,
        variance_duration=0.0,
        coverage=1.0,
    ):
        self.name = name
        self.intended_efficacy = as_distribution(intended_efficacy)
        self.variant_efficacy = as_distribution(variant_efficacy)
        self.variance_frequency = as_distribution(variance_frequency)
        self.variance_duration = as_distribution(variance_duration)
        self.coverage = as_distribution(coverage)

    def operational_efficacy(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Berechnet OpEff über ``n`` Monte-Carlo-Iterationen.

        OpEff = Cov × [Rel × IntEff + (1 - Rel) × VarEff]
        mit    Rel = (1 - VF/365) ^ VD
        """
        int_eff = np.clip(self.intended_efficacy.sample(n, rng), 0.0, 1.0)
        var_eff = np.clip(self.variant_efficacy.sample(n, rng), 0.0, 1.0)
        vf = self.variance_frequency.sample(n, rng)
        vd = self.variance_duration.sample(n, rng)
        cov = np.clip(self.coverage.sample(n, rng), 0.0, 1.0)

        rel = reliability(vf, vd)
        return operational_efficacy(cov, rel, int_eff, var_eff)
