"""Local Git repository management — init, commit, status."""

import os
import shutil, stat, subprocess, tempfile
from pathlib import Path
from datetime import datetime, timezone

from .utils import file_lock, ensure_dir, timestamp_iso
from .redact import scan_for_secrets


def git_init(project_dir: Path) -> bool:
    """Initialize a local Git repository. No remote is set."""
    try:
        result = subprocess.run(
            ["git", "init"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def git_config_local(project_dir: Path, key: str, value: str) -> bool:
    """Set a local Git config value for the project."""
    try:
        subprocess.run(
            ["git", "config", "--local", key, value],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def ensure_git_identity(project_dir: Path) -> None:
    """Ensure Git user identity is set (global or local fallback)."""
    # Check global
    try:
        name = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        email = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        name = ""
        email = ""

    # If global is set, use local override only if user wants
    if not name:
        git_config_local(project_dir, "user.name", "AI Project Recorder")
    if not email:
        git_config_local(project_dir, "user.email", "ai-project-recorder@localhost")


def git_status(project_dir: Path) -> dict:
    """Get Git status information."""
    status = {
        "is_repo": False,
        "branch": "",
        "changed_files": [],
        "untracked_files": [],
        "staged_files": [],
        "clean": True,
    }

    try:
        # Check if it's a repo
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return status
        status["is_repo"] = True

        # Branch
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=5
        )
        status["branch"] = branch.stdout.strip()

        # Status --porcelain
        porc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=10
        )
        for line in porc.stdout.strip().split("\n"):
            if not line:
                continue
            code = line[:2]
            filename = line[3:].strip()
            if code[0] in "MRC":
                status["staged_files"].append(filename)
            if code[1] in "MD":
                status["changed_files"].append(filename)
            if code[0] == "?" or code == "??":
                status["untracked_files"].append(filename)

        status["clean"] = not (status["changed_files"] or status["staged_files"] or status["untracked_files"])
        return status

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return status


def git_add(project_dir: Path, paths: list[str]) -> bool:
    """Stage specified paths."""
    if not paths:
        return True
    try:
        result = subprocess.run(
            ["git", "add", "--"] + paths,
            cwd=project_dir,
            capture_output=True, text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


MAX_STAGE_FILE_SIZE=10485760
def _stage_result(**k):
 r={"ok":False,"added":[],"skipped":[],"blocked":[],"errors":[],"index_committed":False,"nothing_to_commit":False};r.update(k);return r
def _git_bytes(p,a,env=None,timeout=30):return subprocess.run([b"git",b"-C",os.fsencode(p),*[os.fsencode(x) for x in a]],capture_output=True,timeout=timeout,env=env)
def _decode_paths(b):
 if not b:return []
 if not b.endswith(b"\0"):raise ValueError("non-NUL paths")
 return [os.fsdecode(x) for x in b[:-1].split(b"\0")]
def _skip(x):
 p=Path(x).parts;n=p[-1] if p else x
 return x==".env" or n.startswith(".env.") or tuple(p[:2])==(".ai-session","private") or "secrets" in p or "__pycache__" in p or n.endswith((".pem",".key",".log",".lock",".tmp",".swp","~",".bak",".orig",".pyc"))
def _special(root):
 out=[];todo=[root]
 while todo:
  try:es=list(os.scandir(todo.pop()))
  except OSError:continue
  for e in es:
   rel=os.path.relpath(e.path,root)
   if rel==".git" or rel.startswith(".git"+os.sep):continue
   try:m=e.stat(follow_symlinks=False).st_mode
   except OSError:continue
   if stat.S_ISDIR(m):todo.append(Path(e.path))
   elif not stat.S_ISREG(m) and not stat.S_ISLNK(m):out.append(rel)
 return out
def _index(p):
 r=_git_bytes(p,["rev-parse","--path-format=absolute","--git-path","index"])
 if not r.returncode:return Path(os.fsdecode(r.stdout.rstrip(b"\n"))).resolve(strict=False)
 t=_git_bytes(p,["rev-parse","--show-toplevel"]);g=_git_bytes(p,["rev-parse","--absolute-git-dir"]);i=_git_bytes(p,["rev-parse","--git-path","index"])
 if any(x.returncode for x in(t,g,i)):raise RuntimeError("index resolution")
 t=Path(os.fsdecode(t.stdout.rstrip())).resolve();g=Path(os.fsdecode(g.stdout.rstrip())).resolve();raw=Path(os.fsdecode(i.stdout.rstrip()));out=(raw if raw.is_absolute() else t/raw).resolve(strict=False)
 if out.parent!=g and g not in out.parents:raise RuntimeError("index escape")
 return out
def git_add_all_safe(project_dir:Path,lock_timeout:float=30)->dict:
 root=Path(project_dir).resolve();tmp=None;replaced=False;original_bytes=None;original_mode=None;index_path=None
 try:
  with file_lock(root/".ai-session/locks/git-index.lock",timeout=lock_timeout):
   q=_git_bytes(root,["diff","--cached","--quiet"])
   if q.returncode==1:return _stage_result(blocked=["pre-existing-staged-changes"])
   if q.returncode:return _stage_result(errors=["git-diff-cached-check-failed"])
   ix=_index(root);index_path=ix;m=_git_bytes(root,["ls-files","-m","-d","-z"]);o=_git_bytes(root,["ls-files","--others","--exclude-standard","-z"])
   if m.returncode or o.returncode:return _stage_result(errors=["git-ls-files-failed"])
   candidates=list(dict.fromkeys(_decode_paths(m.stdout)+_decode_paths(o.stdout)+_special(root)))
   if not candidates:return _stage_result(ok=True,nothing_to_commit=True)
   add=[];skip=[];block=[];errors=[]
   for rel in candidates:
    if _skip(rel):skip.append(rel);continue
    p=root/rel
    try:
     parent=p.parent.resolve(strict=False)
     if parent!=root and root not in parent.parents:block.append(f"{rel}:path-escape");continue
     st=p.lstat()
    except FileNotFoundError:
     z=_git_bytes(root,["ls-files","--error-unmatch","--",rel]);(add if not z.returncode else errors).append(rel if not z.returncode else f"{rel}:lstat-failed");continue
    except OSError:errors.append(f"{rel}:lstat-failed");continue
    if stat.S_ISLNK(st.st_mode):block.append(f"{rel}:symlink");continue
    if not stat.S_ISREG(st.st_mode):block.append(f"{rel}:non-regular-file");continue
    try:
     if p.stat().st_size>MAX_STAGE_FILE_SIZE:block.append(f"{rel}:too-large");continue
     b=p.read_bytes()
     if b"\0" in b:block.append(f"{rel}:binary");continue
     if scan_for_secrets(b.decode("utf-8")):block.append(f"{rel}:secret-detected");continue
     add.append(rel)
    except UnicodeDecodeError:block.append(f"{rel}:binary")
    except (OSError,ValueError):errors.append(f"{rel}:content-scan-failed")
   if block or errors:return _stage_result(skipped=skip,blocked=block,errors=errors)
   if not add:return _stage_result(ok=True,skipped=skip,nothing_to_commit=True)
   ix.parent.mkdir(parents=True,exist_ok=True);fd,n=tempfile.mkstemp(prefix=".aiproj-index-",dir=ix.parent);os.close(fd);os.unlink(n);tmp=Path(n)
   if ix.exists():shutil.copy2(ix,tmp)
   else:
    env=os.environ.copy();env["GIT_INDEX_FILE"]=str(tmp)
    if _git_bytes(root,["read-tree","--empty"],env=env).returncode:return _stage_result(skipped=skip,errors=["temp-index-init-failed"])
   env=os.environ.copy();env["GIT_INDEX_FILE"]=str(tmp)
   if _git_bytes(root,["add","--",*add],env=env).returncode:return _stage_result(skipped=skip,errors=["git-add-failed"])
   d=_git_bytes(root,["diff","--cached","--binary"],env=env)
   if d.returncode:return _stage_result(skipped=skip,errors=["cached-diff-scan-failed"])
   try:text=d.stdout.decode("utf-8")
   except UnicodeDecodeError:return _stage_result(skipped=skip,errors=["cached-diff-decode-failed"])
   if scan_for_secrets(text):return _stage_result(skipped=skip,blocked=["cached-diff:secret-detected"])
   with tmp.open("rb") as f:os.fsync(f.fileno())
   original_bytes=ix.read_bytes() if ix.exists() else None;original_mode=stat.S_IMODE(ix.stat().st_mode) if ix.exists() else None
   os.replace(tmp,ix);tmp=None;replaced=True
   if original_mode is not None:os.chmod(ix,original_mode)
   fd=os.open(ix.parent,os.O_RDONLY|os.O_DIRECTORY)
   try:os.fsync(fd)
   finally:os.close(fd)
   return _stage_result(ok=True,added=add,skipped=skip,index_committed=True)
 except TimeoutError:return _stage_result(errors=["git-index-lock-timeout"])
 except (OSError,subprocess.TimeoutExpired,ValueError,RuntimeError) as e:
  if replaced and index_path is not None:
   try:
    if original_bytes is None:index_path.unlink(missing_ok=True)
    else:
     fd,name=tempfile.mkstemp(prefix=".aiproj-restore-",dir=index_path.parent)
     with os.fdopen(fd,"wb") as f:f.write(original_bytes);f.flush()
     if original_mode is not None:os.chmod(name,original_mode)
     os.replace(name,index_path)
   except OSError as restore_error:
    return _stage_result(errors=[f"CRITICAL-index-restore-failed:{type(restore_error).__name__}"])
  return _stage_result(errors=[f"staging-failed:{type(e).__name__}"])
 finally:
  if tmp is not None:
   try:tmp.unlink(missing_ok=True)
   except OSError:tmp=None


def git_commit(project_dir: Path, subject: str, body: str) -> str | None:
    """Create a Git commit. Returns commit hash or None on failure."""
    import tempfile

    if not subject or subject in ("update", "changes", "save", "auto commit", "misc"):
        return None

    full_message = f"{subject}\n\n{body}"

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(full_message)
            tmp_path = tmp.name

        result = subprocess.run(
            ["git", "commit", "-F", tmp_path],
            cwd=project_dir,
            capture_output=True, text=True,
            timeout=60,
        )
        os.unlink(tmp_path)

        if result.returncode != 0:
            return None

        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_dir,
            capture_output=True, text=True,
            timeout=5,
        )
        return hash_result.stdout.strip() if hash_result.returncode == 0 else None

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def build_commit_message(tool: str, title: str, session_id: str,
                         model: str = "", provider: str = "",
                         status: str = "", start_time: str = "",
                         end_time: str = "", goal: str = "",
                         decisions: list[str] | None = None,
                         completed: list[str] | None = None,
                         files_changed: list[str] | None = None,
                         transcript_hash: str = "",
                         redaction: bool = False,
                         summary_mode: str = "",
                         unresolved: str = "") -> tuple[str, str]:
    """Build commit subject and body based on session data."""
    subject = f"ai-session({tool}): {title}"

    body_lines = [
        f"Tool: {tool}",
        f"Model: {model}",
        f"Profile: {provider}",
        f"Session ID: {session_id}",
        f"Status: {status}",
        f"Start: {start_time}",
        f"End: {end_time}",
        f"Goal: {goal}",
    ]

    if decisions:
        body_lines.append("")
        body_lines.append("Key decisions:")
        for d in decisions[:10]:
            body_lines.append(f"  - {d}")

    if completed:
        body_lines.append("")
        body_lines.append("Completed:")
        for c in completed[:15]:
            body_lines.append(f"  - {c}")

    if files_changed:
        body_lines.append("")
        body_lines.append(f"Files changed: {len(files_changed)}")
        for f in files_changed[:30]:
            body_lines.append(f"  - {f}")

    body_lines.append("")
    body_lines.append(f"Transcript SHA-256: {transcript_hash}")
    body_lines.append(f"Redaction: {'applied' if redaction else 'none'}")
    body_lines.append(f"Summary mode: {summary_mode}")
    body_lines.append(f"Unresolved: {unresolved}")

    return subject, "\n".join(body_lines)
