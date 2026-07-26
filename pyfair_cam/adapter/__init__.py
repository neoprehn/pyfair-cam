"""Adapter: FairCamModel -> pyfair (optionale Integration, siehe ROADMAP.md)."""

from .to_pyfair import compare_paths, to_pyfair

__all__ = ["to_pyfair", "compare_paths"]
