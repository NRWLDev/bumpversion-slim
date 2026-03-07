# Configuration

General configuration is grouped in the `[tool.bumpversion]` section of pyproject.toml.

## Simple configuration

```toml
[tool.bumpversion]
current_version = "1.2.3"
allowed_branches = [
    "main",
]

[[tool.bumpversion.files]]
filename = "README.md"
```

### `commit`
  _**[optional]**_<br />
  **default**: True

  Commit version replacement changes to the configured files.

  Also available as `--commit/--no-commit` (e.g. `bumpversion 1.2.3 --commit`)

### `tag`
  _**[optional]**_<br />
  **default**: True

  Tag the committed changes with the new version.

  Also available as `--tag/--no-tag` (e.g. `bumpversion 1.2.3 --tag`)

### `allow_dirty`
  _**[optional]**_<br />
  **default**: False

  Don't abort if the current branch contains uncommitted changes

  Also available as `--allow-dirty` (e.g. `bumpversion 1.2.3 --allow-dirty`)

### `allow_missing`
  _**[optional]**_<br />
  **default**: False

  Don't abort if the local and remote branches are out of sync.

  Also available as `--allow-missing` (e.g. `bumpversion 1.2.3 --allow-missing`)

### `version_string`
  _**[optional]**_<br />
  **default**: `v{new_version}`

  Format for the version tag, this will be passed into commit messages.

  Example:

```toml
[tool.bumpversion]
version_string = "{new_version}"
```

### `commit_extra`
  _**[optional]**_<br />
  **default**: None

  Additional file(s) to commit even if `bumpversion` has not modified them
  itself. Useful if another tool has modified a file in a previous pipeline
  step.

  Example:

```toml
[tool.bumpversion]
commit_extra = [
    "CHANGELOG.md",
]
```

### `allowed_branches`
  _**[optional]**_<br />
  **default**: None

  Prevent version being bumped if the current branch is not in the
  supplied list. By default all branches are allowed.

  Example:

```toml
[tool.bumpversion]
allowed_branches = [
  "main",
  "develop",
]
```

### `hooks`
  _**[optional]**_<br />
  **default**: None

  Run additional hooks when generating a release, this allows regenerating
  automated documentation during release process, for example.

  Example:

```toml
[tool.bumpversion]
hooks = [
  "path.to.module:hook_function",
]
```

### `custom`
  _**[optional]**_<br />
  **default**: None

  Arbitrary configuration that can be used in hooks.

  Example:

```toml
[tool.bumpversion.custom]
key = "value"
a_list = ["key", "key2"]
```

## Versioning

Versioning configuration is very similar to
[bump-my-version](https://github.com/callowayproject/bump-my-version?tab=readme-ov-file#semantic-versioning-example),
but with a few simplifications.

The default configuration will support the typical semver use case of `X.Y.Z`
version strings.

### `current_version`
  _**[optional]**_<br />
  **default**: None

  The minimum required configuration to manage versions is the current version,
  which can be moved directly from `[tool.bumpversion]`

```toml
[tool.bumpversion]
current_version = "1.2.3"
```

### `files`
  _**[optional]**_<br />
  **default**: None

  If multiple files have the current version string in them, they can be
  configured for replacement.

  Where the version string can safely be replaced with the default pattern
  `{version}`, use:

```
[[tool.bumpversion.files]]
filename = "README.md"
```

  For files that might contain other version strings that could match and
  shouldn't be updated, a search/replace pattern can be configured.

```
[[tool.bumpversion.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
```
