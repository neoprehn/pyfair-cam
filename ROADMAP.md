# pyfair-cam — Entwicklungsroadmap

> **Ziel:** Eigenständige Python-Library für FAIR-CAM (Controls Analytics Model),
> die — analog zu `pyfair` — lokal lauffähig ist und einen eigenen HTML-Report
> erzeugt. Web-Integration in `fair.neoprehn.de` (fair-web) erfolgt **danach**.
>
> **Engine-Strategie (aktualisiert):** pyfair-cam ist eine **eigenständige,
> unabhängige Bibliothek** mit eigener Monte-Carlo-Engine. KEINE pyfair-Dependency.
> Die Integration von FAIR und FAIR-CAM erfolgt erst auf Anwendungsebene in
> **fair-web** (fair.neoprehn.de), nicht in dieser Library.

Erledigtes (Phasen 0–2) steht kompakt unten und im Detail in `ROADMAP-ARCHIV.md`.

---

## Stand — was erledigt ist (Details in `ROADMAP-ARCHIV.md`)

**Phase 0 — Fundament & Korrektur:** RNG-/Seed-Bug behoben (`np.random.default_rng`,
kein `.seed()` mehr pro Sample), Distribution-Interface vereinheitlicht,
pyfair-Dependency entfernt, Statistik-Tests grün (19 Tests). **Offen:** CI
(GitHub Actions) — siehe unten.

**Phase 1 — FAIR-CAM Rechenkern ✅:** `ResistiveControl`-Datenmodell, Reliability
(`Rel`), Operational Efficacy (`OpEff`), Defense-in-Depth/Susceptibility
(`Combined_Susc`), korrekte Modellkette `Risk = (TEF × Susc) × LM`, vollständig
getestet gegen die Knowledge-Base-Formeln.

**Phase 2 — Detection & Response ✅:** Stage-gated Detection-Modell (Kill-Chain),
Multi-Review-Detection, Cumulative Progression, Conditional Magnitude
Distributions, Response Time, Detection-SLO-Alignment. 52 Tests grün.

---

### Als Nächstes → Rest Phase 0
- [ ] **CI aufsetzen** (GitHub Actions): `pytest` + `ruff`/`flake8` bei jedem Push.

---

## Phase 3 — pyfair-Integration (Übergabe an FAIR-Engine)

Ziel: pyfair-cam liefert die abgeleiteten Parameter an pyfair und nutzt dessen MC.

- [ ] **Adapter-Schicht:** CAM-Ergebnisse → pyfair-Inputs
      (TEF via Avoidance/Deterrence, Susceptibility via Resistance, LM via Detection/Response).
- [ ] **`FairCamModel.to_pyfair(mode="vuln"|"cs")`** — baut ein pyfair-`Model` aus den
      CAM-Parametern, mit zwei Andock-Pfaden:
      - **Pfad Vuln (A):** `Susc = 1 − OpEff` direkt auf `model.input_data('Vulnerability', …)`.
      - **Pfad CS (B):** `OpEff → RS-Perzentil`-Umrechnung, dann
        `model.input_data('Control Strength', …)` + `'Threat Capability'` getrennt —
        pyfair rechnet Vulnerability selbst über den nativen Step (`model_calc.py`).
- [ ] **Kalibrierungsfrage lösen (Umrechnungsschicht):** saubere/dokumentierte Abbildung
      `OpEff → RS-Perzentil` finden, sodass Pfad A und B unter gegebener
      TCap-Verteilung dieselbe resultierende Vulnerability liefern (numerisch,
      annahmebehaftet — siehe Abschnitt „Offene Architektur-Entscheidung" unten).
      Ohne das liefern A/B unterschiedliche Ergebnisse bei identischen Controls.
- [ ] **Validierung:** identische Inputs ohne Controls → CAM-Ergebnis == reines pyfair
      (für beide Pfade).
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
- [ ] **LM-Vorher/Nachher-Panel** (siehe „Rechenprinzip LM-Seite" unten): ursprünglicher
      FAIR-LM-Wert unverändert neben den CAM-Detection/Response-Infos, plus
      Stage-Ausgang (early/mid/late/full_impact/attacker_fails) als eigener Layer —
      kein Ersatz, Parallel-Anzeige.
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
- [ ] **Admin-Einstellung für Andockpunkt** (Vuln/CS, analog `AppKonfiguration`) →
      siehe Abschnitt „Offene Architektur-Entscheidung: Andockpunkt FAIR ↔ FAIR-CAM"
      weiter unten. Mechanismus (beide Pfade) kommt aus Phase 3, hier nur die
      Umschalt-UI + Default-Entscheidung.
- [ ] Django-Views/Forms für Control-Eingabe, Report-Einbettung.
- [ ] **Perspektivisch/später:** animierte Vorher-Nachher-Show für die LM-Seite —
      CAM-Ergebnisse (Stage-Ausgang) dynamisch in die FAIR-Ergebnisse einblenden,
      analog zur bereits animiert aufbauenden LEC-Kurve in fair-web. Kein
      MVP-Bestandteil, siehe „Rechenprinzip LM-Seite" oben.
- [ ] Deployment läuft über die **bestehende fair-web CI/CD** (IONOS) — siehe unten.

---

## Offene Architektur-Entscheidung: Andockpunkt FAIR ↔ FAIR-CAM

> **Mechanismus entschieden (2026-07-25), finaler Default noch offen.** Es wird eine
> **Umrechnungsschicht (Variante C)** gebaut, die sowohl A (Vulnerability direkt) als
> auch B (CS/RS über pyfairs nativen Step) unterstützt. Welche der beiden **Default**
> bzw. **einzig sichtbare Option** in fair-web wird, entscheidet sich erst später —
> geplant als **Admin-Einstellung** (analog `AppKonfiguration` in fair-web), die zur
> Laufzeit zwischen Andockpunkt Vuln/CS umschaltet. Der Rechenkern (`core.py`) bleibt
> davon unberührt, siehe unten.

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

**Aktueller Stand:** Die Library implementiert intern weiterhin nur **Susceptibility
= 1 − OpEff** (KB-konform) — das ändert sich nicht. Neu ist, dass **Phase 3** beide
Adapter-Pfade (A und B) auf Basis dieser Susceptibility baut, statt nur A. Die Wahl,
welcher Pfad in fair-web tatsächlich genutzt wird, fällt erst bei der Web-Integration
(Phase 5) und betrifft NUR den Adapter/die Admin-Einstellung — der Rechenkern
(`core.py`) bleibt in allen Varianten gleich.

**Rechenprinzip (2026-07-25, gilt für Frequenz-Seite CF/PoA/Vulnerability):**
FAIR-CAM-Controls (Avoidance, Deterrence, Resistance) sind per Definition reine
**Abschlagsfaktoren** auf die rohe FAIR-Basisrate — nie eine Erhöhung
(`OpEff`/`Rel` ∈ [0,1], strukturell auf Reduktion begrenzt). Stellt sich heraus,
dass die rohe Basisrate selbst falsch geschätzt war (z.B. CF eigentlich 50% höher),
ist das **keine CAM-Frage**, sondern eine normale Korrektur des rohen FAIR-Inputs
(CF/PoA/TEF-Verteilung direkt anpassen) — komplett getrennt von der
CAM-Reduktionsschicht, die immer nur auf die (ggf. korrigierte) Basisrate wirkt.

**Wichtig für Phase 3 (simultane Berechnung statt sequenziell):** CAM-Ergebnisse
(v.a. Susceptibility) dürfen beim Übergang zu pyfair **niemals auf einen
Kennwert (Mittelwert) reduziert** werden — das würde die Unsicherheit der
Susceptibility wegmitteln und die Tails (VaR/Max) der Risk-Verteilung
künstlich verschmälern. Stattdessen: volle rohe Arrays (Länge n, ein Wert pro
Trial) trialweise verrechnen — pyfair-cams eigener Simulator macht das intern
bereits so (`cam_model.py:calculate()`: TEF, Susceptibility, LM werden im
selben Aufruf mit demselben `rng` gezogen, elementweise multipliziert). Für
den `to_pyfair()`-Adapter heißt das konkret: **gleiche `n_simulations` auf
beiden Seiten**, volles Susceptibility-Array via `input_raw_data()` an pyfair
übergeben (nicht der Mittelwert), pyfair verrechnet es elementweise mit seinem
eigenen (ebenfalls n-langen) TEF/CF/PoA-Array. Ein gemeinsamer Seed ist dafür
nicht nötig — TEF/CF/PoA und Susceptibility sind unabhängige Zufallsgrößen,
die nur trialweise (per Index) gepaart werden müssen, nicht korreliert.

---

## Rechenprinzip LM-Seite (Detection & Response) — entschieden (2026-07-25)

Anders als bei Vuln/CS (noch offen, siehe oben) ist die LM-Seite **kein
Ersatz** und **kein reiner Abschlagsfaktor** (Detection/Response zieht pro
Trial aus 5 unabhängigen Verteilungen statt einen Basiswert zu skalieren —
"Abschlag" stimmt hier nur im Erwartungswert, nicht pro Trial, siehe Diskussion
oben). Stattdessen: **Parallel-Anzeige statt Ersatz.**

- Der **ursprüngliche, unveränderte FAIR-LM-Wert** ("Vorher") bleibt sichtbar.
- Die **CAM-Informationen** (Detection/Response) werden **separat** angezeigt.
- Ein **zweiter Verlauf/Layer** zeigt den Stage-Ausgang
  (early/mid/late/full_impact/attacker_fails) obendrauf — keine Verschmelzung
  zu einer einzigen Zahl.

Das betrifft konkret:
- **Phase 4** (lokaler Report): Vorher/Nachher nebeneinander darstellen (siehe
  Bullet dort), keine Animation nötig, nur Datenverfügbarkeit.
- **Phase 5** (fair-web): perspektivisch **animierte** Vorher-Nachher-Show —
  CAM-Ergebnisse dynamisch in die FAIR-Ergebnisse einblenden (Vorbild:
  fair-web hat mit der "animiert aufbauenden" LEC-Kurve bereits ein Muster
  dafür, siehe `fair-web/ROADMAP-ARCHIV.md` Phase 5). Kein MVP-Bestandteil,
  spätere Ausbaustufe.

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

- **Andockpunkt FAIR ↔ FAIR-CAM:** Mechanismus entschieden (Umrechnungsschicht, beide
  Pfade A+B), Default/Admin-Wahl noch offen — siehe eigener Abschnitt oben.
  *Wichtigste offene Frage bleibt die `OpEff → RS-Perzentil`-Kalibrierung.*
- **Rechenprinzip LM-Seite:** entschieden (Parallel-Anzeige statt Ersatz, siehe
  eigener Abschnitt oben) — offen ist nur noch die Umsetzung in Phase 4/5.
- VM- und DS-Domänen: voller Umfang oder zunächst vereinfacht?
- Eigene MC-Engine endgültig zugunsten pyfair aufgeben, oder als Fallback behalten?
- Report: statisches HTML (wie pyfair) oder interaktiv (Plotly)? — Plotly ist in
  `pyfair_cam_mc_notiz.md` bereits als Dependency angedacht.
