from __future__ import annotations

import importlib
import importlib.metadata
import time
import argparse

import typer

from bumpversion_slim import (
    config,
    errors,
)
from bumpversion_slim.bump import BumpVersion
from bumpversion_slim.context import Context
from bumpversion_slim.git import Git


version = importlib.metadata.version("bumpversion_slim")
parser = argparse.ArgumentParser(prog="bumpversion")
parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
parser.add_argument("version_number", help="The desired version number to bump to.")
parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, help="Don't commit changes, check for errors.")
parser.add_argument("--allow-dirty", action=argparse.BooleanOptionalAction, help="Don't abort if branch contains uncommited changes.")
parser.add_argument("--allow-missing", action=argparse.BooleanOptionalAction, help="Don't abort if missing commits on origin.")
parser.add_argument("--commit", action=argparse.BooleanOptionalAction, help="Commit changes made to package, and configured files, after writing.")
parser.add_argument("--tag", action=argparse.BooleanOptionalAction, help="Tag changes made after commit.")
parser.add_argument("--verbose", "-v", action="count", default=0, help="Set output verbosity.")


def process_info(info: dict, context: Context, cfg: config.Config, *, dry_run: bool) -> None:
    """Process git info and raise on invalid state."""
    if dry_run:
        return

    if info["dirty"] and not cfg.allow_dirty:
        context.error("Working directory is not clean. Use `allow_dirty` configuration to ignore.")
        raise typer.Exit(code=1)

    if info["missing_local"] and not cfg.allow_missing:
        context.error(
            "Current local branch is missing commits from remote %s.\nUse `allow_missing` configuration to ignore.",
            info["branch"],
        )
        raise typer.Exit(code=1)

    if info["missing_remote"] and not cfg.allow_missing:
        context.error(
            "Current remote branch is missing commits from local %s.\nUse `allow_missing` configuration to ignore.",
            info["branch"],
        )
        raise typer.Exit(code=1)

    allowed_branches = cfg.allowed_branches
    if allowed_branches and info["branch"] not in allowed_branches:
        context.error("Current branch not in allowed generation branches.")
        raise typer.Exit(code=1)


def main() -> None:
    """Bump package version."""
    args = parser.parse_args()
    start = time.time()
    cfg = config.read(
        allow_dirty=args.allow_dirty,
        allow_missing=args.allow_missing,
        commit=args.commit,
        tag=args.tag,
        verbose=args.verbose,
    )
    context = Context(args.verbose)

    try:
        _bump(
            context,
            cfg,
            args.version_number,
            dry_run=args.dry_run,
        )
    except errors.BumpException as ex:
        context.stacktrace()
        context.debug("Run time (error) %f", (time.time() - start) * 1000)
        context.error(str(ex))
        raise typer.Exit(code=1) from ex
    context.debug("Run time %f", (time.time() - start) * 1000)


def _bump(
    context: Context,
    cfg: config.Config,
    new_version: str,
    *,
    dry_run: bool = False,
) -> None:
    bv = BumpVersion(cfg, new_version, dry_run=dry_run, allow_dirty=cfg.allow_dirty)
    git = Git(context=context, dry_run=dry_run, commit=cfg.commit, tag=cfg.tag)

    process_info(git.get_current_info(), context, cfg, dry_run=dry_run)

    version_tag = cfg.version_string.format(new_version=str(new_version))

    def release_hook(_context: Context, new_version: str) -> list[str]:
        return bv.replace(new_version)

    hooks = [release_hook]
    for hook in cfg.hooks:
        try:
            import_path, hook_func = hook.split(":")
        except ValueError as e:
            context.error("Invalid hook format, expected `path.to.module:hook_func`.")
            raise typer.Exit(code=1) from e

        try:
            mod = importlib.import_module(import_path)
        except ModuleNotFoundError as e:
            context.error("Invalid hook module `%s`, not found.", import_path)
            raise typer.Exit(code=1) from e

        try:
            hooks.append(getattr(mod, hook_func))
        except AttributeError as e:
            context.error("Invalid hook func `%s`, not found in hook module.", hook_func)
            raise typer.Exit(code=1) from e

    paths = cfg.commit_extra
    for hook in hooks:
        hook_paths = hook(context, new_version)
        paths.extend(hook_paths)

    git.commit(cfg.current_version, new_version, version_tag, paths)
