"""Integration coverage for real Git repository preparation."""

import subprocess
from pathlib import Path

from src.infrastructure.repository import GitRepositoryAdapter


def _run_git(arguments: list[str], cwd: Path) -> None:
    """Run a Git setup command for the integration fixture."""

    subprocess.run(
        ["git", *arguments], cwd=cwd, check=True, capture_output=True, text=True
    )


def test_prepare_status_and_diff_use_real_git(tmp_path: Path) -> None:
    """A task workspace is cloned, branched, and inspected through Git."""

    source = tmp_path / "source"
    source.mkdir()
    _run_git(["init", "--initial-branch", "main"], source)
    _run_git(["config", "user.email", "integration@example.test"], source)
    _run_git(["config", "user.name", "Integration Test"], source)
    (source / "README.md").write_text("initial\n", encoding="utf-8")
    _run_git(["add", "README.md"], source)
    _run_git(["commit", "-m", "initial"], source)

    workspace = tmp_path / "workspace"
    prepared = GitRepositoryAdapter().prepare(
        remote_url=str(source),
        base_branch="main",
        agent_branch="task/integration-test",
        workspace=workspace,
    )

    assert prepared.path == workspace
    assert prepared.agent_branch == "task/integration-test"
    assert len(prepared.base_commit) == 40
    assert GitRepositoryAdapter().status(workspace) == ""

    (workspace / "README.md").write_text("changed\n", encoding="utf-8")
    assert "-initial" in GitRepositoryAdapter().diff(workspace)
    assert "+changed" in GitRepositoryAdapter().diff(workspace)
