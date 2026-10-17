"""Run untrusted student code with hard limits.

Two backends, chosen automatically (override with SANDBOX_MODE=docker|subprocess):

docker      `docker run --network none --read-only --tmpfs --memory --pids-limit --cap-drop ALL`
            (preferred when the docker CLI exists; per-language images, see DOCKER_IMAGES).
subprocess  Linux-only restricted child process:
              * new session + process group, killed as a group on timeout (infinite loops,
                sleeps, fork bombs),
              * RLIMIT_CPU / RLIMIT_DATA / RLIMIT_NPROC / RLIMIT_FSIZE / RLIMIT_NOFILE / no core dumps,
              * when root: dropped to a throw-away numeric uid (so RLIMIT_NPROC really applies to
                the fork bomb) via setpriv, plus a private network namespace (no network), plus a
                private mount namespace where `/` is remounted read-only and only the work dir
                is writable,
              * when not root: rlimits + process-group kill only. `capabilities()` says exactly
                what is enforced on this host, so the daemon can refuse to run un-isolated code
                if it wants to (require_isolation=True).

Output is captured to files (not pipes) and truncated, so `print` floods cannot exhaust memory.
"""
from __future__ import annotations
import os
import random
try:
    import resource
except ImportError:
    resource = None
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


@dataclass
class Limits:
    wall_s: float = 20.0          # real-time limit
    cpu_s: int = 15               # CPU-seconds limit (RLIMIT_CPU)
    memory_mb: int = 768          # data-segment/heap limit (RLIMIT_DATA / docker --memory)
    max_procs: int = 64           # RLIMIT_NPROC offset / docker --pids-limit
    max_file_mb: int = 32         # largest file the process may write
    max_open_files: int = 512
    max_output_kb: int = 256      # captured stdout/stderr each


@dataclass
class SandboxResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int
    reason: str = ""              # "", "timeout", "signal:SIGKILL", ...
    backend: str = "subprocess"


DOCKER_IMAGES = {
    "python": "python:3.12-slim", "javascript": "node:20-slim", "typescript": "node:20-slim",
    "go": "golang:1.22", "java": "eclipse-temurin:21-jdk", "kotlin": "eclipse-temurin:21-jdk",
    "rust": "rust:1.77", "cpp": "gcc:13", "c": "gcc:13", "c_sharp": "mcr.microsoft.com/dotnet/sdk:8.0",
}


@lru_cache(maxsize=1)
def capabilities() -> dict:
    """What this host can actually enforce for the subprocess backend."""
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    has_rlimits = resource is not None
    has_proc_kill = hasattr(os, "setsid")
    caps = {"docker": shutil.which("docker") is not None, "root": is_root,
            "process_group_kill": has_proc_kill, "rlimits": has_rlimits, "uid_drop": False,
            "network_isolation": False, "readonly_fs": False}
    if caps["root"] and shutil.which("setpriv") and shutil.which("unshare"):
        caps["uid_drop"] = True
        try:
            r = subprocess.run(["unshare", "-n", "true"], capture_output=True, timeout=5)
            caps["network_isolation"] = r.returncode == 0
            with tempfile.TemporaryDirectory() as d:
                script = (f'mount --bind "{d}" "{d}" && mount --make-rprivate / && '
                          f'mount -o remount,ro,bind / && touch "{d}/ok" && ! touch /nonexistent_probe')
                r = subprocess.run(["unshare", "-m", "-n", "sh", "-c", script], capture_output=True, timeout=5)
                caps["readonly_fs"] = r.returncode == 0
        except Exception:
            pass
    return caps


def _count_procs(uid: int) -> int:
    if not os.path.exists("/proc"):
        return 0
    n = 0
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                if os.stat(f"/proc/{pid}").st_uid == uid:
                    n += 1
            except OSError:
                pass
    return n


def _kill_session(sid: int, uid: int | None):
    """SIGKILL everything in the session (and, for a dedicated uid, everything that uid owns)."""
    if not os.path.exists("/proc"):
        if sys.platform == "win32":
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(sid)], capture_output=True, timeout=5)
            except Exception:
                pass
        return
    for _ in range(3):
        found = False
        for pid in os.listdir("/proc"):
            if not pid.isdigit() or int(pid) == os.getpid():
                continue
            try:
                with open(f"/proc/{pid}/stat") as f:
                    parts = f.read().rsplit(")", 1)[1].split()
                psid = int(parts[3])
                owner = os.stat(f"/proc/{pid}").st_uid
                if psid == sid or (uid is not None and owner == uid):
                    os.kill(int(pid), signal.SIGKILL)
                    found = True
            except (OSError, IndexError, ValueError):
                pass
        if not found:
            break
        time.sleep(0.05)


class Sandbox:
    def __init__(self, limits: Limits | None = None, mode: str | None = None,
                 require_isolation: bool = False):
        self.limits = limits or Limits()
        self.mode = (mode or os.environ.get("SANDBOX_MODE") or "auto").lower()
        self.require_isolation = require_isolation

    # ------------------------------------------------------------------ public
    def backend(self) -> str:
        caps = capabilities()
        if self.mode == "docker":
            return "docker"
        if self.mode == "auto" and caps["docker"]:
            try:
                r = subprocess.run(["docker", "info"], capture_output=True, timeout=1)
                if r.returncode == 0:
                    return "docker"
            except Exception:
                pass
        return "subprocess"

    def run(self, cmd: list, workdir: str | Path, language: str = "python", env: dict | None = None,
            limits: Limits | None = None, data_limit_mb: int | None = None) -> SandboxResult:
        lim = limits or self.limits
        workdir = Path(workdir).resolve()
        if self.backend() == "docker":
            return self._run_docker(cmd, workdir, language, env or {}, lim, data_limit_mb)
        return self._run_subprocess(cmd, workdir, env or {}, lim, data_limit_mb)

    # ------------------------------------------------------------------ subprocess backend
    def _run_subprocess(self, cmd, workdir: Path, env_extra: dict, lim: Limits, data_mb) -> SandboxResult:
        caps = capabilities()
        if self.require_isolation and not (caps["uid_drop"] and caps["network_isolation"] and caps["readonly_fs"]):
            raise RuntimeError(f"require_isolation=True but this host cannot isolate: {caps}")
        uid = None
        argv = list(cmd)
        if caps["uid_drop"]:
            uid = random.randint(40000, 59999)
            while _count_procs(uid):
                uid = random.randint(40000, 59999)
            self._chown(workdir, uid)
            inner = ["setpriv", f"--reuid={uid}", f"--regid={uid}", "--clear-groups", "--no-new-privs", "--"] + argv
            if caps["network_isolation"] and caps["readonly_fs"]:
                script = ('mount --bind "$W" "$W" && mount --make-rprivate / && '
                          'mount -o remount,ro,bind / && cd "$W" && exec "$@"')   # cd: cwd predates the mount ns
                argv = ["unshare", "-m", "-n", "sh", "-c", script, "sandbox"] + inner
            elif caps["network_isolation"]:
                argv = ["unshare", "-n"] + inner
            else:
                argv = inner
        tmp = workdir / "tmp"
        tmp.mkdir(exist_ok=True)
        if uid is not None and hasattr(os, "chown"):
            os.chown(tmp, uid, uid)
        if sys.platform == "win32":
            env = dict(os.environ)
            env["HOME"] = str(workdir)
            env["TMPDIR"] = str(tmp)
            env["TEMP"] = str(tmp)
            env["TMP"] = str(tmp)
            env["W"] = str(workdir)
        else:
            env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(workdir), "TMPDIR": str(tmp),
                   "LANG": "C.UTF-8", "W": str(workdir)}
        env.update(env_extra)

        nproc_base = _count_procs(uid if uid is not None else (os.geteuid() if hasattr(os, "geteuid") else 0))
        data_bytes = (data_mb or lim.memory_mb) * 1024 * 1024

        preexec = None
        if sys.platform != "win32" and resource is not None and hasattr(os, "setsid"):
            def preexec():
                os.setsid()
                resource.setrlimit(resource.RLIMIT_CPU, (lim.cpu_s, lim.cpu_s + 1))
                resource.setrlimit(resource.RLIMIT_DATA, (data_bytes, data_bytes))
                resource.setrlimit(resource.RLIMIT_FSIZE, (lim.max_file_mb << 20, lim.max_file_mb << 20))
                resource.setrlimit(resource.RLIMIT_NOFILE, (lim.max_open_files, lim.max_open_files))
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                n = nproc_base + lim.max_procs
                resource.setrlimit(resource.RLIMIT_NPROC, (n, n))

        out_f = tempfile.NamedTemporaryFile(prefix="sbx-out-", delete=False)
        err_f = tempfile.NamedTemporaryFile(prefix="sbx-err-", delete=False)
        t0 = time.monotonic()
        timed_out, reason = False, ""
        proc = subprocess.Popen(argv, cwd=str(workdir), env=env, stdin=subprocess.DEVNULL,
                                stdout=out_f, stderr=err_f, preexec_fn=preexec, close_fds=(sys.platform != "win32"))
        try:
            proc.wait(timeout=lim.wall_s)
        except subprocess.TimeoutExpired:
            timed_out, reason = True, "timeout"
        finally:
            _kill_session(proc.pid, uid)
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        dur = int((time.monotonic() - t0) * 1000)
        rc = proc.returncode
        if not timed_out and rc is not None and rc < 0:
            try:
                reason = "signal:" + signal.Signals(-rc).name
            except ValueError:
                reason = f"signal:{-rc}"
        stdout, stderr = self._read(out_f.name, lim), self._read(err_f.name, lim)
        for f in (out_f, err_f):
            f.close()
            os.unlink(f.name)
        return SandboxResult(rc, stdout, stderr, timed_out, dur, reason, "subprocess")

    @staticmethod
    def _chown(path: Path, uid: int):
        os.chown(path, uid, uid)
        for root, dirs, files in os.walk(path):
            for n in dirs + files:
                try:
                    os.chown(os.path.join(root, n), uid, uid, follow_symlinks=False)
                except OSError:
                    pass

    @staticmethod
    def _read(path: str, lim: Limits) -> str:
        with open(path, "rb") as f:
            data = f.read(lim.max_output_kb * 1024 + 1)
        txt = data[: lim.max_output_kb * 1024].decode("utf8", "replace")
        return txt + ("\n[output truncated]" if len(data) > lim.max_output_kb * 1024 else "")

    # ------------------------------------------------------------------ docker backend
    def _run_docker(self, cmd, workdir: Path, language, env_extra, lim: Limits, data_mb) -> SandboxResult:
        image = os.environ.get(f"SANDBOX_IMAGE_{language.upper()}") or DOCKER_IMAGES.get(language, "ubuntu:24.04")
        name = f"tutor-sbx-{os.getpid()}-{random.randint(0, 1 << 30)}"
        mem = data_mb or lim.memory_mb
        args = ["docker", "run", "--rm", "--name", name, "--network", "none", "--read-only",
                "--tmpfs", "/tmp:rw,exec,size=128m", "--memory", f"{mem * 2}m", "--memory-swap", f"{mem * 2}m",
                "--cpus", "1", "--pids-limit", str(lim.max_procs), "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--ulimit", f"cpu={lim.cpu_s}",
                "--ulimit", f"fsize={lim.max_file_mb << 20}", "-v", f"{workdir}:/work:rw", "-w", "/work",
                "-e", "HOME=/work", "-e", "TMPDIR=/tmp"]
        for k, v in env_extra.items():
            args += ["-e", f"{k}={v}"]
        args += [image] + list(cmd)
        t0 = time.monotonic()
        timed_out = False
        try:
            r = subprocess.run(args, capture_output=True, timeout=lim.wall_s + 5)
            rc, so, se = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired as e:
            timed_out, rc, so, se = True, None, e.stdout or b"", e.stderr or b""
            subprocess.run(["docker", "kill", name], capture_output=True)
        dur = int((time.monotonic() - t0) * 1000)
        cut = lim.max_output_kb * 1024
        return SandboxResult(rc, so[:cut].decode("utf8", "replace"), se[:cut].decode("utf8", "replace"),
                             timed_out, dur, "timeout" if timed_out else "", "docker")


def make_workdir(prefix: str = "lesson-") -> Path:
    d = Path(tempfile.mkdtemp(prefix=prefix))
    d.chmod(0o755)
    return d


def cleanup(workdir: Path):
    shutil.rmtree(workdir, ignore_errors=True)
