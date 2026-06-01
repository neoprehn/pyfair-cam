"""
Beispiel – FAIR-CAM Simulation (Frequenz-Seite) 🌭

Zeigt den korrekten FAIR-CAM-Aufbau:
    Risk = (TEF × Susceptibility) × LM
mit Susceptibility = Π (1 - OpEffᵢ) über die resistiven Controls.
"""

from pyfair_cam import (
    FairCamModel,
    FairCamSimulator,
    BetaPert,
    LogNormal,
    ResistiveControl,
    FairCamReport,
)

# 1. Modell: Ransomware-Szenario
model = FairCamModel(name="Ransomware Szenario", n_simulations=10_000)

# 2. Threat Event Frequency – 5 bis 20 Threat-Events pro Jahr
model.input_threat_frequency(BetaPert(low=5, mode=10, high=20))

# 3. Loss Magnitude – ~200k EUR pro Loss-Event (rechts-schief)
model.input_loss_magnitude(LogNormal(mean=200_000, stdev=150_000))

# 4. Resistive Controls (FAIR-CAM Resistance → wirkt auf Susceptibility)
#    EDR/Anti-Malware: stark im Soll, fällt aber gelegentlich aus.
model.add_resistive_control(
    ResistiveControl(
        name="EDR / Anti-Malware",
        intended_efficacy=BetaPert(low=0.70, mode=0.85, high=0.95),
        variant_efficacy=0.10,        # Rest-Schutz im Ausfall
        variance_frequency=4,          # 4× pro Jahr variant
        variance_duration=5,           # je 5 Tage
        coverage=0.95,                 # 95 % der Systeme abgedeckt
    )
)
#    MFA / Zugriffsbeschränkung: binäres, sehr zuverlässiges Control.
model.add_resistive_control(
    ResistiveControl(
        name="MFA / Access Control",
        intended_efficacy=BetaPert(low=0.60, mode=0.75, high=0.90),
        variant_efficacy=0.0,
        variance_frequency=1,
        variance_duration=2,
        coverage=0.90,
    )
)

# 5. Simulation (zentraler, reproduzierbarer RNG via seed)
simulator = FairCamSimulator(n_simulations=10_000, seed=42)
simulator.run(model)

# 6. Report
report = FairCamReport(simulator)
report.print_summary()

lec = report.get_lec()
print("Loss Exceedance Curve (erste 5 Zeilen):")
print(lec.head())
