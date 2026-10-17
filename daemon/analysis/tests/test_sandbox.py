import os
import time
from pathlib import Path

import pytest
from analysis.sandbox import Sandbox, Limits, capabilities, make_workdir, cleanup, _count_procs

CAPS = capabilities()


def sandbox_procs():
    """Live processes that belong to a sandbox run: owned by a throw-away uid (>= 40000) when we can drop uid,
    otherwise: the exact `python3 -c ...fork` / bash bomb command lines of the tests below."""
    out = []
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            uid = os.stat(f"/proc/{p}").st_uid
            cmd = Path(f"/proc/{p}/cmdline").read_bytes()
            if Path(f"/proc/{p}/stat").read_text().rsplit(")", 1)[1].split()[0] == "Z":
                continue                      # dead, just not yet reaped by this host's PID 1
        except OSError:
            continue
        if (CAPS["uid_drop"] and 40000 <= uid <= 59999) or (not CAPS["uid_drop"] and (cmd.startswith(b"python3\x00-c\x00import os\nwhile True") or cmd.startswith(b"bash\x00-c\x00:()"))):
            out.append((p, cmd[:40]))
    return out


@pytest.fixture
def wd():
    d = make_workdir()
    yield d
    cleanup(d)


def py(code, wd, wall=4, **lim):
    return Sandbox(Limits(wall_s=wall, **lim)).run(["python3", "-c", code], wd, "python")


def test_normal_program_runs_and_output_is_captured(wd):
    r = py("print('hi')", wd)
    assert (r.returncode, r.stdout.strip(), r.timed_out) == (0, "hi", False)


def test_while_true_is_killed_cleanly(wd):
    t = time.time()
    r = py("while True:\n    pass", wd, wall=2)
    assert r.timed_out and r.reason == "timeout" and time.time() - t < 8


def test_sleeping_forever_is_killed(wd):
    assert py("import time; time.sleep(999)", wd, wall=1).timed_out


def test_python_fork_bomb_survives(wd):
    code = "import os\nwhile True:\n    try:\n        os.fork()\n    except OSError:\n        pass\n"
    t = time.time()
    r = py(code, wd, wall=3)
    assert time.time() - t < 15
    time.sleep(0.3)
    assert sandbox_procs() == [], "fork-bomb children must all be reaped"
    assert r.timed_out or r.returncode is not None


@pytest.mark.skipif(not __import__("shutil").which("bash"), reason="bash needed")
def test_shell_fork_bomb_survives(wd):
    r = Sandbox(Limits(wall_s=3)).run(["bash", "-c", ":(){ :|:& };:"], wd, "python")
    time.sleep(0.3)
    assert sandbox_procs() == [] and r.duration_ms < 15000


def test_memory_bomb_is_stopped(wd):
    r = py("x = bytearray(4 * 1024**3)\nprint('allocated')", wd, wall=10, memory_mb=256)
    assert "allocated" not in r.stdout and r.returncode != 0 and not r.timed_out


def test_output_flood_is_truncated(wd):
    r = py("while True:\n    print('x' * 1000)", wd, wall=2, max_output_kb=64)
    assert len(r.stdout) < 70_000 and ("[output truncated]" in r.stdout)


def test_environment_is_scrubbed(wd, monkeypatch):
    monkeypatch.setenv("MY_SECRET_TOKEN", "hunter2")
    r = py("import os; print(os.environ.get('MY_SECRET_TOKEN'))", wd)
    assert r.stdout.strip() == "None"


def test_can_write_workdir_but_not_elsewhere_when_isolated(wd):
    r = py("open('ok.txt','w').write('1'); print('wd ok')\n"
           "try:\n    open('/usr/evil','w'); print('LEAK')\nexcept OSError as e:\n    print('blocked')", wd)
    assert "wd ok" in r.stdout
    if CAPS["readonly_fs"] or CAPS["uid_drop"]:
        assert "blocked" in r.stdout and "LEAK" not in r.stdout


@pytest.mark.skipif(not CAPS["network_isolation"], reason="host cannot create network namespaces")
def test_no_network(wd):
    r = py("import socket\ntry:\n    socket.create_connection(('1.1.1.1', 53), 1); print('CONNECTED')\nexcept OSError as e:\n    print('no network')", wd)
    assert "no network" in r.stdout


@pytest.mark.skipif(not CAPS["uid_drop"], reason="needs root to drop uid")
def test_runs_as_unprivileged_uid(wd):
    r = py("import os; print(os.getuid())", wd)
    assert int(r.stdout) >= 40000


def test_require_isolation_refuses_when_unavailable(wd):
    if CAPS["uid_drop"] and CAPS["network_isolation"] and CAPS["readonly_fs"]:
        pytest.skip("this host can isolate")
    with pytest.raises(RuntimeError):
        Sandbox(require_isolation=True, mode="subprocess").run(["true"], wd)
