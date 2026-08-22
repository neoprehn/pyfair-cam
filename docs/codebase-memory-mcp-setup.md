# codebase-memory-mcp — Installation & Anbindung an Claude Code (Windows)

**Erprobt am 27.07.2026 auf dem Heimrechner.** Diese Fassung beschreibt den Weg, der tatsächlich
funktioniert hat — nicht den aus dem README. Für den Laptop einfach von oben nach unten abarbeiten.

**Umgebung:** Windows · privater Rechner · VS Code mit Claude Code · Projekte unter `D:\Entwicklung\`

---

## ⚠️ Zwei bekannte Bugs, die Zeit kosten

| Problem | Auswirkung | Umgehung |
|---|---|---|
| `install.ps1` aus dem `main`-Branch bricht ab mit `unsafe or incomplete release archive: archive must contain exactly one codebase-memory-mcp.payload.exe` | Installation unmöglich | Archiv manuell laden, Binary direkt installieren (Schritt 1–3) |
| Installer schreibt den PATH-Eintrag nach `~/.profile` (Unix-Datei) | `codebase-memory-mcp` wird in PowerShell nicht gefunden | PATH von Hand setzen (Schritt 4) |

Der erste Bug ist gemeldet (Issue #1257, PR #1259 vom 25.07.2026). Vor der Installation auf dem
Laptop kurz prüfen, ob er behoben ist — dann geht der normale Weg über `install.ps1` wieder.
Die Prüfsummenmeldung `Checksum verified.` vor dem Fehler bedeutet: Das Archiv ist echt, nur der
Aufbau passt nicht zur Erwartung des Skripts. Kein Sicherheitsproblem.

---

## Schritt 1 — Archiv manuell herunterladen

Browser: <https://github.com/DeusData/codebase-memory-mcp/releases/latest>

Unter **Assets**: `codebase-memory-mcp-windows-amd64.zip` nach `D:\DeusData` speichern.

> `amd64` ist auch bei Intel-CPUs richtig — das ist der Architekturname (x86-64), nicht der
> Hersteller. Nur bei ARM-Geräten (Surface mit Snapdragon) wäre er falsch.
> Prüfen mit `$env:PROCESSOR_ARCHITECTURE`.

---

## Schritt 2 — Entpacken

```powershell
cd D:\DeusData
Expand-Archive .\codebase-memory-mcp-windows-amd64.zip -DestinationPath .\cbm -Force
Get-ChildItem .\cbm -Recurse | Unblock-File
Get-ChildItem .\cbm -Recurse | Select-Object Name
```

Erwartung: `codebase-memory-mcp.exe` ist in der Liste.

---

## Schritt 3 — Sicherung und Installation

```powershell
Copy-Item "$env:USERPROFILE\.claude.json" "$env:USERPROFILE\.claude.json.bak" -ErrorAction SilentlyContinue

.\cbm\codebase-memory-mcp.exe install
```

Das Binary bringt die Installationsroutine selbst mit — die Archivprüfung des `.ps1` entfällt damit.

**Erwartete Ausgabe:**

```
Detected agents: Claude-Code VS-Code
Claude Code:
  skills: 1 installed
  mcp: C:/Users/<Name>/.claude/.mcp.json
  hooks: PreToolUse / SessionStart / SubagentStart
...
Install complete.
```

Die Abschlusszeile `source C:/Users/<Name>/.profile` ist eine Unix-Ausgabe auf Windows und
funktionslos — ignorieren.

**Zielort des Binaries:** `C:\Users\<Name>\.local\bin\codebase-memory-mcp.exe`

---

## Schritt 4 — PATH reparieren

```powershell
$bin = "$env:USERPROFILE\.local\bin"
$alt = [Environment]::GetEnvironmentVariable("PATH","User")
if ($alt -notlike "*$bin*") {
    [Environment]::SetEnvironmentVariable("PATH", "$alt;$bin", "User")
    "PATH ergaenzt."
} else { "PATH war bereits gesetzt." }
```

**Neues PowerShell-Fenster öffnen**, dann:

```powershell
codebase-memory-mcp --version
```

> Bewusst `[Environment]::SetEnvironmentVariable` statt `setx` — `setx` kappt bei über
> 1024 Zeichen stillschweigend.

---

## Schritt 5 — MCP-Konfiguration ergänzen

Der Installer legt `C:\Users\<Name>\.claude\.mcp.json` an, **ohne** `env`-Block. Die Leitplanke
`CBM_ALLOWED_ROOT` muss von Hand hinein:

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

Vorwärts-Schrägstriche funktionieren unter Windows und sparen doppelte Backslashes.
Benutzernamen anpassen, falls auf dem Laptop anders.

`CBM_ALLOWED_ROOT` weist jeden Indizierungspfad ab, der nach Symlink- und `..`-Auflösung außerhalb
liegt. `CBM_CACHE_DIR` bewusst **nicht** gesetzt — Standard (`~/.cache/codebase-memory-mcp/`)
genügt und ist ein Wert weniger, der schiefgehen kann.

**Prüfen, ob ein zweiter Eintrag existiert:**

```powershell
Select-String -Path "$env:USERPROFILE\.claude.json" -Pattern "codebase-memory" -SimpleMatch
```

---

## Schritt 6 — Konfiguration

```powershell
codebase-memory-mcp config set auto_watch true
codebase-memory-mcp config list
```

**Sollstand:**

| Einstellung | Wert | Warum |
|---|---|---|
| `auto_watch` | `true` | Hintergrund-Watcher hält indizierte Projekte per Git-Polling aktuell — wichtig bei zwei Arbeitsgeräten |
| `auto_index` | `false` | Keine ungefragte Indizierung fremder Ordner |

---

## Schritt 7 — VS Code neu starten und prüfen

**Komplett schließen**, neu öffnen. In Claude Code:

```
/mcp
```

Erwartung: `codebase-memory-mcp` verbunden, 15 Tools.

---

## Schritt 8 — Projekte indizieren

⚠️ **Immer den absoluten Pfad angeben.** Claude Code orientiert sich am Arbeitsverzeichnis, nicht
an der geöffneten Datei — bei einem Multi-Root-Workspace erwischt es sonst den falschen Ordner.

In Claude Code, je Projekt:

```
Indiziere D:\Entwicklung\<ordner> mit codebase-memory-mcp, Projektname "<ordner>".
```

> **Projektname immer explizit angeben (`name`-Parameter).** Ohne ihn derivt das Tool automatisch
> `D-Entwicklung-<Ordner>` statt der Kurzform — bei bereits vorhandenem Kurzform-Eintrag entsteht
> ein zweites, divergierendes Duplikat (gefunden/bereinigt 22.08.2026). Siehe `delete_project` bei
> `list_projects`-Treffern mit `D-Entwicklung-*`-Präfix.

Aus **einem** Workspace heraus möglich — die anderen Ordner müssen nicht geöffnet sein.

Kontrolle:

```
Zeig mir list_projects.
```

### Aktueller Stand (Heimrechner, 27.07.2026)

| Projekt | Nodes | Edges | Rolle |
|---|---|---|---|
| `fair` | 473 | 2.666 | Monte-Carlo-Rechenkern FAIR |
| `pyfair-cam` | 809 | 2.271 | FAIR-CAM |
| `fair-web` | 960 | 3.797 | Frontend / UI |
| `iam` | 3.516 | 5.572 | |
| `ai-calculator` | 205 | 446 | |
| `forum-monitor` | 154 | 489 | |

> `status:"degraded"` statt `indexed` bedeutet: zu wenige Knoten persistiert — erneut indizieren.

---

## Ergänzung für den Session-Start-Prompt

Zwischen den `git pull`-Block und das Lesen von ROADMAP.md einfügen:

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

Der Watcher läuft nur, solange Claude Code aktiv ist. Ein Pull bei geschlossenem VS Code wird erst
mit Verzögerung bemerkt — deshalb die explizite Auffrischung.

---

## Alltagsnutzung

| Statt | Besser |
|---|---|
| „Schau dir `simulation.py` an…" | „In `fair`: `get_architecture` — gib mir den Überblick" |
| „Such alle Stellen mit Lognormal" | „In `fair`: `search_graph`, `name_pattern` für Lognormal" |
| „Wer ruft diese Funktion auf?" | „In `fair`: `trace_path` für `<Funktion>`, Richtung inbound" |
| „Was breche ich, wenn ich X ändere?" | „In `fair`: `detect_changes` — Blast Radius meiner Änderungen" |
| „Gibt es toten Code?" | „In `pyfair-cam`: Funktionen ohne Aufrufer" |

Repoübergreifend:

```
Wie ruft fair-web den Rechenkern in fair auf? Zeig mir die Verbindungen.
```

Vor jedem Commit lohnt `detect_changes` — bei drei gekoppelten Repositories der nützlichste
einzelne Aufruf.

---

## Zweiter Rechner (Laptop)

Index wird **nicht** synchronisiert — er ist ein wegwerfbarer Beschleuniger, Neuaufbau dauert
Sekunden.

1. Schritte 1–7 abarbeiten (Benutzernamen und Laufwerkspfade anpassen)
2. Projekte einmal indizieren (Schritt 8)

`.gitignore` je Projekt ergänzen:

```
.codebase-memory/
```

**Bewusst maschinenlokal — divergiert zwischen den Geräten:**

- der Graph-Index
- ADRs aus `manage_adr` (liegen in der lokalen SQLite-DB)
- Claude Codes Auto Memory (`~/.claude/projects/<project>/memory/`), davon lädt nur `MEMORY.md`
  mit den ersten 200 Zeilen bzw. 25 KB automatisch

→ Alles, was konsistent sein muss, gehört ins Repository: `ROADMAP.md`, `CLAUDE.md`,
`docs/adr/`.

---

## Rückbau

```powershell
codebase-memory-mcp uninstall
```

Entfernt Agent-Konfigurationseinträge, Skills, Hooks, Instruktionen und das Binary. Vorhandene
Graph-Indizes werden aufgelistet und erst nach Bestätigung gelöscht.

---

## Stolpersteine

| Symptom | Ursache / Abhilfe |
|---|---|
| `install.ps1` bricht mit `payload.exe`-Fehler ab | Bekannter Bug — Weg über Schritte 1–3 |
| `codebase-memory-mcp` nicht gefunden | PATH-Bug — Schritt 4, danach **neues** Fenster |
| `/mcp` zeigt nichts | VS Code nur neu geladen statt neu gestartet |
| Falscher Ordner indiziert | Absoluten Pfad angeben (Schritt 8) |
| Treffer aus fremdem Projekt | Projektnamen in der Frage mitgeben |
| `trace_path` liefert 0 Treffer | Erst `search_graph` mit `name_pattern` für den exakten Namen |
| Server doppelt in `/mcp` | Eintrag zusätzlich in VS Codes eigener `mcp.json` — einen entfernen |
| CLI-Aufrufe scheitern in PowerShell | JSON-Zitierregeln — Aufrufe über Claude Code stellen |
