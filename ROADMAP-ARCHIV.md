# pyfair-cam — Archiv (erledigte Phasen)

Diese Datei sammelt abgeschlossene Roadmap-Punkte, damit `ROADMAP.md` schlank
bleibt und nur noch offene Arbeit zeigt. Historischer Kontext, keine
Handlungsanweisung.

---

### Ausgangslage (Stand: Scaffold, vor Phase 0)

**Vorhanden & brauchbar:**
- Verteilungen (`BetaPert`, `LogNormal`, `Normal`, `Uniform`, `Poisson`, `Bernoulli`) — solide
- Architektur: Faktoren als Pipeline, erweiterbar
- Knowledge-Base vollständig (10 MD-Dateien), sauber lizenziert (CC BY-NC-ND 4.0)

**Kritische Lücken (durch Phase 0/1 behoben):**
1. **Seed-Bug:** `np.random.seed(seed)` wurde bei *jedem* `.sample()` neu gesetzt →
   TEF/LM/Resistance teilten denselben Zufallsstrom → korrelierte, verfälschte Samples.
2. **Falsche Mathematik:** `cam_model` rechnete `TEF × LM × (1−resistance)`.
   Resistance gehört in die **Susceptibility** (Frequenz-Seite), nicht als
   Multiplikator auf die Magnitude.
3. **Kernformeln fehlten:** kein `Rel`, `OpEff`, `Cov`, `Susc = 1−OpEff`,
   keine AND/OR-Boolean-Logik, kein stage-gated Detection-Modell.
4. **Keine echte pyfair-Integration:** pyfair war als Dependency genannt, aber
   `cam_model` baute eine eigene Mini-Engine statt pyfair zu nutzen.
5. **Testabdeckung:** nur ein `test_model.py`.

---

### Phase 0 — Fundament & Korrektur (Basis)

Ziel: Der bestehende Code rechnet *korrekt* und reproduzierbar, bevor Features kommen.

- [x] **Seed/RNG-Refactor:** `np.random.default_rng(seed)` zentral im Simulator erzeugt,
      an alle `.sample(n, rng)`-Aufrufe durchgereicht. Kein `np.random.seed()` mehr.
- [x] **Distribution-Interface vereinheitlicht:** alle Verteilungen `sample(n, rng)`,
      gemeinsame Basisklasse `Distribution`, Skalar→`PointEstimate`-Helfer.
- [x] **Unabhängigkeit hergestellt:** pyfair-Dependency entfernt (`requirements.txt`).
- [x] **Statistik-Tests:** Seed-Reproduzierbarkeit, verschiedene Seeds unterscheiden sich,
      TEF/LM-Unkorreliertheit (corr < 0.05) → Seed-Bug nachweislich behoben.

**Status:** `pytest` grün (19 Tests), RNG reproduzierbar & statistisch sauber.
Offener Rest (CI) steht in `ROADMAP.md`.

---

### Phase 1 — FAIR-CAM Rechenkern (Herzstück) ✅ ERLEDIGT

Ziel: Die FAIR-CAM-Kernformeln korrekt, getestet, dokumentiert.

- [x] **`ResistiveControl`-Datenmodell:** `IntEff`, `VarEff`, `VF`, `VD`, `Cov`
      je Control (jeweils Skalar oder Distribution).
- [x] **Reliability:** `Rel = (1 − VF/365)^VD` → `core.reliability()`
- [x] **Operational Efficacy:** `OpEff = Cov × [Rel×IntEff + (1−Rel)×VarEff]`
      → `core.operational_efficacy()`
- [x] **Defense-in-Depth (Resistance, OR-Logik):**
      `Combined_Susc = Π (1 − OpEffᵢ)` → `core.combined_susceptibility()`
- [x] **Korrekte Modellkette:** `Risk = (TEF × Susc) × LM`; Resistance wirkt auf
      Susceptibility (Frequenz-Seite), NICHT auf die LM.
- [x] **Unit-Tests gegen Knowledge-Base-Formeln** (`tests/test_core.py`).
- [x] **Boolean-Control-Logik vervollständigen:** Detection = AND
      (Visibility ∧ Monitoring ∧ Recognition); umgesetzt in Phase 2 über
      `P(Detect) = Cov × V_eff × [...]` (Coverage/Visibility/Recognition
      multiplizieren sich, die AND-Semantik ist in der Formel selbst kodiert).

**Status:** Resistance/Prevention-Mathematik vollständig & getestet.
Detection/Response (AND-Logik) umgesetzt in Phase 2.

---

### Phase 2 — Detection & Response (Loss-Magnitude-Seite) ✅ ERLEDIGT

Ziel: Detection/Response wirken korrekt auf die Loss Magnitude (stage-gated).

- [x] **Stage-gated Detection-Modell** (Kill-Chain-Stufen mit Stage-Parametern):
      `Stage`-Klasse (`factors/detection_response.py`), 10 Parameter je Stage
      (Cov/V/Rel_V/R/Rel_R/M/Rel_M/τ/P/ρ), Skalar-oder-Distribution wie bei
      `ResistiveControl`.
- [x] **Multi-Review-Detection:**
      `λ = τ / (M/Rel_M)`,
      `P(Detect) = Cov × V_eff × [1 − (1 − R_eff)^(ρ×λ)]`
      inkl. ρ=0-Sonderfall (echter Sprung, kein Grenzwert) →
      `core.reviews_per_stage`, `core.stage_detection_probability`.
- [x] **Cumulative Progression:** `P(Reach_i) = P(Reach_{i-1}) × [1−P(Detect_{i-1})] × P_{i-1}`
      → `core.progression_reach_probability`, in `DetectionResponseFactor.simulate()`
      als per-Trial-Bernoulli-Walk über die Stages (nicht als geschlossene Form –
      siehe KB-Warnung zur Nichtlinearität von Loss-Minimization).
- [x] **Conditional Magnitude Distributions:**
      Outcome-Klassen (konfigurierbar, z.B. Early/Mid/Late/Full/Attacker-Fails) →
      pro Trial wird aus der zur Outcome-Klasse passenden Verteilung gezogen
      (`DetectionResponseFactor` sampelt alle Klassenverteilungen immer
      vollständig, Auswahl per Maske – hält den RNG-Strom deterministisch).
- [x] **Response Time mit Concurrency:**
      `T = T_containment + T_resilience − α × min(...)` → `core.response_time`,
      `DetectionResponseFactor.response_time()` (Reporting-only, nicht im Risk-Pfad).
- [x] **Detection-SLO-Alignment:** `P(Detect within T)` → `core.detection_within_time`
      (Reporting-only).
- [x] **`DetectionResponseFactor` implementiert** (`set_detection_response()` in
      `FairCamModel`, schließt sich mit `input_loss_magnitude()` aus).
- [x] Tests gegen `04_Detection_Response_Measurement.md` (`test_core.py`,
      `test_detection_response.py`, `test_model.py`; 52 Tests grün).

**Status:** Rechenkern vollständig & getestet. Beim Nachrechnen des KB-eigenen
6-Stufen-Ransomware-Beispiels reproduzieren Stage 1 und 6 ihre eigenen
P(Detect)-Zahlen nicht exakt aus Formel+Tabelle (Stufen 2–5 passen exakt) –
die Implementierung folgt bewusst der dokumentierten Formel wörtlich statt der
abgedruckten Beispielzahlen (Entscheidung mit @neoprehn abgestimmt); die
Outcome-Klassen-Wahrscheinlichkeiten am Ende der Kaskade weichen dadurch nur
~0.5–0.9pp von den KB-Kopfzahlen ab. Frontend-Anbindung bewusst noch nicht
begonnen (kommt erst mit Phase 5, nach Phase 3/4).
