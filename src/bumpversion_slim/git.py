from __future__ import annotations

import typing as t

import git

from bumpversion_slim import errors

if t.TYPE_CHECKING:
    from bumpversion_slim.context import Context

T = t.TypeVar("T", bound="Git")


class Git:
    """VCS implementation for git repositories."""

    def __init__(
        self,
        context: Context,
        *,
        commit: bool = True,
        tag: bool = True,
        dry_run: bool = False,
    ) -> None:
        self.context = context
        self._commit = commit
        self._tag = tag
        self.dry_run = dry_run
        try:
            self.repo = git.Repo()
        except git.exc.InvalidGitRepositoryError as e:
            msg = "No git repository found, please run git init."
            raise errors.GitError(msg) from e

    def get_current_info(self) -> dict[str, str | bool]:
        """Get current state info from git."""
        branch = self.repo.active_branch.name
        try:
            missing_local = list(self.repo.iter_commits(f"HEAD..origin/{branch}"))
        except git.GitCommandError as e:
            if f"bad revision 'HEAD..origin/{branch}'" in str(e):
                missing_local = []
            else:
                msg = f"Unable to determine missing commit status: {e}"
                raise errors.GitError(msg) from e

        try:
            missing_remote = list(self.repo.iter_commits(f"origin/{branch}..HEAD"))
        except git.GitCommandError as e:
            if f"bad revision 'origin/{branch}..HEAD'" in str(e):
                missing_remote = ["missing"]
            else:
                msg = f"Unable to determine missing commit status: {e}"
                raise errors.GitError(msg) from e

        return {
            "missing_local": missing_local != [],
            "missing_remote": missing_remote != [],
            "dirty": self.repo.is_dirty(),
            "branch": branch,
        }

    def add_paths(self, paths: list[str]) -> None:
        """Add path to git repository."""
        if self.dry_run:
            self.context.warning("  Would add paths '%s' to Git", "', '".join(paths))
            return
        self.repo.git.add(*paths)

    def commit(self, current: str, new: str, tag: str, paths: list[str] | None = None) -> None:
        """Commit changes to git repository."""
        self.context.warning("Would prepare Git commit")
        paths = paths or []

        if paths:
            self.add_paths(paths)

        msg = [
            f"Update CHANGELOG for {new}",
            f"Bump version: {current} → {new}",
        ]

        message = "\n".join(msg).strip()
        if self.dry_run or not self._commit:
            self.context.warning("  Would commit to Git with message '%s", message)
            return

        try:
            self.repo.git.commit(message=message)
        except git.GitCommandError as e:
            msg = f"Unable to commit: {e}"
            raise errors.GitError(msg) from e

        if not self._tag:
            self.context.warning("  Would tag with version '%s", tag)
            return

        try:
            self.repo.git.tag(tag)
        except git.GitCommandError as e:
            self.revert()
            msg = f"Unable to tag: {e}"
            raise errors.GitError(msg) from e

    def revert(self) -> None:
        """Revert a commit."""
        if self.dry_run:
            self.context.warning("Would revert commit in Git")
            return
        self.repo.git.reset("HEAD~1", hard=True)
