import pytest

def test_thing(monkeypatch):
  monkeypatch.setenv("THING", "a thing")
