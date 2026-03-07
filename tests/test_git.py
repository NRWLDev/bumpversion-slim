from unittest import mock

import git
import pytest

from bumpversion_slim import errors
from bumpversion_slim import git as vcs
from bumpversion_slim.config import Config
from bumpversion_slim.context import Context
from bumpversion_slim.git import Git


@pytest.fixture
def context():
    return Context(Config(current_version="0.1.0"))


@pytest.fixture
def repo(git_repo):
    path = git_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world!")

    git_repo.run("git add hello.txt")
    git_repo.api.index.commit("initial commit")

    git_repo.api.create_tag("0.0.1")

    f.write_text("hello world! v2")
    git_repo.run("git add hello.txt")
    git_repo.api.index.commit("update")

    git_repo.api.create_tag("0.0.2")

    return git_repo


def test_init_no_repo(context):
    with pytest.raises(errors.GitError, match="No git repository found"):
        Git(context)


def test_get_current_info_branch(repo, monkeypatch, context):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(return_value=[]))
    path = repo.workspace
    f = path / "hello.txt"

    f.write_text("hello world! v3")

    info = Git(context).get_current_info()

    assert info["branch"] == "main"


@pytest.mark.usefixtures("repo")
def test_get_current_info_clean(monkeypatch, context):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(return_value=[]))
    info = Git(context).get_current_info()

    assert info["dirty"] is False


def test_get_current_info_dirty(repo, monkeypatch, context):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(return_value=[]))
    path = repo.workspace
    f = path / "hello.txt"

    f.write_text("hello world! v3")

    info = Git(context).get_current_info()

    assert info["dirty"] is True


@pytest.mark.usefixtures("repo")
def test_get_current_info_error_remote_branch(monkeypatch, context):
    monkeypatch.setattr(
        vcs.git.Repo,
        "iter_commits",
        mock.Mock(side_effect=vcs.git.GitCommandError("git iter_commits")),
    )

    with pytest.raises(errors.GitError, match="Unable to determine missing commit status"):
        Git(context).get_current_info()


@pytest.mark.usefixtures("repo")
def test_get_current_info_error_local_branch(monkeypatch, context):
    monkeypatch.setattr(
        vcs.git.Repo,
        "iter_commits",
        mock.Mock(side_effect=[[], vcs.git.GitCommandError("git iter_commits")]),
    )

    with pytest.raises(errors.GitError, match="Unable to determine missing commit status"):
        Git(context).get_current_info()


@pytest.mark.usefixtures("repo")
def test_get_current_info_no_local_branch(monkeypatch, context):
    monkeypatch.setattr(
        vcs.git.Repo,
        "iter_commits",
        mock.Mock(side_effect=[vcs.git.GitCommandError("cmd", "bad revision 'HEAD..origin/main'"), []]),
    )

    info = Git(context).get_current_info()
    assert info["missing_local"] is False


@pytest.mark.usefixtures("repo")
def test_get_current_info_no_remote_branch(monkeypatch, context):
    monkeypatch.setattr(
        vcs.git.Repo,
        "iter_commits",
        mock.Mock(side_effect=[[], vcs.git.GitCommandError("cmd", "bad revision 'origin/main..HEAD'")]),
    )

    info = Git(context).get_current_info()
    assert info["missing_remote"] is True


@pytest.mark.usefixtures("repo")
def test_get_current_info_missing_local(monkeypatch, context):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(side_effect=[["commit"], []]))

    info = Git(context).get_current_info()

    assert info["missing_local"] is True


@pytest.mark.usefixtures("repo")
def test_get_current_info_missing_remote(monkeypatch, context):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(side_effect=[[], ["commit"]]))

    info = Git(context).get_current_info()

    assert info["missing_remote"] is True


def test_add_paths_stages_changes_for_commit(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    assert "Changes not staged for commit" in repo.run("git status", capture=True)

    Git(context).add_paths(["hello.txt"])

    assert "Changes not staged for commit" not in repo.run("git status", capture=True)


def test_add_paths_dry_run(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")

    Git(context, dry_run=True).add_paths(["hello.txt"])

    assert "Changes not staged for commit" in repo.run("git status", capture=True)


def test_commit_adds_message_with_version_string(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    repo.run("git add hello.txt")

    Git(context).commit("current_version", "new_version", "version_tag")

    assert (
        repo.api.head.commit.message
        == "Update CHANGELOG for new_version\nBump version: current_version → new_version\n"
    )


def test_commit_with_paths(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")

    Git(context).commit("current_version", "new_version", "version_tag", ["hello.txt"])

    assert (
        repo.api.head.commit.message
        == "Update CHANGELOG for new_version\nBump version: current_version → new_version\n"
    )


def test_commit_dry_run(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")

    Git(context, dry_run=True).commit("current_version", "new_version", "version_tag", ["hello.txt"])

    assert "Changes not staged for commit" in repo.run("git status", capture=True)


def test_commit_no_changes_staged(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")

    with pytest.raises(errors.GitError) as e:
        Git(context).commit("current_version", "new_version", "version_tag")

    assert "Changes not staged for commit" in str(e.value)


def test_commit(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    repo.run("git add hello.txt")
    repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    repo.run("git add hello.txt")

    Git(context).commit("0.0.2", "0.0.3", "v0.0.3")

    assert repo.api.head.commit.message == "Update CHANGELOG for 0.0.3\nBump version: 0.0.2 → 0.0.3\n"
    assert git.TagReference(repo, path="refs/tags/v0.0.3") in repo.api.refs


def test_commit_no_tag(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    repo.run("git add hello.txt")
    repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    repo.run("git add hello.txt")

    Git(context, tag=False).commit("0.0.2", "0.0.3", "v0.0.3")

    assert repo.api.head.commit.message == "Update CHANGELOG for 0.0.3\nBump version: 0.0.2 → 0.0.3\n"
    assert git.TagReference(repo, path="refs/tags/v0.0.3") not in repo.api.refs


def test_commit_reverts_on_tag_failure(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    repo.run("git add hello.txt")
    repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    repo.run("git add hello.txt")

    with pytest.raises(errors.GitError):
        Git(context).commit("0.0.1", "0.0.2", "0.0.2")

    assert repo.api.head.commit.message == "commit log"


@pytest.mark.usefixtures("repo")
def test_commit_no_changes(context):
    with pytest.raises(errors.GitError) as ex:
        Git(context).commit("0.0.2", "0.0.3", "v0.0.3")

    assert (
        str(ex.value)
        == """Unable to commit: Cmd('git') failed due to: exit code(1)
  cmdline: git commit --message=Update CHANGELOG for 0.0.3\nBump version: 0.0.2 → 0.0.3
  stdout: 'On branch main
nothing to commit, working tree clean'"""
    )


def test_revert(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    repo.run("git add hello.txt")
    repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    repo.run("git add hello.txt")
    repo.api.index.commit("commit log 2")

    assert repo.api.head.commit.message == "commit log 2"

    Git(context).revert()

    assert repo.api.head.commit.message == "commit log"


def test_revert_dry_run(repo, context):
    path = repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    repo.run("git add hello.txt")
    repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    repo.run("git add hello.txt")
    repo.api.index.commit("commit log 2")

    assert repo.api.head.commit.message == "commit log 2"

    Git(context, dry_run=True).revert()

    assert repo.api.head.commit.message == "commit log 2"
