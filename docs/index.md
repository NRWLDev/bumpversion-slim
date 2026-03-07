# Overview

This tool is intended as a very light version of
[bump-my-version](https://github.com/callowayproject/bump-my-version). It does
not provide semantic version generation, instead relying on the version
specifically being supplied. This is due to this projects intention of
augmenting [git-cliff](https://git-cliff.org), which provides changelog generation from conventional
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

## Installation

```bash
pip install bumpversion-slim
```
