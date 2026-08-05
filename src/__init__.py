"""Compatibility namespace for the pre-migration ``src`` import path.

New code should import :mod:`feedback_intelligence`.  The aliases below point
to the same module objects so monkeypatching, SQLAlchemy metadata, and cached
configuration are not duplicated during the deprecation window.
"""

from __future__ import annotations

import importlib
import sys

_ALIASES = (
    "config",
    "schemas",
    "models",
    "database",
    "prompts",
    "prompts.sentiment_v1",
    "connectors",
    "connectors.base",
    "connectors.csv_connector",
    "connectors.json_connector",
    "connectors.mock_connector",
    "connectors.apify_connector",
    "repositories",
    "repositories.feedback_repo",
    "services",
    "services.dedup_service",
    "services.import_service",
    "services.export_service",
    "services.deepseek_service",
    "services.analysis_service",
)

for _module_name in _ALIASES:
    _module = importlib.import_module(f"feedback_intelligence.{_module_name}")
    sys.modules[f"src.{_module_name}"] = _module
    if "." not in _module_name:
        globals()[_module_name] = _module

__all__ = tuple(name for name in _ALIASES if "." not in name)
