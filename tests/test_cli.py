import sys

import pytest

from beacon.cli import parse_args


def test_history_options_are_parsed(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["beacon", "--history", "--suspicious", "--limit", "12"],
    )

    args = parse_args()

    assert args.history is True
    assert args.suspicious is True
    assert args.limit == 12


@pytest.mark.parametrize("value", ["0", "-1", "not-a-number"])
def test_history_limit_rejects_invalid_values(monkeypatch, value):
    monkeypatch.setattr(sys, "argv", ["beacon", "--history", "--limit", value])

    with pytest.raises(SystemExit) as exc:
        parse_args()

    assert exc.value.code == 2
