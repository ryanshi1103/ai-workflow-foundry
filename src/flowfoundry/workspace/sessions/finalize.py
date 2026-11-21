"""Backward-compatible façade for the composable finalization pipeline."""

from .finalization.pipeline import finalize_session

__all__ = ["finalize_session"]
