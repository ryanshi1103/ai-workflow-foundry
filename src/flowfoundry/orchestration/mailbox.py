"""Atomic filesystem mailbox for agent-to-agent result exchange."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .workspace import RunWorkspace, atomic_write_json, secure_file_lock, utc_now


@dataclass(frozen=True)
class MailMessage:
    sequence: int
    sender: str
    recipient: str
    task_id: str
    kind: str
    payload: dict[str, Any]
    created_at: str
    schema_version: int = 1


class Mailbox:
    def __init__(self, workspace: RunWorkspace) -> None:
        self.workspace = workspace

    def send(
        self,
        *,
        sender: str,
        recipient: str,
        task_id: str,
        kind: str,
        payload: dict[str, Any],
    ) -> MailMessage:
        messages_dir = self.workspace.contained("messages")
        with secure_file_lock(self.workspace.contained(".mailbox.lock")):
            sequence = len(list(messages_dir.glob("*.json"))) + 1
            message = MailMessage(
                sequence=sequence,
                sender=sender,
                recipient=recipient,
                task_id=task_id,
                kind=kind,
                payload=payload,
                created_at=utc_now(),
            )
            atomic_write_json(
                messages_dir / f"{sequence:06d}-{task_id}.json",
                message.__dict__,
            )
        return message

    def list(self, *, recipient: str | None = None) -> list[dict[str, Any]]:
        messages = [
            self.workspace.read_json(str(path.relative_to(self.workspace.path)))
            for path in sorted(self.workspace.contained("messages").glob("*.json"))
        ]
        if recipient is not None:
            messages = [message for message in messages if message["recipient"] == recipient]
        return messages
