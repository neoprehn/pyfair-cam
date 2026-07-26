"""
Stage / DetectionResponseFactor – FAIR-CAM Detection & Response
(Loss-Magnitude-Seite, Phase 2).

Ein Angriff durchläuft eine geordnete Liste von Stages (Kill-Chain-Stufen).
Jede Stage ist eine eigene Detection-Gelegenheit mit stufenspezifischen
Parametern (vgl. 04_Detection_Response_Measurement.md):

    - coverage               (Cov)    : Anteil der Angriffsfläche mit Detection [0..1]
    - visibility              (V)      : Wahrscheinlichkeit, dass Evidenz erfasst wird [0..1]
    - vis_reliability         (Rel_V)  : Zuverlässigkeit der Visibility-Controls [0..1]
    - recognition             (R)      : Wahrscheinlichkeit korrekter Klassifikation [0..1]
    - rec_reliability         (Rel_R)  : Zuverlässigkeit der Recognition-Controls [0..1]
    - monitoring_cadence      (M)      : Zeit zwischen Reviews [Tage]
    - mon_reliability         (Rel_M)  : Zuverlässigkeit des Monitorings [0..1]
    - duration                (τ)      : erwartete Verweildauer des Angreifers [Tage]
    - progression_probability (P)      : Wahrscheinlichkeit, zur nächsten Stage vorzudringen [0..1]
    - review_independence     (ρ)      : Unabhängigkeit aufeinanderfolgender Reviews [0..1]

Jeder Parameter darf Skalar oder Distribution sein (wie bei ResistiveControl).
"""

import numpy as np

from ..core import (
    effective_parameter,
    reviews_per_stage,
    stage_detection_probability,
)
from ..core import (
    response_time as _response_time,
)
from ..simulator.distributions import as_distribution


class Stage:
    """Eine einzelne Kill-Chain-Stufe mit FAIR-CAM Detection-Parametern."""

    def __init__(
        self,
        name: str,
        coverage,
        visibility,
        vis_reliability,
        recognition,
        rec_reliability,
        monitoring_cadence,
        mon_reliability,
        duration,
        progression_probability,
        review_independence=0.0,
    ):
        self.name = name
        self.coverage = as_distribution(coverage)
        self.visibility = as_distribution(visibility)
        self.vis_reliability = as_distribution(vis_reliability)
        self.recognition = as_distribution(recognition)
        self.rec_reliability = as_distribution(rec_reliability)
        self.monitoring_cadence = as_distribution(monitoring_cadence)
        self.mon_reliability = as_distribution(mon_reliability)
        self.duration = as_distribution(duration)
        self.progression_probability = as_distribution(progression_probability)
        self.review_independence = as_distribution(review_independence)

    def sample(self, n: int, rng: np.random.Generator) -> dict:
        """Zieht alle zehn Stage-Parameter für ``n`` Trials, feste Reihenfolge.

        Die Reihenfolge ist absichtlich fix (Coverage → Visibility → ... →
        Review Independence), damit der RNG-Strom bei gleichem Seed immer
        deterministisch an derselben Position steht, unabhängig davon, was
        der Aufrufer mit den Werten anschließend tut.
        """
        return {
            "coverage": np.clip(self.coverage.sample(n, rng), 0.0, 1.0),
            "visibility": np.clip(self.visibility.sample(n, rng), 0.0, 1.0),
            "vis_reliability": np.clip(self.vis_reliability.sample(n, rng), 0.0, 1.0),
            "recognition": np.clip(self.recognition.sample(n, rng), 0.0, 1.0),
            "rec_reliability": np.clip(self.rec_reliability.sample(n, rng), 0.0, 1.0),
            "monitoring_cadence": self.monitoring_cadence.sample(n, rng),
            "mon_reliability": np.clip(self.mon_reliability.sample(n, rng), 0.0, 1.0),
            "duration": self.duration.sample(n, rng),
            "progression_probability": np.clip(self.progression_probability.sample(n, rng), 0.0, 1.0),
            "review_independence": np.clip(self.review_independence.sample(n, rng), 0.0, 1.0),
        }

    def detection_probability(self, n: int, rng: np.random.Generator):
        """Samplet die Stage-Parameter einmal und berechnet P(Detect).

        Returns
        -------
        tuple[np.ndarray, dict]
            ``(p_detect, params)`` – ``params`` ist das Sample-Dict aus
            :meth:`sample`, zur Weiterverwendung durch den Aufrufer (z.B.
            ``progression_probability``). Es wird NICHT erneut gesamplet,
            um den RNG-Strom nicht zu verschieben und die Reproduzierbarkeit
            nicht zu brechen.
        """
        params = self.sample(n, rng)
        v_eff = effective_parameter(params["visibility"], params["vis_reliability"])
        r_eff = effective_parameter(params["recognition"], params["rec_reliability"])
        lam = reviews_per_stage(params["duration"], params["monitoring_cadence"], params["mon_reliability"])
        p_detect = stage_detection_probability(
            params["coverage"], v_eff, r_eff, params["review_independence"], lam
        )
        return p_detect, params


class DetectionResponseFactor:
    """FAIR-CAM Detection & Response – stage-gated Modell der Loss-Magnitude-Seite.

    Ein Angriff durchläuft die ``stages`` der Reihe nach. An jeder Stage wird
    pro Trial per Bernoulli-Ziehung entschieden, ob erkannt wird (Wahrschein-
    lichkeit ``P(Detect)`` der Stage) oder ob der Angreifer weiter vordringt
    (Wahrscheinlichkeit ``progression_probability`` der Stage). Jeder Trial
    endet in genau einer Outcome-Klasse:

        - an einer Stage entdeckt  → die per ``stage_outcome_map`` zugeordnete
          Klasse (z.B. "early", "mid", "late")
        - nie entdeckt, aber bricht unterwegs ab → ``ATTACKER_FAILS``
        - erreicht und übersteht die letzte Stage unentdeckt → ``FULL_IMPACT``

    Jede Outcome-Klasse hat eine eigene bedingte Verlustverteilung
    (``loss_distributions``); die Loss Magnitude eines Trials wird aus der
    zu seiner Outcome-Klasse passenden Verteilung gezogen.
    """

    FULL_IMPACT = "full_impact"
    ATTACKER_FAILS = "attacker_fails"

    def __init__(
        self,
        name: str,
        stages: list,
        stage_outcome_map: dict,
        loss_distributions: dict,
        t_containment=None,
        t_resilience=None,
        concurrency=0.0,
    ):
        if not stages:
            raise ValueError("DetectionResponseFactor benötigt mindestens eine Stage.")
        if set(stage_outcome_map.keys()) != set(range(1, len(stages) + 1)):
            raise ValueError(
                "stage_outcome_map muss für jede Stage (1-basiert, 1..len(stages)) "
                "genau einen Eintrag haben."
            )
        reserved = {self.FULL_IMPACT, self.ATTACKER_FAILS}
        if reserved & set(stage_outcome_map.values()):
            raise ValueError(
                f"stage_outcome_map darf die reservierten Klassennamen {reserved} nicht verwenden."
            )
        required_classes = set(stage_outcome_map.values()) | reserved
        if set(loss_distributions.keys()) != required_classes:
            raise ValueError(
                f"loss_distributions muss genau die Klassen {required_classes} abdecken, "
                f"erhalten: {set(loss_distributions.keys())}."
            )

        self.name = name
        self.stages = stages
        self.stage_outcome_map = stage_outcome_map
        self.loss_distributions = {cls: as_distribution(dist) for cls, dist in loss_distributions.items()}
        self.t_containment = as_distribution(t_containment) if t_containment is not None else None
        self.t_resilience = as_distribution(t_resilience) if t_resilience is not None else None
        self.concurrency = as_distribution(concurrency)

    def simulate(self, n: int, rng: np.random.Generator) -> dict:
        """Führt den Stage-Walk für ``n`` Trials aus.

        Returns
        -------
        dict
            ``outcome_class`` (object-Array, n), ``detected_at_stage``
            (int-Array, n; -1 = nie entdeckt), ``loss_magnitude`` (float-
            Array, n), ``p_detect_by_stage`` (Liste von k Arrays, Diagnose).
        """
        active = np.ones(n, dtype=bool)
        outcome_class = np.full(n, "", dtype=object)
        detected_at_stage = np.full(n, -1, dtype=int)
        p_detect_by_stage = []

        n_stages = len(self.stages)
        for i, stage in enumerate(self.stages, start=1):
            p_detect, params = stage.detection_probability(n, rng)
            p_detect_by_stage.append(p_detect)

            u_detect = rng.random(n)
            detected_here = active & (u_detect < p_detect)
            outcome_class[detected_here] = self.stage_outcome_map[i]
            detected_at_stage[detected_here] = i

            still_active = active & ~detected_here
            u_progress = rng.random(n)
            progressed = still_active & (u_progress < params["progression_probability"])
            failed_here = still_active & ~progressed
            outcome_class[failed_here] = self.ATTACKER_FAILS

            if i == n_stages:
                outcome_class[progressed] = self.FULL_IMPACT
                active = np.zeros(n, dtype=bool)
            else:
                active = progressed

        if np.any(outcome_class == ""):
            raise RuntimeError(
                "Interner Fehler: nicht jeder Trial hat eine Outcome-Klasse erhalten."
            )

        loss_magnitude = self._sample_loss_magnitude(outcome_class, n, rng)

        return {
            "outcome_class": outcome_class,
            "detected_at_stage": detected_at_stage,
            "loss_magnitude": loss_magnitude,
            "p_detect_by_stage": p_detect_by_stage,
        }

    def _sample_loss_magnitude(self, outcome_class: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
        # Wichtig: JEDE Klassenverteilung wird immer für alle n Trials gesamplet
        # (feste Reihenfolge), unabhängig davon wie wenige Trials tatsächlich in
        # diese Klasse fallen. Alles andere würde die Anzahl der RNG-Ziehungen
        # vom Zufallsergebnis selbst abhängig machen und die Reproduzierbarkeit
        # brechen (derselbe Fehlertyp, den Phase 0 beim Seed-Bug behoben hat).
        class_order = sorted(self.loss_distributions.keys())
        samples = {cls: self.loss_distributions[cls].sample(n, rng) for cls in class_order}

        loss_magnitude = np.full(n, np.nan)
        for cls in class_order:
            mask = outcome_class == cls
            loss_magnitude[mask] = samples[cls][mask]

        if np.any(np.isnan(loss_magnitude)):
            raise RuntimeError(
                "Interner Fehler: Loss Magnitude konnte nicht für alle Trials zugeordnet werden."
            )
        return loss_magnitude

    def response_time(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Response-Zeit (Reporting-Kennzahl, NICHT Teil von ``simulate()``).

        T_response = T_containment + T_resilience - α × min(T_containment, T_resilience)
        """
        if self.t_containment is None or self.t_resilience is None:
            raise ValueError(
                "response_time() benötigt t_containment und t_resilience "
                "(im Konstruktor von DetectionResponseFactor setzen)."
            )
        tc = self.t_containment.sample(n, rng)
        ts = self.t_resilience.sample(n, rng)
        alpha = self.concurrency.sample(n, rng)
        return _response_time(tc, ts, alpha)
