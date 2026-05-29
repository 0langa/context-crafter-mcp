"""Tests for greeter.core."""

from greeter.core import greet


def test_greet_default() -> None:
    assert greet("world") == "Hello, world!"


def test_greet_excited() -> None:
    assert greet("world", excited=True) == "Hello, world!!!!"
