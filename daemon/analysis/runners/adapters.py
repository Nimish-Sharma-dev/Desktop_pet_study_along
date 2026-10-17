"""One adapter per language. Each adapter knows: which file the student edits, how to
build, how to run the framework, and how to parse its native output.

Status in this repo (see README "Verification"):
  end-to-end tested : python (pytest), javascript (Jest), go (go test), java (JUnit 5), cpp (GoogleTest)
  parser/command tested only (toolchain not installed where this was built):
                      typescript (Vitest), rust (cargo test), c_sharp (xUnit), kotlin (JUnit 5)
"""
from __future__ import annotations
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import parsers as P
from .base import Adapter, RunnerError, Step

CACHE_DIR = Path(os.environ.get("ANALYSIS_CACHE", Path.home() / ".cache" / "tutor-analysis"))


def _read(workdir: Path, name: str) -> str:
    f = workdir / name
    return f.read_text(errors="replace") if f.exists() else ""


def _need(*tools) -> str | None:
    missing = [t for t in tools if not shutil.which(t)]
    return f"required tool(s) not on PATH: {', '.join(missing)}" if missing else None


# ------------------------------------------------------------------------------ Python / pytest
class PythonAdapter(Adapter):
    language, framework, solution_files = "python", "pytest", ["solution.py"]
    isolate = True

    def available(self):
        try:
            subprocess.run([sys.executable, "-c", "import pytest"], check=True, capture_output=True, timeout=20)
        except Exception:
            return "pytest is not installed for " + sys.executable
        return None

    def test_step(self, workdir, only=None):
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml=results.xml",
               "--rootdir=.", "test_visible.py", "test_hidden.py"]
        if only:
            cmd += ["-k", f"test_{only}"]
        return Step(cmd, env={"PYTHONDONTWRITEBYTECODE": "1"}, wall_s=40, data_mb=1024)

    def parse(self, workdir, res):
        return P.parse_junit_xml(_read(workdir, "results.xml"))


# ------------------------------------------------------------------------------ JavaScript / Jest
def _jest_bin() -> str | None:
    env = os.environ.get("JEST_BIN")
    if env:
        return env
    j = shutil.which("jest")
    return str(Path(j).resolve()) if j else None


class JavaScriptAdapter(Adapter):
    language, framework, solution_files = "javascript", "jest", ["solution.js"]
    isolate = True
    data_mb = 2048

    def available(self):
        return _need("node") or (None if _jest_bin() else "jest not found (npm i -g jest, or set JEST_BIN)")

    def test_step(self, workdir, only=None):
        cmd = ["node", _jest_bin(), "--config", "jest.config.js", "--json", "--outputFile=results.json",
               "--runInBand", "--ci"]
        if only:
            cmd += ["-t", f"^{only}$"]
        return Step(cmd, env={"NODE_OPTIONS": "--max-old-space-size=384"}, wall_s=60, data_mb=self.data_mb)

    def parse(self, workdir, res):
        return P.parse_jest_json(_read(workdir, "results.json"))


class TypeScriptAdapter(JavaScriptAdapter):
    language, framework, solution_files = "typescript", "vitest", ["solution.ts"]

    def available(self):
        return _need("node", "vitest")

    def test_step(self, workdir, only=None):
        cmd = ["vitest", "run", "--root", str(workdir), "--reporter=json", "--outputFile=results.json"]
        if only:
            cmd += ["-t", f"^{only}$"]
        return Step(cmd, env={"NODE_OPTIONS": "--max-old-space-size=384"}, wall_s=60, data_mb=self.data_mb)


# ------------------------------------------------------------------------------ Go / go test
class GoAdapter(Adapter):
    rerun_timeouts = True
    language, framework, solution_files = "go", "go test", ["solution.go"]
    isolate = True
    data_mb = 1536

    def available(self):
        return _need("go")

    def _env(self, workdir):
        return {"GOCACHE": str(workdir / ".gocache"), "GOPATH": str(workdir / ".gopath"),
                "GOFLAGS": "-mod=mod", "GO111MODULE": "on", "GOTOOLCHAIN": "local", "GOPROXY": "off",
                "CGO_ENABLED": "0", "GOROOT": subprocess.check_output(["go", "env", "GOROOT"], text=True).strip()}

    def _warm(self) -> Path:
        """Pre-compile the standard library once so each run starts with a warm build cache."""
        warm = CACHE_DIR / "gocache"
        if (warm / ".warm").exists():
            return warm
        warm.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_DIR / "gowarm"
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "go.mod").write_text("module lesson\n\ngo 1.22\n")
        (tmp / "w_test.go").write_text('package lesson\nimport ("testing";"fmt";"reflect";"encoding/json";"time";"runtime/debug";"strings";"sort")\n'
                                       'var _ = fmt.Sprint\nvar _ = reflect.DeepEqual\nvar _ = json.Marshal\nvar _ = time.Now\n'
                                       'var _ = debug.Stack\nvar _ = strings.Join\nvar _ = sort.Ints\nfunc TestW(t *testing.T){}\n')
        env = dict(os.environ, GOCACHE=str(warm), GOFLAGS="-mod=mod", GOTOOLCHAIN="local", GOPROXY="off", CGO_ENABLED="0")
        subprocess.run(["go", "test", "-vet=off", "-count=1", "./..."], cwd=tmp, env=env, check=True,
                       capture_output=True, timeout=300)
        (warm / ".warm").write_text("ok")
        return warm

    def prepare(self, lesson_dir, solution, workdir):
        super().prepare(lesson_dir, solution, workdir)
        (workdir / "go.mod").write_text("module lesson\n\ngo 1.22\n")
        shutil.copytree(self._warm(), workdir / ".gocache", dirs_exist_ok=True)

    def build_steps(self, workdir):
        return [Step(["go", "test", "-c", "-vet=off", "-o", "lesson.test"], "build", self._env(workdir),
                     self.data_mb, 120)]

    def test_step(self, workdir, only=None):
        cmd = ["go", "tool", "test2json", "-p", "lesson", "./lesson.test", "-test.v", "-test.timeout=25s"]
        if only:
            cmd.append(f"-test.run=^Test_{only}$")
        return Step(cmd, env=self._env(workdir), data_mb=self.data_mb, wall_s=40)

    def parse(self, workdir, res):
        return P.parse_go_test_json(res.stdout)

    def canonical(self, native):
        return native.removeprefix("Test_")


# ------------------------------------------------------------------------------ Java / JUnit 5
def _junit_jar() -> str | None:
    env = os.environ.get("JUNIT_CONSOLE_JAR")
    if env:
        return env
    for pat in ("/usr/share/java/junit-platform-console-standalone*.jar", "/usr/local/share/java/junit-platform-console-standalone*.jar"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


class JavaAdapter(Adapter):
    rerun_timeouts = True
    language, framework, solution_files = "java", "JUnit 5", ["Solution.java"]
    isolate = True
    data_mb = 2048

    def available(self):
        return _need("javac", "java") or (None if _junit_jar() else "junit-platform-console-standalone.jar not found (set JUNIT_CONSOLE_JAR)")

    def build_steps(self, workdir):
        srcs = [p.name for p in workdir.glob("*.java")]
        return [Step(["javac", "-J-Xmx256m", "-cp", _junit_jar(), "-d", "out", *srcs], "build", data_mb=self.data_mb, wall_s=90)]

    def test_step(self, workdir, only=None):
        cmd = ["java", "-Xmx256m", "-XX:+UseSerialGC", "-XX:TieredStopAtLevel=1", "-Xshare:auto",
               "-cp", f"out:{_junit_jar()}", "org.junit.platform.console.ConsoleLauncher",
               "--disable-banner", "--details=none", "--reports-dir=reports"]
        if only:
            cmd += ["--select-method", f"VisibleTest#{only}", "--select-method", f"HiddenTest#{only}"]
        else:
            cmd += ["--scan-class-path", "out"]
        return Step(cmd, data_mb=self.data_mb, wall_s=60)

    def parse(self, workdir, res):
        out = []
        for f in sorted((workdir / "reports").glob("TEST-*.xml")):
            out += P.parse_junit_xml(f.read_text(errors="replace"))
        return out


# ------------------------------------------------------------------------------ C++ / GoogleTest
class CppAdapter(Adapter):
    rerun_timeouts = True
    language, framework, solution_files = "cpp", "GoogleTest", ["solution.cpp"]
    isolate = True

    def available(self):
        return _need("g++")

    def prepare(self, lesson_dir, solution, workdir):
        super().prepare(lesson_dir, solution, workdir)
        # unity build: student code + visible + hidden tests in one translation unit
        parts = ['#include "solution.cpp"', "#include <gtest/gtest.h>"]
        for f in sorted(workdir.glob("*_test.cpp")):
            parts.append(f'#include "{f.name}"')
        (workdir / "all_tests.cpp").write_text("\n".join(parts) + "\n")

    def build_steps(self, workdir):
        return [Step(["g++", "-std=c++17", "-O1", "-o", "lesson_test", "all_tests.cpp", "-lgtest", "-lgtest_main", "-pthread"],
                     "build", wall_s=120)]

    def test_step(self, workdir, only=None):
        cmd = ["./lesson_test", "--gtest_output=xml:results.xml"]
        if only:
            cmd.append(f"--gtest_filter=*.{only}")
        return Step(cmd, wall_s=40)

    def parse(self, workdir, res):
        return P.parse_junit_xml(_read(workdir, "results.xml"))


# ------------------------------------------------------------------------------ Rust / cargo test
class RustAdapter(Adapter):
    rerun_timeouts = True
    language, framework, solution_files = "rust", "cargo test", ["solution.rs"]
    isolate = True
    data_mb = 2048

    def available(self):
        return _need("cargo")

    def prepare(self, lesson_dir, solution, workdir):
        (workdir / "src").mkdir(exist_ok=True)
        (workdir / "tests").mkdir(exist_ok=True)
        (workdir / "Cargo.toml").write_text('[package]\nname = "lesson"\nversion = "0.1.0"\nedition = "2021"\n\n[lib]\npath = "src/lib.rs"\n')
        shutil.copy2(solution, workdir / "src" / "lib.rs")
        for sub in ("visible", "hidden"):
            d = lesson_dir / "tests" / "rust" / sub
            if d.exists():
                for f in d.iterdir():
                    shutil.copy2(f, workdir / "tests" / f.name)

    def _env(self, workdir):
        return {"CARGO_HOME": str(workdir / ".cargo"), "CARGO_TARGET_DIR": str(workdir / "target"),
                "CARGO_NET_OFFLINE": "true", "RUSTUP_HOME": os.environ.get("RUSTUP_HOME", str(Path.home() / ".rustup"))}

    def build_steps(self, workdir):
        return [Step(["cargo", "test", "--offline", "--no-run"], "build", self._env(workdir), self.data_mb, 180)]

    def test_step(self, workdir, only=None):
        cmd = ["cargo", "test", "--offline", "--", "--test-threads=1"]
        if only:
            cmd += ["--exact", only]
        return Step(cmd, env=self._env(workdir), data_mb=self.data_mb, wall_s=60)

    def parse(self, workdir, res):
        return P.parse_cargo_test(res.stdout)


# ------------------------------------------------------------------------------ C# / xUnit
class CSharpAdapter(Adapter):
    rerun_timeouts = True
    language, framework, solution_files = "c_sharp", "xUnit", ["Solution.cs"]
    isolate = True
    data_mb = 2048

    def available(self):
        return _need("dotnet")

    def prepare(self, lesson_dir, solution, workdir):
        super().prepare(lesson_dir, solution, workdir)   # support/ must contain Lesson.csproj referencing xunit (offline NuGet cache)

    def _env(self, workdir):
        return {"DOTNET_CLI_HOME": str(workdir), "DOTNET_NOLOGO": "1", "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
                "NUGET_PACKAGES": os.environ.get("NUGET_PACKAGES", str(Path.home() / ".nuget" / "packages"))}

    def build_steps(self, workdir):
        return [Step(["dotnet", "build", "--no-restore", "-nologo"], "build", self._env(workdir), self.data_mb, 180)]

    def test_step(self, workdir, only=None):
        cmd = ["dotnet", "test", "--no-build", "--logger", "xunit;LogFilePath=results.xml"]
        if only:
            cmd += ["--filter", f"Name={only}"]
        return Step(cmd, env=self._env(workdir), data_mb=self.data_mb, wall_s=90)

    def parse(self, workdir, res):
        txt = _read(workdir, "results.xml")
        return P.parse_xunit_xml(txt) if "<assemblies" in txt[:500] else P.parse_junit_xml(txt)


# ------------------------------------------------------------------------------ Kotlin / JUnit 5
class KotlinAdapter(JavaAdapter):
    language, framework, solution_files = "kotlin", "JUnit 5", ["Solution.kt"]

    def available(self):
        return _need("kotlinc", "java") or (None if _junit_jar() else "junit-platform-console-standalone.jar not found")

    def build_steps(self, workdir):
        srcs = [p.name for p in workdir.glob("*.kt")]
        return [Step(["kotlinc", "-cp", _junit_jar(), "-d", "out", *srcs], "build", data_mb=self.data_mb, wall_s=180)]
