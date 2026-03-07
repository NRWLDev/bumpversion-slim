import pytest

from bumpversion_slim import config, errors


@pytest.fixture
def config_factory(cwd):
    def factory(contents=None):
        p = cwd / "pyproject.toml"
        p.touch()
        if contents:
            p.write_text(contents)

    return factory


@pytest.fixture
def pyproject_factory(cwd):
    def factory(contents=None):
        p = cwd / "pyproject.toml"
        p.touch()
        if contents:
            p.write_text(contents)

    return factory


@pytest.fixture
def _empty_config(config_factory):
    config_factory()


def test_read_handles_missing_file(cwd):
    p = cwd / "pyproject.toml"
    p.unlink()
    with pytest.raises(errors.BumpException):
        config.read()


@pytest.mark.usefixtures("_empty_config")
def test_read_handles_empty_file():
    with pytest.raises(errors.BumpException):
        config.read()


class TestPyprojectToml:
    @pytest.mark.parametrize(
        ("value", "exp_key", "exp_value"),
        [
            ("commit = true", "commit", True),
            ("allow_dirty = true", "allow_dirty", True),
            ("allow_missing = true", "allow_missing", True),
            ("commit = false", "commit", False),
            ("allow_dirty = false", "allow_dirty", False),
            ("allow_missing = false", "allow_missing", False),
        ],
    )
    def test_read_picks_up_boolean_values(self, config_factory, value, exp_key, exp_value):
        config_factory(
            f"""
[tool.bumpversion]
current_version = "0.0.0"
{value}
""",
        )

        c = config.read()
        assert getattr(c, exp_key) == exp_value

    def test_read_picks_up_list_values(self, config_factory):
        config_factory(
            """
[tool.bumpversion]
current_version = "0.0.0"
allowed_branches = [
    "main",
    "feature/11",
]
""",
        )

        c = config.read()
        assert c.allowed_branches == ["main", "feature/11"]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("commit", True),
        ("allow_dirty", True),
    ],
)
def test_read_overrides(config_factory, key, value):
    config_factory(
        """
[tool.bumpversion]
current_version = "0.0.0"
""",
    )

    c = config.read(**{key: value})
    assert getattr(c, key) == value


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("commit", True),
        ("allow_dirty", True),
    ],
)
def test_read_overrides_pyproject(config_factory, key, value):
    config_factory(
        """
[tool.bumpversion]
current_version = "0.0.0"
""",
    )

    c = config.read(**{key: value})
    assert getattr(c, key) == value


def test_config_defaults():
    c = config.Config(current_version="0.0.0")
    assert c.verbose == 0
    assert c.version_string == "v{new_version}"
    assert c.allowed_branches == []

    for attr in [
        "commit",
        "tag",
    ]:
        assert getattr(c, attr) is True

    for attr in [
        "allow_dirty",
        "allow_missing",
    ]:
        assert getattr(c, attr) is False
