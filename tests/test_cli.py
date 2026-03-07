import sys
from typing import NamedTuple
from unittest import mock

import pytest

from bumpversion_slim import cli, errors


class Result(NamedTuple):
    exit_code: int
    output: str


class CliRunner:
    def __init__(self, capsys, monkeypatch):
        self.capsys = capsys
        self.mp = monkeypatch

    def invoke(self, *args):
        self.mp.setattr(sys, "argv", ["bumpversion", *args])
        with pytest.raises(SystemExit) as e:
            cli.main()
        captured = self.capsys.readouterr()
        return Result(int(str(e.value)), captured.out)


@pytest.fixture
def cli_runner(capsys, monkeypatch):
    return CliRunner(capsys, monkeypatch)


@pytest.fixture(autouse=True)
def mock_git(monkeypatch):
    mock_git = mock.Mock()
    mock_git.get_current_info.return_value = {
        "missing_local": False,
        "missing_remote": False,
        "dirty": False,
        "branch": "main",
    }
    mock_git.get_logs.return_value = []
    mock_git.find_tag.return_value = "v0.0.0"

    monkeypatch.setattr(cli, "Git", mock.Mock(return_value=mock_git))

    return mock_git


@pytest.fixture
def mock_bump(monkeypatch):
    mock_bump = mock.Mock()
    mock_bump.replace.return_value = ["pyproject.toml"]

    monkeypatch.setattr(cli, "BumpVersion", mock.Mock(return_value=mock_bump))

    return mock_bump


@pytest.fixture
def changelog(cwd):
    p = cwd / "CHANGELOG.md"
    p.write_text("# Changelog\n")

    return p


@pytest.mark.usefixtures("changelog")
def test_bump_handles_exceptions(cli_runner, config_factory, monkeypatch):
    monkeypatch.setattr(cli, "_bump", mock.Mock(side_effect=errors.BumpException("Something happened")))
    config_factory(allow_dirty=False)
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 1
    assert "Something happened" in result.output


@pytest.mark.usefixtures("changelog")
def test_bump_aborts_if_dirty(cli_runner, mock_git, config_factory):
    config_factory(allow_dirty=False)
    mock_git.get_current_info.return_value = {
        "dirty": True,
        "branch": "main",
    }
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 1
    assert result.output.strip() == "Working directory is not clean. Use `allow_dirty` configuration to ignore."


@pytest.mark.usefixtures("changelog")
def test_bump_allows_dirty(cli_runner, config_factory):
    config_factory(allow_dirty=False)
    result = cli_runner.invoke("1.2.3", "--allow-dirty")

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog")
def test_bupm_continues_if_allow_dirty_configured(cli_runner, config_factory):
    config_factory(allow_dirty=True)
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog")
def test_bump_aborts_if_missing_local(cli_runner, config_factory, mock_git):
    config_factory(allow_missing=False)
    mock_git.get_current_info.return_value = {
        "missing_local": True,
        "dirty": False,
        "branch": "main",
    }
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 1
    assert "Current local branch is missing commits from remote main." in result.output


@pytest.mark.usefixtures("changelog")
def test_bump_continues_if_allow_missing_configured_missing_local(cli_runner, mock_git, config_factory):
    config_factory(allow_missing=True)
    mock_git.get_current_info.return_value = {
        "missing_remote": False,
        "missing_local": True,
        "dirty": False,
        "branch": "main",
    }
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog")
def test_bump_aborts_if_missing_remote(cli_runner, config_factory, mock_git):
    config_factory(allow_missing=False)
    mock_git.get_current_info.return_value = {
        "missing_remote": True,
        "missing_local": False,
        "dirty": False,
        "branch": "main",
    }
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 1
    assert "Current remote branch is missing commits from local main." in result.output


@pytest.mark.usefixtures("changelog")
def test_bump_continues_if_allow_missing_configured_missing_remote(cli_runner, config_factory, mock_git):
    config_factory(allow_missing=True)
    mock_git.get_current_info.return_value = {
        "missing_remote": True,
        "missing_local": False,
        "dirty": False,
        "branch": "main",
    }
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog")
def test_bump_aborts_if_unsupported_current_branch(cli_runner, config_factory):
    config_factory(allow_dirty=True, allowed_branches=["release_candidate"])
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 1
    assert result.output.strip() == "Current branch not in allowed generation branches."


@pytest.mark.usefixtures("changelog")
def test_bump_allows_supported_branch(cli_runner, config_factory):
    config_factory(allow_dirty=True, allowed_branches=["main"])
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog")
def test_bump_creates_release(
    cli_runner,
    mock_git,
    mock_bump,
    config_factory,
):
    config_factory(commit_extra=["CHANGELOG.md"])
    result = cli_runner.invoke("1.2.3", "--commit")

    assert result.exit_code == 0
    assert mock_git.commit.call_args == mock.call("0.0.0", "1.2.3", "v1.2.3", ["CHANGELOG.md", "pyproject.toml"])
    assert mock_bump.replace.call_args == mock.call("1.2.3")


@pytest.mark.usefixtures("changelog")
def test_bump_creates_release_using_config(
    cli_runner,
    mock_git,
    config_factory,
):
    config_factory(commit=True)

    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 0
    assert mock_git.commit.call_args == mock.call("0.0.0", "1.2.3", "v1.2.3", ["pyproject.toml"])


@pytest.mark.usefixtures("changelog")
@pytest.mark.parametrize(
    "hook",
    [
        "invalid_format",
        "invalid_module:func",
        "tests.test_cli:invalid_func",
    ],
)
def test_bump_handles_invalid_hooks(
    cli_runner,
    config_factory,
    hook,
):
    config_factory(hooks=[hook])
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 1
    assert "Invalid hook" in result.output


def hook(_ctx, _new):
    return ["test_path"]


@pytest.mark.usefixtures("changelog")
def test_bump_handles_valid_hooks(
    cli_runner,
    config_factory,
    mock_git,
):
    config_factory(hooks=["tests.test_cli:hook"])
    result = cli_runner.invoke("1.2.3")

    assert result.exit_code == 0, result.output
    assert mock_git.commit.call_args == mock.call("0.0.0", "1.2.3", "v1.2.3", ["pyproject.toml", "test_path"])


@pytest.mark.usefixtures("config")
def test_bump_dry_run(
    cli_runner,
    mock_bump,
):
    result = cli_runner.invoke("1.2.3", "--dry-run")

    assert result.exit_code == 0

    assert mock_bump.call_args is None
