import subprocess
import tempfile
import shutil
import uuid
import logging
from typing import Tuple

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

# Source filename and in-container command per supported language. C/C++ are
# compiled to the writable /tmp tmpfs (the source mount at /app is read-only),
# then executed; a compile failure simply surfaces as a non-zero exit code
# with the compiler diagnostics on stderr, same as any other runtime error.
# -Wno-implicit-function-declaration: GCC 14+ turned a missing #include (e.g. forgetting
# <stdio.h> before scanf/printf) from a warning into a hard compile error. That's a very
# common beginner/AI-generated omission that still runs fine on this architecture, so it's
# downgraded back to a warning rather than failing programs that would otherwise work.
LANGUAGE_COMMANDS = {
    "python": ("main.py", "python main.py < input.txt"),
    "c": (
        "main.c",
        "gcc -O2 -Wno-implicit-function-declaration -o /tmp/main main.c && /tmp/main < input.txt",
    ),
    "cpp": (
        "main.cpp",
        "g++ -O2 -o /tmp/main main.cpp && /tmp/main < input.txt",
    ),
}

SUPPORTED_LANGUAGES = tuple(LANGUAGE_COMMANDS.keys())


class SandboxUnavailableError(RuntimeError):
    """Raised when the Docker sandbox cannot be used. Untrusted code is never run on the host."""


def run_code(language: str, source_code: str, input_data: str) -> Tuple[str, str, int, bool]:
    """
    Runs source_code inside an isolated Docker container for the given language.
    Raises SandboxUnavailableError if Docker or the python-runner image is unavailable.
    Returns (stdout, stderr, return_code, is_timeout)
    """
    if language not in LANGUAGE_COMMANDS:
        raise ValueError(f"Unsupported language: {language}")
    filename, run_command = LANGUAGE_COMMANDS[language]

    temp_dir = tempfile.mkdtemp()

    with open(f"{temp_dir}/{filename}", "w", encoding="utf-8") as f:
        f.write(source_code)

    with open(f"{temp_dir}/input.txt", "w", encoding="utf-8") as f:
        f.write(input_data)

    container_name = f"runner_{uuid.uuid4().hex}"
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
        "sh", "-c", f"timeout {TIMEOUT_SECONDS} sh -c '{run_command}'",
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
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        stdout = e.stdout.decode("utf-8") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return stdout, stderr, -1, True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    stderr_lower = process.stderr.lower()
    if process.returncode != 0 and any(m in stderr_lower for m in DOCKER_UNAVAILABLE_MARKERS):
        logger.error("[CodeRunner] Docker daemon unavailable or python-runner image missing.")
        raise SandboxUnavailableError(
            "Code execution sandbox is unavailable. Ensure Docker is running and the "
            "'python-runner' image is built."
        )

    is_timeout = process.returncode in TIMEOUT_EXIT_CODES
    return process.stdout, process.stderr, process.returncode, is_timeout
