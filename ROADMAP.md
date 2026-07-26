# pyfair-cam — Entwicklungsroadmap

> **Ziel:** Eigenständige Python-Library für FAIR-CAM (Controls Analytics Model), die — analog zu `pyfair` — lokal lauffähig ist und einen eigenen HTML-Report
> erzeugt. Web-Integration in `fair.neoprehn.de` (fair-web) erfolgt **danach**.
>
> **Engine-Strategie (aktualisiert, präzisiert 2026-07-26):** pyfair-cam ist eine **eigenständige, unabhängige Bibliothek** mit eigener Monte-Carlo-Engine.
> KEINE harte pyfair-Dependency im Core-Install. Der `to_pyfair()`-Adapter (Phase 3) lebt trotzdem *in* pyfair-cam, aber pyfair ist dafür nur eine **optionale
> Extra-Dependency** (`pip install pyfair-cam[pyfair]`, lazy import). Wer nur die CAM-Engine nutzt, installiert nichts von pyfair mit. Die eigentliche
> *Anwendungs*-Integration (Admin-Umschaltung Vuln/CS, UI) bleibt Sache von **fair-web** (Phase 5).

Erledigtes (Phasen 0–3) steht kompakt unten und im Detail in `ROADMAP-ARCHIV.md`.

---

## Stand — was erledigt ist (Details in `ROADMAP-ARCHIV.md`)

**Phase 0 — Fundament & Korrektur ✅:** RNG-/Seed-Bug behoben (`np.random.default_rng`, kein `.seed()` mehr pro Sample), Distribution-Interface vereinheitlicht,
pyfair-Dependency entfernt, Statistik-Tests grün. CI (GitHub Actions: `ruff` + `pytest` bei jedem Push/PR auf `main`) eingerichtet.

**Phase 1 — FAIR-CAM Rechenkern ✅:** `ResistiveControl`-Datenmodell, Reliability (`Rel`), Operational Efficacy (`OpEff`), Defense-in-Depth/Susceptibility
(`Combined_Susc`), korrekte Modellkette `Risk = (TEF × Susc) × LM`, vollständig getestet gegen die Knowledge-Base-Formeln.

**Phase 2 — Detection & Response ✅:** Stage-gated Detection-Modell (Kill-Chain), Multi-Review-Detection, Cumulative Progression, Conditional Magnitude
Distributions, Response Time, Detection-SLO-Alignment.

**Phase 3 — pyfair-Integration ✅:** `to_pyfair(mode="vuln"|"cs")` als optionaler Adapter (Extra `pyfair-cam[pyfair]`), beide Andockpunkte implementiert und
bewusst unkalibriert gelassen, `compare_paths()` zur Gegenüberstellung, End-to-End-Test mit vollständigem Ransomware-Szenario. Dabei gefunden und dokumentiert:
pyfairs natives `Vulnerability = mean(CS < TCap)` ist ein Skalar über alle Trials, Pfad CS/B verliert dadurch strukturell Streuung (siehe „Offene
Architektur-Entscheidung" unten). 69 Tests grün.

---

## Phase 4 — Eigener HTML-Report (lokal, wie pyfair) ← **als Nächstes**

Ziel: `report.to_html()` erzeugt einen eigenständigen, ansehnlichen Report — lokal.

- [ ] **Report-Gerüst** analog `pyfair/report/` (base_report + HTML-Template + CSS).
- [ ] **Visualisierungen:** Loss Exceedance Curve (LEC), Verteilungshistogramm, Control-Wirksamkeits-Übersicht (OpEff je Control), Detection-Stage-Breakdown.
- [ ] **FAIR-CAM-spezifische Panels:** Susceptibility-Zerlegung, Boolean-Control-Tree, Vorher/Nachher-Vergleich (mit/ohne Controls).
- [ ] **LM-Vorher/Nachher-Panel** (siehe „Rechenprinzip LM-Seite" unten): ursprünglicher FAIR-LM-Wert unverändert neben den CAM-Detection/Response-Infos, plus
      Stage-Ausgang (early/mid/late/full_impact/attacker_fails) als eigener Layer — kein Ersatz, Parallel-Anzeige.
- [ ] **Pfad-A/B-Panel:** `compare_paths()`-Ergebnis (stats-Tabelle beider Andockpunkte) inkl. des Streuungs-Hinweises als Fußnote — nicht nur die Zahlen zeigen,
      sondern auch, warum Pfad B schmalere Tails hat.
- [ ] **Design-System anwenden** (Dark-Mode, Bahnschrift, Sky-Blau — siehe Memory).
- [ ] Beispiel-Notebook / `examples/` aktualisieren.

**Definition of Done:** `examples/`-Skript erzeugt eine vollständige HTML-Datei offline.

---

## Phase 5 — Web-Integration in fair-web (fair.neoprehn.de)

Ziel: pyfair-cam als Library in der Django-App nutzbar.

- [ ] **pyfair-cam als Dependency in fair-web** aufnehmen (`pip install git+https://github.com/neoprehn/pyfair-cam.git@<tag>` in `requirements.txt`, analog zur
      pyfair-Anbindung).
- [ ] **Version-Tagging** in pyfair-cam (SemVer, z.B. `v0.2.0`) für reproduzierbare Builds.
- [ ] **Admin-Einstellung für Andockpunkt** (Vuln/CS, analog `AppKonfiguration`) → siehe Abschnitt „Offene Architektur-Entscheidung: Andockpunkt FAIR ↔
      FAIR-CAM" weiter unten. Mechanismus (beide Pfade) kommt aus Phase 3, hier nur die Umschalt-UI + Default-Entscheidung.
- [ ] Django-Views/Forms für Control-Eingabe, Report-Einbettung.
- [ ] **Perspektivisch/später:** animierte Vorher-Nachher-Show für die LM-Seite — CAM-Ergebnisse (Stage-Ausgang) dynamisch in die FAIR-Ergebnisse einblenden,
      analog zur bereits animiert aufbauenden LEC-Kurve in fair-web. Kein MVP-Bestandteil, siehe „Rechenprinzip LM-Seite" oben.
- [ ] Deployment läuft über die **bestehende fair-web CI/CD** (IONOS) — siehe unten.

---

## Phase 6 — Variance Management (VM)

> Verschoben aus Phase 3 (2026-07-26): VM/DS waren dort als optionaler Anhang geführt, sind aber jeweils ein eigenes Modellthema mit eigener Wirkmechanik und
> gehören deshalb hinter die Anwendungs-Phasen als eigene Phase.

Ziel: VM-Controls als eigene Modellschicht, die **nicht** direkt auf Susceptibility wirkt, sondern auf die **Reliability anderer Controls** — also auf `VF`/`VD`,
die über `Rel = (1 − VF/365)^VD` in die `OpEff` jedes betroffenen Controls eingehen. Fachliche Grundlage: `knowledge-base/.../01_FAIR_CAM_Core_Concepts.md`
(VM-Funktionsbaum) und `.../09_Resistance_Susceptibility_Measurement.md` (Varianzquellen).

- [ ] **VM-Datenmodell** entlang des KB-Funktionsbaums: *Prevention* (Änderungsfrequenz senken, Wahrscheinlichkeit senken, dass eine Änderung Varianz erzeugt),
      *Identification* (Controls Monitoring, Threat-Capability-Monitoring, Priorisierung der Behandlung), *Correction* (Implementation, z.B. Patchen/Rekonfig).
- [ ] **Wirkmechanik statt eigener Risikoformel:** ein VM-Control verändert die `VF`/`VD`-Parameter der Controls, auf die es zeigt. Neu ist damit vor allem die
      *Verdrahtung* (welches VM-Control wirkt auf welches LE-Control), nicht die Mathematik — `reliability()`/`operational_efficacy()` bleiben unverändert.
- [ ] **VD realistisch zerlegen:** Variance Duration ist nicht nur die Reparaturzeit, sondern *Zeit bis die Varianz überhaupt auffällt* (VM Identification, hängt
      am Monitoring-Takt) **plus** *Zeit bis zur Korrektur* (VM Correction). Erst diese Zerlegung macht „besseres Monitoring" im Modell überhaupt wirksam.
- [ ] **Intrinsische vs. extrinsische Varianz trennen:** intrinsisch (eigene Änderungen, Fehlkonfiguration, fehlgeschlagene Patches) vs. extrinsisch (die
      Bedrohungslage ändert sich, z.B. neue Exploits — das Control selbst bleibt unverändert, seine Wirksamkeit sinkt trotzdem). Beide speisen dieselbe `VF`,
      haben aber unterschiedliche Datenquellen und unterschiedliche Gegenmaßnahmen → getrennt erfassen, summiert verrechnen.
- [ ] **Rekursionsgrenze festlegen:** laut KB kann Varianz *jeden* Control-Typ treffen, auch VM- und DS-Controls selbst. Ein unbegrenzt rekursives Modell ist
      weder rechenbar noch schätzbar → bewusst auf eine Ebene begrenzen (VM wirkt auf LE) und die Entscheidung dokumentieren.
- [ ] Tests + Beispiel (`examples/`), das zeigt, wie sich ein VM-Control auf `OpEff`/Risk eines LE-Controls durchschlägt.

---

## Phase 7 — Decision Support (DS)

> Ebenfalls aus Phase 3 hierher verschoben (2026-07-26), gleiche Begründung wie bei VM.

Ziel: DS-Controls als Qualitätsschicht auf **Entscheidungen**, die ihrerseits VM- und LE-Parameter treiben. DS wirkt am weitesten weg vom Risiko und ist deshalb
die am schwersten quantifizierbare Domäne — entsprechend vorsichtig modellieren. Grundlage: `.../01_FAIR_CAM_Core_Concepts.md` (DS-Funktionsbaum).

- [ ] **DS-Datenmodell** entlang des KB-Funktionsbaums: *Misaligned Decision Prevention* (Erwartungen definieren, Erwartungen kommunizieren, Situational
      Awareness über Daten → Analyse → Reporting, Befähigung sicherstellen, Anreize setzen) und *Misaligned Decision Identification* (RCA, Audits, Post-Mortems).
- [ ] **Wirkmechanik:** DS verändert keine FAIR-Faktoren direkt, sondern die Parameter *anderer* Controls — typischerweise VM (z.B. schlechte Priorisierung
      verlängert `VD`) und LE (z.B. fehlende Befähigung senkt `Cov` oder `IntEff`). Die Verdrahtung DS → VM → LE ist der eigentliche Modellinhalt.
- [ ] **Einheiten-Problem lösen:** DS wird laut KB in Frequenz/Timeliness/Qualität gemessen, nicht in Wahrscheinlichkeiten. Diese Größen müssen erst in einen
      Effekt auf `VF`/`VD`/`Cov` übersetzt werden — diese Übersetzung ist annahmebehaftet und muss explizit dokumentiert und abschaltbar sein.
- [ ] **Offene Modellierungsfrage:** DS als multiplikativer Modifikator auf VM-Parameter, oder als eigene Verteilung mit eigener Unsicherheit? Ersteres ist
      einfacher, Letzteres ehrlicher. Entscheiden, bevor Code entsteht.
- [ ] Tests + Beispiel.

---

## Phase 8 — Risk Appetite, KRI/KPI & Board-Reporting

Ziel: Risikoappetit **explizit abfragbar und prüfbar** machen, statt ihn als „niedrig/mittel/hoch" zu belassen. Grundlage:
`.../05_Risk_Appetite_Metrics.md`. Der Rechenkern liefert dafür bereits alles Nötige (Risk-Verteilung, LEC) — hier kommt die Bewertungs- und Reporting-Schicht
darauf.

- [ ] **`RiskAppetite`-Datenobjekt:** ein Appetit ist laut KB immer ein Tripel aus *Verlusthöhen-Schwelle*, *maximal akzeptierter Wahrscheinlichkeit für deren
      Überschreitung* und *Zeitfenster* (z.B. „höchstens 5 % Wahrscheinlichkeit in 12 Monaten, dass Verlust X überschritten wird"). Genau diese drei Felder
      abfragen — ohne alle drei ist die Aussage nicht prüfbar.
- [ ] **Prüfung gegen die Simulation:** P(Verlust > Schwelle) direkt aus der vorhandenen Risk-Verteilung bzw. `get_lec()` ableiten und gegen die erlaubte
      Wahrscheinlichkeit stellen → Status *eingehalten / grenzwertig / überschritten*. Das ist die Kernfunktion dieser Phase.
- [ ] **Mehrere Appetite parallel:** verschiedene Schadensarten (z.B. Datenabfluss, Ausfall, Regulatorik, Finanzberichterstattung) haben eigene Schwellen und
      werden nebeneinander bewertet, nicht zu einer Zahl verdichtet.
- [ ] **Rückwärtsrechnung Appetit → Control-Ziele:** die eigentlich wertvolle Richtung — „welche Detection-/Resistance-Werte müssten erreicht werden, damit die
      Überschreitungswahrscheinlichkeit unter die Schwelle fällt?". Numerisch über Zielsuche auf den bestehenden Modellparametern lösbar.
- [ ] **KRI und KPI sauber trennen** (KB warnt ausdrücklich vor dem Vermischen): KRI = Risiko-Indikatoren aus dem Modell (Überschreitungswahrscheinlichkeit,
      Susceptibility, Perzentile der Verlustverteilung); KPI = Control-Performance (`VF`, `VD`, Coverage, Termintreue bei Korrekturen). Zwei getrennte Ausgaben.
- [ ] **Kennzahlen-Guardrails aus der KB übernehmen:** Mittelwert nie allein ausweisen (Median + P90 dazu, sonst verdeckt der Mittelwert genau die Ausreißer, um
      die es geht), und bei Zielwerten den Anreiz zum Kennzahl-Optimieren mitdenken statt nur die Zahl zu rendern.
- [ ] **Board-Rollup als Report-Panel** (setzt auf Phase 4 auf): Appetit-Status je Schadensart, Trend, und je Maßnahme die erwartete Veränderung der
      Überschreitungswahrscheinlichkeit.
- [ ] `core.detection_within_time()` (Detection-SLO, existiert seit Phase 2) hier ins Appetit-Framework einhängen statt separat stehen zu lassen.

---

## Phase 9 — Root Cause Analysis (RCA)

Ziel: strukturiert erfassen, **warum** ein Control versagt hat, und das an die Simulation anschließen. Grundlage: `.../03_RCA_with_FAIR_CAM.md`.
Setzt Phase 6+7 voraus, weil die Remedies fast immer VM- oder DS-Controls sind.

- [ ] **Die fünf RCA-Dimensionen als Datenmodell** (Governance, Awareness, Capability, Prioritization, Intent) — jeweils als beantwortbare Frage, nicht als
      Freitextfeld.
- [ ] **Mapping RCA-Dimension → FAIR-CAM-Funktion → Maßnahmentyp**, damit aus dem Befund direkt folgt, an welchem Control-Typ zu drehen ist.
- [ ] **Quantitativer Anschluss (der eigentliche Mehrwert):** RCA-Kategorie → geschätzter Effekt auf `VF`/`VD` → über `Rel`/`OpEff` in die Risikorechnung. Damit
      wird aus „wir hatten drei Priorisierungsprobleme" eine belastbare Aussage über den Risikobeitrag.
- [ ] **Verteilung der Ursachen über die Zeit auswerten:** häufen sich Befunde in einer Dimension, ist das ein systemisches DS-Problem und keine Einzelfallkette
      — genau dafür ist die Verteilung da.

---

## Phase 10 — Resistance-Vertiefung (Software selbst als Control)

Ziel: die Resistance-Seite aus Phase 1 verfeinern. Grundlage: `.../09_Resistance_Susceptibility_Measurement.md`. Phase 1 modelliert ein resistives Control
bislang als *einen* Satz aus `IntEff`/`VarEff`/`VF`/`VD`/`Cov`; die KB zerlegt Resistance deutlich feiner.

- [ ] **Zentrale Unterscheidung übernehmen: Zustand ≠ Prozess.** Die Software (bzw. die Person) ist selbst das resistive Control; Patchen bzw. Schulen sind
      VM-Correction darauf. Häufiger Modellierungsfehler ist, *alles* Härtungsbezogene nach VM zu schieben und den Schutz des gehärteten Zustands zu verlieren.
- [ ] **Resistance-Kategorien getrennt modellierbar machen** (jede mit eigener Wirksamkeit und eigenem Varianzprofil): Patch-Zustand, Exploit-Mitigations,
      Konfigurationshärtung/Angriffsflächenreduktion, Sandboxing. Diese schichten sich multiplikativ — dafür ist `combined_susceptibility()` bereits da.
- [ ] **Binäre Controls als Convenience:** ist ein Control an/aus (Mitigation aktiv oder nicht), ist `VarEff = 0` und `OpEff` reduziert sich auf `Cov × Rel ×
      IntEff`. Als eigener Konstruktor anbieten, damit man nicht künstlich ein `VarEff` erfinden muss.
- [ ] **Wirksamkeit abhängig von der Angreiferklasse:** dieselbe Härtung hält gegen Massen-Malware anders als gegen einen gezielten, gut ausgestatteten Angreifer.
      `IntEff` je Bedrohungsklasse angebbar machen (passt zur Threat-Capability-Frage aus Phase 3, Pfad CS/B).
- [ ] **Unabhängigkeitsannahme prüfbar machen:** `combined_susceptibility()` multipliziert aktuell unter der Annahme unabhängiger Controls. Die KB warnt explizit
      vor korrelierten Ausfällen (dieselben VM-/DS-Controls hängen an mehreren Schutzschichten). Optionaler Korrelationsaufschlag + deutlicher Hinweis im Report.

---

## Phase 11 — Opportunity Analysis (Chancen statt Schäden)

Ziel: dieselbe Engine für die Chancen-Seite nutzbar machen. Grundlage: `.../06_Opportunity_Analysis.md`. Die Mathematik ist laut KB identisch — es ist im
Kern eine Umbenennungs- und Reporting-Schicht plus *ein* echter neuer Mechanismus.

- [ ] **Terminologie-Abbildung** als dünne Schicht über der bestehenden Engine: Threat-Event-Frequenz → Frequenz von Chancen-Signalen, Loss-Event-Frequenz →
      Frequenz realisierter Chancen, Susceptibility → Wahrscheinlichkeit, dass das Gegenüber zusagt, Verlust → entgangener bzw. realisierter Wert.
- [ ] **Detection/Response umdeuten:** Detection = die Chance rechtzeitig überhaupt bemerken, Response = rechtzeitig handeln. Das stage-gated Modell aus Phase 2
      passt unverändert.
- [ ] **Wertverfall über Zeit — der einzige echte Neubau:** Chancen verlieren mit der Zeit an Wert. Detection + Response müssen die Verfallskurve schlagen. Diese
      Kurve gibt es im Risikomodell nicht und muss als eigene Komponente ergänzt werden.
- [ ] **Abgrenzung mitdokumentieren:** Prevention bleibt in ihrer Rolle — sie erzeugt keine Chancen, kann aber versehentlich gute Fälle abwürgen (zu strenge
      Filter). Das ist ein Diagnose-Use-Case, kein Modellierungs-Hebel.

---

## Querschnitt: Rechen- und Qualitätsstandards (laufend, keine eigene Phase)

Grundlage: `.../08_Quantitative_Analysis_Quality_Standards.md`. Kein Feature, sondern eine Testkonvention, die bei **jeder** neuen Phase mitläuft.

- Mathematische Obergrenzen im Test prüfen statt nur im Kopf: z.B. kann die Detection-Wahrscheinlichkeit nie über `Cov × V_eff` liegen (in
  `stage_detection_probability()` bereits als Deckel implementiert), Wahrscheinlichkeiten bleiben in [0,1], Outcome-Klassen summieren sich auf 1.
- Monte-Carlo-Ergebnisse gegen die analytische Erwartung gegenprüfen, wo eine geschlossene Form existiert (`core.expected_gross_loss()` ist genau dafür da).
- Einheiten explizit halten (Tage vs. Stunden, Anteil vs. Prozent) — laut KB eine der häufigsten Fehlerquellen in solchen Modellen.

---

## Offene Architektur-Entscheidung: Andockpunkt FAIR ↔ FAIR-CAM

> **Mechanismus entschieden (2026-07-25), Kalibrierung pragmatisch abgehakt (2026-07-26), finaler Default noch offen.** Beide Pfade (A: Vulnerability direkt, B:
> CS/RS über pyfairs nativen Step) sind implementiert (`to_pyfair(mode="vuln"|"cs")`) — **bewusst unkalibriert**: statt die Umrechnung `OpEff → RS-Perzentil` zu
> lösen, akzeptiert Pfad B einfach, dass er (weil er auf CS/TCap-Ebene simuliert und erst danach auf Susceptibility/Vuln hochrechnet) andere Zahlen liefern kann
> als Pfad A. Wer Konsistenz mit Pfad A will, bleibt auf Pfad A. Eine **dritte, explizit kalibrierte Variante**, die beide synchron macht, ist als möglicher
> zukünftiger Task vermerkt (siehe „Offene Punkte" unten), aber nicht gebaut. Welcher Pfad in fair-web **Default** bzw. **einzig sichtbare Option** wird,
> entscheidet sich weiterhin erst später — geplant als **Admin-Einstellung** (analog `AppKonfiguration` in fair-web), die zur Laufzeit zwischen Andockpunkt
> Vuln/CS umschaltet. Der Rechenkern (`core.py`) bleibt davon unberührt, siehe unten.

**Worum geht es?** FAIR-CAM kann an zwei verschiedenen Stellen der FAIR-Taxonomie andocken. Beide sind fachlich vertretbar, führen aber zu unterschiedlicher
Architektur bei der Integration.

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

**Fund (2026-07-26): pyfairs native Vulnerability ist EIN Skalar, kein Wert pro Trial.** `_calculate_step_average()` in `pyfair/model_calc.py` bildet
`mean(CS < TCap)` über **alle** n Trials und legt diesen einen Mittelwert dann auf jeden einzelnen Trial — empirisch verifiziert
(`tests/test_adapter.py::test_compare_paths_documents_variance_collapse_in_cs_path`: `Vulnerability.nunique() == 1`). Pfad B verliert dadurch strukturell die
trialweise Susceptibility-Streuung, die Pfad A bewusst erhält (vgl. „Rechenprinzip" unten, das genau das für den *Adapter* verbietet — hier passiert es aber
*innerhalb von pyfairs eigenem Rechenkern*, nicht im Adapter). Folge: `std(Risk)` ist in Pfad B strukturell kleiner als in Pfad A, unabhängig von der
Konfidenz/Breite der CS-Eingangsverteilung — eine engere CS-Verteilung verschiebt nur den einen Vulnerability-Skalar, stellt die verlorene Trial-Varianz aber
nicht wieder her. Tails/VaR aus Pfad B sind entsprechend vorsichtig zu interpretieren.

**Kalibrierungsfrage — pragmatisch entschieden statt gelöst (2026-07-26).** Ursprüngliche Idee war eine **Übersetzungsschicht**, die `OpEff → RS-Perzentil` so
umrechnet, dass Pfad A und B bei identischen Controls dieselbe Vulnerability liefern. Die Skalen sind aber nicht trivial deckungsgleich (OpEff = „Anteil
abgewehrter Events" auf 0–1; RS = Perzentil relativ zur Threat-Community), und eine belastbare Abbildung wäre eine eigene Forschungsfrage. Entscheidung: **nicht
lösen, sondern akzeptieren.** `to_pyfair(mode="cs")` nutzt `CS = 1 − Susc` direkt als Control-Strength-Perzentil und lässt pyfair nativ dagegen simulieren —
ohne Anspruch, mit Pfad A übereinzustimmen. Wer identische Ergebnisse zu Pfad A braucht, nutzt Pfad A (Vuln) und lässt CS/TCap unangetastet.
- **Offener Punkt für später:** eine dritte, *explizit kalibrierte* Variante (numerisch gelöst, annahmebehaftet), die A und B synchron macht, könnte man bauen,
  falls sich das als nötig erweist — kein aktueller Task, nur vorgemerkt.
- **Wichtig für diese spätere Kalibrierung:** Selbst eine perfekte `OpEff → RS-Perzentil`-Abbildung würde nur den *Mittelwert* von Pfad B an Pfad A angleichen —
  die Trial-Varianz bliebe kleiner (siehe Fund oben). Eine Kalibrierung, die auch die Streuung angleicht, müsste in pyfair selbst ansetzen, nicht nur an der
  CS-Eingangsverteilung.

**Aktueller Stand:** Die Library implementiert intern weiterhin nur **Susceptibility = 1 − OpEff** (KB-konform) — das ändert sich nicht. **Phase 3** liefert
darauf aufbauend beide Adapter-Pfade: **Pfad A** (`to_pyfair(mode="vuln")`, KB-konform, identisch zu `calculate()`) und **Pfad B** (`to_pyfair(mode="cs")`,
pyfairs nativer Mechanismus, erfordert eine separat übergebene `threat_capability`-Verteilung, da FAIR-CAM TCap nicht selbst modelliert). Die Wahl, welcher Pfad
in fair-web tatsächlich genutzt wird, fällt erst bei der Web-Integration (Phase 5) und betrifft NUR den Adapter/die Admin-Einstellung — der Rechenkern
(`core.py`) bleibt in allen Varianten gleich.

**Rechenprinzip (2026-07-25, gilt für Frequenz-Seite CF/PoA/Vulnerability):** FAIR-CAM-Controls (Avoidance, Deterrence, Resistance) sind per Definition reine
**Abschlagsfaktoren** auf die rohe FAIR-Basisrate — nie eine Erhöhung (`OpEff`/`Rel` ∈ [0,1], strukturell auf Reduktion begrenzt). Stellt sich heraus, dass die
rohe Basisrate selbst falsch geschätzt war (z.B. CF eigentlich 50% höher), ist das **keine CAM-Frage**, sondern eine normale Korrektur des rohen FAIR-Inputs
(CF/PoA/TEF-Verteilung direkt anpassen) — komplett getrennt von der CAM-Reduktionsschicht, die immer nur auf die (ggf. korrigierte) Basisrate wirkt.

**Wichtig für Phase 3 (simultane Berechnung statt sequenziell):** CAM-Ergebnisse (v.a. Susceptibility) dürfen beim Übergang zu pyfair **niemals auf einen
Kennwert (Mittelwert) reduziert** werden — das würde die Unsicherheit der Susceptibility wegmitteln und die Tails (VaR/Max) der Risk-Verteilung künstlich
verschmälern. Stattdessen: volle rohe Arrays (Länge n, ein Wert pro Trial) trialweise verrechnen — pyfair-cams eigener Simulator macht das intern bereits so
(`cam_model.py:calculate()`: TEF, Susceptibility, LM werden im selben Aufruf mit demselben `rng` gezogen, elementweise multipliziert). Für den
`to_pyfair()`-Adapter heißt das konkret: **gleiche `n_simulations` auf beiden Seiten**, volles Susceptibility-Array via `input_raw_data()` an pyfair übergeben
(nicht der Mittelwert), pyfair verrechnet es elementweise mit seinem eigenen (ebenfalls n-langen) TEF/CF/PoA-Array. Ein gemeinsamer Seed ist dafür nicht nötig —
TEF/CF/PoA und Susceptibility sind unabhängige Zufallsgrößen, die nur trialweise (per Index) gepaart werden müssen, nicht korreliert.

---

## Rechenprinzip LM-Seite (Detection & Response) — entschieden (2026-07-25)

Anders als bei Vuln/CS (noch offen, siehe oben) ist die LM-Seite **kein Ersatz** und **kein reiner Abschlagsfaktor** (Detection/Response zieht pro Trial aus 5
unabhängigen Verteilungen statt einen Basiswert zu skalieren — "Abschlag" stimmt hier nur im Erwartungswert, nicht pro Trial, siehe Diskussion oben).
Stattdessen: **Parallel-Anzeige statt Ersatz.**

- Der **ursprüngliche, unveränderte FAIR-LM-Wert** ("Vorher") bleibt sichtbar.
- Die **CAM-Informationen** (Detection/Response) werden **separat** angezeigt.
- Ein **zweiter Verlauf/Layer** zeigt den Stage-Ausgang (early/mid/late/full_impact/attacker_fails) obendrauf — keine Verschmelzung zu einer einzigen Zahl.

Das betrifft konkret:
- **Phase 4** (lokaler Report): Vorher/Nachher nebeneinander darstellen (siehe Bullet dort), keine Animation nötig, nur Datenverfügbarkeit.
- **Phase 5** (fair-web): perspektivisch **animierte** Vorher-Nachher-Show — CAM-Ergebnisse dynamisch in die FAIR-Ergebnisse einblenden (Vorbild: fair-web hat
  mit der "animiert aufbauenden" LEC-Kurve bereits ein Muster dafür, siehe `fair-web/ROADMAP-ARCHIV.md` Phase 5). Kein MVP-Bestandteil, spätere Ausbaustufe.

---

## IONOS / Deployment — Entscheidung

**pyfair-cam braucht KEINE eigene IONOS-Anbindung.**

Es ist eine *Library* (wie pyfair), kein Service. Libraries werden nicht deployed, sondern von der App konsumiert:

```
pyfair-cam (GitHub) ─┐
pyfair     (GitHub) ─┼──> fair-web (fair.neoprehn.de) ──> IONOS / CI-CD
                      │     installiert beide als Dependency
```

Nur **fair-web** hat die Server-/Deploy-Pipeline. pyfair-cam bleibt auf GitHub mit sauberem Version-Tagging — das reicht. Eine eigene Pipeline wäre Overhead
ohne Nutzen.

---

## Abhängigkeiten zwischen den Phasen

```
Phase 0 (Fundament) ✅
   └─> Phase 1 (Rechenkern) ✅ ──> Phase 2 (Detection/Response) ✅
                                      └─> Phase 3 (pyfair-Integration) ✅
                                             └─> Phase 4 (HTML-Report, lokal)   ← als Nächstes
                                                    └─> Phase 5 (fair-web / IONOS)
                                                           ├─> Phase 6 (Variance Management)
                                                           │      └─> Phase 7 (Decision Support)
                                                           │             └─> Phase 9 (RCA)
                                                           ├─> Phase 8 (Risk Appetite & Metriken)
                                                           ├─> Phase 10 (Resistance-Vertiefung)
                                                           └─> Phase 11 (Opportunity Analysis)
```

Phase 0+1 sind nicht verhandelbar (Korrektheit). Phase 4 kann jederzeit begonnen werden, der Rechenkern liefert bereits alles Nötige.

Die Reihenfolge 6 → 7 → 9 ist inhaltlich zwingend (DS wirkt über VM; RCA-Remedies sind fast immer VM-/DS-Controls). Die Phasen 8, 10 und 11 hängen dagegen nur
lose an ihren Vorgängern und könnten vorgezogen werden:
- **Phase 8** braucht für den KRI-Teil nur die vorhandene Risk-Verteilung — nur der KPI-Teil (Control-Performance) profitiert wirklich von 6+7.
- **Phase 10** ist eine Verfeinerung von Phase 1 und technisch jederzeit machbar; sie liegt hier hinten, weil sie Modellierungstiefe statt Nutzwert bringt.
- **Phase 11** ist überwiegend eine Umbenennungs-/Reporting-Schicht auf der fertigen Engine.

---

## Offene Punkte / spätere Entscheidungen

- **Andockpunkt FAIR ↔ FAIR-CAM:** beide Pfade A+B implementiert, bewusst unkalibriert (siehe eigener Abschnitt oben); Default/Admin-Wahl noch offen (Phase 5).
- **Kalibrierte dritte Variante (Pfad A ↔ Pfad B synchron):** vorgemerkt, aber kein aktueller Task — nur bauen, falls sich Inkonsistenz zwischen den Pfaden in
  der Praxis als echtes Problem erweist (siehe „Offene Architektur-Entscheidung" oben).
- **Widerspruch innerhalb der Knowledge Base selbst (gefunden 2026-07-26, ungelöst):** `.../09_Resistance_Susceptibility_Measurement.md` formuliert Detection als
  Faktor auf der **Frequenz-Seite** (Vulnerability ergibt sich aus Susceptibility *und* der Detection-/Response-Fähigkeit), während
  `.../04_Detection_Response_Measurement.md` — und damit unsere Phase 2 — Detection über Outcome-Klassen auf die **Loss-Magnitude-Seite** legt. Beide Varianten
  stehen so in der KB. Implementiert ist die LM-Seite. Vor Phase 10 klären, ob die Frequenz-Variante zusätzlich gebraucht wird oder ob es zwei Sichtweisen auf
  denselben Sachverhalt sind — doppelte Anrechnung von Detection wäre der Fehler, den es zu vermeiden gilt.
- **Unabhängigkeitsannahme bei Defense-in-Depth:** `combined_susceptibility()` multipliziert unter der Annahme unabhängiger Controls; die KB warnt vor
  korrelierten Ausfällen. Behandelt in Phase 10.
- **Rechenprinzip LM-Seite:** entschieden (Parallel-Anzeige statt Ersatz, siehe eigener Abschnitt oben) — offen ist nur noch die Umsetzung in Phase 4/5.
- VM- und DS-Domänen: voller Umfang oder zunächst vereinfacht? (Konkretisiert in Phase 6 bzw. 7 — v.a. Rekursionsgrenze und Einheiten-Übersetzung.)
- Eigene MC-Engine endgültig zugunsten pyfair aufgeben, oder als Fallback behalten?
- Report: statisches HTML (wie pyfair) oder interaktiv (Plotly)? — Plotly ist in `pyfair_cam_mc_notiz.md` bereits als Dependency angedacht.
