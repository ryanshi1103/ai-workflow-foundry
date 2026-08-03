#!/usr/bin/env python3
"""Project maintenance system for ~/Projects.

Supports:
  --quick    Weekly quick maintenance
  --deep     Monthly deep maintenance
  --report   Generate projects index
  --purge-quarantine  Process quarantine retention
  --dry-run  Preview only, no changes
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import defaultdict, Counter

from .utils import (
    PROJECTS_ROOT, ensure_dir, read_json, atomic_write_json,
    timestamp_iso, generate_short_id, compute_sha256,
)
from .auto_name import (
    analyze_project, update_project_json, is_placeholder_name,
    is_meaningful_name, safe_rename_project, suggest_rename,
    analyze_all_projects,
)

# ─── Paths ─────────────────────────────────────────────────────────────────

CONFIG_DIR = Path.home() / ".config" / "cc-projects"
MAINTENANCE_CONF = CONFIG_DIR / "maintenance.conf"
PROTECTED_LIST = CONFIG_DIR / "protected-projects"
MANAGED_PROJECTS_LIST = CONFIG_DIR / "managed-projects"
STATE_DIR = Path.home() / ".local" / "state" / "cc-projects"
QUARANTINE_DIR = PROJECTS_ROOT / "_trash-review"
QUARANTINE_INDEX = STATE_DIR / "quarantine-index.jsonl"
PROJECTS_INDEX_MD = PROJECTS_ROOT / "PROJECTS_INDEX.md"
PROJECTS_INDEX_JSON = STATE_DIR / "projects-index.json"
MAINTENANCE_LOG = STATE_DIR / "maintenance.log"
BACKUP_DIR = STATE_DIR / "backups"

# ─── Default config ────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "PROJECTS_ROOT": str(PROJECTS_ROOT),
    "QUARANTINE_DAYS": "14",
    "AUTO_RENAME_PLACEHOLDERS": "true",
    "AUTO_MERGE_DUPLICATES": "true",
    "AUTO_QUARANTINE_LOW_VALUE": "true",
    "AUTO_PURGE_AFTER_RETENTION": "true",
    "AUTO_SYNC_MANAGED": "true",
    "DRY_RUN": "false",
    "QUICK_CRON": "weekly",
    "DEEP_CRON": "monthly",
    "PURGE_CRON": "weekly",
}


def load_config() -> dict:
    """Load maintenance configuration."""
    config = dict(DEFAULT_CONFIG)
    if MAINTENANCE_CONF.exists():
        try:
            content = MAINTENANCE_CONF.read_text(encoding='utf-8')
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip().strip('"').strip("'")
        except OSError:
            pass
    return config


def load_protected() -> set:
    """Load protected project paths or names.

    Both the original one-value-per-line format and the annotated
    ``PATH | TYPE | REASON`` format used by deployed configurations are
    accepted.  Only the first field participates in protection checks.
    """
    protected = set()
    if PROTECTED_LIST.exists():
        try:
            for line in PROTECTED_LIST.read_text(encoding='utf-8').split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    entry = line.split('|', 1)[0].strip()
                    if entry:
                        protected.add(entry)
        except OSError:
            pass
    return protected


def load_managed_projects() -> list[dict]:
    """Load cc picker groups and safe local update policy.

    Lines use ``NAME | GROUP | AUTO_UPDATE | REASON``. Invalid project names
    are ignored so configuration can never escape the direct Projects root.
    """
    projects = []
    if not MANAGED_PROJECTS_LIST.exists():
        return projects
    try:
        lines = MANAGED_PROJECTS_LIST.read_text(encoding="utf-8").splitlines()
    except OSError:
        return projects

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split("|", 3)]
        if len(fields) < 3:
            continue
        name, group, auto_update = fields[:3]
        reason = fields[3] if len(fields) == 4 else ""
        if not name or name in {".", ".."} or "/" in name or "\\" in name:
            continue
        if group not in {"primary", "managed", "archive"}:
            group = "primary"
        projects.append({
            "name": name,
            "group": group,
            "auto_update": auto_update.lower() in {"1", "true", "yes", "on"},
            "reason": reason,
        })
    return projects


def _run_git(project_dir: Path, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    """Run Git without prompts so timers cannot hang waiting for credentials."""
    env = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    return subprocess.run(
        ["git", "-C", str(project_dir), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def sync_managed_projects(dry_run: bool = False) -> list[dict]:
    """Safely fast-forward configured local Git repositories.

    No dirty, ahead, detached, untracked-upstream, or diverged repository is
    modified. A dry run does not fetch and only reports the currently known
    upstream relationship.
    """
    results = []
    root = PROJECTS_ROOT.resolve()
    for entry in load_managed_projects():
        if not entry["auto_update"]:
            continue
        project_dir = (root / entry["name"]).resolve()
        result = {"name": entry["name"], "group": entry["group"]}
        if project_dir.parent != root or not project_dir.is_dir():
            results.append({**result, "status": "missing"})
            continue
        if not (project_dir / ".git").exists():
            results.append({**result, "status": "not-git"})
            continue

        try:
            dirty = _run_git(project_dir, ["status", "--porcelain"])
            if dirty.returncode != 0:
                results.append({**result, "status": "error", "detail": dirty.stderr.strip()})
                continue
            if dirty.stdout.strip():
                results.append({**result, "status": "dirty"})
                continue

            branch = _run_git(project_dir, ["symbolic-ref", "--quiet", "--short", "HEAD"])
            if branch.returncode != 0:
                results.append({**result, "status": "detached"})
                continue
            upstream = _run_git(project_dir, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"])
            if upstream.returncode != 0:
                results.append({**result, "status": "no-upstream"})
                continue

            if not dry_run:
                fetched = _run_git(project_dir, ["fetch", "--prune"], timeout=120)
                if fetched.returncode != 0:
                    results.append({**result, "status": "fetch-error", "detail": fetched.stderr.strip()})
                    continue

            counts = _run_git(project_dir, ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"])
            if counts.returncode != 0:
                results.append({**result, "status": "error", "detail": counts.stderr.strip()})
                continue
            ahead_text, behind_text = counts.stdout.split()
            ahead, behind = int(ahead_text), int(behind_text)
            if ahead:
                status = "diverged" if behind else "ahead"
                results.append({**result, "status": status, "ahead": ahead, "behind": behind})
                continue
            if not behind:
                results.append({**result, "status": "up-to-date"})
                continue
            if dry_run:
                results.append({**result, "status": "would-update", "behind": behind})
                continue

            merged = _run_git(project_dir, ["merge", "--ff-only", "@{upstream}"])
            if merged.returncode == 0:
                results.append({**result, "status": "updated", "behind": behind})
            else:
                results.append({**result, "status": "merge-error", "detail": merged.stderr.strip()})
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            results.append({**result, "status": "error", "detail": str(exc)})
    return results


def is_protected(project_path: Path, protected: set) -> bool:
    """Check if a project is in the protection list."""
    path_str = str(project_path.resolve())
    name = project_path.name
    for entry in protected:
        if entry == path_str or entry == name:
            return True
        if entry.endswith('/') and path_str.startswith(entry.rstrip('/')):
            return True
    return False


def log_maintenance(message: str, level: str = "INFO") -> None:
    """Log a maintenance action."""
    ensure_dir(STATE_DIR)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        with open(MAINTENANCE_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {level} {message}\n")
    except OSError:
        pass


# ─── Project classification ────────────────────────────────────────────────

def classify_project(project_dir: Path) -> str:
    """Classify a project into A/B/C/D/E categories.

    A: Core infrastructure
    B: Real deliverable projects
    C: Duplicate or old versions
    D: Pure session noise
    E: Uncertain
    """
    import re
    name = project_dir.name.lower()

    # Detect timestamp session directories
    ts_pattern = re.compile(r'^\d{8}-\d{6}-[a-z]+-[a-f0-9]{6}$')
    is_timestamp_dir = bool(ts_pattern.match(project_dir.name))

    # A: Core infrastructure (NOT timestamp dirs)
    infra_keywords = ['claude-switcher', 'codex-claude',
                       'ai-project-manager', 'ai-project-workspace', 'cc-launcher',
                       'global-rules', 'shell-integration']
    # Only classify as A if the name IS the project (not a session copy)
    if not is_timestamp_dir:
        if any(kw in name for kw in infra_keywords):
            has_config = ((project_dir / "CLAUDE.md").exists() or
                           (project_dir / ".claude").exists())
            has_code = _has_source_content(project_dir)
            if has_config or has_code:
                return "A"

        # Also A if it's a named infrastructure directory with real content
        infra_exact = {'claude-switcher-setup'}
        if name in infra_exact:
            return "A"

    # Check for real deliverables (not just AI skeleton)
    has_source = _has_source_content(project_dir)
    has_docs = _has_bounded_content(
        project_dir, {'.pptx', '.ppt', '.pdf', '.docx', '.odt', '.odp'},
        {'deliverables', 'artifacts', 'output', 'outputs'},
    )
    has_data = _has_bounded_content(
        project_dir, {'.csv', '.json', '.xlsx', '.parquet'},
        {'data', 'reports', 'output', 'outputs'},
    )
    has_media = _has_bounded_content(
        project_dir, {'.jpg', '.jpeg', '.png', '.mp4', '.mp3', '.wav'},
        {'assets', 'deliverables', 'images', 'media', 'output', 'outputs'},
    )
    has_nested_project = _has_nested_project(project_dir)

    # Check if project has ONLY AI session content
    is_session_only = _is_session_only_project(project_dir)

    # For timestamp dirs, check if they have unique source code
    # (not just staging/deployment copies of installed packages)
    if is_timestamp_dir:
        if has_source:
            # Check if the source files are unique or just staging copies
            source_files = (list(project_dir.glob("*.py")) +
                          list(project_dir.glob("*.sh")) +
                          list(project_dir.glob("repair-staging/**/*.py")))
            # If sources are only in staging/backup dirs, it's a session copy
            non_staging_sources = [f for f in source_files
                                  if 'staging' not in str(f) and 'backup' not in str(f)
                                  and '.ai/' not in str(f)]
            if non_staging_sources:
                return "B"  # Has unique source files
            # Staging sources only — likely deployment copies
            if is_session_only:
                return "D"
            return "E"

        if has_docs or has_data or has_media or has_nested_project:
            return "B"  # Has real user deliverables

        if is_session_only:
            return "D"

        return "E"

    # Non-timestamp dirs
    if has_source or has_docs or has_data or has_media or has_nested_project:
        return "B"

    if is_session_only:
        return "D"

    # Empty or near-empty
    try:
        contents = list(project_dir.iterdir())
        if not contents:
            return "D"
        if len(contents) == 1 and contents[0].name == '.git':
            return "D"
    except OSError:
        pass

    return "E"


def _has_source_content(project_dir: Path) -> bool:
    """Detect source without recursively traversing caches or vendored trees."""
    source_suffixes = {'.py', '.sh', '.js', '.ts', '.rs', '.go', '.java', '.kt'}
    try:
        if any(p.is_file() and p.suffix.lower() in source_suffixes
               for p in project_dir.iterdir()):
            return True
    except OSError:
        return False

    source_dirs = {
        'app', 'backend', 'bin', 'frontend', 'mediaflow', 'package',
        'packages', 'scripts', 'src',
    }
    return any((project_dir / name).is_dir() for name in source_dirs)


def _has_bounded_content(project_dir: Path, suffixes: set[str],
                         content_dirs: set[str]) -> bool:
    """Find deliverables at the root or one level inside known content dirs."""
    try:
        if any(p.is_file() and p.suffix.lower() in suffixes
               for p in project_dir.iterdir()):
            return True
    except OSError:
        return False

    for name in content_dirs:
        directory = project_dir / name
        if not directory.is_dir():
            continue
        try:
            if any(p.is_file() and p.suffix.lower() in suffixes
                   for p in directory.iterdir()):
                return True
        except OSError:
            continue
    return False


def _has_nested_project(project_dir: Path) -> bool:
    """Recognize a single real project nested below a generic container."""
    ignored = {'.ai', '.ai-session', '.git', '.venv', 'node_modules', 'venv'}
    try:
        children = [p for p in project_dir.iterdir()
                    if p.is_dir() and p.name not in ignored
                    and not p.name.startswith('.')]
    except OSError:
        return False

    for child in children:
        if not (child / 'README.md').is_file():
            continue
        if (_has_source_content(child)
                or any((child / marker).exists()
                       for marker in ('pyproject.toml', 'package.json', 'Cargo.toml',
                                      'go.mod', 'Makefile', 'theme'))):
            return True
    return False


def _is_session_only_project(project_dir: Path) -> bool:
    """Check if project only contains AI session records and work artifacts."""
    total_files = 0
    session_files = 0
    skeleton_names = {'CLAUDE.md', 'AGENTS.md', 'README.md', '.gitignore',
                       'project.json', 'meta.json', 'conversation.md',
                       'transcript.md', 'events.jsonl', 'heartbeat',
                       'transcript.redacted.jsonl', 'transcript.sha256',
                       'transcript.raw.jsonl', 'finalization.json',
                       'finalize.lock', 'git-index.lock'}

    # Directories that indicate session-only work artifacts (not user deliverables)
    session_artifact_dirs = {'backups', 'repair-staging', 'staging', 'trash-isolated',
                              'docs', '.ai-session', '.ai', '__pycache__'}

    for f in project_dir.rglob("*"):
        if not f.is_file():
            continue
        if '.git/' in str(f):
            continue

        total_files += 1
        rel = str(f.relative_to(project_dir))

        # Check if file is in a session artifact directory
        in_session_dir = any(
            rel.startswith(d + '/') or rel == d
            for d in session_artifact_dirs
        )

        if in_session_dir or f.name in skeleton_names:
            session_files += 1

    if total_files == 0:
        return True

    # More than 75% session-related files
    if total_files > 3 and session_files / total_files > 0.75:
        return True

    # Check for skeleton-only project (no real user content outside skeleton/backups/sessions)
    non_session_count = 0
    for f in project_dir.rglob("*"):
        if not f.is_file():
            continue
        if '.git/' in str(f):
            continue
        rel = str(f.relative_to(project_dir))
        in_session_dir = any(
            rel.startswith(d + '/') or rel == d
            for d in session_artifact_dirs
        )
        if not in_session_dir and f.name not in skeleton_names:
            non_session_count += 1

    # Very few non-session files suggests session-only
    if non_session_count <= 3:
        return True

    return False


# ─── Duplicate detection ───────────────────────────────────────────────────

def find_duplicates(all_projects: list[dict]) -> list[dict]:
    """Find duplicate/similar projects across ~/Projects."""
    duplicates = []

    for i, p1 in enumerate(all_projects):
        path1 = Path(p1["path"])
        for j, p2 in enumerate(all_projects):
            if j <= i:
                continue
            path2 = Path(p2["path"])

            score = _similarity_score(path1, path2)
            if score > 0.7:
                duplicates.append({
                    "project1": str(path1),
                    "project2": str(path2),
                    "similarity": score,
                    "reason": _similarity_reason(path1, path2),
                })

    return duplicates


def _similarity_score(path1: Path, path2: Path) -> float:
    """Calculate similarity score between two projects (0.0 to 1.0)."""
    score = 0.0
    reasons = 0

    # Same README content
    readme1 = path1 / "README.md"
    readme2 = path2 / "README.md"
    if readme1.exists() and readme2.exists():
        try:
            h1 = compute_sha256(readme1)
            h2 = compute_sha256(readme2)
            if h1 == h2 and h1:
                score += 1.0
                reasons += 1
        except Exception:
            pass

    # Same CLAUDE.md content
    claude1 = path1 / "CLAUDE.md"
    claude2 = path2 / "CLAUDE.md"
    if claude1.exists() and claude2.exists():
        try:
            h1 = compute_sha256(claude1)
            h2 = compute_sha256(claude2)
            if h1 == h2 and h1:
                score += 0.3
                reasons += 1
        except Exception:
            pass

    # Same .ai/project.json tool/session pattern
    pj1 = read_json(path1 / ".ai-session" / "project.json") or read_json(path1 / ".ai" / "project.json")
    pj2 = read_json(path2 / ".ai-session" / "project.json") or read_json(path2 / ".ai" / "project.json")
    if pj1 and pj2:
        if pj1.get("tool") == pj2.get("tool"):
            score += 0.2
            reasons += 1

    # Git remote match
    try:
        r1 = subprocess.run(["git", "-C", str(path1), "remote", "get-url", "origin"],
                          capture_output=True, text=True, timeout=5)
        r2 = subprocess.run(["git", "-C", str(path2), "remote", "get-url", "origin"],
                          capture_output=True, text=True, timeout=5)
        if r1.returncode == 0 and r2.returncode == 0 and r1.stdout.strip() == r2.stdout.strip():
            score += 0.8
            reasons += 1
    except Exception:
        pass

    if reasons == 0:
        return 0.0
    return score / max(reasons, 1)


def _similarity_reason(path1: Path, path2: Path) -> str:
    """Explain why two projects are similar."""
    reasons = []
    if compute_sha256(path1 / "README.md") == compute_sha256(path2 / "README.md"):
        reasons.append("相同的 README.md")
    if compute_sha256(path1 / "CLAUDE.md") == compute_sha256(path2 / "CLAUDE.md"):
        reasons.append("相同的 CLAUDE.md")
    if (path1 / ".ai-session").exists() and (path2 / ".ai-session").exists():
        reasons.append("都是 AI 会话项目")
    return "; ".join(reasons) if reasons else "相似文件结构"


# ─── Quarantine system ─────────────────────────────────────────────────────

def quarantine_project(project_dir: Path, reason: str,
                        dry_run: bool = False) -> dict:
    """Move a project to quarantine."""
    project_dir = Path(project_dir).resolve()
    name = project_dir.name
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    target_dir = QUARANTINE_DIR / date_str / name

    result = {
        "original_path": str(project_dir),
        "quarantine_path": str(target_dir),
        "reason": reason,
        "success": False,
        "dry_run": dry_run,
    }

    # Gather metadata
    file_count = sum(1 for _ in project_dir.rglob("*") if _.is_file())
    total_size = sum(_.stat().st_size for _ in project_dir.rglob("*") if _.is_file())

    result["file_count"] = file_count
    result["total_size"] = total_size

    # Git info
    if (project_dir / ".git").exists():
        try:
            git_result = subprocess.run(
                ["git", "-C", str(project_dir), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"}
            )
            if git_result.returncode == 0:
                result["git_head"] = git_result.stdout.strip()
        except Exception:
            pass

    # SHA256 manifest
    if not dry_run:
        manifest = {}
        for f in sorted(project_dir.rglob("*")):
            if f.is_file() and '.git/' not in str(f):
                try:
                    manifest[str(f.relative_to(project_dir))] = compute_sha256(f)
                except Exception:
                    pass
        result["sha256_manifest"] = manifest

    if dry_run:
        result["success"] = True
        return result

    # Execute move
    ensure_dir(target_dir.parent)
    try:
        shutil.move(str(project_dir), str(target_dir))
        result["success"] = True

        # Record to quarantine index
        _record_quarantine(result)

        log_maintenance(f"Quarantined: {project_dir} -> {target_dir} ({reason})")
    except OSError as e:
        result["error"] = str(e)
        log_maintenance(f"Quarantine FAILED: {project_dir} — {e}", "ERROR")

    return result


def _record_quarantine(result: dict) -> None:
    """Record a quarantine entry to the index."""
    ensure_dir(STATE_DIR)
    entry = {
        "timestamp": timestamp_iso(),
        "original_path": result["original_path"],
        "quarantine_path": result["quarantine_path"],
        "reason": result["reason"],
        "file_count": result.get("file_count", 0),
        "total_size": result.get("total_size", 0),
        "git_head": result.get("git_head", ""),
        "sha256_manifest": result.get("sha256_manifest", {}),
        "restore_command": f"mv '{result['quarantine_path']}' '{result['original_path']}'",
    }
    try:
        with open(QUARANTINE_INDEX, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except OSError:
        pass


def purge_quarantine(dry_run: bool = False) -> list[dict]:
    """Purge items past retention period from quarantine."""
    config = load_config()
    retention_days = int(config.get("QUARANTINE_DAYS", 14))
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    purged = []
    if not QUARANTINE_DIR.exists():
        return purged

    for date_dir in sorted(QUARANTINE_DIR.iterdir()):
        if not date_dir.is_dir():
            continue
        try:
            dir_date = datetime.strptime(date_dir.name, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        if dir_date < cutoff:
            for project_dir in date_dir.iterdir():
                if project_dir.is_dir():
                    item = {
                        "path": str(project_dir),
                        "date": date_dir.name,
                        "action": "would_delete" if dry_run else "deleted",
                    }
                    if not dry_run:
                        try:
                            # Safety: only delete within _trash-review
                            resolved = project_dir.resolve()
                            if str(resolved).startswith(str(QUARANTINE_DIR.resolve())):
                                shutil.rmtree(str(resolved))
                                item["action"] = "deleted"
                            else:
                                item["action"] = "skipped_outside_quarantine"
                        except OSError as e:
                            item["action"] = f"error: {e}"
                    purged.append(item)
                    log_maintenance(f"Purged: {project_dir}")

            # Remove empty date dir
            if not dry_run:
                try:
                    remaining = list(date_dir.iterdir())
                    if not remaining:
                        date_dir.rmdir()
                except OSError:
                    pass

    return purged


def restore_from_quarantine(quarantine_path: str) -> dict:
    """Restore a project from quarantine."""
    qpath = Path(quarantine_path)
    if not qpath.exists():
        return {"success": False, "error": "Quarantine path not found"}

    # Find original path from index
    original_path = None
    if QUARANTINE_INDEX.exists():
        try:
            with open(QUARANTINE_INDEX, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get("quarantine_path") == str(qpath):
                        original_path = entry.get("original_path")
                        break
        except (OSError, json.JSONDecodeError):
            pass

    if not original_path:
        return {"success": False, "error": "Original path not found in quarantine index"}

    orig = Path(original_path)
    if orig.exists():
        return {"success": False, "error": f"Original path already exists: {orig}"}

    try:
        shutil.move(str(qpath), str(orig))
        log_maintenance(f"Restored from quarantine: {qpath} -> {orig}")
        return {"success": True, "original_path": str(orig)}
    except OSError as e:
        return {"success": False, "error": str(e)}


# ─── Quick maintenance ─────────────────────────────────────────────────────

def quick_maintenance(dry_run: bool = False) -> dict:
    """Execute weekly quick maintenance."""
    report = {
        "timestamp": timestamp_iso(),
        "mode": "quick",
        "dry_run": dry_run,
        "cleaned_recent_projects": 0,
        "removed_stale_entries": [],
        "new_timestamp_dirs": [],
        "empty_dirs": [],
        "test_residuals": [],
        "duplicate_logs": [],
        "name_suggestions": [],
        "active_sessions": [],
        "managed_sync": [],
    }

    # 1. Clean recent projects (remove non-existent)
    recent_file = Path.home() / ".local" / "state" / "cc-launcher" / "recent-projects"
    if recent_file.exists():
        try:
            lines = recent_file.read_text(encoding='utf-8').strip().split('\n')
            valid = [l for l in lines if l.strip() and Path(l.strip()).exists()]
            removed = len(lines) - len(valid)
            report["cleaned_recent_projects"] = removed
            if not dry_run and removed > 0:
                recent_file.write_text('\n'.join(valid) + '\n', encoding='utf-8')
        except OSError:
            pass

    # 2. Scan for new timestamp directories
    import re
    ts_pattern = re.compile(r'^\d{8}-\d{6}-[a-z]+-[a-f0-9]{6}$')
    for entry in sorted(PROJECTS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if ts_pattern.match(entry.name):
            report["new_timestamp_dirs"].append(str(entry))

    # 3. Check for empty dirs
    for entry in sorted(PROJECTS_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith('_') or entry.name.startswith('.'):
            continue
        try:
            contents = list(entry.iterdir())
            if not contents:
                report["empty_dirs"].append(str(entry))
            # Just .git and nothing else
            elif len(contents) == 1 and contents[0].name == '.git':
                report["empty_dirs"].append(str(entry))
        except OSError:
            pass

    # 4. Update project.json with naming for B-category placeholder projects
    for entry in sorted(PROJECTS_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith('_'):
            continue
        if is_placeholder_name(entry.name):
            cat = classify_project(entry)
            # Only suggest renames for B-category projects (real deliverables)
            if cat == "B":
                suggestion = suggest_rename(entry)
                if suggestion:
                    report["name_suggestions"].append({
                        "path": str(entry),
                        "current_name": entry.name,
                        "suggested_name": suggestion,
                    })
                    if not dry_run:
                        analysis = analyze_project(entry)
                        update_project_json(entry, analysis)

    # 5. Check for test residuals
    test_patterns = ['test-*.sh', '*_test.py', 'test_*.py', '*.tmp', '*~', '*.bak']
    for entry in sorted(PROJECTS_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith('_'):
            continue
        for pattern in test_patterns:
            for f in entry.glob(pattern):
                report["test_residuals"].append(str(f))

    # 6. Safely fast-forward managed publishing/integration repositories.
    config = load_config()
    if config.get("AUTO_SYNC_MANAGED", "true").lower() == "true":
        report["managed_sync"] = sync_managed_projects(dry_run=dry_run)

    # 7. Generate projects index
    if not dry_run:
        generate_projects_index()

    log_maintenance(f"Quick maintenance completed. {len(report['name_suggestions'])} name suggestions.")
    return report


# ─── Deep maintenance ──────────────────────────────────────────────────────

def deep_maintenance(dry_run: bool = False) -> dict:
    """Execute monthly deep maintenance."""
    report = {
        "timestamp": timestamp_iso(),
        "mode": "deep",
        "dry_run": dry_run,
        "classification": {},
        "duplicates": [],
        "rename_candidates": [],
        "merge_plans": [],
        "quarantine_candidates": [],
        "protected": [],
    }

    config = load_config()
    protected = load_protected()

    # 1. Classify all projects
    all_projects = []
    for entry in sorted(PROJECTS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith('_'):
            continue

        category = classify_project(entry)
        is_prot = is_protected(entry, protected)
        analysis = analyze_project(entry)

        proj_info = {
            "name": entry.name,
            "path": str(entry),
            "category": category,
            "is_protected": is_prot,
            "is_placeholder": is_placeholder_name(entry.name),
            "display_name": analysis.get("display_name", entry.name),
            "summary": analysis.get("summary", ""),
            "project_type": analysis.get("project_type", "unknown"),
            "suggested_name": analysis.get("suggested_directory_name", ""),
        }
        all_projects.append(proj_info)
        report["classification"][str(entry)] = category

        if is_prot:
            report["protected"].append(str(entry))

    # 2. Find duplicates
    report["duplicates"] = find_duplicates(all_projects)

    # 3. Generate rename candidates (only B-category placeholder names)
    if config.get("AUTO_RENAME_PLACEHOLDERS", "true").lower() == "true":
        for proj in all_projects:
            # Only rename B-category projects with placeholder names
            if (proj["is_placeholder"] and proj["suggested_name"]
                    and proj["category"] == "B"
                    and proj["suggested_name"] != proj["name"]):
                report["rename_candidates"].append({
                    "path": proj["path"],
                    "old_name": proj["name"],
                    "new_name": proj["suggested_name"],
                    "reason": "占位名称，已生成合理名称建议",
                })
                if not dry_run and not proj["is_protected"]:
                    result = safe_rename_project(
                        Path(proj["path"]), proj["suggested_name"],
                        dry_run=dry_run
                    )
                    if result["success"]:
                        proj["path"] = result["new_path"]
                        proj["name"] = proj["suggested_name"]

    # 4. Generate merge plans for duplicates
    if config.get("AUTO_MERGE_DUPLICATES", "true").lower() == "true":
        for dup in report["duplicates"]:
            plan = _generate_merge_plan(Path(dup["project1"]), Path(dup["project2"]))
            if plan:
                report["merge_plans"].append(plan)

    # 5. Identify quarantine candidates (category D, not protected, auto-quarantine enabled)
    if config.get("AUTO_QUARANTINE_LOW_VALUE", "true").lower() == "true":
        for proj in all_projects:
            if proj["category"] == "D" and not proj["is_protected"]:
                entry = Path(proj["path"])
                if entry.exists() and entry.parent == PROJECTS_ROOT.resolve():
                    report["quarantine_candidates"].append({
                        "path": str(entry),
                        "reason": "纯 AI 会话记录，无独立交付成果",
                        "name": entry.name,
                    })
                    if not dry_run:
                        quarantine_project(entry,
                            "纯 AI 会话记录，无独立交付成果",
                            dry_run=dry_run)

    # 6. Update all project.json files
    if not dry_run:
        for proj in all_projects:
            entry = Path(proj["path"])
            if entry.exists():
                try:
                    update_project_json(entry)
                except Exception:
                    pass

    # 7. Generate index
    if not dry_run:
        generate_projects_index()

    log_maintenance(f"Deep maintenance completed. "
                    f"Categories: {Counter(report['classification'].values())}")
    return report


def _generate_merge_plan(path1: Path, path2: Path) -> Optional[dict]:
    """Generate a merge plan for two similar projects."""
    # Determine which is primary (newer, more complete)
    size1 = sum(_.stat().st_size for _ in path1.rglob("*") if _.is_file())
    size2 = sum(_.stat().st_size for _ in path2.rglob("*") if _.is_file())

    primary = path1 if size1 >= size2 else path2
    secondary = path2 if size1 >= size2 else path1

    # Find unique files in secondary
    unique_files = []
    for f in secondary.rglob("*"):
        if f.is_file() and '.git/' not in str(f):
            rel = f.relative_to(secondary)
            corresponding = primary / rel
            if not corresponding.exists():
                unique_files.append(str(rel))

    if not unique_files:
        return None

    return {
        "primary": str(primary),
        "secondary": str(secondary),
        "unique_files_in_secondary": unique_files[:20],  # cap
        "action": "merge_then_quarantine_secondary",
    }


# ─── Projects index ────────────────────────────────────────────────────────

def generate_projects_index() -> dict:
    """Generate PROJECTS_INDEX.md and projects-index.json."""
    protected = load_protected()
    projects = []

    if not PROJECTS_ROOT.exists():
        return {"projects": [], "error": "Projects root not found"}

    for entry in sorted(PROJECTS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith('_'):
            continue
        if entry.name.startswith('.'):
            continue

        analysis = analyze_project(entry)
        category = classify_project(entry)
        is_prot = is_protected(entry, protected)
        has_git = (entry / ".git").exists()

        # Get last git commit date
        last_updated = ""
        if has_git:
            try:
                result = subprocess.run(
                    ["git", "-C", str(entry), "log", "-1", "--format=%aI"],
                    capture_output=True, text=True, timeout=10,
                    env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"}
                )
                if result.returncode == 0:
                    last_updated = result.stdout.strip()
            except Exception:
                pass

        if not last_updated:
            # Use filesystem mtime
            try:
                last_updated = datetime.fromtimestamp(
                    entry.stat().st_mtime, tz=timezone.utc).isoformat()
            except OSError:
                pass

        proj = {
            "name": entry.name,
            "path": str(entry),
            "display_name": analysis.get("display_name", entry.name),
            "project_type": analysis.get("project_type", "unknown"),
            "category": category,
            "status": analysis.get("status", "unknown"),
            "summary": analysis.get("summary", ""),
            "git": has_git,
            "last_updated": last_updated,
            "is_protected": is_prot,
            "protection_reason": _protection_reason(entry.name, is_prot),
            "is_placeholder": is_placeholder_name(entry.name),
            "has_rename_suggestion": bool(suggest_rename(entry)),
            "suggested_name": suggest_rename(entry) or "",
            "is_session_only": _is_session_only_project(entry),
            "suggested_action": _suggest_action(category, is_prot, is_placeholder_name(entry.name)),
            "effective_action": _effective_action(category, is_prot),
            "anomaly": _detect_anomaly(category, is_prot),
        }
        projects.append(proj)

    # Write JSON index
    ensure_dir(STATE_DIR)
    index_data = {
        "generated": timestamp_iso(),
        "project_count": len(projects),
        "categories": Counter(p["category"] for p in projects),
        "projects": projects,
    }
    try:
        atomic_write_json(PROJECTS_INDEX_JSON, index_data)
    except OSError:
        pass  # Read-only filesystem — index file will be generated on next writable run

    # Write Markdown index
    _write_markdown_index(projects)

    return index_data


def _suggest_action(category: str, is_protected: bool, is_placeholder: bool) -> str:
    """Suggest an action for a project. Protection does NOT override category."""
    if is_protected and category == "D":
        return "受保护的低价值项目 — 需人工审核"
    if is_protected and category == "A":
        return "保留（核心基础设施 + 受保护）"
    if is_protected and category == "B":
        return "保留（真实成果 + 受保护）"
    if is_protected:
        return "保留（受保护）"
    if category == "A":
        return "保留（核心基础设施）"
    if category == "B":
        if is_placeholder:
            return "自动重命名"
        return "保留并维护"
    if category == "C":
        return "合并唯一内容后隔离"
    if category == "D":
        return "审核后隔离"
    return "人工审核"


def _effective_action(category: str, is_protected: bool) -> str:
    """Determine what action is actually allowed given protection status."""
    if is_protected:
        return "manual-review"  # Can't auto-modify protected projects
    if category == "A":
        return "keep"
    if category == "B":
        return "maintain-or-rename"
    if category == "C":
        return "merge-then-quarantine"
    if category == "D":
        return "quarantine"
    return "manual-review"


def _detect_anomaly(category: str, is_protected: bool) -> str:
    """Detect classification anomalies (e.g., protected D-class)."""
    anomalies = []
    if is_protected and category == "D":
        anomalies.append("protected-low-value: 受保护但内容为纯会话记录")
    if is_protected and category in ("C", "E"):
        anomalies.append(f"protected-uncertain: 受保护但分类为 {category}")
    if not is_protected and category == "A":
        anomalies.append("unprotected-infrastructure: 核心基础设施未受保护")
    return "; ".join(anomalies) if anomalies else ""


def _protection_reason(name: str, is_protected: bool) -> str:
    """Explain why a project is protected."""
    if not is_protected:
        return ""
    infra = {
        'codex-claude',
        'claude-switcher-setup',
        'ai-project-workspace-manager',
        'ai-workflow-foundry',
        'ai-workspace-manager',
    }
    user_projects = {
        'meeting-media-auto',
        'meeting-media-desktop',
        'phone-control',
        'PhotoTransform',
        'Hunan-University-Motivation-PPT',
        'confera-media-skills',
        'feedback-analysis-system',
        'print-ready-nameplate-generator',
        'ryanshi1103',
    }
    if name in infra:
        return "核心基础设施"
    if name in user_projects:
        return "用户真实项目"
    if name == '13':
        return "当前工作区（遗留保护，建议审核后移除）"
    return "保护列表中"


def _write_markdown_index(projects: list[dict]) -> None:
    """Write PROJECTS_INDEX.md."""
    lines = [
        "# ~/Projects 项目索引",
        "",
        f"生成时间: {timestamp_iso()}",
        f"项目总数: {len(projects)}",
        "",
        "## 分类统计",
        "",
    ]

    cats = Counter(p["category"] for p in projects)
    cat_names = {
        "A": "核心基础设施",
        "B": "有真实成果的项目",
        "C": "重复/旧版本",
        "D": "纯会话记录",
        "E": "待审核",
    }
    for cat in ["A", "B", "C", "D", "E"]:
        count = cats.get(cat, 0)
        lines.append(f"- **{cat}**: {cat_names.get(cat, cat)}: {count} 个项目")

    lines.extend([
        "",
        "## 项目列表",
        "",
    ])

    for p in projects:
        cat = p.get("category", "?")
        prot = " 🔒" if p.get("is_protected") else ""
        placeholder = " ⚠️占位" if p.get("is_placeholder") else ""
        lines.append(f"### {p['name']}{prot}{placeholder}")
        lines.append(f"- **路径**: `{p['path']}`")
        lines.append(f"- **显示名称**: {p.get('display_name', 'N/A')}")
        lines.append(f"- **类型**: {p.get('project_type', 'N/A')}")
        lines.append(f"- **分类**: {cat} — {cat_names.get(cat, '未知')}")
        lines.append(f"- **状态**: {p.get('status', 'N/A')}")
        lines.append(f"- **Git**: {'是' if p.get('git') else '否'}")
        lines.append(f"- **最近更新**: {p.get('last_updated', 'N/A')}")
        if p.get('summary'):
            lines.append(f"- **摘要**: {p['summary']}")
        if p.get('suggested_name'):
            lines.append(f"- **建议名称**: `{p['suggested_name']}`")
        lines.append(f"- **建议动作**: {p.get('suggested_action', 'N/A')}")
        lines.append("")

    try:
        PROJECTS_INDEX_MD.write_text('\n'.join(lines), encoding='utf-8')
    except OSError:
        # Try writing to state dir as fallback
        try:
            (STATE_DIR / "PROJECTS_INDEX.md").write_text('\n'.join(lines), encoding='utf-8')
        except OSError:
            pass


# ─── Main entry for cc-projects-maintain ───────────────────────────────────

def run_maintenance(mode: str, dry_run: bool = False) -> dict:
    """Run maintenance in the specified mode. Returns report dict."""
    ensure_dir(STATE_DIR)
    ensure_dir(CONFIG_DIR)

    # Ensure config files exist
    if not MAINTENANCE_CONF.exists():
        _write_default_config()
    if not PROTECTED_LIST.exists():
        _write_default_protected_list()

    if mode == "quick":
        return quick_maintenance(dry_run=dry_run)
    elif mode == "deep":
        return deep_maintenance(dry_run=dry_run)
    elif mode == "report":
        return generate_projects_index()
    elif mode == "sync-managed":
        return {"managed_sync": sync_managed_projects(dry_run=dry_run)}
    elif mode == "purge-quarantine":
        config = load_config()
        if config.get("AUTO_PURGE_AFTER_RETENTION", "true").lower() != "true" and not dry_run:
            return {"error": "AUTO_PURGE_AFTER_RETENTION is disabled"}
        return {"purged": purge_quarantine(dry_run=dry_run)}
    else:
        return {"error": f"Unknown mode: {mode}"}


def _write_default_config() -> None:
    """Write default maintenance.conf."""
    ensure_dir(CONFIG_DIR)
    content = """# cc-projects maintenance configuration
# Edit this file to customize behavior.

PROJECTS_ROOT="/home/ryan/Projects"
QUARANTINE_DAYS=14
AUTO_RENAME_PLACEHOLDERS=true
AUTO_MERGE_DUPLICATES=true
AUTO_QUARANTINE_LOW_VALUE=true
AUTO_PURGE_AFTER_RETENTION=true
AUTO_SYNC_MANAGED=true
DRY_RUN=false
"""
    try:
        MAINTENANCE_CONF.write_text(content, encoding='utf-8')
    except OSError:
        pass


def _write_default_protected_list() -> None:
    """Write initial protected projects list based on current Projects."""
    ensure_dir(CONFIG_DIR)
    protected = [
        "# Protected projects — one per line (path or project name)",
        "# Projects listed here will NOT be auto-deleted, quarantined, or merged.",
        "# Generated: " + timestamp_iso(),
        "",
        "# Core infrastructure",
    ]

    if PROJECTS_ROOT.exists():
        for entry in sorted(PROJECTS_ROOT.iterdir()):
            if not entry.is_dir():
                continue
            name = entry.name
            # Auto-protect core infrastructure
            if any(kw in name.lower() for kw in [
                'claude-switcher', 'codex-claude',
                'ai-workflow-foundry', 'ai-workspace-manager',
                'meeting-media-auto', 'phone-control',
                'hunan-university', 'confera-media-skills',
                'feedback-analysis-system', 'print-ready-nameplate-generator',
            ]):
                protected.append(name)

    try:
        PROTECTED_LIST.write_text('\n'.join(protected) + '\n', encoding='utf-8')
    except OSError:
        pass


# Need re for classify_project
import re
