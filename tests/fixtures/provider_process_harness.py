"""Offline process fixture for provider cancellation tests."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def mark_ready(path: str) -> None:
    if path != "-":
        Path(path).write_text("ready\n", encoding="utf-8")


def sleep_forever() -> None:
    while True:
        time.sleep(1)


def main() -> int:
    mode = sys.argv[1]
    ready_path = sys.argv[2] if len(sys.argv) > 2 else "-"
    extra_path = sys.argv[3] if len(sys.argv) > 3 else "-"

    if mode == "exec-launcher":
        target_ready_path = sys.argv[4]
        target_mode = sys.argv[5] if len(sys.argv) > 5 else "exec-target"
        child_pid_path = sys.argv[6] if len(sys.argv) > 6 else "-"
        mark_ready(ready_path)
        while not Path(extra_path).exists():
            time.sleep(0.01)
        os.execv(
            sys.executable,
            [sys.executable, __file__, target_mode, target_ready_path, child_pid_path],
        )

    if mode == "exec-target":
        def stop_after_exec(_signum: int, _frame: object) -> None:
            print("exec-target-stop", flush=True)
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, stop_after_exec)
        print("exec-target-running", flush=True)
        mark_ready(ready_path)
        sleep_forever()

    if mode == "exec-target-child":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        child = subprocess.Popen(
            [sys.executable, __file__, "child-worker", "-"],
            start_new_session=False,
        )
        if extra_path != "-":
            Path(extra_path).write_text(str(child.pid), encoding="utf-8")
        print(f"exec-target-child-running:{child.pid}", flush=True)
        mark_ready(ready_path)
        sleep_forever()

    if mode == "complete":
        mark_ready(ready_path)
        print("completed", flush=True)
        return 0

    if mode == "graceful":
        def stop(_signum: int, _frame: object) -> None:
            print("graceful-stop", flush=True)
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, stop)
        print("partial-before-cancel", flush=True)
        mark_ready(ready_path)
        sleep_forever()

    if mode == "write-graceful":
        def stop_writer(_signum: int, _frame: object) -> None:
            print("graceful-writer-stop", flush=True)
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, stop_writer)
        Path("base.txt").write_text("partial-candidate\n", encoding="utf-8")
        print("partial-candidate-written", flush=True)
        mark_ready(ready_path)
        sleep_forever()

    if mode == "ignore":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        print("partial-before-force", flush=True)
        mark_ready(ready_path)
        sleep_forever()

    if mode == "child":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        child = subprocess.Popen(
            [sys.executable, __file__, "child-worker", "-"],
            start_new_session=False,
        )
        if extra_path != "-":
            Path(extra_path).write_text(str(child.pid), encoding="utf-8")
        print(f"child-started:{child.pid}", flush=True)
        mark_ready(ready_path)
        sleep_forever()

    if mode == "child-worker":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        sleep_forever()

    raise ValueError(f"unknown harness mode: {mode}")


if __name__ == "__main__":
    raise SystemExit(main())
