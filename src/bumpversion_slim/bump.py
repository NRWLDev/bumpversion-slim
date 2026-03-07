from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass
from pathlib import Path

from bumpversion_slim import errors

if t.TYPE_CHECKING:
    from bumpversion_slim.config import Config

logger = logging.getLogger(__name__)

T = t.TypeVar("T", bound="BumpVersion")


@dataclass
class ModifyFile:
    """Configured file for modification."""

    filename: str
    path: Path
    patterns: list[str]

    def update(self, current: str, new: str, *, dry_run: bool) -> tuple[Path, Path]:
        """Update file with configured patterns."""
        try:
            with self.path.open("r") as f:
                contents = f.read()
        except FileNotFoundError as e:
            msg = f"Configured file not found '{self.filename}'."
            raise errors.VersionError(msg) from e

        for pattern in self.patterns:
            try:
                search, replace = pattern.format(version=current), pattern.format(version=new)
            except KeyError as e:
                msg = f"Incorrect pattern '{pattern}' for '{self.filename}'."
                raise errors.VersionError(msg) from e

            if search == replace:
                msg = f"Pattern '{pattern}' generated no change for '{self.filename}'."
                raise errors.VersionError(msg)

            new_contents = contents.replace(search, replace)
            if new_contents == contents:
                msg = f"No change for '{self.filename}', ensure pattern '{pattern}' is correct."
                raise errors.VersionError(msg)
            contents = new_contents

        backup = Path(f"{self.path}.bak")
        if not dry_run:
            with backup.open("w") as f:
                f.write(contents)

        return (self.path, backup)


class BumpVersion:  # noqa: D101
    def __init__(self, cfg: Config, new: str = "", *, allow_dirty: bool = False, dry_run: bool = False) -> None:
        self.allow_dirty = allow_dirty
        self.dry_run = dry_run
        self.config = cfg
        self.new = new

    def replace(self, version: str) -> list[str]:  # noqa: D102
        cwd = Path.cwd()
        files_to_modify = {
            "pyproject.toml": ModifyFile("pyproject.toml", cwd / "pyproject.toml", ['current_version = "{version}"']),
        }
        for file in self.config.files:
            mf = files_to_modify.get(file["filename"], ModifyFile(file["filename"], cwd / file["filename"], []))
            mf.patterns.append(file.get("pattern", "{version}"))
            files_to_modify[file["filename"]] = mf

        modified_files = []
        for file in files_to_modify.values():
            try:
                modified_files.append(file.update(self.config.current_version, version, dry_run=self.dry_run))
            except Exception:  # noqa: PERF203
                if not self.dry_run:
                    for _original, backup in modified_files:
                        backup.unlink()
                raise

        if not self.dry_run:
            for original, backup in modified_files:
                original.write_text(backup.read_text())
                backup.unlink()

        return sorted({mf.filename for mf in files_to_modify.values()})
