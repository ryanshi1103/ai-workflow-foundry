"""Project creation, directory structure, meta.json management."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..utils import (
    PROJECT_INDEX_FILE,
    PROJECTS_ROOT,
    atomic_write_json,
    ensure_dir,
    generate_project_temp_name,
    read_json,
    sanitize_project_title,
    timestamp_iso,
)


def discover_projects() -> list[dict]:
    """Return valid projects, newest first, deduplicated by resolved path.

    The global index is authoritative when usable.  A filesystem scan is used
    only when it is missing, malformed, or contains no valid project paths.
    """
    projects = []
    index = read_json(PROJECT_INDEX_FILE)
    if isinstance(index, dict) and isinstance(index.get("projects"), dict):
        for key, entry in index["projects"].items():
            if not isinstance(entry, dict) or not entry.get("path"):
                continue
            path = Path(entry["path"]).expanduser().resolve()
            meta = read_project_meta(path)
            if not meta:
                continue
            projects.append(_project_choice(path, meta, entry, key))

    if not projects and PROJECTS_ROOT.exists():
        for meta_path in PROJECTS_ROOT.glob("*/.ai-session/project.json"):
            path = meta_path.parent.parent.resolve()
            meta = read_json(meta_path)
            if isinstance(meta, dict):
                projects.append(
                    _project_choice(path, meta, {}, meta.get("session_id", ""))
                )

    # The index may contain one entry per session. Present each project once.
    by_path = {}
    for item in projects:
        old = by_path.get(item["path"])
        if old is None or item["last_updated"] > old["last_updated"]:
            by_path[item["path"]] = item
    return sorted(by_path.values(), key=lambda p: p["last_updated"], reverse=True)


PROJECT_DISCOVERY_MARKERS = (
    ".git",
    ".ai-session",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
    "CMakeLists.txt",
    "Makefile",
    "src",
    "app",
)
PROJECT_DISCOVERY_EXCLUDED = {"_Archive", "_Inbox", "trash", "cache", "__pycache__"}
PROJECT_DISCOVERY_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".rs",
    ".go",
    ".java",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".sh",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
}


def _has_project_evidence(path: Path) -> bool:
    if any((path / marker).exists() for marker in PROJECT_DISCOVERY_MARKERS):
        return True
    for config_dir in (path / ".claude", path / ".codex"):
        if config_dir.is_dir() and any(
            item.is_file() for item in config_dir.rglob("*")
        ):
            return True
    try:
        return any(
            item.is_file() and item.suffix.lower() in PROJECT_DISCOVERY_SUFFIXES
            for item in path.iterdir()
        )
    except OSError:
        return False


def discover_project_directories() -> list[dict]:
    """Discover direct, unregistered Projects candidates without writing."""
    if not PROJECTS_ROOT.is_dir():
        return []
    root = PROJECTS_ROOT.resolve()
    found = []
    for entry in sorted(PROJECTS_ROOT.iterdir(), key=lambda p: p.name.casefold()):
        if (
            entry.name.startswith(".")
            or entry.name in PROJECT_DISCOVERY_EXCLUDED
            or not entry.is_dir()
        ):
            continue
        path = entry.resolve()
        if path.parent != root or not _has_project_evidence(path):
            continue
        found.append(
            {
                "project_id": None,
                "name": path.name,
                "path": str(path),
                "status": "unregistered",
                "tool": "—",
                "last_updated": "",
            }
        )
    return found


def discover_selectable_projects() -> list[dict]:
    registered = discover_projects()
    seen = {str(Path(item["path"]).resolve()) for item in registered}
    return registered + [
        item
        for item in discover_project_directories()
        if str(Path(item["path"]).resolve()) not in seen
    ]


def _project_choice(path: Path, meta: dict, entry: dict, key: str) -> dict:
    return {
        "project_id": meta.get("project_id") or key,
        "name": path.name,
        "path": str(path),
        "status": entry.get("status") or meta.get("status") or "unknown",
        "tool": entry.get("tool") or meta.get("tool") or "unknown",
        "last_updated": (
            entry.get("last_updated")
            or meta.get("last_updated")
            or meta.get("end_time")
            or meta.get("start_time")
            or ""
        ),
    }


def print_project_choices(projects: list[dict]) -> None:
    """Print a stable, human-readable numbered project list."""
    for number, item in enumerate(projects, 1):
        print(f"[{number}] {item['name']}")
        print(
            f"    状态: {item['status']}  工具: {item['tool']}  last_updated: {item['last_updated'] or '-'}"
        )
        print(f"    路径: {item['path']}")


def choose_project(input_func=input) -> Path | None:
    """Interactively choose an existing project; reusable by any tool."""
    projects = discover_selectable_projects()
    if not projects:
        print("没有找到已有项目。", file=sys.stderr)
        return None
    print_project_choices(projects)
    try:
        answer = input("请输入项目编号（q 取消）: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if answer == "q":
        return None
    try:
        selected = projects[int(answer) - 1]
    except (ValueError, IndexError):
        print("无效的项目编号。", file=sys.stderr)
        return None
    return Path(selected["path"])


# ─── Project directory structure ────────────────────────────────────────────

PROJECT_SKELETON = {
    "files": {
        "README.md": "# {title}\n\n## 项目目标\n\n<!-- Auto-generated by ai-project-manager -->\n\n## 当前状态\n\n初始化中…\n\n## 最后更新时间\n\n{timestamp}\n",
        "AGENTS.md": (
            "# AGENTS.md — Project Rules\n\n"
            "1. All project deliverables are saved within this project directory.\n"
            "2. Do not modify files outside this project unless the user explicitly requests it.\n"
            "3. Maintain README.md and docs/ as the session progresses.\n"
            "4. Do not modify `.ai-session/private/`.\n"
            "5. Do not write secrets or API keys into Git.\n"
            "6. Auto-archiving is infrastructure — do not treat it as a primary task.\n"
        ),
        "CLAUDE.md": (
            "# CLAUDE.md — Project Rules\n\n"
            "1. All project deliverables are saved within this project directory.\n"
            "2. Do not modify files outside this project unless the user explicitly requests it.\n"
            "3. Maintain README.md and docs/ as the session progresses.\n"
            "4. Do not modify `.ai-session/private/`.\n"
            "5. Do not write secrets or API keys into Git.\n"
            "6. Auto-archiving is infrastructure — do not treat it as a primary task.\n"
        ),
    },
    "dirs": [
        "docs/sessions",
        ".ai-session/sessions",
        ".ai-session/private",
    ],
}

GITIGNORE_CONTENT = """\
# AI Project Manager — private session data (NOT committed)
.ai-session/private/
.ai-session/*.lock
.ai-session/**/*.lock

# Temporary files
*.tmp
*.swp
*~

# Python cache
__pycache__/
*.pyc

# Secrets
.env
.env.*
*.pem
*.key
secrets/
credentials.*
"""


def create_project_structure(project_dir: Path, title: str = "New Project") -> None:
    """Create the standard project directory skeleton."""
    ensure_dir(project_dir)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Create directories
    for d in PROJECT_SKELETON["dirs"]:
        ensure_dir(project_dir / d)

    # Create files with template content
    for filename, template in PROJECT_SKELETON["files"].items():
        filepath = project_dir / filename
        if not filepath.exists():
            content = template.format(title=title, timestamp=timestamp)
            filepath.write_text(content, encoding="utf-8")

    # Create .gitignore
    gitignore = project_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(GITIGNORE_CONTENT, encoding="utf-8")

    # Ensure private dir is locked down
    private_dir = project_dir / ".ai-session" / "private"
    ensure_dir(private_dir)
    try:
        private_dir.chmod(0o700)
    except OSError:
        pass


def create_project_meta(
    project_dir: Path,
    tool: str,
    session_id: str,
    cli_session_id: str = "",
    model: str = "",
    provider: str = "",
    permission_mode: str = "",
    transcript_path: str = "",
    cli_path: str = "",
    cli_version: str = "",
    workflow_contract: dict | None = None,
) -> dict:
    """Create project.json metadata."""
    meta = {
        "project_id": session_id,  # initial; may be renamed later
        "session_id": session_id,
        "cli_session_id": cli_session_id,
        "tool": tool,
        "model": model,
        "provider_or_profile": provider,
        "permission_mode": permission_mode,
        "start_time": timestamp_iso(),
        "end_time": None,
        "status": "initializing",
        "initial_cwd": str(project_dir),
        "project_path_initial": str(project_dir),
        "project_path_final": str(project_dir),
        "git_root": str(project_dir),
        "transcript_source": transcript_path,
        "transcript_parser": f"transcript_{tool}.py",
        "cli_path": cli_path,
        "cli_version": cli_version,
        "shell": os.environ.get("SHELL", ""),
        "hostname": os.uname().nodename,
        "first_prompt_hash": None,
        "transcript_hash": None,
        "redaction_applied": False,
        "summary_mode": None,  # "ai", "fallback", or None
        "summary_success": False,
        "final_commit": None,
        "finalize_attempts": 0,
        "last_error": None,
    }
    if workflow_contract:
        meta["workflow_contract"] = {
            "id": workflow_contract["id"],
            "version": workflow_contract["version"],
            "source": "repo",
            "file": ".ai-session/workflow.contract.json",
        }
    atomic_write_json(project_dir / ".ai-session" / "project.json", meta)
    return meta


def read_project_meta(project_dir: Path) -> dict | None:
    """Read project.json from a project directory."""
    return read_json(project_dir / ".ai-session" / "project.json")


def create_session_meta(
    project_dir: Path,
    session_id: str,
    tool: str,
    model: str = "",
    provider: str = "",
    permission_mode: str = "",
    cli_path: str = "",
    cli_version: str = "",
    cli_session_id: str = "",
    transcript_path: str = "",
) -> dict:
    """Create session meta.json for a specific session."""
    session_meta = {
        "session_id": session_id,
        "cli_session_id": cli_session_id,
        "tool": tool,
        "model": model,
        "provider_or_profile": provider,
        "permission_mode": permission_mode,
        "start_time": timestamp_iso(),
        "end_time": None,
        "status": "initializing",
        "cwd": str(project_dir),
        "transcript_source": transcript_path,
        "transcript_parser": f"transcript_{tool}.py",
        "cli_path": cli_path,
        "cli_version": cli_version,
        "shell": os.environ.get("SHELL", ""),
        "hostname": os.uname().nodename,
        "first_prompt_hash": None,
        "transcript_hash": None,
        "redaction_applied": False,
        "summary_mode": None,
        "summary_success": False,
        "final_commit": None,
        "finalize_attempts": 0,
        "last_error": None,
    }
    session_dir = project_dir / ".ai-session" / "sessions" / session_id
    ensure_dir(session_dir)
    atomic_write_json(session_dir / "meta.json", session_meta)
    return session_meta


def create_new_project(
    tool: str,
    model: str = "",
    provider: str = "",
    permission_mode: str = "",
    cli_path: str = "",
    cli_version: str = "",
    workflow_contract_id: str | None = None,
) -> Path:
    """Create a new project directory in ~/Projects and return its path.

    If *workflow_contract_id* is given, the referenced contract is validated
    and copied into the project's ``.ai-session/`` directory so the project
    carries its own workflow definition.
    """
    ensure_dir(PROJECTS_ROOT)

    # Validate workflow contract early if specified
    workflow_contract = None
    if workflow_contract_id:
        try:
            from flowfoundry.workflow_contract import load_workflow_contracts

            contracts = load_workflow_contracts()
            matching = [c for c in contracts if c["id"] == workflow_contract_id]
            if not matching:
                print(
                    f"Error: unknown workflow contract: {workflow_contract_id}",
                    file=sys.stderr,
                )
                raise SystemExit(1)
            workflow_contract = matching[0]
        except SystemExit:
            raise
        except Exception as exc:
            print(f"Error: cannot load workflow contract: {exc}", file=sys.stderr)
            raise SystemExit(1)

    temp_name = generate_project_temp_name(tool)
    project_dir = PROJECTS_ROOT / temp_name
    ensure_dir(project_dir)

    session_id = temp_name  # same as project temp name initially

    create_project_structure(project_dir, title="New Project")

    # Save workflow contract reference if specified
    if workflow_contract:
        import json

        wf_file = project_dir / ".ai-session" / "workflow.contract.json"
        wf_file.write_text(
            json.dumps(workflow_contract, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    create_project_meta(
        project_dir=project_dir,
        tool=tool,
        session_id=session_id,
        model=model,
        provider=provider,
        permission_mode=permission_mode,
        cli_path=cli_path,
        cli_version=cli_version,
        workflow_contract=workflow_contract,
    )
    create_session_meta(
        project_dir=project_dir,
        session_id=session_id,
        tool=tool,
        model=model,
        provider=provider,
        permission_mode=permission_mode,
        cli_path=cli_path,
        cli_version=cli_version,
    )

    # Update project index (initial status matches project.json)
    _update_project_index(project_dir, session_id, tool, status="initializing")

    return project_dir


def rename_project(project_dir: Path, title: str) -> Path | None:
    """Rename project directory to include the title. Returns new path or None."""
    if not project_dir.exists():
        return None

    title = sanitize_project_title(title)
    if not title or len(title) < 3:
        return None

    # Extract timestamp prefix from original name
    orig_name = project_dir.name
    # Format: YYYYMMDD-HHMMSS-tool-shortid
    parts = orig_name.split("-", 2)
    if len(parts) >= 2:
        prefix = f"{parts[0]}-{parts[1]}"  # YYYYMMDD-HHMMSS
    else:
        prefix = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    new_name = f"{prefix}-{title}"
    new_path = project_dir.parent / new_name

    # Handle collision
    if new_path.exists() and new_path != project_dir:
        counter = 2
        while (project_dir.parent / f"{new_name}-{counter:02d}").exists():
            counter += 1
        new_name = f"{new_name}-{counter:02d}"
        new_path = project_dir.parent / new_name

    try:
        project_dir.rename(new_path)
    except OSError:
        return None

    # Update meta
    meta = read_project_meta(new_path)
    if meta:
        meta["project_path_final"] = str(new_path)
        atomic_write_json(new_path / ".ai-session" / "project.json", meta)

    return new_path


def _update_project_index(
    project_dir: Path, session_id: str, tool: str, status: str = "running"
) -> None:
    """Update the global project index atomically."""
    from ..utils import GLOBAL_LOCK_FILE, STATE_DIR, atomic_write_json, file_lock

    ensure_dir(STATE_DIR)

    index_path = STATE_DIR / "project-index.json"
    with file_lock(GLOBAL_LOCK_FILE):
        index = read_json(index_path) or {"projects": {}}
        if session_id in index.get("projects", {}):
            # Update existing entry
            existing = index["projects"][session_id]
            existing["status"] = status
            existing["last_updated"] = timestamp_iso()
        else:
            # New entry
            index["projects"][session_id] = {
                "path": str(project_dir),
                "tool": tool,
                "status": status,
                "created": timestamp_iso(),
                "last_updated": timestamp_iso(),
            }
        atomic_write_json(index_path, index)


# ─── Status transition validation ────────────────────────────────────────────

VALID_TRANSITIONS = {
    "initializing": {"running", "failed", "empty"},
    "running": {"finalizing", "interrupted", "failed", "completed"},
    "finalizing": {"completed", "failed", "interrupted"},
    "completed": set(),  # terminal — no further transitions allowed
    "interrupted": {"running", "finalizing", "failed", "completed"},
    "failed": {"running", "finalizing"},
    "empty": {"completed", "failed"},
}


def validate_status_transition(from_status: str, to_status: str) -> bool:
    """Check if a status transition is valid."""
    if from_status not in VALID_TRANSITIONS:
        return True  # Unknown status — allow
    if to_status not in VALID_TRANSITIONS:
        return True  # Unknown target — allow
    return to_status in VALID_TRANSITIONS.get(from_status, set())


def update_project_status(
    project_dir: Path,
    new_status: str,
    session_id: str | None = None,
    tool: str | None = None,
    metadata: dict | None = None,
    index_metadata: dict | None = None,
) -> bool:
    """Synchronize project, session, and global-index finalization state.

    Uses a two-phase approach:
    1. Write project.json with new status (under file lock)
    2. Update project-index.json (under global lock)
    3. If index update fails, roll back project.json
    """
    from ..utils import (
        GLOBAL_LOCK_FILE,
        STATE_DIR,
        atomic_write_json,
        ensure_dir,
        file_lock,
        read_json,
        timestamp_iso,
    )

    project_file = project_dir / ".ai-session" / "project.json"
    if not project_file.exists():
        return False

    # Read current state
    meta = read_json(project_file)
    if not meta:
        return False
    old_meta = dict(meta)

    old_status = meta.get("status", "unknown")
    if old_status != new_status and not validate_status_transition(
        old_status, new_status
    ):
        # Invalid transition — log and skip
        try:
            log_dir = Path.home() / ".local" / "state" / "ai-project-manager" / "logs"
            ensure_dir(log_dir)
            with open(log_dir / "status-transitions.log", "a") as f:
                f.write(
                    f"[{timestamp_iso()}] BLOCKED: {old_status} → {new_status} "
                    f"in {project_dir.name}\n"
                )
        except (OSError, ValueError):
            return False
        return False

    if not session_id:
        session_id = meta.get("session_id", "")
    if not tool:
        tool = meta.get("tool", "unknown")

    session_meta_path = (
        project_dir / ".ai-session" / "sessions" / session_id / "meta.json"
    )
    old_session_meta = (
        read_json(session_meta_path) if session_meta_path.exists() else None
    )

    # Phase 1: Update both tracked metadata files with the exact same shared fields.
    meta["status"] = new_status
    meta["last_updated"] = timestamp_iso()
    if metadata:
        meta.update(metadata)
    atomic_write_json(project_file, meta)
    if old_session_meta:
        session_meta = dict(old_session_meta)
        session_meta["status"] = new_status
        session_meta["last_updated"] = meta["last_updated"]
        if metadata:
            session_meta.update(metadata)
        atomic_write_json(session_meta_path, session_meta)

    # Phase 2: Update project-index.json
    try:
        ensure_dir(STATE_DIR)
        index_path = STATE_DIR / "project-index.json"
        with file_lock(GLOBAL_LOCK_FILE):
            index = read_json(index_path) or {"projects": {}}
            if session_id in index.get("projects", {}):
                index["projects"][session_id]["status"] = new_status
                index["projects"][session_id]["last_updated"] = timestamp_iso()
            else:
                index["projects"][session_id] = {
                    "path": str(project_dir),
                    "tool": tool,
                    "status": new_status,
                    "created": meta.get("start_time", timestamp_iso()),
                    "last_updated": timestamp_iso(),
                }
            if index_metadata:
                index["projects"][session_id].update(index_metadata)
            atomic_write_json(index_path, index)
    except Exception:
        # Roll back both tracked files if the global phase fails.
        atomic_write_json(project_file, old_meta)
        if old_session_meta:
            atomic_write_json(session_meta_path, old_session_meta)
        return False

    return True
