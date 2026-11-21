"""Replaceable execution contracts.  FlowFoundry owns coordination, not engines."""

from .base import Executor, ExecutorRequest, ExecutorResult

__all__ = ["Executor", "ExecutorRequest", "ExecutorResult"]
