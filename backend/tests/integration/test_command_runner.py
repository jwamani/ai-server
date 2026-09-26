"""Integration coverage for real bounded command execution."""

from pathlib import Path

import pytest

from src.infrastructure.commands import CommandExecutionError, CommandRunner


def test_command_runner_captures_output_and_exit_code(tmp_path: Path) -> None:
    """A real Python subprocess runs in the requested workspace."""

    result = CommandRunner().run(
        ["python", "-c", "from pathlib import Path; print(Path.cwd().name)"],
        cwd=tmp_path,
    )

    assert result.return_code == 0
    assert result.stdout.strip() == tmp_path.name
    assert result.stderr == ""
    assert result.command[0] == "python"


def test_command_runner_captures_nonzero_result(tmp_path: Path) -> None:
    """A failed command returns its exit code and stderr for persistence."""

    result = CommandRunner().run(
        ["python", "-c", "import sys; print('failure', file=sys.stderr); sys.exit(7)"],
        cwd=tmp_path,
    )

    assert result.return_code == 7
    assert result.stdout == ""
    assert result.stderr.strip() == "failure"


def test_command_runner_enforces_timeout(tmp_path: Path) -> None:
    """A command exceeding its limit is stopped with a useful error."""

    with pytest.raises(CommandExecutionError, match="timed out"):
        CommandRunner(timeout_seconds=1).run(
            ["python", "-c", "import time; time.sleep(2)"],
            cwd=tmp_path,
        )
