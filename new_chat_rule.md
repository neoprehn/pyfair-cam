Lies bitte:

    Als allererstes: git pull (bzw. mind. git fetch + Abgleich mit origin/main) — es gibt seit
    2026-07-12 zwei Arbeitsgeräte (Heim-Rechner + mobiler Laptop für Zugfahrten), der lokale Stand
    kann also hinter dem sein, was vom jeweils anderen Gerät gepusht wurde. Erst danach die
    folgenden Dateien lesen, sonst ggf. veralteter Stand:
    ROADMAP.md — „Stand" + offene Punkte mit [ ]/[~]/[x] (das ist der eigentliche Übergabepunkt),
    ROADMAP-ARCHIV.md — was erledigt ist,
    Git-Historie — jeder Commit beschreibt einen Schritt,
    das persistente Memory (MEMORY.md + memory/*.md) — wird in jede neue Session geladen,
    CLAUDE.md — Projektregeln.

    Danach kurz die FAIR-CAM Knowledge Base (Submodule `knowledge-base/`) gegen upstream
    (https://github.com/faircam/FAIR-CAM-Knowledge-Base, Branch main) prüfen:
    `cd knowledge-base && git fetch origin && git log --oneline -1 origin/main` mit dem
    aktuell eingebundenen Commit vergleichen. Bei Abweichung kurz Bescheid geben, nicht
    automatisch aktualisieren (Auffrischen: `git submodule update --remote knowledge-base`
    + Commit des neuen Submodule-Pointers im Hauptrepo).

Was steht als nächstes an?

