# pyfair-cam — Entwicklungsroadmap

> **Ziel:** Eigenständige Python-Library für FAIR-CAM (Controls Analytics Model),
> die — analog zu `pyfair` — lokal lauffähig ist und einen eigenen HTML-Report
> erzeugt. Web-Integration in `fair.neoprehn.de` (fair-web) erfolgt **danach**.
>
> **Engine-Strategie (aktualisiert, präzisiert 2026-07-26):** pyfair-cam ist eine
> **eigenständige, unabhängige Bibliothek** mit eigener Monte-Carlo-Engine. KEINE
> harte pyfair-Dependency im Core-Install. Der `to_pyfair()`-Adapter (Phase 3)
> lebt trotzdem *in* pyfair-cam, aber pyfair ist dafür nur eine **optionale
> Extra-Dependency** (`pip install pyfair-cam[pyfair]`, lazy import). Wer nur die
> CAM-Engine nutzt, installiert nichts von pyfair mit. Die eigentliche
> *Anwendungs*-Integration (Admin-Umschaltung Vuln/CS, UI) bleibt Sache von
> **fair-web** (Phase 5).

Erledigtes (Phasen 0–2) steht kompakt unten und im Detail in `ROADMAP-ARCHIV.md`.

---

## Stand — was erledigt ist (Details in `ROADMAP-ARCHIV.md`)

**Phase 0 — Fundament & Korrektur ✅:** RNG-/Seed-Bug behoben (`np.random.default_rng`,
kein `.seed()` mehr pro Sample), Distribution-Interface vereinheitlicht,
pyfair-Dependency entfernt, Statistik-Tests grün. CI (GitHub Actions:
`ruff` + `pytest` bei jedem Push/PR auf `main`) eingerichtet.

**Phase 1 — FAIR-CAM Rechenkern ✅:** `ResistiveControl`-Datenmodell, Reliability
(`Rel`), Operational Efficacy (`OpEff`), Defense-in-Depth/Susceptibility
(`Combined_Susc`), korrekte Modellkette `Risk = (TEF × Susc) × LM`, vollständig
getestet gegen die Knowledge-Base-Formeln.

**Phase 2 — Detection & Response ✅:** Stage-gated Detection-Modell (Kill-Chain),
Multi-Review-Detection, Cumulative Progression, Conditional Magnitude
Distributions, Response Time, Detection-SLO-Alignment. 52 Tests grün.

---

## Phase 3 — pyfair-Integration (Übergabe an FAIR-Engine)

Ziel: pyfair-cam liefert die abgeleiteten Parameter an pyfair und nutzt dessen MC.

- [x] **Adapter-Schicht (Pfad Vuln/A):** `pyfair_cam/adapter/to_pyfair.py` — volle
      Rohdatenarrays (TEF, Susceptibility, Loss Magnitude aus `calculate()`) werden
      trialweise, ohne Mittelwertbildung, via `input_raw_data()` an ein natives
      pyfair-`FairModel` übergeben (gleiche `n_simulations` auf beiden Seiten, wie
      im Rechenprinzip unten gefordert). `pyfair` ist dabei nur optionale
      Extra-Dependency (`pyfair-cam[pyfair]`, lazy import) — siehe Engine-Strategie
      oben.
- [x] **`FairCamModel.to_pyfair(mode="vuln"|"cs")`** — dünner Wrapper-Methode auf
      `FairCamModel`, delegiert an die Adapter-Funktion.
      - **Pfad Vuln (A) ✅ implementiert:** `Susc = 1 − OpEff` (kombiniert über alle
        Controls) direkt als `Vulnerability`-Rohdaten an pyfair.
      - **Pfad CS (B) ✅ implementiert (pragmatisch, unkalibriert):** `CS = 1 − Susc`
        tritt gegen eine separat übergebene `threat_capability`-Verteilung an
        (FAIR-CAM modelliert TCap nicht selbst) — pyfair berechnet `Vulnerability`
        über seinen **eigenen nativen Step-Vergleich** (`model_calc.py`). Siehe
        Kalibrierungsfrage unten für die bewusste Entscheidung, A und B *nicht*
        aufeinander abzustimmen.
      - **Wichtiger Fund (2026-07-26): pyfairs native Vulnerability ist EIN
        Skalar, kein Wert pro Trial.** `_calculate_step_average()` in
        `pyfair/model_calc.py` bildet `mean(CS < TCap)` über **alle** n Trials
        und legt diesen einen Mittelwert dann auf jeden einzelnen Trial —
        empirisch verifiziert (`tests/test_adapter.py::test_compare_paths_
        documents_variance_collapse_in_cs_path`: `Vulnerability.nunique() == 1`).
        Pfad B verliert dadurch strukturell die trialweise
        Susceptibility-Streuung, die Pfad A bewusst erhält (vgl. "Rechenprinzip"
        unten, das genau das für den *Adapter* verbietet — hier passiert es aber
        *innerhalb von pyfairs eigenem Rechenkern*, nicht im Adapter). Folge:
        `std(Risk)` ist in Pfad B strukturell kleiner als in Pfad A, unabhängig
        von der Konfidenz/Breite der CS-Eingangsverteilung — eine engere
        CS-Verteilung verschiebt nur den einen Vulnerability-Skalar, stellt die
        verlorene Trial-Varianz aber nicht wieder her. Tails/VaR aus Pfad B sind
        entsprechend vorsichtig zu interpretieren.
      - **`compare_paths()` / `FairCamModel.compare_pyfair_paths()`
        (Parallel-Anzeige):** rechnet Pfad A und Pfad B mit demselben Seed
        (identische TEF/Susceptibility/LM-Trials) nebeneinander und liefert
        beide `FairModel`-Instanzen plus eine `stats`-Tabelle
        (mean/std/median/VaR95/VaR99/max je Pfad) — statt zu kalibrieren, macht
        das die tatsächliche Abweichung (inkl. des Streuungs-Funds oben) auf
        einen Blick sichtbar, analog zur "Parallel-Anzeige statt Ersatz"-
        Entscheidung bei der LM-Seite (siehe unten).
- [x] **Kalibrierungsfrage — pragmatisch entschieden (2026-07-26), nicht gelöst:**
      Statt eine Abbildung `OpEff → RS-Perzentil` zu suchen, die A und B numerisch
      synchron macht, wird die Abweichung bewusst **akzeptiert**: Pfad B simuliert
      auf CS/TCap-Ebene (pyfairs nativer Mechanismus) und rechnet erst danach auf
      Susceptibility/Vulnerability-Ebene hoch — das darf von Pfad A abweichen. Wer
      Konsistenz mit Pfad A braucht, bleibt einfach auf Pfad A (CS/TCap unangetastet).
      **Offener Punkt für später:** eine dritte, *explizit kalibrierte* Variante, die
      beide Pfade synchron macht, ist als möglicher zukünftiger Task vermerkt (siehe
      „Offene Punkte / spätere Entscheidungen" unten), aber nicht Teil von Phase 3.
- [x] **Validierung:** `tests/test_adapter.py` — Pfad A: ohne Controls
      (`Susceptibility ≡ 1`) liefert der pyfair-Weg exakt (`assert_allclose`) dieselbe
      Risk-Verteilung wie `FairCamModel.calculate()`; mit Controls stimmt `Vulnerability`
      in pyfair 1:1 mit der CAM-Susceptibility überein, mittlerer Risk sinkt gegenüber
      dem controllosen Baseline-Modell. Pfad B: `Control Strength`/`Threat Capability`
      kommen korrekt in pyfair an, ohne Controls ist `Vulnerability` **nahe** (nicht
      exakt) 1 — dokumentiert bewusst die Abweichung zu Pfad A statt Gleichheit zu
      behaupten.
- [ ] **Variance Management (VM) & Decision Support (DS)** als Modifikatoren auf
      Reliability/Decision-Quality (optional, kann nach Phase 4 rutschen).
- [x] **End-to-End-Test:** `tests/test_end_to_end.py` — vollständiges
      Ransomware-Szenario (Resistive Control + 6-stufige Detection/Response-Kill-Chain,
      wie `examples/ransomware_scenario.py`) über `to_pyfair(mode="vuln")` gerechnet,
      inkl. Prüfung der Outcome-Klassen-Verteilung als Datengrundlage für die spätere
      Parallel-Anzeige (Phase 4).

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

> **Mechanismus entschieden (2026-07-25), Kalibrierung pragmatisch abgehakt
> (2026-07-26), finaler Default noch offen.** Beide Pfade (A: Vulnerability
> direkt, B: CS/RS über pyfairs nativen Step) sind implementiert
> (`to_pyfair(mode="vuln"|"cs")`) — **bewusst unkalibriert**: statt die
> Umrechnung `OpEff → RS-Perzentil` zu lösen, akzeptiert Pfad B einfach, dass
> er (weil er auf CS/TCap-Ebene simuliert und erst danach auf
> Susceptibility/Vuln hochrechnet) andere Zahlen liefern kann als Pfad A. Wer
> Konsistenz mit Pfad A will, bleibt auf Pfad A. Eine **dritte, explizit
> kalibrierte Variante**, die beide synchron macht, ist als möglicher
> zukünftiger Task vermerkt (siehe „Offene Punkte" unten), aber nicht gebaut.
> Welcher Pfad in fair-web **Default** bzw. **einzig sichtbare Option** wird,
> entscheidet sich weiterhin erst später — geplant als **Admin-Einstellung**
> (analog `AppKonfiguration` in fair-web), die zur Laufzeit zwischen
> Andockpunkt Vuln/CS umschaltet. Der Rechenkern (`core.py`) bleibt davon
> unberührt, siehe unten.

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
| **Andockpunkt** | `Susc = 1 − OpEff` direkt (aktueller Stand) | `CS = 1 − Susc`, dann pyfairs TCap-vs-CS-Step |
| **Quelle** | FAIR-CAM-Knowledge-Base (`01_..Core_Concepts.md`) schreibt das so vor | natives FAIR / pyfair (`model_calc.py._calculate_step_average`) |
| **Pro** | KB-konform; erfasst Reliability, Coverage, Variance direkt | erhält FAIRs nativen TCap-vs-CS-Wettstreit; nutzt pyfair-Engine unverändert |
| **Contra** | umgeht pyfairs nativen Vulnerability-Mechanismus | Ergebnis kann von Pfad A abweichen (bewusst in Kauf genommen, siehe unten) |

**Kalibrierungsfrage — pragmatisch entschieden statt gelöst (2026-07-26).**
Ursprüngliche Idee war eine **Übersetzungsschicht**, die `OpEff → RS-Perzentil` so
umrechnet, dass Pfad A und B bei identischen Controls dieselbe Vulnerability liefern.
Die Skalen sind aber nicht trivial deckungsgleich (OpEff = „Anteil abgewehrter
Events" auf 0–1; RS = Perzentil relativ zur Threat-Community), und eine belastbare
Abbildung wäre eine eigene Forschungsfrage. Entscheidung: **nicht lösen, sondern
akzeptieren.** `to_pyfair(mode="cs")` nutzt `CS = 1 − Susc` direkt als
Control-Strength-Perzentil und lässt pyfair nativ dagegen simulieren — ohne
Anspruch, mit Pfad A übereinzustimmen. Wer identische Ergebnisse zu Pfad A braucht,
nutzt Pfad A (Vuln) und lässt CS/TCap unangetastet.
- **Offener Punkt für später:** eine dritte, *explizit kalibrierte* Variante
  (numerisch gelöst, annahmebehaftet), die A und B synchron macht, könnte man bauen,
  falls sich das als nötig erweist — kein aktueller Task, nur vorgemerkt.
- **Wichtig für diese spätere Kalibrierung:** Selbst eine perfekte
  `OpEff → RS-Perzentil`-Abbildung würde nur den *Mittelwert* von Pfad B an Pfad A
  angleichen — die Trial-Varianz bliebe kleiner, weil pyfairs natives
  `Vulnerability = mean(CS < TCap)` ein einziger Skalar über alle Trials ist (siehe
  Fund oben, Phase-3-Checkliste). Eine Kalibrierung, die auch die Streuung
  angleicht, müsste an dieser Stelle in pyfair selbst ansetzen, nicht nur an der
  CS-Eingangsverteilung.

**Aktueller Stand:** Die Library implementiert intern weiterhin nur **Susceptibility
= 1 − OpEff** (KB-konform) — das ändert sich nicht. **Phase 3** liefert darauf
aufbauend beide Adapter-Pfade: **Pfad A** (`to_pyfair(mode="vuln")`, KB-konform,
identisch zu `calculate()`) und **Pfad B** (`to_pyfair(mode="cs")`, pyfairs nativer
Mechanismus, erfordert eine separat übergebene `threat_capability`-Verteilung, da
FAIR-CAM TCap nicht selbst modelliert). Die Wahl, welcher Pfad in fair-web
tatsächlich genutzt wird, fällt erst bei der Web-Integration (Phase 5) und betrifft
NUR den Adapter/die Admin-Einstellung — der Rechenkern (`core.py`) bleibt in allen
Varianten gleich.

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

- **Andockpunkt FAIR ↔ FAIR-CAM:** beide Pfade A+B implementiert, bewusst
  unkalibriert (siehe eigener Abschnitt oben); Default/Admin-Wahl noch offen (Phase 5).
- **Kalibrierte dritte Variante (Pfad A ↔ Pfad B synchron):** vorgemerkt, aber kein
  aktueller Task — nur bauen, falls sich Inkonsistenz zwischen den Pfaden in der
  Praxis als echtes Problem erweist (siehe „Offene Architektur-Entscheidung" oben).
- **Rechenprinzip LM-Seite:** entschieden (Parallel-Anzeige statt Ersatz, siehe
  eigener Abschnitt oben) — offen ist nur noch die Umsetzung in Phase 4/5.
- VM- und DS-Domänen: voller Umfang oder zunächst vereinfacht?
- Eigene MC-Engine endgültig zugunsten pyfair aufgeben, oder als Fallback behalten?
- Report: statisches HTML (wie pyfair) oder interaktiv (Plotly)? — Plotly ist in
  `pyfair_cam_mc_notiz.md` bereits als Dependency angedacht.
