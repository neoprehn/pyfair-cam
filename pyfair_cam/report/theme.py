"""
theme – Design-Tokens für den HTML-Report.

Übernimmt Schrift (Bahnschrift), Sky-Blau-Akzent und das Dark/Light-Farbschema
aus fair-web (``fair-web/templates/base.html``), damit ein pyfair-cam-Report
optisch zur restlichen FAIR-Toolchain passt. Der Report ist trotzdem
vollständig eigenständig (keine Bootstrap-CDN-Abhängigkeit – DoD ist eine
einzelne, offline lauffähige HTML-Datei), daher ein eigenes, schlankes CSS
statt fair-webs Bootstrap-Overrides.

Chart-Farben sind die validierte Default-Palette aus der ``dataviz``-Skill
(``references/palette.md``), gegen die tatsächlichen fair-web-Oberflächen
(``--bg-1`` dunkel/hell) geprüft (``scripts/validate_palette.js``) – nicht
eigens erfunden.
"""

# Kategoriale Palette (validiert, adjacent-pairlist – ausreichend für Bar-
# Charts mit direkten Beschriftungen). Reihenfolge ist die CVD-Sicherheit,
# nicht kosmetisch – nicht umsortieren. Als CSS-Variablen (--cat-1 .. --cat-5)
# in CSS unten hinterlegt, damit Chart-Datenfarben dem Theme-Toggle folgen,
# nicht nur Text/Rahmen. Diese Python-Liste ist nur die Referenz für Legenden
# (Label + welcher Slot), die Farbwerte selbst kommen zur Laufzeit aus der CSS-Variable.
CATEGORICAL_SLOTS = ["var(--cat-1)", "var(--cat-2)", "var(--cat-3)", "var(--cat-4)", "var(--cat-5)"]

# Status-Palette (fix, nicht themebar) – immer mit Icon/Label, nie Farbe allein.
STATUS = {
    "good": "var(--status-good)",
    "warning": "var(--status-warning)",
    "serious": "var(--status-serious)",
    "critical": "var(--status-critical)",
}

CSS = """
:root[data-theme="dark"] {
  --bg-0:#020617; --bg-1:#07111f; --bg-2:#0f172a; --bg-3:#101826;
  --txt:#f8fafc; --txt-muted:#cbd5e1; --txt-dim:#94a3b8;
  --accent:#7dd3fc; --accent-2:#93c5fd; --ok:#86efac; --danger:#f87171;
  --border:#1e293b; --card-shadow: 0 18px 60px rgba(2,6,23,.45);
  --grid: #1e293b;
  --cat-1:#3987e5; --cat-2:#d95926; --cat-3:#199e70; --cat-4:#c98500; --cat-5:#d55181;
  --status-good:#0ca30c; --status-warning:#fab219; --status-serious:#ec835a; --status-critical:#d03b3b;
}
:root[data-theme="light"] {
  --bg-0:#ffffff; --bg-1:#f4f7fb; --bg-2:#ffffff; --bg-3:#eef2f7;
  --txt:#0f172a; --txt-muted:#334155; --txt-dim:#64748b;
  --accent:#0284c7; --accent-2:#0369a1; --ok:#16a34a; --danger:#dc2626;
  --border:#d8e0ea; --card-shadow: 0 10px 30px rgba(15,23,42,.08);
  --grid: #d8e0ea;
  --cat-1:#2a78d6; --cat-2:#eb6834; --cat-3:#1baf7a; --cat-4:#eda100; --cat-5:#e87ba4;
  --status-good:#0ca30c; --status-warning:#fab219; --status-serious:#ec835a; --status-critical:#d03b3b;
}
* { box-sizing: border-box; }
body {
  margin: 0; font-family: Bahnschrift, "Segoe UI", sans-serif;
  background: var(--bg-1); color: var(--txt-muted);
}
.wrap { max-width: 1120px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
header.report-header {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;
}
h1, h2, h3 { color: var(--txt); letter-spacing: .2px; margin: 0 0 .75rem; }
h1 { font-size: 1.6rem; }
h2 { font-size: 1.15rem; margin-top: 2.5rem; }
p.subtitle { color: var(--txt-dim); margin: .2rem 0 0; }
.theme-toggle {
  border-radius: 999px; border: 1px solid var(--border); background: var(--bg-2);
  color: var(--txt-muted); padding: .4rem .9rem; font: inherit; cursor: pointer;
}
.theme-toggle:hover { border-color: var(--accent); color: var(--txt); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: .9rem; }
.card {
  background: var(--bg-2); border: 1px solid var(--border); border-radius: 1rem;
  box-shadow: var(--card-shadow); padding: 1.25rem 1.4rem;
}
.stat-tile .label { color: var(--txt-dim); font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }
.stat-tile .value { color: var(--txt); font-size: 1.5rem; font-weight: 600; margin-top: .3rem; font-variant-numeric: tabular-nums; }
.section { margin-top: 1rem; }
table { width: 100%; border-collapse: collapse; font-size: .92rem; }
th, td { text-align: left; padding: .5rem .6rem; border-bottom: 1px solid var(--border); }
th { color: var(--txt-dim); text-transform: uppercase; font-size: .74rem; letter-spacing: .06em; font-weight: 600; }
td { color: var(--txt-muted); font-variant-numeric: tabular-nums; }
td.num, th.num { text-align: right; }
.note {
  font-size: .85rem; color: var(--txt-dim); border-left: 3px solid var(--accent);
  padding: .4rem .9rem; margin-top: .8rem; background: var(--bg-3); border-radius: 0 .5rem .5rem 0;
}
.legend { display: flex; flex-wrap: wrap; gap: .9rem; margin-top: .6rem; font-size: .82rem; color: var(--txt-dim); }
.legend .swatch { display: inline-block; width: .7rem; height: .7rem; border-radius: 2px; margin-right: .35rem; vertical-align: -1px; }
.chart-svg text { fill: var(--txt-dim); font-family: Bahnschrift, "Segoe UI", sans-serif; }
.chart-svg .axis-line { stroke: var(--grid); stroke-width: 1; }
.chart-svg .gridline { stroke: var(--grid); stroke-width: 1; opacity: .6; }
.badge { display: inline-block; padding: .15rem .55rem; border-radius: 999px; font-size: .72rem; font-weight: 600; }
footer.report-footer { margin-top: 3rem; color: var(--txt-dim); font-size: .8rem; border-top: 1px solid var(--border); padding-top: 1rem; }
"""

TOGGLE_SCRIPT = """
(function () {
  try {
    var saved = localStorage.getItem('pyfairCamReportTheme');
    if (saved === 'light' || saved === 'dark') {
      document.documentElement.setAttribute('data-theme', saved);
    }
  } catch (e) {}
  window.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    function current() { return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark'; }
    function label() { btn.textContent = current() === 'dark' ? 'Helles Design' : 'Dunkles Design'; }
    label();
    btn.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('pyfairCamReportTheme', next); } catch (e) {}
      label();
    });
  });
})();
"""
