"""
to_pyfair – Adapter FairCamModel -> pyfair.FairModel (Pfad Vuln/A und CS/B).

Übergibt die abgeleiteten FAIR-CAM-Parameter als volle Rohdatenarrays an ein
natives pyfair-Modell, statt sie auf einen Kennwert (Mittelwert) zu
reduzieren. Siehe ROADMAP.md, Abschnitt "Offene Architektur-Entscheidung:
Andockpunkt FAIR ↔ FAIR-CAM", Unterabschnitt "Rechenprinzip" für die
Begründung ("volle rohe Arrays ... trialweise verrechnen").

``pyfair`` ist eine optionale Abhängigkeit (Extra ``pyfair-cam[pyfair]``) –
pyfair-cam bleibt ohne sie voll nutzbar, siehe README/ROADMAP
("Engine-Strategie").

Pfad Vuln (A) und Pfad CS (B) sind bewusst **nicht kalibriert** aufeinander
abgestimmt (Entscheidung 2026-07-26, siehe ROADMAP.md "Offene
Architektur-Entscheidung"): Pfad B rechnet auf CS/TCap-Ebene mit pyfairs
nativer Step-Funktion und rechnet erst danach auf Susceptibility/Vulnerability
hoch – das darf von Pfad A abweichende Ergebnisse liefern. Eine spätere,
explizit kalibrierte dritte Variante (die beide Pfade synchron macht) ist
als offener Punkt in der Roadmap vermerkt, aber nicht Teil dieses Adapters.
"""

import numpy as np

from ..model.cam_model import FairCamModel
from ..simulator.distributions import as_distribution


def to_pyfair(
    cam_model: FairCamModel,
    mode="vuln",
    n_simulations=None,
    random_seed=42,
    threat_capability=None,
):
    """Baut ein pyfair-``FairModel`` aus einem ``FairCamModel``.

    Parameters
    ----------
    cam_model : FairCamModel
        Vollständig konfiguriertes CAM-Modell (TEF + LM/Detection-Response,
        optional resistive Controls).
    mode : str
        ``"vuln"`` (Pfad A): ``Susc = 1 − OpEff`` (kombiniert über alle
        Controls) wird direkt als ``Vulnerability`` an pyfair übergeben.
        ``"cs"`` (Pfad B): ``CS = 1 − Susc`` wird als ``Control Strength``
        gegen eine separat übergebene ``Threat Capability``-Verteilung
        antreten gelassen – pyfair berechnet ``Vulnerability`` dabei über
        seinen eigenen nativen Step-Vergleich (``model_calc.py``). Pfad A
        und Pfad B sind bewusst nicht kalibriert und können bei identischen
        Controls unterschiedliche Ergebnisse liefern (siehe Modul-Docstring).
    n_simulations : int, optional
        Anzahl Trials. Default: ``cam_model.n_simulations`` (beide Seiten
        müssen dieselbe Anzahl verwenden, siehe ROADMAP.md "Rechenprinzip").
    random_seed : int, optional
        Seed für das pyfair-Modell (Default 42, wie pyfair-üblich) und für
        das Sampling von ``threat_capability``. Wirkt sich bei ``mode="vuln"``
        nicht auf die Ergebniswerte aus, da TEF/Vulnerability/LM vollständig
        als Rohdaten übergeben werden und pyfair intern nichts mehr zufällig
        zieht.
    threat_capability : pyfair_cam Distribution oder Skalar, nur für mode="cs"
        FAIR-CAM modelliert keine Threat Capability (das ist reine
        FAIR-Domäne) – für Pfad B muss sie deshalb explizit übergeben werden.

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
    ValueError
        Für unbekannte ``mode``-Werte, oder wenn ``mode="cs"`` ohne
        ``threat_capability`` aufgerufen wird.
    """
    if mode not in ("vuln", "cs"):
        raise ValueError(f"Unbekannter mode {mode!r}, erwartet 'vuln' oder 'cs'.")

    if mode == "cs" and threat_capability is None:
        raise ValueError(
            "mode='cs' benötigt eine explizite 'threat_capability'-Verteilung: "
            "FAIR-CAM modelliert Threat Capability nicht selbst (reine "
            "FAIR-Domäne)."
        )

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
    fair_model.input_raw_data("Loss Magnitude", cam_result["loss_magnitude"])

    if mode == "vuln":
        fair_model.input_raw_data("Vulnerability", cam_result["susceptibility"])
    else:
        control_strength = 1.0 - cam_result["susceptibility"]
        tcap = as_distribution(threat_capability).sample(n, rng)
        fair_model.input_raw_data("Control Strength", control_strength)
        fair_model.input_raw_data("Threat Capability", tcap)

    fair_model.calculate_all()

    return fair_model, cam_result
