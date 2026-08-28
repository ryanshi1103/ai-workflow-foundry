"""Minimum-sufficient model-visible tool exposure at the provider boundary."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from .models import TaskSpec
from .workspace import atomic_write_json, utc_now

POLICY_VERSION = "v0"
_POLICY_FILE = "tool-exposure-policy.json"
_ATTEMPT_PATTERN = re.compile(r"tool-policy-attempt-(\d{4})\.json")


class TaskToolRequirement(StrEnum):
    """Provider-independent task requirements covered by v0."""

    NO_EXTERNAL_ACTION = "NO_EXTERNAL_ACTION"
    READ_EXACT_FILE = "READ_EXACT_FILE"


class ToolCapability(StrEnum):
    """Provider-independent task tool capabilities."""

    READ_FILE = "READ_FILE"


class ProtocolTool(StrEnum):
    """Provider protocol auxiliaries that are not task capabilities."""

    STRUCTURED_OUTPUT = "StructuredOutput"


class ToolPolicyMode(StrEnum):
    MINIMUM_SUFFICIENT = "minimum_sufficient"
    PROVIDER_DEFAULT = "provider_default"
    UNSUPPORTED = "unsupported"


class TranslationStatus(StrEnum):
    TRANSLATED = "translated"
    PROVIDER_DEFAULT = "provider_default"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ToolExposurePolicy:
    """One durable task requirement and its concrete provider translation."""

    task_id: str
    mode: ToolPolicyMode
    policy_applied: bool
    coverage: bool
    required_capabilities: tuple[str, ...]
    task_tools: tuple[str, ...]
    protocol_tools: tuple[str, ...]
    effective_tool_names: tuple[str, ...]
    provider: str
    translation_status: TranslationStatus
    effective_tools_status: str
    reason: str
    tool_exposure_fingerprint: str | None
    policy_version: str = POLICY_VERSION
    schema_version: int = 1

    @property
    def runnable(self) -> bool:
        return self.translation_status != TranslationStatus.UNSUPPORTED

    @property
    def cli_tool_names(self) -> tuple[str, ...] | None:
        """Task tools for an explicit Claude-compatible ``--tools`` argument."""

        if not self.policy_applied or not self.runnable:
            return None
        return tuple(
            name for name in self.effective_tool_names if name not in self.protocol_tools
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "task_id": self.task_id,
            "mode": self.mode.value,
            "policy_applied": self.policy_applied,
            "coverage": self.coverage,
            "required_capabilities": list(self.required_capabilities),
            "task_tools": list(self.task_tools),
            "protocol_tools": list(self.protocol_tools),
            "effective_tool_names": list(self.effective_tool_names),
            "provider": self.provider,
            "translation_status": self.translation_status.value,
            "effective_tools_status": self.effective_tools_status,
            "reason": self.reason,
            "tool_exposure_fingerprint": self.tool_exposure_fingerprint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolExposurePolicy:
        if int(data.get("schema_version", 0)) != 1:
            raise ValueError("unsupported tool exposure policy schema")
        if str(data.get("policy_version")) != POLICY_VERSION:
            raise ValueError("unsupported tool exposure policy version")
        return cls(
            task_id=str(data["task_id"]),
            mode=ToolPolicyMode(str(data["mode"])),
            policy_applied=bool(data.get("policy_applied", False)),
            coverage=bool(data.get("coverage", False)),
            required_capabilities=tuple(
                str(item) for item in data.get("required_capabilities", ())
            ),
            task_tools=tuple(str(item) for item in data.get("task_tools", ())),
            protocol_tools=tuple(str(item) for item in data.get("protocol_tools", ())),
            effective_tool_names=tuple(
                str(item) for item in data.get("effective_tool_names", ())
            ),
            provider=str(data.get("provider", "")),
            translation_status=TranslationStatus(str(data["translation_status"])),
            effective_tools_status=str(data.get("effective_tools_status", "unavailable")),
            reason=str(data.get("reason", "")),
            tool_exposure_fingerprint=(
                str(data["tool_exposure_fingerprint"])
                if data.get("tool_exposure_fingerprint") is not None
                else None
            ),
        )

    def compact_receipt(self) -> dict[str, Any]:
        return {
            "tool_policy_version": self.policy_version,
            "tool_policy_applied": self.policy_applied,
            "tool_policy_coverage": self.coverage,
            "required_capabilities": list(self.required_capabilities),
            "task_tool_count": len(self.task_tools),
            "protocol_tool_count": len(self.protocol_tools),
            "effective_tool_count": (
                len(self.effective_tool_names)
                if self.effective_tools_status == "exact"
                else None
            ),
            "translation_status": self.translation_status.value,
            "tool_exposure_fingerprint": self.tool_exposure_fingerprint,
        }


@dataclass(frozen=True)
class ProviderToolExposure:
    policy: ToolExposurePolicy
    cli_args: tuple[str, ...]


@dataclass(frozen=True)
class ToolObservation:
    """Keep requested, exposed, and executed facts explicitly separate."""

    tools_exposed: tuple[str, ...]
    tools_requested: tuple[str, ...]
    tools_executed: tuple[str, ...]
    unexpected_tool_requests: tuple[str, ...]
    exposure_status: str
    request_status: str
    execution_status: str

    @classmethod
    def from_events(
        cls,
        *,
        exposed: Iterable[str],
        requested: Iterable[str],
        executed: Iterable[str],
        request_status: str = "complete",
        execution_status: str = "complete",
    ) -> ToolObservation:
        exposed_names = tuple(sorted(set(exposed)))
        requested_names = tuple(sorted(set(requested)))
        executed_names = tuple(sorted(set(executed)))
        return cls(
            tools_exposed=exposed_names,
            tools_requested=requested_names,
            tools_executed=executed_names,
            unexpected_tool_requests=tuple(
                name for name in requested_names if name not in exposed_names
            ),
            exposure_status="exact",
            request_status=request_status,
            execution_status=execution_status,
        )

    @classmethod
    def from_runtime_wrapper(
        cls,
        policy: ToolExposurePolicy,
        wrapper: dict[str, object],
    ) -> ToolObservation:
        exposed = (
            policy.effective_tool_names
            if policy.effective_tools_status == "exact"
            else ()
        )
        denied = wrapper.get("permission_denials")
        requested: list[str] = []
        if isinstance(denied, list):
            for item in denied:
                if isinstance(item, dict):
                    for key in ("tool_name", "tool", "name"):
                        value = item.get(key)
                        if isinstance(value, str) and value:
                            requested.append(value)
                            break
        observation = cls.from_events(
            exposed=exposed,
            requested=requested,
            executed=(),
            request_status="partial_denials_only" if isinstance(denied, list) else "unavailable",
            execution_status="unavailable",
        )
        if policy.effective_tools_status != "exact":
            return replace(observation, exposure_status="provider_default_unenumerated")
        return observation

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "tools_exposed": list(self.tools_exposed),
            "tools_requested": list(self.tools_requested),
            "tools_executed": list(self.tools_executed),
            "unexpected_tool_requests": list(self.unexpected_tool_requests),
            "unexpected_tool_request_count": len(self.unexpected_tool_requests),
            "exposure_status": self.exposure_status,
            "request_status": self.request_status,
            "execution_status": self.execution_status,
        }


def build_tool_policy(task: TaskSpec, provider: str) -> ToolExposurePolicy:
    """Classify only explicit v0 requirements; never infer no-tool from prose."""

    if task.tool_policy_mode != ToolPolicyMode.MINIMUM_SUFFICIENT.value:
        return ToolExposurePolicy(
            task_id=task.id,
            mode=ToolPolicyMode.PROVIDER_DEFAULT,
            policy_applied=False,
            coverage=False,
            required_capabilities=(),
            task_tools=(),
            protocol_tools=(),
            effective_tool_names=(),
            provider=provider,
            translation_status=TranslationStatus.PROVIDER_DEFAULT,
            effective_tools_status="provider_default_unenumerated",
            reason="task is not explicitly classified for v0; preserve provider default",
            tool_exposure_fingerprint=None,
        )

    requirement = str(task.tool_requirement or "")
    mapping: dict[str, tuple[str, ...]] = {
        TaskToolRequirement.NO_EXTERNAL_ACTION.value: (),
        TaskToolRequirement.READ_EXACT_FILE.value: (ToolCapability.READ_FILE.value,),
    }
    if requirement not in mapping:
        return ToolExposurePolicy(
            task_id=task.id,
            mode=ToolPolicyMode.UNSUPPORTED,
            policy_applied=False,
            coverage=False,
            required_capabilities=(requirement,) if requirement else (),
            task_tools=(),
            protocol_tools=(),
            effective_tool_names=(),
            provider=provider,
            translation_status=TranslationStatus.UNSUPPORTED,
            effective_tools_status="unavailable",
            reason="TOOL_POLICY_UNSUPPORTED_CAPABILITY",
            tool_exposure_fingerprint=None,
        )
    if requirement == TaskToolRequirement.READ_EXACT_FILE.value and not (
        isinstance(task.inputs.get("exact_file_path"), str)
        and str(task.inputs["exact_file_path"]).strip()
    ):
        return ToolExposurePolicy(
            task_id=task.id,
            mode=ToolPolicyMode.UNSUPPORTED,
            policy_applied=False,
            coverage=False,
            required_capabilities=(requirement,),
            task_tools=(),
            protocol_tools=(),
            effective_tool_names=(),
            provider=provider,
            translation_status=TranslationStatus.UNSUPPORTED,
            effective_tools_status="unavailable",
            reason="TOOL_POLICY_EXACT_PATH_REQUIRED",
            tool_exposure_fingerprint=None,
        )
    base = ToolExposurePolicy(
        task_id=task.id,
        mode=ToolPolicyMode.MINIMUM_SUFFICIENT,
        policy_applied=True,
        coverage=True,
        required_capabilities=(requirement,),
        task_tools=mapping[requirement],
        protocol_tools=(),
        effective_tool_names=(),
        provider=provider,
        translation_status=TranslationStatus.UNSUPPORTED,
        effective_tools_status="unavailable",
        reason="provider translation pending",
        tool_exposure_fingerprint=None,
    )
    return translate_tool_exposure(base)


def translate_tool_exposure(policy: ToolExposurePolicy) -> ToolExposurePolicy:
    """Translate provider-independent capabilities only at the adapter boundary."""

    if policy.mode != ToolPolicyMode.MINIMUM_SUFFICIENT:
        return policy
    if policy.provider not in {"claude", "deepseek"}:
        return replace(
            policy,
            translation_status=TranslationStatus.UNSUPPORTED,
            reason="TOOL_POLICY_UNSUPPORTED_PROVIDER",
        )
    names_by_capability = {ToolCapability.READ_FILE.value: "Read"}
    try:
        task_names = tuple(names_by_capability[item] for item in policy.task_tools)
    except KeyError:
        return replace(
            policy,
            translation_status=TranslationStatus.UNSUPPORTED,
            reason="TOOL_POLICY_UNSUPPORTED_CAPABILITY",
        )
    protocol = (ProtocolTool.STRUCTURED_OUTPUT.value,)
    effective = tuple(sorted((*task_names, *protocol)))
    fingerprint = _fingerprint(policy.provider, effective)
    return replace(
        policy,
        protocol_tools=protocol,
        effective_tool_names=effective,
        translation_status=TranslationStatus.TRANSLATED,
        effective_tools_status="exact",
        reason="v0 requirement translated to minimum sufficient exposure",
        tool_exposure_fingerprint=fingerprint,
    )


def provider_tool_exposure(policy: ToolExposurePolicy) -> ProviderToolExposure:
    if not policy.runnable or not policy.policy_applied:
        return ProviderToolExposure(policy, ())
    task_names = policy.cli_tool_names
    assert task_names is not None
    return ProviderToolExposure(policy, ("--tools", ",".join(task_names)))


class ToolPolicyStore:
    """Persist one immutable decision and a compact receipt for every provider attempt."""

    def __init__(self, task_dir: Path) -> None:
        self.task_dir = task_dir
        self.policy_path = task_dir / _POLICY_FILE

    def resolve(self, task: TaskSpec, provider: str) -> tuple[ProviderToolExposure, str]:
        if self.policy_path.is_file():
            data = json.loads(self.policy_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("tool exposure policy must be a JSON object")
            policy = ToolExposurePolicy.from_dict(data)
            if policy.task_id != task.id:
                raise ValueError("durable tool policy belongs to another task")
            if policy.provider != provider and policy.policy_applied:
                policy = replace(
                    policy,
                    provider=provider,
                    translation_status=TranslationStatus.UNSUPPORTED,
                    effective_tool_names=(),
                    effective_tools_status="unavailable",
                    reason="TOOL_POLICY_PROVIDER_CHANGED",
                    tool_exposure_fingerprint=None,
                )
        else:
            policy = build_tool_policy(task, provider)
            atomic_write_json(self.policy_path, policy.to_dict())

        attempt_number = self._next_attempt_number()
        attempt_ref = f"tool-policy-attempt-{attempt_number:04d}.json"
        atomic_write_json(
            self.task_dir / attempt_ref,
            {
                **policy.to_dict(),
                "attempt_sequence": attempt_number,
                "decision_ref": _POLICY_FILE,
                "recorded_at": utc_now(),
            },
        )
        return provider_tool_exposure(policy), attempt_ref

    def _next_attempt_number(self) -> int:
        numbers = [
            int(match.group(1))
            for path in self.task_dir.glob("tool-policy-attempt-*.json")
            if (match := _ATTEMPT_PATTERN.fullmatch(path.name)) is not None
        ]
        return max(numbers, default=0) + 1


def persist_tool_observation(
    task_dir: Path,
    policy: ToolExposurePolicy,
    wrapper: dict[str, object] | None = None,
) -> tuple[str, ToolObservation]:
    observation = ToolObservation.from_runtime_wrapper(policy, wrapper or {})
    ref = "tool-observation.json"
    atomic_write_json(task_dir / ref, observation.to_dict())
    return ref, observation


def _fingerprint(provider: str, effective_names: tuple[str, ...]) -> str:
    payload = json.dumps(
        {
            "effective_tool_names": sorted(effective_names),
            "policy_version": POLICY_VERSION,
            "provider": provider,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
