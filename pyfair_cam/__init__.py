"""
pyfair-cam – Monte Carlo Simulator for FAIR-CAM (Controls Analytics Model)

Eigenständige Bibliothek (unabhängig von pyfair). Die Integration von FAIR
und FAIR-CAM erfolgt auf Anwendungsebene (fair-web), nicht hier.

Based on the FAIR-CAM Knowledge Base by Jack Jones / FAIR Institute.
License: MIT (own code) | Knowledge Base: CC BY-NC-ND 4.0
"""

VERSION = '0.2.0-alpha.1'

from .model.cam_model import FairCamModel
from .simulator.monte_carlo import FairCamSimulator
from .simulator.distributions import (
    Distribution,
    PointEstimate,
    Constant,
    BetaPert,
    LogNormal,
    Normal,
    Uniform,
    Poisson,
    Bernoulli,
)
from .factors.resistance import ResistiveControl
from .factors.detection_response import Stage, DetectionResponseFactor
from .core import (
    reliability,
    operational_efficacy,
    combined_susceptibility,
    effective_parameter,
    reviews_per_stage,
    stage_detection_probability,
    progression_reach_probability,
    response_time,
    pert_mean,
    expected_gross_loss,
    detection_within_time,
)
from .report.simple_report import FairCamReport

__all__ = [
    "VERSION",
    "FairCamModel",
    "FairCamSimulator",
    "Distribution",
    "PointEstimate",
    "Constant",
    "BetaPert",
    "LogNormal",
    "Normal",
    "Uniform",
    "Poisson",
    "Bernoulli",
    "ResistiveControl",
    "Stage",
    "DetectionResponseFactor",
    "reliability",
    "operational_efficacy",
    "combined_susceptibility",
    "effective_parameter",
    "reviews_per_stage",
    "stage_detection_probability",
    "progression_reach_probability",
    "response_time",
    "pert_mean",
    "expected_gross_loss",
    "detection_within_time",
    "FairCamReport",
]
