# pyfair-cam — Entwicklungsroadmap

> **Ziel:** Eigenständige Python-Library für FAIR-CAM (Controls Analytics Model),
> die — analog zu `pyfair` — lokal lauffähig ist und einen eigenen HTML-Report
> erzeugt. Web-Integration in `fair.neoprehn.de` (fair-web) erfolgt **danach**.
>
> **Engine-Strategie (aktualisiert):** pyfair-cam ist eine **eigenständige,
> unabhängige Bibliothek** mit eigener Monte-Carlo-Engine. KEINE pyfair-Dependency.
> Die Integration von FAIR und FAIR-CAM erfolgt erst auf Anwendungsebene in
> **fair-web** (fair.neoprehn.de), nicht in dieser Library.

---

## Ausgangslage (Stand: Scaffold)

**Vorhanden & brauchbar:**
- Verteilungen (`BetaPert`, `LogNormal`, `Normal`, `Uniform`, `Poisson`, `Bernoulli`) — solide
- Architektur: Faktoren als Pipeline, erweiterbar
- Knowledge-Base vollständig (10 MD-Dateien), sauber lizenziert (CC BY-NC-ND 4.0)

**Kritische Lücken (vor Feature-Arbeit zu beheben):**
1. **Seed-Bug:** `np.random.seed(seed)` wird bei *jedem* `.sample()` neu gesetzt →
   TEF/LM/Resistance teilen denselben Zufallsstrom → korrelierte, verfälschte Samples.
   → Umstellung auf `np.random.Generator` (rng), einmalig erzeugt und durchgereicht.
2. **Falsche Mathematik:** `cam_model` rechnet `TEF × LM × (1−resistance)`.
   Resistance gehört in die **Susceptibility** (Frequenz-Seite), nicht als
   Multiplikator auf die Magnitude.
3. **Kernformeln fehlen:** kein `Rel`, `OpEff`, `Cov`, `Susc = 1−OpEff`,
   keine AND/OR-Boolean-Logik, kein stage-gated Detection-Modell.
4. **Keine echte pyfair-Integration:** pyfair ist als Dependency genannt, aber
   `cam_model` baut eine eigene Mini-Engine statt pyfair zu nutzen.
5. **Testabdeckung:** nur ein `test_model.py`.

---

## Phase 0 — Fundament & Korrektur (Basis) ✅ ERLEDIGT

Ziel: Der bestehende Code rechnet *korrekt* und reproduzierbar, bevor Features kommen.

- [x] **Seed/RNG-Refactor:** `np.random.default_rng(seed)` zentral im Simulator erzeugt,
      an alle `.sample(n, rng)`-Aufrufe durchgereicht. Kein `np.random.seed()` mehr.
- [x] **Distribution-Interface vereinheitlicht:** alle Verteilungen `sample(n, rng)`,
      gemeinsame Basisklasse `Distribution`, Skalar→`PointEstimate`-Helfer.
- [x] **Unabhängigkeit hergestellt:** pyfair-Dependency entfernt (`requirements.txt`).
- [ ] **CI aufsetzen** (GitHub Actions): `pytest` + `ruff`/`flake8` bei jedem Push. *(offen)*
- [x] **Statistik-Tests:** Seed-Reproduzierbarkeit, verschiedene Seeds unterscheiden sich,
      TEF/LM-Unkorreliertheit (corr < 0.05) → Seed-Bug nachweislich behoben.

**Status:** `pytest` grün (19 Tests), RNG reproduzierbar & statistisch sauber.
Offen bleibt nur die GitHub-Actions-CI.

---

## Phase 1 — FAIR-CAM Rechenkern (Herzstück) ✅ Frequenz-Seite erledigt

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
- [ ] **Boolean-Control-Logik vervollständigen:** Detection = AND
      (Visibility ∧ Monitoring ∧ Recognition); kommt mit der LM-Seite (Phase 2).

**Status:** Resistance/Prevention-Mathematik vollständig & getestet.
Detection/Response (AND-Logik) gehört zur LM-Seite → Phase 2.

---

## Phase 2 — Detection & Response (Loss-Magnitude-Seite)

Ziel: Detection/Response wirken korrekt auf die Loss Magnitude (stage-gated).

- [ ] **Stage-gated Detection-Modell** (Kill-Chain-Stufen mit Stage-Parametern).
- [ ] **Multi-Review-Detection:**
      `λ = τ / (M/Rel_M)`,
      `P(Detect) = Cov × V_eff × [1 − (1 − R_eff)^(ρ×λ)]`
- [ ] **Conditional Magnitude Distributions:**
      Outcome-Klassen (Early/Mid/Late/Full/Attacker-Fails) →
      `E[Loss] = Σ P(outcome) × E[LM_class]`
- [ ] **Response Time mit Concurrency:**
      `T = T_containment + T_resilience − α × min(...)`
- [ ] **Detection-SLO-Alignment:** `P(Detect within T)`
- [ ] **`DetectionResponseFactor` neu implementieren** (ersetzt aktuelle Platzhalter-Mult.).
- [ ] Tests gegen `04_Detection_Response_Measurement.md`.

---

## Phase 3 — pyfair-Integration (Übergabe an FAIR-Engine)

Ziel: pyfair-cam liefert die abgeleiteten Parameter an pyfair und nutzt dessen MC.

- [ ] **Adapter-Schicht:** CAM-Ergebnisse → pyfair-Inputs
      (TEF via Avoidance/Deterrence, Susceptibility via Resistance, LM via Detection/Response).
- [ ] **`FairCamModel.to_pyfair()`** — baut ein pyfair-`Model` aus den CAM-Parametern.
- [ ] **Validierung:** identische Inputs ohne Controls → CAM-Ergebnis == reines pyfair.
- [ ] **Variance Management (VM) & Decision Support (DS)** als Modifikatoren auf
      Reliability/Decision-Quality (optional, kann nach Phase 4 rutschen).
- [ ] End-to-End-Test: vollständiges Szenario (z.B. Ransomware) durchrechnen.

---

## Phase 4 — Eigener HTML-Report (lokal, wie pyfair)

Ziel: `report.to_html()` erzeugt einen eigenständigen, ansehnlichen Report — lokal.

- [ ] **Report-Gerüst** analog `pyfair/report/` (base_report + HTML-Template + CSS).
- [ ] **Visualisierungen:** Loss Exceedance Curve (LEC), Verteilungshistogramm,
      Control-Wirksamkeits-Übersicht (OpEff je Control), Detection-Stage-Breakdown.
- [ ] **FAIR-CAM-spezifische Panels:** Susceptibility-Zerlegung, Boolean-Control-Tree,
      Vorher/Nachher-Vergleich (mit/ohne Controls).
- [ ] **Design-System anwenden** (Dark-Mode, Bahnschrift, Sky-Blau — siehe Memory).
- [ ] Beispiel-Notebook / `examples/` aktualisieren.

**Definition of Done:** `examples/`-Skript erzeugt eine vollständige HTML-Datei offline.

---

## Phase 5 — Web-Integration in fair-web (fair.neoprehn.de)

Ziel: pyfair-cam als Library in der Django-App nutzbar.

- [ ] **pyfair-cam als Dependency in fair-web** aufnehmen
      (`pip install git+https://github.com/neoprehn/pyfair-cam.git@<tag>` in `requirements.txt`,
      analog zur pyfair-Anbindung).
- [ ] **Version-Tagging** in pyfair-cam (SemVer, z.B. `v0.2.0`) für reproduzierbare Builds.
- [ ] **Andock-Variante festlegen** → siehe Abschnitt
      „Offene Architektur-Entscheidung: Andockpunkt FAIR ↔ FAIR-CAM" weiter unten.
- [ ] Django-Views/Forms für Control-Eingabe, Report-Einbettung.
- [ ] Deployment läuft über die **bestehende fair-web CI/CD** (IONOS) — siehe unten.

---

## Offene Architektur-Entscheidung: Andockpunkt FAIR ↔ FAIR-CAM

> **Noch nicht entschieden.** Bewusst offen gelassen — vielleicht sind wir bis zur
> Integration (Phase 3/5) schlauer. Diese Entscheidung NICHT vorschnell treffen.

**Worum geht es?**
FAIR-CAM kann an zwei verschiedenen Stellen der FAIR-Taxonomie andocken. Beide sind
fachlich vertretbar, führen aber zu unterschiedlicher Architektur bei der Integration.

```
FAIR-Frequenzseite:
   LEF = TEF × Susceptibility
                    └── Susceptibility entsteht aus: Control Strength (CS) vs. Threat Capability (TCap)
                        (pyfair rechnet das nativ als Step-Funktion: Vuln = mean(CS < TCap))
```

| | **Variante A — an Susceptibility** | **Variante B — an CS/RS** |
|---|---|---|
| **Andockpunkt** | `Susc = 1 − OpEff` direkt (aktueller Stand) | OpEff → CS/RS-Wert, dann pyfairs TCap-vs-CS-Step |
| **Quelle** | FAIR-CAM-Knowledge-Base (`01_..Core_Concepts.md`) schreibt das so vor | natives FAIR / pyfair (`model_calc.py._calculate_step_average`) |
| **Pro** | KB-konform; erfasst Reliability, Coverage, Variance direkt | erhält FAIRs nativen TCap-vs-CS-Wettstreit; nutzt pyfair-Engine unverändert |
| **Contra** | umgeht pyfairs nativen Vulnerability-Mechanismus | OpEff muss als RS-Perzentil ausgedrückt werden; weicht von KB ab |

**Variante C — beide / Umrechnung (zu erforschen).**
Idee: eine **Übersetzungsschicht**, die `OpEff` ↔ `CS/RS` (bzw. TCap-Perzentil)
ineinander umrechnet, sodass der Nutzer wählen kann, an welcher Stelle er andockt —
oder sodass FAIR-CAM-Controls in ein bestehendes pyfair-Modell „eingespeist" werden,
ohne dessen native Susceptibility-Logik zu verlieren.
- Offene Forschungsfrage: Gibt es eine saubere Abbildung `OpEff → RS-Perzentil`?
  (OpEff ist „Anteil abgewehrter Events" auf 0–1; RS ist ein Perzentil relativ zur
  Threat-Community — die Skalen sind nicht trivial deckungsgleich.)
- Evtl. Kalibrierung: Welcher RS-Perzentilwert erzeugt unter gegebener TCap-Verteilung
  dieselbe Vulnerability wie `1 − OpEff`? → numerisch lösbar, aber annahmebehaftet.

**Aktueller Stand:** Die Library implementiert **Variante A** (KB-konform, eigenständig).
Die Entscheidung A / B / C fällt erst bei der fair-web-Integration und betrifft NUR
den Adapter — der Rechenkern (`core.py`) bleibt in allen Varianten gleich.

---

## IONOS / Deployment — Entscheidung

**pyfair-cam braucht KEINE eigene IONOS-Anbindung.**

Es ist eine *Library* (wie pyfair), kein Service. Libraries werden nicht deployed,
sondern von der App konsumiert:

```
pyfair-cam (GitHub) ─┐
pyfair     (GitHub) ─┼──> fair-web (fair.neoprehn.de) ──> IONOS / CI-CD
                      │     installiert beide als Dependency
```

Nur **fair-web** hat die Server-/Deploy-Pipeline. pyfair-cam bleibt auf GitHub mit
sauberem Version-Tagging — das reicht. Eine eigene Pipeline wäre Overhead ohne Nutzen.

---

## Abhängigkeiten zwischen den Phasen

```
Phase 0 (Fundament)
   └─> Phase 1 (Rechenkern) ──> Phase 2 (Detection/Response)
                                      └─> Phase 3 (pyfair-Integration)
                                             └─> Phase 4 (HTML-Report, lokal)
                                                    └─> Phase 5 (fair-web / IONOS)
```

Phase 0+1 sind nicht verhandelbar (Korrektheit). Phase 4 (eigener Report) kann
parallel zu Phase 2/3 begonnen werden, sobald der Rechenkern erste Ergebnisse liefert.

---

## Offene Punkte / spätere Entscheidungen

- **Andockpunkt FAIR ↔ FAIR-CAM (A / B / C):** an Susceptibility, an CS/RS oder
  beide via Umrechnungsschicht — siehe eigener Abschnitt oben. *Wichtigste offene Frage.*
- VM- und DS-Domänen: voller Umfang oder zunächst vereinfacht?
- Eigene MC-Engine endgültig zugunsten pyfair aufgeben, oder als Fallback behalten?
- Report: statisches HTML (wie pyfair) oder interaktiv (Plotly)? — Plotly ist in
  `pyfair_cam_mc_notiz.md` bereits als Dependency angedacht.
