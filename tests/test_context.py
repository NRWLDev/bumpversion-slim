from pathlib import Path
from unittest import mock

import pytest

from bumpversion_slim.config import Config
from bumpversion_slim.context import Context


@pytest.fixture
def config():
    return Config(current_version="0.0.0")


def test_indent(config):
    c = Context(config)
    c.indent()

    assert c._indent == 1


def test_dedent(config):
    c = Context(config)
    c._indent = 2
    c.dedent()

    assert c._indent == 1


def test_reset(config):
    c = Context(config)
    c._indent = 2
    c.reset()

    assert c._indent == 0


@pytest.mark.parametrize("verbosity", [0, 1, 2, 3])
def test_verbosity(verbosity, monkeypatch, config):
    monkeypatch.setattr(Context, "_echo", mock.Mock())
    c = Context(config, verbosity)

    messages = [
        "error",
        "warning",
        "info",
        "debug",
    ]
    for message in messages:
        getattr(c, message)(message)

    assert c._echo.call_args_list == [mock.call(message) for message in messages[: verbosity + 1]]


def test_stacktrace(monkeypatch, config):
    monkeypatch.setattr(Context, "_echo", mock.Mock())
    c = Context(config, 3)

    try:
        raise Exception("message")  # noqa: TRY002, EM101
    except:  # noqa: E722
        c.stacktrace()

    name = Path(__file__)
    assert c._echo.call_args == mock.call(
        f"""Traceback (most recent call last):
  File "{name}", line 60, in test_stacktrace
    raise Exception("message")  # noqa: TRY002, EM101
Exception: message
""",
    )


def test_stacktrace_quiet(monkeypatch, config):
    monkeypatch.setattr(Context, "_echo", mock.Mock())
    c = Context(config, 2)

    try:
        raise Exception("message")  # noqa: TRY002, EM101
    except:  # noqa: E722
        c.stacktrace()

    assert c._echo.call_count == 0
