"""
to_pyfair – Adapter FairCamModel -> pyfair.FairModel (Pfad Vuln / "A").

Übergibt die abgeleiteten FAIR-CAM-Parameter (TEF, Susceptibility, Loss
Magnitude) als volle Rohdatenarrays an ein natives pyfair-Modell, statt sie
auf einen Kennwert (Mittelwert) zu reduzieren. Siehe ROADMAP.md, Abschnitt
"Offene Architektur-Entscheidung: Andockpunkt FAIR ↔ FAIR-CAM", Unterabschnitt
"Rechenprinzip" für die Begründung ("volle rohe Arrays ... trialweise
verrechnen").

``pyfair`` ist eine optionale Abhängigkeit (Extra ``pyfair-cam[pyfair]``) –
pyfair-cam bleibt ohne sie voll nutzbar, siehe README/ROADMAP
("Engine-Strategie").
"""

import numpy as np

from ..model.cam_model import FairCamModel


def to_pyfair(cam_model: FairCamModel, mode="vuln", n_simulations=None, random_seed=42):
    """Baut ein pyfair-``FairModel`` aus einem ``FairCamModel``.

    Parameters
    ----------
    cam_model : FairCamModel
        Vollständig konfiguriertes CAM-Modell (TEF + LM/Detection-Response,
        optional resistive Controls).
    mode : str
        ``"vuln"`` (Pfad A, implementiert): Susceptibility = 1 − OpEff wird
        direkt als ``Vulnerability`` an pyfair übergeben.
        ``"cs"`` (Pfad B): noch nicht implementiert – siehe unten.
    n_simulations : int, optional
        Anzahl Trials. Default: ``cam_model.n_simulations`` (beide Seiten
        müssen dieselbe Anzahl verwenden, siehe ROADMAP.md "Rechenprinzip").
    random_seed : int, optional
        Seed für das pyfair-Modell (Default 42, wie pyfair-üblich). Wirkt
        sich hier nicht auf die Ergebniswerte aus, da TEF/Vulnerability/LM
        vollständig als Rohdaten übergeben werden und pyfair intern nichts
        mehr zufällig zieht – nur pyfairs eigener (harmloser) globaler
        ``np.random.seed()``-Aufruf im Konstruktor.

    Returns
    -------
    tuple[pyfair.FairModel, dict]
        Das berechnete pyfair-Modell sowie das rohe CAM-``calculate()``-
        Ergebnis (inkl. ``outcome_class``/``detected_at_stage`` bei
        Detection/Response-Modellen) für die spätere Parallel-Anzeige
        (siehe ROADMAP.md "Rechenprinzip LM-Seite").

    Raises
    ------
    ImportError
        Wenn das optionale ``pyfair``-Paket nicht installiert ist.
    NotImplementedError
        Für ``mode="cs"`` – die Kalibrierung ``OpEff -> RS-Perzentil`` ist
        eine offene Forschungsfrage, siehe ROADMAP.md.
    ValueError
        Für unbekannte ``mode``-Werte.
    """
    if mode == "cs":
        raise NotImplementedError(
            "mode='cs' (Andockpunkt Control Strength/Resistance Strength) ist "
            "noch nicht implementiert: die Kalibrierung 'OpEff -> RS-Perzentil' "
            "ist eine offene Forschungsfrage, siehe ROADMAP.md, Abschnitt "
            "'Offene Architektur-Entscheidung: Andockpunkt FAIR <-> FAIR-CAM'."
        )
    if mode != "vuln":
        raise ValueError(f"Unbekannter mode {mode!r}, erwartet 'vuln' oder 'cs'.")

    try:
        from pyfair import FairModel
    except ImportError as exc:
        raise ImportError(
            "to_pyfair() benötigt das optionale 'pyfair'-Paket. "
            "Installation: pip install pyfair-cam[pyfair]"
        ) from exc

    n = n_simulations or cam_model.n_simulations
    rng = np.random.default_rng(random_seed)
    cam_result = cam_model.calculate(n, rng)

    fair_model = FairModel(name=cam_model.name, n_simulations=n, random_seed=random_seed)
    fair_model.input_raw_data("Threat Event Frequency", cam_result["tef"])
    fair_model.input_raw_data("Vulnerability", cam_result["susceptibility"])
    fair_model.input_raw_data("Loss Magnitude", cam_result["loss_magnitude"])
    fair_model.calculate_all()

    return fair_model, cam_result
