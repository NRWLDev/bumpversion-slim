import pytest

from bumpversion_slim import bump, errors
from bumpversion_slim.config import Config, read


@pytest.fixture
def config_factory():
    def factory(**kwargs):
        if "current_version" not in kwargs:
            kwargs["current_version"] = "0.0.0"
        return Config(**kwargs)

    return factory


class TestModifyFile:
    def test_missing_file_raises(self, cwd):
        mf = bump.ModifyFile("filename", cwd / "filename", [])

        with pytest.raises(errors.VersionError, match=r"Configured file not found 'filename'"):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_invalid_pattern_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = bump.ModifyFile("filename", cwd / "filename", ["{invalid}"])

        with pytest.raises(errors.VersionError, match=r"Incorrect pattern '{invalid}' for 'filename'."):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_nullop_pattern_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = bump.ModifyFile("filename", cwd / "filename", ["invalid"])

        with pytest.raises(errors.VersionError, match=r"Pattern 'invalid' generated no change for 'filename'."):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_pattern_no_change_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = bump.ModifyFile("filename", cwd / "filename", ["version = {version}"])

        with pytest.raises(
            errors.VersionError,
            match=r"No change for 'filename', ensure pattern 'version = {version}' is correct.",
        ):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_update_applies_multiple_updates(self, cwd):
        (cwd / "filename").write_text('version1 = "0.0.0"\nversion2 = "0.0.0"')
        mf = bump.ModifyFile("filename", cwd / "filename", ['version1 = "{version}"', 'version2 = "{version}'])

        mf.update("0.0.0", "0.0.1", dry_run=False)

        assert (cwd / "filename.bak").read_text() == 'version1 = "0.0.1"\nversion2 = "0.0.1"'

    def test_update_writes_to_backup(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = bump.ModifyFile("filename", cwd / "filename", ["{version}"])

        original, backup = mf.update("0.0.0", "0.0.1", dry_run=False)

        assert (cwd / "filename").read_text() == "0.0.0"
        assert original.read_text() == "0.0.0"
        assert backup.read_text() == "0.0.1"


class TestInHouse:
    def test_replace(self, cwd):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[project]
version = "0.0.0"

[tool.bumpversion]
current_version = "0.0.0"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip(),
        )
        cfg = read(str(p))

        new = "1.2.3"
        bump.BumpVersion(cfg).replace(new)
        with p.open() as f:
            assert (
                f.read()
                == """[project]
version = "1.2.3"

[tool.bumpversion]
current_version = "1.2.3"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'"""
            )

    def test_replace_dry_run(self, cwd):
        content = """
[project]
version = "0.0.0"

[tool.bumpversion]
current_version = "0.0.0"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip()

        p = cwd / "pyproject.toml"
        p.write_text(content)
        cfg = read(str(p))

        new = "1.2.3"
        bump.BumpVersion(cfg, dry_run=True).replace(new)
        with p.open() as f:
            assert f.read() == content

    def test_replace_invalid_pattern_reverts_files(self, cwd):
        content = """
[project]
version = "0.0.0"

[tool.bumpversion]
current_version = "0.0.0"

[[tool.bumpversion.files]]
filename = "README.md"
pattern = "{invalid}"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip()

        (cwd / "README.md").write_text("0.0.0")
        p = cwd / "pyproject.toml"
        p.write_text(content)
        cfg = read(str(p))

        new = "1.2.3"
        with pytest.raises(errors.VersionError):
            bump.BumpVersion(cfg).replace(new)

        with (cwd / "pyproject.toml").open() as f:
            assert f.read() == content
        with (cwd / "README.md").open() as f:
            assert f.read() == "0.0.0"

    def test_replace_invalid_pattern_dry_run(self, cwd):
        content = """
[project]
version = "0.0.0"

[tool.bumpversion]
current_version = "0.0.0"

[[tool.bumpversion.files]]
filename = "README.md"
pattern = "{invalid}"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip()
        (cwd / "README.md").write_text("0.0.0")
        p = cwd / "pyproject.toml"
        p.write_text(content)
        cfg = read(str(p))

        new = "1.2.3"
        with pytest.raises(errors.VersionError):
            bump.BumpVersion(cfg, dry_run=True).replace(new)

        with (cwd / "pyproject.toml").open() as f:
            assert f.read() == content
        with (cwd / "README.md").open() as f:
            assert f.read() == "0.0.0"

    def test_replace_returns_modified_files(self, cwd):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[project]
version = "0.0.0"

[tool.bumpversion]
current_version = "0.0.0"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'

[[tool.bumpversion.files]]
filename = "nested/README.md"
        """.strip(),
        )
        cfg = read(str(p))

        p = cwd / "nested"
        p.mkdir()
        r = p / "README.md"
        r.write_text("Hello 0.0.0")

        new = "1.2.3"
        files = bump.BumpVersion(cfg).replace(new)
        assert files == ["nested/README.md", "pyproject.toml"]
