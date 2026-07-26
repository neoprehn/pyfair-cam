"""
FairCamReport – Report für FAIR-CAM-Simulationsergebnisse.

Zwei Ausgabeformen: die bestehende Text-Zusammenfassung (``print_summary``)
und ein eigenständiger, offline lauffähiger HTML-Report (``to_html``,
Phase 4) – eine einzelne HTML-Datei ohne externe Abhängigkeiten (kein CDN),
Design an fair-web angelehnt (Bahnschrift, Sky-Blau, Dark/Light-Toggle).
"""

import datetime
import html as _html

import numpy as np
import pandas as pd

from ..factors.detection_response import DetectionResponseFactor
from .charts import (
    bar_chart_horizontal,
    control_tree_diagram,
    histogram_chart,
    line_area_chart,
)
from .theme import CATEGORICAL_SLOTS, CSS, STATUS, TOGGLE_SCRIPT


def _esc(text) -> str:
    return _html.escape(str(text), quote=True)


def _fmt_currency(value: float) -> str:
    return f"€ {value:,.0f}".replace(",", ".")


def _fmt_percent(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def _fmt_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _delta_html(before: float, after: float) -> str:
    """Farbige Prozent-Delta-Anzeige: grün = Reduktion, rot = Erhöhung."""
    if before == 0:
        return "–"
    delta = (before - after) / before
    color = STATUS["good"] if delta >= 0 else STATUS["critical"]
    sign = "-" if delta >= 0 else "+"
    return f'<span style="color:{color}">{sign}{_fmt_percent(abs(delta))}</span>'


class FairCamReport:
    """Erstellt Reports aus FairCamSimulator Ergebnissen."""

    def __init__(self, simulator):
        self.simulator = simulator

    def get_summary(self) -> pd.DataFrame:
        """Gibt eine Zusammenfassung der Simulationsergebnisse zurück."""
        return self.simulator.export_results()

    def get_lec(self) -> pd.DataFrame:
        """Gibt die Loss Exceedance Curve zurück."""
        return self.simulator.get_lec()

    def print_summary(self):
        """Gibt eine lesbare Zusammenfassung aus."""
        stats = self.simulator.get_statistics()
        print(f"\n{'='*50}")
        print("  FAIR-CAM Simulationsergebnisse")
        print(f"{'='*50}")
        components = self.simulator.get_components()
        mean_susc = float(components['susceptibility'].mean())
        mean_lef = float(components['lef'].mean())
        print(f"  Mittlere Susceptibility: {mean_susc:.1%}")
        print(f"  Mittlere LEF:            {mean_lef:.2f} Loss-Events/Jahr")
        print(f"  ALE (Erwartungswert):  € {stats['mean']:,.0f}")
        print(f"  Median:                € {stats['median']:,.0f}")
        print(f"  VaR 95%:               € {stats['p95']:,.0f}")
        print(f"  VaR 99%:               € {stats['p99']:,.0f}")
        print(f"  Min:                   € {stats['min']:,.0f}")
        print(f"  Max:                   € {stats['max']:,.0f}")
        print(f"{'='*50}\n")

    # ------------------------------------------------------------------
    # HTML-Report (Phase 4)
    # ------------------------------------------------------------------

    def to_html(self, path=None, *, threat_capability=None) -> str:
        """Erzeugt einen eigenständigen, offline lauffähigen HTML-Report.

        Parameters
        ----------
        path : str oder Path, optional
            Wenn angegeben, wird die HTML-Datei dort gespeichert.
        threat_capability : pyfair_cam Distribution oder Skalar, optional
            Nur wirksam, wenn das optionale ``pyfair``-Paket installiert ist
            (Extra ``pyfair-cam[pyfair]``): aktiviert ein zusätzliches Panel,
            das Pfad Vuln/A und Pfad CS/B gegenüberstellt
            (siehe :func:`pyfair_cam.adapter.compare_paths`).

        Returns
        -------
        str
            Der HTML-Quelltext (auch wenn ``path`` gesetzt ist).
        """
        model = self.simulator.model
        if model is None:
            raise RuntimeError(
                "Simulation wurde noch nicht ausgeführt. Bitte simulator.run() aufrufen."
            )

        sections = [
            self._section_stats(),
            self._section_lec(),
            self._section_histogram(),
        ]
        if model._controls:
            sections.append(self._section_controls(model))
            sections.append(self._section_before_after(model))
        if model._detection_response is not None:
            sections.append(self._section_detection_response(model))
        if threat_capability is not None:
            pyfair_section = self._section_pyfair_comparison(model, threat_capability)
            if pyfair_section:
                sections.append(pyfair_section)

        html_out = self._render_shell(model, "\n".join(sections))

        if path is not None:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_out)

        return html_out

    def _render_shell(self, model, body: str) -> str:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        n = self.simulator.n_simulations
        seed = self.simulator.seed
        meta = f"{_fmt_int(n)} Trials"
        if seed is not None:
            meta += f" · Seed {seed}"
        meta += f" · erzeugt {now}"

        return f"""<!doctype html>
<html lang="de" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FAIR-CAM Report — {_esc(model.name)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="report-header">
  <div>
    <h1>{_esc(model.name)}</h1>
    <p class="subtitle">FAIR-CAM Monte-Carlo-Report · {meta}</p>
  </div>
  <button class="theme-toggle" id="theme-toggle" type="button">Helles Design</button>
</header>
{body}
<footer class="report-footer">
  Erzeugt mit <strong>pyfair-cam</strong> — Monte Carlo Simulator für FAIR-CAM.
  FAIR-CAM-Methodik: Jack Jones / FAIR Institute (CC BY-NC-ND 4.0).
</footer>
</div>
<script>{TOGGLE_SCRIPT}</script>
</body>
</html>
"""

    def _section_stats(self) -> str:
        stats = self.simulator.get_statistics()
        components = self.simulator.get_components()
        tiles = [
            ("ALE (Erwartungswert)", _fmt_currency(stats["mean"])),
            ("Median", _fmt_currency(stats["median"])),
            ("VaR 95%", _fmt_currency(stats["p95"])),
            ("VaR 99%", _fmt_currency(stats["p99"])),
            ("Max", _fmt_currency(stats["max"])),
            ("Mittlere Susceptibility", _fmt_percent(float(np.mean(components["susceptibility"])))),
        ]
        tile_html = "".join(
            f'<div class="card stat-tile"><div class="label">{_esc(label)}</div>'
            f'<div class="value">{value}</div></div>'
            for label, value in tiles
        )
        return f'<section class="section"><div class="grid">{tile_html}</div></section>'

    def _section_lec(self) -> str:
        lec = self.simulator.get_lec()
        chart = line_area_chart(
            lec["loss"].to_numpy(),
            lec["exceedance_probability"].to_numpy(),
            x_label="Verlust",
            y_label="Überschreitungswahrscheinlichkeit",
        )
        return (
            '<section class="section"><h2>Loss Exceedance Curve</h2>'
            f'<div class="card">{chart}</div></section>'
        )

    def _section_histogram(self) -> str:
        chart = histogram_chart(self.simulator.get_results(), x_label="Risk pro Trial")
        return (
            '<section class="section"><h2>Verteilung der Risk-Simulation</h2>'
            f'<div class="card">{chart}</div></section>'
        )

    def _section_controls(self, model) -> str:
        n = self.simulator.n_simulations
        rng = np.random.default_rng(self.simulator.seed)
        names = [c.name for c in model._controls]
        mean_opeff = [float(np.mean(c.operational_efficacy(n, rng))) for c in model._controls]

        colors = [CATEGORICAL_SLOTS[i % len(CATEGORICAL_SLOTS)] for i in range(len(names))]
        bars = bar_chart_horizontal(
            names, mean_opeff, colors=colors, value_fmt=_fmt_percent, max_value=1.0
        )
        tree = control_tree_diagram(names)

        combined_susc = 1.0
        for v in mean_opeff:
            combined_susc *= 1.0 - v

        rows = "".join(
            f"<tr><td>{_esc(name)}</td><td class='num'>{_fmt_percent(v)}</td>"
            f"<td class='num'>{_fmt_percent(1 - v)}</td></tr>"
            for name, v in zip(names, mean_opeff)
        )
        table = (
            "<table><thead><tr><th>Control</th><th class='num'>Mittleres OpEff</th>"
            "<th class='num'>Verbleibende Susceptibility</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            "<tfoot><tr><td>Kombiniert (Π, OR-Logik)</td><td class='num'>—</td>"
            f"<td class='num'>{_fmt_percent(combined_susc)}</td></tr></tfoot></table>"
        )

        return f"""
        <section class="section">
          <h2>Control-Wirksamkeit &amp; Susceptibility-Zerlegung</h2>
          <div class="card">{tree}</div>
          <div class="card" style="margin-top:.9rem">{bars}</div>
          <div class="card" style="margin-top:.9rem">{table}</div>
          <p class="note">Susceptibility kombiniert über Defense-in-Depth (OR-Logik): jedes
          zusätzliche Control senkt sie multiplikativ, unter der Annahme unabhängiger Controls
          (siehe ROADMAP.md, Phase 10).</p>
        </section>
        """

    def _section_before_after(self, model) -> str:
        n = self.simulator.n_simulations
        rng = np.random.default_rng(self.simulator.seed)
        controls_backup = model._controls
        try:
            model._controls = []
            baseline = model.calculate(n, rng)
        finally:
            model._controls = controls_backup

        with_controls = self.simulator.get_results()
        without_controls = baseline["risk"]

        rows_data = [
            ("Mittelwert (ALE)", np.mean, {}),
            ("Median", np.median, {}),
            ("VaR 95%", np.percentile, {"q": 95}),
            ("VaR 99%", np.percentile, {"q": 99}),
        ]
        rows = []
        for label, fn, kwargs in rows_data:
            before = float(fn(without_controls, **kwargs))
            after = float(fn(with_controls, **kwargs))
            rows.append(
                f"<tr><td>{label}</td><td class='num'>{_fmt_currency(before)}</td>"
                f"<td class='num'>{_fmt_currency(after)}</td>"
                f"<td class='num'>{_delta_html(before, after)}</td></tr>"
            )
        table = (
            "<table><thead><tr><th></th><th class='num'>Ohne Controls</th>"
            "<th class='num'>Mit Controls</th><th class='num'>Reduktion</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
        return f"""
        <section class="section">
          <h2>Vorher/Nachher: Wirkung der Controls</h2>
          <div class="card">{table}</div>
          <p class="note">„Ohne Controls" ist eine Vergleichsrechnung mit identischer
          TEF/LM-Konfiguration und Susceptibility ≡ 1 — gleiche Trial-Anzahl, eigener
          RNG-Strom für die Gegenrechnung.</p>
        </section>
        """

    def _section_detection_response(self, model) -> str:
        n = self.simulator.n_simulations
        components = self.simulator.get_components()
        outcome_class = components["outcome_class"]
        dr = model._detection_response

        stage_order = []
        seen = set()
        for i in sorted(dr.stage_outcome_map.keys()):
            cls = dr.stage_outcome_map[i]
            if cls not in seen:
                stage_order.append(cls)
                seen.add(cls)
        class_order = (
            [DetectionResponseFactor.ATTACKER_FAILS] + stage_order + [DetectionResponseFactor.FULL_IMPACT]
        )

        shares = {cls: float(np.mean(outcome_class == cls)) for cls in class_order}
        colors = [CATEGORICAL_SLOTS[i % len(CATEGORICAL_SLOTS)] for i in range(len(class_order))]
        bars = bar_chart_horizontal(
            class_order,
            [shares[c] for c in class_order],
            colors=colors,
            value_fmt=_fmt_percent,
            max_value=max(shares.values()) if shares else 1.0,
        )

        # LM Vorher/Nachher: "vorher" = reines FAIR-LM ohne Detection/Response
        # (Full-Impact-Verteilung), "nachher" = tatsächlich realisierte LM.
        rng = np.random.default_rng(self.simulator.seed)
        baseline_lm = dr.loss_distributions[DetectionResponseFactor.FULL_IMPACT].sample(n, rng)
        actual_lm = components["loss_magnitude"]

        lm_table = (
            "<table><thead><tr><th>Loss Magnitude</th><th class='num'>Mittelwert</th>"
            "<th class='num'>Median</th></tr></thead><tbody>"
            f"<tr><td>Vorher (Full Impact, unentdeckt)</td>"
            f"<td class='num'>{_fmt_currency(float(np.mean(baseline_lm)))}</td>"
            f"<td class='num'>{_fmt_currency(float(np.median(baseline_lm)))}</td></tr>"
            f"<tr><td>Nachher (tatsächlich, inkl. Detection/Response)</td>"
            f"<td class='num'>{_fmt_currency(float(np.mean(actual_lm)))}</td>"
            f"<td class='num'>{_fmt_currency(float(np.median(actual_lm)))}</td></tr>"
            "</tbody></table>"
        )

        return f"""
        <section class="section">
          <h2>Detection &amp; Response: Outcome-Klassen</h2>
          <div class="card">{bars}</div>
          <p class="note">Reihenfolge von bestem zu schlechtestem Ausgang.
          „{_esc(DetectionResponseFactor.FULL_IMPACT)}" heißt: über die gesamte Kill-Chain nie entdeckt.</p>
          <h2>Loss Magnitude: Vorher/Nachher (Parallel-Anzeige)</h2>
          <div class="card">{lm_table}</div>
          <p class="note">Kein Ersatz: der ursprüngliche FAIR-LM-Wert ("Vorher" = Full-Impact-Verteilung)
          bleibt unverändert sichtbar neben dem tatsächlichen, durch Detection/Response reduzierten
          Ergebnis — siehe ROADMAP.md „Rechenprinzip LM-Seite".</p>
        </section>
        """

    def _section_pyfair_comparison(self, model, threat_capability):
        try:
            from ..adapter.to_pyfair import compare_paths
        except ImportError:
            return None

        seed = self.simulator.seed if self.simulator.seed is not None else 42
        result = compare_paths(model, threat_capability=threat_capability, random_seed=seed)
        stats = result["stats"]

        rows = "".join(
            f"<tr><td>{_esc(metric)}</td>"
            f"<td class='num'>{_fmt_currency(stats.loc[metric, 'vuln (Pfad A)'])}</td>"
            f"<td class='num'>{_fmt_currency(stats.loc[metric, 'cs (Pfad B)'])}</td></tr>"
            for metric in stats.index
        )
        table = (
            "<table><thead><tr><th>Kennzahl</th><th class='num'>Pfad Vuln (A)</th>"
            f"<th class='num'>Pfad CS (B)</th></tr></thead><tbody>{rows}</tbody></table>"
        )
        return f"""
        <section class="section">
          <h2>pyfair-Andockpunkte im Vergleich</h2>
          <div class="card">{table}</div>
          <p class="note">{_esc(result["note"])}</p>
        </section>
        """
