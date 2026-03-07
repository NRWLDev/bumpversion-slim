# Lightweight Version Release Manager
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![image](https://img.shields.io/pypi/v/bumpversion_slim.svg)](https://pypi.org/project/bumpversion_slim/)
[![image](https://img.shields.io/pypi/l/bumpversion_slim.svg)](https://pypi.org/project/bumpversion_slim/)
[![image](https://img.shields.io/pypi/pyversions/bumpversion_slim.svg)](https://pypi.org/project/bumpversion_slim/)
![style](https://github.com/NRWLDev/bumpversion-slim/actions/workflows/style.yml/badge.svg)
![tests](https://github.com/NRWLDev/bumpversion-slim/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/NRWLDev/bumpversion-slim/branch/main/graph/badge.svg)](https://codecov.io/gh/NRWLDev/bumpversion-slim)

# Details

This tool is intended as a very light version of
[bump-my-version](https://github.com/callowayproject/bump-my-version). It does
not provide semantic version generation, instead relying on the version
specifically being supplied. This is due to this projects intention of
augmenting [git-cliff](https://git-cliff.org), which provides changelog
generation from conventional commits as well as semantic versioning, but does
not provide file update functionality or commit/tag support.

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

or clone this repo and install with invoke/uv.

```bash
invoke install-dev
```

## Contributing

This project uses pre-commit hooks, please run `invoke install-dev` after
cloning to install dev dependencies and commit hooks.
