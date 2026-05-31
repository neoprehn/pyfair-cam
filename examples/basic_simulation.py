"""
Beispiel – Einfache FAIR-CAM Simulation (Wurstmaschine)

Zeigt wie man ein FAIR-CAM Modell aufbaut und simuliert.
"""

from pyfair_cam import (
    FairCamModel,
    FairCamSimulator,
    BetaPert,
    LogNormal,
    ResistanceFactor,
    SusceptibilityFactor,
    FairCamReport
)

# 1. Modell erstellen
model = FairCamModel(name="Ransomware Szenario", n_simulations=10_000)

# 2. Bedrohungshäufigkeit – 5 bis 20 Events pro Jahr
model.input_threat_frequency(
    BetaPert(low=5, mode=10, high=20)
)

# 3. Verlusthöhe – 50k bis 2M EUR pro Event
model.input_loss_magnitude(
    LogNormal(mean=200_000, stdev=150_000)
)

# 4. FAIR-CAM Faktoren hinzufügen
model.add_factor(
    'resistance',
    ResistanceFactor(BetaPert(low=0.3, mode=0.6, high=0.9))
)
model.add_factor(
    'susceptibility',
    SusceptibilityFactor(BetaPert(low=0.1, mode=0.3, high=0.6))
)

# 5. Wurstmaschine starten
simulator = FairCamSimulator(n_simulations=10_000, seed=42)
simulator.run(model)

# 6. Report erstellen
report = FairCamReport(simulator)
report.print_summary()

# 7. LEC Daten
lec = report.get_lec()
print("Loss Exceedance Curve (erste 5 Zeilen):")
print(lec.head())
