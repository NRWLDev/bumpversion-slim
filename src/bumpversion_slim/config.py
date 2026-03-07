from __future__ import annotations

import dataclasses
import typing
from pathlib import Path

import rtoml

from bumpversion_slim import errors

P = typing.ParamSpec("P")


@dataclasses.dataclass
class Config:
    """Changelog configuration options."""

    current_version: str
    allowed_branches: list[str] = dataclasses.field(default_factory=list)

    # CLI overrides
    verbose: int = 0
    commit: bool = True
    tag: bool = True
    allow_dirty: bool = False
    allow_missing: bool = False
    commit_extra: list[str] = dataclasses.field(default_factory=list)

    # Version bumping
    files: dict = dataclasses.field(default_factory=dict)
    version_string: str = "v{new_version}"

    # Hooks
    hooks: list[str] = dataclasses.field(default_factory=list)
    custom: dict = dataclasses.field(default_factory=dict)


def _process_overrides(overrides: dict) -> dict:
    """Process provided overrides.

    Remove any unsupplied values (None).
    """
    return {k: v for k, v in overrides.items() if v is not None}


def _process_pyproject(pyproject: Path) -> dict:
    cfg = {}
    with pyproject.open() as f:
        data = rtoml.load(f)

        if "tool" not in data or "bumpversion" not in data["tool"]:
            return cfg

        return data["tool"]["bumpversion"]


def check_deprecations(cfg: dict) -> None:  # noqa: ARG001
    """Check parsed configuration dict for deprecated features."""
    # No current deprecations
    return


def read(path: str = "pyproject.toml", **kwargs: P.kwargs) -> Config:
    """Read configuration from local environment.

    Supported configuration locations (checked in order):
    * pyproject.toml
    """
    overrides = _process_overrides(kwargs)
    cfg = {}

    pyproject = Path(path)

    if not pyproject.exists():
        msg = "pyproject.toml configuration missing."
        raise errors.ChangelogException(msg)

    # parse pyproject
    cfg = _process_pyproject(pyproject)

    cfg.update(overrides)

    check_deprecations(cfg)  # pragma: no mutate

    try:
        return Config(**cfg)
    except TypeError as e:
        msg = "Invalid configuration."
        raise errors.ChangelogException(msg) from e
