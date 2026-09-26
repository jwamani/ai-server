"""Bounded subprocess execution for repository workspaces."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


class CommandExecutionError(RuntimeError):
    """Raised when a command cannot be started or exceeds its time limit."""


@dataclass(frozen=True)
class CommandResult:
    """Captured result of one command execution."""

    command: tuple[str, ...]
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class CommandRunner:
    """Execute argument-vector commands without invoking a shell."""

    def __init__(self, timeout_seconds: int = 120) -> None:
        self._timeout_seconds = timeout_seconds

    def run(self, command: list[str], cwd: Path) -> CommandResult:
        """Execute a command in a workspace and capture both output streams."""

        if not command:
            raise ValueError("Command must contain at least one argument.")
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                check=False,
                text=True,
                timeout=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            raise CommandExecutionError(
                f"Command timed out after {self._timeout_seconds} seconds: {command[0]}"
            ) from error
        except OSError as error:
            raise CommandExecutionError(
                f"Command could not start: {command[0]}"
            ) from error
        return CommandResult(
            command=tuple(command),
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
