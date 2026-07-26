"""
charts – Reine SVG-Chart-Bausteine für den HTML-Report.

Kein matplotlib/PNG-Roundtrip: Charts sind Inline-SVG, damit sie über CSS
Custom Properties automatisch dem Dark/Light-Theme des Reports folgen (Text/
Achsen nutzen ``var(--txt-dim)`` etc. aus ``theme.CSS``, siehe Klasse
``chart-svg``). Datenfarben kommen aus der validierten Palette in
``theme.py`` (``dataviz``-Skill), nicht aus matplotlibs Default-Zyklus.

Interaktion bewusst minimal gehalten: native SVG-``<title>``-Tooltips pro
Balken/Punkt (Browser-nativ, kein JS, offline-sicher) statt eines vollen
JS-Crosshairs – angemessen für einen statischen, einmalig erzeugten Report.
"""

import html

import numpy as np


def _fmt_currency(value: float) -> str:
    return f"€ {value:,.0f}".replace(",", ".")


def _fmt_percent(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _linear_scale(domain_min, domain_max, range_min, range_max):
    span = domain_max - domain_min
    if span == 0:
        span = 1.0

    def scale(value):
        t = (value - domain_min) / span
        return range_min + t * (range_max - range_min)

    return scale


def line_area_chart(
    x: np.ndarray,
    y: np.ndarray,
    *,
    width: int = 760,
    height: int = 300,
    x_label: str = "",
    y_label: str = "",
    x_fmt=_fmt_currency,
    y_fmt=lambda v: _fmt_percent(v, 0),
    color: str = "var(--accent)",
    n_ticks_x: int = 5,
    n_ticks_y: int = 5,
) -> str:
    """Linienchart mit Flächenfüllung unter der Kurve (z.B. Loss Exceedance Curve).

    ``x``/``y`` müssen bereits nach ``x`` sortiert sein.
    """
    margin_l, margin_r, margin_t, margin_b = 56, 16, 16, 40
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    x_min, x_max = float(np.min(x)), float(np.max(x))
    y_min, y_max = 0.0, max(1e-9, float(np.max(y)))

    sx = _linear_scale(x_min, x_max, margin_l, margin_l + plot_w)
    sy = _linear_scale(y_min, y_max, margin_t + plot_h, margin_t)

    points = [(sx(xi), sy(yi)) for xi, yi in zip(x, y)]
    path_d = "M " + " L ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    area_d = (
        f"M {points[0][0]:.1f},{sy(0):.1f} L "
        + " L ".join(f"{px:.1f},{py:.1f}" for px, py in points)
        + f" L {points[-1][0]:.1f},{sy(0):.1f} Z"
    )

    parts = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" width="100%" role="img" '
             f'aria-label="{_esc(x_label)} vs. {_esc(y_label)}">']

    # Gridlines + y-Achsenbeschriftung
    for i in range(n_ticks_y + 1):
        ty = y_min + (y_max - y_min) * i / n_ticks_y
        py = sy(ty)
        parts.append(f'<line class="gridline" x1="{margin_l}" y1="{py:.1f}" x2="{width - margin_r}" y2="{py:.1f}"/>')
        parts.append(f'<text x="{margin_l - 8}" y="{py + 4:.1f}" font-size="11" text-anchor="end">{y_fmt(ty)}</text>')

    # x-Achsenbeschriftung
    for i in range(n_ticks_x + 1):
        tx = x_min + (x_max - x_min) * i / n_ticks_x
        px = sx(tx)
        parts.append(f'<text x="{px:.1f}" y="{height - margin_b + 18}" font-size="11" text-anchor="middle">{x_fmt(tx)}</text>')

    parts.append(f'<line class="axis-line" x1="{margin_l}" y1="{margin_t + plot_h}" x2="{width - margin_r}" y2="{margin_t + plot_h}"/>')
    parts.append(f'<line class="axis-line" x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + plot_h}"/>')

    parts.append(f'<path d="{area_d}" fill="{color}" fill-opacity="0.16" stroke="none"/>')
    parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2"/>')

    # Hover-Punkte (native Tooltips), auf ~40 Stützstellen ausgedünnt.
    step = max(1, len(points) // 40)
    for idx in range(0, len(points), step):
        px, py = points[idx]
        tooltip = f"{x_fmt(x[idx])} → {y_fmt(y[idx])}"
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="{color}" opacity="0">'
            f'<title>{_esc(tooltip)}</title></circle>'
        )
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.5" fill="{color}"/>')

    parts.append(
        f'<text x="{margin_l + plot_w / 2:.1f}" y="{height - 4}" font-size="11" text-anchor="middle">{_esc(x_label)}</text>'
    )
    parts.append(
        f'<text x="12" y="{margin_t + plot_h / 2:.1f}" font-size="11" text-anchor="middle" '
        f'transform="rotate(-90 12 {margin_t + plot_h / 2:.1f})">{_esc(y_label)}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def histogram_chart(
    values: np.ndarray,
    *,
    bins: int = 30,
    width: int = 760,
    height: int = 260,
    x_label: str = "",
    color: str = "var(--accent)",
) -> str:
    """Histogramm der Risk-Verteilung."""
    counts, edges = np.histogram(values, bins=bins)
    margin_l, margin_r, margin_t, margin_b = 56, 16, 16, 40
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    x_min, x_max = float(edges[0]), float(edges[-1])
    y_max = max(1, int(counts.max()))

    sx = _linear_scale(x_min, x_max, margin_l, margin_l + plot_w)
    sy = _linear_scale(0, y_max, margin_t + plot_h, margin_t)

    parts = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" width="100%" role="img" '
             f'aria-label="Histogramm {_esc(x_label)}">']

    for i in range(5):
        ty = y_max * i / 4
        py = sy(ty)
        parts.append(f'<line class="gridline" x1="{margin_l}" y1="{py:.1f}" x2="{width - margin_r}" y2="{py:.1f}"/>')
        parts.append(f'<text x="{margin_l - 8}" y="{py + 4:.1f}" font-size="11" text-anchor="end">{int(round(ty))}</text>')

    for i in range(len(counts)):
        x0, x1 = sx(edges[i]), sx(edges[i + 1])
        y0 = sy(counts[i])
        bar_w = max(0.5, x1 - x0 - 1)
        tooltip = f"{_fmt_currency(edges[i])} – {_fmt_currency(edges[i + 1])}: {int(counts[i])} Trials"
        parts.append(
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{bar_w:.1f}" height="{(sy(0) - y0):.1f}" fill="{color}" fill-opacity="0.85">'
            f'<title>{_esc(tooltip)}</title></rect>'
        )

    n_ticks_x = 5
    for i in range(n_ticks_x + 1):
        tx = x_min + (x_max - x_min) * i / n_ticks_x
        px = sx(tx)
        parts.append(f'<text x="{px:.1f}" y="{height - margin_b + 18}" font-size="11" text-anchor="middle">{_fmt_currency(tx)}</text>')

    parts.append(f'<line class="axis-line" x1="{margin_l}" y1="{margin_t + plot_h}" x2="{width - margin_r}" y2="{margin_t + plot_h}"/>')
    parts.append(f'<line class="axis-line" x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + plot_h}"/>')
    parts.append(
        f'<text x="{margin_l + plot_w / 2:.1f}" y="{height - 4}" font-size="11" text-anchor="middle">{_esc(x_label)}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def bar_chart_horizontal(
    labels: list,
    values: list,
    *,
    colors=None,
    width: int = 760,
    value_fmt=lambda v: f"{v:.1%}",
    row_height: int = 34,
    max_value: float = None,
) -> str:
    """Horizontaler Balkenchart (Control-OpEff, Outcome-Klassen, Pfad-A/B-Vergleich, ...)."""
    n = len(labels)
    margin_l, margin_r, margin_t = 160, 70, 8
    plot_w = width - margin_l - margin_r
    height = margin_t * 2 + n * row_height

    vmax = max_value if max_value is not None else max([abs(v) for v in values] + [1e-9])
    sx = _linear_scale(0, vmax, 0, plot_w)

    default_color = "var(--accent)"
    if colors is None:
        colors = [default_color] * n

    parts = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Balkendiagramm">']
    for i, (label, value, color) in enumerate(zip(labels, values, colors)):
        y = margin_t + i * row_height
        bar_w = max(0.0, sx(abs(value)))
        parts.append(
            f'<text x="{margin_l - 10}" y="{y + row_height / 2 + 4:.1f}" font-size="12" text-anchor="end">{_esc(label)}</text>'
        )
        parts.append(
            f'<rect x="{margin_l}" y="{y + 6}" width="{bar_w:.1f}" height="{row_height - 12}" rx="3" fill="{color}">'
            f'<title>{_esc(label)}: {_esc(value_fmt(value))}</title></rect>'
        )
        parts.append(
            f'<text x="{margin_l + bar_w + 8:.1f}" y="{y + row_height / 2 + 4:.1f}" font-size="12">{_esc(value_fmt(value))}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def control_tree_diagram(control_names: list, *, width: int = 760) -> str:
    """Schematische Defense-in-Depth-Kette: TEF -> (Control OR Control OR ...) -> Susceptibility -> Risk.

    Bewusst schlicht gehalten (kein Koordinaten-Layout wie pyfairs FAIR-Baum) –
    FAIR-CAMs Resistance-Controls kombinieren sich über eine einzige OR-Kette,
    nicht über einen mehrstufigen Baum.
    """
    box_h = 44
    gap = 14
    n = max(1, len(control_names))
    box_w = min(190, (width - 220) / n - gap) if n else 190
    box_w = max(120, box_w)
    height = box_h + 90

    parts = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" width="100%" role="img" '
             f'aria-label="Defense-in-Depth-Kette">']

    def box(x, y, w, h, label, sub=None, fill="var(--bg-3)", stroke="var(--border)", text_fill="var(--txt)"):
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}"/>')
        ty = y + h / 2 + (0 if sub is None else -6)
        parts.append(f'<text x="{x + w / 2:.1f}" y="{ty:.1f}" font-size="13" text-anchor="middle" fill="{text_fill}">{_esc(label)}</text>')
        if sub is not None:
            parts.append(f'<text x="{x + w / 2:.1f}" y="{ty + 16:.1f}" font-size="11" text-anchor="middle" fill="{text_fill}" opacity="0.75">{_esc(sub)}</text>')

    tef_w = 90
    x = 0
    box(x, 20, tef_w, box_h, "TEF")
    x += tef_w + gap
    controls_x0 = x
    for i, name in enumerate(control_names):
        cy = 20 - (n - 1) * (box_h + 8) / 2 + i * (box_h + 8)
        box(x, cy, box_w, box_h, name, fill="var(--bg-2)")
        if i < n - 1:
            parts.append(
                f'<text x="{x + box_w + gap / 2:.1f}" y="{cy + box_h / 2 + 4:.1f}" font-size="11" '
                f'text-anchor="middle" fill="var(--txt-dim)">OR</text>'
            )
    controls_x1 = x + box_w
    x = controls_x1 + gap
    susc_x = x
    box(x, 20, 130, box_h, "Susceptibility", sub="Π(1 − OpEffᵢ)")
    x += 130 + gap
    box(x, 20, 100, box_h, "Risk", sub="TEF × Susc × LM", fill="var(--bg-3)", stroke="var(--accent)")

    # Verbindungslinien
    parts.insert(1, (
        f'<line class="axis-line" x1="{tef_w}" y1="{20 + box_h / 2}" x2="{controls_x0}" y2="{20 + box_h / 2}"/>'
        f'<line class="axis-line" x1="{controls_x1}" y1="{20 + box_h / 2}" x2="{susc_x}" y2="{20 + box_h / 2}"/>'
    ))

    parts.append("</svg>")
    return "".join(parts)


def legend(items: list) -> str:
    """items: Liste von (label, color)-Tupeln."""
    spans = "".join(
        f'<span><span class="swatch" style="background:{color}"></span>{_esc(label)}</span>'
        for label, color in items
    )
    return f'<div class="legend">{spans}</div>'
