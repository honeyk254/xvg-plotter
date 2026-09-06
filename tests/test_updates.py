"""Update-check helpers (C02) — pure functions, no Qt, no network."""
from xvg_plotter.updates import is_newer, latest_from_json, parse_version


def test_parse_version():
    assert parse_version("v1.2.3") == (1, 2, 3)
    assert parse_version("1.0") == (1, 0)
    assert parse_version("V2.10.1-beta") == (2, 10, 1)
    assert parse_version("") == (0,)


def test_is_newer():
    assert is_newer("1.0.2", "1.0.1")
    assert is_newer("v1.1", "1.0.9")
    assert not is_newer("1.0.1", "1.0.1")
    assert not is_newer("1.0.0", "1.0.1")


def test_latest_from_json():
    assert latest_from_json({"tag_name": "v1.0.2"}) == "1.0.2"
    assert latest_from_json({"tag_name": ""}) is None
    assert latest_from_json({}) is None
    assert latest_from_json(None) is None
