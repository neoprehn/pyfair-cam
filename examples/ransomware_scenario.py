"""
Beispiel – Ransomware-Szenario mit Detection & Response (Phase 2) 🌭

============================================================================
DAS SZENARIO IN WORTEN (für alle, die mit FAIR-CAM noch nicht firm sind)
============================================================================

Ein Angreifer versucht, das Unternehmen mit Ransomware zu treffen. Dazu muss
er sechs Schritte hintereinander schaffen (die "Kill Chain", Abschnitt 1):
sich zuerst Zugang verschaffen (Initial Access), sich festsetzen
(Persistence), sich höhere Rechte erschleichen (Priv Escalation), sich im
Netzwerk ausbreiten (Lateral Movement), Daten für die Erpressung
zusammentragen (Data Staging) und zuletzt verschlüsseln/erpressen
(Execution).

Nach JEDER Stufe gilt: entweder wird der Angreifer entdeckt (Ende der
Geschichte, mit Schaden je nachdem WIE FRÜH), oder er kommt unentdeckt eine
Stufe weiter, oder er scheitert von selbst (schlecht vorbereiteter Angriff,
Pech, etc.). Zwei Zufallsmechanismen konkurrieren also an jeder Stufe:
"werde ich erwischt?" vs. "komme ich weiter?".

Das Modell rechnet das über zwei FAIR-CAM-Bausteine:

  - Resistance (Phase 1, Frequenz-Seite): EIN "EDR / Anti-Malware"-Control
    senkt die Wahrscheinlichkeit, dass aus einem Angriffsversuch überhaupt
    ein Ereignis wird ("Susceptibility"). Wirkt VOR der Kill Chain.
  - Detection & Response (Phase 2, Schadenshöhen-Seite): bildet die Kill
    Chain selbst ab UND wie hoch der Schaden ausfällt, je nachdem, WANN
    (wenn überhaupt) der Angreifer erwischt wird. Je später die Entdeckung,
    desto größer der angerichtete Schaden.

    Risk = (TEF × Susceptibility) × LM
    LM   = stage-gated Detection/Response-Ergebnis (statt einer einzigen,
           immer gleich breiten Verlustverteilung)

----------------------------------------------------------------------------
1. Die sechs Kill-Chain-Stufen — 10 Parameter pro Stufe

Jede Stufe ist eine eigene "Chance", den Angreifer zu erwischen. Am Beispiel
von Stufe 1 ("Initial Access"):

  - coverage=0.95           : Auf 95% der relevanten Angriffsfläche gibt es
                              überhaupt eine Detection-Möglichkeit (Rest ist
                              blinder Fleck, z.B. nicht überwachte Systeme).
  - visibility=0.70         : WENN der Angreifer dort aktiv wird, entsteht in
                              70% der Fälle tatsächlich eine Spur/ein Log-
                              Eintrag, der das festhält.
  - vis_reliability=0.95    : Wie zuverlässig diese Log-/Telemetrie-Erfassung
                              selbst läuft (95% Betriebssicherheit).
  - recognition=0.40        : WENN eine Spur existiert, wird sie in 40% der
                              Fälle korrekt als bösartig erkannt (Analyst
                              oder Regel) statt übersehen/falsch eingeordnet.
  - rec_reliability=0.90    : Zuverlässigkeit dieser Erkennungslogik selbst.
  - monitoring_cadence=0.042: Alle ~0.042 Tage (≈ 1 Stunde) wird geprüft, ob
                              es Auffälligkeiten gibt (Review-Takt).
  - mon_reliability=0.95    : Zuverlässigkeit, dass dieser Review-Takt auch
                              eingehalten wird.
  - duration=0.25           : Der Angreifer hält sich in dieser Stufe im
                              Schnitt ~0.25 Tage (6 Std.) auf, bevor er
                              weiterzieht — das bestimmt, wie viele
                              Review-Gelegenheiten in dieser Zeit anfallen.
  - progression_probability=0.90: WENN nicht entdeckt, schafft der Angreifer
                              es in 90% der Fälle zur nächsten Stufe (in 10%
                              scheitert er von selbst -> "attacker_fails").
  - review_independence=0.40: Wie unabhängig aufeinanderfolgende Reviews
                              voneinander sind (0.40 = mittelmäßig
                              unabhängig; jeder weitere Blick bringt nicht
                              die volle zusätzliche Fangchance, weil viele
                              Reviews denselben blinden Fleck teilen).

Aus visibility×vis_reliability und recognition×rec_reliability ergibt sich
die "effektive" Sichtbarkeit/Erkennung; aus duration/monitoring_cadence/
mon_reliability die Anzahl echter Review-Gelegenheiten während der
Verweildauer. Daraus (plus coverage, review_independence) berechnet sich
P(Detect) für genau diese Stufe. Die anderen fünf Stufen funktionieren
identisch, nur mit stufentypischen Werten (z.B. Execution hat mit 0.85
etwas geringere Coverage, weil Verschlüsselungsvorgänge schwerer in Echtzeit
zu fassen sind als z.B. Persistence-Mechanismen).

----------------------------------------------------------------------------
2. Wer wird wann erwischt -> welche Schadensklasse?

  stage_outcome_map: Stufe 1-2 (Initial Access, Persistence) = "early",
  Stufe 3-4 (Priv Escalation, Lateral Movement) = "mid",
  Stufe 5-6 (Data Staging, Execution) = "late". Je später die Entdeckung,
  desto mehr konnte der Angreifer schon anrichten.

----------------------------------------------------------------------------
3. Wie hoch ist der Schaden je Klasse?

  - "early"          : € 2.000 – 30.000 (Modus 8.000)   — früh gestoppt
  - "mid"             : € 25.000 – 250.000 (Modus 75.000) — mittel
  - "late"            : € 200.000 – 2 Mio. (Modus 500.000) — spät erwischt
  - full_impact       : € 1 – 5 Mio. (Modus 3 Mio.)  — NIE erwischt, Angriff
                        läuft bis zum Ende durch (Verschlüsselung + Erpressung)
  - attacker_fails    : € 2.000 – 15.000 (Modus 5.000) — Angreifer scheitert
                        von selbst, irgendwo unterwegs (kleine Aufräumkosten)

  detection_response bündelt das Ganze und ergänzt zwei Zeitgrößen, die NUR
  fürs Reporting sind (fließen nicht in die Risikoberechnung ein):
  t_containment (Eindämmung, 1-10 Tage) und t_resilience (Wiederherstellung,
  2-21 Tage), verknüpft über "concurrency" (~0.4 = die beiden Prozesse
  laufen teils parallel statt rein nacheinander).

----------------------------------------------------------------------------
4. Die Frequenz-Seite: wie oft passiert überhaupt ein Angriffsversuch,
   und wie gut hält das EDR/Anti-Malware-Control dagegen?

  - Threat Event Frequency: 5-20× pro Jahr (Modus 10) versucht sich jemand
    an einem Ransomware-Angriff.
  - Das Control wehrt davon einen Teil ab, BEVOR die Kill Chain überhaupt
    beginnt (Resistance, Phase 1):
      - intended_efficacy=0.70-0.95 : Wirksamkeit im Normalbetrieb
      - variant_efficacy=0.02-0.25  : Rest-Wirksamkeit, wenn das Control
                                      gerade geschwächt/außer Takt ist
      - variance_frequency (Poisson, Rate 4/Jahr): wie oft im Jahr das
        passiert
      - variance_duration=2-10 Tage : wie lange so eine Schwächephase dauert
      - coverage=0.85-0.99          : Anteil der Systeme, die das Control
                                      überhaupt erreicht

  Nur was durch dieses Sieb kommt, löst überhaupt die Kill Chain (Abschnitt
  1-3) aus, deren Ausgang dann die tatsächliche Verlusthöhe bestimmt.

----------------------------------------------------------------------------
5. Was am Ende rausfällt

  20.000 Monte-Carlo-Durchläufe -> ALE (Erwartungswert), Median, VaR 95/99,
  eine Verteilung über die fünf Schadensklassen (zeigt z.B.: wie oft endet
  es als "full_impact"?), die Loss-Exceedance-Curve (LEC) und die mittlere
  Response-Zeit.
"""

import numpy as np

from pyfair_cam import (
    BetaPert,
    DetectionResponseFactor,
    FairCamModel,
    FairCamReport,
    FairCamSimulator,
    Poisson,
    ResistiveControl,
    Stage,
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
