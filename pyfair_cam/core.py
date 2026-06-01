"""
core – Reine FAIR-CAM Kernformeln (vektorisiert, ohne Seiteneffekte).

Diese Funktionen bilden die mathematische Grundlage des Modells und sind
bewusst frei von Zufall/State, damit sie 1:1 gegen die Knowledge-Base
(01_FAIR_CAM_Core_Concepts.md) getestet werden können.

Alle Funktionen arbeiten elementweise auf numpy-Arrays *oder* Skalaren.
"""

import numpy as np


def reliability(variance_frequency, variance_duration):
    """
    Reliability (Rel) – Anteil der Zeit, in der ein Control im Soll-Zustand ist.

        Rel = (1 - VF/365) ^ VD

    Parameters
    ----------
    variance_frequency : array_like
        Wie oft pro Jahr das Control variant (defekt) wird.
    variance_duration : array_like
        Wie lange (in Tagen) das Control variant bleibt.

    Returns
    -------
    np.ndarray
        Reliability im Bereich [0, 1].
    """
    base = 1.0 - np.asarray(variance_frequency, dtype=float) / 365.0
    base = np.clip(base, 0.0, 1.0)
    return np.power(base, np.asarray(variance_duration, dtype=float))


def operational_efficacy(coverage, rel, intended_efficacy, variant_efficacy):
    """
    Operational Efficacy (OpEff) – tatsächliche Wirksamkeit über Zeit und Population.

        OpEff = Cov × [Rel × IntEff + (1 - Rel) × VarEff]

    Returns
    -------
    np.ndarray
        Operative Wirksamkeit im Bereich [0, 1].
    """
    cov = np.asarray(coverage, dtype=float)
    rel = np.asarray(rel, dtype=float)
    int_eff = np.asarray(intended_efficacy, dtype=float)
    var_eff = np.asarray(variant_efficacy, dtype=float)
    opeff = cov * (rel * int_eff + (1.0 - rel) * var_eff)
    return np.clip(opeff, 0.0, 1.0)


def combined_susceptibility(opeff_list):
    """
    Combined Susceptibility bei geschichtetem Widerstand (Defense-in-Depth, OR-Logik).

        Combined_Susc = Π (1 - OpEffᵢ)

    Parameters
    ----------
    opeff_list : list of np.ndarray
        Liste der Operational-Efficacy-Arrays je Resistive Control.

    Returns
    -------
    np.ndarray
        Verbleibende Susceptibility im Bereich [0, 1].
        Leere Liste → vollständig anfällig (1.0) ist Sache des Aufrufers;
        hier wird bei leerer Liste ein ValueError vermieden, indem der
        Aufrufer eine Basis vorgeben muss.
    """
    if not opeff_list:
        raise ValueError("combined_susceptibility benötigt mindestens ein OpEff-Array.")
    susc = np.ones_like(np.asarray(opeff_list[0], dtype=float))
    for opeff in opeff_list:
        susc = susc * (1.0 - np.asarray(opeff, dtype=float))
    return np.clip(susc, 0.0, 1.0)
