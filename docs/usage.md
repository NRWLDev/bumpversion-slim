# Usage

## Getting started

This tool is intended as a very light version of
[bump-my-version](https://github.com/callowayproject/bump-my-version). It does
not provide semantic version generation, instead relying on the version
specifically being supplied. This is due to this projects intention of
augmenting [git-cliff](), which provides changelog generation from conventional
commits as well as semantic versioning, but does not provide file update
functionality or commit/tag support.

A basic pyproject.toml configuration can be as simple as:

```toml
[tool.bumpversion]
current_version = "0.0.0"
commit_extra = ["CHANGELOG.md"]
```

## Bumping the version

Run `bumpversion VERSION_STRING` to update configured files with the new
version string, commit and tag the release.

If using in conjunction with `git-cliff` you can output the latest version
string from the cli, and provide it to `bumpversion-slim`.

```console
> git-cliff --config pyproject.toml --bump -o CHANGELOG.md
> VERSION=$(git-cliff --bumped-version)
> bumpversion $VERSION
```

### CLI options and toggles

These options allow customising on a per run basis.

* `--dry-run` extract changes and preview the proposed changelog and version
  without committing or tagging any changes.
* `-v[vv]` increase the output verbosity, handy if an error occurs or behaviour
  does not appear to match expectations.

The following toggles allow overriding configuration per run.

* `--allow-dirty/--no-allow-dirty` toggle configuration for allowing/rejecting git dirty status.
* `--allow-missing/--no-allow-missing` toggle configuration for allowing/rejecting missing commits in local/remote.
* `--reject-empty/--no-reject-empty` toggle configuration for updating configured files.
* `--commit/--no-commit` toggle configuration for committing changes.
* `--tag/--no-tag` toggle configuration for tagging release changes.

See [Configuration](/bumpversion/configuration) for additional configuration and cli flags that are available.
and how to customize them.
