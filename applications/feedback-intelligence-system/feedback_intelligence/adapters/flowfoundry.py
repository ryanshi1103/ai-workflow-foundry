"""Public FlowFoundry application contract without a core runtime dependency."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_APPLICATION_CONTRACT: dict[str, Any] = {
    "schema_version": 1,
    "id": "feedback-intelligence-system",
    "aliases": ["feedback-analysis-system", "social-negative-monitor"],
    "entrypoint": "app:main",
    "workflow": [
        "import",
        "deduplicate",
        "analyze",
        "human_review",
        "export",
    ],
    "capabilities": [
        "feedback.ingest",
        "feedback.deduplicate",
        "feedback.analyze",
        "feedback.review",
        "feedback.export",
    ],
    "workspace": {
        "local_first": True,
        "session_finalization": True,
        "generated_data_default": "data/",
    },
    "policy": {
        "public_or_authorized_inputs_only": True,
        "redact_secrets": True,
        "external_provider_requires_explicit_configuration": True,
        "human_review_before_authoritative_export": True,
    },
}


def application_contract() -> dict[str, Any]:
    """Return an isolated copy of the stable application descriptor."""

    return deepcopy(_APPLICATION_CONTRACT)


__all__ = ["application_contract"]
