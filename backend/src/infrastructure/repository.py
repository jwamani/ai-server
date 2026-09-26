"""Git repository operations used by task execution."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


class RepositoryError(RuntimeError):
    """Raised when a Git repository operation fails."""


@dataclass(frozen=True)
class PreparedRepository:
    """Metadata for a task-specific repository workspace."""

    path: Path
    base_commit: str
    agent_branch: str


class GitRepositoryAdapter:
    """Run validated Git operations without invoking a shell."""

    def __init__(self, git_executable: str = "git", timeout_seconds: int = 120) -> None:
        self._git_executable = git_executable
        self._timeout_seconds = timeout_seconds

    def prepare(
        self,
        remote_url: str,
        base_branch: str,
        agent_branch: str,
        workspace: Path,
    ) -> PreparedRepository:
        """Clone a base branch and create an isolated agent branch."""

        workspace.parent.mkdir(parents=True, exist_ok=True)
        self._run(
            [
                "clone",
                "--branch",
                base_branch,
                "--single-branch",
                remote_url,
                str(workspace),
            ]
        )
        self._run(["checkout", "-b", agent_branch], cwd=workspace)
        base_commit = self._run(["rev-parse", "HEAD"], cwd=workspace).stdout.strip()
        return PreparedRepository(
            path=workspace,
            base_commit=base_commit,
            agent_branch=agent_branch,
        )

    def status(self, workspace: Path) -> str:
        """Return the porcelain status for a prepared workspace."""

        return self._run(["status", "--short"], cwd=workspace).stdout

    def diff(self, workspace: Path) -> str:
        """Return the working-tree diff for a prepared workspace."""

        return self._run(["diff", "--no-ext-diff", "--"], cwd=workspace).stdout

    def _run(
        self, arguments: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run one Git command with bounded execution and captured output."""

        try:
            result = subprocess.run(
                [self._git_executable, *arguments],
                cwd=cwd,
                capture_output=True,
                check=False,
                text=True,
                timeout=self._timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            message = f"Git command failed to start or timed out: {arguments[0]}"
            raise RepositoryError(message) from error
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise RepositoryError(f"Git command failed: {arguments[0]}: {detail}")
        return result
