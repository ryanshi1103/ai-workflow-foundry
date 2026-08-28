"""Load and validate FlowFoundry portable workflow contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .catalog import CatalogError, _require_text
from .resources import resource_path

# Re-export for convenience — workflow contracts are validated separately
# from component manifests but share the same error type.
__all__ = ["CatalogError", "validate_workflow_contract", "load_workflow_contracts"]


CONTRACTS_DIR = resource_path("workflows", "contracts")

STAGE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?"
    r"(?:\+[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?$"
)

ADAPTER_TYPES = {
    "claude-skill",
    "codex-skill",
    "deterministic-command",
    "python-module",
    "manual",
}

APPROVAL_SCOPES = {"destructive", "export", "network", "cost", "all"}
AUTO_APPROVE_POLICIES = {"never", "dry-run", "trusted-inputs", "always"}
SIDE_EFFECT_KINDS = {
    "file_write",
    "file_delete",
    "network_call",
    "api_call",
    "system_command",
    "credential_access",
    "database_write",
    "external_service",
}
IDEMPOTENCY_KEY_SOURCES = {"content-hash", "input-hash", "explicit-version", "none"}


def _validate_semver(value: str, field: str) -> str:
    if not SEMVER_PATTERN.fullmatch(value):
        raise CatalogError(f"{field} must be valid SemVer 2.0, got: {value!r}")
    return value


def validate_workflow_contract(contract: Any) -> dict[str, Any]:
    """Validate a single workflow contract against the portable workflow schema."""
    if not isinstance(contract, dict):
        raise CatalogError("workflow contract must be an object")
    if contract.get("schema_version") != 1:
        raise CatalogError("schema_version must be 1")

    # Identity
    contract_id = _require_text(contract.get("id"), "id")
    if not STAGE_ID_PATTERN.fullmatch(contract_id):
        raise CatalogError("id must use lowercase kebab-case")
    _require_text(contract.get("display_name"), "display_name")
    _validate_semver(_require_text(contract.get("version"), "version"), "version")
    _require_text(contract.get("description"), "description")

    # Stages
    stages = contract.get("stages")
    if not isinstance(stages, list) or not stages:
        raise CatalogError("stages must be a non-empty list")
    seen_stage_ids: set[str] = set()
    for i, stage in enumerate(stages):
        if not isinstance(stage, dict):
            raise CatalogError(f"stages[{i}] must be an object")
        stage_id = _require_text(stage.get("id"), f"stages[{i}].id")
        if not STAGE_ID_PATTERN.fullmatch(stage_id):
            raise CatalogError(f"stages[{i}].id must use lowercase kebab-case")
        if stage_id in seen_stage_ids:
            raise CatalogError(f"duplicate stage id: {stage_id}")
        seen_stage_ids.add(stage_id)
        _require_text(stage.get("name"), f"stages[{i}].name")
        _require_text(stage.get("description"), f"stages[{i}].description")

        # Inputs (optional)
        required_inputs = stage.get("required_inputs")
        if required_inputs is not None:
            if not isinstance(required_inputs, list):
                raise CatalogError(f"stages[{i}].required_inputs must be a list if present")
            seen_input_ids: set[str] = set()
            for j, inp in enumerate(required_inputs):
                if not isinstance(inp, dict):
                    raise CatalogError(f"stages[{i}].required_inputs[{j}] must be an object")
                inp_id = _require_text(inp.get("id"), f"stages[{i}].required_inputs[{j}].id")
                if inp_id in seen_input_ids:
                    raise CatalogError(f"duplicate input id: {inp_id} in stage {stage_id}")
                seen_input_ids.add(inp_id)
                _require_text(inp.get("description"), f"stages[{i}].required_inputs[{j}].description")
                _require_text(inp.get("content_type"), f"stages[{i}].required_inputs[{j}].content_type")

        # Produces
        produces = stage.get("produces")
        if not isinstance(produces, dict):
            raise CatalogError(f"stages[{i}].produces must be an object")
        artifacts = produces.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise CatalogError(f"stages[{i}].produces.artifacts must be a non-empty list")
        seen_artifact_ids: set[str] = set()
        for j, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                raise CatalogError(f"stages[{i}].produces.artifacts[{j}] must be an object")
            art_id = _require_text(artifact.get("id"), f"stages[{i}].produces.artifacts[{j}].id")
            if art_id in seen_artifact_ids:
                raise CatalogError(f"duplicate artifact id: {art_id} in stage {stage_id}")
            seen_artifact_ids.add(art_id)
            _require_text(artifact.get("description"), f"stages[{i}].produces.artifacts[{j}].description")
            _require_text(artifact.get("content_type"), f"stages[{i}].produces.artifacts[{j}].content_type")

        review_required = produces.get("review_required")
        if review_required is not None and not isinstance(review_required, bool):
            raise CatalogError(f"stages[{i}].produces.review_required must be a boolean if present")

        # Adapter (optional)
        adapter = stage.get("adapter")
        if adapter is not None:
            if not isinstance(adapter, dict):
                raise CatalogError(f"stages[{i}].adapter must be an object if present")
            if adapter.get("type") not in ADAPTER_TYPES:
                raise CatalogError(
                    f"stages[{i}].adapter.type must be one of {sorted(ADAPTER_TYPES)}"
                )
            _require_text(adapter.get("entry_point"), f"stages[{i}].adapter.entry_point")
            timeout = adapter.get("timeout_seconds")
            if timeout is not None and (not isinstance(timeout, int) or timeout < 1 or timeout > 86400):
                raise CatalogError(f"stages[{i}].adapter.timeout_seconds must be 1–86400")

        # Dependencies (optional)
        depends_on = stage.get("depends_on")
        if depends_on is not None:
            if not isinstance(depends_on, list):
                raise CatalogError(f"stages[{i}].depends_on must be a list if present")
            for dep in depends_on:
                if not isinstance(dep, str) or not dep.strip():
                    raise CatalogError(f"stages[{i}].depends_on entries must be non-empty strings")

    # Approval gates
    approval_gates = contract.get("approval_gates")
    if not isinstance(approval_gates, list):
        raise CatalogError("approval_gates must be a list")
    seen_gate_ids: set[str] = set()
    for i, gate in enumerate(approval_gates):
        if not isinstance(gate, dict):
            raise CatalogError(f"approval_gates[{i}] must be an object")
        gate_id = _require_text(gate.get("id"), f"approval_gates[{i}].id")
        if not STAGE_ID_PATTERN.fullmatch(gate_id):
            raise CatalogError(f"approval_gates[{i}].id must use lowercase kebab-case")
        if gate_id in seen_gate_ids:
            raise CatalogError(f"duplicate approval gate id: {gate_id}")
        seen_gate_ids.add(gate_id)
        _require_text(gate.get("name"), f"approval_gates[{i}].name")
        _require_text(gate.get("after_stage"), f"approval_gates[{i}].after_stage")
        _require_text(gate.get("description"), f"approval_gates[{i}].description")
        scope = gate.get("scope", "all")
        if scope not in APPROVAL_SCOPES:
            raise CatalogError(f"approval_gates[{i}].scope must be one of {sorted(APPROVAL_SCOPES)}")
        policy = gate.get("auto_approve_policy", "never")
        if policy not in AUTO_APPROVE_POLICIES:
            raise CatalogError(f"approval_gates[{i}].auto_approve_policy must be one of {sorted(AUTO_APPROVE_POLICIES)}")

    # Capabilities (optional)
    capabilities = contract.get("capabilities_required")
    if capabilities is not None:
        if not isinstance(capabilities, list):
            raise CatalogError("capabilities_required must be a list if present")
        for i, cap in enumerate(capabilities):
            if not isinstance(cap, str) or not cap.strip():
                raise CatalogError(f"capabilities_required[{i}] must be a non-empty string")

    # Safety
    safety = contract.get("safety")
    if not isinstance(safety, dict):
        raise CatalogError("safety must be an object")
    if not isinstance(safety.get("local_first"), bool):
        raise CatalogError("safety.local_first must be a boolean")
    _require_text(safety.get("network_policy"), "safety.network_policy")
    side_effects = safety.get("side_effects")
    if not isinstance(side_effects, list):
        raise CatalogError("safety.side_effects must be a list")
    seen_se: set[tuple[str, str]] = set()
    for i, se in enumerate(side_effects):
        if not isinstance(se, dict):
            raise CatalogError(f"safety.side_effects[{i}] must be an object")
        se_stage = _require_text(se.get("stage_id"), f"safety.side_effects[{i}].stage_id")
        se_desc = _require_text(se.get("description"), f"safety.side_effects[{i}].description")
        if se.get("kind") not in SIDE_EFFECT_KINDS:
            raise CatalogError(f"safety.side_effects[{i}].kind must be one of {sorted(SIDE_EFFECT_KINDS)}")
        key = (se_stage, se_desc)
        if key in seen_se:
            raise CatalogError(f"duplicate side effect: {se_desc} in stage {se_stage}")
        seen_se.add(key)

    # Idempotency (optional)
    idempotency = contract.get("idempotency")
    if idempotency is not None:
        if not isinstance(idempotency, dict):
            raise CatalogError("idempotency must be an object if present")
        key_source = idempotency.get("key_source", "none")
        if key_source not in IDEMPOTENCY_KEY_SOURCES:
            raise CatalogError(f"idempotency.key_source must be one of {sorted(IDEMPOTENCY_KEY_SOURCES)}")

    return contract


def load_workflow_contracts(
    directory: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Load and validate all workflow contracts from a directory."""
    contracts_dir = Path(directory) if directory is not None else CONTRACTS_DIR
    if not contracts_dir.is_dir():
        raise CatalogError(f"workflow contracts directory does not exist: {contracts_dir}")

    contracts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for contract_path in sorted(contracts_dir.glob("*.contract.json")):
        try:
            raw = json.loads(contract_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CatalogError(f"cannot read {contract_path.name}: {exc}") from exc
        contract = validate_workflow_contract(raw)
        contract_id = contract["id"]
        if contract_id in seen:
            raise CatalogError(f"duplicate workflow contract id: {contract_id}")
        seen.add(contract_id)
        contracts.append(contract)

    if not contracts:
        raise CatalogError("no workflow contracts found")
    return contracts


def cross_reference_stages(contract: dict[str, Any]) -> list[str]:
    """Check that depends_on and approval_gates reference valid stage IDs.

    Returns a list of issues found (empty means valid).
    """
    issues: list[str] = []
    stage_ids = {s["id"] for s in contract.get("stages", [])}

    for stage in contract.get("stages", []):
        for dep in stage.get("depends_on", []):
            if dep not in stage_ids:
                issues.append(
                    f"stage '{stage['id']}' depends_on unknown stage '{dep}'"
                )

    for gate in contract.get("approval_gates", []):
        after = gate["after_stage"]
        if after not in stage_ids:
            issues.append(
                f"approval gate '{gate['id']}' references unknown stage '{after}'"
            )

    for se in contract.get("safety", {}).get("side_effects", []):
        if se["stage_id"] not in stage_ids:
            issues.append(
                f"side effect '{se['description']}' references unknown stage '{se['stage_id']}'"
            )

    return issues
