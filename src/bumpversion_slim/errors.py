class BumpException(Exception):  # noqa: N818
    """Base exception class."""


class GitError(BumpException):
    """Version control error."""


class VersionError(BumpException):
    """Version change error."""
