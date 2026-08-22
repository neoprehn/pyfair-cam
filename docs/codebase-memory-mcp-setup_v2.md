# codebase-memory-mcp auf Rechner 2 einrichten

**Eigenständige Anleitung — ohne Rückfragen durcharbeitbar.**
Erprobt am 27.07.2026 auf dem Heimrechner (Windows, VS Code, Claude Code).

Jeder Schritt nennt: **Befehl → was passiert → erwartete Ausgabe → was tun, wenn es abweicht.**
Wenn die Ausgabe zur Erwartung passt, einfach weiter. Nur bei Abweichung in den jeweiligen
Abweichungs-Kasten schauen.

Dauer: etwa 20 Minuten.

---

## Inhalt

- [Was am Ende erreicht ist](#was-am-ende-erreicht-ist)
- [Vorbereitung](#vorbereitung)
- [Teil A — Installation](#teil-a--installation)
- [Teil B — PATH reparieren](#teil-b--path-reparieren)
- [Teil C — MCP-Konfiguration](#teil-c--mcp-konfiguration)
- [Teil D — Grundeinstellungen](#teil-d--grundeinstellungen)
- [Teil E — Verifikation](#teil-e--verifikation)
- [Teil F — Projekte indizieren](#teil-f--projekte-indizieren)
- [Teil G — Session-Prompt ergänzen](#teil-g--session-prompt-ergänzen)
- [Alltagsnutzung](#alltagsnutzung)
- [Abschluss-Checkliste](#abschluss-checkliste)
- [Anhang: Fehlerbaum](#anhang-fehlerbaum)
- [Anhang: Rückbau und Neuanfang](#anhang-rückbau-und-neuanfang)

---

## Was am Ende erreicht ist

codebase-memory-mcp indiziert Ihre Repositories in einen Knotengraphen (Funktionen, Klassen,
Aufrufketten, Importe) und stellt Claude Code 15 Werkzeuge zur Verfügung, um diesen Graphen
abzufragen. Statt Dateien einzeln zu lesen, stellt Claude Code eine Strukturabfrage.

**Warum das lohnt:** Fünf Strukturabfragen brauchen laut Projektmessung rund 3.400 Token gegenüber
rund 412.000 bei datei-für-datei-Exploration. Der praktische Effekt: Claude Code verbringt nicht
die erste halbe Stunde jeder Session mit Grep-Archäologie.

**Was es nicht ist:** kein Gedächtnis für Entscheidungen. Es weiß, *was* der Code tut, nicht
*warum* er so gebaut ist. Dafür bleiben `ROADMAP.md`, `CLAUDE.md` und die Git-Historie zuständig.

Am Ende dieser Anleitung ist eingerichtet:

| Komponente | Wirkung |
|---|---|
| Binary + MCP-Server | 15 Werkzeuge in Claude Code |
| Skill | Claude Code weiß, wann der Graph statt Grep zu nutzen ist |
| Drei Graph-Agenten | **Scout** (schnelle vorläufige Suche) · **Verify** (Standard, mit Belegpflicht) · **Auditor** (vollständige Prüfung) |
| Hooks | `PreToolUse` bei Grep/Glob, `SessionStart`, `SubagentStart` — alle nicht-blockierend |
| Indizes | ein Graph je Projekt, alle im selben Store und dadurch untereinander verknüpft |

---

## Vorbereitung

### Voraussetzungen

- Windows 64-Bit (Intel oder AMD — beides `amd64`)
- VS Code mit Claude Code, mindestens einmal gestartet
- Ein Arbeitsverzeichnis für den Download, im Folgenden `D:\DeusData`
- Die Projekte liegen unter einem gemeinsamen Ordner, im Folgenden `D:\Entwicklung`

### Platzhalter anpassen

Diese Anleitung nutzt Pfade vom Heimrechner. Prüfen Sie zuerst, was auf dem Laptop gilt:

```powershell
echo $env:USERNAME
echo $env:USERPROFILE
Test-Path D:\Entwicklung
```

**Erwartete Ausgabe** (Beispiel):

```
mirko
C:\Users\mirko
True
```

> **Wenn `Test-Path` `False` liefert:** Die Projekte liegen auf dem Laptop woanders. Notieren Sie
> den tatsächlichen Pfad und ersetzen Sie `D:\Entwicklung` in **Teil C und F** durchgängig.
> Alles andere bleibt gleich.

Wo unten `mirko` steht, gehört Ihr Benutzername hin. Die meisten Befehle nutzen `$env:USERPROFILE`
und passen sich automatisch an — nur der JSON-Block in Teil C enthält den Namen ausgeschrieben.

### Architektur prüfen

```powershell
$env:PROCESSOR_ARCHITECTURE
```

**Erwartet:** `AMD64`

> `amd64` ist der Name der 64-Bit-Architektur (auch bekannt als x86-64 oder x64), nicht des
> Herstellers. Bei Intel-CPUs ist `amd64` korrekt.
>
> **Wenn dort `ARM64` steht** (Surface mit Snapdragon o. ä.): In Teil A statt der `amd64`-Datei
> die ARM64-Variante nehmen, falls vorhanden. Gibt es keine, endet die Anleitung hier.

---

## Teil A — Installation

### A.1 Zuerst den offiziellen Weg versuchen

Am 27.07.2026 war der Standard-Installer defekt (siehe A.2). Falls der Bug inzwischen behoben ist,
ist das der kürzere Weg — also erst probieren.

```powershell
cd D:\DeusData
Invoke-WebRequest -Uri https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.ps1 -OutFile install.ps1
Unblock-File .\install.ps1
.\install.ps1
```

**Wenn die Ausgabe mit `Install complete.` endet** → weiter bei **Teil B**.

**Wenn diese Zeile erscheint:**

```
error: unsafe or incomplete release archive: archive must contain exactly one codebase-memory-mcp.payload.exe
```

→ weiter bei **A.2**. Das ist der bekannte Bug.

> **Was dieser Fehler bedeutet:** Die Zeile `Checksum verified.` davor sagt, dass das
> heruntergeladene Archiv exakt dem veröffentlichten Artefakt entspricht — es ist unverfälscht.
> Der Abbruch kommt erst danach: Das Skript aus dem `main`-Branch erwartet im ZIP eine Datei
> `codebase-memory-mcp.payload.exe`, das Release liefert die Exe aber flach ohne diesen Wrapper.
> Skript und Archiv sind auseinandergelaufen. **Kein Sicherheitsproblem** — das Skript verhält
> sich korrekt, indem es nichts installiert, dessen Aufbau es nicht verifizieren kann.
> Gemeldet als Issue #1257, Pull Request #1259 vom 25.07.2026.

> **Wenn ein Execution-Policy-Fehler erscheint:**
> ```powershell
> Set-ExecutionPolicy -Scope Process Bypass
> ```
> Danach `.\install.ps1` erneut. Gilt nur für dieses Fenster.

> **Wenn SmartScreen warnt:** „Weitere Informationen" → „Trotzdem ausführen". Die Integrität ist
> über die `checksums.txt` des Releases prüfbar; jedes Release ist zusätzlich Sigstore-signiert.

### A.2 Umgehungsweg — Archiv manuell, Binary installiert sich selbst

**Schritt 1 — Archiv laden.** Im Browser öffnen:

<https://github.com/DeusData/codebase-memory-mcp/releases/latest>

Unter **Assets** die Datei `codebase-memory-mcp-windows-amd64.zip` nach `D:\DeusData` speichern.

**Schritt 2 — Entpacken:**

```powershell
cd D:\DeusData
Expand-Archive .\codebase-memory-mcp-windows-amd64.zip -DestinationPath .\cbm -Force
Get-ChildItem .\cbm -Recurse | Unblock-File
Get-ChildItem .\cbm -Recurse | Select-Object Name
```

**Erwartete Ausgabe:** eine Dateiliste, die `codebase-memory-mcp.exe` enthält.

> `Unblock-File` entfernt die „Mark of the Web"-Markierung, die Windows an heruntergeladene
> Dateien hängt. Ohne das verweigert Windows später möglicherweise die Ausführung.

> **Wenn `codebase-memory-mcp.exe` nicht in der Liste steht:** Das Archiv hat einen anderen Aufbau
> als erwartet. Sehen Sie sich die vollen Pfade an — die Exe liegt eventuell in einem Unterordner:
> ```powershell
> Get-ChildItem .\cbm -Recurse -Filter *.exe | Select-Object FullName
> ```
> Den gefundenen Pfad in Schritt 3 einsetzen.

**Schritt 3 — Sicherung und Installation:**

```powershell
Copy-Item "$env:USERPROFILE\.claude.json" "$env:USERPROFILE\.claude.json.bak" -ErrorAction SilentlyContinue
.\cbm\codebase-memory-mcp.exe install
```

Das Binary bringt die Installationsroutine selbst mit. Die Archivprüfung des Skripts entfällt,
weil nichts mehr entpackt werden muss.

**Erwartete Ausgabe** (Pfade mit Ihrem Benutzernamen):

```
Detected agents: Claude-Code VS-Code

Claude Code:
  skills: 1 installed
  mcp: C:/Users/mirko/.claude/.mcp.json
  mcp: C:/Users/mirko/.claude.json
  hooks: PreToolUse (Grep/Glob search-graph augmenter, non-blocking)
  hooks: SessionStart (MCP usage reminder on startup/resume/clear/compact)
  hooks: SubagentStart (MCP usage reminder for subagents)
VS Code:
  mcp: C:/Users/mirko/AppData/Roaming/Code/User/mcp.json
VS Code:
  mcp: C:/Users/mirko/AppData/Roaming/Code/User/profiles/builtin/mcp.json

PATH already includes C:/Users/mirko/.local/bin

Install complete. Restart your shell or run:
  source C:/Users/mirko/.profile
```

**Das Binary liegt jetzt unter:** `C:\Users\<Benutzer>\.local\bin\codebase-memory-mcp.exe`

> **Zur letzten Zeile:** `source ... .profile` ist eine Unix-Ausgabe auf Windows und funktionslos.
> Ignorieren. Sie ist gleichzeitig der Hinweis auf den PATH-Bug in Teil B.

> **Wenn „Detected agents" leer bleibt oder Claude Code fehlt:** Claude Code wurde auf diesem
> Rechner noch nie gestartet, deshalb existiert das Konfigurationsverzeichnis nicht. VS Code
> öffnen, Claude Code einmal starten, VS Code schließen, dann `install` erneut ausführen.

---

## Teil B — PATH reparieren

Der Installer meldet zwar `PATH already includes ...`, schreibt den Eintrag aber nach
`~/.profile` — eine Unix-Datei, die PowerShell nie liest. Der Befehl ist deshalb in der Konsole
nicht auffindbar.

**Das blockiert die Funktion nicht** (Claude Code startet den Server über den absoluten Pfad),
ist aber für die Konfigurationsbefehle unten lästig.

```powershell
$bin = "$env:USERPROFILE\.local\bin"
$alt = [Environment]::GetEnvironmentVariable("PATH","User")
if ($alt -notlike "*$bin*") {
    [Environment]::SetEnvironmentVariable("PATH", "$alt;$bin", "User")
    "PATH ergaenzt."
} else { "PATH war bereits gesetzt." }
```

**Erwartete Ausgabe:** `PATH ergaenzt.`

Jetzt **ein neues PowerShell-Fenster öffnen** (die Änderung wirkt nur in neuen Prozessen) und
testen:

```powershell
codebase-memory-mcp --version
```

**Erwartet:** eine Versionsnummer, z. B. `0.9.0`

> Bewusst `[Environment]::SetEnvironmentVariable` statt `setx`: `setx` kappt Werte über
> 1024 Zeichen stillschweigend, und ein gewachsener Windows-PATH ist oft länger.

> **Wenn der Befehl weiterhin nicht gefunden wird:** Nicht weiter suchen — es geht auch ohne.
> Setzen Sie für den Rest der Anleitung eine Abkürzung und verwenden Sie überall `& $cbm` statt
> `codebase-memory-mcp`:
> ```powershell
> $cbm = "$env:USERPROFILE\.local\bin\codebase-memory-mcp.exe"
> & $cbm --version
> ```
> Diese Variable gilt nur im aktuellen Fenster und muss nach jedem Neustart neu gesetzt werden.

---

## Teil C — MCP-Konfiguration

Der Installer legt `C:\Users\<Benutzer>\.claude\.mcp.json` an — mit dem Pfad zum Binary, aber
**ohne** Umgebungsvariablen. Die Leitplanke ergänzen wir von Hand.

Erst ansehen, was dort steht:

```powershell
Get-Content "$env:USERPROFILE\.claude\.mcp.json"
```

**Erwartete Ausgabe:**

```json
{
    "mcpServers": {
        "codebase-memory-mcp": {
            "command": "C:/Users/mirko/.local/bin/codebase-memory-mcp.exe"
        }
    }
}
```

Jetzt die Datei mit `env`-Block neu schreiben. **Benutzernamen und Entwicklungspfad anpassen:**

```powershell
$json = @'
{
    "mcpServers": {
        "codebase-memory-mcp": {
            "command": "C:/Users/mirko/.local/bin/codebase-memory-mcp.exe",
            "env": {
                "CBM_ALLOWED_ROOT": "D:/Entwicklung"
            }
        }
    }
}
'@
[System.IO.File]::WriteAllText("$env:USERPROFILE\.claude\.mcp.json", $json)
Get-Content "$env:USERPROFILE\.claude\.mcp.json"
```

**Erwartet:** die Datei wird mit dem `env`-Block ausgegeben.

> **Warum `CBM_ALLOWED_ROOT`:** Die Variable weist jeden Indizierungspfad ab, der nach Symlink-
> und `..`-Auflösung außerhalb des angegebenen Verzeichnisses liegt. Das begrenzt, was ein Agent
> versehentlich einlesen kann — nützlich, weil der Server agentisch angesteuert wird.
>
> **Warum Vorwärts-Schrägstriche:** funktionieren unter Windows und sparen die doppelten
> Backslashes, die JSON sonst verlangt (`D:\\Entwicklung`). Weniger Fehlerquellen.
>
> **Warum kein `CBM_CACHE_DIR`:** Der Standard (`~/.cache/codebase-memory-mcp/`) genügt. Ein
> eigener Ort lohnt nur bei Platzmangel auf `C:` — und er darf **nie** auf einem externen Laufwerk,
> Netzlaufwerk oder in einem Sync-Ordner (OneDrive, Dropbox) liegen: Die SQLite-Datenbank läuft im
> WAL-Modus, den solche Speicherorte nicht zuverlässig unterstützen.

**Zweiten Eintrag prüfen.** Der Installer nannte auch `.claude.json`:

```powershell
Select-String -Path "$env:USERPROFILE\.claude.json" -Pattern "codebase-memory" -SimpleMatch
```

- **Keine Ausgabe** → gut, nichts zu tun.
- **Eine Trefferzeile** → der Server ist doppelt registriert. Siehe Teil E, Abschnitt „Zwei Server".

---

## Teil D — Grundeinstellungen

```powershell
codebase-memory-mcp config set auto_watch true
codebase-memory-mcp config list
```

**Erwartete Ausgabe:**

```
Configuration:
  auto_index                = false
  auto_index_limit          = 50000
  auto_watch                = true
  ui-lang                   = auto
```

| Einstellung | Sollwert | Begründung |
|---|---|---|
| `auto_watch` | `true` | Hintergrund-Watcher erkennt Dateiänderungen per Git-Polling und indiziert nach. **Wichtig bei zwei Arbeitsgeräten:** Nach einem `git pull` kennt der lokale Index die Änderungen vom anderen Gerät sonst nicht — und meldet das nicht. |
| `auto_index` | `false` | Verhindert, dass beim Öffnen eines beliebigen fremden Ordners ungefragt indiziert wird. |

> **Grenze des Watchers:** Er läuft als Hintergrundthread des MCP-Servers, also nur solange
> Claude Code aktiv ist. Ein `git pull` bei geschlossenem VS Code wird erst mit Verzögerung
> bemerkt. Deshalb steht in Teil G eine explizite Auffrischung im Session-Prompt.

---

## Teil E — Verifikation

**VS Code komplett schließen und neu starten.** Nicht nur das Fenster neu laden — der MCP-Server
wird beim Programmstart hochgefahren.

Dann in Claude Code eingeben:

```
/mcp
```

**Erwartet:** `codebase-memory-mcp` ist verbunden, 15 Tools.

### Wenn nichts erscheint

Der Reihe nach prüfen:

1. VS Code wirklich **beendet** und neu gestartet, nicht nur neu geladen?
2. Ist der Pfad in `.mcp.json` absolut und zeigt auf eine existierende Datei?
   ```powershell
   Test-Path "$env:USERPROFILE\.local\bin\codebase-memory-mcp.exe"
   ```
   Erwartet: `True`
3. Startet das Binary überhaupt als Server?
   ```powershell
   echo '{}' | & "$env:USERPROFILE\.local\bin\codebase-memory-mcp.exe"
   ```
   Erwartet: eine JSON-Zeile. Kommt eine Fehlermeldung, ist das Binary beschädigt — Teil A
   wiederholen.
4. Ist die JSON-Datei gültig? Ein fehlendes Komma reicht, damit der Eintrag stumm ignoriert wird:
   ```powershell
   Get-Content "$env:USERPROFILE\.claude\.mcp.json" | ConvertFrom-Json
   ```
   Erwartet: eine strukturierte Ausgabe ohne Fehler.

### Zwei Server

Zeigt `/mcp` zwei Einträge, prüfen Sie im Terminal mit `/mcp`, ob beide auf dieselbe `.exe`
zeigen. Falls ja, ist der Server doppelt registriert — zwei Prozesse auf derselben Datenbank
vertragen sich nicht.

Den Eintrag aus `.claude.json` entfernen (die Datei mit einem Editor öffnen, den Block
`codebase-memory-mcp` samt umgebender Kommata löschen), `.claude\.mcp.json` behalten. Vorher liegt
ja eine Sicherung `.claude.json.bak` aus Teil A.

Ist der zweite Server ein anderer (etwa ein bereits vorher eingerichteter), ist alles in Ordnung.

---

## Teil F — Projekte indizieren

### Wichtigste Regel: immer den absoluten Pfad angeben

Claude Code orientiert sich beim Indizieren am **Arbeitsverzeichnis**, nicht an der gerade
geöffneten Datei. In einem Multi-Root-Workspace erwischt es sonst den falschen Ordner — auf dem
Heimrechner wurde beim ersten Versuch `fair` indiziert, obwohl eine Datei aus `pyfair-cam` offen
war.

### Pfade ermitteln

```powershell
Get-ChildItem D:\Entwicklung -Directory | Select-Object FullName
```

### Indizieren

In Claude Code, je Projekt eine Nachricht:

```
Indiziere D:\Entwicklung\fair mit codebase-memory-mcp, Projektname "fair".
```

Das geht **aus einem einzigen Workspace heraus** — die übrigen Ordner müssen nicht geöffnet sein.
Nur `CBM_ALLOWED_ROOT` muss den Pfad umfassen.

> **Projektname immer explizit angeben (`name`-Parameter).** Ohne ihn derivt das Tool automatisch
> `D-Entwicklung-<Ordner>` aus dem Pfad statt der Kurzform. Fehlt der Parameter bei einem bereits
> unter Kurzform indizierten Projekt, entsteht ein zweiter, divergierender Eintrag (gefunden und
> bereinigt am 22.08.2026 — drei `D-Entwicklung-*`-Duplikate). Zeigt `list_projects` einen
> `D-Entwicklung-*`-Eintrag neben der Kurzform: das ist ein Duplikat, mit `delete_project` auf den
> langen Namen entfernen.

**Erwartete Ausgabe je Lauf:**

```
Codebase-memory-mcp [index_repository]
OUT {"project":"D-Entwicklung-fair","excluded":{"dirs":[".claude",".git",...]}}
Indexed successfully: project D-Entwicklung-fair — 473 nodes, 2666 edges.
```

Dauer: Sekunden bis maximal wenige Minuten.

> **Wenn `status:"degraded"` statt `indexed` erscheint:** Es wurden weniger Knoten persistiert als
> erwartet. Denselben Befehl noch einmal ausführen.

> **Wenn der falsche Ordner indiziert wurde:** Kein Problem, einfach den richtigen Pfad noch einmal
> angeben. Überzählige Projekte lassen sich später mit `delete_project` entfernen.

### Kontrolle

```
Zeig mir list_projects.
```

**Sollstand nach dem Heimrechner-Setup:**

| Projekt | Nodes | Edges | Rolle |
|---|---|---|---|
| `fair` | 473 | 2.666 | Monte-Carlo-Rechenkern FAIR |
| `pyfair-cam` | 809 | 2.271 | FAIR-CAM |
| `fair-web` | 960 | 3.797 | Frontend / UI |
| `iam` | 3.516 | 5.572 | |
| `ai-calculator` | 205 | 446 | |
| `forum-monitor` | 154 | 489 | |

Die Zahlen dürfen abweichen, wenn seitdem Code dazugekommen ist. Deutlich **kleinere** Zahlen
deuten auf einen unvollständigen Lauf hin — dann neu indizieren.

### `.gitignore` ergänzen

Je Projekt:

```
.codebase-memory/
```

> Das Tool kann einen komprimierten Graph-Schnappschuss `.codebase-memory/graph.db.zst` neben dem
> Quellcode ablegen, damit Teammitglieder den Index nicht neu aufbauen müssen. Bei
> Einzelentwicklung lohnt das nicht: Neuindizierung dauert Sekunden, und die Binärdatei würde bei
> jeder Änderung die Commit-Historie verrauschen.

---

## Teil G — Session-Prompt ergänzen

In den bestehenden Session-Start-Prompt, **zwischen** den `git pull`-Block und das Lesen von
`ROADMAP.md`:

```markdown
    Nach dem Pull den Graph-Index auffrischen und den Projektnamen merken:
    index_repository für das aktuelle Repo aufrufen (der Pull kann Änderungen
    vom anderen Gerät gebracht haben, die der lokale Index noch nicht kennt),
    danach index_status prüfen.
    Projektnamen für codebase-memory-mcp in diesem Workspace:
    fair (Rechenkern), pyfair-cam (CAM), fair-web (Frontend).

    Für Struktur-, Aufruf- und Auswirkungsfragen den Graphen verwenden
    (search_graph, trace_path, detect_changes, get_architecture) statt
    Dateien einzeln zu lesen. Projektnamen dabei immer mitgeben.

    Wenn eine der genannten Quellen fehlt, leer ist oder älter als der letzte
    Commit wirkt: sag es mir, statt es zu überspringen.
```

**Warum die Projektnamen wichtig sind:** Ohne sie durchsucht Claude Code alle indizierten
Projekte und liefert Treffer aus `iam` oder `forum-monitor`, wenn es um den Rechenkern geht.

---

## Alltagsnutzung

| Statt | Besser |
|---|---|
| „Schau dir `simulation.py` an und erklär mir…" | „In `fair`: `get_architecture` — gib mir den Überblick" |
| „Such alle Stellen mit Lognormal" | „In `fair`: `search_graph`, `name_pattern` für Lognormal" |
| „Wer ruft diese Funktion auf?" | „In `fair`: `trace_path` für `<Funktion>`, Richtung inbound" |
| „Was breche ich, wenn ich X ändere?" | „In `fair`: `detect_changes` — Blast Radius meiner Änderungen" |
| „Gibt es toten Code?" | „In `pyfair-cam`: Funktionen ohne Aufrufer" |

**Repoübergreifend** (funktioniert, weil alle Projekte im selben Store liegen und automatisch mit
`CROSS_*`-Kanten verknüpft werden):

```
Wie ruft fair-web den Rechenkern in fair auf? Zeig mir die Verbindungen.
```

**Vor jedem Commit** — bei drei gekoppelten Repositories der nützlichste einzelne Aufruf:

```
In fair: detect_changes — was ist der Blast Radius meiner Änderungen?
```

### Werkzeugübersicht

| Werkzeug | Zweck |
|---|---|
| `get_graph_schema` | Knoten-/Kantenzahlen, Beziehungsmuster — zu Sessionbeginn |
| `get_architecture` | Sprachen, Pakete, Einstiegspunkte, Routen, Hotspots, Cluster |
| `search_graph` | Suche nach Label, Namensmuster, Dateimuster, Grad |
| `trace_path` | Aufrufkette vorwärts/rückwärts, Tiefe 1–5 |
| `detect_changes` | Git-Diff auf betroffene Symbole mit Risikoklassifikation |
| `query_graph` | Cypher-Abfragen (nur lesend) |
| `get_code_snippet` | Quelltext einer Funktion über den qualifizierten Namen |
| `search_code` | Grep innerhalb indizierter Dateien |
| `manage_adr` | Architekturentscheidungen — siehe Warnung unten |
| `index_repository`, `list_projects`, `index_status`, `delete_project` | Indexverwaltung |

> **Warnung zu `manage_adr`:** Diese Entscheidungen landen in der lokalen SQLite-Datenbank und
> werden **nicht** zwischen Ihren Geräten synchronisiert. Auf Heimrechner und Laptop entstünden
> zwei divergierende Entscheidungsstände, ohne dass es auffällt. Architekturentscheidungen gehören
> als Markdown ins Repository (`ROADMAP.md`, `docs/adr/`), wo Git sie mitnimmt.

---

## Abschluss-Checkliste

- [ ] `codebase-memory-mcp --version` liefert eine Versionsnummer
- [ ] `.claude\.mcp.json` enthält `command` **und** `env` mit `CBM_ALLOWED_ROOT`
- [ ] `config list` zeigt `auto_watch = true`, `auto_index = false`
- [ ] `/mcp` in Claude Code zeigt den Server mit 15 Tools, **einmal**
- [ ] `list_projects` zeigt alle Projekte mit plausiblen Knotenzahlen
- [ ] `.codebase-memory/` steht in den `.gitignore`-Dateien
- [ ] Session-Prompt um den Block aus Teil G ergänzt
- [ ] Funktionstest: „In `fair`: gib mir einen Architekturüberblick" liefert eine sinnvolle Antwort

---

## Anhang: Fehlerbaum

| Symptom | Ursache | Abhilfe |
|---|---|---|
| `install.ps1` bricht mit `payload.exe`-Fehler ab | Bekannter Bug (#1257) | Teil A.2 |
| `codebase-memory-mcp` nicht gefunden | PATH-Eintrag ging nach `.profile` | Teil B; notfalls `$cbm`-Variable |
| Befehl nach PATH-Reparatur immer noch nicht gefunden | Altes Fenster | Neues PowerShell-Fenster öffnen |
| `/mcp` zeigt nichts | VS Code nur neu geladen; oder ungültiges JSON | Teil E, Punkte 1–4 |
| Server erscheint doppelt | Eintrag in `.claude.json` **und** `.claude\.mcp.json` | Teil E, „Zwei Server" |
| Falscher Ordner indiziert | Arbeitsverzeichnis statt offener Datei | Absoluten Pfad angeben |
| `status:"degraded"` | Unvollständiger Lauf | Erneut indizieren |
| Treffer aus fremdem Projekt | Kein Projektname in der Frage | Projektnamen mitgeben |
| `trace_path` liefert 0 Treffer | Funktionsname nicht exakt | Erst `search_graph` mit `name_pattern` |
| Ergebnisse wirken veraltet | Index nach `git pull` nicht aufgefrischt | `index_repository` erneut; `auto_watch` prüfen |
| CLI-Aufrufe mit JSON scheitern | PowerShell-Zitierregeln | Aufrufe über Claude Code stellen statt über die CLI |

---

## Anhang: Rückbau und Neuanfang

Alles entfernen:

```powershell
codebase-memory-mcp uninstall
```

Entfernt die vom Tool angelegten Agent-Konfigurationseinträge, Skills, Hooks, Instruktionen und
das Binary. Vorhandene Graph-Indizes werden aufgelistet und erst nach ausdrücklicher Bestätigung
gelöscht.

Nur die Indizes verwerfen (Neuaufbau dauert Sekunden):

```powershell
Remove-Item "$env:USERPROFILE\.cache\codebase-memory-mcp" -Recurse -Force
```

Konfiguration zurücksetzen:

```powershell
codebase-memory-mcp config reset auto_watch
```

Sicherung der MCP-Konfiguration zurückspielen:

```powershell
Copy-Item "$env:USERPROFILE\.claude.json.bak" "$env:USERPROFILE\.claude.json" -Force
```

---

## Was bewusst maschinenlokal bleibt

Diese Dinge unterscheiden sich zwischen Heimrechner und Laptop — das ist Absicht, kein Fehler:

- **Der Graph-Index.** Wegwerfartefakt, in Sekunden neu gebaut. Nicht synchronisieren.
- **ADRs aus `manage_adr`.** Liegen in der lokalen Datenbank.
- **Claude Codes Auto Memory** unter `~/.claude/projects/<project>/memory/`. Davon lädt nur
  `MEMORY.md` automatisch, und auch nur die ersten 200 Zeilen bzw. 25 KB; die Themendateien
  daneben werden bei Bedarf gelesen.

Alles, was zwischen den Geräten konsistent sein muss, gehört ins Repository: `ROADMAP.md`,
`ROADMAP-ARCHIV.md`, `CLAUDE.md`, `docs/adr/`. Der `git pull` zu Beginn jeder Session ist damit
der eigentliche Synchronisationsmechanismus.
