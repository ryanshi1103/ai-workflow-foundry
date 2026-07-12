#!/usr/bin/env python3
"""Auto-detect project name based on actual content.

Analyzes a project directory and generates:
  - display_name (human-readable)
  - directory_name (filesystem-safe)
  - summary (one-line description)
  - project_type (category)
  - suggested_directory_name
  - naming_reason

Sources checked in priority order:
  1. Project deliverables (executables, scripts, build artifacts)
  2. README.md
  3. .ai/PROJECT_STATE.md / .ai-session/project.json
  4. Source code function/class names
  5. Recent meaningful git commits
  6. Document and deliverable files
  7. Recent session summaries
"""

import re
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from typing import Optional

from .utils import read_json, PROJECTS_ROOT

# ─── Placeholder name patterns ────────────────────────────────────────────

PLACEHOLDER_PATTERNS = [
    re.compile(r'^\d+$'),                          # pure numbers: 11, 13
    re.compile(r'^\d{8}-\d{6}-[a-z]+-[a-f0-9]{6}$'),  # timestamp dirs
    re.compile(r'^test$', re.IGNORECASE),
    re.compile(r'^tmp$', re.IGNORECASE),
    re.compile(r'^untitled$', re.IGNORECASE),
    re.compile(r'^new-project$', re.IGNORECASE),
    re.compile(r'^claude-[a-f0-9]{4,}$', re.IGNORECASE),
    re.compile(r'^codex-[a-f0-9]{4,}$', re.IGNORECASE),
    re.compile(r'^session-', re.IGNORECASE),
    re.compile(r'^temp-', re.IGNORECASE),
    re.compile(r'^scratch', re.IGNORECASE),
]


def is_placeholder_name(name: str) -> bool:
    """Check if a directory name is clearly a placeholder."""
    for pat in PLACEHOLDER_PATTERNS:
        if pat.match(name):
            return True
    return False


def is_meaningful_name(name: str) -> bool:
    """Check if a directory name appears to have semantic meaning."""
    if is_placeholder_name(name):
        return False
    # Has at least 3 chars and contains letters
    if len(name) >= 3 and re.search(r'[a-zA-Z]', name):
        return True
    # Chinese characters
    if re.search(r'[一-鿿]', name):
        return True
    return False


# ─── Content analyzers ────────────────────────────────────────────────────

def _read_file(path: Path, max_lines: int = 50) -> str:
    """Safely read first N lines of a file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return ''.join(lines)
    except (OSError, UnicodeDecodeError):
        return ""


def _get_readme_title(project_dir: Path) -> Optional[str]:
    """Extract title from README.md."""
    readme = project_dir / "README.md"
    if not readme.exists():
        return None
    content = _read_file(readme, 30)
    # Try markdown heading
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if m:
        title = m.group(1).strip()
        # Filter out generic titles
        if title.lower() not in ('new project', 'project', 'readme', '项目目标',
                                  '项目', 'untitled', 'test project', '测试项目'):
            return title
    return None


def _get_project_state_summary(project_dir: Path) -> Optional[str]:
    """Extract project description from PROJECT_STATE.md."""
    for state_file in [project_dir / ".ai" / "PROJECT_STATE.md",
                        project_dir / ".ai-session" / "PROJECT_STATE.md"]:
        if not state_file.exists():
            continue
        content = _read_file(state_file, 60)
        # Look for project description section
        for pattern in [r'##\s*项目(?:描述|概述|简介|目标)[：:]\s*(.+?)(?:\n|$)',
                         r'##\s*Project\s+Description[：:]\s*(.+?)(?:\n|$)',
                         r'##\s*What\s+is\s+this\?[：:]\s*(.+?)(?:\n|$)',
                         r'^#\s+(.+)$']:
            m = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if m:
                return m.group(1).strip()[:200]
    return None


def _get_project_json_info(project_dir: Path) -> dict:
    """Extract info from project.json."""
    for pj in [project_dir / ".ai" / "project.json",
                project_dir / ".ai-session" / "project.json"]:
        data = read_json(pj)
        if data:
            return data
    return {}


def _get_source_code_clues(project_dir: Path) -> list[str]:
    """Extract functional clues from source code."""
    clues = []
    # Look at Python files
    for py_file in list(project_dir.glob("*.py")) + list(project_dir.glob("src/**/*.py"))[:5]:
        content = _read_file(py_file, 100)
        # Module docstring
        m = re.search(r'^"""(.*?)"""', content, re.DOTALL)
        if m:
            doc = m.group(1).strip()
            # Filter out obvious non-descriptions
            if doc and not doc.startswith('#!/') and len(doc) > 5:
                clues.append(doc[:200])
        # Main function/class names
        for match in re.finditer(r'^\s*(?:def|class)\s+(\w+)', content, re.MULTILINE):
            name = match.group(1)
            if not name.startswith('_') and len(name) > 2:
                clues.append(name)

    # Look at shell scripts
    for sh_file in list(project_dir.glob("*.sh"))[:5]:
        content = _read_file(sh_file, 20)
        for line in content.split('\n'):
            line = line.strip()
            # Skip shebang, empty lines, separators, and pure comments without content
            if line.startswith('#!'):
                continue
            if not line or re.match(r'^[=\-]{10,}$', line):
                continue
            if line.startswith('#') and len(line) > 3:
                comment = line[1:].strip()
                # Skip generic headers, separators, and short comments
                if not comment or comment.startswith('---') or re.match(r'^[=\-]{5,}$', comment):
                    continue
                if len(comment) > 5:
                    clues.append(comment[:200])
                    break  # Take first meaningful comment

    return clues[:10]


def _get_git_clues(project_dir: Path) -> list[str]:
    """Extract functional clues from git commit messages."""
    clues = []
    try:
        result = subprocess.run(
            ["git", "-C", str(project_dir), "log", "--oneline", "--no-merges",
             "-n", "10", "--pretty=format:%s"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"}
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                # Clean up commit messages
                cleaned = re.sub(r'^(ai-session|finalize|init|commit)[:\s]*', '', line, flags=re.IGNORECASE)
                cleaned = cleaned.strip()
                if cleaned and len(cleaned) > 10:
                    clues.append(cleaned[:200])
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return clues[:5]


def _get_file_structure_clues(project_dir: Path) -> list[str]:
    """Get clues from prominent file/directory names."""
    clues = []
    significant_names = []

    for entry in sorted(project_dir.iterdir()):
        if entry.name.startswith('.') or entry.name.startswith('_'):
            continue
        if entry.is_dir():
            significant_names.append(entry.name)
        elif entry.suffix in ('.py', '.sh', '.md', '.json', '.toml', '.yaml', '.yml'):
            name = entry.stem
            # Skip skeleton file names
            if name.lower() not in ('readme', 'claude', 'agents', 'gitignore'):
                significant_names.append(name)

    # Filter out common generic names
    generic = {'src', 'app', 'docs', 'test', 'tests', 'lib', 'bin', 'dist',
               'build', 'node_modules', 'venv', 'env', '__pycache__', 'assets',
               'public', 'static', 'data', 'config', 'scripts', 'utils', 'tools',
               'readme', 'claude', 'agents'}
    return [n for n in significant_names if n.lower() not in generic][:10]


def _get_session_clues(project_dir: Path) -> list[str]:
    """Get clues from recent session summaries."""
    clues = []
    sessions_dir = project_dir / ".ai-session" / "sessions"
    if not sessions_dir.exists():
        sessions_dir = project_dir / ".ai" / "sessions"
    if not sessions_dir.exists():
        return clues

    # Find most recent session with content
    for session_dir in sorted(sessions_dir.iterdir(), reverse=True):
        if not session_dir.is_dir():
            continue
        # Check conversation.md or summary
        for fname in ['conversation.md', 'summary.md', 'SUMMARY.md']:
            fpath = session_dir / fname
            if fpath.exists():
                content = _read_file(fpath, 80)
                # Look for task descriptions
                for m in re.finditer(
                    r'(?:任务|目标|project|task|goal|working on|building|creating|fixing|implementing)[：:\s]+(.+?)(?:\n|$)',
                    content, re.IGNORECASE):
                    clues.append(m.group(1).strip()[:200])
        if clues:
            break
    return clues[:3]


# ─── Main analyzer ────────────────────────────────────────────────────────

def analyze_project(project_dir: Path) -> dict:
    """Analyze a project directory and generate naming suggestions.

    Returns a dict suitable for writing to .ai/project.json.
    """
    project_dir = Path(project_dir).resolve()
    name = project_dir.name

    result = {
        "display_name": name,
        "directory_name": name,
        "summary": "",
        "project_type": "unknown",
        "suggested_directory_name": name,
        "naming_reason": "",
        "is_placeholder": is_placeholder_name(name),
        "last_analyzed": datetime.now(timezone.utc).isoformat(),
    }

    # Priority 1: README title (skip generic auto-generated titles)
    readme_title = _get_readme_title(project_dir)
    GENERIC_TITLES = {'new project', 'project', 'readme', 'untitled',
                       'test project', '测试项目', '项目目标'}
    if readme_title and readme_title.lower() not in GENERIC_TITLES:
        result["display_name"] = readme_title
        result["naming_reason"] = f"根据 README.md 标题: {readme_title}"

    # Priority 2: PROJECT_STATE
    state_summary = _get_project_state_summary(project_dir)
    if state_summary:
        result["summary"] = state_summary[:300]
        if not result["naming_reason"]:
            result["display_name"] = state_summary[:80]
            result["naming_reason"] = f"根据 PROJECT_STATE.md: {state_summary[:100]}"

    # Priority 3: project.json
    pj = _get_project_json_info(project_dir)
    if pj:
        tool = pj.get("tool", "")
        status = pj.get("status", "")
        if tool:
            result["project_type"] = _classify_project_type(project_dir, pj)

    # Priority 4: Source code
    src_clues = _get_source_code_clues(project_dir)
    if src_clues and not result["summary"]:
        result["summary"] = src_clues[0][:300]
        if not result["naming_reason"]:
            result["display_name"] = src_clues[0][:80]
            result["naming_reason"] = f"根据源代码: {src_clues[0][:100]}"

    # Priority 5: Git commits
    git_clues = _get_git_clues(project_dir)
    if git_clues and not result["summary"]:
        result["summary"] = git_clues[0][:300]
        if not result["naming_reason"]:
            result["display_name"] = git_clues[0][:80]
            result["naming_reason"] = f"根据 Git 提交: {git_clues[0][:100]}"

    # Priority 6: File structure
    file_clues = _get_file_structure_clues(project_dir)
    if file_clues and not result["summary"]:
        result["summary"] = f"包含: {', '.join(file_clues[:5])}"

    # Priority 7: Session summaries
    session_clues = _get_session_clues(project_dir)
    if session_clues and not result["summary"]:
        result["summary"] = session_clues[0][:300]

    # Check backup manifests for project purpose clues
    backup_manifest = project_dir / ".ai" / "backups"
    if backup_manifest.exists():
        for backup_dir in sorted(backup_manifest.iterdir(), reverse=True):
            manifest = backup_dir / "MANIFEST.txt"
            if manifest.exists():
                try:
                    backed_up_files = manifest.read_text(encoding='utf-8').strip().split('\n')
                    key_files = [f for f in backed_up_files if any(
                        kw in f.lower() for kw in ['cc', 'aiproj', 'claude.md', 'launcher', 'hooks'])]
                    if key_files:
                        result["display_name"] = "AI 项目管理与启动器配置工作区"
                        result["summary"] = f"包含系统备份: {', '.join(Path(f).name for f in key_files[:5])}"
                        result["project_type"] = "developer-tooling"
                        result["naming_reason"] = "根据备份清单识别为 AI 项目管理工作区"
                        break
                except OSError:
                    pass

    # If still no name, use directory clues
    if not result["display_name"] or result["display_name"] == name:
        if file_clues:
            result["display_name"] = _make_display_name_from_clues(file_clues, project_dir)
            result["naming_reason"] = f"根据文件结构自动生成: {', '.join(file_clues[:3])}"

    # Generate directory name AFTER display name is finalized
    result["directory_name"] = _generate_dir_name(result["display_name"], project_dir)
    result["suggested_directory_name"] = result["directory_name"]

    return result


def _classify_project_type(project_dir: Path, pj: dict) -> str:
    """Classify the project type."""
    tool = pj.get("tool", "").lower()

    # Check for infrastructure patterns
    name = project_dir.name.lower()
    if any(kw in name for kw in ['claude', 'codex', 'deepseek', 'ai-project', 'cc-launcher']):
        return "developer-tooling"

    # Check file patterns
    has_py = any(project_dir.glob("*.py")) or (project_dir / "src").exists()
    has_sh = any(project_dir.glob("*.sh"))
    has_web = (project_dir / "package.json").exists() or (project_dir / "index.html").exists()
    has_ppt = any(project_dir.glob("*.pptx")) or any(project_dir.glob("*.ppt"))
    has_docs = (project_dir / "docs").exists()

    if has_ppt:
        return "presentation"
    if has_web:
        return "web-application"
    if has_py and has_sh:
        return "automation-tool"
    if has_py:
        return "python-project"
    if has_sh:
        return "shell-script"
    if has_docs:
        return "documentation"

    return "session-record" if tool else "unknown"


def _generate_dir_name(display_name: str, project_dir: Path) -> str:
    """Generate a filesystem-safe directory name from display name.

    Rules:
    - 2-6 clear words in kebab-case
    - Max 48 chars, truncate at complete word boundary only
    - No truncated half-words like 'scri', 'manag', 'deplo'
    - No version numbers unless version IS the product
    - No timestamps
    - No session IDs
    """
    # Try to keep existing meaningful name
    if is_meaningful_name(project_dir.name):
        return project_dir.name

    name = display_name.lower()

    # Transliterate common Chinese tech terms (compound first, then components)
    TRANSLITERATIONS = [
        ('项目管理器', 'project-manager'),
        ('工作区管理器', 'workspace-manager'),
        ('启动器', 'launcher'),
        ('工作区', 'workspace'),
        ('工作台', 'workbench'),
        ('项目管理', 'project-management'),
        ('项目', 'project'),
        ('管理', 'manager'),
        ('配置', 'config'),
        ('部署', 'deploy'),
        ('维护', 'maintain'),
        ('启动', 'launch'),
        ('工具', 'tool'),
        ('系统', 'system'),
        ('自动', 'auto'),
        ('协作', 'collab'),
        ('环境', 'env'),
        ('规则', 'rules'),
        ('备份', 'backup'),
        ('测试', 'test'),
        ('会议', 'meeting'),
        ('媒体', 'media'),
        ('电话', 'phone'),
        ('控制', 'control'),
        ('论文', 'thesis'),
        ('演示', 'slides'),
        ('整理', 'organize'),
        ('索引', 'index'),
        ('清理', 'cleanup'),
        ('修复', 'repair'),
        ('审计', 'audit'),
    ]
    for cn, en in TRANSLITERATIONS:
        name = name.replace(cn, en)

    # Remove remaining CJK characters
    name = re.sub(r'[一-鿿㐀-䶿豈-﫿]+', '', name)
    # Remove special chars, keep alphanumeric and hyphens
    name = re.sub(r'[^a-z0-9]+', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')

    if len(name) < 3:
        return project_dir.name

    # Truncate at complete word boundary, max 48 chars
    if len(name) > 48:
        # Find last complete hyphen within limit
        trunc = name[:48]
        last_hyphen = trunc.rfind('-')
        if last_hyphen > 12:  # ensure we have meaningful content
            name = trunc[:last_hyphen]
        else:
            name = trunc  # fallback

    # Remove trailing fragments (incomplete words at the end)
    # Check if last segment looks like a truncated English word
    segments = name.split('-')
    if segments:
        last = segments[-1]
        # Common truncated endings to avoid
        TRUNCATED_ENDINGS = {
            'scri', 'scr', 'sc',         # script
            'manag', 'mana', 'man',       # manager/manage
            'deplo', 'depl', 'dep',       # deploy/deployment
            'confi', 'conf', 'con',       # config/configuration
            'proje', 'proj', 'pro',       # project
            'launch', 'laun', 'lau',      # launcher (launch is a real word though)
            'workspa', 'worksp', 'works', # workspace (works is a real word)
            'testin', 'testi',            # testing
            'automate', 'automat',        # automated/automation
            'mainten', 'mainte', 'maint', # maintenance
            'orchestrat', 'orchestra',    # orchestrator
        }
        if last in TRUNCATED_ENDINGS:
            segments.pop()
            name = '-'.join(segments)

    # Remove version-like patterns unless very short
    name = re.sub(r'-v\d+(-\d+)*$', '', name)
    name = re.sub(r'-\d{6,}$', '', name)  # timestamps

    if len(name) < 3:
        return project_dir.name

    return name


def _generate_name_candidates(project_dir: Path, analysis: dict) -> list[dict]:
    """Generate multiple name candidates with confidence scores.

    Each candidate: {name, source, confidence, reason}
    """
    candidates = []

    # Candidate from README
    readme_title = _get_readme_title(project_dir)
    if readme_title and readme_title.lower() not in GENERIC_TITLES:
        dirname = _generate_dir_name(readme_title, project_dir)
        if dirname and dirname != project_dir.name:
            candidates.append({
                "name": _clean_dir_name(dirname),
                "source": "readme",
                "confidence": 0.7,
                "reason": f"README 标题: {readme_title[:80]}"
            })

    # Candidate from source code purpose
    src_clues = _get_source_code_clues(project_dir)
    if src_clues:
        # Try to find the most descriptive clue
        for clue in src_clues:
            if len(clue) > 15 and ' ' in clue:
                dirname = _generate_dir_name(clue, project_dir)
                if dirname and dirname != project_dir.name:
                    candidates.append({
                        "name": _clean_dir_name(dirname),
                        "source": "source-code",
                        "confidence": 0.5,
                        "reason": f"源代码: {clue[:80]}"
                    })
                    break

    # Candidate from git history
    git_clues = _get_git_clues(project_dir)
    meaningful_git = [g for g in git_clues if not g.startswith('ai-session') and len(g) > 20]
    if meaningful_git:
        dirname = _generate_dir_name(meaningful_git[0], project_dir)
        if dirname and dirname != project_dir.name:
            candidates.append({
                "name": _clean_dir_name(dirname),
                "source": "git-history",
                "confidence": 0.4,
                "reason": f"Git 历史: {meaningful_git[0][:80]}"
            })

    # Candidate from deployed components
    deployed_clues = _get_deployed_component_clues(project_dir)
    if deployed_clues:
        name = '-'.join(deployed_clues[:3])
        candidates.append({
            "name": _clean_dir_name(name),
            "source": "deployed-components",
            "confidence": 0.8,
            "reason": f"已部署组件: {', '.join(deployed_clues[:5])}"
        })

    # Candidate from AI project manager context
    pj = _get_project_json_info(project_dir)
    if pj:
        tool = pj.get("tool", "")
        # Projects about ai-project-manager itself
        if any(kw in str(project_dir) for kw in ['ai-project', 'aiproj', 'cc-launcher']):
            candidates.append({
                "name": "ai-project-workspace-manager",
                "source": "context-analysis",
                "confidence": 0.6,
                "reason": "综合分析: AI 项目管理工作区"
            })

    # Deduplicate by name
    seen = set()
    unique = []
    for c in candidates:
        if c["name"] not in seen and c["name"] != project_dir.name:
            seen.add(c["name"])
            unique.append(c)

    return unique


def _clean_dir_name(name: str) -> str:
    """Final cleanup of directory name."""
    # Remove leading/trailing hyphens
    name = name.strip('-')
    # Remove consecutive hyphens
    name = re.sub(r'-+', '-', name)
    # Ensure minimum length
    if len(name) < 3:
        return name
    # Remove common bad patterns
    name = re.sub(r'^-+|-+$', '', name)
    return name


def _get_deployed_component_clues(project_dir: Path) -> list[str]:
    """Detect what real deployed components this project contains."""
    clues = []
    # Check for cc launcher
    for f in project_dir.rglob("cc"):
        if f.is_file() and f.name == 'cc':
            try:
                content = f.read_text(encoding='utf-8', errors='replace')[:200]
                if 'Claude Code Unified Launcher' in content or 'Claude / DeepSeek' in content:
                    clues.append('cc-launcher')
                    break
            except OSError:
                pass

    # Check for AI project manager
    if (project_dir / "ai_project_manager").exists() or \
       list(project_dir.glob("**/ai_project_manager/__init__.py")):
        clues.append('ai-project-manager')

    # Check for maintenance system
    for f in project_dir.rglob("cc-projects-maintain"):
        if f.is_file():
            clues.append('projects-maintainer')
            break

    # Check for systemd units
    systemd_files = list(project_dir.glob("**/cc-projects-*.service"))
    if systemd_files:
        clues.append('systemd-timers')

    return clues


def _make_display_name_from_clues(clues: list[str], project_dir: Path) -> str:
    """Create a display name from file structure clues."""
    if not clues:
        return project_dir.name
    # Filter out obvious non-names (shebangs, pure code symbols, skeleton names)
    SKELETON = {'claude', 'agents', 'readme', 'gitignore'}
    filtered = []
    for c in clues:
        c = c.strip()
        if not c or c.startswith('#!/') or c.startswith('#'):
            continue
        if c.lower() in SKELETON:
            continue
        if len(c) < 3:
            continue
        # Skip if it looks like a code symbol (no spaces, camelCase or snake_case with underscores)
        if ' ' not in c and ('_' in c or (c[0].isupper() and any(ch.islower() for ch in c))):
            continue
        filtered.append(c)

    if filtered:
        return filtered[0][:80]
    if clues:
        return clues[0][:80]
    return project_dir.name


# ─── Project name updater ─────────────────────────────────────────────────

def update_project_json(project_dir: Path, analysis: dict = None) -> dict:
    """Update or create .ai/project.json with naming information.

    Reads existing project.json if any, merges in the analysis results,
    and writes to .ai/project.json.
    """
    project_dir = Path(project_dir).resolve()

    if analysis is None:
        analysis = analyze_project(project_dir)

    # Read existing data
    existing = {}
    for pj_path in [project_dir / ".ai" / "project.json",
                     project_dir / ".ai-session" / "project.json"]:
        data = read_json(pj_path)
        if data:
            existing = data
            break

    # Build merged result with name candidates
    name_candidates = _generate_name_candidates(project_dir, analysis)

    # Select best candidate
    selected_name = ""
    best_confidence = 0.0
    for c in name_candidates:
        if c["confidence"] > best_confidence:
            best_confidence = c["confidence"]
            selected_name = c["name"]

    result = {
        "display_name": analysis.get("display_name", project_dir.name),
        "directory_name": analysis.get("directory_name", project_dir.name),
        "summary": analysis.get("summary", existing.get("summary", "")),
        "project_type": analysis.get("project_type", existing.get("project_type", "unknown")),
        "suggested_directory_name": analysis.get("suggested_directory_name", project_dir.name),
        "naming_reason": analysis.get("naming_reason", ""),
        "is_placeholder": analysis.get("is_placeholder", is_placeholder_name(project_dir.name)),
        "last_analyzed": analysis.get("last_analyzed", datetime.now(timezone.utc).isoformat()),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "name_candidates": name_candidates,
        "selected_name": selected_name,
        "confidence": best_confidence,
        "name_history": existing.get("name_history", []),
    }

    # Preserve important existing fields
    for key in ('tool', 'status', 'session_id', 'project_path_final',
                'git_root', 'start_time', 'end_time', 'cli_path', 'cli_version'):
        if key in existing and key not in result:
            result[key] = existing[key]

    # Ensure .ai/ directory exists
    ai_dir = project_dir / ".ai"
    ai_dir.mkdir(parents=True, exist_ok=True)

    # Write
    from .utils import atomic_write_json
    atomic_write_json(ai_dir / "project.json", result)

    return result


def suggest_rename(project_dir: Path) -> Optional[str]:
    """Return suggested new directory name, or None if rename not needed."""
    analysis = analyze_project(project_dir)
    suggested = analysis.get("suggested_directory_name", "")

    if not suggested or suggested == project_dir.name:
        return None

    if not is_placeholder_name(project_dir.name):
        # For meaningfully-named projects, only suggest if the new name is
        # substantially different AND the old name is clearly wrong
        return None

    if len(suggested) < 2:
        return None

    return suggested


# ─── Safe rename executor ──────────────────────────────────────────────────

def safe_rename_project(project_dir: Path, new_name: str,
                         dry_run: bool = False) -> dict:
    """Safely rename a project directory.

    Checks all safety conditions before renaming.
    Returns {"success": bool, "old_path": str, "new_path": str, "error": str, "dry_run": bool}.
    """
    project_dir = Path(project_dir).resolve()
    old_name = project_dir.name
    new_path = project_dir.parent / new_name

    result = {
        "success": False,
        "old_path": str(project_dir),
        "new_path": str(new_path),
        "old_name": old_name,
        "new_name": new_name,
        "error": "",
        "dry_run": dry_run,
    }

    # Check 1: Must be in ~/Projects first level
    if project_dir.parent != PROJECTS_ROOT.resolve():
        result["error"] = f"Not in {PROJECTS_ROOT} first level"
        return result

    # Check 2: Current name must be placeholder
    if not is_placeholder_name(old_name):
        result["error"] = f"'{old_name}' is not a placeholder name"
        return result

    # Check 3: New name must not conflict
    if new_path.exists():
        result["error"] = f"Target path already exists: {new_path}"
        return result

    # Check 4: No active AI sessions (check for running processes in this dir)
    if not dry_run:
        try:
            # Check if any process has this as cwd
            proc_result = subprocess.run(
                ["pgrep", "-f", f"cd {project_dir}"],
                capture_output=True, timeout=5
            )
            if proc_result.returncode == 0:
                result["error"] = "Active sessions may be using this directory"
                return result
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Check 5: Git status is clean
    if not dry_run and (project_dir / ".git").exists():
        try:
            git_result = subprocess.run(
                ["git", "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"}
            )
            if git_result.returncode != 0:
                result["error"] = f"Git status check failed"
                return result
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    # Execute rename
    if dry_run:
        result["success"] = True
        return result

    try:
        project_dir.rename(new_path)
        result["success"] = True

        # Update project.json
        update_project_json(new_path)

        # Update recent projects
        _update_recent_projects(str(project_dir), str(new_path))

    except OSError as e:
        result["error"] = str(e)

    return result


def _update_recent_projects(old_path: str, new_path: str) -> None:
    """Update recent-projects file after rename."""
    recent_file = Path.home() / ".local" / "state" / "cc-launcher" / "recent-projects"
    if not recent_file.exists():
        return

    try:
        content = recent_file.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        new_lines = []
        for line in lines:
            if line.strip() == old_path:
                new_lines.append(new_path)
            else:
                new_lines.append(line)
        recent_file.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    except OSError:
        pass


# ─── Batch analysis ───────────────────────────────────────────────────────

def analyze_all_projects() -> list[dict]:
    """Analyze all projects in ~/Projects and return results."""
    results = []
    if not PROJECTS_ROOT.exists():
        return results

    for entry in sorted(PROJECTS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith('_'):
            continue
        if entry.name.startswith('.'):
            continue

        analysis = analyze_project(entry)
        analysis["path"] = str(entry)
        results.append(analysis)

    return results
