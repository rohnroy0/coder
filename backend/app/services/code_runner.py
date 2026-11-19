import subprocess
import tempfile
import shutil
import uuid
import logging
from typing import Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 5
# Extra wall-clock allowance for container startup/teardown, so slow Docker
# startup is not counted against the user's program.
DOCKER_OVERHEAD_SECONDS = 15
# Exit codes produced by the in-container `timeout` (124) or by the program
# being terminated with SIGTERM (128 + 15).
TIMEOUT_EXIT_CODES = (124, 143)

DOCKER_UNAVAILABLE_MARKERS = (
    "docker api",
    "cannot find the file specified",
    "daemon is running",
    "unable to find image",
)

# Source filename, compile command (None for interpreted languages), and run
# command per supported language. C/C++ are compiled to the writable /tmp tmpfs
# (the source mount at /app is read-only), then executed; a compile failure
# simply surfaces as a non-zero exit code with the compiler diagnostics on
# stderr, same as any other runtime error.
# -Wno-implicit-function-declaration: GCC 14+ turned a missing #include (e.g. forgetting
# <stdio.h> before scanf/printf) from a warning into a hard compile error. That's a very
# common beginner/AI-generated omission that still runs fine on this architecture, so it's
# downgraded back to a warning rather than failing programs that would otherwise work.
LANGUAGE_COMMANDS = {
    "python": ("main.py", None, "python main.py < input.txt"),
    "c": (
        "main.c",
        "gcc -O2 -Wno-implicit-function-declaration -o /tmp/main main.c",
        "/tmp/main < input.txt",
    ),
    "cpp": (
        "main.cpp",
        "g++ -O2 -o /tmp/main main.cpp",
        "/tmp/main < input.txt",
    ),
}

SUPPORTED_LANGUAGES = tuple(LANGUAGE_COMMANDS.keys())

# In-container timing wrapper. Host-side wall time around `docker run` includes
# container create/start/teardown (seconds), which made the fast-execution
# bonus unreachable; this measures only the student program itself, excluding
# the compile phase for C/C++. The elapsed time is reported on stderr via a
# marker line; the host takes the LAST marker, and since the wrapper prints
# after the program has exited, a student printing a fake marker can't win.
RUNTIME_MARKER = "__CODER_RUNTIME__"
TIMER_WRAPPER_FILENAME = "_coder_wrapper.py"
TIMER_WRAPPER_SOURCE = f"""\
import subprocess, sys, time

timeout_s = sys.argv[1]
compile_cmd = sys.argv[2]
run_cmd = sys.argv[3]

if compile_cmd:
    comp = subprocess.run(["sh", "-c", compile_cmd])
    if comp.returncode != 0:
        sys.exit(comp.returncode)

start = time.monotonic()
proc = subprocess.run(["timeout", timeout_s, "sh", "-c", run_cmd])
elapsed = time.monotonic() - start
print("{RUNTIME_MARKER} %.6f" % elapsed, file=sys.stderr, flush=True)
sys.exit(proc.returncode)
"""


class SandboxUnavailableError(RuntimeError):
    """Raised when the Docker sandbox cannot be used. Untrusted code is never run on the host."""


def run_code(language: str, source_code: str, input_data: str) -> Tuple[str, str, int, bool, Optional[float]]:
    """
    Runs source_code inside an isolated Docker container for the given language.
    Raises SandboxUnavailableError if Docker or the python-runner image is unavailable.
    Returns (stdout, stderr, return_code, is_timeout, runtime_seconds).
    runtime_seconds is the in-container program execution time (compile phase
    excluded), or None if it could not be measured (e.g. host-side timeout).
    """
    if language not in LANGUAGE_COMMANDS:
        raise ValueError(f"Unsupported language: {language}")
    filename, compile_command, run_command = LANGUAGE_COMMANDS[language]

    temp_dir = tempfile.mkdtemp()
    container_name = f"runner_{uuid.uuid4().hex}"

    try:
        with open(f"{temp_dir}/{filename}", "w", encoding="utf-8") as f:
            f.write(source_code)

        with open(f"{temp_dir}/input.txt", "w", encoding="utf-8") as f:
            f.write(input_data)

        with open(f"{temp_dir}/{TIMER_WRAPPER_FILENAME}", "w", encoding="utf-8") as f:
            f.write(TIMER_WRAPPER_SOURCE)

        cmd = [
            "docker", "run",
            "--name", container_name,
            "--label", "app=code-runner",
            *([] if settings.RUNNER_KEEP_CONTAINERS else ["--rm"]),
            # Without an init process the program runs as PID 1, which ignores SIGTERM
            # and so would never be stopped by `timeout`.
            "--init",
            "--network", "none",
            "--memory", "128m",
            "--memory-swap", "128m",
            "--cpus", "0.5",
            "--pids-limit", "64",
            "--read-only",
            # exec: Docker's tmpfs mounts default to noexec, which would block running the
            # compiled binary for the C path (the binary is written here since /app is read-only).
            "--tmpfs", "/tmp:rw,exec,size=16m",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-v", f"{temp_dir}:/app:ro",
            "python-runner",
            "python", f"/app/{TIMER_WRAPPER_FILENAME}",
            str(TIMEOUT_SECONDS), compile_command or "", run_command,
        ]

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS + DOCKER_OVERHEAD_SECONDS
            )
        except FileNotFoundError:
            raise SandboxUnavailableError("Docker executable not found.")
        except subprocess.TimeoutExpired as e:
            try:
                subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=30)
            except subprocess.TimeoutExpired:
                logger.error("[CodeRunner] Timed out force-removing container %s", container_name)
            stdout = e.stdout.decode("utf-8") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else (e.stderr or "")
            return stdout, stderr, -1, True, None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Extract the in-container runtime marker and strip marker lines from the
    # stderr handed back to callers (it must never reach students). The LAST
    # marker wins - the wrapper's own marker is printed after the program
    # exits, so student-printed fakes are always overridden.
    runtime_seconds = None
    kept_lines = []
    for line in process.stderr.splitlines():
        if line.startswith(RUNTIME_MARKER):
            parts = line.split()
            if len(parts) == 2:
                try:
                    runtime_seconds = float(parts[1])
                except ValueError:
                    pass
        else:
            kept_lines.append(line)
    stderr_text = "\n".join(kept_lines)

    stderr_lower = stderr_text.lower()
    if process.returncode != 0 and any(m in stderr_lower for m in DOCKER_UNAVAILABLE_MARKERS):
        # The captured stderr INCLUDES the student program's own stderr, so a
        # student printing e.g. "unable to find image" could spoof this branch
        # (which deletes their judged submission). Confirm with a probe that
        # talks only to the Docker daemon before declaring the sandbox down.
        if _sandbox_really_unavailable():
            logger.error("[CodeRunner] Docker daemon unavailable or python-runner image missing.")
            raise SandboxUnavailableError(
                "Code execution sandbox is unavailable. Ensure Docker is running and the "
                "'python-runner' image is built."
            )

    is_timeout = process.returncode in TIMEOUT_EXIT_CODES
    return process.stdout, stderr_text, process.returncode, is_timeout, runtime_seconds


def _sandbox_really_unavailable() -> bool:
    """True when the Docker daemon is unreachable or the runner image is missing.
    Output of this probe never contains student-controlled text."""
    try:
        probe = subprocess.run(
            ["docker", "image", "inspect", "python-runner"],
            capture_output=True, text=True, timeout=15
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True
    return probe.returncode != 0
