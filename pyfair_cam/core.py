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


# ---------------------------------------------------------------------------
# Detection & Response (Loss-Magnitude-Seite, FAIR-CAM Phase 2)
# vgl. 04_Detection_Response_Measurement.md
# ---------------------------------------------------------------------------


def effective_parameter(raw, rel):
    """
    Effektiver Stage-Parameter – Reliability degradiert den Soll-Wert.

        V_eff = V × Rel_V   bzw.   R_eff = R × Rel_R

    Identische Formel für Visibility und Recognition, daher eine gemeinsame
    Funktion für beide Anwendungsfälle.
    """
    return np.clip(np.asarray(raw, dtype=float) * np.asarray(rel, dtype=float), 0.0, 1.0)


def reviews_per_stage(duration, monitoring_cadence, monitoring_reliability):
    """
    Anzahl Reviews während des Stage-Aufenthalts (λ).

        λ = τ / (M / Rel_M)

    Parameters
    ----------
    duration : array_like
        Erwartete Verweildauer des Angreifers in der Stage (Tage, τ).
    monitoring_cadence : array_like
        Zeit zwischen Evidenz-Reviews (Tage, M).
    monitoring_reliability : array_like
        Anteil der Zeit, in der Monitoring planmäßig läuft (Rel_M).
    """
    m_eff = np.asarray(monitoring_cadence, dtype=float) / np.asarray(monitoring_reliability, dtype=float)
    return np.asarray(duration, dtype=float) / m_eff


def stage_detection_probability(coverage, v_eff, r_eff, rho, lam):
    """
    Detection-Wahrscheinlichkeit einer Stage bei mehreren Reviews.

        P(Detect) = Cov × V_eff × [1 - (1 - R_eff)^(ρ×λ)]

    Sonderfall ρ = 0 (vollständig deterministische Detection):

        P(Detect) = Cov × V_eff × R_eff

    Das ist laut Knowledge-Base ein echter Sprung an der Grenze ρ = 0
    (kein Grenzwert der allgemeinen Formel – bei ρ=0 würde die allgemeine
    Formel [1-(1-R_eff)^0] = 0 liefern), daher die explizite Fallunterscheidung.

    Returns
    -------
    np.ndarray
        P(Detect) im Bereich [0, Cov×V_eff] (mathematische Obergrenze:
        Detection kann die Visibility-Deckelung nie überschreiten).
    """
    cov = np.asarray(coverage, dtype=float)
    v_eff = np.clip(np.asarray(v_eff, dtype=float), 0.0, 1.0)
    r_eff = np.clip(np.asarray(r_eff, dtype=float), 0.0, 1.0)
    rho = np.asarray(rho, dtype=float)
    lam = np.asarray(lam, dtype=float)

    general = 1.0 - np.power(1.0 - r_eff, rho * lam)
    bracket = np.where(rho == 0.0, r_eff, general)
    ceiling = cov * v_eff
    return np.clip(cov * v_eff * bracket, 0.0, ceiling)


def progression_reach_probability(prev_reach, prev_p_detect, prev_progression):
    """
    Wahrscheinlichkeit, die nächste Stage unentdeckt zu erreichen.

        P(Reach_i) = P(Reach_{i-1}) × [1 - P(Detect_{i-1})] × P_{i-1}
    """
    return (
        np.asarray(prev_reach, dtype=float)
        * (1.0 - np.asarray(prev_p_detect, dtype=float))
        * np.asarray(prev_progression, dtype=float)
    )


def response_time(t_containment, t_resilience, concurrency):
    """
    Response-Zeit unter Berücksichtigung von Überlappung (Concurrency).

        T_response = T_containment + T_resilience - α × min(T_containment, T_resilience)

    α=0 → vollständig sequenziell, α=1 → vollständig parallel.
    """
    tc = np.asarray(t_containment, dtype=float)
    ts = np.asarray(t_resilience, dtype=float)
    alpha = np.clip(np.asarray(concurrency, dtype=float), 0.0, 1.0)
    return tc + ts - alpha * np.minimum(tc, ts)


def pert_mean(low, mode, high, gamma=4.0):
    """Erwartungswert einer PERT-Verteilung: E[X] = (low + γ×mode + high) / (γ+2)."""
    low = np.asarray(low, dtype=float)
    mode = np.asarray(mode, dtype=float)
    high = np.asarray(high, dtype=float)
    return (low + gamma * mode + high) / (gamma + 2.0)


def expected_gross_loss(class_probabilities, class_means):
    """
    Erwarteter Bruttoverlust (Reporting-Kennzahl, NICHT Teil des Risk-MC-Pfads):

        E[Loss_gross] = Σ P(class) × E[LM_class]

    Wichtig: Diese geschlossene Form eignet sich nur zum Reporting. Der
    eigentliche Risk-Pfad muss pro Trial simuliert werden (siehe KB-Warnung
    zur Nichtlinearität von Loss-Minimization/Versicherungs-Deckeln).
    """
    p = np.asarray(class_probabilities, dtype=float)
    m = np.asarray(class_means, dtype=float)
    return float(np.dot(p, m))


def detection_within_time(coverage, v_eff, r_eff, rho, monitoring_cadence,
                           monitoring_reliability, time_budget):
    """
    Detection-SLO-Alignment: P(Detect innerhalb eines Zeitbudgets T).

    Identisch zu ``stage_detection_probability``, nur dass λ auf Basis eines
    Zeitbudgets ``time_budget`` statt der vollen Stage-Dauer τ berechnet wird
    (z.B. "Erkennung von Initial Access innerhalb von 4 Stunden?"). Reines
    Reporting – nicht Teil von ``FairCamModel.calculate()``.
    """
    lam_t = reviews_per_stage(time_budget, monitoring_cadence, monitoring_reliability)
    return stage_detection_probability(coverage, v_eff, r_eff, rho, lam_t)
