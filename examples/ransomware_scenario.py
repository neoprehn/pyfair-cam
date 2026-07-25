"""
Beispiel – Ransomware-Szenario mit Detection & Response (Phase 2) 🌭

Zeigt das vollständige stage-gated Detection/Response-Modell aus
04_Detection_Response_Measurement.md: ein Angreifer durchläuft sechs
Kill-Chain-Stufen; an jeder Stufe entscheidet eine Monte-Carlo-Ziehung über
Erkennung oder Fortschritt. Die resultierende Outcome-Klasse (Early/Mid/Late
Detection, Full Impact, Attacker Fails) bestimmt die Verlusthöhe.

Kombiniert mit einem resistiven Control (Phase 1) auf der Frequenz-Seite:

    Risk = (TEF × Susceptibility) × LM
    LM   = stage-gated Detection/Response-Ergebnis (statt flacher Verteilung)
"""

import numpy as np

from pyfair_cam import (
    FairCamModel,
    FairCamSimulator,
    BetaPert,
    Poisson,
    ResistiveControl,
    Stage,
    DetectionResponseFactor,
    FairCamReport,
)

# 1. Sechs Kill-Chain-Stufen (Parameter aus dem KB-Beispiel:
#    04_Detection_Response_Measurement.md, "Worked Example: Ransomware Attack")
stages = [
    Stage(
        name="Initial Access", coverage=0.95, visibility=0.70, vis_reliability=0.95,
        recognition=0.40, rec_reliability=0.90, monitoring_cadence=0.042,
        mon_reliability=0.95, duration=0.25, progression_probability=0.90,
        review_independence=0.40,
    ),
    Stage(
        name="Persistence", coverage=0.98, visibility=0.85, vis_reliability=0.95,
        recognition=0.60, rec_reliability=0.92, monitoring_cadence=0.042,
        mon_reliability=0.95, duration=0.50, progression_probability=0.85,
        review_independence=0.55,
    ),
    Stage(
        name="Priv Escalation", coverage=0.96, visibility=0.80, vis_reliability=0.94,
        recognition=0.75, rec_reliability=0.90, monitoring_cadence=0.042,
        mon_reliability=0.94, duration=0.50, progression_probability=0.80,
        review_independence=0.60,
    ),
    Stage(
        name="Lateral Movement", coverage=0.92, visibility=0.90, vis_reliability=0.96,
        recognition=0.65, rec_reliability=0.88, monitoring_cadence=0.042,
        mon_reliability=0.92, duration=1.00, progression_probability=0.75,
        review_independence=0.65,
    ),
    Stage(
        name="Data Staging", coverage=0.88, visibility=0.75, vis_reliability=0.92,
        recognition=0.55, rec_reliability=0.85, monitoring_cadence=0.042,
        mon_reliability=0.90, duration=0.75, progression_probability=0.70,
        review_independence=0.50,
    ),
    Stage(
        name="Execution", coverage=0.85, visibility=0.60, vis_reliability=0.90,
        recognition=0.45, rec_reliability=0.80, monitoring_cadence=0.042,
        mon_reliability=0.88, duration=0.25, progression_probability=0.95,
        review_independence=0.45,
    ),
]

# 2. Stufen 1-2 -> Early Detection, 3-4 -> Mid, 5-6 -> Late (vgl. KB "Outcome Class Summary")
stage_outcome_map = {1: "early", 2: "early", 3: "mid", 4: "mid", 5: "late", 6: "late"}

# 3. Bedingte Verlustverteilungen je Outcome-Klasse (PERT: low, mode, high aus der KB-Tabelle)
loss_distributions = {
    "early": BetaPert(low=2_000, mode=8_000, high=30_000),
    "mid": BetaPert(low=25_000, mode=75_000, high=250_000),
    "late": BetaPert(low=200_000, mode=500_000, high=2_000_000),
    DetectionResponseFactor.FULL_IMPACT: BetaPert(low=1_000_000, mode=3_000_000, high=5_000_000),
    DetectionResponseFactor.ATTACKER_FAILS: BetaPert(low=2_000, mode=5_000, high=15_000),
}

detection_response = DetectionResponseFactor(
    name="Ransomware Kill-Chain",
    stages=stages,
    stage_outcome_map=stage_outcome_map,
    loss_distributions=loss_distributions,
    t_containment=BetaPert(low=1, mode=3, high=10),
    t_resilience=BetaPert(low=2, mode=7, high=21),
    concurrency=BetaPert(low=0.2, mode=0.4, high=0.6),
)

# 4. Modell: Threat Event Frequency + Resistive Control (Frequenz-Seite, Phase 1)
#    + Detection/Response (Loss-Magnitude-Seite, Phase 2) statt flacher LM.
model = FairCamModel(name="Ransomware Szenario", n_simulations=20_000)
model.input_threat_frequency(BetaPert(low=5, mode=10, high=20))
model.add_resistive_control(
    ResistiveControl(
        name="EDR / Anti-Malware",
        # Alle Verteilungen auf "moderate" Konfidenz (siehe pyfair
        # confidence_mapping.py: pert gamma=4 [Default], poisson range=0.4).
        intended_efficacy=BetaPert(low=0.70, mode=0.85, high=0.95),
        variant_efficacy=BetaPert(low=0.02, mode=0.10, high=0.25),
        variance_frequency=Poisson(lam=4, range_=0.4),
        variance_duration=BetaPert(low=2, mode=5, high=10),
        coverage=BetaPert(low=0.85, mode=0.95, high=0.99),
    )
)
model.set_detection_response(detection_response)

# 5. Simulation
simulator = FairCamSimulator(n_simulations=20_000, seed=42)
simulator.run(model)

report = FairCamReport(simulator)
report.print_summary()

# 6. Outcome-Klassen-Verteilung (Diagnose, noch nicht Teil des Reports – Phase 4)
components = simulator.get_components()
outcome_class = components["outcome_class"]
print("Outcome-Klassen-Verteilung:")
for cls in ["early", "mid", "late", DetectionResponseFactor.FULL_IMPACT, DetectionResponseFactor.ATTACKER_FAILS]:
    share = float(np.mean(outcome_class == cls))
    print(f"  {cls:>16}: {share:6.2%}")

lec = report.get_lec()
print("\nLoss Exceedance Curve (erste 5 Zeilen):")
print(lec.head())

# 7. Response-Zeit separat (Reporting-only, nicht Teil der Risk-Berechnung)
rt = detection_response.response_time(20_000, np.random.default_rng(42))
print(f"\nMittlere Response-Zeit (Containment+Resilience, Concurrency ~0.4): {rt.mean():.1f} Tage")
